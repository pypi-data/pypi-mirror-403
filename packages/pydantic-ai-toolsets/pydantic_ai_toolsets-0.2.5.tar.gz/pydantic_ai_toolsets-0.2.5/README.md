# Pydantic AI Toolsets

A comprehensive collection of reasoning, reflection, and multi-agent toolsets for pydantic-ai agents.

## Overview

This package provides a rich set of toolsets that can be used individually or combined to create powerful multi-stage workflows:

- **Reasoning Toolsets**: Chain of Thought, Tree of Thought, Graph of Thought, Beam Search, Monte Carlo Tree Search
- **Reflection Toolsets**: Reflection, Self-Refine, Self-Ask
- **Multi-Agent Toolsets**: Multi-Persona Analysis, Multi-Persona Debate
- **Utility Toolsets**: Search, Todo
- **Meta-Orchestrator**: Workflow coordination and multi-toolset management

### Key Features

- ✅ **Zero Breaking Changes**: All toolsets work standalone or combined
- ✅ **Automatic Collision Resolution**: Dynamic runtime aliasing prevents function name conflicts
- ✅ **Workflow Templates**: Pre-built combinations for common scenarios (Research Assistant, Creative Problem Solver, Strategic Decision Maker, Code Architect)
- ✅ **Intelligent Prompt Combination**: System prompts adapt when toolsets are combined
- ✅ **Cross-Toolset Linking**: Create explicit relationships between outputs from different toolsets
- ✅ **Unified State Management**: Access state across all active toolsets
- ✅ **Usage Tracking**: Built-in metrics for monitoring token usage and performance

### Quick Start

```python
from pydantic_ai import Agent
from pydantic_ai_toolsets import create_cot_toolset, CoTStorage

storage = CoTStorage()
agent = Agent("openai:gpt-4", toolsets=[create_cot_toolset(storage)])
result = await agent.run("Solve this problem step by step")
```

