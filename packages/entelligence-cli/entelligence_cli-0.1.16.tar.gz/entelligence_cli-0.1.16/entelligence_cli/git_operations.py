from __future__ import annotations

import re
import subprocess
from pathlib import Path

from .exceptions import GitError


class GitOperations:
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()

    def get_current_branch(self) -> str:
        """Get the name of the current branch."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else ""
            if "not a git repository" in error_msg.lower():
                raise GitError(
                    f"Not a git repository: {self.repo_path}\n"
                    "Please run this command from within a git repository."
                ) from e
            elif "fatal: ambiguous argument 'HEAD'" in error_msg:
                raise GitError(
                    "Git repository has no commits yet.\n"
                    "Please make an initial commit before using this command."
                ) from e
            else:
                raise GitError(
                    f"Failed to get current branch: {error_msg or 'Unknown error'}\n"
                    "Please ensure git is properly configured and you have access to this repository."
                ) from e
        except FileNotFoundError as e:
            raise GitError(
                "Git command not found. Please ensure git is installed and available in your PATH."
            ) from e

    def get_repo_name(self) -> str:
        """Get repository name in owner/repo format from git remote."""
        try:
            result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            remote_url = result.stdout.strip()

            # Parse different Git URL formats
            # SSH: git@github.com:owner/repo.git
            # HTTPS: https://github.com/owner/repo.git
            if remote_url.startswith("git@"):
                # SSH format
                match = re.search(r":([^/]+)/([^/]+?)(?:\.git)?$", remote_url)
                if match:
                    return f"{match.group(1)}/{match.group(2)}"
            elif remote_url.startswith("http"):
                # HTTPS format
                match = re.search(
                    r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$",
                    remote_url,
                )
                if match:
                    return f"{match.group('owner')}/{match.group('repo')}"

            # Fallback: just return the URL
            return remote_url
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else ""
            if "not a git repository" in error_msg.lower():
                raise GitError(
                    f"Not a git repository: {self.repo_path}\n"
                    "Please run this command from within a git repository."
                ) from e
            else:
                raise GitError(
                    f"Failed to get repository name: {error_msg or 'No remote.origin.url configured'}\n"
                    "Please ensure your repository has a remote origin configured."
                ) from e
        except FileNotFoundError as e:
            raise GitError(
                "Git command not found. Please ensure git is installed and available in your PATH."
            ) from e

    def get_unified_diff(self, base_branch: str = "main") -> str:
        """Get unified diff for all changes compared to base branch.

        Uses two-dot syntax (base_branch..HEAD) to compare current branch
        against base branch directly, showing all commits in current branch.
        """
        result = subprocess.run(
            ["git", "diff", f"{base_branch}..HEAD"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout

    def get_commit_hash(self) -> str:
        """Get the current commit hash."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else ""
            if "not a git repository" in error_msg.lower():
                raise GitError(
                    f"Not a git repository: {self.repo_path}\n"
                    "Please run this command from within a git repository."
                ) from e
            elif (
                "fatal: ambiguous argument 'HEAD'" in error_msg
                or "unknown revision" in error_msg.lower()
            ):
                raise GitError(
                    "Git repository has no commits yet.\n"
                    "Please make an initial commit before using this command."
                ) from e
            else:
                raise GitError(
                    f"Failed to get commit hash: {error_msg or 'Unknown error'}\n"
                    "Please ensure git is properly configured and you have access to this repository."
                ) from e
        except FileNotFoundError as e:
            raise GitError(
                "Git command not found. Please ensure git is installed and available in your PATH."
            ) from e

    def get_changed_files(self, base_branch: str = "main") -> list[str]:
        """Get list of files changed compared to base branch."""
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{base_branch}..HEAD"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return [f for f in result.stdout.strip().split("\n") if f]

    def _parse_numstat_output(self, output: str) -> dict[str, dict[str, int]]:
        """
        Parse git --numstat output into a dict mapping file -> {'additions': int, 'deletions': int}.
        Lines are tab-separated: additions<TAB>deletions<TAB>path
        Binary files show '-' for counts; we treat them as 0.
        """
        file_to_stats: dict[str, dict[str, int]] = {}
        for line in (line for line in output.strip().split("\n") if line):
            parts = line.split("\t", 2)
            if len(parts) != 3:
                continue
            add_str, del_str, path = parts
            try:
                additions = int(add_str) if add_str.isdigit() else 0
            except ValueError:
                additions = 0
            try:
                deletions = int(del_str) if del_str.isdigit() else 0
            except ValueError:
                deletions = 0
            file_to_stats[path] = {"additions": additions, "deletions": deletions}
        return file_to_stats

    def get_changed_files_with_stats(self, base_branch: str = "main") -> list[dict[str, int]]:
        """Get list of changed files vs base with additions/deletions per file."""
        result = subprocess.run(
            ["git", "diff", "--numstat", f"{base_branch}..HEAD"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        stats_map = self._parse_numstat_output(result.stdout)
        # Return a stable order by path
        return [
            {"path": p, "additions": s["additions"], "deletions": s["deletions"]}
            for p, s in sorted(stats_map.items())
        ]

    def get_uncommitted_changed_files_with_stats(self) -> list[dict[str, int]]:
        """Get uncommitted (staged & unstaged) changes with additions/deletions per file."""
        unstaged = subprocess.run(
            ["git", "diff", "--numstat"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        staged = subprocess.run(
            ["git", "diff", "--numstat", "--staged"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        unstaged_map = self._parse_numstat_output(unstaged)
        staged_map = self._parse_numstat_output(staged)
        combined: dict[str, dict[str, int]] = {}
        for path, s in unstaged_map.items():
            combined[path] = {"additions": s["additions"], "deletions": s["deletions"]}
        for path, s in staged_map.items():
            if path in combined:
                combined[path]["additions"] += s["additions"]
                combined[path]["deletions"] += s["deletions"]
            else:
                combined[path] = {
                    "additions": s["additions"],
                    "deletions": s["deletions"],
                }
        return [
            {"path": p, "additions": s["additions"], "deletions": s["deletions"]}
            for p, s in sorted(combined.items())
        ]

    def get_file_diff(self, file_path: str, base_branch: str = "main") -> str:
        """Get the diff for a specific file."""
        result = subprocess.run(
            ["git", "diff", f"{base_branch}..HEAD", "--", file_path],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout

    def get_uncommitted_file_diff(self, file_path: str) -> str:
        """Get the uncommitted (staged + unstaged) diff for a specific file."""
        # Unstaged diff for file
        unstaged = subprocess.run(
            ["git", "diff", "--", file_path],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        # Staged diff for file
        staged = subprocess.run(
            ["git", "diff", "--staged", "--", file_path],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        if unstaged and staged:
            return f"{staged}\n{unstaged}"
        return staged or unstaged

    def build_file_diff_array(
        self, files: list[str], base_branch: str = "main", uncommitted: bool = False
    ) -> list[dict[str, str]]:
        """Build a fileDiff array: [{'filePath': str, 'diff': str}, ...], skipping empty diffs."""
        file_diffs: list[dict[str, str]] = []
        for path in files:
            if uncommitted:
                diff = self.get_uncommitted_file_diff(path)
            else:
                diff = self.get_file_diff(path, base_branch)
            if diff and diff.strip():
                file_diffs.append({"filePath": path, "diff": diff})
        return file_diffs

    def get_commit_info(self) -> dict[str, str]:
        """Get information about the latest commit."""
        commit_hash = self.get_commit_hash()
        # Note: The following subprocess calls are intentionally separate for clarity and reliability

        commit_message = subprocess.run(
            ["git", "log", "-1", "--pretty=%B"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        commit_author = subprocess.run(
            ["git", "log", "-1", "--pretty=%an"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        return {"hash": commit_hash, "message": commit_message, "author": commit_author}

    def get_uncommitted_changed_files(self) -> list[str]:
        """Get list of files with uncommitted changes (staged or unstaged)."""
        # Unstaged changes
        unstaged = (
            subprocess.run(
                ["git", "diff", "--name-only"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            .stdout.strip()
            .split("\n")
        )
        # Staged changes
        staged = (
            subprocess.run(
                ["git", "diff", "--name-only", "--staged"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            .stdout.strip()
            .split("\n")
        )
        files = {f for f in unstaged + staged if f}
        return sorted(files)

    def get_uncommitted_unified_diff(self) -> str:
        """Get unified diff for all uncommitted changes (staged and unstaged)."""
        # Unstaged diff
        unstaged = subprocess.run(
            ["git", "diff"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        # Staged diff
        staged = subprocess.run(
            ["git", "diff", "--staged"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        # Concatenate diffs (both are valid unified diffs)
        if unstaged and staged:
            return f"{staged}\n{unstaged}"
        return staged or unstaged

    def build_review_payload(
        self,
        base_branch: str = "main",
        org_uuid: str = "",
        priority_level: str = "medium",
        mode: str = "verbose",
        pr_diff: str = None,
    ) -> dict:
        """Build payload for EntelligenceAI review API."""
        return {
            "prDiff": pr_diff if pr_diff is not None else self.get_unified_diff(base_branch),
            "repoName": self.get_repo_name(),
            "branch": self.get_current_branch(),
            "commitId": self.get_commit_hash(),
            "orgUUID": org_uuid,
            "priorityLevel": priority_level,
            "mode": mode,
            "pr_review_enabled": True,
            "static_scan_enabled": True,
        }
