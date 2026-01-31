"""Main evaluation runner for toolsets."""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import logfire
except ImportError:
    logfire = None

from pydantic_ai_toolsets.evals.config import EvaluationConfig, default_config
from pydantic_ai_toolsets.evals.categories.multi_agent.compare_multi_agent import (
    compare_multi_agent_toolsets,
)
from pydantic_ai_toolsets.evals.categories.reflection.compare_reflection import (
    compare_reflection_toolsets,
)
from pydantic_ai_toolsets.evals.categories.thinking_cognition.compare_thinking import (
    compare_thinking_toolsets,
)
from pydantic_ai_toolsets.evals.categories.uniques.search_eval import evaluate_search_toolset
from pydantic_ai_toolsets.evals.categories.uniques.todo_eval import evaluate_todo_toolset
from pydantic_ai_toolsets.evals.categories.combinations.compare_combinations import (
    compare_combinations,
)

# Import individual evaluation functions for toolset-level runs
from pydantic_ai_toolsets.evals.categories.thinking_cognition.beam_eval import evaluate_beam_toolset
from pydantic_ai_toolsets.evals.categories.thinking_cognition.cot_eval import evaluate_cot_toolset
from pydantic_ai_toolsets.evals.categories.thinking_cognition.got_eval import evaluate_got_toolset
from pydantic_ai_toolsets.evals.categories.thinking_cognition.mcts_eval import evaluate_mcts_toolset
from pydantic_ai_toolsets.evals.categories.thinking_cognition.tot_eval import evaluate_tot_toolset
from pydantic_ai_toolsets.evals.categories.multi_agent.multi_personas_eval import evaluate_multi_personas_toolset
from pydantic_ai_toolsets.evals.categories.multi_agent.persona_debate_eval import evaluate_persona_debate_toolset
from pydantic_ai_toolsets.evals.categories.reflection.reflection_eval import evaluate_reflection_toolset
from pydantic_ai_toolsets.evals.categories.reflection.self_ask_eval import evaluate_self_ask_toolset
from pydantic_ai_toolsets.evals.categories.reflection.self_refine_eval import evaluate_self_refine_toolset
from pydantic_ai_toolsets.evals.categories.combinations.research_assistant_eval import evaluate_research_assistant_workflow
from pydantic_ai_toolsets.evals.categories.combinations.creative_problem_solver_eval import evaluate_creative_problem_solver_workflow
from pydantic_ai_toolsets.evals.categories.combinations.strategic_decision_maker_eval import evaluate_strategic_decision_maker_workflow
from pydantic_ai_toolsets.evals.categories.combinations.code_architect_eval import evaluate_code_architect_workflow


# Registry of all available toolsets
TOOLSET_REGISTRY: dict[str, dict[str, Any]] = {
    # Uniques category
    "todo": {
        "category": "uniques",
        "eval_func": evaluate_todo_toolset,
        "display_name": "Todo",
    },
    "search": {
        "category": "uniques",
        "eval_func": evaluate_search_toolset,
        "display_name": "Search",
    },
    # Thinking/Cognition category
    "beam": {
        "category": "thinking",
        "eval_func": evaluate_beam_toolset,
        "display_name": "Beam Search Reasoning",
    },
    "cot": {
        "category": "thinking",
        "eval_func": evaluate_cot_toolset,
        "display_name": "Chain of Thought",
    },
    "got": {
        "category": "thinking",
        "eval_func": evaluate_got_toolset,
        "display_name": "Graph of Thought",
    },
    "mcts": {
        "category": "thinking",
        "eval_func": evaluate_mcts_toolset,
        "display_name": "Monte Carlo Tree Search",
    },
    "tot": {
        "category": "thinking",
        "eval_func": evaluate_tot_toolset,
        "display_name": "Tree of Thought",
    },
    # Multi-agent category
    "multi_personas": {
        "category": "multi_agent",
        "eval_func": evaluate_multi_personas_toolset,
        "display_name": "Multi Personas",
    },
    "persona_debate": {
        "category": "multi_agent",
        "eval_func": evaluate_persona_debate_toolset,
        "display_name": "Persona Debate",
    },
    # Reflection category
    "self_refine": {
        "category": "reflection",
        "eval_func": evaluate_self_refine_toolset,
        "display_name": "Self Refine",
    },
    "reflection": {
        "category": "reflection",
        "eval_func": evaluate_reflection_toolset,
        "display_name": "Reflection",
    },
    "self_ask": {
        "category": "reflection",
        "eval_func": evaluate_self_ask_toolset,
        "display_name": "Self Ask",
    },
    # Combinations category
    "research_assistant": {
        "category": "combinations",
        "eval_func": evaluate_research_assistant_workflow,
        "display_name": "Research Assistant",
    },
    "creative_problem_solver": {
        "category": "combinations",
        "eval_func": evaluate_creative_problem_solver_workflow,
        "display_name": "Creative Problem Solver",
    },
    "strategic_decision_maker": {
        "category": "combinations",
        "eval_func": evaluate_strategic_decision_maker_workflow,
        "display_name": "Strategic Decision Maker",
    },
    "code_architect": {
        "category": "combinations",
        "eval_func": evaluate_code_architect_workflow,
        "display_name": "Code Architect",
    },
}


