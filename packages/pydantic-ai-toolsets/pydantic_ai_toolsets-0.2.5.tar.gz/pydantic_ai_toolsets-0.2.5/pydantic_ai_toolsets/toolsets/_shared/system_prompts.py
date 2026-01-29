"""System prompt combination for multi-toolset workflows."""

from __future__ import annotations

import re
from typing import Any

from pydantic_ai.toolsets import AbstractToolset

from ..meta_orchestrator.types import WorkflowTemplate

# Import all system prompt getters
from ..chain_of_thought_reasoning.toolset import get_cot_system_prompt
from ..reflection.toolset import get_reflection_system_prompt
from ..self_ask.toolset import get_self_ask_system_prompt
from ..self_ask.types import MAX_DEPTH as SELF_ASK_MAX_DEPTH
from ..self_refine.toolset import get_self_refine_system_prompt
from ..to_do.toolset import get_todo_system_prompt
from ..search.toolset import get_search_system_prompt
from ..tree_of_thought_reasoning.toolset import get_tot_system_prompt
from ..graph_of_thought_reasoning.toolset import get_got_system_prompt
from ..monte_carlo_reasoning.toolset import get_mcts_system_prompt
from ..beam_search_reasoning.toolset import get_beam_system_prompt
from ..multi_persona_analysis.toolset import get_persona_system_prompt
from ..multi_persona_debate.toolset import get_persona_debate_system_prompt

# Mapping of toolset types to their system prompt getter functions
# These return STANDALONE prompts (for single-toolset usage)
TOOLSET_SYSTEM_PROMPT_GETTERS: dict[str, Any] = {
    "cot": lambda storage: get_cot_system_prompt(storage),
    "tot": lambda storage: get_tot_system_prompt(storage),
    "got": lambda storage: get_got_system_prompt(storage),
    "mcts": lambda storage: get_mcts_system_prompt(storage),
    "beam": lambda storage: get_beam_system_prompt(storage),
    "reflection": lambda storage: get_reflection_system_prompt(),
    "self_refine": lambda storage: get_self_refine_system_prompt(),
    "self_ask": lambda storage: get_self_ask_system_prompt(),
    "persona": lambda storage: get_persona_system_prompt(storage),
    "persona_debate": lambda storage: get_persona_debate_system_prompt(),
    "search": lambda storage: get_search_system_prompt(),
    "todo": lambda storage: get_todo_system_prompt(storage),
}


def identify_toolset_type(toolset: AbstractToolset[Any]) -> str:
    """Identify toolset type from its ID or label.

    Args:
        toolset: The toolset to identify

    Returns:
        Toolset type string (e.g., "cot", "tot", "self_ask")
    """
    toolset_id = (toolset.id or "").lower() if hasattr(toolset, "id") else ""
    toolset_label = (getattr(toolset, "label", "") or "").lower()

    # Check for known patterns
    if "cot" in toolset_id or "chain" in toolset_label:
        return "cot"
    elif "tot" in toolset_id or "tree" in toolset_label:
        return "tot"
    elif "got" in toolset_id or "graph" in toolset_label:
        return "got"
    elif "mcts" in toolset_id or "monte" in toolset_label:
        return "mcts"
    elif "beam" in toolset_id or toolset_label:
        return "beam"
    elif "reflection" in toolset_id or toolset_label:
        return "reflection"
    elif "self_refine" in toolset_id or "self-refine" in toolset_label:
        return "self_refine"
    elif "self_ask" in toolset_id or "self-ask" in toolset_label:
        return "self_ask"
    elif "persona" in toolset_id or toolset_label:
        if "debate" in toolset_id or toolset_label:
            return "persona_debate"
        return "persona"
    elif "search" in toolset_id or toolset_label:
        return "search"
    elif "todo" in toolset_id or toolset_label or "to_do" in toolset_id:
        return "todo"

    return "unknown"


def build_tool_name_mapping(prompt: str, prefix: str) -> dict[str, str]:
    """Build mapping of original tool names to prefixed names from prompt.

    Extracts tool names mentioned in backticks and creates mapping.

    Args:
        prompt: System prompt text
        prefix: Prefix to add to tool names

    Returns:
        Dictionary mapping original tool names to prefixed names
    """
    # Find all tool names in backticks (e.g., `read_thoughts`)
    tool_names = re.findall(r"`([a-z_]+)`", prompt.lower())
    # Remove duplicates while preserving order
    seen = set()
    unique_tool_names = []
    for name in tool_names:
        if name not in seen and len(name) > 2:  # Filter out very short matches
            seen.add(name)
            unique_tool_names.append(name)

    return {name: f"{prefix}{name}" for name in unique_tool_names}


def update_prompt_tool_names(prompt: str, tool_name_mapping: dict[str, str]) -> str:
    """Update tool names in a system prompt to reflect aliased names.

    Args:
        prompt: Original system prompt
        tool_name_mapping: Mapping of original tool names to aliased names
                          e.g., {"read_thoughts": "cot_read_thoughts"}

    Returns:
        Updated prompt with aliased tool names
    """
    updated_prompt = prompt
    for original_name, aliased_name in tool_name_mapping.items():
        # Replace backtick-wrapped tool names (common in prompts)
        updated_prompt = updated_prompt.replace(f"`{original_name}`", f"`{aliased_name}`")
        # Replace tool names in lists/descriptions
        updated_prompt = updated_prompt.replace(f"- `{original_name}`", f"- `{aliased_name}`")
        # Replace standalone mentions
        updated_prompt = updated_prompt.replace(f" {original_name}:", f" {aliased_name}:")

    return updated_prompt


def generate_workflow_instructions(
    workflow_template: WorkflowTemplate,
    prefix_map: dict[str, str] | None = None,
) -> str:
    """Generate workflow-specific instructions from a template.

    Args:
        workflow_template: The workflow template
        prefix_map: Optional mapping of toolset IDs to prefixes

    Returns:
        Workflow instructions string
    """
    lines = [
        "# Workflow: " + workflow_template.name.replace("_", " ").title(),
        "",
        workflow_template.description or "",
        "",
        "## ⚠️ IMPORTANT: Workflow Initialization",
        "",
        "**Before using any toolsets, you MUST initialize the workflow:**",
        "",
        f"1. Call `orchestrator_start_workflow` with `template_name='{workflow_template.name}'`",
        "2. This activates the workflow and enables proper coordination between toolsets",
        "3. After initialization, you can proceed with the workflow stages",
        "",
        "**Example:**",
        f"```",
        f"orchestrator_start_workflow(template_name='{workflow_template.name}')",
        f"```",
        "",
        "## Workflow Stages",
        "",
    ]

    for idx, stage in enumerate(workflow_template.stages):
        toolset_id = stage.toolset_id
        prefix = ""
        if prefix_map and toolset_id in prefix_map:
            prefix = prefix_map[toolset_id]

        lines.append(f"### Stage {idx + 1}: {stage.name}")
        lines.append(f"- **Toolset**: {toolset_id}")
        if prefix:
            lines.append(f"- **Prefix**: {prefix}")
        lines.append(f"- **Transition Condition**: {stage.transition_condition}")
        if stage.description:
            lines.append(f"- **Description**: {stage.description}")
        lines.append("")

    if workflow_template.handoff_instructions:
        lines.append("## Handoff Instructions")
        lines.append("")
        for transition, instruction in workflow_template.handoff_instructions.items():
            lines.append(f"- **{transition}**: {instruction}")
        lines.append("")

    return "\n".join(lines)


# =============================================================================
# COMBINATION PROMPT GENERATORS
# =============================================================================
# These generate prompts adapted for multi-toolset workflows

