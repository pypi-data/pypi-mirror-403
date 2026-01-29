"""
OntoCubes - Universal ontological cube framework.

Represent any entity as a 5-layer cube:
- Temporal: identity & versioning
- Typology: type hierarchy
- Ontology: semantic classification
- Causality: parent/ancestry chain
- Individuality: actual data (delta from type)

Quick Start:
    from ontocubes import CubeVault, Resolver

    # Load vault
    vault = CubeVault.from_folder("./cubes")
    vault.load()

    # Resolve with payload
    resolver = Resolver(vault=vault)
    result = resolver.resolve("my-prompt", payload={"user": "Alice"})

    print(result["individuality_resolved"])
"""

__version__ = "0.1.0"

# Core classes
from .storage import Storage
from .resolver import Resolver
from .vault import CubeVault
from .loader import YAMLLoader

# Types and schema
from .types import TypeSchema
from .schema import (
    SchemaDeriver,
    SchemaValidator,
    ValidationMode,
    ValidationResult,
)

# Processors
from .processors import (
    ProcessorRegistry,
    Processor,
    SubprocessProcessor,
    APIProcessor,
    TextContentProcessor,
    PromptFieldProcessor,
    PromptLLMProcessor,
    SchemaExtractProcessor,
    DefaultProcessor,
    register_default_processors,
)

__all__ = [
    # Version
    "__version__",
    # Core
    "Storage",
    "Resolver",
    "CubeVault",
    "YAMLLoader",
    # Types & Schema
    "TypeSchema",
    "SchemaDeriver",
    "SchemaValidator",
    "ValidationMode",
    "ValidationResult",
    # Processors
    "ProcessorRegistry",
    "Processor",
    "SubprocessProcessor",
    "APIProcessor",
    "TextContentProcessor",
    "PromptFieldProcessor",
    "PromptLLMProcessor",
    "SchemaExtractProcessor",
    "DefaultProcessor",
    "register_default_processors",
]
