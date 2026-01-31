"""Shared evaluator factory for evaluation datasets."""

from pydantic_evals.evaluators import Evaluator, IsInstance, LLMJudge, MaxDuration

from pydantic_ai_toolsets.evals.config import EvaluationConfig


def create_evaluators(config: EvaluationConfig) -> list[Evaluator]:
    """Create evaluators based on configuration.
    
    Args:
        config: Evaluation configuration.
    
    Returns:
        List of evaluators to use for evaluation.
    """
    evaluators: list[Evaluator] = [
        IsInstance(type_name='str', evaluation_name='output_is_string'),
        MaxDuration(seconds=config.max_duration_seconds),
    ]
    
    if config.use_llm_judge:
        evaluators.append(
            LLMJudge(
                rubric='The output is complete, relevant, and addresses the input prompt appropriately.',
                model=config.llm_judge_model or config.get_model_string(),
                include_input=True,
                assertion={'evaluation_name': 'quality_check', 'include_reason': True},
            )
        )
    
    return evaluators
