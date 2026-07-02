import json
from unittest.mock import MagicMock

from edu_image_tag.gemini_client import GeminiClient, build_describe_request


def _client(sdk):
    return GeminiClient(sdk_client=sdk, classify_model="c", describe_model="d",
                        retry_base_delay=0)


def test_build_describe_request_has_prefix_first_for_caching():
    req = build_describe_request(
        image_b64="AAAA", mime_type="image/jpeg", image_type="artwork",
        context_block="", system_instruction="SYS", metadata_id="a.jpg")
    assert req["metadata"]["key"] == "a.jpg"
    assert req["config"]["system_instruction"] == "SYS"


def test_write_batch_jsonl_sorts_by_type_then_writes_lines(tmp_path):
    sdk = MagicMock()
    client = _client(sdk)
    requests = [
        {"metadata": {"key": "b.jpg"}, "_sort": "z"},
        {"metadata": {"key": "a.jpg"}, "_sort": "a"},
    ]
    path = client.write_batch_jsonl(requests, str(tmp_path / "reqs.jsonl"),
                                    sort_key="_sort")
    lines = [json.loads(l) for l in open(path)]
    assert lines[0]["metadata"]["key"] == "a.jpg"
    assert "_sort" not in lines[0]


def test_submit_batch_uploads_and_creates_job(tmp_path):
    sdk = MagicMock()
    sdk.files.upload.return_value = MagicMock(name="uploaded")
    sdk.files.upload.return_value.name = "files/xyz"
    sdk.batches.create.return_value = MagicMock()
    sdk.batches.create.return_value.name = "batches/123"
    client = _client(sdk)
    p = tmp_path / "reqs.jsonl"
    p.write_text('{"metadata":{"key":"a"}}\n')
    job_name = client.submit_batch(str(p), model="d")
    assert job_name == "batches/123"
    sdk.files.upload.assert_called_once()
    sdk.batches.create.assert_called_once()


def test_poll_batch_returns_when_succeeded():
    sdk = MagicMock()
    running = MagicMock(); running.state = "JOB_STATE_RUNNING"
    done = MagicMock(); done.state = "JOB_STATE_SUCCEEDED"
    sdk.batches.get.side_effect = [running, done]
    client = _client(sdk)
    job = client.poll_batch("batches/123", interval=0)
    assert job.state == "JOB_STATE_SUCCEEDED"
    assert sdk.batches.get.call_count == 2
