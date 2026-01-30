"""UI module for EntelligenceAI CLI."""

from .interactive import InteractiveUI
from .loaders import AnimatedLoader, ascii_art_loader, file_tree_loader, loader_screen
from .output import TerminalUI
from .styles import (
    ACCENT,
    ELLIE_TITLES,
    LOADER_PHRASES,
    SEVERITY_COLORS,
    SEVERITY_ICONS,
)


__all__ = [
    "TerminalUI",
    "InteractiveUI",
    "AnimatedLoader",
    "loader_screen",
    "ascii_art_loader",
    "file_tree_loader",
    "ACCENT",
    "SEVERITY_COLORS",
    "SEVERITY_ICONS",
    "LOADER_PHRASES",
    "ELLIE_TITLES",
]
