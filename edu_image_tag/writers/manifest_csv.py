from __future__ import annotations

import csv
from pathlib import Path

from edu_image_tag.models import ImageResult
from edu_image_tag.registry import register_writer
from edu_image_tag.writers.base import OutputWriter

_COLUMNS = [
    "image_id", "content_hash", "image_type", "status", "confidence_score",
    "short_alt_text", "long_description", "key_takeaways",
    "review_reasons", "source_uri", "processed_at", "error",
]


@register_writer("manifest_csv")
class ManifestCsvWriter(OutputWriter):
    def __init__(self, output_dir: str, **_ignored):
        path = Path(output_dir) / "manifest.csv"
        path.parent.mkdir(parents=True, exist_ok=True)
        # Append so a resumed run accumulates rows instead of truncating prior
        # results. Write the header only when the file is new/empty.
        needs_header = not path.exists() or path.stat().st_size == 0
        self._fh = path.open("a", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._fh, fieldnames=_COLUMNS)
        if needs_header:
            self._writer.writeheader()

    def write(self, result: ImageResult) -> None:
        d = result.to_dict()
        d["key_takeaways"] = " | ".join(d.get("key_takeaways") or [])
        d["review_reasons"] = " | ".join(d.get("review_reasons") or [])
        self._writer.writerow({k: d.get(k) for k in _COLUMNS})

    def finalize(self) -> None:
        self._fh.close()
