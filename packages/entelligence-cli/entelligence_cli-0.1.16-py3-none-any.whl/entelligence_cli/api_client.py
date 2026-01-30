from __future__ import annotations

import json
import logging
from contextlib import suppress
from dataclasses import dataclass
from typing import Any

import requests


logger = logging.getLogger(__name__)


@dataclass
class APIConfig:
    endpoint: str
    api_token: str = None
    timeout: int = 300  # Increase default timeout to 5 minutes for longer reviews


class APIClient:
    def __init__(self, config: APIConfig):
        self.config = config

    def generate_review(self, payload: dict) -> dict:
        """Send code changes to EntelligenceAI for review."""

        def _mask(tok: str) -> str:
            if not tok:
                return "(empty)"
            if len(tok) <= 8:
                return "*" * (len(tok) - 1) + tok[-1]
            return f"{tok[:4]}...{tok[-4:]}"

        # Normalize API token
        api_token = (self.config.api_token or "").strip()
        headers = {
            "Content-Type": "application/json",
        }

        if api_token:
            headers["Authorization"] = f"Bearer {api_token}"

        try:
            response = requests.post(
                self.config.endpoint,
                json=payload,
                headers=headers,
                timeout=self.config.timeout,
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            return {"error": "Ellie is taking too long to review - she might be stuck in a coffee queue ☕ Try again in a moment!"}
        except requests.exceptions.HTTPError as e:
            # Don't expose endpoint URLs or technical error details in error messages
            status_code = e.response.status_code if e.response else None
            
            # Friendly Ellie-style error messages based on status code
            if status_code == 500:
                return {"error": "Oops! Ellie encountered an unexpected error on the server 🤖 - try again in a moment!"}
            elif status_code == 401:
                return {"error": "Ellie can't authenticate you - please check your API token 🔑"}
            elif status_code == 403:
                return {"error": "Ellie says you don't have permission for this action 🚫 Check your API key permissions!"}
            elif status_code == 404:
                return {"error": "Ellie couldn't find what you're looking for 🔍 Check your endpoint URL!"}
            elif status_code == 429:
                return {"error": "Ellie is getting too many requests - slow down a bit! ⏳ Try again in a moment."}
            else:
                # Generic error without exposing status code or technical details
                return {"error": "Ellie ran into an issue - try again or contact support if it persists 🤔"}
        except requests.exceptions.RequestException:
            # Don't expose endpoint URLs in error messages
            # Only show generic error, not the full exception (might contain URLs)
            return {"error": "Ellie can't reach the server - check your internet connection 🌐"}

    def _coerce_to_dict(self, resp: Any) -> dict[str, Any]:
        """
        Try very hard to coerce backend response into a dict.
        Handles: dict, bytes, JSON string, double-encoded JSON string,
        and string with leading text before the first '{'.
        """
        # Unwrap bytes
        if isinstance(resp, bytes | bytearray):
            with suppress(Exception):
                resp = resp.decode("utf-8", errors="ignore")
        # Attempt up to 3 JSON parses (double-encoded cases)
        for _ in range(3):
            if isinstance(resp, dict):
                return resp
            if isinstance(resp, str):
                s = resp.strip()
                # If string has leading text, try to extract the first JSON object
                if not (s.startswith("{") or s.startswith("[")):
                    start = s.find("{")
                    end = s.rfind("}")
                    if start != -1 and end != -1 and end > start:
                        s = s[start : end + 1]
                try:
                    resp = json.loads(s)
                    continue
                except Exception:
                    break
            else:
                break
        # Final fallback
        if isinstance(resp, dict):
            return resp
        return {
            "raw_response": resp,
            "error": "Non-JSON or unexpected backend response",
        }

    def parse_review_response(self, response: Any) -> dict:
        """Parse EntelligenceAI response into display format."""
        # Normalize to a dict (supports double-encoded string cases)
        response = self._coerce_to_dict(response)
        if not isinstance(response, dict):
            return {
                "error": "Unexpected backend response type",
                "raw_response": response,
            }
        if "error" in response and response["error"]:
            return response

        # Normalize multiple possible response shapes
        comments: list[dict] = []
        meta: dict = {}
        # Capture helpful meta so we can show it even without comments
        # Also check for prompts in top-level response
        for key in (
            "releaseNote",
            "walkthrough_and_changes",
            "file_overview",
            "pr_diff",
            "prompt_for_ai_agents_for_addressing_review",
            "ai_prompt",
            "agent_prompt",
        ):
            if key in response and response[key] is not None:
                value = response[key]
                # Filter out sequence diagrams from walkthrough_and_changes for CLI
                if key == "walkthrough_and_changes" and isinstance(value, str):
                    # Remove sequence diagram section if present
                    sequence_diagram_marker = "## Sequence Diagram"
                    if sequence_diagram_marker in value:
                        # Split at the sequence diagram marker and take only the part before it
                        parts = value.split(sequence_diagram_marker)
                        value = parts[0].rstrip()  # Remove trailing whitespace
                meta[key] = value

        # v1 format: {"review": {"files": [ {path, comments:[...]}, ... ] }, "security_findings": [...]}
        if isinstance(response, dict) and "review" in response:
            review_data = response["review"]

            # Parse file-level comments
            if "files" in review_data:
                for file_review in review_data["files"]:
                    file_path = file_review.get("path", "unknown")

                    if "comments" in file_review:
                        for comment in file_review["comments"]:
                            comments.append(
                                {
                                    "severity": comment.get("severity", "info"),
                                    "file": file_path,
                                    "line": comment.get("line"),
                                    "message": comment.get("message", ""),
                                    "code_snippet": comment.get("snippet", ""),
                                    "language": self._detect_language(file_path),
                                }
                            )

            # Parse security findings
            if "security_findings" in review_data:
                for finding in review_data["security_findings"]:
                    comments.append(
                        {
                            "severity": "error",
                            "file": finding.get("file", "unknown"),
                            "line": finding.get("line"),
                            "message": f"Security: {finding.get('description', '')}",
                            "code_snippet": finding.get("snippet", ""),
                            "language": self._detect_language(finding.get("file", "")),
                        }
                    )

        # v2 format A: {"gitdiff_chunks_review": [ { "file"|"file_path"|"path": str, "comments":[...] }, ... ]}
        # v2 format B: {"gitdiff_chunks_review": [ { "file_name"/"path": str, "body"/"bug_description": str, ... }, ... ]}
        gitdiff_chunks = response.get("gitdiff_chunks_review")
        if (
            isinstance(response, dict)
            and gitdiff_chunks is not None
            and isinstance(gitdiff_chunks, list)
        ):
            for item in response["gitdiff_chunks_review"]:
                # Case A: per-file bucket with comments array
                if isinstance(item, dict) and isinstance(item.get("comments"), list):
                    file_path = (
                        item.get("file") or item.get("file_path") or item.get("path") or "unknown"
                    )
                    for c in item["comments"]:
                        comments.append(
                            {
                                "severity": c.get("severity", "info"),
                                "file": file_path,
                                "line": c.get("line") or c.get("lineno"),
                                "message": c.get("message") or c.get("text") or "",
                                "code_snippet": c.get("code_snippet") or c.get("snippet") or "",
                                "language": self._detect_language(file_path),
                            }
                        )
                    continue
                # Case B: each element is a single review object
                if isinstance(item, dict):
                    file_path = (
                        item.get("path") or item.get("file_name") or item.get("file") or "unknown"
                    )
                    message = item.get("body") or item.get("bug_description") or ""
                    line = item.get("line") or item.get("start_line") or None

                    # PRIORITY: Use suggested_code (diff format) over committable_code
                    suggested_code = item.get("suggested_code") or ""

                    # Extract clean code from suggested_code (strip +/- prefixes and backticks)
                    snippet = ""
                    if suggested_code:
                        # Strip backticks if present
                        code_content = suggested_code
                        if code_content.startswith("`"):
                            code_content = code_content.strip("`")

                        # Parse diff format - extract ALL lines (both + and context)
                        snippet_lines = []
                        for ln in code_content.splitlines():
                            stripped = ln.strip()
                            # Skip diff metadata
                            if (
                                stripped.startswith("diff")
                                or stripped.startswith("@@")
                                or stripped.startswith("---")
                                or stripped.startswith("+++")
                            ):
                                continue
                            # Extract lines marked with + (additions) - remove + prefix
                            if ln.startswith("+"):
                                snippet_lines.append(ln[1:])  # Remove + prefix, keep indentation
                            # Skip lines marked with - (deletions)
                            elif ln.startswith("-"):
                                continue
                            # Include context lines (no prefix) - these show existing code structure
                            elif ln.strip():
                                snippet_lines.append(ln)
                            # Preserve empty lines
                            else:
                                snippet_lines.append("")
                        snippet = "\n".join(snippet_lines)

                    # Fallback to committable_code fields if suggested_code is empty
                    if not snippet:
                        snippet = (
                            item.get("commitable_suggestion")  # common variant from backend
                            or item.get("committable_suggestion")
                            or item.get("committable_code")
                            or item.get("commitable_code")
                            or item.get("code_snippet")
                            or ""
                        )
                        # Strip triple-fence if present for display/application
                        if isinstance(snippet, str) and "```" in snippet:
                            snippet = "\n".join(
                                ln
                                for ln in snippet.splitlines()
                                if not ln.strip().startswith("```")
                            ).strip()
                    # Extract context line from suggested_code for smart apply fallback
                    context_line = None
                    if isinstance(suggested_code, str):
                        for line in suggested_code.splitlines():
                            stripped = line.strip()
                            if (
                                not stripped.startswith("```")
                                and not stripped.startswith("+")
                                and not stripped.startswith("-")
                                and stripped
                                and any(c in stripped for c in "{}();=><+-*/")
                            ):
                                context_line = stripped
                                break

                    # Process suggested_code if it's a proper unified diff or a ```diff fenced block
                    suggested_patch = None
                    patch_approach = "none"
                    if isinstance(suggested_code, str) and (
                        suggested_code.startswith("diff --git") or "```" in suggested_code
                    ):
                        # Handle raw unified diff format (no backticks)
                        if suggested_code.startswith("diff --git"):
                            suggested_patch = suggested_code
                            patch_approach = "raw_unified_diff"
                        else:
                            # Handle markdown-wrapped diff
                            lines = [
                                ln
                                for ln in suggested_code.splitlines()
                                if not ln.strip().startswith("```")
                            ]
                            raw_patch = "\n".join(lines).strip()
                            # Build proper unified diff if not already a complete diff
                            if raw_patch and not raw_patch.startswith("diff --git"):
                                suggested_patch = self._build_unified_diff(
                                    file_path=file_path,
                                    raw_patch=raw_patch,
                                    line_numbers=item.get("line_numbers"),
                                    start_line=item.get("start_line"),
                                    line=item.get("line"),
                                )
                                patch_approach = "markdown_built_diff"
                            else:
                                suggested_patch = raw_patch
                                patch_approach = "markdown_raw_diff"
                    else:
                        patch_approach = "line_based_fallback"

                    # Log which patch approach was used (for debugging)
                    if suggested_code:
                        logger.debug(
                            f"[PATCH] {file_path}:{item.get('start_line', '?')} - approach={patch_approach}, "
                            f"has_suggested_patch={suggested_patch is not None}, "
                            f"has_apply_snippet={bool(snippet)}"
                        )
                    # Determine severity from fields
                    suggestion_type = item.get("suggestion_type") or ""
                    impact = (item.get("impact") or "").lower()
                    sev = "info"
                    if suggestion_type.lower() in ("bug fix", "bug", "error") or impact == "high":
                        sev = "error"
                    elif impact in ("medium", "med"):
                        sev = "warning"
                    else:
                        sev = "suggestion"
                    # Parse range "line_numbers": "16-26"
                    apply_start = item.get("start_line")
                    apply_end = item.get("end_line") or item.get("line")
                    ln_range = item.get("line_numbers")
                    if (
                        (apply_start is None or apply_end is None)
                        and isinstance(ln_range, str)
                        and "-" in ln_range
                    ):
                        with suppress(Exception):
                            a, b = ln_range.split("-", 1)
                            apply_start = apply_start or int(a.strip())
                            apply_end = apply_end or int(b.strip())
                    # Fallback: use explicit line/start_line if still not set
                    if apply_start is None and line:
                        apply_start = int(line)
                    if apply_end is None:
                        apply_end = apply_start

                    # Auto-adjust line range based on actual snippet size
                    # Only if snippet is significantly different from specified range
                    if snippet and apply_start and apply_end:
                        snippet_line_count = len(snippet.splitlines())
                        original_range = apply_end - apply_start + 1

                        # If snippet has 10+ more lines than the range, likely wrong range
                        if snippet_line_count > original_range + 10:
                            logger.warning(
                                f"⚠️  Line range {apply_start}-{apply_end} ({original_range} lines) "
                                f"doesn't match snippet size ({snippet_line_count} lines). "
                                f"Suggested: {apply_start}-{apply_start + snippet_line_count - 1}. "
                                f"Backend should fix this line range."
                            )
                    # Capture optional agent prompt to display/copy
                    agent_prompt_obj = item.get("prompt_for_ai_agents_for_addressing_review")
                    agent_prompt_str = None
                    if agent_prompt_obj is not None:
                        # If it's already a string, use it directly
                        if isinstance(agent_prompt_obj, str):
                            agent_prompt_str = agent_prompt_obj
                        else:
                            # If it's an object/dict, convert to string
                            try:
                                agent_prompt_str = json.dumps(agent_prompt_obj, indent=2)
                            except Exception:
                                agent_prompt_str = str(agent_prompt_obj)
                    extra = {
                        "suggestion_type": item.get("suggestion_type"),
                        "impact": item.get("impact"),
                        "score": item.get("score"),
                        "reasoning": item.get("reasoning"),
                        "line_numbers": item.get("line_numbers"),
                        "agent_prompt": agent_prompt_str,
                    }
                    comments.append(
                        {
                            "severity": sev,
                            "file": file_path,
                            "line": line,
                            "message": message,
                            "code_snippet": snippet,
                            "language": self._detect_language(file_path),
                            "suggested_patch": suggested_patch,
                            "apply_snippet": snippet,
                            "original_code": item.get("file_context")
                            or item.get("original_code")
                            or "",
                            "apply_start": apply_start,
                            "apply_end": apply_end,
                            "context_line": context_line,
                            "ai_prompt": agent_prompt_str,
                            "extra": extra,
                        }
                    )

        # Extract apply_snippet from pr_diff if committable_suggestion was null/empty

        # Build summary
        # Handle file_overview being None
        file_overview = meta.get("file_overview")
        files_selected = []
        if file_overview and isinstance(file_overview, dict):
            files_selected = file_overview.get("files_selected", [])

        summary = {
            "files_changed": response.get("files_changed", 0) or len(files_selected),
            "errors": len([c for c in comments if c["severity"] == "error"]),
            "warnings": len([c for c in comments if c["severity"] == "warning"]),
            "suggestions": len([c for c in comments if c["severity"] in ["info", "suggestion"]]),
        }

        return {
            "comments": comments,
            "summary": summary,
            "meta": meta,
            "raw_response": response,  # Keep raw response for debugging
        }

    def get_user_info(self):
        """Fetch user information from backend including org UUID, GitHub token, etc."""
        if not self.config.api_token:
            return None

        # Extract base URL from endpoint (remove /generateReviewForPR/)
        base_url = (
            self.config.endpoint.rsplit("/", 2)[0]
            if "/" in self.config.endpoint
            else self.config.endpoint
        )
        user_info_url = f"{base_url}/getUserInfo/"

        headers = {
            "Authorization": f"Bearer {self.config.api_token}",
        }

        try:
            response = requests.get(user_info_url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Handle potential double-stringified JSON
            if isinstance(data, str):
                with suppress(Exception):
                    data = json.loads(data)

            if isinstance(data, dict):
                if data.get("Error") or data.get("error"):
                    error_msg = data.get("Error") or data.get("error")
                    # Return error dict so login can check the error message
                    return {"Error": error_msg}

                # Return the user info dict with expected fields
                return {
                    "UserUUID": data.get("UserUUID"),
                    "OrgUUID": data.get("OrgUUID"),
                    "OrgName": data.get("OrgName"),
                    "Email": data.get("Email"),
                    "Name": data.get("Name"),
                    "GitHubToken": data.get("GitHubToken"),
                }

            return None
        except requests.exceptions.HTTPError as e:
            # Silently handle 404 (endpoint doesn't exist yet on older backends)
            if e.response.status_code == 404:
                return None

            # Try to parse error response body
            status_code = e.response.status_code if e.response else None
            error_msg = None

            # Try to get error message from response body
            with suppress(Exception):
                if e.response and e.response.text:
                    error_data = e.response.json()
                    if isinstance(error_data, dict):
                        error_msg = (
                            error_data.get("Error")
                            or error_data.get("error")
                            or error_data.get("message")
                        )

            # Fallback to status code based error message (Ellie-style, no technical details)
            if not error_msg:
                if status_code == 401:
                    error_msg = "Ellie can't authenticate you - please check your API token 🔑"
                elif status_code == 403:
                    error_msg = "Ellie says you don't have permission for this action 🚫"
                elif status_code == 500:
                    error_msg = "Oops! Ellie hit a snag on the backend 🤖 Our team has been notified!"
                else:
                    error_msg = "Ellie couldn't complete the request - try again! 🤔"

            return {"Error": error_msg}
        except requests.exceptions.RequestException:
            # Network errors - return error dict instead of None
            # Don't expose endpoint URLs in error messages
            return {"Error": "Ellie can't reach the server - check your internet connection 🌐"}

    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".cpp": "cpp",
            ".c": "c",
            ".rb": "ruby",
            ".php": "php",
            ".swift": "swift",
            ".kt": "kotlin",
        }

        for ext, lang in ext_map.items():
            if file_path.endswith(ext):
                return lang

        return "text"

    def _build_unified_diff(
        self,
        file_path: str,
        raw_patch: str,
        line_numbers: str = None,
        start_line: int = None,
        line: int = None,
    ) -> str:
        """
        Build a proper unified diff from a partial patch string.

        Args:
            file_path: Path to the file being modified
            raw_patch: The patch content (may have +, -, and context lines)
            line_numbers: String like "14-20" indicating the line range
            start_line: Starting line number from the review
            line: Line number from the review

        Returns:
            A properly formatted unified diff string
        """
        if not raw_patch:
            return ""

        # Parse line numbers to determine hunk location
        old_start = 1
        if start_line:
            old_start = int(start_line)
        elif line:
            old_start = int(line)
        elif line_numbers and "-" in str(line_numbers):
            with suppress(Exception):
                old_start = int(str(line_numbers).split("-")[0].strip())

        # Split the raw patch into lines and categorize them
        patch_lines = raw_patch.splitlines()
        removed_lines = []  # Lines to remove (marked with -)
        added_lines = []  # Lines to add (marked with +)
        context_lines = []  # Context lines (space prefix)

        has_plus = any(pl.strip().startswith("+") for pl in patch_lines)
        has_minus = any(pl.strip().startswith("-") for pl in patch_lines)

        if has_plus or has_minus:
            # Standard diff format with + and - prefixes
            for pl in patch_lines:
                stripped = pl.rstrip()
                if stripped.startswith("-"):
                    removed_lines.append(stripped[1:])  # Remove the -
                elif stripped.startswith("+"):
                    added_lines.append(stripped[1:])  # Remove the +
                elif stripped.startswith(" ") or stripped == "":
                    # Context line (starts with space) or empty line
                    context_lines.append(stripped)
                else:
                    # Line without prefix - could be context
                    if any(c in stripped for c in "{}();=><+-*/") or not stripped:
                        context_lines.append(stripped)
        else:
            # No diff prefixes - treat as new code with possible context at end
            # Last line that looks like existing code is context, rest are additions
            # Context lines typically look like: function calls, control flow, etc.
            # New code typically looks like: function definitions, assignments, etc.
            code_indicators = [
                "const ",
                "let ",
                "var ",
                "function",
                "=>",
                "class ",
                "import ",
                "export ",
                "def ",
            ]

            # Separate potential context from additions
            potential_context = []
            for i, pl in enumerate(patch_lines):
                stripped = pl.strip()
                # Check if this looks like existing code (not new code being added)
                # Context lines often start with closing braces, return statements, etc.
                is_context = (
                    stripped.startswith("}")
                    or stripped.startswith("]")
                    or stripped.startswith(")")
                    or stripped.startswith("return ")
                    or stripped in ("", "};", ");", "];", "}")
                )
                # Also treat lines that DON'T look like new definitions as context
                if not is_context:
                    is_context = not any(
                        stripped.startswith(indicator) for indicator in code_indicators
                    )

                if is_context:
                    potential_context.append((i, pl))
                else:
                    # This is new code being added - add ALL lines from here (including context before)
                    # We need to add ALL lines from the start, not just from this point
                    for j in range(len(patch_lines)):
                        added_lines.append(patch_lines[j])
                    break

            # If we found additions, use them. Otherwise treat all as additions
            if not added_lines:
                # No additions found by detection - treat all non-empty lines as additions
                added_lines = patch_lines.copy()

        # Build old_lines and new_lines for the diff
        if removed_lines:
            # We have explicit removals - these are the "before" state
            old_lines = removed_lines
            # New state = old lines transformed + any additions + context
            new_lines = added_lines if added_lines else removed_lines
        elif added_lines:
            # Pure addition - old state is empty (adding new code)
            old_lines = []
            # Normalize indentation for all added lines
            # Use 2 spaces as base, but preserve relative indentation
            new_lines = []

            # Get indentation of first meaningful line as reference
            first_line_indent = 0
            for al in added_lines:
                if al.strip():
                    first_line_indent = len(al) - len(al.lstrip())
                    break

            for al in added_lines:
                if al.strip():
                    stripped = al.strip()
                    leading = len(al) - len(al.lstrip())
                    # Calculate relative to first line
                    relative = leading - first_line_indent
                    # Base indent is 2 spaces, add relative
                    total_indent = 2 + relative
                    new_lines.append(" " * total_indent + stripped)
                elif al == "":
                    new_lines.append("")
                else:
                    new_lines.append(al)
            # For pure additions, we don't need context lines
            # git apply doesn't require context for additions (hunk shows @@ -X,0 +X,N @@)
        elif context_lines:
            # No diff prefixes - treat all context_lines as NEW CODE to add
            # This handles the case where backend sends raw code without +/-
            old_lines = []
            new_lines = []
            for cl in context_lines:
                stripped = cl.strip()
                if stripped:
                    # Normalize indentation - use 2 spaces as default for TypeScript/React
                    # This prevents indentation mismatches
                    new_lines.append("  " + stripped)
                elif cl == "":
                    # Preserve empty lines
                    new_lines.append("")
        else:
            old_lines = []
            new_lines = []

        # Build unified diff format
        diff_lines = [
            f"diff --git a/{file_path} b/{file_path}",
            f"--- a/{file_path}",
            f"+++ b/{file_path}",
            f"@@ -{old_start},{len(old_lines)} +{old_start},{len(new_lines)} @@",
        ]

        # Add old lines (with - prefix for removed, space for context)
        for ol in old_lines:
            if ol.strip().startswith("+"):
                continue  # Skip lines marked as additions
            diff_lines.append("-" + ol if ol.strip() else "")

        # Add new lines (with + prefix for added, space for context)
        for nl in new_lines:
            if nl.strip().startswith("-"):
                diff_lines.append("-" + nl)
            elif nl.strip().startswith("+"):
                diff_lines.append("+" + nl[1:].strip() if nl[1:].strip() else "")
            else:
                diff_lines.append("+" + nl if nl.strip() else "")

        return "\n".join(diff_lines)