def get_available_toolsets() -> list[str]:
    """Get list of all available toolset names."""
    return list(TOOLSET_REGISTRY.keys())


def get_toolsets_by_category(category: str) -> list[str]:
    """Get list of toolset names for a given category."""
    return [
        name for name, info in TOOLSET_REGISTRY.items()
        if info["category"] == category
    ]


def extract_case_passed_status(case_result: Any) -> bool:
    """Extract passed status from a case result.
    
    Handles different structures from pydantic-evals EvaluationReport:
    - ReportCase objects (successful cases) with evaluators have a 'passed' attribute
    - ReportCaseFailure objects (failed cases) have 'error_message' attribute
    - Case results may have 'evaluator_results' dict
    - Case results may have 'error' or 'exception' attributes
    
    Args:
        case_result: A case result from pydantic-evals EvaluationReport.
    
    Returns:
        True if case passed, False otherwise.
    """
    # Check if this is a failure case (ReportCaseFailure)
    if hasattr(case_result, "error_message") and case_result.error_message:
        return False
    if hasattr(case_result, "error_stacktrace") and case_result.error_stacktrace:
        return False
    
    # Check for explicit passed attribute
    if hasattr(case_result, "passed"):
        return bool(case_result.passed)
    
    # Check for error/exception (if present, case failed)
    if hasattr(case_result, "error") and case_result.error:
        return False
    if hasattr(case_result, "exception") and case_result.exception:
        return False
    
    # Check evaluator results - case passes if all evaluators pass
    if hasattr(case_result, "evaluator_results") and case_result.evaluator_results:
        evaluator_results = case_result.evaluator_results
        if isinstance(evaluator_results, dict):
            # Check all evaluator results
            for eval_name, eval_result in evaluator_results.items():
                # Evaluator results can be bool, EvaluationReason, or dict
                if isinstance(eval_result, bool):
                    if not eval_result:
                        return False
                elif hasattr(eval_result, "value"):
                    # EvaluationReason has a value attribute
                    if not bool(eval_result.value):
                        return False
                elif isinstance(eval_result, dict):
                    # Some evaluators return dicts
                    if "value" in eval_result and not bool(eval_result["value"]):
                        return False
            # All evaluators passed
            return True
    
    # Check assertions - if any assertion is False, case fails
    if hasattr(case_result, "assertions") and case_result.assertions:
        assertions = case_result.assertions
        if isinstance(assertions, dict):
            for assertion_name, assertion_result in assertions.items():
                if hasattr(assertion_result, "value"):
                    if not bool(assertion_result.value):
                        return False
                elif isinstance(assertion_result, bool):
                    if not assertion_result:
                        return False
    
    # If no evaluators and no error, assume passed (for backward compatibility)
    # This handles cases where evaluators weren't configured
    return True


