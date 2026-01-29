"""
TEXT.SCHEMA type processors.

TEXT.SCHEMA schema:
  individuality:
    output:
      schema:
        type: str
        properties: dict
        required: list
        ...
"""
from .base import Processor


class SchemaExtractProcessor(Processor):
    """TEXT.SCHEMA → any: extract output.schema."""

    def apply(self, source: dict, target: dict, ref_name: str) -> dict:
        """Return the schema object from TEXT.SCHEMA cube.

        Extracts individuality.output.schema for direct injection.
        Use this when target expects a schema object.
        """
        individuality = source.get("individuality_resolved") or source.get("individuality", {})
        output = individuality.get("output", {})
        return output.get("schema", {})


class SchemaWrapProcessor(Processor):
    """TEXT.SCHEMA → TEXT.PROMPT.LLM: wrap schema for output.schema field."""

    def apply(self, source: dict, target: dict, ref_name: str) -> dict:
        """Wrap source schema in output.schema structure.

        Returns {"output": {"schema": {...}}} for deep merge.
        Use when you want to merge schema into target's output.schema.
        """
        individuality = source.get("individuality_resolved") or source.get("individuality", {})
        output = individuality.get("output", {})
        schema = output.get("schema", {})
        return {"output": {"schema": schema}}


# Alias for backwards compatibility
SchemaMergeProcessor = SchemaExtractProcessor
