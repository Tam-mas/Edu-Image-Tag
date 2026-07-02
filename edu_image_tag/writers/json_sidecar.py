from __future__ import annotations

import json
from pathlib import Path

from edu_image_tag.models import ImageResult
from edu_image_tag.registry import register_writer
from edu_image_tag.writers.base import OutputWriter


@register_writer("json_sidecar")
class JsonSidecarWriter(OutputWriter):
    def __init__(self, output_dir: str, **_ignored):
        self._root = Path(output_dir).resolve()

    def write(self, result: ImageResult) -> None:
        target = (self._root / (result.image_id + ".json")).resolve()
        if self._root not in target.parents:
            raise ValueError(
                f"Refusing to write outside output_dir: {result.image_id}"
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(result.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