# Mapping of toolset types to their COMBINATION prompt generators
TOOLSET_COMBINATION_PROMPT_GENERATORS: dict[str, Any] = {
    "cot": lambda toolset, storage, other_toolsets, position, prefix_map, workflow_template: generate_cot_combination_prompt(
        toolset, storage, other_toolsets, position, prefix_map, workflow_template
    ),
    "tot": lambda toolset, storage, other_toolsets, position, prefix_map, workflow_template: generate_tot_combination_prompt(
        toolset, storage, other_toolsets, position, prefix_map, workflow_template
    ),
    "got": lambda toolset, storage, other_toolsets, position, prefix_map, workflow_template: generate_got_combination_prompt(
        toolset, storage, other_toolsets, position, prefix_map, workflow_template
    ),
    "mcts": lambda toolset, storage, other_toolsets, position, prefix_map, workflow_template: generate_mcts_combination_prompt(
        toolset, storage, other_toolsets, position, prefix_map, workflow_template
    ),
    "beam": lambda toolset, storage, other_toolsets, position, prefix_map, workflow_template: generate_beam_combination_prompt(
        toolset, storage, other_toolsets, position, prefix_map, workflow_template
    ),
    "reflection": lambda toolset, storage, other_toolsets, position, prefix_map, workflow_template: generate_reflection_combination_prompt(
        toolset, storage, other_toolsets, position, prefix_map, workflow_template
    ),
    "self_refine": lambda toolset, storage, other_toolsets, position, prefix_map, workflow_template: generate_self_refine_combination_prompt(
        toolset, storage, other_toolsets, position, prefix_map, workflow_template
    ),
    "self_ask": lambda toolset, storage, other_toolsets, position, prefix_map, workflow_template: generate_self_ask_combination_prompt(
        toolset, storage, other_toolsets, position, prefix_map, workflow_template
    ),
    "persona": lambda toolset, storage, other_toolsets, position, prefix_map, workflow_template: generate_persona_combination_prompt(
        toolset, storage, other_toolsets, position, prefix_map, workflow_template
    ),
    "persona_debate": lambda toolset, storage, other_toolsets, position, prefix_map, workflow_template: generate_persona_debate_combination_prompt(
        toolset, storage, other_toolsets, position, prefix_map, workflow_template
    ),
    "search": lambda toolset, storage, other_toolsets, position, prefix_map, workflow_template: generate_search_combination_prompt(
        toolset, storage, other_toolsets, position, prefix_map, workflow_template
    ),
    "todo": lambda toolset, storage, other_toolsets, position, prefix_map, workflow_template: generate_todo_combination_prompt(
        toolset, storage, other_toolsets, position, prefix_map, workflow_template
    ),
}


def generate_search_combination_prompt(
    toolset: AbstractToolset[Any],
    storage: Any | None,
    other_toolsets: list[AbstractToolset[Any]],
    position: int,
    prefix_map: dict[str, str] | None,
    workflow_template: WorkflowTemplate | None,
) -> str:
    """Generate combination-specific prompt for Search toolset."""
    toolset_id = toolset.id if hasattr(toolset, "id") else "search"
    prefix = prefix_map.get(toolset_id, "search_") if prefix_map else "search_"

    other_types = [identify_toolset_type(t) for t in other_toolsets]
    prev_types = [identify_toolset_type(t) for i, t in enumerate(other_toolsets) if i < position]
    next_types = [identify_toolset_type(t) for i, t in enumerate(other_toolsets) if i > position]

    # Get standalone prompt for reference (search doesn't use storage)
    base_prompt = get_search_system_prompt()

    prompt = f"""## Web Search, News Search, and Image Search (Stage {position + 1} of {len(other_toolsets) + 1})

You have access to tools for searching the web, news, and images, and extracting content:
- `{prefix}search_web`: Search the web for information using Firecrawl
- `{prefix}search_news`: Search for news articles using Firecrawl (supports time filtering)
- `{prefix}search_images`: Search for images using Firecrawl (supports resolution filtering)
- `{prefix}extract_web_content`: Extract main content from webpages using Trafilatura (works with web and news results only)

### When to Use Each Search Type

**Web Search (`{prefix}search_web`):**
1. Finding current information on the web
2. Researching topics that require up-to-date data
3. Gathering information from multiple sources
4. Verifying facts or finding authoritative sources

**News Search (`{prefix}search_news`):**
1. Finding recent news articles and developments
2. Searching for time-specific news (use time_filter: PAST_HOUR, PAST_DAY, PAST_WEEK, PAST_MONTH, PAST_YEAR, or CUSTOM)
3. Getting news from specific date ranges
4. When you need news-focused results rather than general web results

**Image Search (`{prefix}search_images`):**
1. Finding images related to a topic
2. Searching for high-resolution images (use exact_width/exact_height or min_width/min_height)
3. Finding images of specific sizes

**In this workflow context:**
- Your search results will feed into subsequent reasoning stages
- Focus on gathering comprehensive, relevant information
- Extract content from the most authoritative sources (web and news only)

### Your Role in This Workflow

You are the **information gathering** stage. Your search results will be used by other toolsets in this workflow:
"""

    if "self_ask" in other_types:
        prompt += "- Search results will be used to formulate questions for decomposition\n"
    if "self_refine" in other_types or "reflection" in other_types:
        prompt += "- Search results will inform the refinement process\n"
    if "todo" in other_types:
        prompt += "- Search results may be tracked as completed research tasks\n"

    prompt += f"""
### Key Principles

- **Specific Queries**: Use specific, keyword-rich queries for better results
- **Time Filtering**: Use `{prefix}search_news` with time_filter when you need recent news (e.g., "news from past week")
- **Resolution Filtering**: Use `{prefix}search_images` with exact_width/exact_height for exact sizes or min_width/min_height for minimum sizes
- **Relevant URLs**: Extract content from URLs that are most relevant to your task
- **Format Choice**: Use markdown format if you need structured content, txt for simple text
- **Efficiency**: Previously extracted content is stored and can be accessed without re-extraction
- **Content Extraction**: Only web and news results support content extraction; image results cannot be extracted
- **Workflow Integration**: Your results inform the next stage's reasoning process

### Workflow Process

1. **Search**: Choose the appropriate search tool based on your needs
   - `{prefix}search_web`: General web search
   - `{prefix}search_news`: News articles (use time_filter for recent news)
   - `{prefix}search_images`: Images (use resolution parameters for size filtering)
   - Provide specific, keyword-rich queries for better results
   - Specify number of results needed (default: 5, max: 50)
   - Results include titles, URLs, and descriptions (images also include dimensions)
2. **Extract**: Use `{prefix}extract_web_content` for relevant URLs
   - **Only works with web and news search results** (not image results)
   - Choose URLs from search results that are most relevant
   - Choose output format: 'txt' for plain text or 'markdown' for markdown
   - Previously extracted content is stored and can be accessed without re-extraction
3. **Transition**: After gathering sufficient information, proceed to the next stage
"""

    if "self_ask" in next_types:
        prompt += f"   - Use search results to formulate main questions for `{prefix_map.get('self_ask', 'self_ask_')}ask_main_question`\n"
    if "self_refine" in next_types or "reflection" in next_types:
        prompt += f"   - Use search results as context for refinement in the next stage\n"

    return prompt


def generate_self_ask_combination_prompt(
    toolset: AbstractToolset[Any],
    storage: Any | None,
    other_toolsets: list[AbstractToolset[Any]],
    position: int,
    prefix_map: dict[str, str] | None,
    workflow_template: WorkflowTemplate | None,
) -> str:
    """Generate combination-specific prompt for Self-Ask toolset."""
    toolset_id = toolset.id if hasattr(toolset, "id") else "self_ask"
    prefix = prefix_map.get(toolset_id, "self_ask_") if prefix_map else "self_ask_"

    other_types = [identify_toolset_type(t) for t in other_toolsets]
    prev_types = [identify_toolset_type(t) for i, t in enumerate(other_toolsets) if i < position]
    next_types = [identify_toolset_type(t) for i, t in enumerate(other_toolsets) if i > position]

    # Get standalone prompt for reference (self_ask doesn't use storage)
    base_prompt = get_self_ask_system_prompt()
    max_depth = SELF_ASK_MAX_DEPTH

    prompt = f"""## Self-Ask Question Decomposition (Stage {position + 1} of {len(other_toolsets) + 1})

You have access to tools for decomposing complex questions into simpler sub-questions:
- `{prefix}read_self_ask_state`: Read current self-ask state
- `{prefix}ask_main_question`: Initialize main question (depth 0)
- `{prefix}ask_sub_question`: Generate sub-question from parent question
- `{prefix}answer_question`: Answer a question/sub-question
- `{prefix}compose_final_answer`: Compose final answer from sub-question answers
- `{prefix}get_final_answer`: Retrieve the final composed answer

### When to Use Self-Ask

Use these tools in these scenarios:
1. Complex questions requiring multi-hop reasoning
2. Questions that need to be broken down into simpler parts
3. Problems where intermediate answers build toward a final answer
4. Questions requiring information gathering from multiple sources
5. Situations where explicit decomposition makes reasoning transparent

**In this workflow context:**
- Use information from previous stages to inform your main question
- Your decomposed answer will feed into subsequent refinement stages
- Focus on thorough decomposition rather than perfect answers (refinement comes next)

### Your Role in This Workflow

You are the **question decomposition** stage. """

    if "search" in prev_types:
        prompt += "Use search results from the previous stage to formulate your main question.\n"
    if "self_refine" in next_types or "reflection" in next_types:
        prompt += "Your final answer will be refined by the next stage.\n"

    prompt += f"""
### Integration with Other Stages

**Input from Previous Stages:**
"""
    if "search" in prev_types:
        prompt += "- Use search results to inform your main question\n"
        prompt += "- Reference extracted content when answering sub-questions\n"

    prompt += f"""
**Output to Next Stages:**
"""
    if "self_refine" in next_types or "reflection" in next_types:
        prompt += "- Your final answer will be refined/improved by the next stage\n"
        prompt += "- Focus on completeness rather than perfection (refinement comes next)\n"
    if "todo" in next_types:
        prompt += "- Your final answer may be tracked as a completed task\n"

    prompt += f"""
### Depth Constraint

**IMPORTANT**: Maximum depth of {max_depth} levels:
- Main question: depth 0
- Sub-questions: depth 1
- Sub-sub-questions: depth 2
- Sub-sub-sub-questions: depth 3 (maximum)

When the depth limit is reached:
- Answer remaining questions at maximum depth
- Use those answers to compose the final answer
- Do not attempt to create questions beyond depth {max_depth}

### Question Types

- **Sequential Dependency**: Later questions depend on earlier answers
  - Example: "Where were the 2016 Olympics?" → "What was the population there?"
- **Parallel Questions**: Independent questions that can be answered in any order
  - Example: "Japan's GDP growth?" and "Germany's GDP growth?" (both independent)
- **Recursive Decomposition**: Sub-questions spawn sub-sub-questions
  - Example: "How did WWI affect art?" → "What art movements emerged?" → "What was Dadaism?"

### Key Principles

- **Explicit Decomposition**: Make reasoning transparent by showing sub-questions
- **Sequential Dependency**: Build answers from earlier sub-question answers
- **Compositional Reasoning**: Combine simple facts into complex insights
- **Depth Management**: Respect the depth limit and compose final answer when limit reached
- **Answer Tracking**: Track which answers contribute to the final composition

### Self-Ask Process

1. **Read State**: Call `{prefix}read_self_ask_state` to see current state
   - Review existing questions and their depths
   - Check which questions have been answered
   - Understand the question tree structure
2. **Main Question**: Initialize using `{prefix}ask_main_question`
   - Base it on information from previous stages if available
   - This will be at depth 0 (the root)
3. **Decompose**: Generate sub-questions using `{prefix}ask_sub_question`
   - Respect the maximum depth limit ({max_depth})
   - Generate sub-questions that help answer the main question
   - Consider sequential vs parallel question strategies
4. **Answer**: Answer sub-questions using `{prefix}answer_question`
   - Use answers from earlier sub-questions to answer later ones
   - Mark if a sub-question needs further decomposition
   - Provide confidence scores when helpful
5. **Compose**: Synthesize final answer using `{prefix}compose_final_answer`
   - Reference the main question ID
   - List all answer IDs that contributed
   - Create a coherent, complete answer
6. **Retrieve**: Get the final composed answer using `{prefix}get_final_answer`
7. **Transition**: After composing final answer, proceed to next stage

**IMPORTANT**: Always call `{prefix}read_self_ask_state` before asking questions, answering, or composing.
"""

    return prompt


