from unittest.mock import MagicMock

from edu_image_tag.models import ImageRef, ImageResult
from edu_image_tag.context import ContextLookup
from edu_image_tag.pipeline.sync_runner import SyncRunner


def _ref(image_id):
    return ImageRef(id=image_id, uri="/x/" + image_id, mime_type="image/jpeg",
                    load_bytes=lambda: b"b")


class _Cfg:
    class processing:
        max_workers = 2


class _RecordingWriter:
    def __init__(self):
        self.written = []
    def write(self, r): self.written.append(r.image_id)
    def finalize(self): self.written.append("FINALIZED")


def _ok_result(image_id):
    return ImageResult(image_id=image_id, source_uri="/x", image_type="artwork",
                       short_alt_text="s", long_description="l",
                       key_takeaways=[], confidence_score=0.9, status="ok",
                       review_reasons=[], model={}, processed_at="t")


def test_runner_processes_all_and_finalizes(monkeypatch):
    import edu_image_tag.pipeline.sync_runner as mod
    monkeypatch.setattr(mod, "process_image",
                        lambda ref, c, cfg, ctx: _ok_result(ref.id))
    writer = _RecordingWriter()
    summary = SyncRunner().run(
        refs=[_ref("a"), _ref("b")], client=MagicMock(), config=_Cfg(),
        writers=[writer], context_lookup=ContextLookup({}),
        force=False, dry_run=False)
    assert set(writer.written[:-1]) == {"a", "b"}
    assert writer.written[-1] == "FINALIZED"
    assert summary.ok == 2 and summary.total == 2


def test_dry_run_does_not_process(monkeypatch):
    import edu_image_tag.pipeline.sync_runner as mod
    called = []
    monkeypatch.setattr(mod, "process_image",
                        lambda *a, **k: called.append(1))
    writer = _RecordingWriter()
    summary = SyncRunner().run(refs=[_ref("a")], client=MagicMock(), config=_Cfg(),
                               writers=[writer], context_lookup=ContextLookup({}),
                               force=False, dry_run=True)
    assert called == []
    assert summary.total == 1 and summary.skipped == 1


def test_resume_skips_completed_ids(monkeypatch):
    import edu_image_tag.pipeline.sync_runner as mod
    monkeypatch.setattr(mod, "process_image",
                        lambda ref, c, cfg, ctx: _ok_result(ref.id))
    writer = _RecordingWriter()
    summary = SyncRunner(completed_ids={"a"}).run(
        refs=[_ref("a"), _ref("b")], client=MagicMock(), config=_Cfg(),
        writers=[writer], context_lookup=ContextLookup({}),
        force=False, dry_run=False)
    assert "a" not in writer.written
    assert "b" in writer.written
    assert summary.skipped == 1 and summary.ok == 1
