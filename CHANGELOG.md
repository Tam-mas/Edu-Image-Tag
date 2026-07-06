# Changelog

### [2026-07-06 20:29] Added

**Tech:** `hashing.py`, `ImageRef`/`ImageResult.content_hash`, `LocalFolderSource` composite id, `process_image`/`BatchRunner` propagation, `manifest_csv` column — content-hash identity for every image
**Dev:** Added `sha256_hex`/`short_hash` helpers. Every result now carries a full SHA-256 `content_hash` (the push-back fingerprint) plus an `image_id`; the local-folder source builds `image_id = "<relpath>#<first8-of-hash>"`. Identical bytes in different locations get the same `content_hash` but different `image_id`, so occurrences are tagged separately yet remain duplicate-detectable. The hash is taken from `ImageRef.content_hash` when a source supplies it, else computed once from the already-loaded bytes (no double read in the pipeline path). New `content_hash` CSV column; both fields land in the manifest and sidecars. 57 tests passing.
**Plain:** Every image now gets a unique fingerprint and a unique id, so 20k+ images can be told apart and each result pushed back to exactly the right source record.
**Why:** Two images could share a name and get confused, and there was no reliable key to match a generated description back to the original image — this makes each image individually addressable at scale.

### [2026-07-06 20:07] Added

**Tech:** `README.md` — added a Mermaid two-stage pipeline diagram and a "Customizing the description prompt" section
**Dev:** Documents that the describe behavior lives entirely in `gemini_client.py`: edit `_SYSTEM_DESCRIBE` (shared by sync + batch via `DESCRIBE_SYSTEM_INSTRUCTION`) for instructions, `describe()` / `build_describe_request()` for per-image wording, and `DescriptionSchema` for output fields (with the downstream `ImageResult`/`_to_result`/`_COLUMNS` touch-points noted). Also clarifies Stage-1 categories come from `image_types` in config.
**Plain:** The README now shows a picture of how the small "sort it" model and the big "describe it" model work together, and explains how to reword what the big model writes.
**Why:** People adopting the tool need to see the flow at a glance and know exactly which one line to edit to change the wording or fields — without reading the whole codebase first.

### [2026-07-02 21:10] Added

**Tech:** Initial release of the `edu_image_tag` package — CLI, `GeminiClient`, pluggable `InputSource`/`OutputWriter`, sync + batch runners, YAML config, 48 passing tests
**Dev:** Two-stage Gemini pipeline (optional cheap `classify` → high-fidelity `describe` with a `DescriptionSchema` structured-output contract). All SDK calls isolated in `gemini_client.py`. Extension seams resolved by name via `registry.py`; built-in `LocalFolderSource` and `json_sidecar`/`manifest_csv`/`jsonl`/`review_jsonl` writers. `sync` mode runs concurrent real-time calls with manifest-based resume; `batch` mode assembles a sorted JSONL, submits one Gemini Batch job, polls, and resumes via `batch_state.json`. Low-confidence/malformed results are flagged `needs_review` and routed to `review.jsonl`. API key read only from `GEMINI_API_KEY`; sidecar writes are path-traversal-guarded; image/context text is framed as untrusted in the prompt. Ships configured for `gemini-3.1-flash-lite` / `gemini-3.1-pro-preview`.
**Plain:** First version of a tool that automatically writes alt text and descriptions for large batches of educational images so they're accessible to people with visual impairments.
**Why:** Institutions had thousands of images with no accessible descriptions and no practical way to generate them at scale — this makes it a one-command job that each organization can adapt to its own storage and database.
