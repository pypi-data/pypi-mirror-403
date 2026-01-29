"""DefaultProcessor - Fallback for unknown type pairs."""
import logging
from typing import Any
from .base import Processor

logger = logging.getLogger(__name__)


class DefaultProcessor(Processor):
    """Fallback processor - returns raw individuality.

    NO HEURISTICS. Just returns the source individuality as-is.

    When this processor is used, it means no specific processor
    exists for the (source_type, target_type) pair.
    """

    def apply(self, source: dict, target: dict, ref_name: str) -> Any:
        """Return raw source individuality.

        Logs warning about missing processor.
        """
        source_type = source.get("typology", "*")
        target_type = target.get("typology", "*")

        logger.warning(
            f"DefaultProcessor used for ({source_type} → {target_type}). "
            f"Consider registering a specific processor."
        )

        return source.get("individuality_resolved") or source.get("individuality", {})
