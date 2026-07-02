from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterator

from edu_image_tag.models import ImageRef


class InputSource(ABC):
    """Yields images to process. Extension seam: subclass + register_source."""

    @abstractmethod
    def iter_images(self) -> Iterator[ImageRef]:
        ...
