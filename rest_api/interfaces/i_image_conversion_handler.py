"""Contract for local and Lambda image-conversion backends."""

from typing import Any, Protocol, Sequence, runtime_checkable


@runtime_checkable
class IImageConversionHandler(Protocol):
    """Convert one original image into a batch of requested outputs."""

    def convert(
        self,
        original_url: str,
        outputs: Sequence[dict[str, Any]],
    ) -> dict[str, Any]:
        """Create every output and return conversion metadata."""
        ...
