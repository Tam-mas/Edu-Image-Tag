from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Iterator

from edu_image_tag.models import ImageRef
from edu_image_tag.registry import register_source
from edu_image_tag.sources.base import InputSource

_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}


@register_source("local_folder")
class LocalFolderSource(InputSource):
    def __init__(self, path: str, **_ignored):
        self.root = Path(path)

    def iter_images(self) -> Iterator[ImageRef]:
        if not self.root.exists():
            raise FileNotFoundError(f"Source path does not exist: {self.root}")
        for p in sorted(self.root.rglob("*")):
            if not p.is_file() or p.suffix.lower() not in _IMAGE_EXTS:
                continue
            rel = p.relative_to(self.root).as_posix()
            mime = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
            yield ImageRef(
                id=rel,
                uri=str(p),
                mime_type=mime,
                load_bytes=(lambda fp=p: fp.read_bytes()),
            )
