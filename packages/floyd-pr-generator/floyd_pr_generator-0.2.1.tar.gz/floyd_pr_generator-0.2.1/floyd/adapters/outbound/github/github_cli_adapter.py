from floyd.application.ports.outbound.pr_repository_port import PRRepositoryPort
from floyd.domain.entities.pull_request import PullRequest
from floyd.adapters.outbound.utils.terminal import Terminal


class GitHubCLIAdapter(PRRepositoryPort):

    def __init__(self, terminal: Terminal):
        self.terminal = terminal

    def pr_exists(self, head_branch: str, base_branch: str) -> bool:
        result = self.terminal.run(
            [
                "gh",
                "pr",
                "list",
                "--head",
                head_branch,
                "--base",
                base_branch,
                "--state",
                "open",
                "--json",
                "number",
                "--jq",
                ".[0].number",
            ]
        )
        return bool(result)

    def create_pr(self, pr: PullRequest, base_branch: str) -> str:
        result = self.terminal.run(
            [
                "gh",
                "pr",
                "create",
                "--title",
                pr.title,
                "--body",
                pr.body,
                "--base",
                base_branch,
            ]
        )
        return result or ""
