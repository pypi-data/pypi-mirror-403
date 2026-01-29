"""Evaluation system for assessing conversation quality using LLM judges."""

from enum import Enum

from pydantic import BaseModel, ConfigDict

from voiceground.evaluations.base import (
    BaseEvaluator,
    BooleanEvaluationResponse,
    CategoryEvaluationResponse,
)
from voiceground.evaluations.providers import OpenAIEvaluator


class EvaluationType(str, Enum):
    """Type of evaluation to perform."""

    BOOLEAN = "boolean"  # Pass/Fail
    CATEGORY = "category"  # Classification
    RATING = "rating"  # Numeric rating (e.g., 1-5)


class EvaluationResult(BaseModel):
    """Result of an evaluation."""

    name: str
    type: EvaluationType
    passed: bool | None = None  # For BOOLEAN
    category: str | None = None  # For CATEGORY
    rating: int | None = None  # For RATING
    reasoning: str  # LLM's explanation


class BaseEvaluationDefinition(BaseModel):
    """Base class for evaluation definitions."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str  # e.g., "goal_achieved"
    criteria: str  # Free text criteria for LLM
    evaluator: BaseEvaluator | None = None  # If None, use observer's default

    @property
    def type(self) -> EvaluationType:
        """Get the evaluation type."""
        raise NotImplementedError

    def build_prompt(self, conversation_json: str) -> str:
        """Build the evaluation prompt with conversation data.

        Args:
            conversation_json: JSON-formatted conversation transcript.

        Returns:
            Formatted prompt for the evaluator.
        """
        raise NotImplementedError


class BooleanEvaluationDefinition(BaseEvaluationDefinition):
    """Boolean (pass/fail) evaluation definition."""

    system_prompt_template: str = """Evaluate this conversation based on the following criteria:
{criteria}

Conversation:
{conversation_json}

Respond in JSON format:
{{
  "passed": true/false,
  "reasoning": "your explanation"
}}"""

    @property
    def type(self) -> EvaluationType:
        return EvaluationType.BOOLEAN

    def build_prompt(self, conversation_json: str) -> str:
        """Build boolean evaluation prompt."""
        return self.system_prompt_template.format(
            criteria=self.criteria, conversation_json=conversation_json
        )


class CategoryEvaluationDefinition(BaseEvaluationDefinition):
    """Category classification evaluation definition."""

    categories: list[str]  # Required list of possible categories
    system_prompt_template: str = """Classify this conversation based on the following criteria:
{criteria}

Available categories: {categories}

Conversation:
{conversation_json}

Respond in JSON format:
{{
  "category": "chosen_category",
  "reasoning": "your explanation"
}}"""

    @property
    def type(self) -> EvaluationType:
        return EvaluationType.CATEGORY

    def build_prompt(self, conversation_json: str) -> str:
        """Build category evaluation prompt."""
        categories_str = ", ".join(self.categories)
        return self.system_prompt_template.format(
            criteria=self.criteria, categories=categories_str, conversation_json=conversation_json
        )


class RatingEvaluationDefinition(BaseEvaluationDefinition):
    """Numeric rating evaluation definition."""

    min_rating: int = 1  # Default minimum
    max_rating: int = 5  # Default maximum
    system_prompt_template: str = """Rate this conversation based on the following criteria:
{criteria}

Provide a rating between {min_rating} and {max_rating}.

Conversation:
{conversation_json}

Respond in JSON format:
{{
  "rating": <number between {min_rating} and {max_rating}>,
  "reasoning": "your explanation"
}}"""

    @property
    def type(self) -> EvaluationType:
        return EvaluationType.RATING

    def build_prompt(self, conversation_json: str) -> str:
        """Build rating evaluation prompt."""
        return self.system_prompt_template.format(
            criteria=self.criteria,
            min_rating=self.min_rating,
            max_rating=self.max_rating,
            conversation_json=conversation_json,
        )


# Type alias for backwards compatibility and convenience
EvaluationDefinition = (
    BooleanEvaluationDefinition | CategoryEvaluationDefinition | RatingEvaluationDefinition
)


__all__ = [
    # Base classes
    "BaseEvaluator",
    "BooleanEvaluationResponse",
    "CategoryEvaluationResponse",
    # Providers
    "OpenAIEvaluator",
    # Types and models
    "EvaluationType",
    "EvaluationResult",
    "BaseEvaluationDefinition",
    "BooleanEvaluationDefinition",
    "CategoryEvaluationDefinition",
    "RatingEvaluationDefinition",
    "EvaluationDefinition",  # Type alias
]
