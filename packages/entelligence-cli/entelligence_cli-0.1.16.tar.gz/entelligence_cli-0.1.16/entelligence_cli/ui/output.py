"""Output utilities for EntelligenceAI CLI."""

from __future__ import annotations

import itertools
import sys
import termios
import threading
import time
import tty
from contextlib import contextmanager
from typing import Any

from rich.align import Align
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text


console = Console()


class TerminalUI:
    """Terminal UI for displaying review results and information."""

    def __init__(self, output_mode="rich"):
        """
        Initialize Terminal UI.

        Args:
            output_mode: 'rich' for full UI, 'plain' for simple text, 'prompt-only' for minimal
        """
        self.console = console
        self.output_mode = output_mode
        # Accent color for subtle highlights
        self.accent = "#00e5ff"
        self._stop_loader_event = None

    @contextmanager
    def loader_screen(
        self,
        title: str = "Summoning the ghosts of bugs past...",
        phrases: list = None,
        interval: float = 0.9,
    ):
        """
        Display a full-screen animated loader with cycling phrases until the context exits.
        Usage:
            with ui.loader_screen("Getting AI review..."):
                result = api_call()
        """
        if phrases is None:
            phrases = [
                "Summoning the ghosts of bugs past...",
                "Feeding diffs to the entropy dragons...",
                "Persuading linters to be nice...",
                "Untangling merge-knot paradoxes...",
                "Counting semicolons very carefully...",
                "Convincing tests to pass in public...",
            ]
        stop_event = threading.Event()
        self._stop_loader_event = stop_event

        def _animate():
            phrase_cycle = itertools.cycle(phrases)
            with Live(console=self.console, refresh_per_second=8, screen=True) as live:
                while not stop_event.is_set():
                    phrase = next(phrase_cycle)
                    panel = Panel.fit(
                        Align.center(f"[{self.accent}]{title}[/]\n\n{phrase}"),
                        border_style="white",
                    )
                    live.update(Align.center(panel))
                    # Small sleep; still responsive to stop
                    for _ in range(int(max(1, interval * 10))):
                        if stop_event.is_set():
                            break
                        time.sleep(0.1)

        t = threading.Thread(target=_animate, daemon=True)
        t.start()
        try:
            yield
        finally:
            stop_event.set()
            t.join(timeout=2.0)

    @contextmanager
    def ascii_art_loader(
        self, title: str = "EntelligenceAI", subtitle: str = "Analyzing your changes..."
    ):
        """
        Full-screen animated ASCII logo loader using pure Python.
        """
        from .loaders import AnimatedLoader

        # Create and run loader in a separate thread
        loader = AnimatedLoader(title=title, subtitle=subtitle)
        stop_event = threading.Event()

        def run_loader():
            try:
                while not stop_event.is_set():
                    loader.frame += 1
                    # The loader will handle its own animation loop
                    if stop_event.wait(0.1):
                        break
            except Exception:
                pass

        thread = threading.Thread(target=run_loader, daemon=True)

        try:
            with Live(
                loader._create_frame(),
                console=loader.console,
                refresh_per_second=10,
                transient=True,
            ) as live:
                thread.start()

                # Update the live display in the main thread
                def update_display():
                    while not stop_event.is_set():
                        live.update(loader._create_frame())
                        if stop_event.wait(0.1):
                            break

                update_thread = threading.Thread(target=update_display, daemon=True)
                update_thread.start()

                yield

                stop_event.set()
                update_thread.join(timeout=1.0)
        finally:
            stop_event.set()
            thread.join(timeout=1.0)

    def _read_key(self) -> str:
        """Read a single key (supports arrow keys) without echoing."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch1 = sys.stdin.read(1)
            if ch1 == "\x1b":  # escape sequence
                ch2 = sys.stdin.read(1)
                if ch2 == "[":
                    ch3 = sys.stdin.read(1)
                    return f"\x1b[{ch3}"
                return "\x1b"
            return ch1
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def show_banner(self):
        """Display a welcome banner."""
        banner = """
