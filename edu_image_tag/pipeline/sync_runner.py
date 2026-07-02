from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from edu_image_tag.pipeline.base import process_image


@dataclass
class RunSummary:
    total: int = 0
    ok: int = 0
    needs_review: int = 0
    error: int = 0
    skipped: int = 0


class SyncRunner:
    def __init__(self, completed_ids: set[str] | None = None):
        self._completed = completed_ids or set()

    def run(self, refs, client, config, writers, context_lookup,
            force: bool, dry_run: bool) -> RunSummary:
        summary = RunSummary()
        todo = []
        for ref in refs:
            summary.total += 1
            if dry_run:
                summary.skipped += 1
                continue
            if not force and ref.id in self._completed:
                summary.skipped += 1
                continue
            todo.append(ref)

        if not dry_run and todo:
            workers = max(1, config.processing.max_workers)
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = {
                    pool.submit(process_image, ref, client, config,
                                context_lookup.get(ref.id)): ref
                    for ref in todo
                }
                for fut in as_completed(futures):
                    result = fut.result()
                    for w in writers:
                        w.write(result)
                    self._tally(summary, result.status)

        for w in writers:
            w.finalize()
        return summary

    @staticmethod
    def _tally(summary: RunSummary, status: str) -> None:
        if status == "ok":
            summary.ok += 1
        elif status == "needs_review":
            summary.needs_review += 1
        else:
            summary.error += 1
