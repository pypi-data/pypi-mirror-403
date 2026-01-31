from pydantic import BaseModel, Field

from floyd.domain.value_objects.ai_provider import ProviderType


class AIConfig(BaseModel):
    provider: ProviderType
    model: str = Field(default="")
    diff_limit: int = Field(default=-1)
    instructions: str = Field(default="")
