from abc import ABC, abstractmethod

from floyd.application.dto.ai_config import AIConfig
from floyd.domain.entities.git_context import GitContext
from floyd.domain.entities.pull_request import PullRequest


class AIServicePort(ABC):

    @abstractmethod
    def generate_draft(
        self,
        context: GitContext,
        config: AIConfig,
        feedback: str | None = None,
    ) -> PullRequest:
        ...
