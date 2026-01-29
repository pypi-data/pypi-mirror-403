"""Base classes and models for evaluation system."""

import json
from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


class BaseEvaluator(ABC):
    """Base class for LLM evaluators."""

    @abstractmethod
    async def evaluate(self, prompt: str) -> str:
        """Send a prompt to the LLM and return the response.

        Args:
            prompt: The evaluation prompt to send to the LLM.

        Returns:
            The LLM's response as a string.
        """
        pass

    def _validate_response(self, response: str, model: type[T]) -> T:
        """Validate and parse a JSON response against a Pydantic model.

        Args:
            response: The raw JSON string response from the LLM.
            model: The Pydantic model to validate against.

        Returns:
            The validated Pydantic model instance.

        Raises:
            ValueError: If the response is invalid JSON or doesn't match the schema.
        """
        try:
            data = json.loads(response)
            return model.model_validate(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response: {e}") from e
        except ValidationError as e:
            raise ValueError(f"Response doesn't match expected schema: {e}") from e


class BooleanEvaluationResponse(BaseModel):
    """Structured response for boolean evaluations."""

    passed: bool
    reasoning: str


class CategoryEvaluationResponse(BaseModel):
    """Structured response for category evaluations."""

    category: str
    reasoning: str