def generate_self_refine_combination_prompt(
    toolset: AbstractToolset[Any],
    storage: Any | None,
    other_toolsets: list[AbstractToolset[Any]],
    position: int,
    prefix_map: dict[str, str] | None,
    workflow_template: WorkflowTemplate | None,
) -> str:
    """Generate combination-specific prompt for Self-Refine toolset."""
    toolset_id = toolset.id if hasattr(toolset, "id") else "self_refine"
    prefix = prefix_map.get(toolset_id, "self_refine_") if prefix_map else "self_refine_"

    other_types = [identify_toolset_type(t) for t in other_toolsets]
    prev_types = [identify_toolset_type(t) for i, t in enumerate(other_toolsets) if i < position]
    next_types = [identify_toolset_type(t) for i, t in enumerate(other_toolsets) if i > position]

    # Get standalone prompt for reference (self_refine doesn't use storage)
    base_prompt = get_self_refine_system_prompt()

    prompt = f"""## Self-Refinement (Stage {position + 1} of {len(other_toolsets) + 1})

You have access to tools for improving outputs through iterative self-refinement:
- `{prefix}read_refinement_state`: Read current refinement state
- `{prefix}generate_output`: Create initial output (iteration 0)
- `{prefix}provide_feedback`: Provide structured, actionable feedback
- `{prefix}refine_output`: Generate improved version based on feedback
- `{prefix}get_best_output`: Find the best refined output

### When to Use Self-Refinement

Use these tools in these scenarios:
1. Tasks requiring high-quality, polished outputs
2. Problems where initial solutions may have flaws
3. Situations where iterative improvement is valuable
4. Tasks where structured feedback helps identify issues
5. Problems where multiple refinement cycles improve results
6. When you need to meet specific quality thresholds

**In this workflow context:**
- Use outputs from previous stages as your initial output
- Focus on improving completeness, accuracy, and clarity
- Your refined output will be the final result or feed into subsequent stages

### Your Role in This Workflow

You are the **refinement** stage. """

    if "self_ask" in prev_types:
        prompt += "Use the final answer from self-ask as your initial output.\n"
    elif "search" in prev_types:
        prompt += "Use search results to inform your initial output.\n"
    elif "tot" in prev_types or "got" in prev_types:
        prompt += "Use the best solution from exploration as your initial output.\n"

    prompt += f"""
### Integration with Other Stages

**Input from Previous Stages:**
"""
    if "self_ask" in prev_types:
        prompt += "- Use the final composed answer from self-ask as your initial output\n"
        prompt += "- Refine and improve upon the decomposed answer\n"
    if "search" in prev_types:
        prompt += "- Use search results as context for refinement\n"
    if "tot" in prev_types or "got" in prev_types:
        prompt += "- Use the best solution from exploration as your initial output\n"

    prompt += f"""
**Output to Next Stages:**
"""
    if "todo" in next_types:
        prompt += "- Your refined output may be tracked as a completed task\n"

    prompt += f"""
### Feedback Types

- **Additive**: Missing information about X, should include Y
- **Subtractive**: Remove redundant section Z
- **Transformative**: Restructure argument to lead with conclusion
- **Corrective**: Fix factual error in paragraph 3

### Feedback Dimensions

- **Factuality**: Accuracy and correctness of information
- **Coherence**: Logical flow and consistency
- **Completeness**: All necessary information included
- **Style**: Writing style and clarity

### Key Principles

- **Structured Feedback**: Use feedback types and dimensions systematically
- **Actionable Suggestions**: Feedback should be specific enough to guide improvement
- **Weighted Feedback**: Prioritize certain aspects (e.g., correctness > style)
- **Iterative Convergence**: Quality typically improves most in first 2-3 iterations
- **Quality Tracking**: Use quality scores to track improvement and compare against thresholds

### Self-Refinement Process

1. **Read State**: Call `{prefix}read_refinement_state` to see current state
   - Review existing outputs and their iterations
   - Check feedback and identified areas for improvement
   - Track quality scores and thresholds
2. **Generate**: Create initial output using `{prefix}generate_output`
   - Use outputs from previous stages if available
   - Set quality_threshold if you have a target quality level
   - Set iteration_limit if you want to cap refinement cycles (typically 2-3)
3. **Feedback**: Provide detailed, actionable feedback using `{prefix}provide_feedback`
   - Use structured feedback types: additive, subtractive, transformative, corrective
   - Evaluate multiple dimensions: factuality, coherence, completeness, style
   - Prioritize feedback (higher priority = more important)
   - Indicate if refinement should continue
4. **Refine**: Generate improved version using `{prefix}refine_output`
   - Address all feedback, especially high-priority items
   - Provide quality score to track improvement
   - Mark as final if quality threshold is met or no further improvement needed
5. **Repeat**: Continue feedback-refine cycle until:
   - Quality threshold is met (quality_score >= quality_threshold)
   - Iteration limit is reached (iteration >= iteration_limit)
   - Feedback indicates no further improvements needed
6. **Select**: Use `{prefix}get_best_output` for final result

**IMPORTANT**: Always call `{prefix}read_refinement_state` before generating, providing feedback, or refining.
"""

    return prompt


