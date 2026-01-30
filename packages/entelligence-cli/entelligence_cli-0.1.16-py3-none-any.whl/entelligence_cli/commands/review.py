"""Review command for EntelligenceAI CLI."""

import random
import subprocess
import sys
from pathlib import Path

import click

from ..api_client import APIClient, APIConfig
from ..config import ConfigManager
from ..exceptions import GitError
from ..git_operations import GitOperations
from ..ui.output import TerminalUI


_NO_ISSUES_MESSAGES = [
    "Nothing to fix! Go touch some grass 🌱",
    "Clean code! Ellie didn't even need her coffee ☕",
    "Ellie says: this code is actually clean ✨",
    "No bugs found! Ellie approves 👍",
    "Nothing to fix! Ellie is proud of you 🎉",
    "Clean. Ellie is shook 🤯",
]


@click.command()
@click.option("--base-branch", default="main", help="Base branch to compare against")
@click.option(
    "--endpoint",
    envvar="ENTELLIGENCE_ENDPOINT",
    help="API endpoint URL (or set ENTELLIGENCE_ENDPOINT env var)",
)
@click.option(
    "--token",
    envvar="ENTELLIGENCE_TOKEN",
    help="API token for authentication (or set ENTELLIGENCE_TOKEN env var)",
)
@click.option(
    "--org-uuid",
    envvar="ENTELLIGENCE_ORG_UUID",
    help="Organization UUID (or set ENTELLIGENCE_ORG_UUID env var)",
)
@click.option(
    "--priority",
    default="medium",
    type=click.Choice(["low", "medium", "high"]),
    help="Priority level for the review",
)
@click.option(
    "--mode",
    default="verbose",
    type=click.Choice(["concise", "verbose"]),
    help="Review mode - concise or verbose",
)
@click.option("--plain", is_flag=True, help="Plain text output for AI coding agents (detailed)")
@click.option(
    "--prompt-only",
    is_flag=True,
    help="Minimal output for token efficiency (AI agents)",
)
@click.option(
    "--repo-path",
    default=".",
    type=click.Path(exists=True),
    help="Path to the git repository",
)
@click.option(
    "--committed-only",
    is_flag=True,
    help="Review only committed changes vs base branch (default: reviews uncommitted, falls back to committed)",
)
@click.option(
    "--textual",
    is_flag=True,
    help="Use Textual files index before interactive review (experimental)",
)
@click.option(
    "--mock",
    is_flag=True,
    help="Use mock review data (no API call) to test the interface",
)
@click.option("--debug", is_flag=True, help="Print raw backend request/response for debugging")
@click.pass_context
def review(
    ctx,
    base_branch,
    endpoint,
    token,
    org_uuid,
    priority,
    mode,
    plain,
    prompt_only,
    repo_path,
    committed_only,
    textual,
    mock,
    debug,
):
    """Run AI-powered code review on current changes.

    Default behavior: Reviews uncommitted changes (staged & unstaged),
    automatically falls back to committed changes vs base branch if none.

    Examples:
      entelligence review                  # Review uncommitted (or committed if none)
      entelligence review --committed-only # Review only committed changes vs base
      entelligence review --plain          # Detailed output for AI agents
      entelligence review --prompt-only    # Minimal output for AI agents
    """
    config = ConfigManager()

    # Get configuration from args, env, or config file
    if not token:
        token = config.get_token()
    # org_uuid will be fetched from backend via get_user_info()
    if not endpoint:
        endpoint = config.get_endpoint()

    if not token:
        click.echo("Error: No authentication token found.", err=True)
        click.echo("\nRun: entelligence auth login", err=True)
        sys.exit(1)

    # Determine output mode
    output_mode = "plain" if plain else ("prompt-only" if prompt_only else "rich")

    ui = TerminalUI(output_mode=output_mode)

    # Initialize Git operations
    git_ops = GitOperations(repo_path)

    try:
        # Get branch info
        current_branch = git_ops.get_current_branch()
        repo_name = git_ops.get_repo_name()
        commit_hash = git_ops.get_commit_hash()

        # Use cached API client and user info from session
        api_client = ctx.obj.get("api_client") if ctx.obj else None
        user_info = ctx.obj.get("user_info") if ctx.obj else None

        # If not in context (e.g., CLI args override), create new client
        if not api_client:
            api_config = APIConfig(endpoint=endpoint, api_token=token)
            api_client = APIClient(api_config)
            # Fetch user info if not cached
            if not user_info:
                user_info = api_client.get_user_info()

        # Extract org UUID from backend (required, unless provided via CLI)
        if not org_uuid:
            if not user_info:
                click.echo("Error: Could not fetch user info from backend.", err=True)
                click.echo("Please ensure your API key is valid.", err=True)
                sys.exit(1)

            if not user_info.get("OrgUUID"):
                click.echo("Error: Backend did not provide organization UUID.", err=True)
                click.echo("Please ensure your API key is valid.", err=True)
                sys.exit(1)

            org_uuid = user_info["OrgUUID"]
            if debug:
                click.echo(f"[debug] Using org UUID from backend: {org_uuid}")
        elif debug:
            click.echo(f"[debug] Using org UUID from CLI argument: {org_uuid}")

        # Get GitHub token from backend (optional - backend may not provide it)
        github_token = user_info.get("GitHubToken") if user_info else None
        if debug:
            if github_token:
                click.echo("[debug] Using GitHub token from backend")
            else:
                click.echo("[debug] No GitHub token provided by backend")

        # Optional debug: show how tokens were resolved (masked)
        def _mask(t: str) -> str:
            if not t:
                return "(empty)"
            if len(t) <= 8:
                return "*" * (len(t) - 1) + t[-1]
            return f"{t[:4]}...{t[-4:]}"

        if debug:
            click.echo(f"[debug] API token: {_mask(token)}")
            click.echo(f"[debug] GitHub token for backend: {_mask(github_token)}")
            if user_info:
                click.echo(
                    f"[debug] User info: Name={user_info.get('Name')}, Email={user_info.get('Email')}, Org={user_info.get('OrgName')}"
                )

        if output_mode == "plain":
            click.echo(f"Repository: {repo_name}")
            click.echo(f"Branch: {current_branch} (base: {base_branch})")
            click.echo(f"Commit: {commit_hash[:8]}")
            click.echo("")

        # Determine changes and prepare intro splash if rich
        # Default: Try uncommitted first, fall back to committed if none
        pr_diff_override = None
        used_uncommitted = False
        if committed_only:
            # Explicitly requested committed-only review
            changed_files = git_ops.get_changed_files(base_branch)
            used_uncommitted = False
        else:
            # Default: Try uncommitted first, fall back to committed if none
            uncommitted_files = git_ops.get_uncommitted_changed_files()
            if uncommitted_files:
                changed_files = uncommitted_files
                pr_diff_override = git_ops.get_uncommitted_unified_diff()
                used_uncommitted = True
            else:
                # No uncommitted changes, fall back to committed
                changed_files = git_ops.get_changed_files(base_branch)
                used_uncommitted = False

        if output_mode == "rich":
            # Show intro splash and wait for Enter before doing API call
            file_stats = (
                git_ops.get_uncommitted_changed_files_with_stats()
                if used_uncommitted
                else git_ops.get_changed_files_with_stats(base_branch)
            )
            total_add = sum(f["additions"] for f in file_stats)
            total_del = sum(f["deletions"] for f in file_stats)
            intro_ctx = {
                "repo_path": str(Path(repo_path).resolve()),
                "branch": current_branch,
                "base_branch": base_branch,
                "compare_mode": "uncommitted" if used_uncommitted else "committed",
                "num_files": len(file_stats),
                "insertions": total_add,
                "deletions": total_del,
            }
            action = ui.run_intro(intro_ctx)
            if action == "quit":
                return
            # 'last' not implemented yet; fall through to proceed
        elif output_mode == "plain":
            click.echo(f"Changed files ({len(changed_files)}):")
            for f in changed_files:
                click.echo(f"  - {f}")
            click.echo("")

        # If mocking, we don't require repo changes
        if not mock and not changed_files:
            if output_mode == "prompt-only":
                click.echo("NO_CHANGES")
            else:
                if committed_only:
                    ui.info("No committed changes detected compared to base branch.")
                else:
                    ui.info(
                        "No changes detected (neither uncommitted nor committed vs base branch)."
                    )
            return

        # Build payload
        if output_mode == "rich":
            with ui.show_progress("Building review request...") as progress:
                _task = progress.add_task("Building...", total=None)
                payload = git_ops.build_review_payload(
                    base_branch=base_branch,
                    org_uuid=org_uuid,
                    priority_level=priority,
                    mode=mode,
                    pr_diff=pr_diff_override,
                )
                # Attach GitHub token if available
                if github_token:
                    payload["githubToken"] = github_token
                # Mask sensitive token in logs
                _log_payload = dict(payload)
                if "githubToken" in _log_payload:
                    _log_payload["githubToken"] = "***"
        else:
            payload = git_ops.build_review_payload(
                base_branch=base_branch,
                org_uuid=org_uuid,
                priority_level=priority,
                mode=mode,
                pr_diff=pr_diff_override,
            )
            if github_token:
                payload["githubToken"] = github_token

        # Explicitly disable cross-repo analysis for this request
        payload["crossRepoAnalysisEnabled"] = False

        # Ensure diff-aware path: provide non-empty prDiff or a fileDiff array
        if not payload.get("prDiff") or not str(payload["prDiff"]).strip():
            try:
                if used_uncommitted:
                    files_for_fd = git_ops.get_uncommitted_changed_files()
                    payload["fileDiff"] = git_ops.build_file_diff_array(
                        files_for_fd, base_branch=base_branch, uncommitted=True
                    )
                else:
                    files_for_fd = git_ops.get_changed_files(base_branch)
                    payload["fileDiff"] = git_ops.build_file_diff_array(
                        files_for_fd, base_branch=base_branch, uncommitted=False
                    )
            except Exception:
                # Silently handle fileDiff building errors
                pass
        # Confirm required fields
        payload["repoName"] = payload.get("repoName") or git_ops.get_repo_name()
        payload["orgUUID"] = org_uuid or payload.get("orgUUID", "")

        if output_mode == "rich":
            ui.success(f"Prepared diff with {len(changed_files)} changed files")

        # Prepare results: real API or mock
        if not mock:
            # Send to EntelligenceAI (api_client already created above for GitHub token fetch)
            if output_mode == "rich":
                # Show Entelligence ASCII logo loader during the API call
                ellie_titles = [
                    "Brace yourself, Ellie is reviewing",
                    "Why would you do this?",
                    "This review is brought to you by therapy",
                    "Ellie has seen things...",
                    "Ellie is questioning her life choices",
                    "POV: Ellie is tired",
                    "Ellie has entered her villain era",
                ]
                with ui.ascii_art_loader(title=ellie_titles):
                    result = api_client.generate_review(payload)
            elif output_mode == "plain":
                with ui.show_progress("Requesting AI review...") as progress:
                    _task = progress.add_task("Analyzing...", total=None)
                    result = api_client.generate_review(payload)
                if debug:
                    try:
                        import json as _json

                        click.echo(
                            "\nRAW RESPONSE:\n" + _json.dumps(result, indent=2)
                            if isinstance(result, dict)
                            else str(result)
                        )
                    except Exception:
                        click.echo(f"\nRAW RESPONSE (repr): {repr(result)}")
            else:  # prompt-only
                # Show Entelligence ASCII logo loader during the API call (same as rich mode)
                ellie_titles = [
                    "Brace yourself, Ellie is reviewing",
                    "Why would you do this?",
                    "This review is brought to you by therapy",
                    "Ellie has seen things...",
                    "Ellie is questioning her life choices",
                    "POV: Ellie is tired",
                    "Ellie has entered her villain era",
                ]
                with ui.ascii_art_loader(title=ellie_titles):
                    result = api_client.generate_review(payload)
                if debug:
                    try:
                        import json as _json

                        print(
                            "RAW RESPONSE:",
                            _json.dumps(result, indent=2)
                            if isinstance(result, dict)
                            else str(result),
                        )
                    except Exception:
                        print("RAW RESPONSE (repr):", repr(result))
        else:
            # Build a deterministic mock response with an applicable patch
            mock_file = "entelligence_mock_demo.py"
            mock_patch = f"""--- /dev/null
+++ b/{mock_file}
@@
+def main():
+    print("hello from entelligence")
+
+if __name__ == "__main__":
+    main()
"""
            result = {
                "review": {
                    "files": [
                        {
                            "path": mock_file,
                            "comments": [
                                {
                                    "severity": "suggestion",
                                    "line": 1,
                                    "message": "Create a demo file with a minimal main(). Press 'a' to apply.",
                                    "snippet": "print('hello from entelligence')",
                                }
                            ],
                        }
                    ]
                },
                "mockSuggestedPatch": mock_patch,
                "files_changed": 1,
            }

        if isinstance(result, dict) and "error" in result and result["error"] is not None:
            if output_mode == "prompt-only":
                click.echo(result["error"])
            else:
                ui.error(result["error"])
            sys.exit(1)

        # Parse and display results
        if not mock:
            try:
                parsed_result = api_client.parse_review_response(result)

                # Print raw backend response in debug mode
                if debug:
                    import json

                    raw = parsed_result.get("raw_response", {})
                    if raw:
                        click.echo("\n" + "=" * 80)
                        click.echo("RAW BACKEND RESPONSE")
                        click.echo("=" * 80)
                        click.echo(json.dumps(raw, indent=2))
                        click.echo("=" * 80 + "\n")
            except Exception as e:
                # On parser error, print raw response to aid debugging
                if output_mode == "prompt-only":
                    click.echo(f"PARSER_ERROR: {str(e)}")
                    click.echo(f"RAW_RESPONSE: {repr(result)}")
                else:
                    ui.error(f"Parser error: {str(e)}")
                    try:
                        import json as _json

                        pretty = (
                            _json.dumps(result, indent=2)
                            if isinstance(result, dict)
                            else str(result)
                        )
                    except Exception:
                        pretty = repr(result)
                    click.echo("\nRAW RESPONSE:\n" + pretty)
                sys.exit(1)
        else:
            # Build a richer mock (20+ lines) and attach a suggested patch
            mock_file = "entelligence_mock_demo.py"
            buggy_snippet = (
                "import json\n"
                "from typing import List\n"
                "\n"
                "def compute_average(nums=[]):\n"
                '    """Compute average of numbers. BUG: mutable default and zero division.\n'
                '    """\n'
                "    return sum(nums) / len(nums)\n"
                "\n"
                "def load_config(path: str) -> dict:\n"
                '    """BUG: file not closed, no encoding, no error handling."""\n'
                "    f = open(path)\n"
                "    data = json.load(f)\n"
                "    return data\n"
                "\n"
                "def main():\n"
                '    data = load_config("config.json")\n'
                '    scores = data.get("scores", [])\n'
                "    avg = compute_average(scores)\n"
                '    print("Average score: %s" % avg)\n'
                "\n"
                'if __name__ == "__main__":\n'
                "    main()\n"
            )
            fixed_file_content = (
                "import json\n"
                "from typing import List, Optional\n"
                "\n"
                "def compute_average(nums: Optional[List[float]] = None) -> float:\n"
                '    """Compute average safely; avoid mutable defaults and handle empty input."""\n'
                "    if not nums:\n"
                "        return 0.0\n"
                "    return sum(nums) / len(nums)\n"
                "\n"
                "def load_config(path: str) -> dict:\n"
                '    """Read JSON config with proper resource handling and defaults."""\n'
                "    try:\n"
                '        with open(path, "r", encoding="utf-8") as f:\n'
                "            return json.load(f)\n"
                "    except FileNotFoundError:\n"
                "        return {}\n"
                "\n"
                "def main() -> None:\n"
                '    data = load_config("config.json")\n'
                '    scores = data.get("scores", [1, 2, 3, 4, 5])\n'
                "    avg = compute_average(scores)\n"
                '    print(f"Average score: {avg:.2f}")\n'
                "\n"
                'if __name__ == "__main__":\n'
                "    main()\n"
            )
            mock_patch = f"""--- /dev/null
+++ b/{mock_file}
@@
{"".join("+" + line for line in fixed_file_content.splitlines(True))}
"""
            # Second file: a small TS utility with a bug and a fix
            ts_file = "src/utils/math.ts"
            ts_bug = (
                "export function toFixed(num: number, digits: number) {\n"
                "  // BUG: digits not validated; may throw or round incorrectly\n"
                "  return num.toFixed(digits)\n"
                "}\n"
            )
            ts_fix = (
                "export function toFixed(num: number, digits: number): string {\n"
                "  const d = Number.isFinite(digits) && digits >= 0 ? Math.min(20, Math.floor(digits)) : 2;\n"
                "  return num.toFixed(d);\n"
                "}\n"
            )
            ts_patch = f"""--- /dev/null
+++ b/{ts_file}
@@
{"".join("+" + line for line in ts_fix.splitlines(True))}
"""
            # Third file: a README suggestion without an auto-apply patch
            md_file = "README.md"
            md_snippet = (
                "# Project\n\nQuick start instructions are missing installation commands.\n"
            )
            parsed_result = {
                "comments": [
                    {
                        "severity": "error",
                        "file": mock_file,
                        "line": 1,
                        "message": "Multiple issues: mutable default, possible ZeroDivisionError, unclosed file without encoding, and legacy string formatting.",
                        "code_snippet": buggy_snippet
                        if buggy_snippet.endswith("\n")
                        else buggy_snippet + "\n",
                        "language": "python",
                        "suggested_patch": mock_patch,
                        "id": "mock-1",
                    },
                    {
                        "severity": "warning",
                        "file": ts_file,
                        "line": 2,
                        "message": "Validate digits and cap precision; add return type.",
                        "code_snippet": ts_bug if ts_bug.endswith("\n") else ts_bug + "\n",
                        "language": "typescript",
                        "suggested_patch": ts_patch,
                        "id": "mock-2",
                    },
                    {
                        "severity": "suggestion",
                        "file": md_file,
                        "line": 1,
                        "message": "Add install section with \n\n```bash\nnpm i\n```\n",
                        "code_snippet": md_snippet
                        if md_snippet.endswith("\n")
                        else md_snippet + "\n",
                        "language": "markdown",
                        "id": "mock-3",
                    },
                ],
                "summary": {
                    "files_changed": 3,
                    "errors": 1,
                    "warnings": 1,
                    "suggestions": 1,
                },
            }

        if "error" in parsed_result and parsed_result["error"] is not None:
            if output_mode == "prompt-only":
                click.echo(parsed_result["error"])
            else:
                ui.error(parsed_result["error"])
            sys.exit(1)

        # Display results based on output mode
        if output_mode == "prompt-only":
            # Structured output for AI agents
            meta = parsed_result.get("meta", {})
            raw_response = parsed_result.get("raw_response", {})

            # Get prompt - check meta first, then raw_response (top level or in gitdiff_chunks)
            backend_prompt = meta.get("prompt_for_ai_agents_for_addressing_review")

            if not backend_prompt and isinstance(raw_response, dict):
                # Check top level of raw_response
                backend_prompt = raw_response.get("prompt_for_ai_agents_for_addressing_review")
                if not backend_prompt:
                    # Check inside gitdiff_chunks
                    gitdiff_chunks = raw_response.get("gitdiff_chunks_review", [])
                    if isinstance(gitdiff_chunks, list):
                        for item in gitdiff_chunks:
                            if isinstance(item, dict):
                                prompt_from_backend = item.get(
                                    "prompt_for_ai_agents_for_addressing_review"
                                )
                                if prompt_from_backend:
                                    backend_prompt = prompt_from_backend
                                    break

            if backend_prompt:
                click.echo("Prompt for AI Agent:")
                click.echo(backend_prompt)
            else:
                click.echo("No issues found")

        elif output_mode == "plain":
            # Detailed plain text output
            comments = parsed_result.get("comments", [])

            click.echo("\n" + "=" * 80)
            click.echo("REVIEW RESULTS")
            click.echo("=" * 80 + "\n")

            if comments:
                for comment in comments:
                    severity_icon = {
                        "error": "❌",
                        "warning": "⚠️",
                        "info": "ℹ️",
                        "suggestion": "💡",
                    }.get(comment["severity"], "•")

                    click.echo(f"{severity_icon} {comment['severity'].upper()}: {comment['file']}")
                    if comment.get("line"):
                        click.echo(f"   Line: {comment['line']}")
                    click.echo(f"   {comment['message']}")

                    # Committable suggestion (code snippet)
                    if comment.get("code_snippet"):
                        click.echo("\n   Committable Suggestion:")
                        for line in str(comment["code_snippet"]).split("\n"):
                            click.echo(f"     {line}")
                    # Proposed fix (diff) if present
                    if comment.get("suggested_patch"):
                        click.echo("\n   Proposed Fix (diff):")
                        for line in str(comment["suggested_patch"]).split("\n"):
                            click.echo(f"     {line}")
                    # Reasoning if provided
                    extra = comment.get("extra") or {}
                    if extra.get("reasoning"):
                        click.echo("\n   Reasoning:")
                        for line in str(extra.get("reasoning")).split("\n"):
                            click.echo(f"     {line}")
                    # Prompt for AI agents (if provided)
                    if comment.get("ai_prompt") or extra.get("agent_prompt"):
                        prompt_text = comment.get("ai_prompt") or extra.get("agent_prompt")
                        click.echo("\n   Prompt to Fix with AI:")
                        for line in str(prompt_text).split("\n"):
                            click.echo(f"     {line}")

                    click.echo("")

                summary = parsed_result.get("summary", {})
                click.echo("=" * 80)
                click.echo(
                    f"Summary: {summary.get('errors', 0)} errors, "
                    f"{summary.get('warnings', 0)} warnings, "
                    f"{summary.get('suggestions', 0)} suggestions"
                )
                click.echo("=" * 80)
            else:
                # Show review feedback even if no code comments
                meta = parsed_result.get("meta", {})
                has_review_feedback = meta.get("releaseNote") or meta.get("walkthrough_and_changes")

                if has_review_feedback:
                    click.echo("📋 Review Summary:")
                    # Show release note as review feedback
                    if meta.get("releaseNote"):
                        release_note = meta["releaseNote"]
                        # Show first few lines (actionable feedback)
                        lines = release_note.split("\n")
                        for line in lines[:5]:  # First 5 lines
                            if line.strip():
                                click.echo(f"  {line}")
                        if len(lines) > 5:
                            click.echo("  ...")
                    # Show diff if available (for applying changes)
                    if meta.get("pr_diff"):
                        click.echo("\n📝 Diff:")
                        diff_lines = meta["pr_diff"].split("\n")
                        # Show first 20 lines of diff
                        for line in diff_lines[:20]:
                            click.echo(f"  {line}")
                        if len(diff_lines) > 20:
                            click.echo(f"  ... ({len(diff_lines) - 20} more lines)")
                    click.echo("")
                else:
                    click.echo("✓ No code issues found!")

                # Always show file changes summary
                if used_uncommitted:
                    file_stats = git_ops.get_uncommitted_changed_files_with_stats()
                else:
                    file_stats = git_ops.get_changed_files_with_stats(base_branch)

                if file_stats:
                    click.echo(f"📁 Changed files ({len(file_stats)}):")
                    total_add = sum(f.get("additions", 0) for f in file_stats)
                    total_del = sum(f.get("deletions", 0) for f in file_stats)
                    for f in file_stats:
                        add = f.get("additions", 0)
                        del_count = f.get("deletions", 0)
                        click.echo(f"  {f.get('path', '?')}  [+{add}/-{del_count}]")
                    click.echo(f"\n  Total: +{total_add} / -{total_del} lines")

                # Final closing message
                if not comments:
                    summary = parsed_result.get("summary", {})
                    error_count = summary.get("errors", 0)
                    warning_count = summary.get("warnings", 0)
                    if error_count == 0 and warning_count == 0:
                        click.echo("\n" + "=" * 80)
                        click.echo(random.choice(_NO_ISSUES_MESSAGES))
                        click.echo("=" * 80)

        else:  # rich mode
            # Build file stats for interactive review
            if mock:
                file_stats = [
                    {
                        "path": "entelligence_mock_demo.py",
                        "additions": 24,
                        "deletions": 0,
                    },
                    {"path": "src/utils/math.ts", "additions": 4, "deletions": 0},
                    {"path": "README.md", "additions": 0, "deletions": 0},
                ]
            elif pr_diff_override is not None:
                file_stats = git_ops.get_uncommitted_changed_files_with_stats()
            else:
                file_stats = git_ops.get_changed_files_with_stats(base_branch)
            repo_info = {
                "name": repo_name,
                "path": repo_path,
                "branch": current_branch,
                "base": base_branch,
            }
            comments = parsed_result.get("comments", [])
            summary = parsed_result.get("summary", {})
            if comments:
                # Optional: launch Textual files index to pick a file first
                if textual:
                    try:
                        from ..textual_ui import run_textual_files_index

                        selected = run_textual_files_index(file_stats, comments)
                        if selected:
                            comments = [c for c in comments if c.get("file") == selected]
                            # Move selected file to the front
                            file_stats = [f for f in file_stats if f.get("path") == selected] + [
                                f for f in file_stats if f.get("path") != selected
                            ]
                    except Exception:
                        pass

                ui.run_interactive_review(repo_info, file_stats, comments, summary, repo_path)
                # After TUI returns, show closing message based on results
                final_summary = parsed_result.get("summary", {})
                error_count = final_summary.get("errors", 0)
                warning_count = final_summary.get("warnings", 0)
                if error_count == 0 and warning_count == 0:
                    click.echo("")
                    click.echo("=" * 80)
                    click.echo(random.choice(_NO_ISSUES_MESSAGES))
                    click.echo("=" * 80)
            else:
                # No comments found - show closing message
                summary = parsed_result.get("summary", {})
                error_count = summary.get("errors", 0)
                warning_count = summary.get("warnings", 0)
                if error_count == 0 and warning_count == 0:
                    click.echo("")
                    click.echo("=" * 80)
                    click.echo(random.choice(_NO_ISSUES_MESSAGES))
                    click.echo("=" * 80)

    except GitError as e:
        if output_mode == "prompt-only":
            click.echo(f"GIT_ERROR: {str(e)}")
        else:
            ui.error(str(e))
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        if output_mode == "prompt-only":
            click.echo("ERROR: Git command failed")
        else:
            ui.error(f"Git command failed: {e}")
        sys.exit(1)
    except Exception as e:
        if output_mode == "prompt-only":
            click.echo(f"ERROR: {str(e)}")
        else:
            ui.error(f"Failed to run review: {str(e)}")
        sys.exit(1)


