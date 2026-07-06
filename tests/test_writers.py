import json
from pathlib import Path

from edu_image_tag.models import ImageResult
from edu_image_tag.writers.jsonl import JsonlWriter
from edu_image_tag.writers.manifest_csv import ManifestCsvWriter
from edu_image_tag.writers.json_sidecar import JsonSidecarWriter


def _result(image_id="a/b.jpg", status="ok"):
    return ImageResult(
        image_id=image_id, source_uri="/x/" + image_id, image_type="artwork",
        short_alt_text="s", long_description="l", key_takeaways=["k"],
        confidence_score=0.9, status=status, review_reasons=[],
        model={"classify": "m1", "describe": "m2"},
        processed_at="2026-07-02T00:00:00Z",
    )


def test_jsonl_writer_appends_one_line_per_result(tmp_path):
    w = JsonlWriter(output_dir=str(tmp_path))
    w.write(_result("a.jpg"))
    w.write(_result("b.jpg"))
    w.finalize()
    lines = (tmp_path / "manifest.jsonl").read_text().strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["image_id"] == "a.jpg"


def test_manifest_csv_has_header_and_rows(tmp_path):
    w = ManifestCsvWriter(output_dir=str(tmp_path))
    w.write(_result("a.jpg"))
    w.finalize()
    text = (tmp_path / "manifest.csv").read_text()
    assert "image_id" in text.splitlines()[0]
    assert "a.jpg" in text


def test_sidecar_writer_writes_json_next_to_image_id(tmp_path):
    w = JsonSidecarWriter(output_dir=str(tmp_path))
    w.write(_result("sub/a.jpg"))
    w.finalize()
    out = tmp_path / "sub" / "a.jpg.json"
    assert out.exists()
    assert json.loads(out.read_text())["image_id"] == "sub/a.jpg"


def test_sidecar_rejects_path_traversal(tmp_path):
    import pytest
    w = JsonSidecarWriter(output_dir=str(tmp_path))
    with pytest.raises(ValueError, match="outside"):
        w.write(_result("../evil.jpg"))


def test_review_writer_only_records_flagged_results(tmp_path):
    from edu_image_tag.writers.review_jsonl import ReviewJsonlWriter
    w = ReviewJsonlWriter(output_dir=str(tmp_path))
    w.write(_result("ok.jpg", status="ok"))
    w.write(_result("bad.jpg", status="needs_review"))
    w.write(_result("err.jpg", status="error"))
    w.finalize()
    lines = (tmp_path / "review.jsonl").read_text().strip().splitlines()
    ids = [json.loads(l)["image_id"] for l in lines]
    assert ids == ["bad.jpg", "err.jpg"]   # "ok" excluded


def test_manifest_csv_appends_without_duplicate_header(tmp_path):
    ManifestCsvWriter(output_dir=str(tmp_path)).write(_result("a.jpg"))
    w2 = ManifestCsvWriter(output_dir=str(tmp_path))  # reopened (resume)
    w2.write(_result("b.jpg"))
    w2.finalize()
    lines = (tmp_path / "manifest.csv").read_text().strip().splitlines()
    assert lines[0].startswith("image_id")
    assert sum(1 for l in lines if l.startswith("image_id")) == 1  # one header
    assert "a.jpg" in lines[1] and "b.jpg" in lines[2]


def test_manifest_csv_includes_content_hash_column(tmp_path):
    w = ManifestCsvWriter(output_dir=str(tmp_path))
    r = _result("a.jpg")
    r.content_hash = "abc123def"
    w.write(r)
    w.finalize()
    text = (tmp_path / "manifest.csv").read_text()
    assert "content_hash" in text.splitlines()[0]
    assert "abc123def" in text
