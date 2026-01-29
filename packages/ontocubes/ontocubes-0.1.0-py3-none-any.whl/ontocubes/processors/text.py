"""
TEXT type processors.

TEXT schema:
  individuality:
    content: str      # The text content
    encoding: str     # utf-8, ascii, base64
    language: str     # ISO 639-1
    format: str       # plain, markdown, html, json
"""
from .base import Processor


class TextContentProcessor(Processor):
    """TEXT → any: extract content field."""

    def apply(self, source: dict, target: dict, ref_name: str) -> str:
        """Return content from TEXT cube.

        This is the primary extraction for TEXT type.
        Content is injected as string at {{ref}} position.
        """
        individuality = source.get("individuality_resolved") or source.get("individuality", {})
        return individuality.get("content", "")


# Alias for backwards compatibility
TextToPromptProcessor = TextContentProcessor
