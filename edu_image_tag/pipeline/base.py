from __future__ import annotations

from datetime import datetime, timezone

from edu_image_tag.hashing import sha256_hex
from edu_image_tag.models import ImageContext, ImageRef, ImageResult


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def process_image(ref: ImageRef, client, config, context: ImageContext) -> ImageResult:
    """Run the full per-image pipeline. Never raises: failures become status=error."""
    models = {"classify": None, "describe": config.models.describe}
    content_hash = ref.content_hash
    try:
        image_bytes = ref.load_bytes()
        content_hash = ref.content_hash or sha256_hex(image_bytes)
        image_type = None
        if config.enable_classification:
            image_type = client.classify(image_bytes, ref.mime_type,
                                          config.image_types)
            models["classify"] = config.models.classify

        desc = client.describe(image_bytes, ref.mime_type, image_type,
                               context.as_prompt_block())

        review_reasons: list[str] = []
        if desc.confidence_score < config.confidence_threshold:
            review_reasons.append(
                f"confidence {desc.confidence_score:.2f} < "
                f"threshold {config.confidence_threshold:.2f}"
            )
        status = "needs_review" if review_reasons else "ok"

        return ImageResult(
            image_id=ref.id, source_uri=ref.uri,
            image_type=desc.image_type or image_type,
            short_alt_text=desc.short_alt_text,
            long_description=desc.long_description,
            key_takeaways=list(desc.key_takeaways),
            confidence_score=desc.confidence_score,
            status=status, review_reasons=review_reasons,
            model=models, processed_at=_now(), content_hash=content_hash,
        )
    except Exception as e:  # noqa: BLE001 - isolate per-image failures
        return ImageResult(
            image_id=ref.id, source_uri=ref.uri, image_type=None,
            short_alt_text=None, long_description=None, key_takeaways=[],
            confidence_score=None, status="error",
            review_reasons=["processing error"], model=models,
            processed_at=_now(), error=str(e), content_hash=content_hash,
        )
