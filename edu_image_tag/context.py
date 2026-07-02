from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Optional

from edu_image_tag.models import ImageContext


class ContextLookup:
    def __init__(self, table: dict[str, dict[str, str]]):
        self._table = table

    def get(self, image_id: str) -> ImageContext:
        return ImageContext(fields=dict(self._table.get(image_id, {})))


_ID_COLUMNS = ("image_id", "id", "filename")


def load_context_lookup(path: Optional[str]) -> ContextLookup:
    if not path:
        return ContextLookup({})
    p = Path(path)
    if p.suffix.lower() == ".json":
        data = json.loads(p.read_text(encoding="utf-8"))
        table = {k: {ik: str(iv) for ik, iv in v.items()} for k, v in data.items()}
        return ContextLookup(table)
    # default: CSV
    table: dict[str, dict[str, str]] = {}
    with p.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        id_col = next((c for c in _ID_COLUMNS if c in (reader.fieldnames or [])), None)
        if id_col is None:
            raise ValueError(
                f"Context CSV must have an id column ({', '.join(_ID_COLUMNS)})"
            )
        for row in reader:
            key = row.pop(id_col)
            table[key] = {k: str(v) for k, v in row.items() if v not in (None, "")}
    return ContextLookup(table)
