"""Interactive review UI for EntelligenceAI CLI."""

from __future__ import annotations

import os
import platform
import subprocess
import sys
import termios
import tty
from typing import Any

from rich.align import Align
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text


console = Console()


class InteractiveUI:
    """Interactive review UI with keyboard navigation."""

    def __init__(self, accent: str = "#00e5ff"):
        self.console = console
        self.accent = accent

    def _compute_pane_widths(self) -> tuple[int, int, int]:
        """
        Heuristic widths for left/center/right panes based on terminal width.
        Layout ratios are approximately 1 : 2 : 2.
        """
        total = self.console.size.width
        # Leave a small allowance for borders/padding
        body_width = max(40, total - 6)
        left = max(20, body_width * 1 // 5)
        center = max(30, body_width * 2 // 5)
        right = max(30, body_width - left - center)
        return left, center, right

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

    def _copy_to_clipboard(self, text: str) -> bool:
        """Copy text to system clipboard."""
        try:
            if platform.system().lower() == "darwin":
                p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
                p.communicate(input=text.encode("utf-8"))
                return p.returncode == 0
            elif platform.system().lower() == "linux":
                p = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
                p.communicate(input=text.encode("utf-8"))
                return p.returncode == 0
            else:
                return False
        except Exception:
            return False

    def _git_apply_with_fallbacks(self, patch: str, repo_path: str) -> tuple[bool, str]:
        """Try to apply a unified diff using git apply with multiple fallbacks."""
        # First try: Try different strip levels (a/, b/ prefix handling)
        for apply_flags in [[], ["-p0"], ["-p1"]]:
            try:
                apply_cmd = ["git", "apply", "--index"] + apply_flags
                subprocess.run(
                    apply_cmd,
                    input=patch.encode("utf-8"),
                    cwd=repo_path,
                    capture_output=True,
                    check=True,
                )
                return True, "✓ Applied via git apply"
            except subprocess.CalledProcessError:
                continue

        # Fallback 2: Try with --3way for conflicts
        try:
            subprocess.run(
                ["git", "apply", "--3way", "--index"],
                input=patch.encode("utf-8"),
                cwd=repo_path,
                capture_output=True,
                check=True,
            )
            # 3-way merge might not auto-stage, explicitly stage
            subprocess.run(["git", "add", "-A"], cwd=repo_path, capture_output=True)
            return True, "✓ Applied via git apply (3-way merge)"
        except subprocess.CalledProcessError as e:
            err = e.stderr.decode("utf-8", errors="ignore") if e.stderr else "Unknown error"
            pass

        # Final attempt: --reject (creates .rej files)
        try:
            subprocess.run(
                ["git", "apply", "--reject"],
                input=patch.encode("utf-8"),
                cwd=repo_path,
                capture_output=True,
                check=True,
            )
            return (
                False,
                "Patch partially applied with rejects; please resolve .rej hunks.",
            )
        except subprocess.CalledProcessError as e:
            err = e.stderr.decode("utf-8", errors="ignore") if e.stderr else "Unknown error"
            return False, f"Failed to apply patch: {err.strip()}"

    def _apply_snippet_by_lines(
        self,
        file_path: str,
        start_line: int,
        end_line: int,
        new_code: str,
        repo_path: str,
    ) -> tuple[bool, str]:
        """
        Replace lines [start_line, end_line] (1-based inclusive) in file_path with new_code.
        Stage the change with `git add`. Returns (ok, message).
        """
        try:
            abs_path = os.path.join(repo_path, file_path)
            with open(abs_path, encoding="utf-8") as f:
                lines = f.read().splitlines()

            # Parse the new code to get its lines
            new_code_lines = [ln for ln in new_code.splitlines() if ln.strip() or ln == ""]
            if not new_code_lines:
                return False, "Empty new code to apply"

            # Validate line numbers
            s = max(1, int(start_line))
            total_lines = len(lines)
            e = s if end_line is None else max(s, int(end_line))

            # Clamp to valid range
            if s > total_lines:
                return (
                    False,
                    f"Start line {s} exceeds file length ({total_lines} lines)",
                )
            e = min(e, total_lines)

            # ADJUST START LINE: Check if new_code contains context lines that
            # already exist in the file before the original start_line.
            adjusted_s = s
            for i, new_line in enumerate(new_code_lines[:5]):  # Check first 5 lines
                if i >= s - 1:  # Don't look before line 1
                    break
                # Check if this line exists in the file before the original start_line
                for check_line in range(1, s):
                    if lines[check_line - 1].strip() == new_line.strip():
                        # Found matching line! Adjust start to include this line
                        adjusted_s = check_line
                        break
                if adjusted_s < s:
                    break

            s = adjusted_s

            # Convert to 0-based for slicing
            s0 = s - 1  # inclusive start
            e0 = e  # exclusive end (so we replace lines s through e inclusive)

            # Replace lines [s, e] with new_lines
            updated = lines[:s0] + new_code_lines + lines[e0:]

            with open(abs_path, "w", encoding="utf-8") as f:
                f.write("\n".join(updated) + ("\n" if (updated and updated) else ""))

            subprocess.run(
                ["git", "add", "--", file_path],
                cwd=repo_path,
                capture_output=True,
                check=True,
            )
            return True, f"⚠️  Applied via line-based replacement: {file_path}:{s}-{e}"
        except Exception as ex:
            return False, f"Failed: {ex}"

    def _apply_by_search_replace(
        self,
        file_path: str,
        original_code: str,
        new_code: str,
        repo_path: str,
    ) -> tuple[bool, str]:
        """
        Apply fix using search-replace instead of line numbers.
        More reliable when file has been edited since review was generated.

        Returns:
            (success, message) tuple
        """
        try:
            abs_path = os.path.join(repo_path, file_path)

            # Read current file
            with open(abs_path, encoding="utf-8") as f:
                content = f.read()

            # Validate original code exists
            if original_code not in content:
                return False, (
                    "Original code not found in file. File may have been modified since review."
                )

            # Check for multiple matches (ambiguous replacement)
            match_count = content.count(original_code)
            if match_count > 1:
                return False, (
                    f"Found {match_count} matches for original code. "
                    f"Too risky to auto-apply - please apply manually."
                )

            # Perform replacement (exactly once)
            updated_content = content.replace(original_code, new_code, 1)

            # Verify something actually changed
            if updated_content == content:
                return False, "No changes made (original and new code are identical)"

            # Write updated file
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(updated_content)

            # Stage with git
            subprocess.run(
                ["git", "add", "--", file_path],
                cwd=repo_path,
                capture_output=True,
                check=True,
            )

            return True, f"✓ Applied via search-replace: {file_path}"

        except Exception as e:
            return False, f"Search-replace failed: {e}"

    def _apply_snippet_by_context(
        self,
        file_path: str,
        context_line: str,
        end_marker: str,
        new_code: str,
        repo_path: str,
    ) -> tuple[bool, str]:
        """Apply a code change by finding a context line in the file and replacing until an end marker."""
        try:
            abs_path = os.path.join(repo_path, file_path)
            with open(abs_path, encoding="utf-8") as f:
                lines = f.read().splitlines()

            # Find the context line - use apply_start line number from backend if available
            context_idx = None
            if end_marker and end_marker.replace(" ", "").isdigit():
                # end_marker is being used as line number
                line_num = int(end_marker)
                if 1 <= line_num <= len(lines):
                    context_idx = line_num - 1
            else:
                # Search for context line
                for i, line in enumerate(lines):
                    if line == context_line:
                        context_idx = i
                        break

                if context_idx is None:
                    # Try loose match as fallback
                    for i, line in enumerate(lines):
                        if line.strip() == context_line.strip():
                            context_idx = i
                            break

            if context_idx is None:
                return False, "Could not find context line in file"

            # Find the real end of the block using brace counting
            block_end = context_idx
            brace_count = 0
            for i in range(context_idx, len(lines)):
                line = lines[i]
                # Count braces
                brace_count += line.count("{") - line.count("}")
                block_end = i
                # When brace_count reaches 0, we've found the closing }
                if brace_count == 0:
                    break

            # If we didn't find closing brace, use end_marker or default
            if brace_count != 0:
                # Fallback to end_marker search
                if end_marker:
                    for i in range(context_idx + 1, min(context_idx + 20, len(lines))):
                        if lines[i] == end_marker or lines[i].strip() == end_marker.strip():
                            block_end = i
                            break
                # Last resort: use next 15 lines
                if brace_count != 0:
                    block_end = min(context_idx + 15, len(lines) - 1)

            # Use new_code AS-IS from backend (preserves indentation)
            correct_lines = new_code.splitlines()

            # Replace the ENTIRE block from context_idx to block_end (inclusive)
            updated = lines[:context_idx] + correct_lines + lines[block_end + 1 :]

            with open(abs_path, "w", encoding="utf-8") as f:
                f.write("\n".join(updated) + ("\n" if updated else ""))

            subprocess.run(
                ["git", "add", "--", file_path],
                cwd=repo_path,
                capture_output=True,
                check=True,
            )
            return True, f"Applied fix to {file_path} and staged."
        except Exception as ex:
            return False, f"Failed: {ex}"

    def _fix_corrupted_404_file(
        self, file_path: str, correct_code: str, repo_path: str
    ) -> tuple[bool, str]:
        """
        Fix the 404 file corruption pattern.
        """
        try:
            abs_path = os.path.join(repo_path, file_path)
            with open(abs_path, encoding="utf-8") as f:
                lines = f.read().splitlines()

            correct_lines = [ln for ln in correct_code.splitlines() if ln.strip() or ln == ""]

            # Pattern 1: Check for merged corruption "}, [router]);Name="
            corruption_start = None
            for i, line in enumerate(lines):
                stripped = line.strip()
                if "}, [router]);" in stripped and "Name=" in stripped:
                    corruption_start = i
                    break

            # Pattern 2: Check for duplicate consecutive lines (new pattern)
            if corruption_start is None:
                for i in range(len(lines) - 1):
                    line1 = lines[i].strip()
                    line2 = lines[i + 1].strip()
                    # Skip empty lines
                    if line1 and line2 and line1 == line2:
                        # Found duplicate! Remove the second occurrence
                        corruption_start = i
                        corruption_end = i + 1
                        # Build fixed file: keep everything, just remove line at corruption_end
                        fixed = lines[:corruption_end] + lines[corruption_end + 1 :]
                        with open(abs_path, "w", encoding="utf-8") as f:
                            f.write("\n".join(fixed) + ("\n" if fixed else ""))
                        subprocess.run(
                            ["git", "add", "--", file_path],
                            cwd=repo_path,
                            capture_output=True,
                            check=True,
                        )
                        return (
                            True,
                            f"Removed duplicate line in {file_path} and staged.",
                        )

            if corruption_start is None:
                return False, "Could not find corruption pattern"

            # Pattern 1 continuation: Find end of merged corruption
            corruption_end = None
            for i in range(corruption_start + 1, len(lines)):
                stripped = lines[i].strip()
                if stripped == "}, [router]);" or stripped.startswith("}, [router]);"):
                    corruption_end = i
                    break

            if corruption_end is None:
                return False, "Could not find corruption end"

            # Build the fixed file
            fixed = lines[:corruption_start] + correct_lines + lines[corruption_end + 1 :]

            with open(abs_path, "w", encoding="utf-8") as f:
                f.write("\n".join(fixed) + ("\n" if fixed else ""))

            subprocess.run(
                ["git", "add", "--", file_path],
                cwd=repo_path,
                capture_output=True,
                check=True,
            )
            return True, f"Fixed corruption in {file_path} and staged."

        except Exception as ex:
            return False, f"Failed: {ex}"

    def render_intro(self, context: dict[str, Any]):
        """Render intro/triage page."""
        from ..ui.output import TerminalUI

        ui = TerminalUI()
        ui.show_banner()
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

    def _aggregate_file_severity(self, comments: list[dict]) -> dict[str, dict[str, int]]:
        """Aggregate comment counts per file by severity."""
        counts: dict[str, dict[str, int]] = {}
        for c in comments:
            path = c.get("file", "unknown")
            sev = c.get("severity", "info")
            file_counts = counts.setdefault(path, {"error": 0, "warning": 0, "suggestion": 0})
            if sev == "error":
                file_counts["error"] += 1
            elif sev == "warning":
                file_counts["warning"] += 1
            else:
                file_counts["suggestion"] += 1
        return counts

    def build_review_state(
        self,
        repo_info: dict[str, Any],
        files_with_stats: list[dict],
        comments: list[dict],
        summary: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Merge file stats with severity counts and produce a minimal state structure consumable by render_review().
        """
        severity_map = self._aggregate_file_severity(comments)
        files_merged: list[dict[str, Any]] = []
        for entry in files_with_stats:
            path = entry.get("path", "")
            counts = severity_map.get(path, {"error": 0, "warning": 0, "suggestion": 0})
            merged = {
                "path": path,
                "additions": entry.get("additions", 0),
                "deletions": entry.get("deletions", 0),
                "counts": counts,
            }
            files_merged.append(merged)

        # Sort by severity weight then by total churn
        def sort_key(e: dict[str, Any]) -> tuple[int, int]:
            sev_score = (
                e["counts"]["error"] * 100 + e["counts"]["warning"] * 10 + e["counts"]["suggestion"]
            )
            churn = e["additions"] + e["deletions"]
            return (-sev_score, -churn)

        files_merged.sort(key=sort_key)
        state = {
            "repo": repo_info,
            "summary": summary or {},
            "files": files_merged,
            "comments": comments,
            "selectedFileIdx": 0,
            "selectedCommentIdx": 0,
            "pane": "files",
            "expandedFiles": set(),  # paths expanded in left pane
            "selectedRowIdx": 0,  # index into visible rows (files + comments)
            "appliedIds": set(),  # ids of comments successfully applied
            "center_scroll_v": 0,  # vertical scroll offset for center panel
            "center_scroll_h": 0,  # horizontal scroll offset for center panel
            "details_scroll_v": 0,  # vertical scroll offset for details panel
            "details_scroll_h": 0,  # horizontal scroll offset for details panel
        }
        return state

    def _create_scrollable_renderable(
        self, content: Any, scroll_v: int = 0, scroll_h: int = 0, height: int = None
    ) -> Group:
        """
        Create a scrollable view of content with vertical and horizontal offsets.

        Args:
            content: Rich renderable (Text, Syntax, Group, etc.)
            scroll_v: Vertical scroll offset (lines from top)
            scroll_h: Horizontal scroll offset (columns from left)
            height: Visible height in lines (None = auto)

        Returns:
            Group with scrolled content and scroll indicators
        """

        # Convert content to lines
        if isinstance(content, Text | str):
            if isinstance(content, str):
                content = Text(content)
            lines = content.split("\n")
        elif isinstance(content, Syntax):
            # Render syntax to console and capture
            temp_console = Console(width=200, legacy_windows=False)
            with temp_console.capture() as capture:
                temp_console.print(content)
            rendered = capture.get()
            lines = [Text.from_ansi(line) for line in rendered.split("\n")]
        elif isinstance(content, Markdown):
            # Render markdown
            temp_console = Console(width=200, legacy_windows=False)
            with temp_console.capture() as capture:
                temp_console.print(content)
            rendered = capture.get()
            lines = [Text.from_ansi(line) for line in rendered.split("\n")]
        elif isinstance(content, Group):
            # Flatten group renderables
            all_lines = []
            for item in content.renderables:
                if isinstance(item, Text | str):
                    if isinstance(item, str):
                        item = Text(item)
                    all_lines.extend(item.split("\n"))
                else:
                    # Render complex items
                    temp_console = Console(width=200, legacy_windows=False)
                    with temp_console.capture() as capture:
                        temp_console.print(item)
                    rendered = capture.get()
                    all_lines.extend([Text.from_ansi(line) for line in rendered.split("\n")])
            lines = all_lines
        else:
            # Fallback: render to string
            temp_console = Console(width=200, legacy_windows=False)
            with temp_console.capture() as capture:
                temp_console.print(content)
            rendered = capture.get()
            lines = [Text.from_ansi(line) for line in rendered.split("\n")]

        # Apply vertical scroll
        total_lines = len(lines)
        scroll_v = max(0, min(scroll_v, max(0, total_lines - (height or 10))))

        visible_lines = lines[scroll_v : scroll_v + height] if height else lines[scroll_v:]

        # Apply horizontal scroll
        scrolled_lines = []
        for line in visible_lines:
            if isinstance(line, Text):
                # Horizontal scroll by slicing text
                if scroll_h > 0:
                    # Slice the text content
                    line_text = str(line.plain)
                    if len(line_text) > scroll_h:
                        scrolled_lines.append(Text(line_text[scroll_h:]))
                    else:
                        scrolled_lines.append(Text(""))
                else:
                    scrolled_lines.append(line)
            else:
                # String fallback
                if scroll_h > 0 and len(str(line)) > scroll_h:
                    scrolled_lines.append(Text(str(line)[scroll_h:]))
                else:
                    scrolled_lines.append(Text(str(line) if scroll_h == 0 else ""))

        # Add scroll indicators
        indicators = []
        if scroll_v > 0:
            indicators.append(Text("▲ Scroll up for more", style="dim"))
        if height and scroll_v + height < total_lines:
            indicators.append(Text("▼ Scroll down for more", style="dim"))
        if scroll_h > 0:
            indicators.append(Text("◄ Scrolled right", style="dim"))

        result_group = Group(*scrolled_lines)
        if indicators:
            return Group(
                Text(" | ".join(str(i.plain) for i in indicators), style="dim"), result_group
            )
        return result_group

    def compose_review_layout(self, state: dict[str, Any]) -> Layout:
        """
        Build the three-pane review layout renderable without printing it.
        """
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=3),
        )
        layout["body"].split_row(
            Layout(name="files", ratio=1),
            Layout(name="center", ratio=2),
            Layout(name="details", ratio=2),
        )
        # Header
        repo = state.get("repo", {})
        summary = state.get("summary", {})
        hdr = (
            f"[{self.accent}]Repo[/]: {repo.get('name', repo.get('path', '?'))}   "
            f"[{self.accent}]Branch[/]: {repo.get('branch', '?')} → {repo.get('base', '?')}   "
            f"[{self.accent}]Errors[/]: {summary.get('errors', 0)}   "
            f"[{self.accent}]Warnings[/]: {summary.get('warnings', 0)}   "
            f"[{self.accent}]Suggestions[/]: {summary.get('suggestions', 0)}"
        )
        layout["header"].update(Panel(hdr, border_style="white"))
        # Compute pane widths for better wrapping
        left_w, center_w, right_w = self._compute_pane_widths()
        # Build "visible rows" for left pane: files plus expanded comments
        files = state.get("files", [])
        expanded: set = state.get("expandedFiles", set())
        all_comments: list[dict[str, Any]] = state.get("comments", [])
        path_to_comments: dict[str, list[dict[str, Any]]] = {}
        for c in all_comments:
            path_to_comments.setdefault(c.get("file", ""), []).append(c)
        visible_rows: list[dict[str, Any]] = []
        for file_index, f in enumerate(files):
            visible_rows.append(
                {"type": "file", "path": f.get("path", ""), "file_index": file_index}
            )
            if f.get("path", "") in expanded:
                for idx, _c in enumerate(path_to_comments.get(f.get("path", ""), [])):
                    visible_rows.append(
                        {
                            "type": "comment",
                            "path": f.get("path", ""),
                            "file_index": file_index,
                            "comment_index": idx,
                        }
                    )
        # Persist visible rows for the input loop to use
        state["visible_rows"] = visible_rows
        selected_row = min(state.get("selectedRowIdx", 0), max(0, len(visible_rows) - 1))
        state["selectedRowIdx"] = selected_row

        # Files list (simple list, no grid) with per-file dropdown comments
        list_lines = []
        for row_idx, row in enumerate(visible_rows):
            is_selected = row_idx == selected_row
            if row["type"] == "file":
                f = files[row["file_index"]]
                is_expanded = f.get("path", "") in expanded
                caret = "▾" if is_expanded else "▸"
                label = f"[{self.accent}]{caret}[/] {f.get('path', '')}"
                if is_selected:
                    label = f"[{self.accent} bold]{label}[/]"
                list_lines.append(label)
            else:
                # Comment row: indent and show a short preview
                file_path = row["path"]
                c = path_to_comments.get(file_path, [])[row["comment_index"]]
                sev = c.get("severity", "info").upper()
                preview = c.get("message", "").split("\n", 1)[0]
                cid = c.get("id", id(c))
                is_applied = cid in state.get("appliedIds", set())
                dot = "[green]●[/]" if is_applied else "•"
                label = f"    {dot} [{self.accent}]↳[/] [{sev}] {preview[:80]}"
                if is_selected:
                    label = f"[{self.accent} bold]{label}[/]"
                list_lines.append(label)
        files_list_text = Text.from_markup("\n".join(list_lines) if list_lines else "No files")
        files_list_text.no_wrap = False
        files_list_text.overflow = "fold"
        files_border_style = self.accent if state.get("pane") == "files" else "white"
        layout["files"].update(
            Panel(files_list_text, title="Files", border_style=files_border_style, width=left_w)
        )
        # Center pane: show code snippet for selected comment, else placeholder
        selected_comment = None
        if visible_rows:
            row = visible_rows[selected_row]
            if row["type"] == "comment":
                selected_comment = path_to_comments.get(row["path"], [])[row["comment_index"]]
        if selected_comment and selected_comment.get("code_snippet"):
            code = selected_comment["code_snippet"]
            lang = selected_comment.get("language", "python")
            syntax = Syntax(
                code,
                lang,
                theme="monokai",
                line_numbers=True,
                word_wrap=False,  # Disable word wrap for horizontal scrolling
                code_width=None,  # Don't constrain width
            )
            # Get terminal height for center pane (rough estimate)
            pane_height = max(10, self.console.size.height - 10)
            center_scroll_v = state.get("center_scroll_v", 0)
            center_scroll_h = state.get("center_scroll_h", 0)
            scrollable_content = self._create_scrollable_renderable(
                syntax, scroll_v=center_scroll_v, scroll_h=center_scroll_h, height=pane_height
            )
            border_style = self.accent if state.get("pane") == "center" else "white"
            layout["center"].update(
                Panel(
                    scrollable_content,
                    title=f"{row['path']}",
                    border_style=border_style,
                    width=center_w,
                )
            )
        else:
            # Hide center pane until a comment is selected
            layout["center"].update(Panel(Text(""), border_style="white", width=center_w))
        # Details pane: selected comment details with patch preview
        if selected_comment:
            c0 = selected_comment
            sev = c0.get("severity", "info").upper()
            msg = c0.get("message", "")
            meta = f"File: {c0.get('file', '?')}  Line: {c0.get('line', '?')}"
            header = Text.from_markup(f"[bold]{sev}[/bold]\n{meta}\n")
            body_renderables = []
            # Description
            if msg:
                body_renderables.append(Text.from_markup(f"[{self.accent}]Description[/]"))
                body_renderables.append(Markdown(msg))
            # Show extra metadata if provided (suggestion type, impact, score, etc.)
            extra = c0.get("extra") or {}
            extra_lines: list[str] = []
            if extra.get("suggestion_type"):
                extra_lines.append(f"Suggestion: {extra.get('suggestion_type')}")
            if extra.get("impact"):
                extra_lines.append(f"Impact: {extra.get('impact')}")
            if extra.get("score"):
                extra_lines.append(f"Score: {extra.get('score')}")
            if extra.get("line_numbers"):
                extra_lines.append(f"Lines: {extra.get('line_numbers')}")
            if extra_lines:
                body_renderables.append(Text.from_markup(f"[{self.accent}]Details[/]"))
                body_renderables.append(Text("\n".join(extra_lines)))
            # Committable suggestion (code)
            apply_snippet = c0.get("apply_snippet")
            if apply_snippet:
                lang_guess = c0.get("language", "text")
                syntax_apply = Syntax(
                    apply_snippet,
                    lang_guess,
                    theme="monokai",
                    line_numbers=False,
                    word_wrap=True,
                    code_width=right_w - 4,
                )
                body_renderables.append(
                    Text.from_markup(f"[{self.accent}]Committable Suggestion[/]")
                )
                body_renderables.append(syntax_apply)
            # Proposed fix diff (if available)
            if c0.get("suggested_patch"):
                patch = c0["suggested_patch"]
                diff_syntax = Syntax(
                    patch,
                    "diff",
                    theme="monokai",
                    line_numbers=False,
                    word_wrap=True,
                    code_width=right_w - 4,
                )
                body_renderables.append(Text.from_markup(f"[{self.accent}]Proposed fix (diff)[/]"))
                body_renderables.append(diff_syntax)
            # Reasoning
            if extra.get("reasoning"):
                body_renderables.append(Text.from_markup(f"[{self.accent}]Reasoning[/]"))
                body_renderables.append(Markdown(str(extra.get("reasoning"))))
            # Prompt for AI agents
            agent_prompt = extra.get("agent_prompt")
            if agent_prompt:
                # Create a syntax-highlighted block exactly like Committable Suggestion and Proposed fix
                prompt_syntax = Syntax(
                    str(agent_prompt),
                    "text",
                    theme="monokai",
                    line_numbers=False,
                    word_wrap=True,
                    code_width=right_w - 4,
                )
                body_renderables.append(
                    Text.from_markup(f"[{self.accent}]Prompt to Fix with AI[/]")
                )
                body_renderables.append(prompt_syntax)
            # Build stacked group: header + collected panels
            stacked: list[Any] = []
            stacked.append(Text.from_markup(f"[{self.accent}]Proposed Fix[/]"))
            stacked.append(header)
            for r in body_renderables:
                stacked.append(r)

            # Apply scrolling to details panel
            pane_height = max(10, self.console.size.height - 10)
            details_scroll_v = state.get("details_scroll_v", 0)
            details_scroll_h = state.get("details_scroll_h", 0)
            scrollable_details = self._create_scrollable_renderable(
                Group(*stacked),
                scroll_v=details_scroll_v,
                scroll_h=details_scroll_h,
                height=pane_height,
            )
            border_style = self.accent if state.get("pane") == "details" else "white"
            layout["details"].update(
                Panel(scrollable_details, border_style=border_style, width=right_w)
            )
        else:
            # Hide details until a comment is selected
            layout["details"].update(Panel(Text(""), border_style="white", width=right_w))
        # Footer hints
        status = state.get("status_message", "")
        pane = state.get("pane", "files")
        if pane == "files":
            footer = "↑/↓ move • Enter expand/select • h collapse • →switch pane • a apply • r reject • c copy • q quit"
        else:
            footer = f"[{self.accent}]{pane.upper()} PANE[/] • ↑/↓ scroll • ←/→ switch pane • Esc back • a apply • q quit"
        if status:
            footer += f"\n{status}"
        layout["footer"].update(Panel(Text.from_markup(footer), border_style="white"))
        return layout

    def render_review(self, state: dict[str, Any]):
        """Static three-pane review layout scaffold."""
        self.console.print(self.compose_review_layout(state))

    def run_interactive_review(
        self,
        repo_info: dict[str, Any],
        files_with_stats: list[dict],
        comments: list[dict],
        summary: dict[str, Any],
        repo_path: str,
    ):
        """
        Build state and start a simple key-driven loop to handle actions.
        """
        state = self.build_review_state(repo_info, files_with_stats, comments, summary)
        state["pane"] = "files"  # Start with files panel active
        rejected_ids: set = set()
        # Ensure initial visible comments are present before first render
        state["comments"] = [c for c in comments if c.get("id", id(c)) not in rejected_ids]
        # Use Live without alternate screen for broader terminal compatibility
        with Live(
            self.compose_review_layout(state),
            console=self.console,
            refresh_per_second=10,
            screen=False,
            auto_refresh=False,
        ) as live:
            live.refresh()
            while True:
                # Keep comments view in sync each loop and refresh immediately
                visible_comments = [c for c in comments if c.get("id", id(c)) not in rejected_ids]
                state["comments"] = visible_comments
                live.update(self.compose_review_layout(state))
                live.refresh()
                key = self._read_key()

                current_pane = state.get("pane", "files")

                # Handle arrow keys based on active pane
                if key in ("\x1b[A", "k"):  # up
                    if current_pane == "files":
                        # Move selection in left pane
                        state["selectedRowIdx"] = max(0, state.get("selectedRowIdx", 0) - 1)
                    elif current_pane == "center":
                        # Scroll center pane up
                        state["center_scroll_v"] = max(0, state.get("center_scroll_v", 0) - 1)
                    elif current_pane == "details":
                        # Scroll details pane up
                        state["details_scroll_v"] = max(0, state.get("details_scroll_v", 0) - 1)

                elif key in ("\x1b[B", "j"):  # down
                    if current_pane == "files":
                        # Move selection in left pane
                        state["selectedRowIdx"] = min(
                            len(state.get("visible_rows", [])) - 1,
                            state.get("selectedRowIdx", 0) + 1,
                        )
                    elif current_pane == "center":
                        # Scroll center pane down
                        state["center_scroll_v"] = state.get("center_scroll_v", 0) + 1
                    elif current_pane == "details":
                        # Scroll details pane down
                        state["details_scroll_v"] = state.get("details_scroll_v", 0) + 1

                # Left/Right arrows to switch between panes
                elif key == "\x1b[C":  # right arrow - switch pane right
                    if current_pane == "files":
                        state["pane"] = "center"
                        # Reset scroll when switching panes
                        state["center_scroll_v"] = 0
                        state["center_scroll_h"] = 0
                    elif current_pane == "center":
                        state["pane"] = "details"
                        state["details_scroll_v"] = 0
                        state["details_scroll_h"] = 0
                    state["status_message"] = f"Switched to {state['pane']} pane"

                elif key == "\x1b[D":  # left arrow - switch pane left
                    if current_pane == "details":
                        state["pane"] = "center"
                        state["center_scroll_v"] = 0
                        state["center_scroll_h"] = 0
                    elif current_pane == "center":
                        state["pane"] = "files"
                    state["status_message"] = f"Switched to {state['pane']} pane"

                # Escape to return to files pane
                elif key == "\x1b":  # Esc
                    if current_pane != "files":
                        state["pane"] = "files"
                        state["status_message"] = "Returned to files pane"

                # Expand/collapse/select on Enter
                elif key in ("\r", "\n"):
                    rows = state.get("visible_rows", [])
                    if rows:
                        row = rows[state.get("selectedRowIdx", 0)]
                        if row["type"] == "file":
                            path = row["path"]
                            if path in state["expandedFiles"]:
                                state["expandedFiles"].remove(path)
                            else:
                                state["expandedFiles"].add(path)
                        else:
                            # comment selection - switch to center pane to view
                            state["selectedFileIdx"] = row["file_index"]
                            state["selectedCommentIdx"] = row["comment_index"]
                            state["pane"] = "center"
                            state["center_scroll_v"] = 0
                            state["center_scroll_h"] = 0
                            state["status_message"] = "Viewing in center pane (use ↑/↓ to scroll)"

                elif key == "h":
                    # Collapse file or go back to parent
                    rows = state.get("visible_rows", [])
                    if rows:
                        row = rows[state.get("selectedRowIdx", 0)]
                        if row["type"] == "file":
                            state["expandedFiles"].discard(row["path"])
                        else:
                            # move focus to parent file row
                            file_row_idx = 0
                            for i, r in enumerate(rows):
                                if r["type"] == "file" and r["path"] == row["path"]:
                                    file_row_idx = i
                                    break
                            state["selectedRowIdx"] = file_row_idx
                # Copy prompt
                elif key == "c":
                    # Determine selected comment
                    rows = state.get("visible_rows", [])
                    if rows and rows[state.get("selectedRowIdx", 0)]["type"] == "comment":
                        row = rows[state.get("selectedRowIdx", 0)]
                        file_comments = [
                            c for c in visible_comments if c.get("file") == row["path"]
                        ]
                        idx = row["comment_index"]
                        if idx < len(file_comments):
                            prompt = file_comments[idx].get("ai_prompt") or file_comments[idx].get(
                                "message", ""
                            )
                            if self._copy_to_clipboard(prompt):
                                state["status_message"] = "Copied prompt to clipboard."
                            else:
                                state["status_message"] = (
                                    "Clipboard unavailable; prompt printed below.\n" + prompt
                                )
                    else:
                        state["status_message"] = "No file selected."
                # Apply suggestion
                elif key == "a":
                    rows = state.get("visible_rows", [])
                    if rows:
                        current = rows[state.get("selectedRowIdx", 0)]
                        # If on a file row, try first patchable comment under it
                        if current["type"] == "file":
                            file_path = current["path"]
                            file_comments = [
                                c for c in visible_comments if c.get("file") == file_path
                            ]
                            target_idx = next(
                                (
                                    i
                                    for i, c in enumerate(file_comments)
                                    if c.get("suggested_patch")
                                    or (c.get("apply_snippet") and c.get("apply_start"))
                                ),
                                None,
                            )
                            if target_idx is None or target_idx >= len(file_comments):
                                state["status_message"] = "No apply-ready comments under this file."
                            else:
                                target = file_comments[target_idx]
                                target_id = target.get("id", id(target))

                                # Check if already applied
                                if target_id in state.get("appliedIds", set()):
                                    state["status_message"] = "Already applied."
                                    live.update(self.compose_review_layout(state))
                                    live.refresh()
                                    continue

                                state["status_message"] = f"Processing apply for {file_path}..."
                                live.update(self.compose_review_layout(state))
                                live.refresh()

                                # PRIORITY 1: Try search-replace (most reliable)
                                if target.get("original_code") and target.get("apply_snippet"):
                                    # Validate original_code completeness
                                    expected_lines = (
                                        target.get("apply_end", 0)
                                        - target.get("apply_start", 0)
                                        + 1
                                    )
                                    actual_lines = len(target["original_code"].splitlines())

                                    if actual_lines < expected_lines * 0.5:
                                        # original_code is suspiciously short, skip search-replace
                                        ok = False
                                        msg = f"Search-replace skipped (original_code incomplete: {actual_lines}/{expected_lines} lines)"
                                    else:
                                        ok, msg = self._apply_by_search_replace(
                                            file_path=file_path,
                                            original_code=target["original_code"],
                                            new_code=target["apply_snippet"],
                                            repo_path=repo_path,
                                        )
                                else:
                                    ok = False
                                    msg = "Search-replace not available (missing original_code)"

                                # PRIORITY 2: Try git apply if search-replace failed
                                if not ok and target.get("suggested_patch"):
                                    ok, msg = self._git_apply_with_fallbacks(
                                        target.get("suggested_patch"), repo_path
                                    )

                                # PRIORITY 3: Special fixes and line-based fallback
                                if not ok and target.get("apply_snippet"):
                                    # Try the special 404 file corruption fix
                                    if file_path.endswith("not-found.tsx"):
                                        ok, msg = self._fix_corrupted_404_file(
                                            file_path=file_path,
                                            correct_code=target.get("apply_snippet") or "",
                                            repo_path=repo_path,
                                        )
                                    # Fall back to line-based apply
                                    if not ok:
                                        start_line = (
                                            target.get("apply_start") or target.get("line") or 1
                                        )
                                        end_line = (
                                            target.get("apply_end")
                                            or target.get("line")
                                            or target.get("apply_start")
                                            or 1
                                        )
                                        ok, msg = self._apply_snippet_by_lines(
                                            file_path=file_path,
                                            start_line=start_line,
                                            end_line=end_line,
                                            new_code=target.get("apply_snippet") or "",
                                            repo_path=repo_path,
                                        )
                                state["status_message"] = msg
                                if ok:
                                    cid = file_comments[target_idx].get(
                                        "id", id(file_comments[target_idx])
                                    )
                                    applied = state.get("appliedIds", set())
                                    applied.add(cid)
                                    state["appliedIds"] = applied
                        else:
                            # On a specific comment row
                            row = current
                            file_comments = [
                                c for c in visible_comments if c.get("file") == row["path"]
                            ]
                            idx = row["comment_index"]
                            if idx < len(file_comments):
                                target = file_comments[idx]
                                target_id = target.get("id", id(target))

                                # Check if already applied
                                if target_id in state.get("appliedIds", set()):
                                    state["status_message"] = "Already applied."
                                    live.update(self.compose_review_layout(state))
                                    live.refresh()
                                    continue

                                # PRIORITY 1: Try search-replace (most reliable)
                                if target.get("original_code") and target.get("apply_snippet"):
                                    ok, msg = self._apply_by_search_replace(
                                        file_path=row["path"],
                                        original_code=target["original_code"],
                                        new_code=target["apply_snippet"],
                                        repo_path=repo_path,
                                    )
                                else:
                                    ok = False
                                    msg = "Search-replace not available"

                                # PRIORITY 2: Try git apply if search-replace failed
                                if not ok and target.get("suggested_patch"):
                                    patch = target.get("suggested_patch")
                                    # Ensure patch has proper headers for git apply
                                    if not patch.startswith("diff --git"):
                                        # Add basic headers
                                        file_path = row["path"]
                                        patch = f"diff --git a/{file_path} b/{file_path}\n--- a/{file_path}\n+++ b/{file_path}\n{patch}"
                                    ok, msg = self._git_apply_with_fallbacks(patch, repo_path)

                                # PRIORITY 3: Special fixes and line-based fallback
                                if not ok and target.get("apply_snippet"):
                                    # Try the special 404 file corruption fix
                                    if row["path"].endswith("not-found.tsx"):
                                        ok, msg = self._fix_corrupted_404_file(
                                            file_path=row["path"],
                                            correct_code=target.get("apply_snippet") or "",
                                            repo_path=repo_path,
                                        )
                                    # Fall back to line-based apply
                                    if not ok and (target.get("apply_start") or target.get("line")):
                                        ok, msg = self._apply_snippet_by_lines(
                                            file_path=row["path"],
                                            start_line=target.get("apply_start")
                                            or target.get("line")
                                            or 1,
                                            end_line=target.get("apply_end")
                                            or target.get("line")
                                            or target.get("apply_start")
                                            or 1,
                                            new_code=target.get("apply_snippet") or "",
                                            repo_path=repo_path,
                                        )
                                state["status_message"] = msg
                                if ok:
                                    # Mark as applied and move selection back to the parent file row
                                    cid = target.get("id", id(target))
                                    applied = state.get("appliedIds", set())
                                    applied.add(cid)
                                    state["appliedIds"] = applied
                                    # Move focus to parent file row
                                    for i, r in enumerate(rows):
                                        if r["type"] == "file" and r["path"] == row["path"]:
                                            state["selectedRowIdx"] = i
                                            break
                    else:
                        state["status_message"] = "No file selected."
                # Reject
                elif key == "r":
                    rows = state.get("visible_rows", [])
                    if rows and rows[state.get("selectedRowIdx", 0)]["type"] == "comment":
                        row = rows[state.get("selectedRowIdx", 0)]
                        file_comments = [
                            c for c in visible_comments if c.get("file") == row["path"]
                        ]
                        idx = row["comment_index"]
                        if idx < len(file_comments):
                            cid = file_comments[idx].get("id", id(file_comments[idx]))
                            rejected_ids.add(cid)
                            state["status_message"] = "Comment dismissed."
                    else:
                        state["status_message"] = "No file selected."
                # Quit
                elif key in ("q", "\x03"):  # q or Ctrl-C
                    break
                # Refresh the frame after processing the key
                live.update(self.compose_review_layout(state))
                live.refresh()
