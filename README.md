# Edu-Image-Tag

Tag educational images with accessibility metadata (alt text, long
descriptions, key takeaways) using Google Gemini — built for institutions
processing large image libraries to improve access for learners with visual
impairments.

## Install

```bash
pip install -e .
export GEMINI_API_KEY="your-key"     # never put the key in config.yaml
```

## Quickstart

```bash
cp config.example.yaml config.yaml   # edit paths/models as needed
mkdir images && cp your/*.jpg images/
edu-image-tag --config config.yaml
```

Results land in `./output/`:
- `<image>.json` — full result per image (sidecar)
- `manifest.csv` — combined results (add `jsonl` to `outputs` for `manifest.jsonl`)
- `review.jsonl` — only the results flagged `needs_review` or `error`

Use `--dry-run` to count images and estimate scope without calling the API, and
`--force` to reprocess images already in the manifest.

## Configuration

Everything is controlled by `config.yaml` (see `config.example.yaml` for the
fully-commented reference). Swap `models.classify` / `models.describe` to trade
cost vs accuracy, toggle `enable_classification`, and choose `processing.mode`
(`sync` or `batch`).

Ships configured for `gemini-3.1-flash-lite` (classify) and
`gemini-3.1-pro-preview` (describe) — change these to any model IDs your Gemini
account can access.

## Extending (the two seams)

The tool is meant to be customized at exactly two points:

**Where images come from — `InputSource`.** Subclass it, register it, name it in
config:

```python
from edu_image_tag.sources.base import InputSource
from edu_image_tag.registry import register_source

@register_source("gcs")
class GcsSource(InputSource):
    def __init__(self, bucket, **_): ...
    def iter_images(self): ...  # yield ImageRef objects
```

**Where results go — `OutputWriter`.** This is where you push into your own
database. Ship it as a small file, add its name to `outputs:`:

```python
from edu_image_tag.writers.base import OutputWriter
from edu_image_tag.registry import register_writer

@register_writer("postgres")
class PostgresWriter(OutputWriter):
    def __init__(self, output_dir, **_): ...
    def write(self, result): ...     # INSERT/UPDATE your accessibility fields
    def finalize(self): ...
```

Direct production-database injection and a human-review dashboard are
intentionally **not** built in — they are too organization-specific. The
`needs_review` flag and `review.jsonl` output give you the hook to build them.

## Context (optional)

Point `context_file` at a CSV or JSON mapping image id → context fields
(textbook title, chapter, surrounding text). Present context is injected into
the description prompt to improve accuracy.

## Processing modes

- **sync** (default): concurrent real-time API calls. Simple, easy to debug,
  restartable (already-processed images are skipped on re-run).
- **batch**: submits a single Gemini Batch job (cheapest at scale via implicit
  caching), polls to completion, then writes results. Resumable via a job-state
  file.

## Security notes

- The API key is read only from `GEMINI_API_KEY` — keep it out of config and git.
- Text inside images (`dense_text_ocr`) or in the context file is treated as
  untrusted data in the prompt and output is schema-constrained. This limits,
  but does not eliminate, prompt-injection risk — review flagged results.
- Sidecar output paths are validated to prevent writing outside `output_dir`.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT — see [LICENSE](LICENSE).
