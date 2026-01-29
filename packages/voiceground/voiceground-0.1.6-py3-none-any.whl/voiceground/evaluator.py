"""VoicegroundEvaluator - Runs LLM-based evaluations on conversations."""

import json

from loguru import logger

from voiceground.evaluations import (
    BaseEvaluator,
    EvaluationDefinition,
    EvaluationResult,
    EvaluationType,
)


class VoicegroundEvaluator:
    """Evaluator that runs LLM-based evaluations on conversation transcripts.

    Args:
        evaluations: List of evaluation definitions to run.
        default_evaluator: Default evaluator to use when evaluation doesn't specify one.
    """

    def __init__(
        self,
        evaluations: list[EvaluationDefinition] | None = None,
        default_evaluator: BaseEvaluator | None = None,
    ):
        self._evaluations = evaluations or []
        self._default_evaluator = default_evaluator

    async def evaluate_conversation(self, transcript: list[dict]) -> list[EvaluationResult]:
        """Run all evaluations on a conversation transcript.

        Args:
            transcript: List of conversation entries with role, content, and optional tool data.
                Expected format:
                - {"role": "user", "content": "..."}
                - {"role": "bot", "content": "..."}
                - {"role": "tool_call", "name": "...", "arguments": {...}, "result": {...}}

        Returns:
            List of evaluation results.
        """
        if not self._evaluations:
            return []

        results = []
        for eval_def in self._evaluations:
            evaluator = eval_def.evaluator or self._default_evaluator
            if not evaluator:
                logger.warning(f"No evaluator configured for '{eval_def.name}', skipping")
                continue

            # Format conversation as structured JSON
            conversation_json = json.dumps(transcript, indent=2)

            # Build evaluation prompt using the definition's template
            prompt = eval_def.build_prompt(conversation_json)

            try:
                # Use structured outputs if evaluator supports it
                if eval_def.type == EvaluationType.BOOLEAN and hasattr(
                    evaluator, "evaluate_boolean"
                ):
                    parsed = await evaluator.evaluate_boolean(prompt)
                    result = EvaluationResult(
                        name=eval_def.name,
                        type=eval_def.type,
                        passed=parsed.passed,
                        reasoning=parsed.reasoning,
                    )
                elif eval_def.type == EvaluationType.CATEGORY and hasattr(
                    evaluator, "evaluate_category"
                ):
                    parsed = await evaluator.evaluate_category(prompt)
                    result = EvaluationResult(
                        name=eval_def.name,
                        type=eval_def.type,
                        category=parsed.category,
                        reasoning=parsed.reasoning,
                    )
                else:
                    # Fallback to regular evaluate and parse JSON
                    response = await evaluator.evaluate(prompt)
                    result = self._parse_evaluation_response(eval_def.name, response, eval_def.type)
                results.append(result)
            except Exception as e:
                logger.error(f"Evaluation '{eval_def.name}' failed: {e}")
                # Add failed result
                results.append(
                    EvaluationResult(
                        name=eval_def.name,
                        type=eval_def.type,
                        reasoning=f"Evaluation failed: {str(e)}",
                    )
                )

        return results

    def _parse_evaluation_response(
        self, name: str, response: str, eval_type: EvaluationType
    ) -> EvaluationResult:
        """Parse LLM response into EvaluationResult.

        Args:
            name: Name of the evaluation.
            response: LLM response string (expected to be JSON).
            eval_type: Type of evaluation.

        Returns:
            Parsed evaluation result.
        """
        try:
            data = json.loads(response)

            if eval_type == EvaluationType.BOOLEAN:
                return EvaluationResult(
                    name=name,
                    type=eval_type,
                    passed=data.get("passed"),
                    reasoning=data.get("reasoning", ""),
                )
            elif eval_type == EvaluationType.CATEGORY:
                return EvaluationResult(
                    name=name,
                    type=eval_type,
                    category=data.get("category"),
                    reasoning=data.get("reasoning", ""),
                )
            elif eval_type == EvaluationType.RATING:
                return EvaluationResult(
                    name=name,
                    type=eval_type,
                    rating=data.get("rating"),
                    reasoning=data.get("reasoning", ""),
                )
            else:
                return EvaluationResult(
                    name=name, type=eval_type, reasoning=f"Unsupported evaluation type: {eval_type}"
                )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse evaluation response: {e}")
            return EvaluationResult(
                name=name, type=eval_type, reasoning=f"Failed to parse response: {response[:100]}"
            )
