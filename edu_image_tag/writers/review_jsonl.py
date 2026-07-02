from __future__ import annotations

import json
from pathlib import Path

from edu_image_tag.models import ImageResult
from edu_image_tag.registry import register_writer
from edu_image_tag.writers.base import OutputWriter


@register_writer("review_jsonl")
class ReviewJsonlWriter(OutputWriter):
    """Records only results that need human attention (needs_review / error)."""

    def __init__(self, output_dir: str, **_ignored):
        path = Path(output_dir) / "review.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = path.open("a", encoding="utf-8")

    def write(self, result: ImageResult) -> None:
        if result.status in ("needs_review", "error"):
            self._fh.write(json.dumps(result.to_dict(), ensure_ascii=False) + "\n")

    def finalize(self) -> None:
        self._fh.close()