def generate_todo_combination_prompt(
    toolset: AbstractToolset[Any],
    storage: Any | None,
    other_toolsets: list[AbstractToolset[Any]],
    position: int,
    prefix_map: dict[str, str] | None,
    workflow_template: WorkflowTemplate | None,
) -> str:
    """Generate combination-specific prompt for Todo toolset."""
    toolset_id = toolset.id if hasattr(toolset, "id") else "todo"
    prefix = prefix_map.get(toolset_id, "todo_") if prefix_map else "todo_"

    other_types = [identify_toolset_type(t) for t in other_toolsets]
    prev_types = [identify_toolset_type(t) for i, t in enumerate(other_toolsets) if i < position]

    # Get standalone prompt with storage for dynamic content
    base_prompt = get_todo_system_prompt(storage)

    prompt = f"""## Task Management (Stage {position + 1} of {len(other_toolsets) + 1})

You have access to tools for managing tasks:
- `{prefix}read_todos`: Read the current todo list
- `{prefix}write_todos`: Update the todo list with new items

### When to Use Task Management

Use these tools in these scenarios:
1. Complex multi-step tasks (3+ distinct steps)
2. Non-trivial tasks requiring careful planning
3. User provides multiple tasks
4. After receiving new instructions - capture requirements as todos
5. When starting a task - mark it as in_progress BEFORE beginning work
6. After completing a task - mark it as completed immediately

**In this workflow context:**
- Track progress across all workflow stages
- Monitor completion of research, decomposition, and refinement tasks
- Ensure workflow milestones are properly tracked

### Task States

- **pending**: Task not yet started
- **in_progress**: Currently working on (limit to ONE at a time)
- **completed**: Task finished successfully

### Important Rules

- Exactly ONE task should be in_progress at any time
- Mark tasks complete IMMEDIATELY after finishing (don't batch completions)
- If you encounter blockers, keep the task as in_progress and create a new task for the blocker

### Your Role in This Workflow

You are the **task tracking** stage. Track progress and manage workflow tasks.

### Integration with Other Stages

**Tracking from Previous Stages:**
"""
    if "self_refine" in prev_types or "reflection" in prev_types:
        prompt += "- Track refined outputs as completed tasks\n"
    if "self_ask" in prev_types:
        prompt += "- Track question decomposition progress\n"
    if "search" in prev_types:
        prompt += "- Track research tasks and completed searches\n"
    if "tot" in prev_types or "got" in prev_types:
        prompt += "- Track exploration and solution finding tasks\n"

    prompt += f"""
### Task Management Process

1. **Read**: Check current tasks using `{prefix}read_todos`
   - Review all todos with their current status (pending, in_progress, completed)
   - Use before updating task statuses or reporting progress
2. **Update**: Mark tasks as completed using `{prefix}write_todos`
   - Break down complex tasks into smaller steps
   - Mark exactly one task as in_progress at a time
   - Mark tasks as completed immediately after finishing
3. **Track**: Monitor workflow progress across all stages
   - Ensure workflow milestones are properly tracked
   - Coordinate with other stages to track their progress
"""

    # Add dynamic storage content if available
    if storage and hasattr(storage, "todos") and storage.todos:
        prompt += "\n### Current Todos\n\n"
        for todo in storage.todos:
            status_icon = {
                "pending": "[ ]",
                "in_progress": "[*]",
                "completed": "[x]",
            }.get(todo.status, "[ ]")
            prompt += f"- {status_icon} {todo.content}\n"

    return prompt


def generate_reflection_combination_prompt(
    toolset: AbstractToolset[Any],
    storage: Any | None,
    other_toolsets: list[AbstractToolset[Any]],
    position: int,
    prefix_map: dict[str, str] | None,
    workflow_template: WorkflowTemplate | None,
) -> str:
    """Generate combination-specific prompt for Reflection toolset."""
    toolset_id = toolset.id if hasattr(toolset, "id") else "reflection"
    prefix = prefix_map.get(toolset_id, "reflection_") if prefix_map else "reflection_"

    other_types = [identify_toolset_type(t) for t in other_toolsets]
    prev_types = [identify_toolset_type(t) for i, t in enumerate(other_toolsets) if i < position]
    next_types = [identify_toolset_type(t) for i, t in enumerate(other_toolsets) if i > position]

    # Get standalone prompt for reference (reflection doesn't use storage)
    base_prompt = get_reflection_system_prompt()

    prompt = f"""## Reflection (Stage {position + 1} of {len(other_toolsets) + 1})

You have access to tools for improving outputs through reflection:
- `{prefix}read_reflection`: Read current reflection state
- `{prefix}create_output`: Create initial output (cycle 0)
- `{prefix}critique_output`: Critically analyze an output
- `{prefix}refine_output`: Generate improved version based on critique
- `{prefix}get_best_output`: Find the best refined output

### When to Use Reflection

Use these tools in these scenarios:
1. Tasks requiring high-quality, polished outputs
2. Problems where initial solutions may have flaws
3. Situations where critical analysis improves results
4. Tasks where iterative improvement through critique is valuable
5. Problems where multiple refinement cycles improve outcomes

**In this workflow context:**
- Use outputs from previous stages as your initial output
- Focus on improving completeness, accuracy, and clarity through critique
- Your refined output will be the final result or feed into subsequent stages

### Your Role in This Workflow

You are the **reflection and refinement** stage. """

    if "self_ask" in prev_types:
        prompt += "Use the final answer from self-ask as your initial output.\n"
    elif "persona" in prev_types:
        prompt += "Use synthesized persona perspectives as your initial output.\n"
    elif "tot" in prev_types or "got" in prev_types:
        prompt += "Use the best solution from tree/graph exploration as your initial output.\n"
    elif "mcts" in prev_types:
        prompt += "Use the best action from MCTS exploration as your initial output.\n"

    prompt += f"""
### Integration with Other Stages

**Input from Previous Stages:**
"""
    if "self_ask" in prev_types:
        prompt += "- Use the final composed answer from self-ask as your initial output\n"
    if "persona" in prev_types:
        prompt += "- Use synthesized persona perspectives as your initial output\n"
    if "tot" in prev_types or "got" in prev_types:
        prompt += "- Use the best solution from exploration as your initial output\n"
    if "mcts" in prev_types:
        prompt += "- Use the best action from MCTS as your initial output\n"

    prompt += f"""
**Output to Next Stages:**
"""
    if "todo" in next_types:
        prompt += "- Your refined output may be tracked as a completed task\n"

    prompt += f"""
### Key Principles

- **Critical Analysis**: Use critique to identify areas for improvement systematically
- **Iterative Refinement**: Multiple critique-refine cycles typically improve quality
- **Comprehensive Critique**: Analyze outputs from multiple angles (accuracy, completeness, clarity)
- **Best Output Selection**: Choose the highest-quality refined output as final result

### Reflection Process

1. **Read State**: Call `{prefix}read_reflection` to see current state
   - Review existing outputs and their refinement cycles
   - Check critiques and identified areas for improvement
2. **Create**: Create initial output using `{prefix}create_output`
   - Use outputs from previous stages if available
   - This will be cycle 0 (starting point for refinement)
3. **Critique**: Analyze critically using `{prefix}critique_output`
   - Identify strengths and weaknesses
   - Provide specific, actionable feedback
   - Consider multiple dimensions: accuracy, completeness, clarity, coherence
4. **Refine**: Generate improved version using `{prefix}refine_output`
   - Address all critique points systematically
   - Incorporate improvements based on feedback
5. **Repeat**: Continue critique-refine cycles until satisfied
   - Typically 2-3 cycles provide significant improvement
   - Stop when critique indicates no further improvements needed
6. **Select**: Use `{prefix}get_best_output` for final result
   - Choose the highest-quality refined output
"""

    return prompt


def generate_cot_combination_prompt(
    toolset: AbstractToolset[Any],
    storage: Any | None,
    other_toolsets: list[AbstractToolset[Any]],
    position: int,
    prefix_map: dict[str, str] | None,
    workflow_template: WorkflowTemplate | None,
) -> str:
    """Generate combination-specific prompt for Chain of Thought toolset."""
    toolset_id = toolset.id if hasattr(toolset, "id") else "cot"
    prefix = prefix_map.get(toolset_id, "cot_") if prefix_map else "cot_"

    other_types = [identify_toolset_type(t) for t in other_toolsets]
    prev_types = [identify_toolset_type(t) for i, t in enumerate(other_toolsets) if i < position]
    next_types = [identify_toolset_type(t) for i, t in enumerate(other_toolsets) if i > position]

    # Get base prompt WITH storage-based dynamic content
    base_prompt = get_cot_system_prompt(storage)

    # Extract "Current State" section if present (contains dynamic storage content)
    current_state_section = ""
    if "## Current State" in base_prompt:
        current_state_section = "\n" + base_prompt.split("## Current State", 1)[1]

    prompt = f"""## Chain of Thoughts (Stage {position + 1} of {len(other_toolsets) + 1})

You have access to tools for managing your reasoning process:
- `{prefix}read_thoughts`: Review your current chain of thoughts
- `{prefix}write_thoughts`: Add a new thought to your chain

### When to Use Chain of Thoughts

Use these tools in these scenarios:
1. Complex problems requiring multi-step reasoning
2. Planning and design tasks that may need revision
3. Analysis where understanding evolves
4. Multi-step solutions needing context tracking
5. Problems with uncertainty requiring exploration
6. Hypothesis generation and verification

**In this workflow context:**
- Use sequential reasoning to build on outputs from previous stages
- Your reasoning chain will inform subsequent stages
- Document your thought process for transparency

### Your Role in This Workflow

You provide **sequential reasoning** capabilities. Use this toolset for step-by-step thinking.

### Integration with Other Stages

**Input from Previous Stages:**
"""
    if "search" in prev_types:
        prompt += "- Use search results to inform your reasoning\n"
    if "self_ask" in prev_types:
        prompt += "- Use decomposed questions to guide your reasoning\n"

    prompt += f"""
**Output to Next Stages:**
"""
    if "reflection" in next_types or "self_refine" in next_types:
        prompt += "- Your reasoning chain will inform the refinement process\n"
    if "todo" in next_types:
        prompt += "- Your reasoning steps may be tracked as completed tasks\n"

    prompt += f"""
### Thought Management

- Start with thought_number=1 and estimate total_thoughts
- Each thought should build on, question, or revise previous insights
- Mark is_revision=true when reconsidering previous thoughts
- Use branch_from_thought and branch_id for alternative paths
- Set next_thought_needed=false when you've reached a satisfactory answer

### Chain of Thoughts Process

1. **Read**: Call `{prefix}read_thoughts` to see your current reasoning state
   - Review previous reasoning
   - Determine the next thought_number
   - Avoid repeating yourself
   - Make informed revisions
2. **Write**: Call `{prefix}write_thoughts` to add your next thought
   - Increment thought_number from previous
   - Build on, question, or revise previous insights
   - Adjust total_thoughts estimate as understanding deepens
3. **Repeat**: Continue until you reach a conclusion
   - Set next_thought_needed=false when satisfied
   - Use revisions and branches to explore alternatives

**IMPORTANT**: Always call `{prefix}read_thoughts` before `{prefix}write_thoughts` to review previous reasoning and determine the next thought_number.
"""

    # Add dynamic storage content if present
    if current_state_section:
        # Update tool names in current state section
        tool_name_mapping = build_tool_name_mapping(current_state_section, prefix)
        current_state_section = update_prompt_tool_names(current_state_section, tool_name_mapping)
        prompt += current_state_section

    # Update tool names in the main prompt
    tool_name_mapping = build_tool_name_mapping(prompt, prefix)
    prompt = update_prompt_tool_names(prompt, tool_name_mapping)

    return prompt


