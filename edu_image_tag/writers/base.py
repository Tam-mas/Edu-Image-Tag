from __future__ import annotations

from abc import ABC, abstractmethod

from edu_image_tag.models import ImageResult


class OutputWriter(ABC):
    """Receives every ImageResult. Extension seam: subclass + register_writer."""

    @abstractmethod
    def write(self, result: ImageResult) -> None:
        ...

    def finalize(self) -> None:
        """Called once after all images. Override to flush/close."""