@click.command()
@click.option("--file", "-f", required=True, help="File to display diff for")
@click.option("--base-branch", default="main", help="Base branch to compare against")
@click.option("--repo-path", default=".", type=click.Path(exists=True))
def diff(file, base_branch, repo_path):
    """Show diff for a specific file."""
    ui = TerminalUI()
    git_ops = GitOperations(repo_path)

    try:
        diff_content = git_ops.get_file_diff(file, base_branch)
        if not diff_content:
            ui.info(f"No changes in {file}")
            return

        ui.show_diff(file, diff_content)

    except GitError as e:
        ui.error(str(e))
        sys.exit(1)
    except Exception as e:
        ui.error(f"Failed to get diff: {str(e)}")
        raise click.Abort() from e


@click.command()
@click.option("--base-branch", default="main", help="Base branch to compare against")
@click.option("--repo-path", default=".", type=click.Path(exists=True))
def status(base_branch, repo_path):
    """Show status of current branch."""
    ui = TerminalUI()
    ui.show_banner()
    git_ops = GitOperations(repo_path)

    try:
        repo_name = git_ops.get_repo_name()
        current_branch = git_ops.get_current_branch()
        commit_info = git_ops.get_commit_info()
        changed_files = git_ops.get_changed_files(base_branch)
        uncommitted_files = git_ops.get_uncommitted_changed_files()
        changed_with_stats = git_ops.get_changed_files_with_stats(base_branch)
        uncommitted_with_stats = git_ops.get_uncommitted_changed_files_with_stats()

        ui.info(f"Repository: {repo_name}")
        ui.info(f"Branch: {current_branch}")
        ui.info(f"Latest commit: {commit_info['hash'][:8]}")
        ui.info(f"Author: {commit_info['author']}")
        ui.info(f"Message: {commit_info['message']}")

        if changed_files:
            ui.info(f"Committed changes vs base '{base_branch}':")
            ui.show_file_changes_with_stats(
                changed_with_stats
                or [{"path": p, "additions": 0, "deletions": 0} for p in changed_files]
            )
        else:
            ui.info(f"No committed changes vs base '{base_branch}'.")

        if uncommitted_files:
            ui.info("Uncommitted changes (staged & unstaged):")
            ui.show_file_changes_with_stats(
                uncommitted_with_stats
                or [{"path": p, "additions": 0, "deletions": 0} for p in uncommitted_files]
            )
        elif not changed_files:
            ui.info("No uncommitted changes found.")

    except GitError as e:
        ui.error(str(e))
        sys.exit(1)
    except Exception as e:
        ui.error(f"Failed to get status: {str(e)}")
        raise click.Abort() from e