def generate_tot_combination_prompt(
    toolset: AbstractToolset[Any],
    storage: Any | None,
    other_toolsets: list[AbstractToolset[Any]],
    position: int,
    prefix_map: dict[str, str] | None,
    workflow_template: WorkflowTemplate | None,
) -> str:
    """Generate combination-specific prompt for Tree of Thought toolset."""
    toolset_id = toolset.id if hasattr(toolset, "id") else "tot"
    prefix = prefix_map.get(toolset_id, "tot_") if prefix_map else "tot_"

    other_types = [identify_toolset_type(t) for t in other_toolsets]
    prev_types = [identify_toolset_type(t) for i, t in enumerate(other_toolsets) if i < position]
    next_types = [identify_toolset_type(t) for i, t in enumerate(other_toolsets) if i > position]

    # Get base prompt WITH storage-based dynamic content
    base_prompt = get_tot_system_prompt(storage)

    # Extract "Current State" section if present
    current_state_section = ""
    if "## Current State" in base_prompt:
        current_state_section = "\n" + base_prompt.split("## Current State", 1)[1]

    prompt = f"""## Tree of Thoughts (Stage {position + 1} of {len(other_toolsets) + 1})

You have access to tools for exploring multiple reasoning paths:
- `{prefix}read_tree`: Review the current tree structure
- `{prefix}create_node`: Create a new reasoning node (root or child)
- `{prefix}evaluate_branch`: Evaluate a branch's promise (0-100 score)
- `{prefix}prune_branch`: Mark a branch as dead end
- `{prefix}merge_insights`: Combine insights from multiple branches

### When to Use Tree of Thoughts

Use these tools in these scenarios:
1. Complex problems with multiple valid approaches
2. Problems requiring exploration of alternatives
3. Situations needing backtracking from dead ends
4. Tasks where combining insights from different paths is valuable
5. Problems where evaluation of paths is important

**In this workflow context:**
- Explore multiple solution approaches systematically
- Your best solution will feed into subsequent refinement stages
- Use evaluation to guide exploration efficiently

### Your Role in This Workflow

You are the **exploration** stage. Explore multiple approaches to find the best solution.

### Integration with Other Stages

**Input from Previous Stages:**
"""
    if "self_ask" in prev_types:
        prompt += "- Use decomposed questions to seed tree exploration\n"
    if "persona" in prev_types:
        prompt += "- Use synthesized persona perspectives to seed exploration\n"

    prompt += f"""
**Output to Next Stages:**
"""
    if "reflection" in next_types:
        prompt += "- Best solution from tree will be refined by reflection\n"
    if "self_refine" in next_types:
        prompt += "- Best solution will be refined through iterative improvement\n"
    if "todo" in next_types:
        prompt += "- Solution finding progress may be tracked as tasks\n"

    prompt += f"""
### Tree Structure

- Nodes represent reasoning states
- Branches represent different paths/approaches (identified by branch_id)
- Root nodes have no parent (parent_id=None)
- Child nodes extend existing branches

### Key Principles

- **Systematic Exploration**: Explore multiple paths before committing to one
- **Evaluation-Driven**: Use branch evaluation to guide exploration
- **Pruning Strategy**: Remove dead ends to focus on promising paths
- **Insight Merging**: Combine insights from multiple branches when valuable
- **Solution Marking**: Mark solution nodes with is_solution=true

### Tree of Thoughts Process

1. **Read**: Call `{prefix}read_tree` to see current state
   - Review tree structure with parent-child relationships
   - Check node status (active, pruned, merged, completed)
   - Review branch evaluations and recommendations
2. **Create**: Create nodes for different approaches using `{prefix}create_node`
   - Create root nodes for different initial approaches (use unique branch_ids)
   - Extend promising branches by creating child nodes
   - Mark solution nodes with is_solution=true
3. **Evaluate**: Evaluate branches using `{prefix}evaluate_branch`
   - Assign 0-100 scores based on promise
   - Provide reasoning for scores
   - Get recommendations: "continue", "prune", "merge", or "explore_deeper"
4. **Prune**: Remove dead ends using `{prefix}prune_branch`
   - Mark branches that lead nowhere
   - Provide reason for pruning
5. **Merge**: Combine insights using `{prefix}merge_insights`
   - Combine insights from multiple source branches
   - Create merged node with combined content
   - Mark as solution if merged result solves the problem

**IMPORTANT**: Always call `{prefix}read_tree` before modifying the tree.
"""

    # Add dynamic storage content if present
    if current_state_section:
        tool_name_mapping = build_tool_name_mapping(current_state_section, prefix)
        current_state_section = update_prompt_tool_names(current_state_section, tool_name_mapping)
        prompt += current_state_section

    # Update tool names in the main prompt
    tool_name_mapping = build_tool_name_mapping(prompt, prefix)
    prompt = update_prompt_tool_names(prompt, tool_name_mapping)

    return prompt


