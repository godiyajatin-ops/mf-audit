
"""LLM interface with Gemini provider, deterministic mock, caching and usage logs."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import os
import re
import time

import yaml
from dotenv import load_dotenv
from tenacity import (
    Retrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)


ROOT = Path(__file__).resolve().parents[1]


class LLMClient(ABC):
    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.0,
        max_tokens: int = 400,
    ) -> str:
        raise NotImplementedError


class MockLLM(LLMClient):
    """Deterministic fixture client that selects a context sentence by word overlap."""

    def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.0,
        max_tokens: int = 400,
    ) -> str:
        context = prompt.split("CONTEXT:", 1)[-1].split("QUESTION:", 1)[0]
        question = prompt.split("QUESTION:", 1)[-1].split("ANSWER:", 1)[0]

        words = set(re.findall(r"[a-z0-9]+", question.lower()))
        candidates = []

        for block in context.split("\n"):
            citation = re.search(
                r"\[(\d+) p\.(\d+)(?:\s*\|[^\]]*)?\]", block
            )
            if not citation:
                continue

            for sentence in re.split(r"(?<=[.!?])\s+", block):
                overlap = len(
                    words & set(re.findall(r"[a-z0-9]+", sentence.lower()))
                )
                candidates.append(
                    (
                        overlap,
                        sentence.strip(),
                        f"[{citation.group(1)} p.{citation.group(2)}]",
                    )
                )

        if not candidates:
            return "Not found in the provided documents."

        _, sentence, citation = max(
            candidates, key=lambda row: (row[0], row[1])
        )
        return f"{sentence} {citation}"


def _retryable(exc: Exception) -> bool:
    """Retry transient network, rate-limit and server errors only."""

    status = getattr(
        exc,
        "status_code",
        getattr(exc, "code", None),
    )

    if status is not None:
        try:
            status = int(status)
        except (TypeError, ValueError):
            return False

        return status == 429 or 500 <= status < 600

    name = type(exc).__name__.lower()

    return any(
        term in name
        for term in (
            "timeout",
            "connection",
            "temporarily",
            "unavailable",
        )
    )


class GeminiLLM(LLMClient):
    """Gemini Developer API client with bounded retries and local caching."""

    def __init__(
        self,
        *,
        client,
        model: str,
        timeout_seconds: int = 300,
        max_retries: int = 3,
        cache_enabled: bool = True,
        cache_dir: Path | None = None,
        usage_log: Path | None = None,
    ):
        self.client = client
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.cache_enabled = cache_enabled
        self.last_usage = None

        self.cache_dir = cache_dir or ROOT / "data" / "cache" / "llm"
        self.usage_log = usage_log or ROOT / "logs" / "llm_usage.jsonl"

    def _cache_path(
        self, prompt: str, temperature: float, max_tokens: int
    ) -> Path:
        cache_identity = json.dumps(
            [self.model, prompt, float(temperature), int(max_tokens)],
            ensure_ascii=False,
            separators=(",", ":"),
        )
        digest = sha256(cache_identity.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{digest}.json"

    def _write_usage(self, record: dict) -> None:
        """Append metadata only. Never log prompts, responses or credentials."""
        self.usage_log.parent.mkdir(parents=True, exist_ok=True)

        safe_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "provider": "gemini",
            "model": self.model,
            **record,
        }

        with self.usage_log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(safe_record) + "\n")

    def _generate_with_retry(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
    ):
        retryer = Retrying(
            stop=stop_after_attempt(self.max_retries + 1),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            retry=retry_if_exception(_retryable),
            reraise=True,
        )

        for attempt in retryer:
            with attempt:
                return self.client.interactions.create(
                    model=self.model,
                    input=prompt,
                    store=False,
                    generation_config={
                        "temperature": temperature,
                        "max_output_tokens": max_tokens,
                    },
                )

    def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.0,
        max_tokens: int = 400,
    ) -> str:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Prompt must be a non-empty string")

        self.last_usage = None
        cache_path = self._cache_path(prompt, temperature, max_tokens)

        if self.cache_enabled and cache_path.exists():
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            self.last_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
            self._write_usage(
                {"status": "cache_hit", "latency_ms": 0,
                 "prompt_tokens": 0, "output_tokens": 0, "total_tokens": 0}
            )
            return cached["text"]

        started = time.perf_counter()

        try:
            response = self._generate_with_retry(
                prompt, temperature, max_tokens
            )

            status = getattr(response, "status", None)
            if status is not None and str(status).lower() != "completed":
                raise RuntimeError(f"Gemini interaction did not complete (status={status})")

            text = getattr(response, "output_text", None)
            if not text:
                steps = getattr(response, "steps", None) or []
                pieces = []
                for step in steps:
                    if getattr(step, "type", None) != "model_output":
                        continue
                    content = getattr(step, "content", None) or []
                    for item in content:
                        value = getattr(item, "text", None)
                        if value:
                            pieces.append(value)
                text = "".join(pieces)
            if not text or not text.strip():
                raise RuntimeError("Gemini returned an empty response")

            usage = getattr(response, "usage", None)
            prompt_tokens = getattr(usage, "total_input_tokens", None)
            output_tokens = getattr(usage, "total_output_tokens", None)
            total_tokens = getattr(usage, "total_tokens", None)
            self.last_usage = {
                "input_tokens": prompt_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
            }

            latency_ms = round(
                (time.perf_counter() - started) * 1000, 2
            )

            self._write_usage({
                "status": "success",
                "latency_ms": latency_ms,
                "prompt_tokens": prompt_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
            })

            if self.cache_enabled:
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(
                    json.dumps({"text": text}, ensure_ascii=False),
                    encoding="utf-8",
                )

            return text

        except Exception as exc:
            latency_ms = round(
                (time.perf_counter() - started) * 1000, 2
            )
            try:
                self._write_usage({
                    "status": "error",
                    "error_type": type(exc).__name__,
                    "latency_ms": latency_ms,
                })
            except OSError:
                pass
            raise


def configured_client(
    config_path: Path | None = None,
    *,
    timeout_seconds_override: int | None = None,
    max_retries_override: int | None = None,
    cache_enabled_override: bool | None = None,
):
    """Build the configured provider client. Fails closed without credentials."""
    load_dotenv(ROOT / ".env")

    config_path = config_path or ROOT / "config.yaml"
    config = yaml.safe_load(
        config_path.read_text(encoding="utf-8")
    ) or {}

    llm_config = config.get("llm", {})

    provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    api_key = os.getenv("LLM_API_KEY", "").strip()

    if not provider or not api_key:
        raise RuntimeError(
            "LLM provider or API credentials are missing"
        )

    if provider != "gemini":
        raise ValueError(f"Unsupported LLM provider: {provider}")

    model = llm_config.get("model", "").strip()
    if not model:
        raise ValueError("llm.model is missing from config.yaml")

    from google import genai
    from google.genai import types

    timeout_seconds = int(
        timeout_seconds_override
        if timeout_seconds_override is not None
        else llm_config.get("timeout_seconds", 60)
    )
    max_retries = int(
        max_retries_override
        if max_retries_override is not None
        else llm_config.get("max_retries", 3)
    )
    cache_enabled = bool(
        cache_enabled_override
        if cache_enabled_override is not None
        else llm_config.get("cache_enabled", True)
    )
    if timeout_seconds < 1:
        raise ValueError("timeout_seconds must be positive")
    if max_retries < 0:
        raise ValueError("max_retries cannot be negative")

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            timeout=timeout_seconds * 1000,
            retry_options=types.HttpRetryOptions(attempts=1),
        ),
    )

    # The 3.x Interactions layer has its own generated retry config. HttpOptions
    # alone does not reliably override its backoff defaults across patch releases.
    interactions = getattr(client, "interactions", None)
    sdk_configuration = getattr(interactions, "sdk_configuration", None)
    retry_config = getattr(sdk_configuration, "retry_config", None)
    if retry_config is not None and hasattr(retry_config, "max_retries"):
        retry_config.max_retries = 0
        retry_config.retry_connection_errors = False

    return GeminiLLM(
        client=client,
        model=model,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
        cache_enabled=cache_enabled,
    )
