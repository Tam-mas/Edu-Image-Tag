from unittest.mock import MagicMock, patch

from edu_image_tag.cli import build_components, main


def _cfg(mode="sync", outputs=("json_sidecar",)):
    cfg = MagicMock()
    cfg.processing.mode = mode
    cfg.outputs = list(outputs)
    cfg.output_dir = "./output"
    cfg.source.type = "local_folder"
    cfg.source.options.return_value = {"path": "./images"}
    cfg.context_file = None
    cfg.models.classify = "c"
    cfg.models.describe = "d"
    return cfg


def test_build_components_resolves_source_and_writers():
    import edu_image_tag.sources  # noqa: F401 (register built-ins)
    import edu_image_tag.writers  # noqa: F401
    cfg = _cfg(outputs=("json_sidecar", "jsonl"))
    source, writers = build_components(cfg)
    assert source.__class__.__name__ == "LocalFolderSource"
    assert len(writers) == 2


def test_main_selects_batch_runner(tmp_path, monkeypatch):
    cfg = _cfg(mode="batch")
    with patch("edu_image_tag.cli.load_config", return_value=cfg), \
         patch("edu_image_tag.cli.build_sdk_client", return_value=MagicMock()), \
         patch("edu_image_tag.cli.BatchRunner") as BR, \
         patch("edu_image_tag.cli.build_components",
               return_value=(MagicMock(iter_images=lambda: []), [])):
        BR.return_value.run.return_value = MagicMock(
            total=0, ok=0, needs_review=0, error=0, skipped=0)
        rc = main(["--config", "x.yaml"])
    assert rc == 0
    BR.return_value.run.assert_called_once()