def generate_got_combination_prompt(
    toolset: AbstractToolset[Any],
    storage: Any | None,
    other_toolsets: list[AbstractToolset[Any]],
    position: int,
    prefix_map: dict[str, str] | None,
    workflow_template: WorkflowTemplate | None,
) -> str:
    """Generate combination-specific prompt for Graph of Thought toolset."""
    toolset_id = toolset.id if hasattr(toolset, "id") else "got"
    prefix = prefix_map.get(toolset_id, "got_") if prefix_map else "got_"

    other_types = [identify_toolset_type(t) for t in other_toolsets]
    prev_types = [identify_toolset_type(t) for i, t in enumerate(other_toolsets) if i < position]
    next_types = [identify_toolset_type(t) for i, t in enumerate(other_toolsets) if i > position]

    # Get base prompt WITH storage-based dynamic content
    base_prompt = get_got_system_prompt(storage)

    # Extract "Current State" section if present
    current_state_section = ""
    if "## Current State" in base_prompt:
        current_state_section = "\n" + base_prompt.split("## Current State", 1)[1]

    prompt = f"""## Graph of Thoughts (Stage {position + 1} of {len(other_toolsets) + 1})

You have access to tools for graph-based reasoning:
- `{prefix}read_graph`: Review current graph state
- `{prefix}create_node`: Create a reasoning node
- `{prefix}create_edge`: Connect nodes with edges
- `{prefix}aggregate_nodes`: Combine multiple nodes
- `{prefix}refine_node`: Improve a node's content
- `{prefix}evaluate_node`: Score a node (0-100)
- `{prefix}prune_node`: Mark node as not useful
- `{prefix}find_path`: Find paths between nodes

### When to Use Graph of Thoughts

Use these tools in these scenarios:
1. Complex problems with interconnected sub-problems
2. Tasks requiring synthesis from multiple perspectives
3. Iterative refinement of solutions
4. Problems with non-linear dependencies
5. Building on partial solutions

**In this workflow context:**
- Explore interconnected solution paths systematically
- Your best path will feed into subsequent refinement stages
- Use graph structure to capture complex reasoning relationships

### Your Role in This Workflow

You are the **graph exploration** stage. Explore interconnected reasoning paths.

### Integration with Other Stages

**Input from Previous Stages:**
"""
    if "persona" in prev_types:
        prompt += "- Use synthesized persona perspectives to seed graph exploration\n"
    if "self_ask" in prev_types:
        prompt += "- Use decomposed questions to seed graph nodes\n"

    prompt += f"""
**Output to Next Stages:**
"""
    if "reflection" in next_types:
        prompt += "- Best path from graph will be refined by reflection\n"
    if "self_refine" in next_types:
        prompt += "- Best path will be refined through iterative improvement\n"
    if "todo" in next_types:
        prompt += "- Graph exploration progress may be tracked as tasks\n"

    prompt += f"""
### Graph Structure

- Nodes represent reasoning states/insights
- Edges connect nodes (dependency, aggregation, refinement, reference, merge)
- Not limited to trees - can have cross-links and cycles
- Aggregation combines multiple nodes into one
- Refinement creates improved versions

### Edge Types

- `dependency`: source depends on target
- `aggregation`: target combines source nodes
- `refinement`: target improves source
- `reference`: source references target
- `merge`: nodes are merged

### Key Principles

- **Interconnected Exploration**: Explore relationships between reasoning states
- **Path Finding**: Find optimal paths through the reasoning graph
- **Node Evaluation**: Use evaluation to guide exploration
- **Graph Building**: Build graph structure that captures reasoning dependencies
- **Aggregation**: Combine complementary insights from multiple nodes
- **Refinement**: Create improved versions of nodes

### Graph of Thoughts Process

1. **Read**: Call `{prefix}read_graph` to see current state
   - Review graph structure with nodes and edges
   - Check node evaluations
   - Understand current reasoning paths
2. **Create**: Create nodes and edges using `{prefix}create_node` and `{prefix}create_edge`
   - Create initial nodes for different aspects/perspectives
   - Connect related nodes with edges (use appropriate edge types)
   - Build graph structure that captures reasoning dependencies
3. **Evaluate**: Evaluate nodes using `{prefix}evaluate_node`
   - Assign 0-100 scores based on promise
   - Guide exploration toward promising nodes
4. **Aggregate**: Combine insights using `{prefix}aggregate_nodes`
   - Combine complementary nodes into aggregated insights
5. **Refine**: Improve nodes using `{prefix}refine_node`
   - Create improved versions of nodes
6. **Prune**: Remove dead ends using `{prefix}prune_node`
   - Mark nodes that are not useful
7. **Find Path**: Find best path using `{prefix}find_path`
   - Identify optimal sequence through the graph
   - Use node evaluations to guide path selection
8. **Mark Solutions**: Mark final solution nodes with is_solution=true

**IMPORTANT**: Always call `{prefix}read_graph` before modifying the graph.
"""

    # Add dynamic storage content if present
    if current_state_section:
        tool_name_mapping = build_tool_name_mapping(current_state_section, prefix)
        current_state_section = update_prompt_tool_names(current_state_section, tool_name_mapping)
        prompt += current_state_section

    # Update tool names in the main prompt
    tool_name_mapping = build_tool_name_mapping(prompt, prefix)
    prompt = update_prompt_tool_names(prompt, tool_name_mapping)

    return prompt


def generate_mcts_combination_prompt(
    toolset: AbstractToolset[Any],
    storage: Any | None,
    other_toolsets: list[AbstractToolset[Any]],
    position: int,
    prefix_map: dict[str, str] | None,
    workflow_template: WorkflowTemplate | None,
) -> str:
    """Generate combination-specific prompt for MCTS toolset."""
    toolset_id = toolset.id if hasattr(toolset, "id") else "mcts"
    prefix = prefix_map.get(toolset_id, "mcts_") if prefix_map else "mcts_"

    other_types = [identify_toolset_type(t) for t in other_toolsets]
    prev_types = [identify_toolset_type(t) for i, t in enumerate(other_toolsets) if i < position]
    next_types = [identify_toolset_type(t) for i, t in enumerate(other_toolsets) if i > position]

    # Get base prompt WITH storage-based dynamic content
    base_prompt = get_mcts_system_prompt(storage)

    # Extract "Current State" section if present
    current_state_section = ""
    if "## Current State" in base_prompt:
        current_state_section = "\n" + base_prompt.split("## Current State", 1)[1]

    prompt = f"""## Monte Carlo Tree Search (Stage {position + 1} of {len(other_toolsets) + 1})

You have access to tools for MCTS-based reasoning:
- `{prefix}read_mcts`: Review current tree state
- `{prefix}select_node`: Select promising node using UCB1
- `{prefix}expand_node`: Expand node with possible children
- `{prefix}simulate`: Run simulation from a node
- `{prefix}backpropagate`: Update statistics from simulation
- `{prefix}get_best_action`: Get best action based on visits

### When to Use MCTS

Use these tools in these scenarios:
1. Decision-making with many possible actions
2. Game-like problems with win/loss outcomes
3. Problems requiring exploration vs exploitation balance
4. Sequential decision problems
5. Simulations can provide reward signals

**In this workflow context:**
- Explore decision space systematically through simulation
- Your best action will feed into subsequent refinement stages
- Use debate positions or other inputs to seed initial decisions

### Your Role in This Workflow

You are the **decision exploration** stage. Explore decision space to find optimal actions.

### Integration with Other Stages

**Input from Previous Stages:**
"""
    if "persona_debate" in prev_types:
        prompt += "- Use debate positions to seed MCTS exploration\n"
    if "persona" in prev_types:
        prompt += "- Use synthesized persona perspectives to inform decisions\n"

    prompt += f"""
**Output to Next Stages:**
"""
    if "reflection" in next_types:
        prompt += "- Best action from MCTS will be refined by reflection\n"
    if "self_refine" in next_types:
        prompt += "- Best action will be refined through iterative improvement\n"
    if "todo" in next_types:
        prompt += "- Decision exploration progress may be tracked as tasks\n"

    prompt += f"""
### MCTS Four Phases (Per Iteration)

1. **Selection**: Pick promising node using UCB1 formula
2. **Expansion**: Add children to selected node
3. **Simulation**: Evaluate with reward (0-1)
4. **Backpropagation**: Update path statistics

### UCB1 Formula

UCB1 = win_rate + c × √(ln(parent_visits) / visits)

- `win_rate`: wins/visits (exploitation)
- `c`: exploration constant (default √2 ≈ 1.414)
- Higher c = more exploration

### Rewards

- Use 0.0-1.0 scale
- 1.0 = best outcome (win)
- 0.0 = worst outcome (loss)
- Intermediate values for partial success

### Key Principles

- **Exploration vs Exploitation**: Balance exploring new actions vs exploiting known good actions
- **Simulation-Based Evaluation**: Use simulations to evaluate decision outcomes
- **Statistical Backpropagation**: Update node statistics based on simulation results
- **Iterative Refinement**: Multiple iterations improve decision quality

### MCTS Process

1. **Read**: Call `{prefix}read_mcts` to see current state
   - Review tree structure with decision nodes
   - Check node values, visit counts, and win rates
   - Understand current exploration state
2. **Iterate**: For each iteration:
   a. **Select**: Use `{prefix}select_node` to find promising leaf using UCB1
   b. **Expand**: Use `{prefix}expand_node` to add possible actions as children
   c. **Simulate**: Use `{prefix}simulate` to evaluate with reward (0-1)
   d. **Backpropagate**: Use `{prefix}backpropagate` to update statistics along path
3. **Get Best**: After iterations, use `{prefix}get_best_action` for final decision
   - Identify best action from root based on visit counts
   - Select action with highest visit count (most explored)

**IMPORTANT**: Always call `{prefix}read_mcts` before modifying the tree.
"""

    # Add dynamic storage content if present
    if current_state_section:
        tool_name_mapping = build_tool_name_mapping(current_state_section, prefix)
        current_state_section = update_prompt_tool_names(current_state_section, tool_name_mapping)
        prompt += current_state_section

    # Update tool names in the main prompt
    tool_name_mapping = build_tool_name_mapping(prompt, prefix)
    prompt = update_prompt_tool_names(prompt, tool_name_mapping)

    return prompt


