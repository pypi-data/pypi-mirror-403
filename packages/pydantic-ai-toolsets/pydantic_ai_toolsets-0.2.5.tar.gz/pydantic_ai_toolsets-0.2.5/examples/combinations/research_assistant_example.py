"""Example: Research Assistant workflow combining Search, Self-Ask, Self-Refine, and Todo toolsets.

This example demonstrates:
- Workflow initialization using RESEARCH_ASSISTANT template
- Toolset combination with automatic prefixing
- Cross-toolset linking
- Unified state reading
- Workflow progression tracking
"""

from __future__ import annotations

import asyncio

from pydantic_ai_toolsets import (
    MetaOrchestratorStorage,
    RESEARCH_ASSISTANT,
    SearchStorage,
    SelfAskStorage,
    SelfRefineStorage,
    TodoStorage,
    create_search_toolset,
    create_self_ask_toolset,
    create_self_refine_toolset,
    create_todo_toolset,
)
from pydantic_ai_toolsets.toolsets.meta_orchestrator.helpers import (
    create_combined_toolset,
    create_workflow_agent,
    register_toolsets_with_orchestrator,
)


async def main() -> None:
    """Run Research Assistant workflow example."""
    print("=" * 70)
    print("Research Assistant Workflow Example")
    print("=" * 70)
    print()

    # 1. Create storages for all toolsets
    print("Step 1: Creating storages...")
    search_storage = SearchStorage(track_usage=True)
    self_ask_storage = SelfAskStorage(track_usage=True)
    self_refine_storage = SelfRefineStorage(track_usage=True)
    todo_storage = TodoStorage(track_usage=True)
    orchestrator_storage = MetaOrchestratorStorage(track_usage=True)
    print("✓ Storages created")
    print()

    # 2. Create toolsets (original function names preserved - backward compatible)
    print("Step 2: Creating toolsets...")
    search_toolset = create_search_toolset(search_storage, id="search")
    self_ask_toolset = create_self_ask_toolset(self_ask_storage, id="self_ask")
    self_refine_toolset = create_self_refine_toolset(self_refine_storage, id="self_refine")
    todo_toolset = create_todo_toolset(todo_storage, id="todo")
    orchestrator_toolset = create_meta_orchestrator_toolset(orchestrator_storage, id="orchestrator")
    print("✓ Toolsets created")
    print()

    # 3. Define prefix map for aliasing
    print("Step 3: Setting up prefix mapping...")
    prefix_map = {
        "search": "search_",
        "self_ask": "self_ask_",
        "self_refine": "self_refine_",
        "todo": "todo_",
    }
    storages_map = {
        "search": search_storage,
        "self_ask": self_ask_storage,
        "self_refine": self_refine_storage,
        "todo": todo_storage,
    }
    print("✓ Prefix map configured")
    print(f"  Tools will be prefixed: {prefix_map}")
    print()

    # 4. Register toolsets with orchestrator
    print("Step 4: Registering toolsets with orchestrator...")
    register_toolsets_with_orchestrator(
        orchestrator_storage=orchestrator_storage,
        toolsets=[search_toolset, self_ask_toolset, self_refine_toolset, todo_toolset],
        storages=storages_map,
    )
    print("✓ Toolsets registered")
    print()

    # 5. Create agent with workflow template using convenience function
    print("Step 5: Creating agent with workflow template...")
    agent = create_workflow_agent(
        model="openrouter:openai/gpt-4o-mini",
        workflow_template=RESEARCH_ASSISTANT,
        toolsets=[search_toolset, self_ask_toolset, self_refine_toolset, todo_toolset],
        storages=storages_map,
        prefix_map=prefix_map,
        orchestrator_storage=orchestrator_storage,
        auto_prefix=True,
        additional_system_prompt="Always cite sources and provide URLs when available.",
    )
    print("✓ Agent created with workflow template")
    print(f"  Workflow: {RESEARCH_ASSISTANT.name}")
    print(f"  Stages: {len(RESEARCH_ASSISTANT.stages)}")
    print()

    # 6. Demonstrate workflow initialization via agent
    print("Step 6: Initializing workflow via agent...")
    try:
        # The agent can call start_workflow tool to initialize the workflow
        init_result = await agent.run("Start the research assistant workflow")
        print("✓ Workflow initialized via agent")
        print(f"  Response: {init_result.data[:200]}..." if len(init_result.data) > 200 else f"  Response: {init_result.data}")
        print()
    except Exception as e:
        print(f"⚠ Error initializing workflow: {e}")
        print("(This is expected if API keys are not configured)")
        print()

    # 7. Run example query
    print("Step 7: Running example query...")
    query = "Research the latest developments in quantum computing and explain the key breakthroughs"
    print(f"Query: {query}")
    print()

    try:
        result = await agent.run(query)
        print("✓ Agent completed")
        print(f"Result: {result.data[:200]}..." if len(result.data) > 200 else f"Result: {result.data}")
        print()
    except Exception as e:
        print(f"⚠ Error during execution: {e}")
        print("(This is expected if API keys are not configured)")
        print()

    # 8. Demonstrate unified state reading via agent
    print("Step 8: Reading unified state via agent...")
    try:
        # The agent can call read_unified_state tool
        state_result = await agent.run("Read the unified state to see all toolset states and workflow progress")
        print("✓ Unified state read via agent")
        print(state_result.data[:500] + "..." if len(state_result.data) > 500 else state_result.data)
        print()
    except Exception as e:
        print(f"⚠ Error reading state: {e}")
        print("(This is expected if API keys are not configured)")
        print()

    # 9. Demonstrate cross-toolset linking via agent
    print("Step 9: Demonstrating cross-toolset linking via agent...")
    from pydantic_ai_toolsets.toolsets.meta_orchestrator.types import LinkToolsetOutputsItem, LinkType

    # Example: Have agent create a link between search result and self-ask question
    if search_storage.search_results and self_ask_storage.questions:
        search_result_id = list(search_storage.search_results.keys())[0]
        question_id = list(self_ask_storage.questions.keys())[0]
        
        try:
            # The agent can call link_toolset_outputs tool
            link_prompt = f"Link the search result {search_result_id} to the self-ask question {question_id} as a reference"
            link_result = await agent.run(link_prompt)
            print("✓ Cross-toolset link created via agent")
            print(f"  Response: {link_result.data[:200]}..." if len(link_result.data) > 200 else f"  Response: {link_result.data}")
            print()
        except Exception as e:
            print(f"⚠ Error creating link via agent: {e}")
            # Fallback: manually create link for demonstration
            from pydantic_ai_toolsets.toolsets.meta_orchestrator.types import CrossToolsetLink
            import time
            
            link = CrossToolsetLink(
                link_id="example_link_1",
                source_toolset_id="search",
                source_item_id=search_result_id,
                target_toolset_id="self_ask",
                target_item_id=question_id,
                link_type=LinkType.REFERENCES,
                created_at=time.time(),
            )
            orchestrator_storage.create_link(link)
            print("✓ Cross-toolset link created manually (fallback)")
            print(f"  {link.source_toolset_id}:{link.source_item_id[:8]}... → {link.target_toolset_id}:{link.target_item_id[:8]}... ({link.link_type.value})")
            print()

    # 10. Demonstrate toolset transitions
    print("Step 10: Demonstrating toolset transitions...")
    try:
        # The agent can call suggest_toolset_transition tool
        transition_result = await agent.run("Suggest the next toolset transition based on current workflow state")
        print("✓ Toolset transition suggested via agent")
        print(f"  Response: {transition_result.data[:200]}..." if len(transition_result.data) > 200 else f"  Response: {transition_result.data}")
        print()
    except Exception as e:
        print(f"⚠ Error suggesting transition: {e}")
        print("(This is expected if API keys are not configured)")
        print()

    # 11. Show workflow summary
    print("Step 11: Workflow Summary")
    print("-" * 70)
    active_workflow = orchestrator_storage.get_active_workflow()
    if active_workflow:
        print(f"Workflow: {active_workflow.template_name}")
        print(f"Current Stage: {active_workflow.current_stage + 1}/{len(RESEARCH_ASSISTANT.stages)}")
        print(f"Completed Stages: {len(active_workflow.completed_stages)}")
        print(f"Total Links: {len(orchestrator_storage.links)}")
        print(f"Total Transitions: {len(orchestrator_storage.transitions)}")
    print()

    # 12. Show storage statistics
    print("Step 12: Storage Statistics")
    print("-" * 70)
    if search_storage.search_results:
        print(f"Search: {len(search_storage.search_results)} results")
    if self_ask_storage.questions:
        print(f"Self-Ask: {len(self_ask_storage.questions)} questions, {len(self_ask_storage.final_answers)} final answers")
    if self_refine_storage.outputs:
        print(f"Self-Refine: {len(self_refine_storage.outputs)} outputs")
    if todo_storage.todos:
        print(f"Todo: {len(todo_storage.todos)} tasks")
    print()

    print("=" * 70)
    print("Example completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
