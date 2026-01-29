"""
TEXT.PROMPT and TEXT.PROMPT.LLM type processors.

TEXT.PROMPT schema:
  individuality:
    prompts:
      system: str
      user: str
      context: str

TEXT.PROMPT.LLM schema:
  individuality:
    model:
      provider: str
      name: str
      temperature: float
      max_tokens: int
    prompts:
      system: str
      user: str
      context: str
    output:
      mime_type: str
      schema: dict
"""
from .base import Processor


class PromptFieldProcessor(Processor):
    """TEXT.PROMPT → any: extract prompts dict."""

    def apply(self, source: dict, target: dict, ref_name: str) -> dict:
        """Return prompts dict from PROMPT cube.

        Returns the prompts object for field-level injection.
        """
        individuality = source.get("individuality_resolved") or source.get("individuality", {})
        return individuality.get("prompts", {})


class PromptLLMProcessor(Processor):
    """TEXT.PROMPT.LLM → TEXT.PROMPT.LLM: return full individuality."""

    def apply(self, source: dict, target: dict, ref_name: str) -> dict:
        """Return full individuality for same-type operations.

        When PROMPT.LLM refs another PROMPT.LLM, return everything
        so the injection can work at any level.
        """
        return source.get("individuality_resolved") or source.get("individuality", {})


# Alias for backwards compatibility
PromptMergeProcessor = PromptLLMProcessor