def generate_beam_combination_prompt(
    toolset: AbstractToolset[Any],
    storage: Any | None,
    other_toolsets: list[AbstractToolset[Any]],
    position: int,
    prefix_map: dict[str, str] | None,
    workflow_template: WorkflowTemplate | None,
) -> str:
    """Generate combination-specific prompt for Beam Search toolset."""
    toolset_id = toolset.id if hasattr(toolset, "id") else "beam"
    prefix = prefix_map.get(toolset_id, "beam_") if prefix_map else "beam_"

    other_types = [identify_toolset_type(t) for t in other_toolsets]
    prev_types = [identify_toolset_type(t) for i, t in enumerate(other_toolsets) if i < position]
    next_types = [identify_toolset_type(t) for i, t in enumerate(other_toolsets) if i > position]

    # Get base prompt WITH storage-based dynamic content
    base_prompt = get_beam_system_prompt(storage)

    # Extract "Current State" section if present
    current_state_section = ""
    if "## Current State" in base_prompt:
        current_state_section = "\n" + base_prompt.split("## Current State", 1)[1]

    prompt = f"""## Beam Search (Stage {position + 1} of {len(other_toolsets) + 1})

You have access to tools for beam search exploration:
- `{prefix}read_beam`: Review current beam state and candidates
- `{prefix}create_candidate`: Create initial candidates
- `{prefix}expand_candidate`: Generate next steps from a candidate
- `{prefix}score_candidate`: Assign quality score (0-100)
- `{prefix}prune_beam`: Keep only top-k candidates at a step
- `{prefix}get_best_path`: Find highest-scoring path to terminal

### When to Use Beam Search

Use these tools in these scenarios:
1. Problems requiring simultaneous multi-path exploration
2. Tasks needing systematic exploration with pruning
3. Balancing exploration vs exploitation
4. Problems with clear scoring/evaluation functions
5. When breadth-first is too expensive

**In this workflow context:**
- Explore top-K solution candidates systematically
- Your best candidate will feed into subsequent refinement stages
- Use scoring to efficiently narrow down to promising candidates

### Your Role in This Workflow

You are the **beam search** stage. Explore top-K candidates efficiently.

### Integration with Other Stages

**Input from Previous Stages:**
"""
    if "search" in prev_types:
        prompt += "- Use search results to seed initial candidates\n"
    if "self_ask" in prev_types:
        prompt += "- Use decomposed questions to inform candidate generation\n"

    prompt += f"""
**Output to Next Stages:**
"""
    if "reflection" in next_types:
        prompt += "- Best candidate will be refined by reflection\n"
    if "self_refine" in next_types:
        prompt += "- Best candidate will be refined through iterative improvement\n"
    if "todo" in next_types:
        prompt += "- Candidate exploration progress may be tracked as tasks\n"

    prompt += f"""
### Key Parameters

- **Beam width (k)**: Candidates to keep per step
  - k=1: greedy search (fast, may miss optimal)
  - k=3-10: typical for practical applications
- **Scoring**: 0-100, higher is better
- **Terminal**: Mark solution candidates with is_terminal=true

### Key Principles

- **Top-K Exploration**: Maintain a beam of K most promising candidates
- **Scoring-Based Selection**: Use scores to select best candidates for expansion
- **Efficient Exploration**: Focus computational resources on promising paths
- **Iterative Refinement**: Expand and score candidates iteratively
- **Pruning Strategy**: Keep only top-k candidates at each step

### Beam Search Process

1. **Read**: Call `{prefix}read_beam` to see current state
   - Review current beam of candidates
   - Check candidate scores and steps
   - Understand current exploration state
2. **Initialize**: Create initial candidates using `{prefix}create_candidate`
   - Generate initial candidates (step 0)
   - Seed beam with promising starting points
3. **Expand**: Expand candidates using `{prefix}expand_candidate`
   - Generate possible next steps from beam candidates
   - Explore variations and alternatives
4. **Score**: Score candidates using `{prefix}score_candidate`
   - Assign quality scores (0-100)
   - Evaluate candidate quality systematically
5. **Prune**: Prune beam using `{prefix}prune_beam`
   - Keep only top-k highest-scoring candidates
   - Maintain beam width for next iteration
6. **Repeat**: Continue until terminal states or depth limit
   - Mark solution candidates with is_terminal=true
   - Continue expansion and pruning
7. **Get Best**: Use `{prefix}get_best_path` for final result
   - Find highest-scoring path to terminal
   - Select best candidate from beam

**IMPORTANT**: Always call `{prefix}read_beam` before modifying the beam.
"""

    # Add dynamic storage content if present
    if current_state_section:
        tool_name_mapping = build_tool_name_mapping(current_state_section, prefix)
        current_state_section = update_prompt_tool_names(current_state_section, tool_name_mapping)
        prompt += current_state_section

    # Update tool names in the main prompt
    tool_name_mapping = build_tool_name_mapping(prompt, prefix)
    prompt = update_prompt_tool_names(prompt, tool_name_mapping)

    return prompt


def generate_persona_combination_prompt(
    toolset: AbstractToolset[Any],
    storage: Any | None,
    other_toolsets: list[AbstractToolset[Any]],
    position: int,
    prefix_map: dict[str, str] | None,
    workflow_template: WorkflowTemplate | None,
) -> str:
    """Generate combination-specific prompt for Multi-Persona Analysis toolset."""
    toolset_id = toolset.id if hasattr(toolset, "id") else "persona"
    prefix = prefix_map.get(toolset_id, "persona_") if prefix_map else "persona_"

    other_types = [identify_toolset_type(t) for t in other_toolsets]
    prev_types = [identify_toolset_type(t) for i, t in enumerate(other_toolsets) if i < position]
    next_types = [identify_toolset_type(t) for i, t in enumerate(other_toolsets) if i > position]

    # Get base prompt WITH storage-based dynamic content
    base_prompt = get_persona_system_prompt(storage)

    # Extract "Current Persona Session" section if present
    current_state_section = ""
    if "## Current Persona Session" in base_prompt:
        current_state_section = "\n" + base_prompt.split("## Current Persona Session", 1)[1]

    prompt = f"""## Multi-Persona Analysis (Stage {position + 1} of {len(other_toolsets) + 1})

You have access to tools for managing multi-persona analysis sessions:
- `{prefix}read_personas`: Read the current session state and all personas/responses
- `{prefix}initiate_persona_session`: Start a new persona analysis session
- `{prefix}create_persona`: Create a new persona with specific expertise
- `{prefix}add_persona_response`: Add a response from a persona
- `{prefix}synthesize`: Synthesize all persona responses into a comprehensive solution

**CRITICAL**: You MUST actively use these tools to participate in persona analysis. Do NOT just answer directly.
Instead, use the tools to create personas, gather their perspectives, and synthesize insights.

### When to Use Multi-Persona Analysis

Use these tools in these scenarios:
1. Complex problems requiring diverse viewpoints
2. Tasks benefiting from multiple expert perspectives
3. Situations where synthesis of viewpoints is valuable
4. Problems requiring comprehensive analysis from different angles
5. Tasks where persona-based reasoning adds value

**In this workflow context:**
- Gather diverse perspectives to inform solution exploration
- Your synthesized perspectives will feed into subsequent stages
- Use multiple personas to cover different aspects of the problem

### Your Role in This Workflow

You are the **perspective gathering** stage. Gather diverse viewpoints to inform decision-making.

### Integration with Other Stages

**Input from Previous Stages:**
"""
    if "search" in prev_types:
        prompt += "- Use search results to inform persona perspectives\n"

    prompt += f"""
**Output to Next Stages:**
"""
    if "got" in next_types:
        prompt += "- Synthesized perspectives will seed graph exploration\n"
    if "reflection" in next_types:
        prompt += "- Synthesized perspectives will be refined by reflection\n"
    if "tot" in next_types:
        prompt += "- Synthesized perspectives will seed tree exploration\n"
    if "todo" in next_types:
        prompt += "- Persona analysis progress may be tracked as tasks\n"

    prompt += f"""
### Key Principles

- **Diverse Perspectives**: Create personas with different expertise and viewpoints
- **Structured Analysis**: Use personas to systematically explore problem aspects
- **Synthesis**: Combine perspectives into coherent insights
- **Iterative Refinement**: Gather multiple rounds of responses if needed
- **Active Tool Usage**: Use tools to create personas and gather responses, don't answer directly

### Persona Types

- **Expert Personas**: Domain specialists (e.g., Data Scientist, Security Expert, UX Designer)
- **Thinking Style Personas**: Different reasoning approaches (e.g., Analytical, Creative, Pragmatic)
- **Stakeholder Personas**: Interested parties (e.g., Employee, Manager, Executive)

### Multi-Persona Process

1. **Read**: Call `{prefix}read_personas` to see current state
   - Review the current session state and round
   - See existing personas and responses
   - Understand the process type
   - Know which personas have responded
2. **Initiate**: Start session using `{prefix}initiate_persona_session` (if no session exists)
   - Define the problem to analyze
   - Set process type (sequential, interactive, devils_advocate)
   - Set max rounds
3. **Create**: Create personas using `{prefix}create_persona`
   - Create 3-6 personas with different expertise areas
   - Choose appropriate persona_type (expert, thinking_style, stakeholder)
   - Provide detailed descriptions of their background and perspective
   - List specific expertise areas
4. **Gather**: Collect responses using `{prefix}add_persona_response`
   - Get responses from each persona
   - For interactive: reference other responses using references field
   - For devils_advocate: skeptic persona should challenge primary persona's solution
   - Continue dialogue across rounds if needed
5. **Synthesize**: Combine perspectives using `{prefix}synthesize`
   - **STOP** and synthesize when:
     - All personas have provided initial responses (sequential)
     - Sufficient dialogue has occurred (interactive)
     - Solution has been refined through challenge (devils_advocate)
     - Max rounds reached
   - Integrate insights from all personas
   - Identify commonalities and conflicts
   - Resolve tensions between perspectives
   - Provide comprehensive solution addressing all viewpoints

**IMPORTANT**: Always call `{prefix}read_personas` before adding responses or synthesizing.
**STOPPING CONDITIONS**: The session MUST end when max rounds are reached or synthesis is provided.
"""

    # Add dynamic storage content if present
    if current_state_section:
        tool_name_mapping = build_tool_name_mapping(current_state_section, prefix)
        current_state_section = update_prompt_tool_names(current_state_section, tool_name_mapping)
        prompt += current_state_section

    # Update tool names in the main prompt
    tool_name_mapping = build_tool_name_mapping(prompt, prefix)
    prompt = update_prompt_tool_names(prompt, tool_name_mapping)

    return prompt


