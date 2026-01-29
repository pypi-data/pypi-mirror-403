"""
Processors package - Type-pair transformations for cube resolution.

Architecture:
- Resolver = pure orchestrator (finds cubes, delegates to processors)
- Processors = all transformation logic (knows type schemas)

Type Hierarchy:
  TEXT                    # content: str
  TEXT.PROMPT             # prompts: {system, user, context}
  TEXT.PROMPT.LLM         # prompts + model + output
  TEXT.SCHEMA             # output.schema: JSON Schema object

Processor Matrix:
  Source → Target         | Processor              | Returns
  ------------------------|------------------------|------------------
  TEXT → any              | TextContentProcessor   | content (str)
  TEXT.PROMPT → any       | PromptFieldProcessor   | prompts (dict)
  TEXT.PROMPT.LLM → same  | PromptLLMProcessor     | individuality (dict)
  TEXT.SCHEMA → any       | SchemaExtractProcessor | output.schema (dict)
  * → *                   | DefaultProcessor       | individuality (dict)
"""
from .registry import ProcessorRegistry
from .base import Processor, SubprocessProcessor, APIProcessor
from .text import TextContentProcessor, TextToPromptProcessor
from .prompt import PromptFieldProcessor, PromptLLMProcessor, PromptMergeProcessor
from .schema import SchemaExtractProcessor, SchemaWrapProcessor, SchemaMergeProcessor
from .default import DefaultProcessor


def register_default_processors():
    """Register default processor matrix."""
    # TEXT → any: extract content
    ProcessorRegistry.register("TEXT", "TEXT", TextContentProcessor())
    ProcessorRegistry.register("TEXT", "TEXT.PROMPT", TextContentProcessor())
    ProcessorRegistry.register("TEXT", "TEXT.PROMPT.LLM", TextContentProcessor())
    ProcessorRegistry.register("TEXT", "TEXT.SCHEMA", TextContentProcessor())

    # TEXT.PROMPT → any: extract prompts
    ProcessorRegistry.register("TEXT.PROMPT", "TEXT.PROMPT", PromptFieldProcessor())
    ProcessorRegistry.register("TEXT.PROMPT", "TEXT.PROMPT.LLM", PromptFieldProcessor())

    # TEXT.PROMPT.LLM → same: full individuality
    ProcessorRegistry.register("TEXT.PROMPT.LLM", "TEXT.PROMPT.LLM", PromptLLMProcessor())

    # TEXT.SCHEMA → any: extract output.schema
    ProcessorRegistry.register("TEXT.SCHEMA", "TEXT.SCHEMA", SchemaExtractProcessor())
    ProcessorRegistry.register("TEXT.SCHEMA", "TEXT.PROMPT", SchemaExtractProcessor())
    ProcessorRegistry.register("TEXT.SCHEMA", "TEXT.PROMPT.LLM", SchemaExtractProcessor())

    # Fallback: no heuristics, returns raw individuality
    ProcessorRegistry.register("*", "*", DefaultProcessor())


# Auto-register on import
register_default_processors()


__all__ = [
    # Registry
    "ProcessorRegistry",
    "register_default_processors",
    # Base classes
    "Processor",
    "SubprocessProcessor",
    "APIProcessor",
    # TEXT processors
    "TextContentProcessor",
    "TextToPromptProcessor",
    # PROMPT processors
    "PromptFieldProcessor",
    "PromptLLMProcessor",
    "PromptMergeProcessor",
    # SCHEMA processors
    "SchemaExtractProcessor",
    "SchemaWrapProcessor",
    "SchemaMergeProcessor",
    # Fallback
    "DefaultProcessor",
]