async def run_single_toolset(
    toolset_name: str,
    config: EvaluationConfig,
) -> dict[str, Any]:
    """Run evaluation for a single toolset.
    
    Args:
        toolset_name: Name of the toolset to evaluate.
        config: Evaluation configuration.
    
    Returns:
        Dictionary with toolset results.
    """
    if toolset_name not in TOOLSET_REGISTRY:
        raise ValueError(
            f"Unknown toolset: {toolset_name}. "
            f"Available toolsets: {', '.join(get_available_toolsets())}"
        )
    
    toolset_info = TOOLSET_REGISTRY[toolset_name]
    eval_func = toolset_info["eval_func"]
    display_name = toolset_info["display_name"]
    category = toolset_info["category"]
    
    print(f"Running evaluation for {display_name} ({toolset_name})...")
    
    try:
        report = await eval_func(config)
        
        # Extract case results from report
        # pydantic-evals EvaluationReport has both 'cases' (successful) and 'failures' (failed) attributes
        case_results = []
        
        # Get successful cases
        if hasattr(report, "cases"):
            successful_cases = report.cases
            if successful_cases:
                if isinstance(successful_cases, (list, tuple)):
                    case_results.extend(successful_cases)
                else:
                    try:
                        case_results.extend(list(successful_cases))
                    except (TypeError, AttributeError):
                        pass
        
        # Get failed cases (these are ReportCaseFailure objects, but we still count them)
        if hasattr(report, "failures"):
            failed_cases = report.failures
            if failed_cases:
                if isinstance(failed_cases, (list, tuple)):
                    case_results.extend(failed_cases)
                else:
                    try:
                        case_results.extend(list(failed_cases))
                    except (TypeError, AttributeError):
                        pass
        
        num_cases = len(case_results) if case_results else 0
        passed = sum(1 for r in case_results if extract_case_passed_status(r)) if case_results else 0
        failed = num_cases - passed
        
        # Extract summary stats if available
        avg_time = 0.0
        total_tokens = 0
        if hasattr(report, "summary_stats") and report.summary_stats:
            stats = report.summary_stats
            avg_time = stats.get("avg_duration_ms", 0) / 1000.0
            total_tokens = stats.get("total_tokens", 0)
        
        print(f"  ✓ {display_name}: {num_cases} cases")
        print(f"    Passed: {passed}")
        print(f"    Failed: {failed}")
        
        return {
            "summary": {
                "total": num_cases,
                "errors": failed,
                "success_rate": (num_cases - failed) / num_cases if num_cases > 0 else 0.0,
            },
            "by_toolset": {
                toolset_name: {
                    "num_cases": num_cases,
                    "passed": passed,
                    "failed": failed,
                    "avg_execution_time": avg_time,
                    "total_tokens": total_tokens,
                    "errors": failed,
                    "report": report,
                }
            },
        }
    except Exception as e:
        import traceback
        print(f"  ✗ {display_name}: {e}")
        traceback.print_exc()
        return {
            "summary": {
                "total": 0,
                "errors": 1,
                "success_rate": 0.0,
            },
            "by_toolset": {
                toolset_name: {
                    "error": str(e),
                    "num_cases": 0,
                    "errors": 1,
                }
            },
        }


