import sys
import types
from dataclasses import dataclass
from typing import Any, Dict

import pytest

from accuralai_core.contracts.models import GenerateRequest, Usage
from accuralai_core.contracts.errors import ConfigurationError

# Prepare stub google.genai module before importing backend implementation.
google_pkg = types.ModuleType("google")


@dataclass
class DummyResponse:
    text: str
    usage_metadata: Dict[str, Any]
    model: str = "gemini-test"
    candidates: list[Any] | None = None


class DummyModels:
    def __init__(self, client: "DummyClient") -> None:
        self.client = client
        self.last_kwargs: Dict[str, Any] | None = None
        self.count_calls = 0

    def generate_content(self, *, model: str, contents, **kwargs):
        self.last_kwargs = {"model": model, "contents": contents, **kwargs}
        return DummyResponse(
            text="Generated text",
            usage_metadata={
                "prompt_token_count": 5,
                "candidates_token_count": 7,
                "total_token_count": 12,
            },
            model=model,
        )

    def count_tokens(self, *, model: str, contents):
        self.count_calls += 1
        return {"total_tokens": 5}


class DummyClient:
    last_init: Dict[str, Any] | None = None

    def __init__(self, *, api_key: str, **client_options: Any) -> None:
        self.api_key = api_key
        self.client_options = client_options
        DummyClient.last_init = {"api_key": api_key, "client_options": client_options}
        self.models = DummyModels(self)


google_pkg.genai = types.ModuleType("google.genai")
google_pkg.genai.Client = DummyClient  # type: ignore[attr-defined]


@dataclass
class DummyFunctionDeclaration:
    name: str
    description: str | None = None
    parameters: Any | None = None


@dataclass
class DummyTool:
    function_declarations: list


class DummyGenerateContentConfig:
    def __init__(self, **kwargs: Any) -> None:
        self.__dict__.update(kwargs)


types_module = types.SimpleNamespace(
    FunctionDeclaration=DummyFunctionDeclaration,
    Tool=DummyTool,
    GenerateContentConfig=DummyGenerateContentConfig,
)

google_pkg.genai.types = types_module  # type: ignore[attr-defined]

sys.modules.setdefault("google", google_pkg)
sys.modules.setdefault("google.genai", google_pkg.genai)

from accuralai_google.backend import GoogleBackend, build_google_backend  # noqa: E402


@pytest.mark.anyio
async def test_build_google_backend_uses_configured_api_key():
    backend = await build_google_backend(config={"api_key": "config-key", "model": "gemini-1.5-pro"})
    assert isinstance(backend, GoogleBackend)
    assert DummyClient.last_init is not None
    assert DummyClient.last_init["api_key"] == "config-key"


@pytest.mark.anyio
async def test_google_backend_generate_maps_usage(monkeypatch):
    backend = await build_google_backend(
        config={
            "api_key": "direct-key",
            "model": "gemini-2.5-flash-lite",
            "generation_config": {"temperature": 0.1},
            "request_metadata": {"purpose": "unit-test"},
        }
    )
    request = GenerateRequest(prompt="Hello Gemini", parameters={"temperature": 0.4})

    response = await backend.generate(request, routed_to="google")

    assert response.output_text == "Generated text"
    assert isinstance(response.usage, Usage)
    assert response.usage.prompt_tokens == 5
    assert response.usage.completion_tokens == 7
    assert response.usage.total_tokens == 12
    assert response.metadata.get("tool_calls") == []
    # Ensure request parameters merged into generation config.
    assert backend.client.models.last_kwargs is not None
    config = backend.client.models.last_kwargs["config"]
    assert config.temperature == 0.4
    assert backend.client.models.last_kwargs["request_metadata"]["purpose"] == "unit-test"
    assert backend.client.models.count_calls == 0


@pytest.mark.anyio
async def test_build_google_backend_requires_api_key(monkeypatch):
    monkeypatch.delenv("GOOGLE_GENAI_API_KEY", raising=False)
    with pytest.raises(ConfigurationError):
        await build_google_backend(config={"model": "gemini-2.5-flash-lite"})


@pytest.mark.anyio
async def test_backend_filters_kwargs_for_strict_signature():
    backend = await build_google_backend(config={"api_key": "strict-key", "model": "gemini-2.5-flash-lite"})

    class StrictModels:
        def __init__(self) -> None:
            self.calls = 0

        def generate_content(self, *, model: str, contents, **kwargs):
            self.calls += 1
            return DummyResponse(
                text="Strict response",
                usage_metadata={
                    "prompt_token_count": 1,
                    "candidates_token_count": 1,
                    "total_token_count": 2,
                },
                model=model,
            )

    strict_models = StrictModels()
    backend.client.models = strict_models  # type: ignore[attr-defined]

    request = GenerateRequest(prompt="Hi")
    response = await backend.generate(request, routed_to="google")

    assert response.output_text == "Strict response"
    assert strict_models.calls == 1


@pytest.mark.anyio
async def test_google_backend_tool_calls_extracted(monkeypatch):
    backend = await build_google_backend(config={"api_key": "tool-key", "model": "gemini-2.5-flash-lite"})

    class ToolCallModels(DummyModels):
        def generate_content(self, *, model: str, contents, **kwargs):
            self.last_kwargs = {"model": model, "contents": contents, **kwargs}
            return DummyResponse(
                text="",
                usage_metadata={"prompt_token_count": 0, "candidates_token_count": 0, "total_token_count": 0},
                model=model,
                candidates=[
                    {
                        "content": {
                            "parts": [
                                {
                                    "functionCall": {
                                        "name": "write_file",
                                        "args": {"path": "note.txt", "text": "hello"},
                                    }
                                }
                            ]
                        }
                    }
                ],
            )

    backend.client.models = ToolCallModels(backend.client)  # type: ignore[attr-defined]

    request = GenerateRequest(prompt="trigger tool", tools=[{"name": "write_file", "parameters": {}}])
    response = await backend.generate(request, routed_to="google")

    calls = response.metadata.get("tool_calls")
    assert calls and calls[0]["name"] == "write_file"
    assert calls[0]["arguments"]["path"] == "note.txt"


@pytest.mark.anyio
async def test_google_backend_estimates_tokens_when_missing(monkeypatch):
    backend = await build_google_backend(config={"api_key": "count-key", "model": "gemini-2.5-flash-lite"})

    class MissingUsageModels(DummyModels):
        def generate_content(self, *, model: str, contents, **kwargs):
            self.last_kwargs = {"model": model, "contents": contents, **kwargs}
            return DummyResponse(
                text="No usage metadata",
                usage_metadata={
                    "prompt_token_count": 0,
                    "candidates_token_count": 0,
                    "total_token_count": 0,
                },
                model=model,
            )

        def count_tokens(self, *, model: str, contents):
            self.count_calls += 1
            return {"total_tokens": 9}

    backend.client.models = MissingUsageModels(backend.client)  # type: ignore[attr-defined]

    request = GenerateRequest(prompt="Count please")
    response = await backend.generate(request, routed_to="google")

    assert response.usage.prompt_tokens == 9
    assert response.usage.total_tokens >= 9
