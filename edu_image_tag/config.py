from __future__ import annotations

from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator

DEFAULT_IMAGE_TYPES = [
    "chart_graph",
    "scientific_diagram",
    "historical_photograph",
    "artwork",
    "dense_text_ocr",
]


class ConfigError(Exception):
    """Raised when config.yaml is missing required fields or is invalid."""


class ModelsConfig(BaseModel):
    classify: str
    describe: str


class ProcessingConfig(BaseModel):
    mode: str = "sync"
    max_workers: int = 8

    @field_validator("mode")
    @classmethod
    def _mode_valid(cls, v: str) -> str:
        if v not in ("sync", "batch"):
            raise ValueError("processing.mode must be 'sync' or 'batch'")
        return v


class SourceConfig(BaseModel):
    type: str
    model_config = {"extra": "allow"}

    def options(self) -> dict[str, Any]:
        return self.__pydantic_extra__ or {}


class Config(BaseModel):
    models: ModelsConfig
    source: SourceConfig
    outputs: list[str]
    image_types: list[str] = Field(default_factory=lambda: list(DEFAULT_IMAGE_TYPES))
    enable_classification: bool = True
    confidence_threshold: float = 0.7
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    context_file: Optional[str] = None
    output_dir: str = "./output"

    @field_validator("outputs")
    @classmethod
    def _outputs_nonempty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("outputs must list at least one writer")
        return v


def load_config(path: str) -> Config:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    try:
        return Config(**raw)
    except ValidationError as e:
        raise ConfigError(str(e)) from e
