from unittest.mock import MagicMock

from edu_image_tag.gemini_client import GeminiClient, DescriptionSchema


def _fake_sdk(parsed=None, text=None):
    sdk = MagicMock()
    resp = MagicMock()
    resp.parsed = parsed
    resp.text = text
    sdk.models.generate_content.return_value = resp
    return sdk


def test_classify_returns_stripped_text():
    sdk = _fake_sdk(text=" artwork ")
    client = GeminiClient(sdk_client=sdk, classify_model="c", describe_model="d")
    result = client.classify(b"img", "image/jpeg",
                             ["artwork", "chart_graph"])
    assert result == "artwork"
    assert sdk.models.generate_content.called


def test_classify_falls_back_when_unknown_type():
    sdk = _fake_sdk(text="banana")
    client = GeminiClient(sdk_client=sdk, classify_model="c", describe_model="d")
    result = client.classify(b"img", "image/jpeg", ["artwork"])
    assert result == "artwork"  # first type as fallback


def test_describe_returns_parsed_schema():
    parsed = DescriptionSchema(
        image_type="artwork", short_alt_text="s", long_description="l",
        key_takeaways=["k"], confidence_score=0.8,
    )
    sdk = _fake_sdk(parsed=parsed)
    client = GeminiClient(sdk_client=sdk, classify_model="c", describe_model="d")
    out = client.describe(b"img", "image/jpeg", "artwork", "chapter: 4")
    assert out.short_alt_text == "s"
    assert out.confidence_score == 0.8


def test_describe_retries_then_raises_on_persistent_failure():
    import pytest
    sdk = MagicMock()
    sdk.models.generate_content.side_effect = RuntimeError("boom")
    client = GeminiClient(sdk_client=sdk, classify_model="c",
                          describe_model="d", max_retries=2, retry_base_delay=0)
    with pytest.raises(RuntimeError):
        client.describe(b"img", "image/jpeg", "artwork", "")
    assert sdk.models.generate_content.call_count == 2
