"""
Runtime primitives for MTP.
"""

from __future__ import annotations

import traceback
import inspect
from contextvars import ContextVar
from pathlib import Path
import sys
from typing import Any, Dict, Optional
import threading

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output
import nbformat

from .docgen import namespace, tool, toolset
from .io import BlockingInput, BlockingOutput, Traceback

__all__ = [
    "Instance",
    "get_instance",
    "set_instance",
    "clear_instance",
    "ensure_instance",
    "new_instance",
    "close_instance",
    "get_global_heap",
    "heap_get",
    "heap_set",
    "heap_delete",
    "heap_keys",
    "heap_clear",
    "heap_release",
    "heap_lock",
    "heap_try_lock",
]


_current_instance: ContextVar[Optional["Instance"]] = ContextVar("mtp_instance", default=None)
_global_heap: Dict[str, Any] = {}
_heap_locks: Dict[str, threading.Lock] = {}


def _lock_for(key: str) -> threading.Lock:
    if key not in _heap_locks:
        _heap_locks[key] = threading.Lock()
    return _heap_locks[key]


def _mtp_help(obj: Any = None) -> str:
    from .docgen import help_doc

    if obj is None:
        return help_doc()
    if isinstance(obj, str):
        return help_doc(obj)
    man = getattr(obj, "man", None)
    if callable(man):
        return man()
    try:
        import pydoc

        return pydoc.render_doc(obj)
    except Exception:
        return inspect.getdoc(obj) or repr(obj)


def _track_lock(key: str) -> None:
    instance = get_instance()
    if instance is not None:
        instance._held_locks.add(key)


def heap_get(key: str, default: Any = None, lock: bool = False) -> Any:
    if lock:
        _lock_for(key).acquire()
        _track_lock(key)
    return _global_heap.get(key, default)


def heap_set(key: str, value: Any) -> Any:
    _global_heap[key] = value
    return value


def heap_delete(key: str) -> bool:
    return _global_heap.pop(key, None) is not None


def heap_keys() -> list[str]:
    return list(_global_heap.keys())


def heap_clear() -> None:
    _global_heap.clear()


def heap_release(key: str) -> bool:
    lock_obj = _heap_locks.get(key)
    if lock_obj is None:
        return False
    try:
        lock_obj.release()
    except RuntimeError:
        return False
    instance = get_instance()
    if instance is not None:
        instance._held_locks.discard(key)
    return True


def heap_lock(key: str) -> None:
    _lock_for(key).acquire()
    _track_lock(key)


def heap_try_lock(key: str) -> bool:
    acquired = _lock_for(key).acquire(blocking=False)
    if acquired:
        _track_lock(key)
    return acquired


