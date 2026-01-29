"""Example: Code Architect workflow combining Self-Ask, Tree of Thoughts, Reflection, and Todo.

This example demonstrates:
- Workflow initialization using CODE_ARCHITECT template
- Toolset combination with automatic prefixing
- Cross-toolset linking
- Unified state reading
- Workflow progression tracking
"""

from __future__ import annotations

import asyncio
import time

from pydantic_ai_toolsets import (
    CODE_ARCHITECT,
    MetaOrchestratorStorage,
    ReflectionStorage,
    SelfAskStorage,
    TodoStorage,
    ToTStorage,
    create_reflection_toolset,
    create_self_ask_toolset,
    create_todo_toolset,
    create_tot_toolset,
)
from pydantic_ai_toolsets.toolsets.meta_orchestrator.helpers import (
    create_workflow_agent,
    register_toolsets_with_orchestrator,
)
from pydantic_ai_toolsets.toolsets.meta_orchestrator.types import (
    CrossToolsetLink,
    LinkType,
)


async def main() -> None:
    """Run Code Architect workflow example."""
    print("=" * 70)
    print("Code Architect Workflow Example")
    print("=" * 70)
    print()

    # 1. Create storages for all toolsets
    print("Step 1: Creating storages...")
    self_ask_storage = SelfAskStorage(track_usage=True)
    tot_storage = ToTStorage(track_usage=True)
    reflection_storage = ReflectionStorage(track_usage=True)
    todo_storage = TodoStorage(track_usage=True)
    orchestrator_storage = MetaOrchestratorStorage(track_usage=True)
    print("✓ Storages created")
    print()

    # 2. Create toolsets
    print("Step 2: Creating toolsets...")
    self_ask_toolset = create_self_ask_toolset(self_ask_storage, id="self_ask")
    tot_toolset = create_tot_toolset(tot_storage, id="tot")
    reflection_toolset = create_reflection_toolset(reflection_storage, id="reflection")
    todo_toolset = create_todo_toolset(todo_storage, id="todo")
    print("✓ Toolsets created")
    print()

    # 3. Define prefix map for aliasing
    print("Step 3: Setting up prefix mapping...")
    prefix_map = {
        "self_ask": "self_ask_",
        "tot": "tot_",
        "reflection": "reflection_",
        "todo": "todo_",
    }
    storages_map = {
        "self_ask": self_ask_storage,
        "tot": tot_storage,
        "reflection": reflection_storage,
        "todo": todo_storage,
    }
    print("✓ Prefix map configured")
    print(f"  Tools will be prefixed: {prefix_map}")
    print()

    # 4. Register toolsets with orchestrator
    print("Step 4: Registering toolsets with orchestrator...")
    register_toolsets_with_orchestrator(
        orchestrator_storage=orchestrator_storage,
        toolsets=[self_ask_toolset, tot_toolset, reflection_toolset, todo_toolset],
        storages=storages_map,
    )
    print("✓ Toolsets registered")
    print()

    # 5. Create agent with workflow template using convenience function
    print("Step 5: Creating agent with workflow template...")
    agent = create_workflow_agent(
        model="openrouter:openai/gpt-4o-mini",
        workflow_template=CODE_ARCHITECT,
        toolsets=[self_ask_toolset, tot_toolset, reflection_toolset, todo_toolset],
        storages=storages_map,
        prefix_map=prefix_map,
        orchestrator_storage=orchestrator_storage,
        auto_prefix=True,
    )
    print("✓ Agent created with workflow template")
    print(f"  Workflow: {CODE_ARCHITECT.name}")
    print(f"  Stages: {len(CODE_ARCHITECT.stages)}")
    print()

    # 6. Demonstrate workflow initialization via agent
    print("Step 6: Initializing workflow via agent...")
    try:
        init_result = await agent.run("Start the code architect workflow")
        print("✓ Workflow initialized via agent")
        print(f"  Response: {init_result.data}..." if len(init_result.data) > 200 else f"  Response: {init_result.data}")
        print()
    except Exception as e:
        print(f"⚠ Error initializing workflow: {e}")
        print("(This is expected if API keys are not configured)")
        print()

    # 7. Run example query
    print("Step 7: Running example query...")
    query = "Design a microservices architecture for an e-commerce platform. Decompose the problem, explore architectural options, and refine the design."
    print(f"Query: {query}")
    print()

    try:
        result = await agent.run(query)
        print("✓ Agent completed")
        print(f"Result: {result.data}..." if len(result.data) > 200 else f"Result: {result.data}")
        print()
    except Exception as e:
        print(f"⚠ Error during execution: {e}")
        print("(This is expected if API keys are not configured)")
        print()

    # 8. Demonstrate unified state reading via agent
    print("Step 8: Reading unified state via agent...")
    try:
        state_result = await agent.run("Read the unified state to see all toolset states and workflow progress")
        print("✓ Unified state read via agent")
        print(state_result.data + "..." if len(state_result.data) > 500 else state_result.data)
        print()
    except Exception as e:
        print(f"⚠ Error reading state: {e}")
        print("(This is expected if API keys are not configured)")
        print()

    # 9. Demonstrate cross-toolset linking via agent
    print("Step 9: Demonstrating cross-toolset linking via agent...")
    if self_ask_storage.final_answers and tot_storage.nodes:
        final_answer_id = list(self_ask_storage.final_answers.keys())[0]
        node_id = list(tot_storage.nodes.keys())[0]
        
        try:
            link_prompt = f"Link the self-ask final answer {final_answer_id} to the tree node {node_id} as exploring that architectural approach"
            link_result = await agent.run(link_prompt)
            print("✓ Cross-toolset link created via agent")
            print(f"  Response: {link_result.data[:200]}..." if len(link_result.data) > 200 else f"  Response: {link_result.data}")
            print()
        except Exception as e:
            print(f"⚠ Error creating link via agent: {e}")
            # Fallback: manually create link for demonstration
            link = CrossToolsetLink(
                link_id="example_link_4",
                source_toolset_id="self_ask",
                source_item_id=final_answer_id,
                target_toolset_id="tot",
                target_item_id=node_id,
                link_type=LinkType.EXPLORES,
                created_at=time.time(),
            )
            orchestrator_storage.create_link(link)
            print("✓ Cross-toolset link created manually (fallback)")
            print(f"  {link.source_toolset_id}:{link.source_item_id} → {link.target_toolset_id}:{link.target_item_id} ({link.link_type.value})")
            print()

    # 10. Demonstrate toolset transitions
    print("Step 10: Demonstrating toolset transitions...")
    try:
        transition_result = await agent.run("Suggest the next toolset transition based on current workflow state")
        print("✓ Toolset transition suggested via agent")
        print(f"  Response: {transition_result.data}..." if len(transition_result.data) > 200 else f"  Response: {transition_result.data}")
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
        print(f"Current Stage: {active_workflow.current_stage + 1}/{len(CODE_ARCHITECT.stages)}")
        print(f"Total Links: {len(orchestrator_storage.links)}")
    print()

    print("=" * 70)
    print("Example completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