async def run_multiple_toolsets(
    toolset_names: list[str],
    config: EvaluationConfig,
    sequential: bool = True,
) -> dict[str, Any]:
    """Run evaluations for multiple toolsets.
    
    Args:
        toolset_names: List of toolset names to evaluate.
        config: Evaluation configuration.
        sequential: If True, run toolsets one by one. If False, run in parallel.
    
    Returns:
        Dictionary with results organized by category.
    """
    # Validate all toolset names
    invalid_toolsets = [name for name in toolset_names if name not in TOOLSET_REGISTRY]
    if invalid_toolsets:
        raise ValueError(
            f"Unknown toolsets: {', '.join(invalid_toolsets)}. "
            f"Available toolsets: {', '.join(get_available_toolsets())}"
        )
    
    # Group toolsets by category
    toolsets_by_category: dict[str, list[str]] = {}
    for toolset_name in toolset_names:
        category = TOOLSET_REGISTRY[toolset_name]["category"]
        if category not in toolsets_by_category:
            toolsets_by_category[category] = []
        toolsets_by_category[category].append(toolset_name)
    
    print(f"Running evaluations for {len(toolset_names)} toolset(s)...")
    if sequential:
        print("Running toolsets sequentially (one by one)...\n")
    else:
        print("Running toolsets in parallel...\n")
    
    results = {}
    
    if sequential:
        toolset_idx = 0
        for category, category_toolsets in toolsets_by_category.items():
            print("=" * 60)
            print(f"CATEGORY: {category.upper()}")
            print("=" * 60)
            
            for toolset_name in category_toolsets:
                toolset_idx += 1
                toolset_info = TOOLSET_REGISTRY[toolset_name]
                display_name = toolset_info["display_name"]
                
                print("-" * 60)
                print(f"TOOLSET {toolset_idx}/{len(toolset_names)}: {display_name.upper()} ({toolset_name})")
                print("-" * 60)
                
                toolset_result = await run_single_toolset(toolset_name, config)
                
                # Merge results by category
                if category not in results:
                    results[category] = {
                        "summary": {"total": 0, "errors": 0},
                        "by_toolset": {},
                    }
                
                # Merge toolset results
                toolset_data = toolset_result["by_toolset"][toolset_name]
                results[category]["by_toolset"][toolset_name] = toolset_data
                
                # Update category summary
                results[category]["summary"]["total"] += toolset_result["summary"]["total"]
                results[category]["summary"]["errors"] += toolset_result["summary"]["errors"]
                
                print("\n")
        
        # Calculate success rates for all categories
        for category in results:
            total = results[category]["summary"]["total"]
            errors = results[category]["summary"]["errors"]
            results[category]["summary"]["success_rate"] = (
                (total - errors) / total if total > 0 else 0.0
            )
    else:
        # Run in parallel
        import asyncio
        tasks = [
            asyncio.create_task(run_single_toolset(name, config))
            for name in toolset_names
        ]
        
        toolset_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Organize results by category
        for toolset_name, toolset_result in zip(toolset_names, toolset_results):
            if isinstance(toolset_result, Exception):
                category = TOOLSET_REGISTRY[toolset_name]["category"]
                if category not in results:
                    results[category] = {
                        "summary": {"total": 0, "errors": 0},
                        "by_toolset": {},
                    }
                results[category]["by_toolset"][toolset_name] = {
                    "error": str(toolset_result),
                    "num_cases": 0,
                    "errors": 1,
                }
                results[category]["summary"]["errors"] += 1
            else:
                category = TOOLSET_REGISTRY[toolset_name]["category"]
                if category not in results:
                    results[category] = {
                        "summary": {"total": 0, "errors": 0},
                        "by_toolset": {},
                    }
                
                toolset_data = toolset_result["by_toolset"][toolset_name]
                results[category]["by_toolset"][toolset_name] = toolset_data
                results[category]["summary"]["total"] += toolset_result["summary"]["total"]
                results[category]["summary"]["errors"] += toolset_result["summary"]["errors"]
        
        # Calculate success rates
        for category in results:
            total = results[category]["summary"]["total"]
            errors = results[category]["summary"]["errors"]
            results[category]["summary"]["success_rate"] = (
                (total - errors) / total if total > 0 else 0.0
            )
    
    return results


