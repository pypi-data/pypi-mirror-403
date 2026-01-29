"""
ProcessorRegistry - Maps (source_type, target_type) pairs to Processors.
"""
from typing import ClassVar, Optional
from .base import Processor


class ProcessorRegistry:
    """Registry of processors by (source_type, target_type) pair."""

    _processors: ClassVar[dict[tuple[str, str], Processor]] = {}

    @classmethod
    def register(cls, source_type: str, target_type: str, processor: Processor):
        """Register a processor for a type pair."""
        cls._processors[(source_type, target_type)] = processor

    @classmethod
    def get(cls, source_type: str, target_type: str) -> Optional[Processor]:
        """Get processor for type pair with hierarchy fallback.

        Lookup order:
        1. Exact match (source_type, target_type)
        2. Parent types (TEXT.PROMPT.LLM → TEXT.PROMPT → TEXT → *)
        3. Fallback ("*", "*")
        """
        # Exact match
        if (source_type, target_type) in cls._processors:
            return cls._processors[(source_type, target_type)]

        # Try parent types
        for src in cls._type_hierarchy(source_type):
            for tgt in cls._type_hierarchy(target_type):
                if (src, tgt) in cls._processors:
                    return cls._processors[(src, tgt)]

        # Fallback
        return cls._processors.get(("*", "*"))

    @classmethod
    def _type_hierarchy(cls, type_path: str) -> list[str]:
        """Return type and all parent types.

        Example: TEXT.PROMPT.LLM → [TEXT.PROMPT.LLM, TEXT.PROMPT, TEXT, *]
        """
        parts = type_path.split(".")
        result = []
        for i in range(len(parts), 0, -1):
            result.append(".".join(parts[:i]))
        result.append("*")
        return result

    @classmethod
    def list_all(cls) -> list[tuple[str, str, str]]:
        """List all registered processors."""
        return [
            (src, tgt, type(proc).__name__)
            for (src, tgt), proc in cls._processors.items()
        ]

    @classmethod
    def clear(cls):
        """Clear all registered processors."""
        cls._processors.clear()
