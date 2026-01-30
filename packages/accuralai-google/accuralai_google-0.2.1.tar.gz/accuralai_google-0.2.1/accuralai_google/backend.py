"""Google GenAI backend adapter implementation."""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence
from uuid import uuid4

from pydantic import BaseModel, Field, ValidationError

from accuralai_core.config.schema import BackendSettings
from accuralai_core.contracts.errors import BackendError, ConfigurationError
from accuralai_core.contracts.models import GenerateRequest, GenerateResponse, Usage
from accuralai_core.contracts.protocols import Backend

LOGGER = logging.getLogger("accuralai.google")

try:  # pragma: no cover - exercised via tests with monkeypatched dependency
    from google import genai  # type: ignore[attr-defined]
    from google.genai import types as genai_types
except ImportError:  # pragma: no cover - handled during backend factory
    genai = None  # type: ignore[assignment]
    genai_types = None  # type: ignore[assignment]


class GoogleOptions(BaseModel):
    """Configuration for Google GenAI backend."""

    model: str = "gemini-2.5-flash-lite"
    api_key: str | None = None
    system_instruction: str | None = None
    generation_config: Dict[str, Any] = Field(default_factory=dict)
    safety_settings: Sequence[Dict[str, Any]] = Field(default_factory=list)
    tools: Sequence[Dict[str, Any]] = Field(default_factory=list)
    client_options: Dict[str, Any] = Field(default_factory=dict)
    request_metadata: Dict[str, str] = Field(default_factory=dict)


def _serialize_structure(data: Any) -> Any:
    """Convert SDK objects into built-in types for metadata."""
    if isinstance(data, (str, int, float, bool)) or data is None:
        return data
    if isinstance(data, Mapping):
        return {key: _serialize_structure(value) for key, value in data.items()}
    if isinstance(data, (list, tuple, set)):
        return [_serialize_structure(item) for item in data]
    if hasattr(data, "to_dict"):
        try:
            return _serialize_structure(data.to_dict())  # type: ignore[misc]
        except Exception:
            pass
    if hasattr(data, "__dict__"):
        return _serialize_structure(vars(data))
    return repr(data)


def _history_to_contents(history: Iterable[Mapping[str, Any]]) -> list[Dict[str, Any]]:
    """Transform request history entries into Google content payloads."""
    formatted: list[Dict[str, Any]] = []
    for message in history:
        role = str(message.get("role") or message.get("speaker") or "user")
        norm_role = "model" if role == "assistant" else role
        if "tool_calls" in message:
            calls = message.get("tool_calls") or []
            parts = []
            if isinstance(calls, Mapping):
                calls = [calls]
            for call in calls:
                name = call.get("name")
                arguments = call.get("arguments") or {}
                parts.append({"function_call": {"name": name, "args": arguments}})
            formatted.append({"role": norm_role, "parts": parts})
            continue

        if norm_role == "tool":
            response_payload = message.get("content")
            tool_name = message.get("name")
            response = response_payload
            if isinstance(response, str):
                try:
                    response = json.loads(response)
                except json.JSONDecodeError:
                    response = {"content": response}

            parts = [
                {
                    "function_response": {
                        "name": tool_name,
                        "response": response,
                    }
                }
            ]
            formatted.append({"role": norm_role, "parts": parts})
            continue

        text = message.get("content") or message.get("text") or message.get("message")
        if isinstance(text, list):
            parts = [{"text": str(part)} for part in text]
        else:
            parts = [{"text": str(text or "")}]
        formatted.append({"role": norm_role, "parts": parts})
    return formatted


def _merge_generation_config(base_config: Mapping[str, Any], request_params: Mapping[str, Any]) -> Dict[str, Any]:
    """Combine backend defaults with per-request generation parameters."""
    if not base_config and not request_params:
        return {}
    merged: Dict[str, Any] = dict(base_config or {})
    for key, value in (request_params or {}).items():
        if value is not None and key != "model":  # Exclude model from generation config
            merged[key] = value
    return merged


