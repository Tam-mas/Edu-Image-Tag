from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Callable, Optional


@dataclass
class ImageRef:
    """A single image to process. `load_bytes` defers I/O until needed."""
    id: str
    uri: str
    mime_type: str
    load_bytes: Callable[[], bytes]
    content_hash: Optional[str] = None


@dataclass
class ImageContext:
    """Optional per-image context injected into the describe prompt."""
    fields: dict[str, str] = field(default_factory=dict)

    def as_prompt_block(self) -> str:
        if not self.fields:
            return ""
        return "\n".join(f"{k}: {v}" for k, v in self.fields.items())


@dataclass
class ImageResult:
    """Normalized output for one image. Same shape for every provider/mode."""
    image_id: str
    source_uri: str
    image_type: Optional[str]
    short_alt_text: Optional[str]
    long_description: Optional[str]
    key_takeaways: list[str]
    confidence_score: Optional[float]
    status: str  # "ok" | "needs_review" | "error"
    review_reasons: list[str]
    model: dict[str, Optional[str]]
    processed_at: str
    error: Optional[str] = None
    content_hash: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)
