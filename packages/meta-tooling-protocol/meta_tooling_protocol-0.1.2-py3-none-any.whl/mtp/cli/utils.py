"""
CLI utilities for mtp.
"""

from rich.console import Console
from rich.panel import Panel


def show_header(title: str, subtitle: str, console: Console) -> None:
    console.print()
    console.print(
        Panel.fit(
            f"[bold cyan]{title}[/bold cyan]\n{subtitle}",
            border_style="cyan",
        )
    )
    console.print()