@dataclass(slots=True)
class GoogleBackend(Backend):
    """AccuralAI backend implementation for Google GenAI."""

    options: GoogleOptions
    client: Any = field(init=False)

    def __post_init__(self) -> None:
        if genai is None or genai_types is None:
            raise ConfigurationError(
                "google-genai is not installed. Install the 'accuralai-google' extra to enable this backend."
            )

        api_key = self.options.api_key or os.getenv("GOOGLE_GENAI_API_KEY")
        if not api_key:
            raise ConfigurationError("Google GenAI API key missing; provide via options.api_key or GOOGLE_GENAI_API_KEY.")

        try:
            self.client = genai.Client(api_key=api_key, **self.options.client_options)
        except TypeError as error:  # pragma: no cover - depends on client signature
            raise ConfigurationError(f"Invalid client options for google-genai: {error}") from error

    async def generate(self, request: GenerateRequest, *, routed_to: str) -> GenerateResponse:
        """Generate a response using Google GenAI."""
        contents = self._build_contents(request)
        try:
            response = await asyncio.to_thread(self._generate_sync, request, contents)
        except Exception as error:  # pragma: no cover - translated for clarity
            raise BackendError(f"Google GenAI request failed: {error}", cause=error) from error

        return self._build_response(request, response, contents)

    def _build_contents(self, request: GenerateRequest) -> list[Dict[str, Any]]:
        contents = _history_to_contents(request.history or [])
        contents.append({"role": "user", "parts": [{"text": request.prompt}]})
        return contents

    def _generate_sync(self, request: GenerateRequest, contents: list[Dict[str, Any]]) -> Any:
        kwargs: Dict[str, Any] = {}
        generation_config = _merge_generation_config(self.options.generation_config, request.parameters)
        config_kwargs: Dict[str, Any] = {}
        if generation_config:
            for forbidden in ("function_calling_config", "automatic_function_calling", "tool_config", "model"):
                generation_config.pop(forbidden, None)
            config_kwargs.update(generation_config)

        safety_settings = list(self.options.safety_settings)
        if safety_settings:
            kwargs["safety_settings"] = safety_settings

        tools = self._build_tools(request)
        if tools:
            config_kwargs["tools"] = tools
            LOGGER.debug(f"Added {len(tools)} tools to generation config")

        system_instruction = request.system_prompt or self.options.system_instruction
        if system_instruction:
            kwargs["system_instruction"] = system_instruction

        if config_kwargs:
            kwargs["config"] = genai_types.GenerateContentConfig(**config_kwargs)

        if self.options.request_metadata:
            kwargs["request_metadata"] = dict(self.options.request_metadata)

        # Determine which model to use - check request parameters first, then metadata, then default
        model = self._determine_model(request)

        LOGGER.debug("Dispatching Google GenAI request with model '%s'", model)
        method = getattr(self.client.models, "generate_content")
        prepared_kwargs = self._prepare_generation_kwargs(method, kwargs)
        return method(model=model, contents=contents, **prepared_kwargs)

    def _build_response(
        self,
        request: GenerateRequest,
        result: Any,
        contents: list[Dict[str, Any]],
    ) -> GenerateResponse:
        output_text = self._extract_text(result)
        finish_reason = self._extract_finish_reason(result)
        usage = self._extract_usage(result, contents, request)
        tool_calls = self._extract_tool_calls(result)

        if tool_calls:
            finish_reason = "stop"  # Tool calls indicate successful completion
            if not output_text:
                output_text = "[tool-call]"

        metadata = {
            "model": getattr(result, "model", self._determine_model(request)),
            "safety_ratings": self._extract_safety_ratings(result),
            "tool_calls": tool_calls,
        }

        return GenerateResponse(
            id=uuid4(),
            request_id=request.id,
            output_text=output_text,
            finish_reason=finish_reason,
            usage=usage,
            latency_ms=0,
            metadata=metadata,
            validator_events=[],
        )

    def _extract_text(self, result: Any) -> str:
        if hasattr(result, "text"):
            text = getattr(result, "text")
            if callable(text):
                try:
                    text = text()
                except TypeError:
                    text = text  # text was already a property
            return str(text or "")

        if isinstance(result, Mapping) and "text" in result:
            return str(result.get("text") or "")

        candidates = self._extract_candidates(result)
        chunks: list[str] = []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            if isinstance(candidate, Mapping):
                content = content or candidate.get("content")
            if content is None:
                continue
            parts = getattr(content, "parts", None)
            if isinstance(content, Mapping):
                parts = parts or content.get("parts")
            if not parts:
                continue
            for part in parts:
                # Skip function_call parts to avoid SDK warnings
                if hasattr(part, "function_call") or (isinstance(part, Mapping) and "function_call" in part):
                    continue
                text = getattr(part, "text", None)
                if isinstance(part, Mapping):
                    text = text or part.get("text")
                if text:
                    chunks.append(str(text))
        return "".join(chunks)

    def _extract_finish_reason(self, result: Any) -> str:
        candidates = self._extract_candidates(result)
        for candidate in candidates:
            finish_reason = getattr(candidate, "finish_reason", None)
            if isinstance(candidate, Mapping):
                finish_reason = finish_reason or candidate.get("finish_reason")
            if finish_reason:
                return self._normalise_finish_reason(finish_reason)
        return "stop"

    def _normalise_finish_reason(self, value: Any) -> str:
        """Map SDK-specific finish reasons to AccuralAI literals."""
        raw = value
        if hasattr(raw, "name"):
            raw = raw.name
        elif hasattr(raw, "value"):
            candidate = getattr(raw, "value")
            if isinstance(candidate, str):
                raw = candidate
        text = str(raw).lower()
        mapping = {
            "finishreason.stop": "stop",
            "stop": "stop",
            "finished": "stop",
            "success": "stop",
            "length": "length",
            "max_tokens": "length",
            "maxoutputtokens": "length",
            "content_filter": "content_filter",
            "safety": "content_filter",
            "blocked": "content_filter",
            "error": "error",
            "tool_calls": "stop",  # Map tool_calls to stop since it's not a valid finish_reason
        }
        return mapping.get(text, "stop")

    def _extract_usage(self, result: Any, contents: list[Dict[str, Any]], request: GenerateRequest) -> Usage:
        usage_metadata = getattr(result, "usage_metadata", None)
        if isinstance(result, Mapping):
            usage_metadata = usage_metadata or result.get("usage_metadata")
        if usage_metadata is None and hasattr(result, "usage"):
            usage_metadata = getattr(result, "usage")

        if isinstance(usage_metadata, Mapping):
            get = usage_metadata.get  # type: ignore[assignment]
        else:
            get = lambda key, default=None: getattr(usage_metadata, key, default) if usage_metadata else default  # noqa: E731

        prompt_tokens = int(get("prompt_token_count", 0) or get("prompt_tokens", 0) or 0)
        completion_tokens = int(
            get("candidates_token_count", 0) or get("completion_tokens", 0) or get("output_tokens", 0) or 0
        )
        total_tokens = int(get("total_token_count", 0) or get("total_tokens", prompt_tokens + completion_tokens))
        extra = {}
        if usage_metadata:
            extra = _serialize_structure(usage_metadata)

        if prompt_tokens == 0:
            estimate = self._estimate_prompt_tokens(contents, request)
            if estimate:
                prompt_tokens = estimate
                if total_tokens == 0:
                    total_tokens = estimate + completion_tokens
        if total_tokens == 0 and prompt_tokens and completion_tokens:
            total_tokens = prompt_tokens + completion_tokens
        if completion_tokens == 0 and total_tokens and prompt_tokens:
            completion_tokens = max(total_tokens - prompt_tokens, 0)

        return Usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            extra=extra if isinstance(extra, Mapping) else {"raw": extra},
        )

    def _extract_tool_calls(self, result: Any) -> list[Dict[str, Any]]:
        tool_calls: list[Dict[str, Any]] = []
        for candidate in self._extract_candidates(result):
            content = self._get_field(candidate, "content")
            parts = self._get_field(content, "parts")
            if not parts:
                continue
            for part in parts:
                function_call = self._get_field(part, "function_call", "functionCall")
                if not function_call:
                    continue
                name = self._get_field(function_call, "name")
                if not name:
                    continue
                raw_args = self._get_field(function_call, "args", "arguments")
                tool_calls.append(
                    {
                        "id": f"call_{uuid4().hex}",
                        "name": str(name),
                        "arguments": self._parse_arguments(raw_args),
                    }
                )
        return tool_calls

    def _parse_arguments(self, payload: Any) -> Dict[str, Any]:
        if payload is None:
            return {}
        if hasattr(payload, "to_dict"):
            try:
                payload = payload.to_dict()
            except Exception:  # pragma: no cover - best effort conversion
                pass
        if isinstance(payload, Mapping):
            return {str(key): _serialize_structure(value) for key, value in payload.items()}
        if isinstance(payload, str):
            try:
                parsed = json.loads(payload)
                if isinstance(parsed, Mapping):
                    return dict(parsed)
            except json.JSONDecodeError:
                return {"raw": payload}
        serialized = _serialize_structure(payload)
        if isinstance(serialized, Mapping):
            return dict(serialized)
        if serialized is None:
            return {}
        return {"raw": serialized}

    def _get_field(self, obj: Any, *names: str) -> Any:
        """Retrieve attribute or mapping key value from mixed SDK structures."""
        if obj is None:
            return None
        for name in names:
            attr = getattr(obj, name, None)
            if attr is not None:
                return attr
        if isinstance(obj, Mapping):
            for name in names:
                if name in obj and obj[name] is not None:
                    return obj[name]
            # Some SDK objects expose camelCase keys when accessed like dicts
            for name in names:
                alt = name.replace("_", "")
                if alt != name and alt in obj and obj[alt] is not None:
                    return obj[alt]
        return None

    def _build_tools(self, request: GenerateRequest) -> list[genai_types.Tool]:
        declarations: list[Any] = []
        if self.options.tools:
            if isinstance(self.options.tools, list):
                declarations.extend(self.options.tools)
        if request.tools:
            declarations.extend(request.tools)
        
        LOGGER.debug(f"Building tools from {len(declarations)} declarations")

        tools: list[genai_types.Tool] = []
        for entry in declarations:
            tool = self._convert_tool_entry(entry)
            if tool:
                tools.append(tool)
            else:
                LOGGER.debug(f"Failed to convert tool entry: {entry}")
        LOGGER.debug(f"Converted {len(tools)} tools for Google GenAI")
        return tools

    def _convert_tool_entry(self, entry: Any) -> Optional[genai_types.Tool]:
        if isinstance(entry, genai_types.Tool):
            return entry
        if callable(entry):
            return entry  # SDK accepts callables directly
        if isinstance(entry, Mapping):
            declarations = []
            if "function_declarations" in entry:
                for decl in entry.get("function_declarations", []):
                    converted = self._convert_function_declaration(decl)
                    if converted:
                        declarations.append(converted)
            else:
                LOGGER.debug(f"Converting tool entry as single function declaration: {entry}")
                converted = self._convert_function_declaration(entry)
                if converted:
                    declarations.append(converted)
            if declarations:
                return genai_types.Tool(function_declarations=declarations)
        return None

    def _convert_function_declaration(self, decl: Mapping[str, Any]) -> Optional[genai_types.FunctionDeclaration]:
        # Handle OpenAI-style format with "function" wrapper
        if "function" in decl and isinstance(decl["function"], Mapping):
            decl = decl["function"]
        
        name = decl.get("name")
        if not name:
            LOGGER.debug(f"No 'name' field in declaration: {decl}")
            return None
        description = decl.get("description")
        parameters = decl.get("parameters")
        if isinstance(parameters, dict):
            parameters.pop("additionalProperties", None)
        
        LOGGER.debug(f"Converted function declaration: {name}")
        return genai_types.FunctionDeclaration(
            name=name,
            description=description,
            parameters=parameters,
        )

    def _estimate_prompt_tokens(self, contents: list[Dict[str, Any]], request: GenerateRequest) -> Optional[int]:
        counter = getattr(self.client.models, "count_tokens", None)
        if counter is None:
            return None
        try:
            model = self._determine_model(request)
            result = counter(model=model, contents=contents)
        except Exception as error:  # pragma: no cover - SDK failure
            LOGGER.debug("Token counting failed: %s", error)
            return None

        total = None
        if isinstance(result, Mapping):
            total = result.get("total_tokens")
        else:
            total = getattr(result, "total_tokens", None)

        if total is None:
            return None
        try:
            return int(total)
        except (TypeError, ValueError):
            return None

    def _extract_safety_ratings(self, result: Any) -> Any:
        candidates = self._extract_candidates(result)
        for candidate in candidates:
            ratings = getattr(candidate, "safety_ratings", None)
            if isinstance(candidate, Mapping):
                ratings = ratings or candidate.get("safety_ratings")
            if ratings:
                return _serialize_structure(ratings)
        ratings = getattr(result, "safety_ratings", None)
        if isinstance(result, Mapping):
            ratings = ratings or result.get("safety_ratings")
        if ratings:
            return _serialize_structure(ratings)
        return None

    @staticmethod
    def _extract_candidates(result: Any) -> Sequence[Any]:
        candidates = getattr(result, "candidates", None)
        if candidates is None and isinstance(result, Mapping):
            candidates = result.get("candidates")
        if candidates is None:
            return []
        return list(candidates)

    def _prepare_generation_kwargs(self, method: Any, candidates: Dict[str, Any]) -> Dict[str, Any]:
        """Filter and rename kwargs to match the client method signature."""
        sanitized: Dict[str, Any] = {}
        try:
            signature = inspect.signature(method)
        except (TypeError, ValueError):
            return {key: value for key, value in candidates.items() if value is not None}

        params = signature.parameters
        accepts_var_kw = any(param.kind == inspect.Parameter.VAR_KEYWORD for param in params.values())
        accepted_names = set(params.keys())

        for key, value in candidates.items():
            if value is None:
                continue

            if key in accepted_names or accepts_var_kw:
                sanitized[key] = value
                continue

            if key == "generation_config":
                if "config" in accepted_names:
                    sanitized["config"] = value
                elif "generationConfig" in accepted_names:
                    sanitized["generationConfig"] = value
                continue

            if key == "safety_settings" and "safetySettings" in accepted_names:
                sanitized["safetySettings"] = value
                continue

            if key == "system_instruction" and "systemInstruction" in accepted_names:
                sanitized["systemInstruction"] = value
                continue

            if key == "request_metadata":
                if "request_metadata" in accepted_names:
                    sanitized["request_metadata"] = value
                elif "requestOptions" in accepted_names:
                    sanitized["requestOptions"] = {"metadata": value}
                elif "request_options" in accepted_names:
                    sanitized["request_options"] = {"metadata": value}
                continue

            if key == "tools" and "tool_config" in accepted_names:
                sanitized["tool_config"] = value

        return sanitized

    def _determine_model(self, request: GenerateRequest) -> str:
        """Determine which model to use for this request."""
        # Check request parameters first (highest priority)
        if "model" in request.parameters:
            return str(request.parameters["model"])
        
        # Check metadata as fallback
        if "model" in request.metadata:
            return str(request.metadata["model"])
        
        # Use configured default
        return self.options.model


async def build_google_backend(
    *,
    config: BackendSettings | Mapping[str, Any] | None = None,
    backend_id: str | None = None,
    **_: Any,
) -> Backend:
    """Entry point registered for the Google GenAI backend."""
    if genai is None:
        raise ConfigurationError(
            "google-genai is not available. Install the package to use the Google backend."
        )

    options_payload: Mapping[str, Any] | None = None
    if isinstance(config, BackendSettings):
        options_payload = config.options or {}
    elif isinstance(config, Mapping):
        options_payload = dict(config)

    try:
        options = GoogleOptions.model_validate(options_payload or {})
    except ValidationError as error:
        raise ConfigurationError(f"Invalid Google backend configuration: {error}") from error

    LOGGER.info("Configuring Google GenAI backend '%s' with model '%s'", backend_id or "google", options.model)
    return GoogleBackend(options=options)
