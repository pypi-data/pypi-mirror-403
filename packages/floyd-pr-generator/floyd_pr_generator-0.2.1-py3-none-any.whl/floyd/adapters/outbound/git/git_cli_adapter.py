import subprocess

from floyd.application.ports.outbound.git_repository_port import GitRepositoryPort
from floyd.adapters.outbound.utils.terminal import Terminal


class GitCLIAdapter(GitRepositoryPort):

    def __init__(self, terminal: Terminal):
        self.terminal = terminal

    def is_git_repo(self) -> bool:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    def branch_exists(self, branch_name: str) -> bool:
        result = subprocess.run(
            ["git", "ls-remote", "--exit-code", "--heads", "origin", branch_name],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    def get_current_branch(self) -> str:
        result = self.terminal.run(["git", "branch", "--show-current"])
        return result or ""

    def get_commits(self, base_branch: str) -> str:
        result = self.terminal.run(
            ["git", "log", f"{base_branch}..HEAD", "--oneline"]
        )
        return result or ""

    def get_diff(self, base_branch: str) -> str:
        result = self.terminal.run(
            [
                "git",
                "diff",
                "--merge-base",
                base_branch,
                ":!*.lock",
                ":!*-lock.json",
            ]
        )
        return result or ""

    def get_diff_stat(self, base_branch: str) -> str:
        result = self.terminal.run(
            [
                "git",
                "diff",
                "--stat",
                "--merge-base",
                base_branch,
                ":!*.lock",
                ":!*-lock.json",
            ]
        )
        return result or ""
