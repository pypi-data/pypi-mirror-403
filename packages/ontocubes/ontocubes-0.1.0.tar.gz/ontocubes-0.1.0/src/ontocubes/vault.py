"""
CubeVault - Packaged cube storage (folder or .vault archive).

A CubeVault contains everything needed for ontocubes to work:
- YAML cubes (source of truth)
- SQLite registry (runtime index)
- Custom processors (optional)

Vaults can be:
- Folders (for development)
- .vault archives (for distribution) - ZIP format like .docx

Structure:
    my-prompts.vault (or folder)
    ├── manifest.yaml          # metadata, version, dependencies
    ├── cubes/
    │   ├── types/             # root type cubes
    │   │   ├── text.yaml
    │   │   └── text_prompt_llm.yaml
    │   └── prompts/           # user cubes
    │       └── *.yaml
    ├── processors/            # custom processors (optional)
    │   └── *.py
    └── registry.sqlite        # runtime index (auto-generated)
"""
from __future__ import annotations

import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from .storage import Storage
from .loader import YAMLLoader
from .schema import SchemaDeriver
from .types import TypeSchema

if TYPE_CHECKING:
    from .processors import ProcessorRegistry


class CubeVault:
    """Packaged cube storage - folder or .vault archive.

    Usage:
        # From folder (development)
        vault = CubeVault.from_folder("./cubes")

        # From archive (distribution)
        vault = CubeVault.from_archive("my-prompts.vault")

        # Use with Resolver
        resolver = Resolver(vault=vault)
        result = resolver.resolve("my-prompt")

        # Pack for distribution
        vault.pack("my-prompts.vault")
    """

    VAULT_EXTENSION = ".vault"
    MANIFEST_FILE = "manifest.yaml"
    CUBES_DIR = "cubes"
    PROCESSORS_DIR = "processors"
    REGISTRY_FILE = "registry.sqlite"

    def __init__(self, path: Path, is_archive: bool = False):
        """Initialize vault.

        Args:
            path: Path to folder or .vault file
            is_archive: True if path is a .vault archive
        """
        self._path = Path(path)
        self._is_archive = is_archive
        self._temp_dir: Path | None = None
        self._storage: Storage | None = None
        self._manifest: dict | None = None

        if is_archive:
            self._extract_archive()

    @classmethod
    def from_folder(cls, path: str | Path) -> CubeVault:
        """Create vault from directory structure."""
        path = Path(path)
        if not path.exists():
            raise ValueError(f"Vault folder not found: {path}")
        return cls(path, is_archive=False)

    @classmethod
    def from_archive(cls, path: str | Path) -> CubeVault:
        """Create vault from .vault (ZIP) archive."""
        path = Path(path)
        if not path.exists():
            raise ValueError(f"Vault archive not found: {path}")
        if not path.suffix == cls.VAULT_EXTENSION:
            raise ValueError(f"Expected {cls.VAULT_EXTENSION} file, got: {path.suffix}")
        return cls(path, is_archive=True)

    @classmethod
    def create(cls, path: str | Path, manifest: dict | None = None) -> CubeVault:
        """Create new empty vault folder structure."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        # Create structure
        (path / cls.CUBES_DIR / "types").mkdir(parents=True, exist_ok=True)
        (path / cls.PROCESSORS_DIR).mkdir(exist_ok=True)

        # Write manifest
        manifest = manifest or {
            "name": path.stem,
            "version": "0.1.0",
            "description": "OntoCubes vault",
        }
        with open(path / cls.MANIFEST_FILE, "w") as f:
            yaml.dump(manifest, f)

        return cls(path, is_archive=False)

    def _extract_archive(self):
        """Extract .vault archive to temp directory."""
        self._temp_dir = Path(tempfile.mkdtemp(prefix="ontocubes_"))
        with zipfile.ZipFile(self._path, "r") as zf:
            zf.extractall(self._temp_dir)

    @property
    def root_path(self) -> Path:
        """Get root path (temp dir for archives, original for folders)."""
        if self._is_archive and self._temp_dir:
            return self._temp_dir
        return self._path

    @property
    def cubes_path(self) -> Path:
        """Get path to cubes directory."""
        return self.root_path / self.CUBES_DIR

    @property
    def registry_path(self) -> Path:
        """Get path to SQLite registry."""
        return self.root_path / self.REGISTRY_FILE

    @property
    def manifest(self) -> dict:
        """Get vault manifest."""
        if self._manifest is None:
            manifest_path = self.root_path / self.MANIFEST_FILE
            if manifest_path.exists():
                with open(manifest_path) as f:
                    self._manifest = yaml.safe_load(f) or {}
            else:
                self._manifest = {}
        return self._manifest

    @property
    def storage(self) -> Storage:
        """Get or create Storage for this vault."""
        if self._storage is None:
            # Reset singleton to use our path
            Storage.reset()
            self._storage = Storage.get(self.registry_path)
        return self._storage

    def load(self) -> int:
        """Load all cubes from YAML to SQLite registry.

        Returns count of cubes loaded.
        """
        # Clear caches
        SchemaDeriver.clear_cache()
        TypeSchema._cache.clear()
        TypeSchema.register_default()

        # Load cubes
        if self.cubes_path.exists():
            loader = YAMLLoader(self.cubes_path, self.storage)
            return loader.load()
        return 0

    def reload(self) -> int:
        """Reload all cubes (hot reload)."""
        return self.load()

    def list_cubes(self) -> list[str]:
        """List all cube names in vault."""
        cubes = self.storage.list_all()
        return [c.get("temporal", {}).get("name", c.get("temporal", {}).get("id")) for c in cubes]

    def get_cube(self, name: str) -> dict | None:
        """Get cube by name."""
        uuid = self.storage.resolve_id(name)
        if uuid:
            return self.storage.load(uuid)
        return None

    def pack(self, output: str | Path) -> Path:
        """Pack vault folder into .vault archive.

        Args:
            output: Output path for .vault file

        Returns:
            Path to created archive
        """
        output = Path(output)
        if not output.suffix:
            output = output.with_suffix(self.VAULT_EXTENSION)

        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in self.root_path.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(self.root_path)
                    zf.write(file_path, arcname)

        return output

    @staticmethod
    def unpack(archive: str | Path, output: str | Path) -> Path:
        """Extract .vault archive to folder.

        Args:
            archive: Path to .vault file
            output: Output directory

        Returns:
            Path to extracted folder
        """
        archive = Path(archive)
        output = Path(output)
        output.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(archive, "r") as zf:
            zf.extractall(output)

        return output

    def close(self):
        """Clean up resources (temp directory for archives)."""
        if self._temp_dir and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir)
            self._temp_dir = None
        if self._storage:
            Storage.reset()
            self._storage = None

    def __enter__(self) -> CubeVault:
        return self

    def __exit__(self, *args):
        self.close()

    def __repr__(self) -> str:
        return f"CubeVault({self._path}, archive={self._is_archive})"