╔═══════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                               ║
║    ███████╗███╗   ██╗████████╗███████╗██╗     ██╗     ██╗ ██████╗ ███████╗███╗   ██╗ ██████╗███████╗          ║
║    ██╔════╝████╗  ██║╚══██╔══╝██╔════╝██║     ██║     ██║██╔════╝ ██╔════╝████╗  ██║██╔════╝██╔════╝          ║
║    █████╗  ██╔██╗ ██║   ██║   █████╗  ██║     ██║     ██║██║  ███╗█████╗  ██╔██╗ ██║██║     █████╗            ║
║    ██╔══╝  ██║╚██╗██║   ██║   ██╔══╝  ██║     ██║     ██║██║   ██║██╔══╝  ██║╚██╗██║██║     ██╔══╝            ║
║    ███████╗██║ ╚████║   ██║   ███████╗███████╗███████╗██║╚██████╔╝███████╗██║ ╚████║╚██████╗███████╗          ║
║    ╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚══════╝╚══════╝╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝ ╚═════╝╚══════╝          ║
║                                                                                                               ║
║                               AI-Powered Code Review & Intelligence                                           ║
║                                                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════════════════════════════════════╝
        """
        self.console.print(Align.center(Text(banner, style="bold green")))

    def show_file_changes(self, files: list[str]):
        """Display list of changed files."""
        table = Table(title="Changed Files", show_header=True, header_style="bold magenta")
        table.add_column("File Path", style="cyan")

        for file_path in files:
            table.add_row(file_path)

        self.console.print(table)

    def show_file_changes_with_stats(self, files_with_stats: list[dict]):
        """Display list of changed files with additions/deletions per file."""
        table = Table(title="Changed Files", show_header=True, header_style="bold magenta")
        table.add_column("File Path", style="cyan")
        table.add_column("+", style="green", justify="right")
        table.add_column("-", style="red", justify="right")

        for entry in files_with_stats:
            path = entry.get("path", "")
            additions = entry.get("additions", 0)
            deletions = entry.get("deletions", 0)
            table.add_row(path, str(additions), str(deletions))

        self.console.print(table)

    def show_diff(self, file_path: str, diff: str):
        """Display diff with syntax highlighting."""
        self.console.print(f"\n[bold yellow]Diff for {file_path}:[/bold yellow]")

        syntax = Syntax(diff, "diff", theme="monokai", line_numbers=False)
        self.console.print(Panel(syntax, border_style="blue"))

    def show_code_snippet(self, file_path: str, code: str, language: str = "python"):
        """Display code snippet with syntax highlighting."""
        self.console.print(f"\n[bold green]Code in {file_path}:[/bold green]")

        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        self.console.print(Panel(syntax, border_style="green"))

    def show_review_comments(self, comments: list[dict]):
        """Display code review comments."""
        for comment in comments:
            severity = comment.get("severity", "info")
            color_map = {
                "error": "red",
                "warning": "yellow",
                "info": "blue",
                "suggestion": "green",
            }
            color = color_map.get(severity, "white")

            self.console.print(f"\n[bold {color}]{severity.upper()}[/bold {color}]")

            if "file" in comment:
                self.console.print(f"File: [cyan]{comment['file']}[/cyan]")

            if "line" in comment:
                self.console.print(f"Line: {comment['line']}")

            # Display the comment message
            message = comment.get("message", "")
            if message:
                from rich.markdown import Markdown

                md = Markdown(message)
                self.console.print(Panel(md, border_style=color))

            # Display code context if available
            if "code_snippet" in comment:
                syntax = Syntax(
                    comment["code_snippet"],
                    comment.get("language", "python"),
                    theme="monokai",
                    line_numbers=True,
                    start_line=comment.get("start_line", 1),
                )
                self.console.print(syntax)

    def show_progress(self, message: str):
        """Show a progress spinner."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True,
        )

    def show_summary(self, summary: dict):
        """Display a summary of the review."""
        table = Table(title="Review Summary", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="yellow")

        table.add_row("Files Changed", str(summary.get("files_changed", 0)))
        table.add_row("Errors", str(summary.get("errors", 0)))
        table.add_row("Warnings", str(summary.get("warnings", 0)))
        table.add_row("Suggestions", str(summary.get("suggestions", 0)))

        self.console.print(table)

    def error(self, message: str):
        """Display an error message."""
        self.console.print(f"[bold red]{message}[/bold red]")

    def success(self, message: str):
        """Display a success message."""
        self.console.print(f"[bold green]✓[/bold green] {message}")

    def info(self, message: str):
        """Display an info message."""
        self.console.print(f"[blue]ℹ[/blue] {message}")

    def render_intro(self, context: dict[str, Any]):
        """Render intro/triage page."""
        self.show_banner()
        repo_line = f"repo: [cyan]{context.get('repo_path', '?')}[/cyan]"
        compare = f"comparing: [yellow]{context.get('branch', '?')}[/yellow] → [yellow]{context.get('base_branch', '?')}[/yellow] (base)"
        stats = f"\n📄 {context.get('num_files', 0)} Files changed\n  {context.get('insertions', 0)} insertions | {context.get('deletions', 0)} deletions"
        mode = f"\nMode: [magenta]{context.get('compare_mode', 'committed')}[/magenta]"
        self.console.print(Align.center(repo_line))
        self.console.print(Align.center(compare))
        self.console.print(Align.center(stats))
        self.console.print(Align.center(mode))
        self.console.print("\n" + Align.center("[bold]Hit Enter to start review[/bold]").renderable)
        self.console.print(Align.center("[dim]Hit Space to view last session[/dim]"))

    def run_intro(self, context: dict[str, Any]) -> str:
        """Render intro and wait for user action. Returns: 'proceed' on Enter, 'last' on Space, 'quit' on q/Esc."""
        while True:
            self.console.clear()
            self.render_intro(context)
            key = self._read_key()
            if key in ("\r", "\n"):  # Enter
                return "proceed"
            if key == " ":
                return "last"
            if key in ("q", "\x1b"):  # q or Esc
                return "quit"

    @contextmanager
    def file_tree_loader(
        self,
        title: str,
        files_with_stats: list,
        header: str = None,
        tick: float = 0.1,
        min_per_file_sec: float = 1.0,
        target_seconds: float = 180.0,  # soft target 3 minutes; typical 2-4 min
    ):
        """
        Animated loader that shows a file tree with + / - counts and highlights
        one file at a time while work is in progress.
        """
        import os

        from rich.live import Live

        stop_event = threading.Event()

        def _progress_bar(elapsed: float) -> str:
            if target_seconds <= 0:
                return ""
            frac = max(0.0, min(1.0, elapsed / target_seconds))
            width = 30
            filled = int(frac * width)
            bar = f"[{self.accent}]" + "█" * filled + "[/]" + "░" * (width - filled)
            pct = f"{int(frac * 100):3d}%"
            return f"{bar}  {pct}"

        def build_tree_lines(active_index: int, elapsed: float) -> Text:
            lines: list[str] = []
            if header:
                lines.append(f"[{self.accent}]{header}[/]\n")
            lines.append(f"[white]{title}[/]")
            pb = _progress_bar(elapsed)
            if pb:
                lines.append(pb + "\n")
            # Build simple tree by indenting path parts
            for idx, entry in enumerate(files_with_stats):
                path = entry.get("path", "")
                additions = entry.get("additions", 0)
                deletions = entry.get("deletions", 0)
                parts = path.split(os.sep)
                indent = "  " * max(0, len(parts) - 1)
                prefix = "▹"
                if idx < active_index:
                    prefix = "[green]✔[/]"
                elif idx == active_index:
                    prefix = f"[{self.accent}]▶[/]"
                line = f"{indent}{prefix} {path}"
                counts = f"  [green]+{additions}[/] [red]-{deletions}[/]"
                lines.append(f"{line}{counts}")
            text = Text.from_markup("\n".join(lines))
            text.no_wrap = False
            text.overflow = "fold"
            return text

        def _animate():
            with Live(console=self.console, refresh_per_second=12, screen=True) as live:
                start = time.time()
                total = max(1, len(files_with_stats))
                while not stop_event.is_set():
                    elapsed = time.time() - start
                    # Compute active index based on elapsed time and per-file target
                    per_file = max(
                        min_per_file_sec,
                        (target_seconds / total) if target_seconds > 0 else min_per_file_sec,
                    )
                    active_idx = min(int(elapsed // per_file), total - 1)
                    # Keep animating but do not cycle back after reaching the end
                    live.update(
                        Panel(
                            build_tree_lines(active_idx, elapsed),
                            border_style="white",
                            title="Preparing review",
                        )
                    )
                    time.sleep(tick)

        t = threading.Thread(target=_animate, daemon=True)
        t.start()
        try:
            yield
        finally:
            stop_event.set()
            t.join(timeout=2.0)

    def run_interactive_review(
        self,
        repo_info: dict[str, Any],
        files_with_stats: list[dict],
        comments: list[dict],
        summary: dict[str, Any],
        repo_path: str,
    ):
        """
        Run interactive review session with keyboard navigation.
        Delegates to InteractiveUI for the actual implementation.
        """
        from .interactive import InteractiveUI

        interactive_ui = InteractiveUI(accent=self.accent)
        interactive_ui.run_interactive_review(
            repo_info, files_with_stats, comments, summary, repo_path
        )
