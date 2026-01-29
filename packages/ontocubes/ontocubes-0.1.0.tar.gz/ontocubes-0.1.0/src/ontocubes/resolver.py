"""
Resolver - Pure orchestrator for cube resolution.

The Resolver finds cubes and delegates ALL transformation to Processors.
It contains NO transformation logic itself.
"""
from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING

from .storage import Storage
from .processors import ProcessorRegistry

if TYPE_CHECKING:
    from .vault import CubeVault

# Pattern for {{ref}} detection
REF_PATTERN = re.compile(r'\{\{([^}]+)\}\}')


class Resolver:
    """
    Pure orchestrator - finds cubes and delegates to processors.

    DOES NOT contain any transformation logic.
    ALL processing is done by Processor classes.
    """

    def __init__(self, vault: "CubeVault | None" = None):
        """Initialize resolver.

        Args:
            vault: Optional CubeVault to use for storage. If None, uses default Storage.
        """
        self._vault = vault
        self._cache: dict[str, dict] = {}

    @property
    def storage(self) -> Storage:
        """Get storage from vault or default."""
        if self._vault:
            return self._vault.storage
        return Storage.get()

    def resolve(self, uuid_or_name: str, payload: dict | None = None,
                _visited: set[str] | None = None) -> dict:
        """
        Resolve cube by UUID or name with optional payload.

        Args:
            uuid_or_name: Cube identifier
            payload: Dict of values to inject as temp cubes
            _visited: Set of visited UUIDs (for circular detection)

        Returns:
            Fully resolved cube dict
        """
        storage = self.storage

        # 1. Register payload as temp cubes
        if payload:
            self._register_payload(payload, storage)

        # 2. Resolve ID
        uuid = storage.resolve_id(uuid_or_name)
        if uuid is None:
            raise ValueError(f"Cube not found: {uuid_or_name}")

        # 3. Circular check
        if _visited is None:
            _visited = set()
        if uuid in _visited:
            raise ValueError(f"Circular reference detected: {uuid_or_name}")
        _visited = _visited | {uuid}

        # Check cache
        if uuid in self._cache:
            return deepcopy(self._cache[uuid])

        # 4. Load caller cube
        caller = storage.load(uuid)
        if caller is None:
            raise ValueError(f"Cube not found after resolve: {uuid}")

        caller_type = self._resolve_typology(caller, storage)
        individuality = caller.get("individuality", {})

        # 5. Find refs and delegate to processors
        refs = self._find_refs(individuality)
        resolved_individuality = deepcopy(individuality)
        warnings = []

        for ref_pattern in refs:
            # Parse ref: "cube-C" or "cube-C.output.schema"
            base_name, path_parts = self._parse_ref(ref_pattern)

            ref_uuid = storage.resolve_id(base_name)
            if ref_uuid is None:
                # Unresolved - leave {{ref}} intact
                warnings.append({
                    "type": "unresolved",
                    "ref": f"{{{{{ref_pattern}}}}}",
                    "source_cube": caller.get("temporal", {}).get("name"),
                })
                continue

            # Recursive resolve
            try:
                ref_cube = self.resolve(ref_uuid, _visited=_visited)
                ref_type = self._resolve_typology(ref_cube, storage)

                # Get value to inject
                if path_parts:
                    # Path ref: extract nested value
                    ref_individuality = ref_cube.get("individuality_resolved") or ref_cube.get("individuality", {})
                    transformed = self._extract_path(ref_individuality, path_parts)
                    if transformed is None:
                        warnings.append({
                            "type": "path_not_found",
                            "ref": f"{{{{{ref_pattern}}}}}",
                            "source_cube": caller.get("temporal", {}).get("name"),
                            "path": ".".join(path_parts),
                        })
                        continue
                else:
                    # Full ref: use processor
                    processor = ProcessorRegistry.get(ref_type, caller_type)
                    if processor:
                        transformed = processor.apply(ref_cube, caller, base_name)
                    else:
                        transformed = ref_cube.get("individuality_resolved") or ref_cube.get("individuality", {})

                resolved_individuality = self._inject(
                    resolved_individuality, ref_pattern, transformed
                )
            except ValueError as e:
                warnings.append({
                    "type": "error",
                    "ref": f"{{{{{ref_pattern}}}}}",
                    "source_cube": caller.get("temporal", {}).get("name"),
                    "error": str(e),
                })

        # Build result
        result = {
            "temporal": caller.get("temporal", {}),
            "typology": caller_type,
            "ontology": caller.get("ontology", {}),
            "causality": caller.get("causality"),
            "individuality": individuality,
            "individuality_resolved": resolved_individuality,
        }

        # Add resolution metadata
        if "meta" not in result["individuality_resolved"]:
            result["individuality_resolved"]["meta"] = {}
        result["individuality_resolved"]["meta"]["resolution"] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "warnings": warnings,
        }

        # Cache result
        self._cache[uuid] = result

        return deepcopy(result)

    def _register_payload(self, payload: dict, storage: Storage):
        """Convert payload items to temp cubes."""
        for name, value in payload.items():
            if isinstance(value, str):
                # String → TEXT cube
                storage.store_temp({
                    "name": name,
                    "typology": "TEXT",
                    "individuality": {"content": value}
                })
            elif isinstance(value, dict):
                if "typology" in value:
                    # Full cube
                    value = deepcopy(value)
                    value.setdefault("name", name)
                    storage.store_temp(value)
                else:
                    # Raw dict → TEXT.DATA
                    storage.store_temp({
                        "name": name,
                        "typology": "TEXT.DATA",
                        "individuality": {"data": value}
                    })

    def _find_refs(self, data: Any) -> list[str]:
        """Find all {{ref}} or {{ref.path}} patterns."""
        try:
            json_str = json.dumps(data)
            matches = REF_PATTERN.findall(json_str)
            # Deduplicate preserving order
            seen = set()
            refs = []
            for ref in matches:
                if ref not in seen:
                    seen.add(ref)
                    refs.append(ref)
            return refs
        except (TypeError, ValueError):
            return []

    def _parse_ref(self, ref: str) -> tuple[str, list[str]]:
        """Parse ref into (base_name, path_parts)."""
        parts = ref.split(".")
        return parts[0], parts[1:]

    def _extract_path(self, data: dict, path: list[str]) -> Any:
        """Extract nested value by path."""
        result = data
        for key in path:
            if isinstance(result, dict) and key in result:
                result = result[key]
            else:
                return None
        return result

    def _resolve_typology(self, cube: dict, storage: Storage) -> str:
        """Resolve actual typology, following causality for '*'."""
        typology = cube.get("typology", "*")

        if typology != "*":
            return typology

        # Walk up causality chain
        causality = cube.get("causality")
        visited = set()

        while causality and causality not in visited:
            visited.add(causality)
            parent = storage.load(causality)
            if parent is None:
                break

            parent_typology = parent.get("typology", "*")
            if parent_typology != "*":
                return parent_typology

            causality = parent.get("causality")

        return "*"

    def _inject(self, data: dict, ref_name: str, value: Any) -> dict:
        """Inject value at {{ref_name}} position."""
        json_str = json.dumps(data)
        pattern = "{{" + ref_name + "}}"

        if isinstance(value, str):
            # Whole value replacement
            json_str = json_str.replace(f'"{pattern}"', json.dumps(value))
            # Inline replacement
            escaped = json.dumps(value)[1:-1]
            json_str = json_str.replace(pattern, escaped)

        elif isinstance(value, dict):
            # Whole value: "{{ref}}" → {object}
            json_str = json_str.replace(f'"{pattern}"', json.dumps(value))
            # Inline: {{ref}} in text → JSON string
            escaped = json.dumps(json.dumps(value))[1:-1]
            json_str = json_str.replace(pattern, escaped)
        else:
            # Other types
            json_str = json_str.replace(f'"{pattern}"', json.dumps(value))
            escaped = json.dumps(str(value))[1:-1]
            json_str = json_str.replace(pattern, escaped)

        return json.loads(json_str)

    def get_expects(self, cube_id: str) -> list[str]:
        """Get unresolved refs (ones not in registry)."""
        storage = self.storage
        uuid = storage.resolve_id(cube_id)
        if uuid is None:
            return []
        cube = storage.load(uuid)
        if cube is None:
            return []
        refs = self._find_refs(cube.get("individuality", {}))
        return [r for r in refs if storage.resolve_id(r) is None]

    def clear_cache(self):
        """Clear resolution cache."""
        self._cache = {}
