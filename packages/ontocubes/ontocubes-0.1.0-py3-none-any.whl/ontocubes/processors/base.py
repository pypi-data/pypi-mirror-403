"""
Base Processor classes for type-pair transformations.

Processors contain ALL transformation logic.
Resolver only orchestrates - processors do the work.
"""
from abc import ABC, abstractmethod
from typing import Any
import subprocess
import json


class Processor(ABC):
    """
    Base class for type-pair processors.

    Processors contain ALL transformation logic.
    Resolver only orchestrates - processors do the work.

    Types of processors:
    - Processor: Python class (fast, same process)
    - SubprocessProcessor: Calls external script
    - APIProcessor: Calls external HTTP service
    """

    @abstractmethod
    def apply(self, source: dict, target: dict, ref_name: str) -> Any:
        """Transform source for injection into target.

        Args:
            source: Resolved source cube (full cube dict)
            target: Caller cube being built
            ref_name: Name of ref being injected

        Returns:
            Value to inject (string, dict, or any JSON-serializable)
        """
        pass


class SubprocessProcessor(Processor):
    """Processor that calls external script/program."""

    def __init__(self, command: list[str]):
        """
        Args:
            command: Command to run, e.g. ["python", "process_text.py"]
        """
        self.command = command

    def apply(self, source: dict, target: dict, ref_name: str) -> Any:
        """Run external process with cubes as JSON input."""
        input_data = json.dumps({
            "source": source,
            "target": target,
            "ref_name": ref_name
        })

        result = subprocess.run(
            self.command,
            input=input_data,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(f"Processor failed: {result.stderr}")

        return json.loads(result.stdout)


class APIProcessor(Processor):
    """Processor that calls external HTTP API."""

    def __init__(self, url: str, headers: dict | None = None):
        self.url = url
        self.headers = headers or {"Content-Type": "application/json"}

    def apply(self, source: dict, target: dict, ref_name: str) -> Any:
        """POST to API with cubes as JSON."""
        import requests

        response = requests.post(
            self.url,
            json={"source": source, "target": target, "ref_name": ref_name},
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
