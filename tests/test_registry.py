import pytest
from edu_image_tag import registry


def test_register_and_get_source():
    @registry.register_source("dummy_src")
    class DummySource:
        pass
    assert registry.get_source("dummy_src") is DummySource


def test_register_and_get_writer():
    @registry.register_writer("dummy_writer")
    class DummyWriter:
        pass
    assert registry.get_writer("dummy_writer") is DummyWriter


def test_unknown_source_raises_with_available_names():
    with pytest.raises(KeyError, match="unknown_x"):
        registry.get_source("unknown_x")