async def run_uniques(config: EvaluationConfig, sequential: bool = True) -> dict[str, Any]:
    """Run evaluations for unique toolsets using pydantic-evals Dataset API.
    
    Args:
        config: Evaluation configuration.
        sequential: If True, run toolsets one by one. If False, run in parallel.
    
    Returns:
        Dictionary of results.
    """
    print("Running evaluations for unique toolsets...")
    if sequential:
        print("Running toolsets sequentially (one by one)...\n")
    
    results = {}
    
    if sequential:
        # Run todo first
        print("-" * 60)
        print("TOOLSET 1/2: TODO")
        print("-" * 60)
        try:
            print("  Running todo toolset evaluation...")
            todo_report = await evaluate_todo_toolset(config)
            
            # Check what attributes the report has
            # EvaluationReport might have 'results' or 'cases' instead of 'case_results'
            if hasattr(todo_report, "case_results"):
                case_results = todo_report.case_results
            elif hasattr(todo_report, "results"):
                case_results = todo_report.results
            elif hasattr(todo_report, "cases"):
                case_results = todo_report.cases
            else:
                # Try to get cases from the report
                case_results = getattr(todo_report, "case_results", [])
            
            num_cases = len(case_results) if case_results else 0
            passed = sum(1 for r in case_results if extract_case_passed_status(r)) if case_results else 0
            failed = num_cases - passed
            
            print(f"  ✓ Todo: {num_cases} cases")
            print(f"    Passed: {passed}")
            print(f"    Failed: {failed}")
            results["todo"] = {
                "report": todo_report,
                "num_cases": num_cases,
                "passed": passed,
                "failed": failed,
            }
        except Exception as e:
            import traceback
            print(f"  ✗ Todo: {e}")
            traceback.print_exc()
            results["todo"] = {"error": str(e)}
        
        print("\n")
        
        # Then run search
        print("-" * 60)
        print("TOOLSET 2/2: SEARCH")
        print("-" * 60)
        try:
            print("  Running search toolset evaluation...")
            search_report = await evaluate_search_toolset(config)
            
            # Check what attributes the report has
            # EvaluationReport might have 'results' or 'cases' instead of 'case_results'
            if hasattr(search_report, "case_results"):
                case_results = search_report.case_results
            elif hasattr(search_report, "results"):
                case_results = search_report.results
            elif hasattr(search_report, "cases"):
                case_results = search_report.cases
            else:
                # Try to get cases from the report
                case_results = getattr(search_report, "case_results", [])
            
            num_cases = len(case_results) if case_results else 0
            passed = sum(1 for r in case_results if extract_case_passed_status(r)) if case_results else 0
            failed = num_cases - passed
            
            print(f"  ✓ Search: {num_cases} cases")
            print(f"    Passed: {passed}")
            print(f"    Failed: {failed}")
            results["search"] = {
                "report": search_report,
                "num_cases": num_cases,
                "passed": passed,
                "failed": failed,
            }
        except Exception as e:
            import traceback
            print(f"  ✗ Search: {e}")
            traceback.print_exc()
            results["search"] = {"error": str(e)}
    else:
        # Run in parallel (original behavior)
        import asyncio
        todo_task = asyncio.create_task(evaluate_todo_toolset(config))
        search_task = asyncio.create_task(evaluate_search_toolset(config))
        
        try:
            todo_report = await todo_task
            # Check what attributes the report has
            if hasattr(todo_report, "case_results"):
                case_results = todo_report.case_results
            elif hasattr(todo_report, "results"):
                case_results = todo_report.results
            elif hasattr(todo_report, "cases"):
                case_results = todo_report.cases
            else:
                case_results = getattr(todo_report, "case_results", [])
            
            num_cases = len(case_results) if case_results else 0
            passed = sum(1 for r in case_results if extract_case_passed_status(r)) if case_results else 0
            failed = num_cases - passed
            
            print(f"  ✓ Todo: {num_cases} cases")
            results["todo"] = {
                "report": todo_report,
                "num_cases": num_cases,
                "passed": passed,
                "failed": failed,
            }
        except Exception as e:
            print(f"  ✗ Todo: {e}")
            results["todo"] = {"error": str(e)}
        
        try:
            search_report = await search_task
            # Check what attributes the report has
            if hasattr(search_report, "case_results"):
                case_results = search_report.case_results
            elif hasattr(search_report, "results"):
                case_results = search_report.results
            elif hasattr(search_report, "cases"):
                case_results = search_report.cases
            else:
                case_results = getattr(search_report, "case_results", [])
            
            num_cases = len(case_results) if case_results else 0
            passed = sum(1 for r in case_results if extract_case_passed_status(r)) if case_results else 0
            failed = num_cases - passed
            
            print(f"  ✓ Search: {num_cases} cases")
            results["search"] = {
                "report": search_report,
                "num_cases": num_cases,
                "passed": passed,
                "failed": failed,
            }
        except Exception as e:
            print(f"  ✗ Search: {e}")
            results["search"] = {"error": str(e)}

    return {
        "summary": {
            "total": results.get("todo", {}).get("num_cases", 0) + results.get("search", {}).get("num_cases", 0),
        },
        "by_toolset": results,
    }


async def run_thinking(config: EvaluationConfig) -> dict[str, Any]:
    """Run evaluations for thinking/cognition toolsets."""
    print("Running evaluations for thinking/cognition toolsets...")
    return await compare_thinking_toolsets(config)


async def run_multi_agent(config: EvaluationConfig) -> dict[str, Any]:
    """Run evaluations for multi-agent toolsets."""
    print("Running evaluations for multi-agent toolsets...")
    return await compare_multi_agent_toolsets(config)


async def run_reflection(config: EvaluationConfig) -> dict[str, Any]:
    """Run evaluations for reflection toolsets."""
    print("Running evaluations for reflection toolsets...")
    return await compare_reflection_toolsets(config)


