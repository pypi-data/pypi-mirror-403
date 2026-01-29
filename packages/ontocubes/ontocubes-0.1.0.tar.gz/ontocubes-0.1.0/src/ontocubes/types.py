"""
TypeSchema - Schema definitions for cube types.
"""
from __future__ import annotations

import json
from typing import ClassVar


class TypeSchema:
    """Schema definition for a cube type. SQLite-backed."""

    _cache: ClassVar[dict[str, TypeSchema]] = {}

    def __init__(self, type_path: str, fields: dict, save: bool = True):
        self.type_path = type_path
        self.fields = fields
        TypeSchema._cache[type_path] = self

        if save:
            from .storage import Storage
            storage = Storage.get()
            storage._conn.execute("""
                INSERT OR REPLACE INTO type_schemas (type_path, fields)
                VALUES (?, ?)
            """, (type_path, json.dumps(fields)))
            storage._conn.commit()

    @classmethod
    def get(cls, type_path: str) -> TypeSchema | None:
        """Get schema for type, or closest parent type."""
        if type_path in cls._cache:
            return cls._cache[type_path]

        from .storage import Storage
        storage = Storage.get()
        row = storage._conn.execute(
            "SELECT * FROM type_schemas WHERE type_path = ?", (type_path,)
        ).fetchone()

        if row:
            schema = cls(row["type_path"], json.loads(row["fields"]), save=False)
            return schema

        # Try parent path
        if "." in type_path:
            parent = ".".join(type_path.split(".")[:-1])
            return cls.get(parent)

        return cls._cache.get("DEFAULT")

    @classmethod
    def register_default(cls):
        """Register default schema for common types."""
        cls("DEFAULT", {
            "prompts": {"type": "object"},
            "model": {"type": "object"},
            "output": {"type": "object"},
            "meta": {"type": "object"},
        })
