#!/usr/bin/env python3
"""
Multi-Agent Research System
────────────────────────────
CLI entry point.

Usage:
    python main.py "What are the latest advances in fusion energy?"
    python main.py --interactive
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

load_dotenv()

from graph.pipeline import run_pipeline
from utils import cache, logger

console = Console()

BANNER = """
╔══════════════════════════════════════════════════════╗
║        Multi-Agent Research System  v1.0             ║
║  LangGraph · Groq LLM · Tavily · Redis Cache         ║
╚══════════════════════════════════════════════════════╝
"""


def run(query: str, show_report: bool = True) -> None:
    console.print(f"[bold cyan]{BANNER}[/bold cyan]")

    # Cache status
    if cache.is_available():
        logger.success("Redis cache: connected")
    else:
        logger.warn("Redis cache: unavailable — all API calls will be live")

    logger.divider()
    console.print(f"[bold white]Research Query:[/bold white] {query}")
    logger.divider()

    start = time.time()
    try:
        state = run_pipeline(query)
    except Exception as exc:
        logger.error(f"Pipeline failed: {exc}")
        raise

    elapsed = time.time() - start
    logger.divider()
    logger.success(f"Pipeline complete in {elapsed:.1f}s")

    # Cache stats
    stats = cache.stats()
    if stats.get("status") == "connected":
        console.print(
            f"[dim]Cache stats — hits: {stats['hits']}  "
            f"misses: {stats['misses']}  keys: {stats['keys']}[/dim]"
        )

    report_path = state.get("report_path", "")
    if report_path:
        console.print(f"\n[bold green]Report saved:[/bold green] {report_path}")

    if show_report:
        final = state.get("final_report", "No report generated.")
        console.print("\n")
        console.print(Panel(Markdown(final), title="Final Research Report", border_style="green"))

    # Disputed facts summary
    disputed = state.get("disputed_facts", [])
    if disputed:
        console.print("\n[bold yellow]⚠ Disputed / uncertain claims:[/bold yellow]")
        for d in disputed:
            console.print(f"  • {d}")


def interactive_mode() -> None:
    console.print(f"[bold cyan]{BANNER}[/bold cyan]")
    console.print("[bold]Interactive mode. Type 'quit' to exit.[/bold]\n")
    while True:
        try:
            query = console.input("[bold cyan]Research query:[/bold cyan] ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if query.lower() in ("quit", "exit", "q"):
            break
        if not query:
            continue
        run(query, show_report=True)
        logger.divider()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Multi-Agent Research System"
    )
    parser.add_argument(
        "query", nargs="?",
        help="Research question (wrap in quotes)"
    )
    parser.add_argument(
        "--interactive", "-i", action="store_true",
        help="Run in interactive REPL mode"
    )
    parser.add_argument(
        "--no-print", action="store_true",
        help="Don't print the final report (just save to file)"
    )
    args = parser.parse_args()

    if args.interactive:
        interactive_mode()
    elif args.query:
        run(args.query, show_report=not args.no_print)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