async def run_combinations(config: EvaluationConfig) -> dict[str, Any]:
    """Run evaluations for combination workflows."""
    print("Running evaluations for combination workflows...")
    return await compare_combinations(config)


async def run_all(config: EvaluationConfig, sequential: bool = True) -> dict[str, Any]:
    """Run all evaluations.
    
    Args:
        config: Evaluation configuration.
        sequential: If True, run evaluations one by one. If False, run in parallel.
    
    Returns:
        Dictionary of results by category.
    """
    print("Running all evaluations...")
    if sequential:
        print("Running evaluations sequentially (one by one)...\n")
    else:
        print("Running evaluations in parallel...\n")
    
    results = {}

    if sequential:
        # Run one by one with clear separation
        print("=" * 60)
        print("CATEGORY 1/5: UNIQUES")
        print("=" * 60)
        results["uniques"] = await run_uniques(config)
        print("\n")

        print("=" * 60)
        print("CATEGORY 2/5: THINKING/COGNITION")
        print("=" * 60)
        results["thinking"] = await run_thinking(config)
        print("\n")

        print("=" * 60)
        print("CATEGORY 3/5: MULTI-AGENT")
        print("=" * 60)
        results["multi_agent"] = await run_multi_agent(config)
        print("\n")

        print("=" * 60)
        print("CATEGORY 4/5: REFLECTION")
        print("=" * 60)
        results["reflection"] = await run_reflection(config)
        print("\n")

        print("=" * 60)
        print("CATEGORY 5/5: COMBINATIONS")
        print("=" * 60)
        results["combinations"] = await run_combinations(config)
    else:
        # Run in parallel (original behavior)
        import asyncio
        uniques_task = asyncio.create_task(run_uniques(config))
        thinking_task = asyncio.create_task(run_thinking(config))
        multi_agent_task = asyncio.create_task(run_multi_agent(config))
        reflection_task = asyncio.create_task(run_reflection(config))
        combinations_task = asyncio.create_task(run_combinations(config))
        
        results["uniques"] = await uniques_task
        results["thinking"] = await thinking_task
        results["multi_agent"] = await multi_agent_task
        results["reflection"] = await reflection_task
        results["combinations"] = await combinations_task

    return results


