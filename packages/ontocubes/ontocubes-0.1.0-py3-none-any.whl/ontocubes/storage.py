"""
Storage - SQLite-backed cube registry with temp cube support.

The Storage is the runtime registry for cubes. YAML files are the source
of truth, but Storage provides fast lookup during resolution.
"""
from __future__ import annotations

import json
import sqlite3
import uuid as uuid_lib
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, ClassVar


def init_database(db_path: Path) -> sqlite3.Connection:
    """Initialize SQLite database with required tables."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    conn.executescript("""
        -- Cubes table
        CREATE TABLE IF NOT EXISTS cubes (
            uuid TEXT PRIMARY KEY,
            name TEXT UNIQUE,
            version INTEGER DEFAULT 1,
            timestamp TEXT,
            typology TEXT,
            ontology TEXT,  -- JSON
            causality TEXT,  -- parent uuid
            individuality TEXT,  -- JSON
            is_type_root INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_cubes_name ON cubes(name);
        CREATE INDEX IF NOT EXISTS idx_cubes_typology ON cubes(typology);

        -- Type schemas table
        CREATE TABLE IF NOT EXISTS type_schemas (
            type_path TEXT PRIMARY KEY,
            fields TEXT,  -- JSON
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    return conn


class Storage:
    """Single source of truth for all cube data. SQLite-backed with temp support."""

    _instance: ClassVar[Storage | None] = None
    _db_path: ClassVar[Path | None] = None

    def __init__(self, db_path: Path):
        self._db_path = db_path
        self._conn = init_database(db_path)
        self._temp: dict[str, Any] = {}  # In-memory temp cubes

    @classmethod
    def get(cls, db_path: Path | str | None = None) -> Storage:
        """Get or create Storage singleton."""
        if db_path is not None:
            db_path = Path(db_path)

        if cls._instance is None:
            if db_path is None:
                db_path = Path("registry.sqlite")
            cls._instance = cls(db_path)
        return cls._instance

    @classmethod
    def reset(cls):
        """Reset the singleton instance."""
        if cls._instance:
            cls._instance._conn.close()
        cls._instance = None

    def store(self, data: dict, uuid: str | None = None, validate: bool = True) -> str:
        """Store cube to SQLite (persistent).

        Args:
            data: Cube data dict
            uuid: Optional UUID (generated if None)
            validate: If True, validate against root type cube schema
        """
        # Import here to avoid circular import
        from .schema import SchemaValidator, ValidationMode

        if uuid is None:
            uuid = str(uuid_lib.uuid4())
        data = deepcopy(data)

        # Ensure temporal is a dict (handle temporal: null from YAML)
        if "temporal" not in data or data["temporal"] is None:
            data["temporal"] = {}
        data["temporal"]["id"] = uuid
        data["temporal"].setdefault("version", 1)
        data["temporal"].setdefault("timestamp", datetime.now(timezone.utc).isoformat())

        # Support name in root or temporal.name
        if "name" in data and "name" not in data["temporal"]:
            data["temporal"]["name"] = data.pop("name")

        name = data["temporal"].get("name")
        version = data["temporal"].get("version", 1)
        timestamp = data["temporal"].get("timestamp")
        typology = data.get("typology", "*")
        ontology = json.dumps(data.get("ontology", {}))
        causality = data.get("causality")
        individuality = json.dumps(data.get("individuality", {}))
        is_type_root = 1 if data.get("is_type_root") else 0

        # Validate against root type cube schema
        if validate and not data.get("is_type_root"):
            result = SchemaValidator.validate(data, self)
            if not result.valid:
                import logging
                if SchemaValidator._mode == ValidationMode.STRICT:
                    raise ValueError(str(result))
                elif SchemaValidator._mode == ValidationMode.WARN:
                    logging.warning(str(result))

        self._conn.execute("""
            INSERT OR REPLACE INTO cubes
            (uuid, name, version, timestamp, typology, ontology, causality, individuality, is_type_root)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (uuid, name, version, timestamp, typology, ontology, causality, individuality, is_type_root))
        self._conn.commit()

        return uuid

    def store_temp(self, data: dict) -> str:
        """Store temporary cube (in-memory only, not persisted)."""
        uuid = str(uuid_lib.uuid4())
        data = deepcopy(data)

        # Ensure temporal is a dict (handle temporal: null from YAML)
        if "temporal" not in data or data["temporal"] is None:
            data["temporal"] = {}
        data["temporal"]["id"] = uuid
        data["temporal"]["is_temp"] = True
        data["temporal"].setdefault("version", 1)
        data["temporal"].setdefault("timestamp", datetime.now(timezone.utc).isoformat())

        if "name" in data and "name" not in data["temporal"]:
            data["temporal"]["name"] = data.pop("name")

        name = data["temporal"].get("name")

        # Store in memory only
        self._temp[uuid] = data
        if name:
            self._temp[f"name:{name}"] = uuid

        return uuid

    def clear_temp(self):
        """Clear all temporary cubes."""
        self._temp = {}

    def load(self, uuid: str) -> dict | None:
        """Load cube by UUID (check temp first)."""
        # Check temp first
        if uuid in self._temp:
            return deepcopy(self._temp[uuid])

        # SQLite lookup
        row = self._conn.execute(
            "SELECT * FROM cubes WHERE uuid = ?", (uuid,)
        ).fetchone()

        if not row:
            return None

        return self._row_to_cube(row)

    def resolve_id(self, uuid_or_name: str) -> str | None:
        """Resolve name to UUID (check temp first)."""
        # Check temp by name
        temp_key = f"name:{uuid_or_name}"
        if temp_key in self._temp:
            return self._temp[temp_key]
        if uuid_or_name in self._temp:
            return uuid_or_name

        # Check by UUID
        row = self._conn.execute(
            "SELECT uuid FROM cubes WHERE uuid = ?", (uuid_or_name,)
        ).fetchone()
        if row:
            return row["uuid"]

        # Check by name
        row = self._conn.execute(
            "SELECT uuid FROM cubes WHERE name = ?", (uuid_or_name,)
        ).fetchone()
        if row:
            return row["uuid"]

        return None

    def _row_to_cube(self, row: sqlite3.Row) -> dict:
        """Convert database row to cube dict."""
        return {
            "temporal": {
                "id": row["uuid"],
                "name": row["name"],
                "version": row["version"],
                "timestamp": row["timestamp"],
            },
            "typology": row["typology"],
            "ontology": json.loads(row["ontology"]) if row["ontology"] else {},
            "causality": row["causality"],
            "individuality": json.loads(row["individuality"]) if row["individuality"] else {},
            "is_type_root": bool(row["is_type_root"]) if "is_type_root" in row.keys() else False,
        }

    def list_all(self) -> list[dict]:
        """List all cubes (persistent only)."""
        rows = self._conn.execute("SELECT * FROM cubes ORDER BY name").fetchall()
        return [self._row_to_cube(row) for row in rows]
