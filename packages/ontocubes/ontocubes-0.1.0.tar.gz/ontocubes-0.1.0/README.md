# ontocubes

Universal ontological cube framework for representing any entity as a 5-layer cube.

## Concept

OntoCubes provides a unified model where **any entity in the world** can be represented as a cube with 5 layers:

| Layer | Purpose | Example |
|-------|---------|---------|
| **Temporal** | Identity & versioning | `id`, `version`, `timestamp`, `name` |
| **Typology** | Type hierarchy | `TEXT.PROMPT.LLM` |
| **Ontology** | Semantic classification | `{"creative/storytelling": 0.95}` |
| **Causality** | Parent/ancestry chain | Reference to parent cube |
| **Individuality** | Actual data (delta from type) | `{prompts: {system: "...", user: "..."}}` |

## Key Features

- **Self-referential**: Same schema in → same schema out
- **Recursive resolution**: `{{ref}}` syntax resolves cubes recursively
- **Type-aware processors**: Transform data between types (TEXT → PROMPT)
- **Schema validation**: Root cubes define schemas for their type hierarchy
- **SQLite persistence**: Fast lookup with YAML as source of truth

## Status

🚧 **Under Development** - API may change

## Installation

```bash
pip install ontocubes
```

## Quick Example

```python
from ontocubes import Storage, Resolver

# Store a cube
storage = Storage.get()
storage.store({
    "name": "greeting",
    "typology": "TEXT",
    "individuality": {"content": "Hello, World!"}
})

# Resolve with refs
storage.store({
    "name": "prompt",
    "typology": "TEXT.PROMPT.LLM",
    "individuality": {
        "prompts": {
            "system": "{{greeting}}",  # Resolves to "Hello, World!"
            "user": ""
        }
    }
})

resolver = Resolver()
result = resolver.resolve("prompt")
print(result["individuality_resolved"]["prompts"]["system"])
# Output: Hello, World!
```

## License

MIT
