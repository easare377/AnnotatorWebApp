"""Contract for polygon-generation backends."""

from typing import Any, Protocol, Sequence, runtime_checkable


@runtime_checkable
class IGeneratePolygonsHandler(Protocol):
    """Generate polygons from a common SAM worker payload."""

    def generate(
        self,
        input_payload: dict[str, Any],
    ) -> Sequence[Any]:
        """Submit the payload and return the generated polygons."""
        ...
