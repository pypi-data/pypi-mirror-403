"""Tests for evaluator implementations and validation pattern."""

import json

import pytest
from pydantic import BaseModel

from voiceground.evaluations import (
    BaseEvaluator,
    BooleanEvaluationResponse,
    CategoryEvaluationResponse,
)


class MockEvaluatorForValidation(BaseEvaluator):
    """Mock evaluator for testing the validation pattern."""

    def __init__(self, response: str):
        self._response = response

    async def evaluate(self, prompt: str) -> str:
        return self._response


@pytest.mark.asyncio
class TestBaseEvaluatorValidation:
    """Test the base evaluator's validation pattern."""

    async def test_validate_response_success(self):
        """Test successful validation of a well-formed JSON response."""
        response = json.dumps({"passed": True, "reasoning": "All criteria met"})
        evaluator = MockEvaluatorForValidation(response)

        result = evaluator._validate_response(response, BooleanEvaluationResponse)

        assert isinstance(result, BooleanEvaluationResponse)
        assert result.passed is True
        assert result.reasoning == "All criteria met"

    async def test_validate_response_invalid_json(self):
        """Test validation failure with invalid JSON."""
        response = "This is not valid JSON"
        evaluator = MockEvaluatorForValidation(response)

        with pytest.raises(ValueError, match="Invalid JSON response"):
            evaluator._validate_response(response, BooleanEvaluationResponse)

    async def test_validate_response_schema_mismatch(self):
        """Test validation failure when response doesn't match schema."""
        # Missing required field 'reasoning'
        response = json.dumps({"passed": True})
        evaluator = MockEvaluatorForValidation(response)

        with pytest.raises(ValueError, match="doesn't match expected schema"):
            evaluator._validate_response(response, BooleanEvaluationResponse)

    async def test_validate_response_wrong_types(self):
        """Test validation failure with wrong field types."""
        # 'passed' should be bool, not a complex object
        response = json.dumps({"passed": {"nested": "object"}, "reasoning": "Good"})
        evaluator = MockEvaluatorForValidation(response)

        with pytest.raises(ValueError, match="doesn't match expected schema"):
            evaluator._validate_response(response, BooleanEvaluationResponse)

    async def test_validate_response_category(self):
        """Test validation with CategoryEvaluationResponse."""
        response = json.dumps({"category": "positive", "reasoning": "Friendly tone"})
        evaluator = MockEvaluatorForValidation(response)

        result = evaluator._validate_response(response, CategoryEvaluationResponse)

        assert isinstance(result, CategoryEvaluationResponse)
        assert result.category == "positive"
        assert result.reasoning == "Friendly tone"

    async def test_validate_response_extra_fields_ignored(self):
        """Test that extra fields in response are ignored."""
        response = json.dumps(
            {
                "passed": False,
                "reasoning": "Failed criteria",
                "extra_field": "ignored",
                "another_field": 123,
            }
        )
        evaluator = MockEvaluatorForValidation(response)

        result = evaluator._validate_response(response, BooleanEvaluationResponse)

        assert isinstance(result, BooleanEvaluationResponse)
        assert result.passed is False
        assert result.reasoning == "Failed criteria"
        # Extra fields should not be included
        assert not hasattr(result, "extra_field")


@pytest.mark.asyncio
class TestEvaluatorImplementations:
    """Test that evaluator implementations follow the pattern."""

    async def test_mock_evaluator_has_validation_method(self):
        """Verify mock evaluator has access to base validation."""
        evaluator = MockEvaluatorForValidation("")
        assert hasattr(evaluator, "_validate_response")
        assert callable(evaluator._validate_response)

    async def test_validation_works_with_custom_models(self):
        """Test validation pattern works with custom Pydantic models."""

        class CustomResponse(BaseModel):
            score: int
            comment: str

        response = json.dumps({"score": 5, "comment": "Excellent"})
        evaluator = MockEvaluatorForValidation(response)

        result = evaluator._validate_response(response, CustomResponse)

        assert isinstance(result, CustomResponse)
        assert result.score == 5
        assert result.comment == "Excellent"
