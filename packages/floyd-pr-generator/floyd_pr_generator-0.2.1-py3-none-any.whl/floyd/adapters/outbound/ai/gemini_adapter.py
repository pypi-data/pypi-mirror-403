from floyd.adapters.inbound.cli import ui
from floyd.adapters.outbound.ai.ai_adapter import AIAdapter
from floyd.application.dto.ai_config import AIConfig
from floyd.domain.entities.git_context import GitContext
from floyd.domain.entities.pull_request import PullRequest


class GeminiAdapter(AIAdapter):
    def generate_draft(
        self, context: GitContext, config: AIConfig, feedback: str | None = None
    ) -> PullRequest:
        prompt = self._build_prompt(context, config, feedback)

        command = ["gemini"]

        if config.model:
            command.extend(["--model", config.model])
            ui.show_info(f"Gemini is using the model: {config.model}")

        command.extend(["-p", prompt])

        response = self.terminal.run(command, error_msg="Gemini CLI")

        return self._parse_response(response)
