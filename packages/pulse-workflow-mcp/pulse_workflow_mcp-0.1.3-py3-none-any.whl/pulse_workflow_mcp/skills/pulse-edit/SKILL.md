---
name: pulse-edit
description: Edit existing Pulse workflows using MCP tools. Modify nodes, update configurations, add/remove connections, restructure workflow flow. Triggers on /pulse-edit, "edit workflow", "modify workflow", "change node", "update workflow", "fix workflow", or requests to alter existing workflow behavior.
---

# Edit Pulse Workflow

Modify an existing workflow with PATCH-style updates.

## Usage

```
/pulse-edit
/pulse-edit <specific change description>
```

Examples:
```
/pulse-edit change the LLM model to Claude
/pulse-edit add error handling to the API call
/pulse-edit remove the classification step
/pulse-edit connect node X to node Y
```

## Edit Workflow Process

### Step 1: Understand Current State

Always start by viewing the current workflow:

```python
# Ensure correct app is selected
list_apps(mode="workflow")
select_app(app_id="...")

# View complete structure
view_workflow(include_details=True)

# List all nodes
list_nodes()

# List all connections
list_edges()
```

### Step 2: Identify Changes Needed

Based on the edit request, determine:

1. **Node modifications**: Change config, title, or position
2. **Node additions**: Add new nodes to the flow
3. **Node deletions**: Remove nodes (and their edges)
4. **Connection changes**: Add/remove edges between nodes
5. **Restructuring**: Reorder or reroute the flow

### Step 3: Apply PATCH-Style Updates

**Critical Rule**: Only change what needs to change. Don't recreate nodes unnecessarily.

## Common Edit Operations

### Modify Node Configuration

```python
# 1. Get current node state
node = get_node(node_id="target-node-id")

# 2. Get schema to understand options
get_node_schema(block_type=node["data"]["type"])

# 3. Apply PATCH update - only changed fields
edit_node(
    node_id="target-node-id",
    config={
        # Only include fields you're changing
        "model": {
            "name": "claude-3-opus"  # Just changing model name
        }
    }
)
```

### Change Node Title

```python
edit_node(
    node_id="target-node-id",
    title="New Descriptive Title"
)
```

### Update Node Position

```python
edit_node(
    node_id="target-node-id",
    position={"x": 300, "y": 150}
)
```

### Add a Node Between Existing Nodes

```python
# Current: A → B
# Desired: A → NEW → B

# 1. Find the edge to break
edges = list_edges()
edge_to_remove = <find A→B edge>

# 2. Remove old connection
disconnect_nodes(source_id="A", target_id="B")

# 3. Add new node
result = add_node(
    node_type="...",
    config={...},
    after_node_id="A"
)
new_node_id = result["node_id"]

# 4. Connect new node to B
connect_nodes(source_id=new_node_id, target_id="B")
```

### Remove a Node

```python
# delete_node automatically removes connected edges
delete_node(node_id="unwanted-node-id")

# If nodes were: A → UNWANTED → B
# You may need to reconnect A → B
connect_nodes(source_id="A", target_id="B")
```

### Add a Branch (Conditional)

```python
# Add if-else after a node
add_node(
    node_type="if-else",
    title="Check Condition",
    config={
        "conditions": [[{
            "variable_selector": ["previous_node", "output"],
            "comparison_operator": "contains",
            "value": "error"
        }]]
    },
    after_node_id="previous-node-id"
)

# Connect branches
connect_nodes(
    source_id="if-else-id",
    target_id="error-handler-id",
    source_handle="true"
)
connect_nodes(
    source_id="if-else-id",
    target_id="success-handler-id",
    source_handle="false"
)
```

### Rewire Connections

```python
# Remove existing connection
disconnect_nodes(source_id="A", target_id="B")

# Add new connection
connect_nodes(source_id="A", target_id="C")
```

### Update LLM Prompt

```python
# Get current config
node = get_node(node_id="llm-node-id")

# Update only the prompt
edit_node(
    node_id="llm-node-id",
    config={
        "prompt_template": [
            {"role": "system", "text": "Updated system prompt..."},
            {"role": "user", "text": "{{#sys.query#}}"}
        ]
    }
)
```

### Change Model Provider

```python
# First, discover available models
list_models(model_type="llm")

# Then update
edit_node(
    node_id="llm-node-id",
    config={
        "model": {
            "provider": "anthropic",
            "name": "claude-3-opus",
            "mode": "chat"
        }
    }
)
```

### Add Knowledge Base to Existing LLM

```python
# 1. Get available datasets
list_datasets()

# 2. Add knowledge retrieval node before LLM
# Find what connects to the LLM
edges = list_edges()
source_of_llm = <find edge where target is llm-node>

# 3. Insert knowledge node
disconnect_nodes(source_id=source_of_llm, target_id="llm-node-id")

add_node(
    node_type="knowledge-retrieval",
    config={
        "dataset_ids": ["discovered-dataset-id"],
        "query_variable_selector": ["sys", "query"]
    },
    after_node_id=source_of_llm
)

connect_nodes(source_id="knowledge-node-id", target_id="llm-node-id")

# 4. Update LLM to use context
edit_node(
    node_id="llm-node-id",
    config={
        "context": {
            "enabled": True,
            "variable_selector": ["knowledge-node-id", "result"]
        }
    }
)
```

## Verification After Edits

Always verify changes:

```python
# View updated workflow
view_workflow()

# Validate
result = validate_workflow()
if result["errors"]:
    print("Errors to fix:", result["errors"])
if result["warnings"]:
    print("Warnings:", result["warnings"])
```

## Testing Individual Nodes

Test a modified node before full workflow:

```python
run_node(
    node_id="modified-node-id",
    inputs={"test_input": "test value"},
    query="test query"
)
```

## Error Recovery

If edit causes issues:

1. **Check node exists**: `get_node(node_id)` returns null if deleted
2. **Check connections**: `list_edges()` to see current state
3. **Re-validate**: `validate_workflow()` to find problems
4. **View full state**: `view_workflow(include_details=True)`

## References

For detailed information:
- [Node Types](../pulse/references/node-types.md) - Node configuration options
- [MCP Tools](../pulse/references/mcp-tools.md) - Complete tool reference
- [Examples](../pulse/references/examples.md) - Common patterns
