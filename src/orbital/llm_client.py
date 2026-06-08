from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import requests
from dotenv import load_dotenv


DEFAULT_LLM_API_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_TIMEOUT_SECONDS = 25
DEFAULT_MAX_TOKENS = 2048
DEFAULT_MAX_COMPLETION_RETRIES = 1
INCOMPLETE_FINISH_REASONS = {"length", "max_tokens", "max_output_tokens"}


class LLMAPIError(RuntimeError):
    pass


@dataclass(frozen=True)
class LLMConfig:
    api_key: str | None
    model: str | None
    api_url: str = DEFAULT_LLM_API_URL
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    stream: bool = False
    max_tokens: int = DEFAULT_MAX_TOKENS
    max_completion_retries: int = DEFAULT_MAX_COMPLETION_RETRIES
    reasoning_effort: str | None = None

    @classmethod
    def from_env(cls) -> "LLMConfig":
        load_dotenv()
        api_url = os.getenv("LLM_API_URL", DEFAULT_LLM_API_URL)
        timeout = _env_int("LLM_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS)
        return cls(
            api_key=os.getenv("LLM_API_KEY"),
            model=os.getenv("LLM_MODEL"),
            api_url=api_url,
            timeout_seconds=timeout,
            stream=_env_bool("LLM_STREAM", default=False),
            max_tokens=_env_int("LLM_MAX_TOKENS", DEFAULT_MAX_TOKENS),
            max_completion_retries=_env_int(
                "LLM_MAX_COMPLETION_RETRIES", DEFAULT_MAX_COMPLETION_RETRIES
            ),
            reasoning_effort=os.getenv("LLM_REASONING_EFFORT")
            or _default_reasoning_effort(api_url),
        )

    @property
    def is_ready(self) -> bool:
        return bool(self.api_key and self.model and self.api_url)


class LLMClient:
    def __init__(self, config: LLMConfig | None = None, http_client=requests):
        self.config = config or LLMConfig.from_env()
        self.http_client = http_client

    @property
    def is_configured(self) -> bool:
        return self.config.is_ready

    def generate_text(
        self,
        messages: Sequence[Mapping[str, str]],
        required_markers: Sequence[str] | None = None,
        min_chars: int = 0,
    ) -> str:
        if not self.is_configured:
            raise LLMAPIError("API LLM não configurada. Defina LLM_API_KEY e LLM_MODEL.")

        messages_list = list(messages)
        result = self._request_text(messages_list)
        text = _require_text(result.text)

        for _ in range(max(0, self.config.max_completion_retries)):
            if not _needs_completion(text, result.finish_reason, required_markers, min_chars):
                break

            continuation_messages = _build_continuation_messages(
                messages_list,
                text,
                required_markers=required_markers,
                min_chars=min_chars,
            )
            result = self._request_text(continuation_messages)
            text = _join_continuation(text, _require_text(result.text))

        if _needs_completion(text, result.finish_reason, required_markers, min_chars):
            detail = f" finish_reason={result.finish_reason}." if result.finish_reason else ""
            missing = _missing_markers(text, required_markers or ())
            missing_detail = f" Seções ausentes: {', '.join(missing)}." if missing else ""
            raise LLMAPIError(
                "Resposta da API LLM veio incompleta após tentativa de continuação."
                f"{detail}{missing_detail}"
            )

        return text

    def _request_text(self, messages: Sequence[Mapping[str, str]]) -> "LLMTextResult":
        payload = {
            "model": self.config.model,
            "messages": list(messages),
            "temperature": 0.25,
            "max_tokens": self.config.max_tokens,
            "stream": self.config.stream,
        }
        if self.config.reasoning_effort:
            payload["reasoning_effort"] = self.config.reasoning_effort

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = self.http_client.post(
                self.config.api_url,
                headers=headers,
                json=payload,
                timeout=self.config.timeout_seconds,
                stream=self.config.stream,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise LLMAPIError(f"Falha ao chamar API LLM: {exc}") from exc

        if self.config.stream:
            return _extract_text_from_stream(response)
        return _extract_text_from_response(response)


@dataclass(frozen=True)
class LLMTextResult:
    text: str
    finish_reason: str | None = None


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "sim", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _default_reasoning_effort(api_url: str) -> str | None:
    if "generativelanguage.googleapis.com" in api_url:
        return "low"
    return None


def _extract_text_from_response(response) -> LLMTextResult:
    try:
        data = response.json()
    except ValueError:
        text = getattr(response, "text", "")
        if _looks_like_event_stream(response, text):
            return _extract_text_from_sse_lines(text.splitlines())
        raise LLMAPIError("Resposta da API LLM não é JSON válido.")

    try:
        choice = data["choices"][0]
        content = choice["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMAPIError("Resposta da API LLM sem conteúdo esperado.") from exc
    return LLMTextResult(
        text=_content_to_text(content),
        finish_reason=_finish_reason(choice),
    )


def _extract_text_from_stream(response) -> LLMTextResult:
    lines = response.iter_lines(decode_unicode=True)
    return _extract_text_from_sse_lines(lines)


def _extract_text_from_sse_lines(lines) -> LLMTextResult:
    parts: list[str] = []
    finish_reason: str | None = None

    for line in lines:
        if isinstance(line, bytes):
            line = line.decode("utf-8")
        line = str(line).strip()
        if not line:
            continue
        if line.startswith("data:"):
            line = line.removeprefix("data:").strip()
        if line == "[DONE]":
            break

        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        choice = _first_choice(event)
        if choice is None:
            continue

        finish_reason = _finish_reason(choice) or finish_reason
        content = _extract_chunk_content(choice)
        if content:
            parts.append(content)

    return LLMTextResult(text="".join(parts).strip(), finish_reason=finish_reason)


def _extract_chunk_content(choice: Mapping[str, Any]) -> str:
    delta = choice.get("delta") or {}
    if "content" in delta:
        return _content_to_text(delta["content"], strip=False)

    message = choice.get("message") or {}
    if "content" in message:
        return _content_to_text(message["content"], strip=False)

    return ""


def _first_choice(event: Mapping[str, Any]) -> Mapping[str, Any] | None:
    try:
        choice = event["choices"][0]
    except (KeyError, IndexError, TypeError):
        return None
    return choice if isinstance(choice, Mapping) else None


def _finish_reason(choice: Mapping[str, Any]) -> str | None:
    reason = choice.get("finish_reason")
    return str(reason) if reason is not None else None


def _content_to_text(content: Any, strip: bool = True) -> str:
    if isinstance(content, str):
        return content.strip() if strip else content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, Mapping):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        text = "".join(parts)
        return text.strip() if strip else text
    text = str(content)
    return text.strip() if strip else text


def _looks_like_event_stream(response, text: str) -> bool:
    headers = getattr(response, "headers", {}) or {}
    content_type = headers.get("content-type") or headers.get("Content-Type") or ""
    return "text/event-stream" in content_type or text.lstrip().startswith("data:")


def _require_text(text: str) -> str:
    if not text:
        raise LLMAPIError("Resposta da API LLM veio vazia.")
    return text


def _needs_completion(
    text: str,
    finish_reason: str | None,
    required_markers: Sequence[str] | None,
    min_chars: int,
) -> bool:
    if _is_incomplete_finish_reason(finish_reason):
        return True
    if min_chars and len(text) < min_chars:
        return True
    return bool(_missing_markers(text, required_markers or ()))


def _is_incomplete_finish_reason(finish_reason: str | None) -> bool:
    if finish_reason is None:
        return False
    return finish_reason.strip().lower() in INCOMPLETE_FINISH_REASONS


def _missing_markers(text: str, required_markers: Sequence[str]) -> list[str]:
    normalized = text.lower()
    return [marker for marker in required_markers if marker.lower() not in normalized]


def _build_continuation_messages(
    messages: Sequence[Mapping[str, str]],
    partial_text: str,
    required_markers: Sequence[str] | None,
    min_chars: int,
) -> list[dict[str, str]]:
    missing = _missing_markers(partial_text, required_markers or ())
    missing_hint = ""
    if missing:
        missing_hint = f" Inclua as seções faltantes: {', '.join(missing)}."

    length_hint = ""
    if min_chars:
        length_hint = f" O relatório final deve ter ao menos {min_chars} caracteres."

    return [
        *[dict(message) for message in messages],
        {"role": "assistant", "content": partial_text},
        {
            "role": "user",
            "content": (
                "A resposta anterior foi interrompida. Continue exatamente de onde parou, "
                "sem repetir o texto já gerado e sem reiniciar o relatório."
                f"{missing_hint}{length_hint}"
            ),
        },
    ]


def _join_continuation(current: str, continuation: str) -> str:
    left = current.rstrip()
    right = continuation.lstrip()
    if not left:
        return right.strip()
    if not right:
        return left.strip()
    if left[-1].isalnum() and right[0].isalnum():
        return f"{left}{right}".strip()
    return f"{left}\n{right}".strip()