def generate_persona_debate_combination_prompt(
    toolset: AbstractToolset[Any],
    storage: Any | None,
    other_toolsets: list[AbstractToolset[Any]],
    position: int,
    prefix_map: dict[str, str] | None,
    workflow_template: WorkflowTemplate | None,
) -> str:
    """Generate combination-specific prompt for Multi-Persona Debate toolset."""
    toolset_id = toolset.id if hasattr(toolset, "id") else "persona_debate"
    prefix = prefix_map.get(toolset_id, "persona_debate_") if prefix_map else "persona_debate_"

    other_types = [identify_toolset_type(t) for t in other_toolsets]
    prev_types = [identify_toolset_type(t) for i, t in enumerate(other_toolsets) if i < position]
    next_types = [identify_toolset_type(t) for i, t in enumerate(other_toolsets) if i > position]

    # Get standalone prompt for reference (persona_debate doesn't use storage)
    base_prompt = get_persona_debate_system_prompt()

    prompt = f"""## Multi-Persona Debate (Stage {position + 1} of {len(other_toolsets) + 1})

You have access to tools for structured debate between personas:
- `{prefix}read_debate`: Read current debate state
- `{prefix}initiate_debate`: Start a new debate session
- `{prefix}create_persona`: Create a persona with a position
- `{prefix}add_position`: Add a position to the debate
- `{prefix}add_critique`: Add critique from one persona to another
- `{prefix}add_agreement`: Record agreement between personas
- `{prefix}resolve_debate`: Resolve the debate with final positions

### When to Use Multi-Persona Debate

Use these tools in these scenarios:
1. Complex decisions requiring structured argumentation
2. Problems where multiple valid positions exist
3. Situations where critique and counter-argument improve analysis
4. Tasks requiring exploration of trade-offs and alternatives
5. Problems where structured debate leads to better decisions

**In this workflow context:**
- Engage in structured debate to explore different positions
- Your resolved debate positions will feed into subsequent exploration stages
- Use debate to systematically evaluate alternatives

### Your Role in This Workflow

You are the **debate** stage. Engage in structured debate to explore different positions.

### Integration with Other Stages

**Input from Previous Stages:**
"""
    if "search" in prev_types:
        prompt += "- Use search results to inform debate positions\n"

    prompt += f"""
**Output to Next Stages:**
"""
    if "mcts" in next_types:
        prompt += "- Debate positions will seed MCTS exploration\n"
    if "reflection" in next_types:
        prompt += "- Resolved debate will be refined by reflection\n"
    if "self_refine" in next_types:
        prompt += "- Resolved debate will be refined through iterative improvement\n"
    if "todo" in next_types:
        prompt += "- Debate progress may be tracked as tasks\n"

    prompt += f"""
### Key Principles

- **Structured Argumentation**: Use positions, critiques, and agreements systematically
- **Multiple Perspectives**: Create personas representing different viewpoints
- **Critical Analysis**: Use critiques to identify weaknesses in positions
- **Agreement Tracking**: Record where personas agree to find common ground
- **Resolution**: Synthesize debate into final positions

### Multi-Persona Debate Process

1. **Read**: Call `{prefix}read_debate` to see current state
   - Review debate session and round
   - See existing personas and their positions
   - Check critiques and agreements
   - Understand debate progress
2. **Initiate**: Start debate using `{prefix}initiate_debate`
   - Define the question or decision to debate
   - Set max rounds for the debate
3. **Create**: Create personas with positions using `{prefix}create_persona` and `{prefix}add_position`
   - Create 2-4 personas representing different viewpoints
   - Each persona should have a distinct position on the question
   - Positions should represent valid alternatives
4. **Debate**: Add critiques and agreements using `{prefix}add_critique` and `{prefix}add_agreement`
   - Add critiques from one persona to another's position
   - Identify weaknesses and counter-arguments
   - Record agreements where personas find common ground
   - Continue debate across multiple rounds
5. **Resolve**: Resolve debate using `{prefix}resolve_debate`
   - Synthesize all positions, critiques, and agreements
   - Provide final positions reflecting the debate outcome
   - Identify key trade-offs and considerations
"""

    return prompt


def generate_combination_prompt_for_toolset(
    toolset_type: str,
    toolset: AbstractToolset[Any],
    storage: Any | None,
    other_toolsets: list[AbstractToolset[Any]],
    toolset_order: int,
    prefix_map: dict[str, str] | None,
    workflow_template: WorkflowTemplate | None,
) -> str:
    """Generate a combination-specific prompt for a single toolset.

    Args:
        toolset_type: Type identifier (e.g., "search", "self_ask")
        toolset: The toolset to generate prompt for
        storage: Optional storage for dynamic prompts
        other_toolsets: Other toolsets in the combination
        toolset_order: Order of toolset (index)
        prefix_map: Mapping of toolset IDs to prefixes
        workflow_template: Optional workflow template

    Returns:
        Combination-specific prompt for this toolset
    """
    # Get the combination prompt generator
    if toolset_type in TOOLSET_COMBINATION_PROMPT_GENERATORS:
        generator = TOOLSET_COMBINATION_PROMPT_GENERATORS[toolset_type]
        return generator(
            toolset=toolset,
            storage=storage,
            other_toolsets=other_toolsets,
            position=toolset_order,
            prefix_map=prefix_map,
            workflow_template=workflow_template,
        )
    else:
        # Fallback to standalone prompt if no combination generator exists
        getter = TOOLSET_SYSTEM_PROMPT_GETTERS.get(toolset_type)
        if getter:
            prompt = getter(storage)
            # Update tool names if prefixing was applied
            toolset_id = toolset.id if hasattr(toolset, "id") else ""
            if prefix_map and toolset_id in prefix_map:
                prefix = prefix_map[toolset_id]
                tool_name_mapping = build_tool_name_mapping(prompt, prefix)
                prompt = update_prompt_tool_names(prompt, tool_name_mapping)
            return prompt
        return ""


def combine_system_prompts(
    toolsets: list[AbstractToolset[Any]],
    storages: dict[str, Any] | None = None,
    prefix_map: dict[str, str] | None = None,
    workflow_template: WorkflowTemplate | None = None,
    use_combination_prompts: bool = True,
) -> str:
    """Combine system prompts from multiple toolsets.

    Args:
        toolsets: List of toolsets to combine prompts from
        storages: Optional mapping of toolset IDs to storage objects
        prefix_map: Optional mapping of toolset IDs to prefixes
        workflow_template: Optional workflow template for context
        use_combination_prompts: If True, use combination-specific prompts

    Returns:
        Combined system prompt with all toolset instructions
    """
    if storages is None:
        storages = {}

    prompt_sections = []

    for idx, toolset in enumerate(toolsets):
        toolset_id = toolset.id if hasattr(toolset, "id") else ""
        toolset_type = identify_toolset_type(toolset)
        storage = storages.get(toolset_id)

        if use_combination_prompts and len(toolsets) > 1:
            # Generate combination-specific prompt
            prompt = generate_combination_prompt_for_toolset(
                toolset_type=toolset_type,
                toolset=toolset,
                storage=storage,
                other_toolsets=[t for i, t in enumerate(toolsets) if i != idx],
                toolset_order=idx,
                prefix_map=prefix_map,
                workflow_template=workflow_template,
            )
        else:
            # Use standalone prompt
            if toolset_type in TOOLSET_SYSTEM_PROMPT_GETTERS:
                getter = TOOLSET_SYSTEM_PROMPT_GETTERS[toolset_type]
                prompt = getter(storage)

                # Update tool names if prefixing was applied
                if prefix_map and toolset_id in prefix_map:
                    prefix = prefix_map[toolset_id]
                    tool_name_mapping = build_tool_name_mapping(prompt, prefix)
                    prompt = update_prompt_tool_names(prompt, tool_name_mapping)
            else:
                prompt = ""

        if prompt:
            prompt_sections.append(prompt)

    # Combine prompts with separators
    combined = "\n\n".join(prompt_sections)

    # Add workflow-specific instructions if provided
    if workflow_template:
        workflow_instructions = generate_workflow_instructions(workflow_template, prefix_map)
        combined = f"{workflow_instructions}\n\n{combined}"

    return combined
