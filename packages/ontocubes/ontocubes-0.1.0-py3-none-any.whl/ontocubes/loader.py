"""
YAMLLoader - Sync YAML cubes to SQLite registry.

YAML files are the source of truth. YAMLLoader syncs them
to SQLite for fast runtime lookup.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from .storage import Storage
from .types import TypeSchema
from .schema import SchemaDeriver

if TYPE_CHECKING:
    pass


class YAMLLoader:
    """Load YAML cubes and sync to SQLite.

    Supports both short and full layer names:
        t/temporal, y/typology, o/ontology, c/causality, i/individuality
    """

    # Short → Full name mapping
    SHORT_TO_FULL = {
        "t": "temporal",
        "y": "typology",
        "o": "ontology",
        "c": "causality",
        "i": "individuality",
    }

    def __init__(self, cubes_dir: Path | str, storage: Storage | None = None):
        self.cubes_dir = Path(cubes_dir)
        self.storage = storage or Storage.get()

    def _normalize_cube(self, cube: dict) -> dict:
        """Normalize short keys to full layer names."""
        result = {}

        for key, value in cube.items():
            # Map short keys to full names
            full_key = self.SHORT_TO_FULL.get(key, key)

            # Handle 't: {name: xyz}' → extract name to top level
            if full_key == "temporal" and isinstance(value, dict):
                if "name" in value:
                    result["name"] = value["name"]
                # Copy other temporal fields if any
                for tk, tv in value.items():
                    if tk != "name":
                        result.setdefault("temporal", {})[tk] = tv
            else:
                result[full_key] = value

        return result

    def load(self) -> int:
        """Load all YAML files from directory.

        Returns count of cubes loaded.
        """
        count = 0
        yaml_files = list(self.cubes_dir.rglob("*.yaml"))

        # Sort to load types/ first (root cubes)
        yaml_files.sort(key=lambda p: (0 if "types" in str(p) else 1, str(p)))

        for yaml_file in yaml_files:
            count += self._load_file(yaml_file)

        return count

    def _load_file(self, path: Path) -> int:
        """Load single YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)

        if not data:
            return 0

        # Handle single cube or list
        cubes = data if isinstance(data, list) else [data]
        count = 0

        for cube_def in cubes:
            # Normalize short keys to full names
            cube_def = self._normalize_cube(cube_def)

            # Resolve parent reference
            if cube_def.get("causality"):
                parent_id = self.storage.resolve_id(cube_def["causality"])
                if parent_id:
                    cube_def["causality"] = parent_id

            # Check if root type cube
            is_type_root = cube_def.get("is_type_root", False)
            if is_type_root:
                self._register_type_schema(cube_def)

            # Root cubes skip validation (they ARE the schema)
            self.storage.store(cube_def, validate=not is_type_root)
            count += 1

        return count

    def _register_type_schema(self, cube_def: dict):
        """Register TypeSchema from root cube."""
        type_path = cube_def.get("typology")
        individuality = cube_def.get("individuality", {})
        schema = individuality.get("schema", {})
        version = individuality.get("version", "1.0.0")

        if type_path and schema:
            TypeSchema(type_path, {
                "schema": schema,
                "version": version
            })

    def reload(self) -> int:
        """Reload all cubes (hot reload).

        Clears schema cache to pick up root cube changes.
        """
        SchemaDeriver.clear_cache()
        TypeSchema._cache.clear()
        TypeSchema.register_default()
        return self.load()
