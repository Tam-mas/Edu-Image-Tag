from __future__ import annotations

import json
from pathlib import Path

from edu_image_tag.gemini_client import DescriptionSchema, build_describe_request
from edu_image_tag.models import ImageResult
from edu_image_tag.pipeline.base import _now
from edu_image_tag.pipeline.sync_runner import RunSummary


class BatchRunner:
    def run(self, refs, client, config, writers, context_lookup,
            force: bool, dry_run: bool) -> RunSummary:
        summary = RunSummary()
        refs = list(refs)
        summary.total = len(refs)

        if dry_run:
            summary.skipped = len(refs)
            for w in writers:
                w.finalize()
            return summary

        out_dir = Path(config.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        state_path = out_dir / "batch_state.json"
        state = json.loads(state_path.read_text()) if state_path.exists() else {}

        # Cache each image's bytes so load_bytes() fires exactly once per image
        # regardless of whether classification is enabled. Note: dict.setdefault
        # would evaluate load_bytes() every call (args are eval'd eagerly), so we
        # gate on membership to guarantee a single disk read.
        bytes_by_id: dict[str, bytes] = {}

        def _img_bytes(ref) -> bytes:
            if ref.id not in bytes_by_id:
                bytes_by_id[ref.id] = ref.load_bytes()
            return bytes_by_id[ref.id]

        # Optional inline classification to get image_type per image.
        types_by_id: dict[str, str | None] = {}
        for ref in refs:
            if config.enable_classification:
                try:
                    types_by_id[ref.id] = client.classify(
                        _img_bytes(ref), ref.mime_type, config.image_types)
                except Exception:  # noqa: BLE001
                    types_by_id[ref.id] = None
            else:
                types_by_id[ref.id] = None

        # Build describe requests (grouped/sorted by type for implicit caching).
        requests = []
        for ref in refs:
            requests.append(build_describe_request(
                image_b64=client.encode_image(_img_bytes(ref)),
                mime_type=ref.mime_type,
                image_type=types_by_id[ref.id],
                context_block=context_lookup.get(ref.id).as_prompt_block(),
                system_instruction=client.DESCRIBE_SYSTEM_INSTRUCTION,
                metadata_id=ref.id,
            ))
            requests[-1]["_sort"] = types_by_id[ref.id] or "zzz"

        # Submit (or resume an already-submitted job).
        job_name = state.get("describe_job")
        if not job_name:
            jsonl_path = client.write_batch_jsonl(
                requests, str(out_dir / "describe_requests.jsonl"),
                sort_key="_sort")
            job_name = client.submit_batch(jsonl_path, model=config.models.describe)
            state["describe_job"] = job_name
            state_path.write_text(json.dumps(state))

        job = client.poll_batch(job_name, interval=30.0)
        if getattr(job, "state", None) != "JOB_STATE_SUCCEEDED":
            # Failed/cancelled job has no usable dest. Clear state so a re-run
            # resubmits fresh instead of re-polling a dead job forever.
            state_path.unlink(missing_ok=True)
            raise RuntimeError(
                f"Batch job {job_name} ended in state "
                f"{getattr(job, 'state', 'UNKNOWN')}"
            )
        results = client.download_batch_results(job)

        refs_by_id = {r.id: r for r in refs}
        for item in results:
            image_id = item.get("metadata", {}).get("key")
            ref = refs_by_id.get(image_id)
            result = self._to_result(image_id, ref, item,
                                     types_by_id.get(image_id), config)
            for w in writers:
                w.write(result)
            self._tally(summary, result.status)

        # Never silently drop an image: emit an error result for any ref whose
        # id did not appear in the batch output.
        returned_ids = {item.get("metadata", {}).get("key") for item in results}
        for ref in refs:
            if ref.id not in returned_ids:
                missing = ImageResult(
                    image_id=ref.id, source_uri=ref.uri, image_type=None,
                    short_alt_text=None, long_description=None, key_takeaways=[],
                    confidence_score=None, status="error",
                    review_reasons=["missing from batch response"],
                    model={"classify": config.models.classify if config.enable_classification else None,
                           "describe": config.models.describe},
                    processed_at=_now(), error="image had no result in the batch output",
                )
                for w in writers:
                    w.write(missing)
                self._tally(summary, "error")

        for w in writers:
            w.finalize()

        # Job finished and results written: clear state so a re-run starts fresh
        # instead of re-downloading this already-completed job.
        state_path.unlink(missing_ok=True)
        return summary

    def _to_result(self, image_id, ref, item, image_type, config) -> ImageResult:
        source_uri = ref.uri if ref else (image_id or "")
        models = {
            "classify": config.models.classify if config.enable_classification else None,
            "describe": config.models.describe,
        }
        try:
            text = item["response"]["candidates"][0]["content"]["parts"][0]["text"]
            desc = DescriptionSchema.model_validate_json(text)
            reasons = []
            if desc.confidence_score < config.confidence_threshold:
                reasons.append(
                    f"confidence {desc.confidence_score:.2f} < "
                    f"threshold {config.confidence_threshold:.2f}")
            return ImageResult(
                image_id=image_id, source_uri=source_uri,
                image_type=desc.image_type or image_type,
                short_alt_text=desc.short_alt_text,
                long_description=desc.long_description,
                key_takeaways=list(desc.key_takeaways),
                confidence_score=desc.confidence_score,
                status="needs_review" if reasons else "ok",
                review_reasons=reasons, model=models, processed_at=_now(),
            )
        except Exception as e:  # noqa: BLE001 - malformed line -> needs_review
            return ImageResult(
                image_id=image_id, source_uri=source_uri, image_type=image_type,
                short_alt_text=None, long_description=None, key_takeaways=[],
                confidence_score=None, status="needs_review",
                review_reasons=["malformed batch response"], model=models,
                processed_at=_now(), error=str(e))

    @staticmethod
    def _tally(summary: RunSummary, status: str) -> None:
        if status == "ok":
            summary.ok += 1
        elif status == "needs_review":
            summary.needs_review += 1
        else:
            summary.error += 1
