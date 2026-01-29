"""Compare different workflow template combinations."""

from typing import Any

from pydantic_ai_toolsets.evals.config import EvaluationConfig
from pydantic_ai_toolsets.evals.categories.combinations.research_assistant_eval import (
    evaluate_research_assistant_workflow,
)
from pydantic_ai_toolsets.evals.categories.combinations.creative_problem_solver_eval import (
    evaluate_creative_problem_solver_workflow,
)
from pydantic_ai_toolsets.evals.categories.combinations.strategic_decision_maker_eval import (
    evaluate_strategic_decision_maker_workflow,
)
from pydantic_ai_toolsets.evals.categories.combinations.code_architect_eval import (
    evaluate_code_architect_workflow,
)


async def compare_combinations(config: EvaluationConfig) -> dict[str, Any]:
    """Compare all workflow template combinations.

    Args:
        config: Evaluation configuration.

    Returns:
        Dictionary with comparison results.
    """
    from typing import Any

    evaluation_functions = [
        ("research_assistant", evaluate_research_assistant_workflow),
        ("creative_problem_solver", evaluate_creative_problem_solver_workflow),
        ("strategic_decision_maker", evaluate_strategic_decision_maker_workflow),
        ("code_architect", evaluate_code_architect_workflow),
    ]

    comparison = {}
    total_cases = 0
    total_errors = 0

    # Run all evaluations
    for workflow_name, eval_func in evaluation_functions:
        try:
            print(f"Evaluating {workflow_name} workflow...")
            report = await eval_func(config)
            
            # Extract case results from report - combine successful cases and failures
            case_results = []
            if hasattr(report, "cases") and report.cases:
                if isinstance(report.cases, (list, tuple)):
                    case_results.extend(report.cases)
                else:
                    try:
                        case_results.extend(list(report.cases))
                    except (TypeError, AttributeError):
                        pass
            
            if hasattr(report, "failures") and report.failures:
                if isinstance(report.failures, (list, tuple)):
                    case_results.extend(report.failures)
                    # Print failure details for debugging
                    for failure in report.failures:
                        if hasattr(failure, "error_message"):
                            case_name = getattr(failure, "name", "unknown")
                            error_msg = failure.error_message[:500] if len(failure.error_message) > 500 else failure.error_message
                            print(f"  ERROR in case '{case_name}': {error_msg}")
                else:
                    try:
                        failures_list = list(report.failures)
                        case_results.extend(failures_list)
                        for failure in failures_list:
                            if hasattr(failure, "error_message"):
                                case_name = getattr(failure, "name", "unknown")
                                error_msg = failure.error_message[:500] if len(failure.error_message) > 500 else failure.error_message
                                print(f"  ERROR in case '{case_name}': {error_msg}")
                    except (TypeError, AttributeError):
                        pass
            
            # Helper function to extract passed status (avoid circular import)
            def extract_passed(case_result: Any) -> bool:
                """Extract passed status from a case result."""
                if hasattr(case_result, "passed"):
                    return bool(case_result.passed)
                if hasattr(case_result, "error") and case_result.error:
                    return False
                if hasattr(case_result, "exception") and case_result.exception:
                    return False
                if hasattr(case_result, "evaluator_results") and case_result.evaluator_results:
                    evaluator_results = case_result.evaluator_results
                    if isinstance(evaluator_results, dict):
                        for eval_name, eval_result in evaluator_results.items():
                            if isinstance(eval_result, bool):
                                if not eval_result:
                                    return False
                            elif hasattr(eval_result, "value"):
                                if not bool(eval_result.value):
                                    return False
                            elif isinstance(eval_result, dict):
                                if "value" in eval_result and not bool(eval_result["value"]):
                                    return False
                        return True
                return True
            
            num_cases = len(case_results) if case_results else 0
            passed = sum(1 for r in case_results if extract_passed(r)) if case_results else 0
            failed = num_cases - passed
            
            # Extract summary stats if available
            avg_time = 0.0
            total_tokens = 0
            if hasattr(report, "summary_stats") and report.summary_stats:
                stats = report.summary_stats
                avg_time = stats.get("avg_duration_ms", 0) / 1000.0
                total_tokens = stats.get("total_tokens", 0)
            
            comparison[workflow_name] = {
                "num_cases": num_cases,
                "passed": passed,
                "failed": failed,
                "avg_execution_time": avg_time,
                "total_tokens": total_tokens,
                "errors": failed,
                "report": report,
            }
            
            total_cases += num_cases
            total_errors += failed
        except Exception as e:
            print(f"Error evaluating {workflow_name}: {e}")
            import traceback
            traceback.print_exc()
            comparison[workflow_name] = {
                "error": str(e),
                "num_cases": 0,
                "errors": 1,
            }
            total_errors += 1

    return {
        "summary": {
            "total": total_cases,
            "errors": total_errors,
            "success_rate": (total_cases - total_errors) / total_cases if total_cases > 0 else 0.0,
        },
        "by_toolset": comparison,
    }
