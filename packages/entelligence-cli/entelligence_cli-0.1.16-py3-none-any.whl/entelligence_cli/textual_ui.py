from __future__ import annotations

from typing import Any


def run_textual_files_index(files_with_stats: list[dict[str, Any]], comments: list[dict[str, Any]]):
    """
    Launch a Textual-based files index screen.
    Returns the selected file path or None if cancelled.
    """
    try:
        from textual.app import App, ComposeResult
        from textual.containers import Vertical
        from textual.widgets import DataTable, Footer, Header, Input, Static
    except Exception:
        # Textual not installed or terminal incompatible
        return None

    # Build a map of issue counts per file from comments
    issue_counts: dict[str, int] = {}
    for c in comments:
        path = c.get("file", "unknown")
        issue_counts[path] = issue_counts.get(path, 0) + 1

    class FilesIndexApp(App):
        CSS = """
        #subtitle { color: grey; }
        """
        BINDINGS = [
            ("q", "quit_app", "Quit"),
            ("enter", "select", "Open"),
            ("/", "focus_filter", "Filter"),
            ("escape", "clear_or_quit", "Back"),
        ]

        def __init__(self):
            super().__init__()
            self.selected_path = None
            self._all_rows: list[dict[str, Any]] = files_with_stats

        def compose(self) -> ComposeResult:
            yield Header()
            yield Static("Filter: Press / to filter files", id="subtitle")
            self.table = DataTable(id="files")
            self.table.add_columns("File", "+", "-", "Issues")
            self._populate_table(self._all_rows)
            yield self.table
            self.filter_input = Input(
                placeholder="Type to filter; Enter to apply; Esc to cancel",
                id="filter",
                visible=False,
            )
            yield Vertical(self.filter_input)
            yield Footer()

        def _populate_table(self, rows: list[dict[str, Any]]):
            self.table.clear()
            for entry in rows:
                path = entry.get("path", "")
                adds = str(entry.get("additions", 0))
                dels = str(entry.get("deletions", 0))
                issues = str(issue_counts.get(path, 0))
                self.table.add_row(path, adds, dels, issues)
            if rows:
                self.table.cursor_type = "row"
                self.table.cursor_coordinate = (0, 0)

        def action_quit_app(self):
            self.exit(None)

        def action_select(self):
            if not self.table.row_count:
                return
            row = self.table.cursor_row
            path = self.table.get_row_at(row)[0]
            self.exit(path)

        def action_focus_filter(self):
            self.filter_input.visible = True
            self.filter_input.value = ""
            self.filter_input.focus()

        def action_clear_or_quit(self):
            if self.filter_input.visible:
                self.filter_input.visible = False
                self.table.focus()
            else:
                self.exit(None)

        async def on_input_submitted(self, event: Input.Submitted):
            query = event.value.strip().lower()
            self.filter_input.visible = False
            if not query:
                self._populate_table(self._all_rows)
                self.table.focus()
                return
            filtered = [r for r in self._all_rows if query in r.get("path", "").lower()]
            self._populate_table(filtered)
            self.table.focus()

    return FilesIndexApp().run()