class Instance(BaseModel):
    """Runtime instance for mtp."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    heap: Dict[str, Any] = Field(default_factory=dict)
    builtins: Dict[str, Any] = Field(default_factory=dict, exclude=True)
    notebook_path: Optional[str] = Field(default=None, exclude=True)
    _shell: Optional[InteractiveShell] = PrivateAttr(default=None)
    _notebook: Optional[Any] = PrivateAttr(default=None)
    _held_locks: set[str] = PrivateAttr(default_factory=set)

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        if "heap" not in data or data.get("heap") is None:
            self.heap = _global_heap
        self.register_builtin("help", _mtp_help)
        cwd = str(Path.cwd())
        if cwd not in sys.path:
            sys.path.insert(0, cwd)
        if self._shell is None:
            self._shell = InteractiveShell.instance()
        if self.notebook_path:
            self._load_notebook()

    def get_heap(self, key: str) -> Any:
        return self.heap.get(key)

    def register_builtin(self, name: str, value: Any) -> None:
        self.builtins[name] = value

    def last_heap_item(self) -> Any:
        if not self.heap:
            return None
        return self.heap.get(next(reversed(self.heap)))

    def _load_notebook(self) -> None:
        path = self._notebook_file()
        if path.exists():
            self._notebook = nbformat.read(path, as_version=4)
        else:
            self._notebook = nbformat.v4.new_notebook()

    def set_notebook_path(self, path: Optional[str]) -> None:
        self.notebook_path = path
        if path:
            self._load_notebook()
        else:
            self._notebook = None

    def release_locks(self) -> None:
        for key in list(self._held_locks):
            lock_obj = _heap_locks.get(key)
            if lock_obj is None:
                self._held_locks.discard(key)
                continue
            try:
                lock_obj.release()
            except RuntimeError:
                pass
            self._held_locks.discard(key)

    def _notebook_file(self) -> Optional["Path"]:
        if not self.notebook_path:
            return None
        from pathlib import Path
        path = Path(self.notebook_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _append_blocking(self, code: str, outputs: list[dict[str, Any]], execution_count: Optional[int]) -> None:
        if not self.notebook_path:
            return
        if self._notebook is None:
            self._load_notebook()
        if self._notebook is None:
            return
        cell = nbformat.v4.new_code_cell(source=code, outputs=outputs, execution_count=execution_count)
        self._notebook.cells.append(cell)
        path = self._notebook_file()
        if path is not None:
            nbformat.write(self._notebook, path)

    @staticmethod
    def _render_cell(
        captured: Any,
        *,
        result: Any,
        error: Optional[BaseException],
        tb: Optional["Traceback"],
    ) -> list[dict[str, Any]]:
        def _execute_result_data(value: Any) -> dict[str, Any]:
            if isinstance(value, BaseModel):
                return {"application/json": value.model_dump()}
            if isinstance(value, dict):
                return {"application/json": value}
            return {"text/plain": repr(value)}

        outputs: list[dict[str, Any]] = []
        if captured.stdout:
            outputs.append(nbformat.v4.new_output("stream", name="stdout", text=captured.stdout))
        if captured.stderr:
            outputs.append(nbformat.v4.new_output("stream", name="stderr", text=captured.stderr))

        for item in captured.outputs:
            if isinstance(item, dict):
                outputs.append(item)
                continue
            data = getattr(item, "data", None)
            if data is None:
                outputs.append(nbformat.v4.new_output("display_data", data={"text/plain": repr(item)}, metadata={}))
                continue
            metadata = getattr(item, "metadata", {}) or {}
            outputs.append(nbformat.v4.new_output("display_data", data=data, metadata=metadata))

        if error is not None and tb is not None:
            tb_lines = tb.to_string().splitlines()
            outputs.append(nbformat.v4.new_output(
                "error",
                ename=tb.exc_type,
                evalue=tb.exc_value,
                traceback=tb_lines,
            ))
        elif result is not None:
            outputs.append(nbformat.v4.new_output(
                "execute_result",
                data=_execute_result_data(result),
                metadata={},
            ))
        return outputs

    def exec(
        self,
        *,
        code: str,
        builtins: Optional[Dict[str, Any]] = None,
    ) -> BlockingOutput:
        token = _current_instance.set(self)
        shell = self._shell or InteractiveShell.instance()
        shell.user_ns.update({
            "heap": self.heap,
        })
        if "init" in self.heap:
            shell.user_ns["init"] = self.heap["init"]
        if self.builtins:
            shell.user_ns.update(self.builtins)
        if builtins:
            shell.user_ns.update(builtins)
        stdout_text = ""
        stderr_text = ""
        error: Optional[BaseException] = None
        try:
            try:
                with capture_output() as captured:
                    exec_result = shell.run_cell(code, store_history=True)
                error = exec_result.error_in_exec or exec_result.error_before_exec
                stdout_text = captured.stdout
                stderr_text = captured.stderr
            except Exception as exc:
                error = exc
                captured = None
                exec_result = None
        finally:
            _current_instance.reset(token)

        result_value = shell.user_ns.get("result")
        tb = Traceback.from_exception(error) if error is not None else None

        if self.notebook_path:
            outputs = self._render_cell(
                captured,
                result=result_value,
                error=error,
                tb=tb,
            ) if captured is not None else []
            exec_count = exec_result.execution_count if exec_result is not None else None
            self._append_blocking(code, outputs, exec_count)

        return BlockingOutput(
            stdout=stdout_text,
            stderr=stderr_text,
            result=result_value,
            traceback=tb,
        )




def get_instance() -> Optional[Instance]:
    return _current_instance.get()


def set_instance(instance: Instance) -> None:
    _current_instance.set(instance)


def clear_instance() -> None:
    _current_instance.set(None)


def get_global_heap() -> Dict[str, Any]:
    return _global_heap


def ensure_instance(instance: Optional[Instance] = None) -> Instance:
    if instance is not None:
        set_instance(instance)
        return instance
    current = get_instance()
    if current is None:
        current = Instance()
        set_instance(current)
    return current


def new_instance() -> Instance:
    instance = Instance()
    set_instance(instance)
    return instance


def close_instance() -> None:
    current = get_instance()
    if current is not None:
        current.release_locks()
    clear_instance()


namespace("mtp")


@toolset("runtime")
class RuntimeTools:
    """Runtime helpers exposed for docs and in-process use."""

    @tool(name="python_exec")
    def exec(
        self,
        code: str,
        timeout: int = 30,
        notebook_path: Optional[str] = None,
        instance_id: Optional[str] = None,
    ) -> BlockingOutput:
        """Execute Python code and return stdout/stderr/result.

        Examples:
            code = "x = 1\\nresult = x + 1"
        """
        instance = ensure_instance()
        if notebook_path:
            instance.set_notebook_path(notebook_path)
        return instance.exec(code=code)

    @tool()
    def heap_get(self, key: str, default: Any = None, lock: bool = False) -> Any:
        """Get a heap value by key. Use lock=True to acquire a per-key lock.

        Examples:
            result = heap_get("counter", 0)
        """
        return heap_get(key, default=default, lock=lock)

    @tool()
    def heap_set(self, key: str, value: Any) -> Any:
        """Set a heap value by key and return the value.

        Examples:
            result = heap_set("counter", 1)
        """
        return heap_set(key, value)

    @tool()
    def heap_delete(self, key: str) -> bool:
        """Delete a heap value by key. Returns True if deleted.

        Examples:
            result = heap_delete("counter")
        """
        return heap_delete(key)

    @tool()
    def heap_keys(self) -> list[str]:
        """List heap keys.

        Examples:
            result = heap_keys()
        """
        return heap_keys()

    @tool()
    def heap_clear(self) -> None:
        """Clear all heap keys.

        Examples:
            heap_clear()
        """
        return heap_clear()

    @tool()
    def heap_lock(self, key: str) -> None:
        """Acquire a per-key heap lock (blocking).

        Examples:
            heap_lock("job")
        """
        return heap_lock(key)

    @tool()
    def heap_try_lock(self, key: str) -> bool:
        """Try to acquire a per-key heap lock without blocking. Returns True on success.

        Examples:
            result = heap_try_lock("job")
        """
        return heap_try_lock(key)

    @tool()
    def heap_release(self, key: str) -> bool:
        """Release a per-key heap lock. Returns True on success.

        Examples:
            result = heap_release("job")
        """
        return heap_release(key)

    @tool()
    def get_instance(self):
        """Get the current runtime instance for this context.

        Examples:
            result = get_instance()
        """
        return get_instance()

    @tool()
    def ensure_instance(self):
        """Ensure and return a runtime instance for this context.

        Examples:
            result = ensure_instance()
        """
        return ensure_instance()

    @tool()
    def new_instance(self):
        """Create and return a new runtime instance.

        Examples:
            result = new_instance()
        """
        return new_instance()

    @tool()
    def close_instance(self) -> None:
        """Close the current runtime instance and release locks.

        Examples:
            close_instance()
        """
        return close_instance()

    @tool()
    def get_global_heap(self) -> dict[str, Any]:
        """Get the global heap object.

        Examples:
            result = get_global_heap()
        """
        return get_global_heap()
