---
name: 03_cross_toolset_linking
overview: Implement cross-toolset linking infrastructure to create references between outputs of different toolsets
todos:
  - id: linking-infrastructure
    content: Create _shared/linking.py with LinkManager for cross-toolset references
    status: pending
  - id: update-storage-classes
    content: Add link tracking to existing storage classes (optional links and linked_from fields)
    status: pending
---

# Cross-Toolset Linking Infrastructure

This plan covers Phase 2: Cross-Toolset Linking.

## Files to Create

### 1. Linking Infrastructure

**File**: `pydantic_ai_toolsets/toolsets/_shared/linking.py`

- `LinkManager` class to manage cross-toolset references
- Methods:
- `create_link(source_toolset, source_id, target_toolset, target_id, link_type)`
- `get_links(toolset_id, item_id)` - get all links for an item
- `resolve_link(link_id)` - get linked item content

- Link types: `refines`, `explores`, `synthesizes`, `references`

### 2. Update Storage Classes

**Files**: All storage classes in `pydantic_ai_toolsets/toolsets/*/storage.py`

Add optional link tracking:

- Add `links: dict[str, list[str]]` to track outgoing links
- Add `linked_from: list[str]` to track incoming links
- Update storage protocols to include link methods

## Dependencies

- None (standalone infrastructure)

## Related Plans

- See `01_core_infrastructure.md` for meta-orchestrator that uses links
- See `04_unified_state.md` for unified state that shows links