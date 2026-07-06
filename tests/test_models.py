from edu_image_tag.models import ImageRef, ImageContext, ImageResult


def test_imageref_loads_bytes_lazily():
    ref = ImageRef(id="a/b.jpg", uri="/x/a/b.jpg", mime_type="image/jpeg",
                   load_bytes=lambda: b"data")
    assert ref.id == "a/b.jpg"
    assert ref.load_bytes() == b"data"


def test_imagecontext_prompt_block_formats_fields():
    ctx = ImageContext(fields={"textbook_title": "Biology", "chapter": "4"})
    block = ctx.as_prompt_block()
    assert "textbook_title: Biology" in block
    assert "chapter: 4" in block


def test_imagecontext_empty_block_is_empty_string():
    assert ImageContext(fields={}).as_prompt_block() == ""


def test_imageresult_to_dict_roundtrip():
    r = ImageResult(
        image_id="a/b.jpg", source_uri="/x/a/b.jpg", image_type="artwork",
        short_alt_text="short", long_description="long",
        key_takeaways=["k1"], confidence_score=0.9, status="ok",
        review_reasons=[], model={"classify": "m1", "describe": "m2"},
        processed_at="2026-07-02T00:00:00Z",
    )
    d = r.to_dict()
    assert d["image_id"] == "a/b.jpg"
    assert d["status"] == "ok"
    assert d["key_takeaways"] == ["k1"]
    assert "error" in d and d["error"] is None


def test_imageref_carries_optional_content_hash():
    ref = ImageRef(id="a", uri="u", mime_type="image/jpeg",
                   load_bytes=lambda: b"", content_hash="abc")
    assert ref.content_hash == "abc"


def test_imageresult_to_dict_includes_content_hash():
    r = ImageResult(
        image_id="a", source_uri="u", image_type=None, short_alt_text=None,
        long_description=None, key_takeaways=[], confidence_score=None,
        status="ok", review_reasons=[], model={}, processed_at="t",
        content_hash="abc123",
    )
    assert r.to_dict()["content_hash"] == "abc123"
