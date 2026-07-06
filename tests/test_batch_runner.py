import json
from unittest.mock import MagicMock

from edu_image_tag.models import ImageRef
from edu_image_tag.context import ContextLookup
from edu_image_tag.pipeline.batch_runner import BatchRunner


def _ref(image_id):
    return ImageRef(id=image_id, uri="/x/" + image_id, mime_type="image/jpeg",
                    load_bytes=lambda: b"bytes")


class _Cfg:
    enable_classification = False
    confidence_threshold = 0.7
    image_types = ["artwork", "chart_graph"]
    output_dir = None  # set in test

    class models:
        classify = "c"
        describe = "d"


class _RecordingWriter:
    def __init__(self): self.written = []
    def write(self, r): self.written.append((r.image_id, r.status))
    def finalize(self): pass


def _fake_client(results_payload, state="JOB_STATE_SUCCEEDED"):
    c = MagicMock()
    c.encode_image.side_effect = lambda b: "B64"
    c.DESCRIBE_SYSTEM_INSTRUCTION = "SYS"
    c.write_batch_jsonl.side_effect = (
        lambda reqs, path, sort_key=None: (open(path, "w").close() or path))
    c.submit_batch.return_value = "batches/999"
    job = MagicMock(); job.state = state
    c.poll_batch.return_value = job
    c.download_batch_results.return_value = results_payload
    return c


def _payload(image_id, conf=0.9):
    body = {"image_type": "artwork", "short_alt_text": "s",
            "long_description": "l", "key_takeaways": ["k"],
            "confidence_score": conf}
    return {"metadata": {"key": image_id},
            "response": {"candidates": [{"content": {"parts": [
                {"text": json.dumps(body)}]}}]}}


def test_batch_runner_maps_results_to_writers(tmp_path):
    cfg = _Cfg(); cfg.output_dir = str(tmp_path)
    client = _fake_client([_payload("a.jpg", 0.9), _payload("b.jpg", 0.3)])
    writer = _RecordingWriter()
    summary = BatchRunner().run(refs=[_ref("a.jpg"), _ref("b.jpg")],
                                client=client, config=cfg, writers=[writer],
                                context_lookup=ContextLookup({}),
                                force=False, dry_run=False)
    statuses = dict(writer.written)
    assert statuses["a.jpg"] == "ok"
    assert statuses["b.jpg"] == "needs_review"
    assert summary.ok == 1 and summary.needs_review == 1


def test_dry_run_skips_submission(tmp_path):
    cfg = _Cfg(); cfg.output_dir = str(tmp_path)
    client = _fake_client([])
    summary = BatchRunner().run(refs=[_ref("a.jpg")], client=client, config=cfg,
                                writers=[_RecordingWriter()],
                                context_lookup=ContextLookup({}),
                                force=False, dry_run=True)
    client.submit_batch.assert_not_called()
    assert summary.total == 1 and summary.skipped == 1


def test_resume_reuses_saved_job_name(tmp_path):
    cfg = _Cfg(); cfg.output_dir = str(tmp_path)
    state = tmp_path / "batch_state.json"
    state.write_text(json.dumps({"describe_job": "batches/existing"}))
    client = _fake_client([_payload("a.jpg", 0.9)])
    BatchRunner().run(refs=[_ref("a.jpg")], client=client, config=cfg,
                      writers=[_RecordingWriter()],
                      context_lookup=ContextLookup({}),
                      force=False, dry_run=False)
    client.submit_batch.assert_not_called()
    client.poll_batch.assert_called_with("batches/existing", interval=30.0)


def test_failed_job_raises_and_clears_state(tmp_path):
    import pytest
    cfg = _Cfg(); cfg.output_dir = str(tmp_path)
    client = _fake_client([], state="JOB_STATE_FAILED")
    with pytest.raises(RuntimeError, match="JOB_STATE_FAILED"):
        BatchRunner().run(refs=[_ref("a.jpg")], client=client, config=cfg,
                          writers=[_RecordingWriter()],
                          context_lookup=ContextLookup({}),
                          force=False, dry_run=False)
    client.download_batch_results.assert_not_called()
    assert not (tmp_path / "batch_state.json").exists()  # cleared for clean re-run


def test_missing_image_in_results_is_flagged(tmp_path):
    cfg = _Cfg(); cfg.output_dir = str(tmp_path)
    client = _fake_client([_payload("a.jpg", 0.9)])  # b.jpg dropped by API
    writer = _RecordingWriter()
    summary = BatchRunner().run(refs=[_ref("a.jpg"), _ref("b.jpg")],
                                client=client, config=cfg, writers=[writer],
                                context_lookup=ContextLookup({}),
                                force=False, dry_run=False)
    statuses = dict(writer.written)
    assert statuses["a.jpg"] == "ok"
    assert statuses["b.jpg"] == "error"
    assert summary.total == 2 and summary.error == 1


def test_bytes_loaded_once_per_image_with_classification(tmp_path):
    from edu_image_tag.models import ImageRef
    cfg = _Cfg(); cfg.output_dir = str(tmp_path); cfg.enable_classification = True
    counts = {"n": 0}
    def _counting_ref(image_id):
        def load():
            counts["n"] += 1
            return b"bytes"
        return ImageRef(id=image_id, uri="/x/" + image_id,
                        mime_type="image/jpeg", load_bytes=load)
    client = _fake_client([_payload("a.jpg", 0.9)])
    client.classify.return_value = "artwork"
    BatchRunner().run(refs=[_counting_ref("a.jpg")], client=client, config=cfg,
                      writers=[_RecordingWriter()], context_lookup=ContextLookup({}),
                      force=False, dry_run=False)
    assert counts["n"] == 1  # loaded once, reused for classify + encode


def test_force_clears_prior_batch_state(tmp_path):
    cfg = _Cfg(); cfg.output_dir = str(tmp_path)
    (tmp_path / "batch_state.json").write_text(json.dumps({"describe_job": "batches/old"}))
    client = _fake_client([_payload("a.jpg", 0.9)])
    BatchRunner().run(refs=[_ref("a.jpg")], client=client, config=cfg,
                      writers=[_RecordingWriter()], context_lookup=ContextLookup({}),
                      force=True, dry_run=False)
    client.submit_batch.assert_called_once()  # ignored the saved job, resubmitted


def test_batch_result_includes_content_hash(tmp_path):
    from edu_image_tag.hashing import sha256_hex
    cfg = _Cfg(); cfg.output_dir = str(tmp_path)
    client = _fake_client([_payload("a.jpg", 0.9)])

    class _CapWriter:
        def __init__(self): self.results = []
        def write(self, r): self.results.append(r)
        def finalize(self): pass

    w = _CapWriter()
    BatchRunner().run(refs=[_ref("a.jpg")], client=client, config=cfg, writers=[w],
                      context_lookup=ContextLookup({}), force=False, dry_run=False)
    assert w.results[0].content_hash == sha256_hex(b"bytes")
