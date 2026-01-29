"""
Schema derivation and validation.

SchemaDeriver: Derives JSON Schema from root cube structure (Living Prototype)
SchemaValidator: Validates cubes against derived schemas
"""
from __future__ import annotations

import logging
from enum import Enum
from typing import Any, ClassVar, TYPE_CHECKING

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    logging.warning("jsonschema not installed - validation disabled. pip install jsonschema")

if TYPE_CHECKING:
    from .storage import Storage


class SchemaDeriver:
    """Derives JSON Schema from root cube structure.

    The root cube IS the prototype - its structure defines
    what instances must look like.

    Derivation Rules:
        null        → Optional field (any type)
        ""          → Required string (must provide)
        "value"     → Optional string, default="value"
        0           → Required integer (explicit zero)
        123         → Optional integer, default=123
        0.0         → Required number (explicit zero)
        0.7         → Optional number, default=0.7
        true/false  → Optional boolean
        {}          → Optional object, any properties
        []          → Required array (must provide)
        {nested}    → Recurse into nested structure
    """

    _cache: ClassVar[dict[str, dict]] = {}  # typology -> derived schema

    @classmethod
    def derive(cls, root_cube: dict) -> dict:
        """Derive JSON Schema from root cube's structure."""
        typology = root_cube.get("typology", "*")

        # Check cache
        if typology in cls._cache:
            return cls._cache[typology]

        # Derive schema from structure
        schema = cls._derive_object(root_cube, is_root=True)

        # Cache and return
        cls._cache[typology] = schema
        return schema

    @classmethod
    def _derive_object(cls, obj: dict, is_root: bool = False) -> dict:
        """Derive schema for an object."""
        schema = {"type": "object", "properties": {}, "required": []}

        for key, value in obj.items():
            # Skip metadata fields in root cube definition
            if is_root and key in ("is_type_root", "name", "version"):
                continue

            prop_schema, required = cls._derive_value(value)
            schema["properties"][key] = prop_schema

            if required:
                schema["required"].append(key)

        # Remove empty required list
        if not schema["required"]:
            del schema["required"]

        return schema

    @classmethod
    def _derive_value(cls, value: Any) -> tuple[dict, bool]:
        """Derive schema for a value. Returns (schema, is_required)."""

        if value is None:
            # null = optional, any type
            return {}, False

        if isinstance(value, str):
            schema = {"type": "string"}
            if value:
                # Non-empty string = optional with default
                schema["default"] = value
                return schema, False
            else:
                # Empty string = REQUIRED
                return schema, True

        if isinstance(value, bool):
            # Must check bool before int (bool is subclass of int)
            # Boolean with default = optional
            return {"type": "boolean", "default": value}, False

        if isinstance(value, int):
            schema = {"type": "integer"}
            if value == 0:
                # Explicit zero = required
                return schema, True
            else:
                # Non-zero = optional with default
                schema["default"] = value
                return schema, False

        if isinstance(value, float):
            schema = {"type": "number"}
            if value == 0.0:
                # Explicit zero = required
                return schema, True
            else:
                # Non-zero = optional with default
                schema["default"] = value
                return schema, False

        if isinstance(value, list):
            # [] = required array (must provide)
            return {"type": "array"}, True

        if isinstance(value, dict):
            if not value:
                # {} = optional object, any properties
                return {"type": "object"}, False
            else:
                # {nested} = recurse, required if has required children
                nested_schema = cls._derive_object(value)
                has_required = bool(nested_schema.get("required"))
                return nested_schema, has_required

        # Unknown type - optional, any type
        return {}, False

    @classmethod
    def clear_cache(cls):
        """Clear derived schema cache (call on reload)."""
        cls._cache.clear()


class ValidationMode(Enum):
    """Validation mode for schema checking."""
    DISABLED = "disabled"
    WARN = "warn"
    STRICT = "strict"  # DEFAULT


class ValidationResult:
    """Result of schema validation."""

    def __init__(self, valid: bool, errors: list[str] | None = None,
                 cube_name: str | None = None, typology: str | None = None):
        self.valid = valid
        self.errors = errors or []
        self.cube_name = cube_name
        self.typology = typology

    def __str__(self) -> str:
        if self.valid:
            return f"✓ Cube '{self.cube_name}' ({self.typology}) is valid"
        lines = [f"✗ Validation failed for cube '{self.cube_name}' ({self.typology}):"]
        for i, err in enumerate(self.errors, 1):
            lines.append(f"  {i}. {err}")
        return "\n".join(lines)

    def __bool__(self) -> bool:
        return self.valid


class SchemaValidator:
    """Validates cubes against schema derived from root type cubes.

    Root cubes are NOT validated - they ARE the schema source.
    """

    _mode: ClassVar[ValidationMode] = ValidationMode.STRICT

    @classmethod
    def set_mode(cls, mode: ValidationMode | str):
        """Set validation mode."""
        if isinstance(mode, str):
            mode = ValidationMode(mode)
        cls._mode = mode

    @classmethod
    def validate(cls, cube: dict, storage: "Storage") -> ValidationResult:
        """Validate cube against its type's root cube schema.

        Root cubes are NOT validated - they ARE the schema source.
        """
        if cls._mode == ValidationMode.DISABLED:
            return ValidationResult(valid=True)

        if not HAS_JSONSCHEMA:
            return ValidationResult(valid=True)  # Skip if no jsonschema

        # Root cubes define schemas - skip validation
        if cube.get("is_type_root"):
            return ValidationResult(valid=True)

        cube_name = cube.get("name") or cube.get("temporal", {}).get("name", "<unnamed>")
        typology = cube.get("typology", "*")

        # Find root cube for this typology
        root_cube = cls._find_root_cube(typology, storage)
        if root_cube is None:
            # No root cube found - allow (lenient mode for untyped cubes)
            return ValidationResult(valid=True, cube_name=cube_name, typology=typology)

        # Derive schema from root cube
        schema = SchemaDeriver.derive(root_cube)

        # Validate using jsonschema
        validator = jsonschema.Draft7Validator(schema)
        errors = []

        for error in validator.iter_errors(cube):
            path = " → ".join(str(p) for p in error.absolute_path) or "(root)"
            errors.append(f"[{path}] {error.message}")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            cube_name=cube_name,
            typology=typology
        )

    @classmethod
    def _find_root_cube(cls, typology: str, storage: "Storage") -> dict | None:
        """Find root cube for typology, walking up type hierarchy."""
        if not typology or typology == "*":
            return None

        parts = typology.split(".")

        for i in range(len(parts), 0, -1):
            type_path = ".".join(parts[:i])
            # Query for root cube with this typology
            row = storage._conn.execute(
                "SELECT * FROM cubes WHERE typology = ? AND is_type_root = 1",
                (type_path,)
            ).fetchone()
            if row:
                return storage._row_to_cube(row)

        return None
