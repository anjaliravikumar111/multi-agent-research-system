"""Colourful console logger using Rich."""
from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


def agent_log(agent: str, msg: str, color: str = "cyan") -> None:
    console.print(f"[bold {color}][{agent}][/bold {color}] {msg}")


def step_log(step: str, detail: str = "") -> None:
    txt = Text(f"▶ {step}", style="bold yellow")
    if detail:
        txt.append(f"  — {detail}", style="dim white")
    console.print(txt)


def success(msg: str) -> None:
    console.print(f"[bold green]✓[/bold green] {msg}")


def warn(msg: str) -> None:
    console.print(f"[bold yellow]⚠[/bold yellow] {msg}")


def error(msg: str) -> None:
    console.print(f"[bold red]✗[/bold red] {msg}")


def section(title: str, color: str = "blue") -> None:
    console.print(Panel(title, style=f"bold {color}", expand=False))


def divider() -> None:
    console.rule(style="dim white")
