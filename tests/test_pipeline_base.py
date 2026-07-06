from unittest.mock import MagicMock

from edu_image_tag.models import ImageRef, ImageContext
from edu_image_tag.gemini_client import DescriptionSchema
from edu_image_tag.pipeline.base import process_image


def _ref(image_id="a.jpg"):
    return ImageRef(id=image_id, uri="/x/" + image_id, mime_type="image/jpeg",
                    load_bytes=lambda: b"bytes")


def _client(desc, image_type="artwork"):
    c = MagicMock()
    c.classify.return_value = image_type
    c.describe.return_value = desc
    return c


def _desc(conf=0.9):
    return DescriptionSchema(image_type="artwork", short_alt_text="s",
                             long_description="l", key_takeaways=["k"],
                             confidence_score=conf)


class _Cfg:
    enable_classification = True
    confidence_threshold = 0.7
    image_types = ["artwork", "chart_graph"]

    class models:
        classify = "c"
        describe = "d"


def test_process_image_ok_when_confidence_high():
    r = process_image(_ref(), _client(_desc(0.9)), _Cfg(),
                      ImageContext(fields={}))
    assert r.status == "ok"
    assert r.short_alt_text == "s"
    assert r.image_type == "artwork"


def test_low_confidence_flagged_needs_review():
    r = process_image(_ref(), _client(_desc(0.3)), _Cfg(),
                      ImageContext(fields={}))
    assert r.status == "needs_review"
    assert any("confidence" in reason for reason in r.review_reasons)


def test_classification_skipped_when_disabled():
    cfg = _Cfg()
    cfg.enable_classification = False
    client = _client(_desc(0.9))
    r = process_image(_ref(), client, cfg, ImageContext(fields={}))
    client.classify.assert_not_called()
    assert r.status == "ok"


def test_describe_exception_becomes_error_result():
    client = MagicMock()
    client.classify.return_value = "artwork"
    client.describe.side_effect = RuntimeError("api down")
    r = process_image(_ref(), client, _Cfg(), ImageContext(fields={}))
    assert r.status == "error"
    assert "api down" in r.error


def test_content_hash_from_ref_is_carried_through():
    ref = ImageRef(id="a.jpg", uri="/x/a.jpg", mime_type="image/jpeg",
                   load_bytes=lambda: b"bytes", content_hash="deadbeef")
    r = process_image(ref, _client(_desc(0.9)), _Cfg(), ImageContext(fields={}))
    assert r.content_hash == "deadbeef"


def test_content_hash_computed_when_ref_missing_it():
    from edu_image_tag.hashing import sha256_hex
    r = process_image(_ref(), _client(_desc(0.9)), _Cfg(), ImageContext(fields={}))
    assert r.content_hash == sha256_hex(b"bytes")
