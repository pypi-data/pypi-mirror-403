from abc import ABC
from floyd.adapters.outbound.utils.terminal import Terminal
from floyd.application.dto.ai_config import AIConfig
from floyd.application.ports.outbound.ai_service_port import AIServicePort
from floyd.domain.entities.git_context import GitContext
from floyd.domain.entities.pull_request import PullRequest
from floyd.domain.exceptions.pr.pr_generation_exception import PRGenerationException


class AIAdapter(AIServicePort, ABC):

    def __init__(self, terminal: Terminal):
        self.terminal = terminal

    def _build_prompt(
        self,
        context: GitContext,
        config: AIConfig,
        feedback: str | None = None,
    ) -> str:
        diff = context.diff

        if config.diff_limit > 0 and len(diff) > config.diff_limit:
            diff = (
                diff[: config.diff_limit]
                + "\n\n[... DIFF TRUNCATED FOR TOKEN LIMITS ...]"
            )

        extra_prompt = ""
        if config.instructions:
            extra_prompt = f"\nUSER-SPECIFIC INSTRUCTIONS:\n{config.instructions}\n"

        feedback_section = ""
        if feedback:
            feedback_section = f"\nUSER FEEDBACK FOR REFINEMENT:\n{feedback}\n"

        prompt = (
            f"Context:\n"
            f"- Working on branch: {context.current_branch.name}\n"
            f"- Target branch: {context.target_branch.name}\n"
            f"- Recent commits:\n{context.commits}\n\n"
            f"- File Change Summary:\n{context.diff_stat}\n\n"
            f"Task: Review the git diff below and write a PR title and description. "
            f"TITLE CONVENTION: Use conventional commits for the title "
            f"(e.g., feat: [title], fix: [title], docs: [title]).\n\n"
            f"Use the commit history to understand the intent behind the changes.\n\n"
            f"{extra_prompt}"
            f"{feedback_section}"
            f"IMPORTANT: Do not include any signatures, footers, or mentions of "
            f"being 'Generated with Claude Code' or any other tool.\n\n"
            f"Format your response exactly like this:\n"
            f"TITLE: [Your Title]\n"
            f"BODY: [Your Description]\n\n"
            f"Diff:\n{diff}"
        )

        return prompt

    def _parse_response(self, response: str) -> PullRequest:
        try:
            title = response.split("TITLE:")[1].split("BODY:")[0].strip()
            body = response.split("BODY:")[1].strip()

            if not title or not body:
                raise PRGenerationException("AI response missing title or body")

            return PullRequest(title=title, body=body)

        except (IndexError, AttributeError) as e:
            raise PRGenerationException(f"Failed to parse AI response: {e}") from e
