from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping, Sequence

import requests
from dotenv import load_dotenv


DEFAULT_LLM_API_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_TIMEOUT_SECONDS = 25


class LLMAPIError(RuntimeError):
    pass


@dataclass(frozen=True)
class LLMConfig:
    api_key: str | None
    model: str | None
    api_url: str = DEFAULT_LLM_API_URL
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS

    @classmethod
    def from_env(cls) -> "LLMConfig":
        load_dotenv()
        timeout = os.getenv("LLM_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS))
        return cls(
            api_key=os.getenv("LLM_API_KEY"),
            model=os.getenv("LLM_MODEL"),
            api_url=os.getenv("LLM_API_URL", DEFAULT_LLM_API_URL),
            timeout_seconds=int(timeout),
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

    def generate_text(self, messages: Sequence[Mapping[str, str]]) -> str:
        if not self.is_configured:
            raise LLMAPIError("API LLM não configurada. Defina LLM_API_KEY e LLM_MODEL.")

        payload = {
            "model": self.config.model,
            "messages": list(messages),
            "temperature": 0.25,
            "max_tokens": 900,
        }
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
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise LLMAPIError(f"Falha ao chamar API LLM: {exc}") from exc

        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMAPIError("Resposta da API LLM sem conteúdo esperado.") from exc

        text = str(content).strip()
        if not text:
            raise LLMAPIError("Resposta da API LLM veio vazia.")
        return text