For combining toolsets, see [Best Practices for Combining Toolsets](#best-practices-for-combining-toolsets).

## Table of Contents

- [Reasoning & Thinking Toolsets](#reasoning--thinking-toolsets)
  - [Reasoning Toolsets Comparison](#reasoning-toolsets-comparison)
- [Reflection & Refinement Toolsets](#reflection--refinement-toolsets)
  - [Reflection Toolsets Comparison](#reflection-toolsets-comparison)
- [Multi-Agent Toolsets](#multi-agent-toolsets)
  - [Multi-Agent Toolsets Comparison](#multi-agent-toolsets-comparison)
- [Utility Toolsets](#utility-toolsets)
- [Combining Toolsets](#combining-toolsets)
  - [Three Ways to Combine Toolsets](#three-ways-to-combine-toolsets)
  - [Workflow Templates](#workflow-templates)
  - [Best Practices for Combining Toolsets](#best-practices-for-combining-toolsets)
  - [Combination Examples](#combination-examples)
- [Meta-Orchestrator](#meta-orchestrator)
- [Running Evaluations](#running-evaluations)

---

## Reasoning & Thinking Toolsets

### Chain of Thought (CoT)

**What it does:** Enables agents to document and explore their reasoning process step-by-step. Agents can write sequential thoughts, revise previous reasoning, and branch into alternative paths.

**Perfect for:**
- Complex problems requiring multi-step reasoning
- Planning and design tasks that may need revision
- Analysis where understanding evolves over time
- Multi-step solutions needing context tracking
- Problems with uncertainty requiring exploration
- Hypothesis generation and verification

**Key Features:**
- Sequential thought tracking with revision support
- Branching for exploring alternative reasoning paths
- Thought metadata (revisions, branches, completion status)
- Flexible thought management with dynamic total estimates

---

### Tree of Thought (ToT)

**What it does:** Allows agents to explore multiple reasoning paths simultaneously in a tree structure. Agents create nodes for different approaches, evaluate branches for promise, prune dead ends, and merge insights from multiple paths.

**Perfect for:**
- Complex problems with multiple valid approaches
- Problems requiring exploration of alternatives
- Situations needing backtracking from dead ends
- Tasks where combining insights from different paths is valuable
- Problems where evaluation of paths is important

**Key Features:**
- Tree structure with nodes and branches
- Branch evaluation with scores and recommendations
- Pruning mechanism for dead ends
- Insight merging from multiple branches
- Solution node marking

---

### Graph of Thought (GoT)

**What it does:** Provides graph-based reasoning where nodes represent reasoning states and edges connect them with various relationships (dependency, aggregation, refinement, reference, merge). More flexible than trees, allowing cross-links and cycles.

**Perfect for:**
- Complex problems with interconnected sub-problems
- Tasks requiring synthesis from multiple perspectives
- Iterative refinement of solutions
- Problems with non-linear dependencies
- Building on partial solutions

**Key Features:**
- Directed graph structure (not limited to trees)
- Multiple edge types (dependency, aggregation, refinement, reference, merge)
- Node evaluation and scoring
- Node aggregation and refinement
- Path finding between nodes

---

### Beam Search

**What it does:** Implements beam search exploration, maintaining a "beam" of top-k candidates at each step. Agents expand candidates, score them, and prune to keep only the best, balancing exploration and exploitation.

**Perfect for:**
- Problems requiring simultaneous multi-path exploration
- Tasks needing systematic exploration with pruning
- Balancing exploration vs exploitation
- Problems with clear scoring/evaluation functions
- When breadth-first search is too expensive

**Key Features:**
- Beam width control (k candidates per step)
- Candidate expansion and scoring
- Pruning to top-k at each step
- Path reconstruction from initial to terminal candidates
- Terminal state marking

---

### Monte Carlo Tree Search (MCTS)

**What it does:** Implements Monte Carlo Tree Search for decision-making with exploration-exploitation balance. Uses UCB1 formula to select promising nodes, expands them, simulates outcomes, and backpropagates statistics.

**Perfect for:**
- Decision-making with many possible actions
- Game-like problems with win/loss outcomes
- Problems requiring exploration vs exploitation balance
- Sequential decision problems
- Situations where simulations can provide reward signals

**Key Features:**
- Four-phase MCTS process (selection, expansion, simulation, backpropagation)
- UCB1 formula for node selection
- Reward-based evaluation (0.0-1.0 scale)
- Visit and win statistics tracking
- Best action selection based on visit counts

---

### Reasoning Toolsets Comparison

| Feature | Chain of Thought | Tree of Thought | Graph of Thought | Beam Search | MCTS |
|---------|------------------|-----------------|------------------|-------------|------|
| **Structure** | Sequential chain | Tree (hierarchical) | Graph (flexible) | Beam (top-k per step) | Tree (with statistics) |
| **Path Exploration** | Single path with branches | Multiple paths simultaneously | Multiple paths with cross-links | Top-k paths per step | Single path per iteration |
| **Evaluation** | None (implicit) | Branch scoring (0-100) | Node scoring (0-100) | Candidate scoring (0-100) | UCB1 + simulation rewards |
| **Pruning** | Manual revision | Branch pruning | Node pruning | Top-k pruning per step | Implicit (UCB1 selection) |
| **Merging** | Branch merging | Branch merging | Node aggregation | Path reconstruction | N/A |
| **Best For** | Step-by-step reasoning | Multiple approaches | Interconnected problems | Systematic exploration | Decision-making with rewards |
| **Complexity** | Low | Medium | High | Medium | High |
| **Use Case** | Planning, analysis | Problem solving | Complex synthesis | Search problems | Game-like decisions |

---

## Reflection & Refinement Toolsets

### Reflection

**What it does:** Enables iterative output improvement through critical analysis. Agents create initial outputs, critique them systematically, and refine them based on identified problems. Supports multiple refinement cycles.

**Perfect for:**
- Tasks requiring high-quality, polished outputs
- Problems where initial solutions may have flaws
- Situations where iterative improvement is valuable
- Tasks where structured critique helps identify issues
- Problems where multiple refinement cycles improve results

**Key Features:**
- Structured critique framework (problems, strengths, suggestions)
- Refinement cycles with parent-child relationships
- Quality score tracking
- Final output marking
- Best output selection

---

### Self-Refine

**What it does:** Provides structured feedback-based refinement with support for quality thresholds and iteration limits. Agents generate outputs, provide structured feedback (additive, subtractive, transformative, corrective), and refine iteratively until quality thresholds are met.

**Perfect for:**
- Tasks requiring high-quality, polished outputs
- Problems where initial solutions may have flaws
- Situations where iterative improvement is valuable
- Tasks where structured feedback helps identify issues
- Problems where multiple refinement cycles improve results
- When you need to meet specific quality thresholds

**Key Features:**
- Structured feedback types (additive, subtractive, transformative, corrective)
- Feedback dimensions (factuality, coherence, completeness, style)
- Priority-weighted feedback
- Quality threshold support
- Iteration limit control
- Quality score tracking

---

### Self-Ask

**What it does:** Decomposes complex questions into simpler sub-questions in a hierarchical structure. Agents ask main questions, generate sub-questions at multiple depth levels, answer them sequentially or in parallel, and compose final answers from sub-question answers.

**Perfect for:**
- Complex questions requiring multi-hop reasoning
- Questions that need to be broken down into simpler parts
- Problems where intermediate answers build toward a final answer
- Questions requiring information gathering from multiple sources
- Situations where explicit decomposition makes reasoning transparent

**Key Features:**
- Hierarchical question decomposition (max depth 3)
- Question tree structure with parent-child relationships
- Sequential and parallel question answering
- Answer composition from sub-questions
- Confidence scoring for answers
- Follow-up question tracking

---

### Reflection Toolsets Comparison

| Feature | Reflection | Self-Refine | Self-Ask |
|---------|------------|------------|----------|
| **Primary Focus** | Output improvement | Output improvement with thresholds | Question decomposition |
| **Process** | Critique → Refine cycles | Feedback → Refine cycles | Question → Answer → Compose |
| **Feedback Structure** | Problems, strengths, suggestions | Types (additive/subtractive/transformative/corrective) + dimensions | Question-answer pairs |
| **Quality Control** | Quality scores (optional) | Quality thresholds + iteration limits | Confidence scores (optional) |
| **Iteration Control** | Manual (mark as final) | Automatic (threshold/limit based) | Depth limit (max 3) |
| **Output Tracking** | Refinement cycles | Refinement iterations | Question-answer tree |
| **Best For** | General output improvement | Quality-gated refinement | Complex question answering |
| **Use Case** | Writing, analysis | Polished outputs | Multi-hop reasoning |
| **Stopping Condition** | Manual final marking | Threshold met or limit reached | All questions answered |

---

## Multi-Agent Toolsets

### Multi-Persona Analysis

**What it does:** Enables analysis from multiple distinct personas or viewpoints WITHOUT debate structure. Personas provide independent analysis, engage in interactive dialogue, or use devil's advocate patterns. Results are synthesized into comprehensive solutions. This is NOT a debate toolset - it's for collaborative analysis.

**Perfect for:**
- Complex problems requiring diverse expertise
- Decisions needing multiple stakeholder perspectives
- Problems where different thinking styles improve outcomes
- Situations where role-playing different experts is valuable
- Tasks requiring comprehensive analysis from multiple angles

**Key Features:**
- Persona creation (expert, thinking_style, stakeholder)
- Process types (sequential, interactive, devil's advocate)
- Persona response tracking
- Synthesis of diverse perspectives
- Round-based interaction management
- No adversarial structure (collaborative analysis)

---

### Multi-Persona Debate

**What it does:** Enables structured debates between multiple personas with distinct expertise and viewpoints. Personas can propose positions, critique each other, agree with positions (coalition-building), and defend their arguments. Supports orchestration of multi-persona interactions.

**Perfect for:**
- Complex decisions requiring diverse expert perspectives
- Problems where multiple viewpoints need structured argumentation
- Situations where personas can both agree and disagree based on logic
- Tasks where coalition-building and consensus formation are valuable
- Problems requiring evidence-based evaluation from different experts

**Key Features:**
- Persona creation with expertise and viewpoints
- Position proposal and defense
- Critique and agreement mechanisms
- Round-based debate structure
- Resolution types (synthesis, winner, consensus)
- Multi-agent orchestration support

---

### Multi-Agent Toolsets Comparison

| Feature | Multi-Persona Analysis | Multi-Persona Debate |
|---------|------------------------|---------------------|
| **Structure** | Analysis (non-debate) | Structured debate |
| **Agent Types** | Custom personas | Custom personas |
| **Interaction** | Independent or interactive | Critique, agree, defend |
| **Agreement Support** | Yes (consensus) | Yes (coalition-building) |
| **Resolution** | Synthesis only | Synthesis/Winner/Consensus |
| **Setup Complexity** | Medium (create personas) | High (create personas) |
| **Best For** | Collaborative analysis | Custom expert debates |
| **Use Case** | Comprehensive analysis | Complex multi-expert decisions |
| **Adversarial** | No (collaborative) | Optional (can agree) |
| **Process Types** | Sequential/Interactive/Devil's Advocate | Debate rounds |

---

## Utility Toolsets

### To-Do

**What it does:** Provides simple task management for agents. Agents can create, track, and update tasks with status (pending, in_progress, completed). Helps manage complex multi-step tasks.

**Perfect for:**
- Complex multi-step tasks (3+ distinct steps)
- Non-trivial tasks requiring careful planning
- User provides multiple tasks
- After receiving new instructions - capture requirements as todos
- When starting a task - mark it as in_progress BEFORE beginning work
- After completing a task - mark it as completed immediately

**Key Features:**
- Task status tracking (pending, in_progress, completed)
- Simple task list management
- Status summary and hints
- Task completion tracking

---

### Search

**What it does:** Provides web search, news search, and image search capabilities using Firecrawl, plus content extraction using Trafilatura. Agents can search the web, news articles, and images, and extract readable content from webpages and news articles.

**Perfect for:**
- Finding current information on the web
- Researching topics that require up-to-date data
- Searching for recent news articles with time filtering
- Finding images with resolution filtering
- Extracting readable content from webpages and news articles
- Gathering information from multiple sources
- Verifying facts or finding authoritative sources
- Discovering recent developments or news

**Key Features:**
- Web search with Firecrawl integration
- News search with time-based filtering (past hour/day/week/month/year or custom date range)
- Image search with resolution filtering (exact size or minimum size)
- Content extraction with Trafilatura (works with web and news results only)
- Multiple output formats (txt, markdown)
- Search result and content caching
- URL-based content extraction

**Tools:**
- `search_web`: General web search
- `search_news`: News article search with optional time filtering
- `search_images`: Image search with optional resolution filtering
- `extract_web_content`: Extract content from webpages and news articles (not supported for images)

**Example Usage:**

```python
from pydantic_ai import Agent
from pydantic_ai_toolsets import create_search_toolset, SearchStorage

storage = SearchStorage()
agent = Agent("openai:gpt-4", toolsets=[create_search_toolset(storage)])

# Web search
result = await agent.run("Search the web for information about Python async programming")

# News search with time filter (past week)
result = await agent.run("Search for news about AI developments from the past week")

# News search with custom date range
result = await agent.run("Search for news about quantum computing from December 2024")

# Image search with exact resolution (1920x1080)
result = await agent.run("Search for 1920x1080 images of sunsets")

# Image search with minimum resolution (at least 2560x1440)
result = await agent.run("Search for high-resolution images (at least 2560x1440) of mountains")

# Extract content from web or news results
result = await agent.run("Extract content from the first search result URL")
```

**Time Filter Options for News Search:**
- `PAST_HOUR`: News from the past hour
- `PAST_DAY`: News from the past 24 hours
- `PAST_WEEK`: News from the past week
- `PAST_MONTH`: News from the past month
- `PAST_YEAR`: News from the past year
- `CUSTOM`: Custom date range (requires `custom_date_min` and `custom_date_max` in MM/DD/YYYY format)

**Resolution Filtering for Image Search:**
- Use `exact_width` and `exact_height` for exact size matching (e.g., 1920x1080)
- Use `min_width` and `min_height` for minimum size filtering (e.g., at least 2560x1440)
- Resolution operators are automatically appended to the query string

---

## Combining Toolsets

### Overview

You can combine multiple toolsets to create powerful multi-stage workflows. When combining toolsets, the system automatically handles function name collisions through dynamic runtime aliasing, ensuring zero breaking changes to existing code.

### Three Ways to Combine Toolsets

There are three approaches to combining toolsets, each suited for different scenarios:

#### 1. **`create_workflow_agent()` - High-Level (Recommended for Most Cases)**

**What it does:** Creates a complete agent with workflow template, automatic toolset combination, orchestrator setup, and optimized system prompts.

**Best for:**
- ✅ Using predefined workflow templates (Research Assistant, Creative Problem Solver, etc.)
- ✅ Production systems requiring workflow tracking
- ✅ Multi-stage workflows with clear transitions
- ✅ When you want orchestrator features (unified state, cross-toolset linking, progress tracking)
- ✅ Quick setup with minimal configuration

**Example:**
```python
from pydantic_ai_toolsets import (
    RESEARCH_ASSISTANT,
    create_search_toolset,
    create_self_ask_toolset,
    create_self_refine_toolset,
    create_todo_toolset,
    SearchStorage,
    SelfAskStorage,
    SelfRefineStorage,
    TodoStorage,
    MetaOrchestratorStorage,
    create_workflow_agent,
)

storages = {
    "search": SearchStorage(),
    "self_ask": SelfAskStorage(),
    "self_refine": SelfRefineStorage(),
    "todo": TodoStorage(),
}

toolsets = [
    create_search_toolset(storages["search"], id="search"),
    create_self_ask_toolset(storages["self_ask"], id="self_ask"),
    create_self_refine_toolset(storages["self_refine"], id="self_refine"),
    create_todo_toolset(storages["todo"], id="todo"),
]

orchestrator_storage = MetaOrchestratorStorage()

agent = create_workflow_agent(
    model="openai:gpt-4",
    workflow_template=RESEARCH_ASSISTANT,
    toolsets=toolsets,
    storages=storages,
    orchestrator_storage=orchestrator_storage,
    additional_system_prompt="Always cite sources.",
)

result = await agent.run("Research quantum computing")
```

**Advantages:**
- ✅ One function call sets up everything
- ✅ Automatic orchestrator integration
- ✅ Workflow-aware system prompts
- ✅ Built-in progress tracking
- ✅ Cross-toolset linking support

**When NOT to use:**
- ❌ Simple 2-toolset combinations without workflow needs
- ❌ Custom workflows that don't fit templates
- ❌ When you need fine-grained control over agent creation

---

#### 2. **`create_combined_toolset()` - Mid-Level (Custom Workflows)**

**What it does:** Combines toolsets and generates system prompts, but you create the agent yourself. Can optionally include orchestrator.

**Best for:**
- ✅ Custom workflows that don't match predefined templates
- ✅ When you need control over agent creation
- ✅ Experimenting with novel toolset combinations
- ✅ Simple 2-3 toolset combinations
- ✅ When you want orchestrator features but custom workflow logic

**Example:**
```python
from pydantic_ai import Agent
from pydantic_ai_toolsets import (
    create_cot_toolset,
    create_reflection_toolset,
    create_meta_orchestrator_toolset,
    CoTStorage,
    ReflectionStorage,
    MetaOrchestratorStorage,
    create_combined_toolset,
)

cot_storage = CoTStorage()
reflection_storage = ReflectionStorage()
orchestrator_storage = MetaOrchestratorStorage()

cot_toolset = create_cot_toolset(cot_storage, id="cot")
reflection_toolset = create_reflection_toolset(reflection_storage, id="reflection")
orchestrator_toolset = create_meta_orchestrator_toolset(orchestrator_storage, id="orchestrator")

prefix_map = {
    "cot": "cot_",
    "reflection": "reflection_",
}

storages_map = {
    "cot": cot_storage,
    "reflection": reflection_storage,
}

# Combine toolsets
combined_toolset, combined_prompt = create_combined_toolset(
    toolsets=[cot_toolset, reflection_toolset],
    storages=storages_map,
    prefix_map=prefix_map,
    orchestrator=orchestrator_toolset,  # Optional
    auto_prefix=True,
)

# Create agent yourself
agent = Agent(
    "openai:gpt-4",
    system_prompt=combined_prompt,
    toolsets=[combined_toolset],
)

result = await agent.run("Solve this problem step by step, then refine")
```

**Advantages:**
- ✅ More control over agent configuration
- ✅ Can use custom workflow logic
- ✅ Still gets automatic prefixing and prompt combination
- ✅ Can optionally include orchestrator
- ✅ Good for custom combinations

**When NOT to use:**
- ❌ When workflow templates fit your needs (use `create_workflow_agent()` instead)
- ❌ When you need full low-level control (use `CombinedToolset` directly)

---

#### 3. **Direct `CombinedToolset` - Low-Level (Full Control)**

**What it does:** Uses pydantic-ai's `CombinedToolset` directly. You handle prefixing, prompt combination, and orchestrator setup manually.

**Best for:**
- ✅ Maximum control over every aspect
- ✅ Custom prefixing strategies
- ✅ Manual prompt combination
- ✅ Advanced use cases requiring fine-grained control
- ✅ When you're building custom combination logic

**Example:**
```python
from pydantic_ai import Agent
from pydantic_ai.toolsets import CombinedToolset
from pydantic_ai_toolsets import (
    create_cot_toolset,
    create_tot_toolset,
    CoTStorage,
    ToTStorage,
    get_cot_system_prompt,
    get_tot_system_prompt,
)

cot_storage = CoTStorage()
tot_storage = ToTStorage()

cot_toolset = create_cot_toolset(cot_storage, id="cot")
tot_toolset = create_tot_toolset(tot_storage, id="tot")

# Manual prefixing
prefixed_cot = cot_toolset.prefixed("cot_")
prefixed_tot = tot_toolset.prefixed("tot_")

# Manual combination
combined_toolset = CombinedToolset([prefixed_cot, prefixed_tot])

# Manual prompt combination
cot_prompt = get_cot_system_prompt(cot_storage)
tot_prompt = get_tot_system_prompt(tot_storage)
combined_prompt = f"{cot_prompt}\n\n{tot_prompt}"

# Create agent
agent = Agent(
    "openai:gpt-4",
    system_prompt=combined_prompt,
    toolsets=[combined_toolset],
)

result = await agent.run("Solve using both sequential and tree reasoning")
```

**Advantages:**
- ✅ Complete control over every step
- ✅ Custom prefixing logic
- ✅ Custom prompt combination
- ✅ No abstractions

**When NOT to use:**
- ❌ Most use cases (prefer higher-level methods)
- ❌ When you want automatic optimizations
- ❌ When workflow templates fit your needs

---

### Comparison Table

| Feature | `create_workflow_agent()` | `create_combined_toolset()` | `CombinedToolset` Direct |
|---------|---------------------------|----------------------------|-------------------------|
| **Ease of Use** | ⭐⭐⭐⭐⭐ Easiest | ⭐⭐⭐⭐ Easy | ⭐⭐ Requires manual setup |
| **Workflow Templates** | ✅ Built-in support | ⚠️ Optional | ❌ Manual |
| **Orchestrator** | ✅ Automatic setup | ⚠️ Optional | ❌ Manual |
| **Auto Prefixing** | ✅ Automatic | ✅ Automatic | ❌ Manual |
| **Prompt Combination** | ✅ Optimized for workflows | ✅ Automatic | ❌ Manual |
| **Agent Creation** | ✅ Included | ❌ You create it | ❌ You create it |
| **Control Level** | Low (high-level) | Medium | High (low-level) |
| **Best For** | Production workflows | Custom workflows | Advanced use cases |
| **Setup Lines** | ~15 lines | ~20 lines | ~30+ lines |

### Quick Decision Guide

**Use `create_workflow_agent()` if:**
- Your workflow matches a template (Research Assistant, Creative Problem Solver, etc.)
- You need workflow tracking and orchestrator features
- You want the easiest setup

**Use `create_combined_toolset()` if:**
- You have a custom workflow
- You want control but still need automatic prefixing/prompts
- You're combining 2-3 toolsets

**Use `CombinedToolset` directly if:**
- You need maximum control
- You're building custom combination logic
- You have advanced requirements

### Function Name Collisions

Many toolsets share common function names (e.g., `read_state`, `create_node`, `evaluate`). When combining toolsets, these collisions are automatically resolved by prefixing tool names at runtime:

- **Chain of Thought** tools become `cot_write_thoughts`, `cot_read_thoughts`, etc.
- **Tree of Thought** tools become `tot_create_node`, `tot_evaluate_branch`, etc.
- **Self-Ask** tools become `self_ask_ask_main_question`, `self_ask_answer_question`, etc.

This prefixing happens **only when toolsets are combined** - standalone toolsets keep their original function names for backward compatibility.

### Dynamic Runtime Aliasing

The aliasing system uses the official Pydantic-AI API (`AbstractToolset.prefixed()` and `CombinedToolset`) to create aliased toolsets at runtime. This means:

- ✅ **Zero breaking changes** - Original toolsets remain unchanged
- ✅ **Automatic collision detection** - Prefixes are applied only when needed
- ✅ **Transparent to agents** - System prompts are automatically updated with prefixed tool names
- ✅ **No source code modifications** - All aliasing happens at runtime

### System Prompt Combination

When toolsets are combined, their system prompts are intelligently merged:

1. **Standalone prompts** are used when a toolset is used alone
2. **Combination prompts** are generated when toolsets are part of a multi-toolset workflow
3. **Workflow instructions** are added when using predefined workflow templates
4. **Tool name updates** automatically reflect prefixed tool names in prompts

The combined prompt provides context-aware guidance, explaining:
- How each toolset fits into the overall workflow
- How to transition between toolsets
- How to link outputs from different toolsets
- The role of each toolset in the combination

### Workflow Templates

Predefined workflow templates provide ready-to-use patterns for common problem-solving scenarios:

#### Research Assistant

**Toolsets:** Search → Self-Ask → Self-Refine → Todo

**Perfect for:** Research tasks requiring information gathering, decomposition, and refinement

**Workflow:**
1. **Research Stage**: Gather information from the web using search tools
2. **Decompose Stage**: Break down complex questions into sub-questions and compose final answer
3. **Refine Stage**: Refine the output through iterative feedback cycles
4. **Track Stage**: Track completed tasks and manage workflow

**Use Case:** Researching a topic, gathering sources, breaking down complex questions, and producing polished research reports.

#### Creative Problem Solver

**Toolsets:** Multi-Persona Analysis → Graph of Thoughts → Reflection

**Perfect for:** Complex problems needing diverse perspectives and synthesis

**Workflow:**
1. **Analyze Stage**: Gather diverse perspectives using multiple personas
2. **Explore Stage**: Explore multiple reasoning paths using graph structure
3. **Reflect Stage**: Reflect on and refine the solution through critique cycles

**Use Case:** Solving complex problems that benefit from multiple expert viewpoints, exploring interconnected solution paths, and refining creative solutions.

#### Strategic Decision Maker

**Toolsets:** Multi-Persona Debate → MCTS → Reflection

**Perfect for:** High-stakes decisions requiring expert debate and exploration

**Workflow:**
1. **Debate Stage**: Engage in structured debate between multiple expert personas
2. **Explore Stage**: Explore decision space using Monte Carlo Tree Search
3. **Reflect Stage**: Reflect on and refine the decision through critique cycles

**Use Case:** Making strategic business decisions, evaluating complex options with multiple stakeholders, and exploring decision trees with uncertainty.

#### Code Architect

**Toolsets:** Self-Ask → Tree of Thoughts → Reflection → Todo

**Perfect for:** Software architecture requiring decomposition, exploration, and task tracking

**Workflow:**
1. **Decompose Stage**: Decompose architecture problem into sub-questions
2. **Explore Stage**: Explore multiple architectural approaches using tree structure
3. **Reflect Stage**: Reflect on and refine the architecture through critique cycles
4. **Track Stage**: Track architectural components and tasks

**Use Case:** Designing software architectures, exploring architectural patterns, decomposing complex systems, and tracking implementation tasks.

---

## Best Practices for Combining Toolsets

### When to Use Each Combination Method

**Use `create_workflow_agent()` (Method 1) When:**
- ✅ Your use case matches one of the predefined templates (Research Assistant, Creative Problem Solver, Strategic Decision Maker, Code Architect)
- ✅ You want structured, stage-based workflows with clear transitions
- ✅ You need workflow tracking and progress monitoring via orchestrator
- ✅ You want automatic system prompt generation optimized for combinations
- ✅ You're building production systems that benefit from proven patterns
- ✅ You need cross-toolset linking and unified state management

**Use `create_combined_toolset()` (Method 2) When:**
- ✅ You need a custom workflow that doesn't fit existing templates
- ✅ You want more control over agent creation but still need automatic prefixing/prompts
- ✅ You're experimenting with novel toolset combinations
- ✅ You're combining 2-3 toolsets for a simple workflow
- ✅ You want orchestrator features but custom workflow logic
- ✅ You need fine-grained control over agent configuration

**Use `CombinedToolset` Directly (Method 3) When:**
- ✅ You need maximum control over every aspect of combination
- ✅ You're building custom combination logic or abstractions
- ✅ You have advanced requirements not covered by higher-level methods
- ✅ You want to implement custom prefixing or prompt combination strategies
- ✅ You're integrating with custom frameworks or systems

**Quick Reference:**
- **Most users:** Start with `create_workflow_agent()` - it handles everything automatically
- **Custom workflows:** Use `create_combined_toolset()` for flexibility with automatic features
- **Advanced use cases:** Use `CombinedToolset` directly for full control

### Choosing the Right Combination Strategy

#### 1. **Sequential Processing Workflows** (Information → Reasoning → Refinement)

**Pattern:** Information Gathering → Decomposition/Reasoning → Refinement → Tracking

**Best Toolsets:**
- **Start with:** Search, Multi-Persona Analysis, or Self-Ask (information gathering/decomposition)
- **Middle:** CoT, ToT, GoT, Beam Search, or MCTS (reasoning/exploration)
- **End with:** Reflection or Self-Refine (refinement)
- **Optional:** Todo (task tracking)

**Example Scenarios:**
- Research tasks: `Search → Self-Ask → Self-Refine → Todo`
- Code architecture: `Self-Ask → ToT → Reflection → Todo`
- Analysis tasks: `Search → CoT → Reflection`

**Why This Works:**
- Information gathering provides context for reasoning
- Reasoning toolsets explore solutions systematically
- Refinement toolsets polish outputs
- Clear data flow from one stage to the next

#### 2. **Multi-Perspective Workflows** (Diverse Views → Synthesis → Refinement)

**Pattern:** Multiple Perspectives → Exploration → Refinement

**Best Toolsets:**
- **Start with:** Multi-Persona Analysis or Multi-Persona Debate (diverse perspectives)
- **Middle:** GoT, ToT, or Beam Search (explore synthesized perspectives)
- **End with:** Reflection (refine final solution)

**Example Scenarios:**
- Creative problem solving: `Multi-Persona Analysis → GoT → Reflection`
- Strategic decisions: `Multi-Persona Debate → MCTS → Reflection`
- Complex analysis: `Multi-Persona Analysis → ToT → Reflection`

**Why This Works:**
- Personas provide diverse expert viewpoints
- Exploration toolsets systematically evaluate synthesized perspectives
- Reflection ensures high-quality final output
- Combines breadth (personas) with depth (exploration)

#### 3. **Exploration-Heavy Workflows** (Reasoning → Exploration → Refinement)

**Pattern:** Initial Reasoning → Deep Exploration → Refinement

**Best Toolsets:**
- **Start with:** CoT or Self-Ask (initial reasoning/decomposition)
- **Middle:** ToT, GoT, Beam Search, or MCTS (deep exploration)
- **End with:** Reflection or Self-Refine (refinement)

**Example Scenarios:**
- Complex problem solving: `CoT → ToT → Reflection`
- Decision making: `Self-Ask → MCTS → Reflection`
- Architecture design: `Self-Ask → ToT → Reflection → Todo`

**Why This Works:**
- Initial reasoning establishes problem structure
- Exploration toolsets find optimal solutions
- Refinement ensures quality
- Good for problems requiring both structure and exploration

#### 4. **Information-Heavy Workflows** (Research → Decomposition → Refinement)

**Pattern:** Research → Question Decomposition → Answer Composition → Refinement

**Best Toolsets:**
- **Start with:** Search (information gathering)
- **Middle:** Self-Ask (decomposition and composition)
- **End with:** Self-Refine or Reflection (refinement)
- **Optional:** Todo (tracking research tasks)

**Example Scenarios:**
- Research reports: `Search → Self-Ask → Self-Refine → Todo`
- Fact-finding missions: `Search → Self-Ask → Reflection`
- Literature reviews: `Search → Self-Ask → Self-Refine`

**Why This Works:**
- Search provides current, authoritative information
- Self-Ask breaks complex questions into manageable parts
- Refinement ensures accuracy and completeness
- Perfect for research-intensive tasks

### Toolset Compatibility Guidelines

#### ✅ **Good Combinations:**

1. **Search + Self-Ask + Self-Refine**
   - Search provides information → Self-Ask decomposes → Self-Refine polishes
   - Clear sequential flow

2. **Multi-Persona Analysis + GoT + Reflection**
   - Personas provide perspectives → GoT explores connections → Reflection refines
   - Combines breadth and depth

3. **Self-Ask + ToT + Reflection**
   - Self-Ask structures problem → ToT explores solutions → Reflection refines
   - Good for structured exploration

4. **Multi-Persona Debate + MCTS + Reflection**
   - Debate explores positions → MCTS explores decisions → Reflection refines
   - Perfect for strategic decisions

5. **CoT + Reflection**
   - Simple sequential reasoning → refinement
   - Good for straightforward problems needing polish

#### ⚠️ **Consider Carefully:**

1. **Multiple Exploration Toolsets** (ToT + GoT + Beam Search)
   - Can be redundant - choose one based on problem structure
   - Use multiple only if you need different exploration strategies

2. **Multiple Refinement Toolsets** (Reflection + Self-Refine)
   - Usually redundant - choose one based on your needs
   - Reflection: critique-based refinement
   - Self-Refine: feedback-based refinement with thresholds

3. **CoT + ToT Together**
   - Can work but may be redundant
   - Use CoT for sequential reasoning, ToT for parallel exploration
   - Better: use CoT → ToT sequentially rather than simultaneously

#### ❌ **Avoid:**

1. **Conflicting Patterns**
   - Don't combine toolsets that serve the same purpose without clear sequencing
   - Example: Using both Reflection and Self-Refine simultaneously (use sequentially or choose one)

2. **Over-Complex Workflows**
   - More than 4-5 toolsets usually indicates over-engineering
   - Simplify by removing redundant stages

### Workflow Design Principles

#### 1. **Start with Information Gathering**
- Use Search for external information
- Use Self-Ask for problem decomposition
- Use Multi-Persona Analysis for diverse perspectives

#### 2. **Use Exploration Toolsets for Complex Problems**
- ToT: Multiple parallel approaches
- GoT: Interconnected solutions
- Beam Search: Top-K exploration
- MCTS: Decision trees with uncertainty

#### 3. **Always End with Refinement**
- Reflection: Critique-based improvement
- Self-Refine: Feedback-based improvement with thresholds
- Choose based on your quality requirements

#### 4. **Add Todo for Complex Multi-Step Tasks**
- Track progress across workflow stages
- Monitor completion of research, reasoning, and refinement tasks
- Useful for long-running workflows

### Common Patterns by Use Case

#### **Research & Information Tasks**
```
Search → Self-Ask → Self-Refine → Todo
```
- Gather information → Decompose questions → Refine answers → Track progress

#### **Creative Problem Solving**
```
Multi-Persona Analysis → GoT → Reflection
```
- Gather perspectives → Explore interconnected solutions → Refine

#### **Strategic Decision Making**
```
Multi-Persona Debate → MCTS → Reflection
```
- Debate positions → Explore decision space → Refine decision

#### **Code & Architecture Design**
```
Self-Ask → ToT → Reflection → Todo
```
- Decompose problem → Explore approaches → Refine design → Track tasks

#### **Analysis & Planning**
```
Search → CoT → Reflection
```
- Gather information → Sequential reasoning → Refine analysis

#### **Complex Multi-Step Tasks**
```
CoT → Todo → Reflection
```
- Plan steps → Track progress → Refine output

### Tips for Effective Combinations

1. **Keep Workflows Focused**
   - Each toolset should have a clear role
   - Avoid redundant toolsets serving the same purpose

2. **Use Meta-Orchestrator for Complex Workflows**
   - Track progress across stages
   - Monitor transitions
   - Link outputs between toolsets

3. **Start Simple, Add Complexity as Needed**
   - Begin with 2-3 toolsets
   - Add more only if they add clear value
   - Test combinations before production use

4. **Consider Token Costs**
   - More toolsets = more system prompt tokens
   - Longer workflows = more API calls
   - Balance capability with cost

5. **Test Workflow Templates First**
   - Use predefined templates as starting points
   - Customize only if templates don't fit your needs
   - Templates are optimized and tested

6. **Monitor Workflow Progress**
   - Use Meta-Orchestrator to track stages
   - Read unified state to understand progress
   - Create cross-toolset links for traceability

---

## Combination Examples

> **Note:** These examples demonstrate different combination methods. For most use cases, start with `create_workflow_agent()` (Method 1) as shown in the Research Assistant and Creative Problem Solver examples. Use `create_combined_toolset()` (Method 2) for custom workflows, and `CombinedToolset` directly (Method 3) only for advanced use cases.

### Research Assistant Workflow (Method 1: `create_workflow_agent()`)

```python
from pydantic_ai_toolsets import (
    RESEARCH_ASSISTANT,
    create_search_toolset,
    create_self_ask_toolset,
    create_self_refine_toolset,
    create_todo_toolset,
    SearchStorage,
    SelfAskStorage,
    SelfRefineStorage,
    TodoStorage,
    MetaOrchestratorStorage,
    create_workflow_agent,
)

# Create storages
storages = {
    "search": SearchStorage(track_usage=True),
    "self_ask": SelfAskStorage(track_usage=True),
    "self_refine": SelfRefineStorage(track_usage=True),
    "todo": TodoStorage(track_usage=True),
}

# Create toolsets with IDs for proper aliasing
toolsets = [
    create_search_toolset(storages["search"], id="search"),
    create_self_ask_toolset(storages["self_ask"], id="self_ask"),
    create_self_refine_toolset(storages["self_refine"], id="self_refine"),
    create_todo_toolset(storages["todo"], id="todo"),
]

# Create orchestrator storage
orchestrator_storage = MetaOrchestratorStorage(track_usage=True)

# Create agent with workflow template
agent = create_workflow_agent(
    model="openai:gpt-4",
    workflow_template=RESEARCH_ASSISTANT,
    toolsets=toolsets,
    storages=storages,
    orchestrator_storage=orchestrator_storage,
    additional_system_prompt="Always cite sources and provide URLs when available.",
)

# Run the agent
result = await agent.run("Research the latest developments in quantum computing")

# Access unified state
unified_state = await agent.run("Read the unified state")
print(unified_state.data)

# Check workflow progress
workflow = orchestrator_storage.get_active_workflow()
print(f"Current stage: {workflow.current_stage + 1}/{len(RESEARCH_ASSISTANT.stages)}")
```

### Creative Problem Solver Workflow (Method 1: `create_workflow_agent()`)

```python
from pydantic_ai_toolsets import (
    CREATIVE_PROBLEM_SOLVER,
    create_persona_toolset,
    create_got_toolset,
    create_reflection_toolset,
    PersonaStorage,
    GoTStorage,
    ReflectionStorage,
    MetaOrchestratorStorage,
    create_workflow_agent,
)

# Create storages
storages = {
    "persona": PersonaStorage(track_usage=True),
    "got": GoTStorage(track_usage=True),
    "reflection": ReflectionStorage(track_usage=True),
}

# Create toolsets
toolsets = [
    create_persona_toolset(storages["persona"], id="persona"),
    create_got_toolset(storages["got"], id="got"),
    create_reflection_toolset(storages["reflection"], id="reflection"),
]

# Create orchestrator and agent
orchestrator_storage = MetaOrchestratorStorage()
agent = create_workflow_agent(
    model="openai:gpt-4",
    workflow_template=CREATIVE_PROBLEM_SOLVER,
    toolsets=toolsets,
    storages=storages,
    orchestrator_storage=orchestrator_storage,
)

# Solve a creative problem
result = await agent.run("How can we reduce plastic waste in oceans? Explore multiple perspectives and synthesize solutions.")
```

### Manual Toolset Combination (Method 2: `create_combined_toolset()`)

You can also combine toolsets manually without using workflow templates:

```python
from pydantic_ai_toolsets import (
    create_cot_toolset,
    create_tot_toolset,
    CoTStorage,
    ToTStorage,
    create_combined_toolset,
)
from pydantic_ai import Agent

# Create storages
cot_storage = CoTStorage()
tot_storage = ToTStorage()

# Create toolsets
cot_toolset = create_cot_toolset(cot_storage, id="cot")
tot_toolset = create_tot_toolset(tot_storage, id="tot")

# Define prefix map
prefix_map = {
    "cot": "cot_",
    "tot": "tot_",
}

storages_map = {
    "cot": cot_storage,
    "tot": tot_storage,
}

# Combine toolsets
combined_toolset, combined_prompt = create_combined_toolset(
    toolsets=[cot_toolset, tot_toolset],
    storages=storages_map,
    prefix_map=prefix_map,
    auto_prefix=True,
)

# Create agent with combined toolset
agent = Agent(
    "openai:gpt-4",
    system_prompt=combined_prompt,
    toolsets=[combined_toolset],
)

# Use the agent
result = await agent.run("Solve this problem using both sequential and tree-based reasoning")
```

### Cross-Toolset Linking

Create links between outputs from different toolsets:

```python
from pydantic_ai_toolsets.toolsets.meta_orchestrator.types import LinkToolsetOutputsItem, LinkType

# After running the agent, create links between toolset outputs
link_item = LinkToolsetOutputsItem(
    source_toolset_id="search",
    source_item_id="result_123",
    target_toolset_id="self_ask",
    target_item_id="question_456",
    link_type=LinkType.REFERENCES,
)

# The agent can call link_toolset_outputs tool to create the link
result = await agent.run(f"Link search result result_123 to question question_456")
```

---

## Meta-Orchestrator

The meta-orchestrator toolset provides workflow orchestration and multi-toolset coordination capabilities.

### When to Use It

Use the meta-orchestrator when you need to:
- **Track multi-stage workflows** across multiple toolsets
- **Monitor workflow progress** and stage transitions
- **Link outputs** between different toolsets
- **Access unified state** across all active toolsets
- **Manage workflow templates** and transitions

### Registering Toolsets

Toolsets are automatically registered when using `create_workflow_agent()`, or you can register them manually:

```python
from pydantic_ai_toolsets import (
    MetaOrchestratorStorage,
    register_toolsets_with_orchestrator,
)

orchestrator_storage = MetaOrchestratorStorage()

# Register toolsets with their storages
register_toolsets_with_orchestrator(
    orchestrator_storage=orchestrator_storage,
    toolsets=[cot_toolset, tot_toolset],
    storages={"cot": cot_storage, "tot": tot_storage},
)
```

### Tracking Workflows

The orchestrator tracks:
- **Active workflows** and their current stage
- **Toolset transitions** between stages
- **Cross-toolset links** connecting outputs
- **Workflow state** including completed stages

```python
# Get active workflow
workflow = orchestrator_storage.get_active_workflow()
if workflow:
    print(f"Workflow: {workflow.template_name}")
    print(f"Current stage: {workflow.current_stage + 1}/{len(workflow.active_toolsets)}")
    print(f"Completed stages: {workflow.completed_stages}")

# Read unified state
from pydantic_ai_toolsets import create_meta_orchestrator_toolset
from pydantic_ai import Agent

orchestrator_toolset = create_meta_orchestrator_toolset(orchestrator_storage)
read_agent = Agent("openai:gpt-4", toolsets=[orchestrator_toolset])
state_result = await read_agent.run("Read the unified state")
print(state_result.data)
```

### Creating Custom Workflows

You can create custom workflow templates:

```python
from pydantic_ai_toolsets.toolsets.meta_orchestrator.types import WorkflowTemplate, Stage

CUSTOM_WORKFLOW = WorkflowTemplate(
    name="custom_workflow",
    toolsets=["cot", "reflection"],
    stages=[
        Stage(
            name="reason",
            toolset_id="cot",
            transition_condition="has_final_thought",
            description="Reason through the problem step by step",
        ),
        Stage(
            name="reflect",
            toolset_id="reflection",
            transition_condition="has_best_output",
            description="Reflect on and refine the solution",
        ),
    ],
    handoff_instructions={
        "cot→reflection": "Use final thought as initial output for reflection",
    },
    description="Custom workflow for reasoning and reflection",
)

# Use the custom template
agent = create_workflow_agent(
    model="openai:gpt-4",
    workflow_template=CUSTOM_WORKFLOW,
    toolsets=[cot_toolset, reflection_toolset],
    storages={"cot": cot_storage, "reflection": reflection_storage},
    orchestrator_storage=orchestrator_storage,
)
```

### Orchestrator Tools

The meta-orchestrator provides these tools to agents:

- **`start_workflow`**: Start a new workflow using a predefined template
- **`suggest_toolset_transition`**: Suggest when to transition between toolsets
- **`link_toolset_outputs`**: Create links between outputs from different toolsets
- **`read_unified_state`**: Read the unified state across all active toolsets
- **`get_workflow_status`**: Get the current status of an active workflow

---

## Installation

```bash
pip install pydantic-ai-toolsets
```

## Quick Start

### Basic Usage

Each toolset can be used with or without storage. Here are examples for each category:

#### Reasoning Toolsets

**Chain of Thought (CoT):**
```python
from pydantic_ai import Agent
from pydantic_ai_toolsets import create_cot_toolset, CoTStorage, get_cot_system_prompt

# Basic usage
agent = Agent("openai:gpt-4", toolsets=[create_cot_toolset()])
result = await agent.run("Solve this complex problem step by step")

# With storage to access thoughts
storage = CoTStorage()
agent = Agent("openai:gpt-4", toolsets=[create_cot_toolset(storage)])
result = await agent.run("Solve this problem")
print(storage.thoughts)  # Access thoughts directly

# With custom system prompt using decorator
storage = CoTStorage()
toolset = create_cot_toolset(storage)
agent = Agent("openai:gpt-4", toolsets=[toolset])

@agent.instructions
async def add_cot_prompt() -> str:
    """Add the chain of thoughts system prompt."""
    return get_cot_system_prompt()

result = await agent.run("Solve this problem step by step")
```

**Tree of Thought (ToT):**
```python
from pydantic_ai import Agent
from pydantic_ai_toolsets import create_tot_toolset, ToTStorage, get_tot_system_prompt

storage = ToTStorage()
toolset = create_tot_toolset(storage)
agent = Agent("openai:gpt-4", toolsets=[toolset])

@agent.instructions
async def add_tot_prompt() -> str:
    """Add the tree of thoughts system prompt."""
    return get_tot_system_prompt()

result = await agent.run("Explore multiple approaches to solve this problem")
print(storage.nodes)  # Access reasoning nodes
```

**Graph of Thought (GoT):**
```python
from pydantic_ai import Agent
from pydantic_ai_toolsets import create_got_toolset, GoTStorage, get_got_system_prompt

storage = GoTStorage()
toolset = create_got_toolset(storage)
agent = Agent("openai:gpt-4", toolsets=[toolset])

@agent.instructions
async def add_got_prompt() -> str:
    """Add the graph of thoughts system prompt."""
    return get_got_system_prompt()

result = await agent.run("Solve this interconnected problem")
```

**Beam Search:**
```python
from pydantic_ai import Agent
from pydantic_ai_toolsets import create_beam_toolset, BeamStorage, get_beam_system_prompt

storage = BeamStorage()
toolset = create_beam_toolset(storage)
agent = Agent("openai:gpt-4", toolsets=[toolset])

@agent.instructions
async def add_beam_prompt() -> str:
    """Add the beam search system prompt."""
    return get_beam_system_prompt()

result = await agent.run("Find the best solution exploring top-k paths")
```

**Monte Carlo Tree Search (MCTS):**
```python
from pydantic_ai import Agent
from pydantic_ai_toolsets import create_mcts_toolset, MCTSStorage, get_mcts_system_prompt

storage = MCTSStorage()
toolset = create_mcts_toolset(storage)
agent = Agent("openai:gpt-4", toolsets=[toolset])

@agent.instructions
async def add_mcts_prompt() -> str:
    """Add the MCTS system prompt."""
    return get_mcts_system_prompt()

result = await agent.run("Make optimal decisions through exploration")
```

#### Reflection Toolsets

**Reflection:**
```python
from pydantic_ai import Agent
from pydantic_ai_toolsets import create_reflection_toolset, ReflectionStorage, get_reflection_system_prompt

storage = ReflectionStorage()
toolset = create_reflection_toolset(storage)
agent = Agent("openai:gpt-4", toolsets=[toolset])

@agent.instructions
async def add_reflection_prompt() -> str:
    """Add the reflection system prompt."""
    return get_reflection_system_prompt(storage)

result = await agent.run("Create and refine a high-quality solution")
print(storage.outputs)  # Access all outputs and refinements
```

**Self-Refine:**
```python
from pydantic_ai import Agent
from pydantic_ai_toolsets import create_self_refine_toolset, SelfRefineStorage, get_self_refine_system_prompt

storage = SelfRefineStorage()
toolset = create_self_refine_toolset(storage)
agent = Agent("openai:gpt-4", toolsets=[toolset])

@agent.instructions
async def add_self_refine_prompt() -> str:
    """Add the self-refine system prompt."""
    return get_self_refine_system_prompt()

result = await agent.run("Generate and iteratively improve this output")
```

**Self-Ask:**
```python
from pydantic_ai import Agent
from pydantic_ai_toolsets import create_self_ask_toolset, SelfAskStorage, get_self_ask_system_prompt

storage = SelfAskStorage()
toolset = create_self_ask_toolset(storage)
agent = Agent("openai:gpt-4", toolsets=[toolset])

@agent.instructions
async def add_self_ask_prompt() -> str:
    """Add the self-ask system prompt."""
    return get_self_ask_system_prompt(storage)

result = await agent.run("Answer this complex question by breaking it down")
```

#### Multi-Agent Toolsets

**Multi-Persona Analysis:**
```python
from pydantic_ai import Agent
from pydantic_ai_toolsets import create_persona_toolset, PersonaStorage, get_persona_system_prompt

storage = PersonaStorage()
toolset = create_persona_toolset(storage)
agent = Agent("openai:gpt-4", toolsets=[toolset])

@agent.instructions
async def add_persona_prompt() -> str:
    """Add the multi-persona analysis system prompt."""
    return get_persona_system_prompt()

result = await agent.run("Analyze this problem from multiple expert perspectives")
print(storage.session)  # Access persona session state
```

**Multi-Persona Debate:**
```python
from pydantic_ai import Agent
from pydantic_ai_toolsets import create_persona_debate_toolset, PersonaDebateStorage, get_persona_debate_system_prompt

storage = PersonaDebateStorage()
toolset = create_persona_debate_toolset(storage)
agent = Agent("openai:gpt-4", toolsets=[toolset])

@agent.instructions
async def add_persona_debate_prompt() -> str:
    """Add the persona debate system prompt."""
    return get_persona_debate_system_prompt(storage)

result = await agent.run("Debate: Should we adopt microservices?")
print(storage.session)  # Access debate state
```

#### Utility Toolsets

**To-Do:**
```python
from pydantic_ai import Agent
from pydantic_ai_toolsets import create_todo_toolset, TodoStorage, get_todo_system_prompt

storage = TodoStorage()
toolset = create_todo_toolset(storage)
agent = Agent("openai:gpt-4", toolsets=[toolset])

@agent.instructions
async def add_todo_prompt() -> str:
    """Add the todo system prompt."""
    return get_todo_system_prompt()

result = await agent.run("Manage these tasks: research, write, review")
print(storage.todos)  # Access task list
```

**Search (requires Firecrawl):**
```python
from pydantic_ai import Agent
from pydantic_ai_toolsets import create_search_toolset, SearchStorage, get_search_system_prompt

storage = SearchStorage()
toolset = create_search_toolset(storage)
agent = Agent("openai:gpt-4", toolsets=[toolset])

@agent.instructions
async def add_search_prompt() -> str:
    """Add the search system prompt."""
    return get_search_system_prompt()

result = await agent.run("Search for recent developments in AI")
```

### Usage Tracking

All storage classes support usage tracking:

```python
from pydantic_ai_toolsets import CoTStorage

# Enable usage tracking
storage = CoTStorage(track_usage=True)
agent = Agent("openai:gpt-4", toolsets=[create_cot_toolset(storage)])
result = await agent.run("Solve this problem")

# Check token usage
print(storage.metrics.total_tokens())
print(storage.metrics.total_requests())
```

---

## Running Evaluations

The evaluation system allows you to test and compare toolsets on standardized test cases. 
Evaluations are integrated with Logfire for monitoring and tracking.

### Prerequisites

Before running evaluations, ensure you have:

1. **OpenRouter API Key**: Set `OPENROUTER_API_KEY` environment variable or pass `--api-key`
2. **Logfire Token** (optional): Set `LOGFIRE_TOKEN` environment variable for monitoring
3. **Dependencies**: Install evaluation dependencies if not already installed

### Basic Usage

Run evaluations from the command line:

```bash
# Run all evaluations (all categories)
python -m pydantic_ai_toolsets.evals.run_evals

# Run evaluations for a specific category
python -m pydantic_ai_toolsets.evals.run_evals --category thinking

# Run a single toolset
python -m pydantic_ai_toolsets.evals.run_evals --toolset cot

# Run multiple toolsets
python -m pydantic_ai_toolsets.evals.run_evals --toolsets cot,tot,beam

# List all available toolsets
python -m pydantic_ai_toolsets.evals.run_evals --list-toolsets
```

### Running by Category

Run all toolsets within a specific category:

```bash
# Thinking/Cognition toolsets (beam, cot, got, mcts, tot)
python -m pydantic_ai_toolsets.evals.run_evals --category thinking

# Reflection toolsets (self_refine, reflection, self_ask)
python -m pydantic_ai_toolsets.evals.run_evals --category reflection

# Multi-agent toolsets (multi_personas, persona_debate)
python -m pydantic_ai_toolsets.evals.run_evals --category multi_agent

# Unique toolsets (todo, search)
python -m pydantic_ai_toolsets.evals.run_evals --category uniques

# Combination workflows (research_assistant, creative_problem_solver, etc.)
python -m pydantic_ai_toolsets.evals.run_evals --category combinations
```

### Running Individual Toolsets

Run a single toolset evaluation:

```bash
# Chain of Thought
python -m pydantic_ai_toolsets.evals.run_evals --toolset cot

# Tree of Thought
python -m pydantic_ai_toolsets.evals.run_evals --toolset tot

# Multi-Persona Analysis
python -m pydantic_ai_toolsets.evals.run_evals --toolset multi_personas

# Self-Refine
python -m pydantic_ai_toolsets.evals.run_evals --toolset self_refine

# Research Assistant workflow
python -m pydantic_ai_toolsets.evals.run_evals --toolset research_assistant
```

### Running Multiple Toolsets

Run multiple toolsets in a single evaluation run. Toolsets can be from the same or different categories:

```bash
# Multiple toolsets from same category
python -m pydantic_ai_toolsets.evals.run_evals --toolsets cot,tot,beam

# Toolsets from different categories
python -m pydantic_ai_toolsets.evals.run_evals --toolsets cot,multi_personas,self_refine

# Mix of individual toolsets and combinations
python -m pydantic_ai_toolsets.evals.run_evals --toolsets cot,research_assistant,reflection
```

### Available Toolsets

List all available toolsets organized by category:

```bash
python -m pydantic_ai_toolsets.evals.run_evals --list-toolsets
```

**Available toolsets by category:**

- **uniques**: `todo`, `search`
- **thinking**: `beam`, `cot`, `got`, `mcts`, `tot`
- **multi_agent**: `multi_personas`, `persona_debate`
- **reflection**: `self_refine`, `reflection`, `self_ask`
- **combinations**: `research_assistant`, `creative_problem_solver`, `strategic_decision_maker`, `code_architect`

### Execution Modes

Control how evaluations run:

```bash
# Sequential execution (default) - runs one toolset at a time
python -m pydantic_ai_toolsets.evals.run_evals --toolset cot

# Parallel execution - runs multiple toolsets simultaneously
python -m pydantic_ai_toolsets.evals.run_evals --toolsets cot,tot,beam --parallel
```

### Logfire Integration

Evaluations are automatically integrated with Logfire for monitoring:

```bash
# Logfire is enabled by default if LOGFIRE_TOKEN is set
export LOGFIRE_TOKEN=your_token_here
python -m pydantic_ai_toolsets.evals.run_evals --category thinking

# Disable Logfire if needed
python -m pydantic_ai_toolsets.evals.run_evals --category thinking --no-logfire
```

When Logfire is enabled:
- All evaluation runs appear in your Logfire dashboard
- You can track performance metrics, token usage, and execution times
- Compare results across different toolsets and runs
- Monitor evaluation progress in real-time

### Output Options

Control where and how results are saved:

```bash
# Save results to custom directory (default: eval_results/)
python -m pydantic_ai_toolsets.evals.run_evals --category thinking --output-dir ./my_results

# Export as JSON (default)
python -m pydantic_ai_toolsets.evals.run_evals --category thinking --format json

# Export as CSV summary
python -m pydantic_ai_toolsets.evals.run_evals --category thinking --format csv
```

### Complete Example

Run a comprehensive evaluation comparing multiple reasoning toolsets:

```bash
# Set API key
export OPENROUTER_API_KEY=your_key_here

# Set Logfire token for monitoring (optional)
export LOGFIRE_TOKEN=your_token_here

# Run evaluation comparing CoT, ToT, and Beam Search
python -m pydantic_ai_toolsets.evals.run_evals \
  --toolsets cot,tot,beam \
  --output-dir ./eval_results/reasoning_comparison \
  --format json

# Results will be saved to ./eval_results/reasoning_comparison/results.json
# And visible in Logfire dashboard if token is set
```

### Evaluation Results

Evaluation results include:

- **Case Results**: Pass/fail status for each test case
- **Summary Statistics**: Total cases, success rate, errors
- **Performance Metrics**: Average execution time, total tokens used
- **Toolset Comparison**: Side-by-side comparison when running multiple toolsets

Results are organized by category and toolset, making it easy to compare performance across different approaches.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Key Points:**
- ✅ Free to use and modify for personal or commercial purposes
- ✅ Author acknowledgment required (copyright notice must be included)
- ✅ Credit to [pydantic-ai-todo](https://github.com/vstorm-co/pydantic-ai-todo) - this project extends their architectural patterns

The MIT License allows you to use, modify, distribute, and sell this software, as long as you include the original copyright notice and license text. This ensures the author is properly acknowledged while giving you maximum freedom to use the software.