def export_results(results: dict[str, Any], output_dir: Path, format: str = "json"):
    """Export results to file.

    Args:
        results: Evaluation results.
        output_dir: Output directory.
        format: Export format ('json' or 'csv').
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    if format == "json":
        output_file = output_dir / "results.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Results exported to {output_file}")
    elif format == "csv":
        # Simple CSV export for summary
        import csv

        output_file = output_dir / "summary.csv"
        with open(output_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Category", "Toolset", "Metric", "Value"])

            for category, category_results in results.items():
                if "by_toolset" in category_results:
                    for toolset, toolset_data in category_results["by_toolset"].items():
                        if "avg_scores" in toolset_data:
                            for metric, value in toolset_data["avg_scores"].items():
                                writer.writerow([category, toolset, metric, value])

        print(f"Summary exported to {output_file}")


def print_summary(results: dict[str, Any]):
    """Print summary of results."""
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)

    for category, category_results in results.items():
        print(f"\n{category.upper()}:")
        if "summary" in category_results:
            summary = category_results["summary"]
            print(f"  Total cases: {summary.get('total', 0)}")
            print(f"  Errors: {summary.get('errors', 0)}")
            print(f"  Success rate: {summary.get('success_rate', 0):.2%}")
            print(f"  Avg execution time: {summary.get('avg_execution_time', 0):.2f}s")
            print(f"  Total tokens: {summary.get('total_tokens', 0)}")

        if "by_toolset" in category_results:
            print("\n  By toolset:")
            for toolset, toolset_data in category_results["by_toolset"].items():
                print(f"    {toolset}:")
                
                # Handle error case
                if "error" in toolset_data:
                    print(f"      Error: {toolset_data['error']}")
                    continue
                
                # Handle pydantic-evals EvaluationReport (from compare functions)
                if "report" in toolset_data:
                    report = toolset_data["report"]
                    # Check what attributes the report has
                    if hasattr(report, "case_results"):
                        case_results = report.case_results
                    elif hasattr(report, "results"):
                        case_results = report.results
                    elif hasattr(report, "cases"):
                        case_results = report.cases
                    else:
                        case_results = []
                    
                    # Use direct values if available, otherwise extract from report
                    num_cases = toolset_data.get("num_cases", len(case_results) if case_results else 0)
                    passed = toolset_data.get("passed", sum(1 for r in case_results if extract_case_passed_status(r)) if case_results else 0)
                    failed = toolset_data.get("failed", num_cases - passed)
                    
                    print(f"      Cases: {num_cases}")
                    print(f"      Passed: {passed}")
                    print(f"      Failed: {failed}")
                    
                    # Get timing and token info from toolset_data or report
                    avg_time = toolset_data.get("avg_execution_time", 0.0)
                    total_tokens = toolset_data.get("total_tokens", 0)
                    
                    if avg_time == 0.0 and hasattr(report, "summary_stats") and report.summary_stats:
                        stats = report.summary_stats
                        avg_time = stats.get("avg_duration_ms", 0) / 1000.0
                        total_tokens = stats.get("total_tokens", 0)
                    
                    if avg_time > 0:
                        print(f"      Avg duration: {avg_time:.2f}s")
                    if total_tokens > 0:
                        print(f"      Total tokens: {total_tokens}")
                # Handle dict with aggregated data (legacy format)
                elif isinstance(toolset_data, dict):
                    if "avg_scores" in toolset_data:
                        for metric, value in toolset_data["avg_scores"].items():
                            print(f"      {metric}: {value:.3f}")
                    print(f"      Avg time: {toolset_data.get('avg_execution_time', 0):.2f}s")
                    print(f"      Total tokens: {toolset_data.get('total_tokens', 0)}")
                    print(f"      Errors: {toolset_data.get('errors', 0)}")
                    print(f"      Cases: {toolset_data.get('num_cases', 0)}")
                # Handle list of results
                elif isinstance(toolset_data, list):
                    if toolset_data:
                        avg_time = sum(r.execution_time for r in toolset_data) / len(toolset_data)
                        total_tokens = sum(r.token_usage.get("total_tokens", 0) for r in toolset_data)
                        errors = sum(1 for r in toolset_data if r.error)
                        
                        # Calculate average scores
                        score_keys = set()
                        for result in toolset_data:
                            score_keys.update(result.scores.keys())
                        
                        print(f"      Cases: {len(toolset_data)}")
                        print(f"      Errors: {errors}")
                        print(f"      Avg time: {avg_time:.2f}s")
                        print(f"      Total tokens: {total_tokens}")
                        if score_keys:
                            print(f"      Scores:")
                            for key in sorted(score_keys):
                                scores = [r.scores[key] for r in toolset_data if key in r.scores]
                                if scores:
                                    avg_score = sum(scores) / len(scores)
                                    print(f"        {key}: {avg_score:.3f}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run toolset evaluations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all evaluations
  python run_evals.py

  # Run a specific category
  python run_evals.py --category thinking

  # Run a single toolset
  python run_evals.py --toolset cot

  # Run multiple toolsets
  python run_evals.py --toolsets cot,tot,beam

  # Run toolsets from different categories
  python run_evals.py --toolsets cot,multi_personas,self_refine

Available toolsets:
  uniques: todo, search
  thinking: beam, cot, got, mcts, tot
  multi_agent: multi_personas, persona_debate
  reflection: self_refine, reflection, self_ask
  combinations: research_assistant, creative_problem_solver, strategic_decision_maker, code_architect
        """,
    )
    
    # Create mutually exclusive group for category/toolset selection
    selection_group = parser.add_mutually_exclusive_group()
    selection_group.add_argument(
        "--category",
        choices=["uniques", "thinking", "multi_agent", "reflection", "combinations", "all"],
        default="all",
        help="Category to evaluate (default: all)",
    )
    selection_group.add_argument(
        "--toolset",
        type=str,
        help="Single toolset to evaluate (e.g., cot, todo, multi_personas)",
    )
    selection_group.add_argument(
        "--toolsets",
        type=str,
        help="Comma-separated list of toolsets to evaluate (e.g., cot,tot,beam)",
    )
    
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("eval_results"),
        help="Output directory for results",
    )
    parser.add_argument(
        "--format",
        choices=["json", "csv"],
        default="json",
        help="Export format",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="OpenRouter API key (or set OPENROUTER_API_KEY env var)",
    )
    parser.add_argument(
        "--no-logfire",
        action="store_true",
        help="Disable Logfire integration",
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run evaluations in parallel instead of sequentially",
    )
    parser.add_argument(
        "--list-toolsets",
        action="store_true",
        help="List all available toolsets and exit",
    )
    parser.add_argument(
        "--use-llm-judge",
        action="store_true",
        help="Enable LLM Judge evaluators for quality assessment (slower, costs money)",
    )
    parser.add_argument(
        "--max-duration",
        type=float,
        default=300.0,
        help="Maximum allowed execution time in seconds (default: 300)",
    )

    args = parser.parse_args()
    
    # Handle --list-toolsets flag
    if args.list_toolsets:
        print("Available toolsets by category:\n")
        categories = ["uniques", "thinking", "multi_agent", "reflection", "combinations"]
        for category in categories:
            toolsets = get_toolsets_by_category(category)
            print(f"{category}:")
            for toolset in toolsets:
                info = TOOLSET_REGISTRY[toolset]
                print(f"  - {toolset:25s} ({info['display_name']})")
            print()
        sys.exit(0)

    # Setup configuration
    config = EvaluationConfig(
        api_key=args.api_key,
        use_llm_judge=args.use_llm_judge,
        max_duration_seconds=args.max_duration,
    )
    if args.no_logfire:
        config.logfire_enabled = False

    # Setup API key environment variable FIRST (before creating any agents)
    config.setup_environment()

    # Setup Logfire if enabled - MUST be configured BEFORE creating datasets
    # This is critical for experiments to show up in Logfire
    # According to docs: https://ai.pydantic.dev/evals/how-to/logfire-integration/
    if config.logfire_enabled and logfire:
        # Configure Logfire
        # Note: We disable scrubbing for evaluations since:
        # 1. We're not logging actual API keys (they're in env vars, not in logs)
        # 2. Model names and evaluation metadata are safe to log
        # 3. Scrubbing was causing false positives on model strings like "openrouter:x-ai/grok-4.1-fast"
        try:
            logfire.configure(
                send_to_logfire="if-token-present",  # Only send if LOGFIRE_TOKEN is set
                service_name="toolset-evaluations",
                environment="development",
                scrubbing=False,  # Disable scrubbing for evaluation runs
            )
        except TypeError:
            # Fallback if scrubbing parameter not supported in this version
            logfire.configure(
                send_to_logfire="if-token-present",
                service_name="toolset-evaluations",
                environment="development",
            )
            print("⚠ Note: Logfire scrubbing parameter not available - some data may be scrubbed")
        
        # Instrument pydantic-ai for full tracing
        logfire.instrument_pydantic_ai()
        print("✓ Logfire configured - experiments will appear in Logfire dashboard")
        print("  (Scrubbing disabled for evaluation data - API keys are not logged)")
    else:
        print("⚠ Logfire disabled - experiments will not appear in Logfire")

    # Run evaluations
    try:
        sequential = not args.parallel  # Default to sequential unless --parallel flag is set
        
        # Determine what to run based on arguments
        if args.toolset:
            # Run a single toolset
            results = await run_multiple_toolsets([args.toolset], config, sequential=sequential)
        elif args.toolsets:
            # Run multiple toolsets
            toolset_names = [name.strip() for name in args.toolsets.split(",")]
            results = await run_multiple_toolsets(toolset_names, config, sequential=sequential)
        elif args.category == "uniques":
            results = {"uniques": await run_uniques(config, sequential=sequential)}
        elif args.category == "thinking":
            results = {"thinking": await run_thinking(config)}
        elif args.category == "multi_agent":
            results = {"multi_agent": await run_multi_agent(config)}
        elif args.category == "reflection":
            results = {"reflection": await run_reflection(config)}
        elif args.category == "combinations":
            results = {"combinations": await run_combinations(config)}
        else:
            # Run all categories
            results = await run_all(config, sequential=sequential)

        # Print summary
        print_summary(results)

        # Export results
        export_results(results, args.output_dir, args.format)

        print("\nEvaluation complete!")

    except KeyboardInterrupt:
        print("\nEvaluation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during evaluation: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

