"""Loading animations for EntelligenceAI CLI."""

from __future__ import annotations

import itertools
import math
import random
import threading
import time
from contextlib import contextmanager
from pathlib import Path

from rich.align import Align
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text


console = Console()


class AnimatedLoader:
    """Animated ASCII art loader with color animations."""

    # Character transition groups for animation
    CHAR_GROUPS = {
        "-": ["-", "=", "~"],
        "=": ["-", "=", "+"],
        "+": ["=", "+", "*"],
        "*": ["+", "*", "#"],
        "#": ["*", "#", "%"],
        "%": ["#", "%", "@"],
        "@": ["%", "@"],
        ":": [":", ";", "."],
        ".": [":", ".", ","],
    }

    # Green color shades for animation - matching JS ANSI codes
    COLORS = {
        "darkGreen": "dim green",  # dark green (dim)
        "green": "green",  # regular green
        "brightGreen": "bright_green",  # bright green
        "boldBrightGreen": "bold bright_green",  # bold bright green (most prominent)
    }

    def __init__(self, title: str = "EntelligenceAI", subtitle: str = ""):
        # Support cycling through multiple titles (list) or single title (string)
        if isinstance(title, list):
            self.titles = title
        else:
            self.titles = [title]
        self.subtitle = subtitle
        self.console = Console()
        self.frame = 0

        # Load ASCII art (look in parent directory, not ui/)
        ascii_art_path = Path(__file__).parent.parent / "ascii-art.txt"
        with open(ascii_art_path, encoding="utf-8") as f:
            art_content = f.read()

        # Remove trailing newlines and split
        self.art_lines = art_content.rstrip("\n").split("\n")
        self.art_height = len(self.art_lines)
        self.art_width = max(len(line) for line in self.art_lines)

    def _get_color_for_char(self, char: str, char_idx: int, line_idx: int) -> str:
        """Get animated color for a character based on position and frame - matches JS version exactly."""
        # Calculate relative position (0.0 to 1.0)
        line_position = line_idx / self.art_height

        # Core area (middle 30-60%) is most prominent
        is_core_area = 0.30 <= line_position <= 0.60

        # Create color wave patterns - same as JS
        color_wave = math.sin((char_idx * 0.1) + (line_idx * 0.15) + (self.frame * 0.2)) * 0.5 + 0.5
        color_wave2 = (
            math.sin((char_idx * 0.15) + (line_idx * 0.2) + (self.frame * 0.25)) * 0.5 + 0.5
        )

        if char in ["#", "%", "@"]:
            # Major green - brightest shades
            if is_core_area:
                # Core area - always use bold bright green for maximum prominence
                return self.COLORS["boldBrightGreen"]
            return self.COLORS["brightGreen"] if color_wave > 0.5 else self.COLORS["green"]
        elif char in ["*", "+"]:
            # Medium green shades
            if is_core_area:
                # Core area - use bright green
                return self.COLORS["brightGreen"]
            return self.COLORS["green"] if color_wave2 > 0.5 else self.COLORS["darkGreen"]
        elif char in ["=", "-"]:
            # Green shades for flow characters
            return self.COLORS["green"] if color_wave > 0.5 else self.COLORS["darkGreen"]
        elif char in [":", ";", ".", ","]:
            # Darker green for sparse characters
            return self.COLORS["darkGreen"]

        return ""

    def _animate_char(self, char: str, char_idx: int, line_idx: int) -> str:
        """Animate a character by transitioning to similar characters."""
        if char == " " or char not in self.CHAR_GROUPS:
            return char

        line_position = line_idx / self.art_height
        is_core_area = 0.30 <= line_position <= 0.60

        # Create wave patterns for animation
        wave1 = math.sin((char_idx * 0.12) + (self.frame * 0.25)) * 0.5 + 0.5
        wave2 = math.sin((line_idx * 0.18) + (self.frame * 0.15)) * 0.5 + 0.5
        wave3 = math.sin((char_idx + line_idx) * 0.08 + (self.frame * 0.3)) * 0.5 + 0.5
        combined_wave = (wave1 + wave2 + wave3) / 3

        group = self.CHAR_GROUPS[char]
        random_factor = random.random()
        frame_based = (self.frame + char_idx + line_idx * 10) % 7

        # Less animation in core area
        if is_core_area:
            should_animate = combined_wave > 0.6 or (random_factor > 0.7 and frame_based < 1)
        else:
            should_animate = combined_wave > 0.45 or random_factor > 0.5 or frame_based < 2

        if should_animate:
            selector = (int(combined_wave * 100) + frame_based + int(random_factor * 10)) % len(
                group
            )
            return group[selector]

        return char

    def _create_frame(self) -> Text:
        """Create a single animated frame."""
        result = Text()

        for line_idx, line in enumerate(self.art_lines):
            for char_idx, char in enumerate(line):
                if char == " ":
                    result.append(" ")
                else:
                    animated_char = self._animate_char(char, char_idx, line_idx)
                    color = self._get_color_for_char(animated_char, char_idx, line_idx)
                    result.append(animated_char, style=color)
            result.append("\n")

        # Add animated title/subtitle - matching JS renderLogo exactly
        dots_count = self.frame % 4
        dots = "." * dots_count
        dots_padded = dots + " " * (3 - dots_count)

        # Cycle through titles every 60 frames (~6 seconds)
        current_title = self.titles[(self.frame // 60) % len(self.titles)]

        # Animated title with pulsing colors - same logic as JS
        # Note: Each character already has bold in boldBrightGreen, so the outer bold wrapper
        # from JS (colors.bold + logoStr) is effectively replicated per-character
        title_text = Text()
        for i, ch in enumerate(current_title):
            wave = math.sin((self.frame * 0.25) + (i * 0.4)) * 0.5 + 0.5
            if wave > 0.75:
                color = self.COLORS["boldBrightGreen"]
            elif wave > 0.5:
                color = self.COLORS["brightGreen"]
            elif wave > 0.25:
                color = self.COLORS["green"]
            else:
                color = self.COLORS["darkGreen"]
            title_text.append(ch, style=f"bold {color}")

        title_text.append(dots_padded, style="dim")

        # Calculate center padding for title relative to ASCII art width
        title_width = len(current_title) + len(dots_padded)
        art_width = self.art_width
        title_padding = max(0, (art_width - title_width) // 2)

        # Add title with calculated padding to center it
        result.append("\n")
        if title_padding > 0:
            result.append(" " * title_padding)
        result.append(title_text)

        return Align.center(result)

    def run(self, duration: float = None):
        """Run the animated loader."""
        try:
            with Live(
                self._create_frame(),
                console=self.console,
                refresh_per_second=10,
                transient=True,
            ) as live:
                start_time = time.time()
                while duration is None or (time.time() - start_time) < duration:
                    time.sleep(0.1)
                    self.frame += 1
                    live.update(self._create_frame())
        except KeyboardInterrupt:
            pass


@contextmanager
def loader_screen(
    ui,
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
    import time

    from rich.live import Live

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
    ui._stop_loader_event = stop_event

    def _animate():
        phrase_cycle = itertools.cycle(phrases)
        with Live(console=ui.console, refresh_per_second=8, screen=True) as live:
            while not stop_event.is_set():
                phrase = next(phrase_cycle)
                panel = Panel.fit(
                    Align.center(f"[{ui.accent}]{title}[/]\n\n{phrase}"),
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
    ui, title: str = "EntelligenceAI", subtitle: str = "Analyzing your changes..."
):
    """
    Full-screen animated ASCII logo loader using pure Python.
    """
    from rich.live import Live

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


@contextmanager
def file_tree_loader(
    ui,
    title: str,
    files_with_stats: list,
    header: str = None,
    tick: float = 0.1,
    min_per_file_sec: float = 1.0,
    target_seconds: float = 180.0,
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
        bar = f"[{ui.accent}]" + "█" * filled + "[/]" + "░" * (width - filled)
        pct = f"{int(frac * 100):3d}%"
        return f"{bar}  {pct}"

    def build_tree_lines(active_index: int, elapsed: float) -> Text:
        lines: list[str] = []
        if header:
            lines.append(f"[{ui.accent}]{header}[/]\n")
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
                prefix = f"[{ui.accent}]▶[/]"
            line = f"{indent}{prefix} {path}"
            counts = f"  [green]+{additions}[/] [red]-{deletions}[/]"
            lines.append(f"{line}{counts}")
        text = Text.from_markup("\n".join(lines))
        text.no_wrap = False
        text.overflow = "fold"
        return text

    def _animate():
        with Live(console=ui.console, refresh_per_second=12, screen=True) as live:
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
