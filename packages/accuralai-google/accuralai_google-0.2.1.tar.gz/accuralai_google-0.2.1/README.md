# AccuralAI Google Backend

This package provides the Google GenAI backend adapter for the AccuralAI orchestration core. It wraps the official `google-genai` client so the orchestrator can target Gemini models with the same pipeline used for other local or remote backends.

## Features

- Async-compatible adapter that internally uses `google-genai`'s synchronous client.
- Configurable model, generation parameters, safety settings, and client options.
- Pulls API keys from configuration or the `GOOGLE_GENAI_API_KEY` environment variable.
- Converts Google usage metadata into AccuralAI's standard `Usage` payload.

## Installation

```bash
pip install accuralai-google
```

## Configuration

From `accuralai-core`, reference the backend ID you register under `backends`:

```toml
[backends.google]
plugin = "google"
[backends.google.options]
model = "gemini-1.5-pro"
generation_config = { temperature = 0.7 }
```

Provide an API key either in the options (`api_key = "...")` or via `GOOGLE_GENAI_API_KEY`.
