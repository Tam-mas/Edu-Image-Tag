# Changelog

### [2026-07-02 21:10] Added

**Tech:** Initial release of the `edu_image_tag` package — CLI, `GeminiClient`, pluggable `InputSource`/`OutputWriter`, sync + batch runners, YAML config, 48 passing tests
**Dev:** Two-stage Gemini pipeline (optional cheap `classify` → high-fidelity `describe` with a `DescriptionSchema` structured-output contract). All SDK calls isolated in `gemini_client.py`. Extension seams resolved by name via `registry.py`; built-in `LocalFolderSource` and `json_sidecar`/`manifest_csv`/`jsonl`/`review_jsonl` writers. `sync` mode runs concurrent real-time calls with manifest-based resume; `batch` mode assembles a sorted JSONL, submits one Gemini Batch job, polls, and resumes via `batch_state.json`. Low-confidence/malformed results are flagged `needs_review` and routed to `review.jsonl`. API key read only from `GEMINI_API_KEY`; sidecar writes are path-traversal-guarded; image/context text is framed as untrusted in the prompt. Ships configured for `gemini-3.1-flash-lite` / `gemini-3.1-pro-preview`.
**Plain:** First version of a tool that automatically writes alt text and descriptions for large batches of educational images so they're accessible to people with visual impairments.
**Why:** Institutions had thousands of images with no accessible descriptions and no practical way to generate them at scale — this makes it a one-command job that each organization can adapt to its own storage and database.
