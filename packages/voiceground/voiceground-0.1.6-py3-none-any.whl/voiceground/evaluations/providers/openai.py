"""OpenAI evaluator implementation."""

import httpx
from openai import AsyncOpenAI

from voiceground.evaluations.base import (
    BaseEvaluator,
    BooleanEvaluationResponse,
    CategoryEvaluationResponse,
)


class OpenAIEvaluator(BaseEvaluator):
    """OpenAI-based evaluator using AsyncOpenAI client with structured outputs."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.0,
        max_tokens: int = 500,
    ):
        """Initialize OpenAI evaluator.

        Args:
            api_key: OpenAI API key. If None, uses OPENAI_API_KEY env var.
            base_url: Custom base URL for OpenAI API.
            model: Model to use for evaluation (default: gpt-4o-mini for structured outputs).
            temperature: Sampling temperature (default: 0.0 for deterministic).
            max_tokens: Maximum tokens in response.
        """
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            http_client=httpx.AsyncClient(
                limits=httpx.Limits(
                    max_keepalive_connections=100,
                    max_connections=1000,
                    keepalive_expiry=None,
                )
            ),
        )
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

    async def evaluate(self, prompt: str) -> str:
        """Evaluate using OpenAI API (fallback for custom evaluators)."""
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )
        return response.choices[0].message.content or ""

    async def evaluate_boolean(self, prompt: str) -> "BooleanEvaluationResponse":
        """Evaluate with structured output for boolean evaluations."""
        response = await self._client.beta.chat.completions.parse(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            response_format=BooleanEvaluationResponse,
        )
        parsed = response.choices[0].message.parsed
        if parsed is None:
            raise ValueError("Failed to parse structured response")
        return parsed

    async def evaluate_category(self, prompt: str) -> "CategoryEvaluationResponse":
        """Evaluate with structured output for category evaluations."""
        response = await self._client.beta.chat.completions.parse(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            response_format=CategoryEvaluationResponse,
        )
        parsed = response.choices[0].message.parsed
        if parsed is None:
            raise ValueError("Failed to parse structured response")
        return parsed
