"""Example: Creative Problem Solver workflow combining Multi-Persona Analysis, Graph of Thoughts, and Reflection.

This example demonstrates:
- Workflow initialization using CREATIVE_PROBLEM_SOLVER template
- Toolset combination with automatic prefixing
- Cross-toolset linking
- Unified state reading
- Workflow progression tracking
"""

from __future__ import annotations

import asyncio
import time

from pydantic_ai_toolsets import (
    CREATIVE_PROBLEM_SOLVER,
    GoTStorage,
    MetaOrchestratorStorage,
    PersonaStorage,
    ReflectionStorage,
    create_got_toolset,
    create_persona_toolset,
    create_reflection_toolset,
)
from pydantic_ai_toolsets.toolsets.meta_orchestrator.helpers import (
    create_workflow_agent,
    register_toolsets_with_orchestrator,
)
from pydantic_ai_toolsets.toolsets.meta_orchestrator.types import (
    CrossToolsetLink,
    LinkType,
    WorkflowState,
)


async def main() -> None:
    """Run Creative Problem Solver workflow example."""
    print("=" * 70)
    print("Creative Problem Solver Workflow Example")
    print("=" * 70)
    print()

    # 1. Create storages for all toolsets
    print("Step 1: Creating storages...")
    persona_storage = PersonaStorage(track_usage=True)
    got_storage = GoTStorage(track_usage=True)
    reflection_storage = ReflectionStorage(track_usage=True)
    orchestrator_storage = MetaOrchestratorStorage(track_usage=True)
    print("✓ Storages created")
    print()

    # 2. Create toolsets
    print("Step 2: Creating toolsets...")
    persona_toolset = create_persona_toolset(persona_storage, id="persona")
    got_toolset = create_got_toolset(got_storage, id="got")
    reflection_toolset = create_reflection_toolset(reflection_storage, id="reflection")
    orchestrator_toolset = create_meta_orchestrator_toolset(orchestrator_storage, id="orchestrator")
    print("✓ Toolsets created")
    print()

    # 3. Define prefix map for aliasing
    print("Step 3: Setting up prefix mapping...")
    prefix_map = {
        "persona": "persona_",
        "got": "got_",
        "reflection": "reflection_",
    }
    storages_map = {
        "persona": persona_storage,
        "got": got_storage,
        "reflection": reflection_storage,
    }
    print("✓ Prefix map configured")
    print(f"  Tools will be prefixed: {prefix_map}")
    print()

    # 4. Register toolsets with orchestrator
    print("Step 4: Registering toolsets with orchestrator...")
    register_toolsets_with_orchestrator(
        orchestrator_storage=orchestrator_storage,
        toolsets=[persona_toolset, got_toolset, reflection_toolset],
        storages=storages_map,
    )
    print("✓ Toolsets registered")
    print()

    # 5. Create agent with workflow template using convenience function
    print("Step 5: Creating agent with workflow template...")
    agent = create_workflow_agent(
        model="openrouter:openai/gpt-4o-mini",
        workflow_template=CREATIVE_PROBLEM_SOLVER,
        toolsets=[persona_toolset, got_toolset, reflection_toolset],
        storages=storages_map,
        prefix_map=prefix_map,
        orchestrator_storage=orchestrator_storage,
        auto_prefix=True,
    )
    print("✓ Agent created with workflow template")
    print(f"  Workflow: {CREATIVE_PROBLEM_SOLVER.name}")
    print(f"  Stages: {len(CREATIVE_PROBLEM_SOLVER.stages)}")
    print()

    # 6. Demonstrate workflow initialization via agent
    print("Step 6: Initializing workflow via agent...")
    try:
        init_result = await agent.run("Start the creative problem solver workflow")
        print("✓ Workflow initialized via agent")
        print(f"  Response: {init_result.data}..." if len(init_result.data) > 200 else f"  Response: {init_result.data}")
        print()
    except Exception as e:
        print(f"⚠ Error initializing workflow: {e}")
        print("(This is expected if API keys are not configured)")
        print()

    # 7. Run example query
    print("Step 7: Running example query...")
    query = "How can we reduce plastic waste in oceans? Explore multiple perspectives and synthesize solutions."
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
    if persona_storage.personas and got_storage.nodes:
        persona_id = list(persona_storage.personas.keys())[0]
        node_id = list(got_storage.nodes.keys())[0]
        
        try:
            link_prompt = f"Link the persona {persona_id} to the graph node {node_id} as exploring that perspective"
            link_result = await agent.run(link_prompt)
            print("✓ Cross-toolset link created via agent")
            print(f"  Response: {link_result.data}..." if len(link_result.data) > 200 else f"  Response: {link_result.data}")
            print()
        except Exception as e:
            print(f"⚠ Error creating link via agent: {e}")
            # Fallback: manually create link for demonstration
            link = CrossToolsetLink(
                link_id="example_link_2",
                source_toolset_id="persona",
                source_item_id=persona_id,
                target_toolset_id="got",
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
        print(f"Current Stage: {active_workflow.current_stage + 1}/{len(CREATIVE_PROBLEM_SOLVER.stages)}")
        print(f"Total Links: {len(orchestrator_storage.links)}")
    print()

    print("=" * 70)
    print("Example completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
