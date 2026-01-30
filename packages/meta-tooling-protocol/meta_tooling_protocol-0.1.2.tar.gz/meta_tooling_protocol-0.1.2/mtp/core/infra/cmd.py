"""
Command tools registered from infra.yaml.

Usage notes (for AI):
- Namespace: infra name (same as toolset name).
- Each tool accepts args/input/timeout/cwd/env and returns returncode/stdout/stderr.
"""

from __future__ import annotations

import os
import shlex
import subprocess
from typing import Any

from ..registry import CmdToolEntry, InfraManager, load_infra, MTP_ROOT
import sys

__all__ = ["load_cmds"]

# MTP cmd tools directory
MTP_CMD_DIR = MTP_ROOT / "infra" / "cmd"

_loaded: set[tuple[str, str, str]] = set()


def _split_cmd(command: str) -> tuple[str, list[str]]:
    if not command:
        raise RuntimeError("Command is required.")
    tokens = shlex.split(command, posix=os.name != "nt")
    if not tokens:
        raise RuntimeError("Command is required.")
    return tokens[0], tokens[1:]


def _run_cmd(entry: CmdToolEntry):
    def run(
        *,
        args: list[str] | None = None,
        input: str | None = None,
        timeout: float | None = None,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        base_cmd = entry.command
        base_args = entry.args or []
        exec_env = dict(entry.env)
        if env:
            exec_env.update(env)
        exec_cwd = cwd or entry.cwd

        # Resolve command path relative to MTP_CMD_DIR if needed
        from pathlib import Path
        cmd_path = Path(base_cmd)

        # If command is relative and contains path separators, try to resolve it
        if not cmd_path.is_absolute() and (os.sep in base_cmd or '/' in base_cmd):
            # Try to resolve relative to MTP_CMD_DIR
            potential_path = MTP_CMD_DIR / base_cmd
            if potential_path.exists():
                base_cmd = str(potential_path)
            else:
                # Try removing common prefixes like "infra/cmd/" or "infra\cmd\"
                for prefix in ["infra/cmd/", "infra\\cmd\\", "cmd/"]:
                    if base_cmd.startswith(prefix):
                        stripped = base_cmd[len(prefix):]
                        potential_path = MTP_CMD_DIR / stripped
                        if potential_path.exists():
                            base_cmd = str(potential_path)
                            break

        # Add MTP cmd directory to PATH to prioritize MTP-managed tools
        if MTP_CMD_DIR.exists():
            current_path = exec_env.get("PATH", os.environ.get("PATH", ""))
            exec_env["PATH"] = f"{MTP_CMD_DIR}{os.pathsep}{current_path}"

        if entry.shell:
            cmd_parts = [base_cmd, *base_args]
            if args:
                cmd_parts.extend(args)
            cmd_str = " ".join(cmd_parts)
            result = subprocess.run(
                cmd_str,
                input=input,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=exec_cwd,
                env=exec_env or None,
                shell=True,
            )
        else:
            cmd_name, cmd_args = _split_cmd(base_cmd)
            final_args = cmd_args + base_args + (args or [])
            result = subprocess.run(
                [cmd_name, *final_args],
                input=input,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=exec_cwd,
                env=exec_env or None,
                shell=False,
            )
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    desc = entry.description or f"Run command: {entry.command}"
    from ..docgen import DocModel

    docmodel = DocModel.from_function(run)
    run.__docmodel__ = DocModel(description=desc, signature=docmodel.signature)
    return run


def load_cmds(infra: InfraManager | None = None) -> list[str]:
    infra = infra or load_infra()
    from ..docgen import register_namespace, register_tool, register_toolset

    registered: list[str] = []
    for entry in infra.cmd_entries():
        tool_fn = _run_cmd(entry)
        namespace = entry.namespace or entry.name
        toolset = entry.toolset or namespace
        tool_name = entry.name
        key = (namespace, toolset, tool_name)
        if key in _loaded:
            registered.append(tool_name)
            continue
        register_namespace(namespace, sys.modules[__name__])
        register_toolset(namespace, toolset)
        register_tool(namespace, toolset, tool_name, tool_fn)
        _loaded.add(key)
        registered.append(tool_name)
    return registered
