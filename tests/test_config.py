import pytest
from edu_image_tag.config import load_config, ConfigError


def _write(tmp_path, text):
    p = tmp_path / "config.yaml"
    p.write_text(text)
    return str(p)


def test_load_minimal_config_applies_defaults(tmp_path):
    path = _write(tmp_path, """
models:
  classify: "c-model"
  describe: "d-model"
source:
  type: local_folder
  path: "./images"
outputs:
  - json_sidecar
""")
    cfg = load_config(path)
    assert cfg.models.describe == "d-model"
    assert cfg.enable_classification is True
    assert cfg.confidence_threshold == 0.7
    assert cfg.processing.mode == "sync"
    assert cfg.processing.max_workers == 8
    assert cfg.output_dir == "./output"
    assert "chart_graph" in cfg.image_types


def test_invalid_processing_mode_raises(tmp_path):
    path = _write(tmp_path, """
models: {classify: c, describe: d}
processing: {mode: turbo}
source: {type: local_folder, path: ./images}
outputs: [json_sidecar]
""")
    with pytest.raises(ConfigError, match="processing.mode"):
        load_config(path)


def test_empty_outputs_raises(tmp_path):
    path = _write(tmp_path, """
models: {classify: c, describe: d}
source: {type: local_folder, path: ./images}
outputs: []
""")
    with pytest.raises(ConfigError, match="outputs"):
        load_config(path)


def test_missing_models_raises(tmp_path):
    path = _write(tmp_path, """
source: {type: local_folder, path: ./images}
outputs: [json_sidecar]
""")
    with pytest.raises(ConfigError):
        load_config(path)
