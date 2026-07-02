from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import edu_image_tag.sources  # noqa: F401 - registers built-in sources
import edu_image_tag.writers  # noqa: F401 - registers built-in writers
from edu_image_tag.config import load_config
from edu_image_tag.context import load_context_lookup
from edu_image_tag.gemini_client import GeminiClient, build_sdk_client
from edu_image_tag.pipeline.batch_runner import BatchRunner
from edu_image_tag.pipeline.sync_runner import SyncRunner
from edu_image_tag.registry import get_source, get_writer


def build_components(config):
    source_cls = get_source(config.source.type)
    source = source_cls(**config.source.options())
    writers = [get_writer(name)(output_dir=config.output_dir)
               for name in config.outputs]
    return source, writers


def _load_completed_ids(output_dir: str) -> set[str]:
    """Read already-processed image ids from whichever manifest exists.

    Must be called BEFORE writers are constructed, since writers open the
    manifest files for appending.
    """
    import csv

    out = Path(output_dir)
    ids: set[str] = set()

    jsonl = out / "manifest.jsonl"
    if jsonl.exists():
        for line in jsonl.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    ids.add(json.loads(line)["image_id"])
                except Exception:  # noqa: BLE001
                    continue

    csv_path = out / "manifest.csv"
    if csv_path.exists():
        with csv_path.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("image_id"):
                    ids.add(row["image_id"])

    return ids


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="edu-image-tag")
    parser.add_argument("--config", default="config.yaml",
                        help="Path to config.yaml")
    parser.add_argument("--force", action="store_true",
                        help="Reprocess images even if already in the manifest")
    parser.add_argument("--dry-run", action="store_true",
                        help="Count images and skip API calls")
    args = parser.parse_args(argv)

    config = load_config(args.config)

    # Read completed ids BEFORE building writers (writers append to the manifest).
    completed = set() if args.force else _load_completed_ids(config.output_dir)

    source, writers = build_components(config)
    context_lookup = load_context_lookup(config.context_file)
    client = GeminiClient(
        sdk_client=build_sdk_client(),
        classify_model=config.models.classify,
        describe_model=config.models.describe,
    )
    refs = list(source.iter_images())

    if config.processing.mode == "batch":
        runner = BatchRunner()
    else:
        runner = SyncRunner(completed_ids=completed)

    summary = runner.run(refs=refs, client=client, config=config, writers=writers,
                         context_lookup=context_lookup, force=args.force,
                         dry_run=args.dry_run)

    print(f"Total: {summary.total}  ok: {summary.ok}  "
          f"needs_review: {summary.needs_review}  errors: {summary.error}  "
          f"skipped: {summary.skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
