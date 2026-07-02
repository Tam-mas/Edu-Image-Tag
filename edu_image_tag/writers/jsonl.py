from __future__ import annotations

import json
from pathlib import Path

from edu_image_tag.models import ImageResult
from edu_image_tag.registry import register_writer
from edu_image_tag.writers.base import OutputWriter


@register_writer("jsonl")
class JsonlWriter(OutputWriter):
    def __init__(self, output_dir: str, **_ignored):
        self._path = Path(output_dir) / "manifest.jsonl"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self._path.open("a", encoding="utf-8")

    def write(self, result: ImageResult) -> None:
        self._fh.write(json.dumps(result.to_dict(), ensure_ascii=False) + "\n")

    def finalize(self) -> None:
        self._fh.close()
