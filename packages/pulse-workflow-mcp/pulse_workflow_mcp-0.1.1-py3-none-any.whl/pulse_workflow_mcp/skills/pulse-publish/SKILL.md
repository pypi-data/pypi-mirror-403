---
name: pulse-publish
description: Validate and publish Pulse workflows using MCP tools. Checks for errors, warnings, and best practices before publishing. Triggers on /pulse-publish, "publish workflow", "deploy workflow", "release workflow", "validate workflow", or requests to make workflow changes live.
---

# Publish Pulse Workflow

Validate and publish workflow with proper checks.

## Usage

```
/pulse-publish
/pulse-publish v1.0 "Initial release"
```

## Publish Process

### Step 1: Ensure Correct App Selected

```python
# Verify you're working with the right app
list_apps(mode="workflow")
select_app(app_id="target-app-id")
```

### Step 2: Review Current State

```python
# View the complete workflow
view_workflow(include_details=True)

# Quick summary
nodes = list_nodes()
edges = list_edges()
print(f"Nodes: {len(nodes)}, Edges: {len(edges)}")
```

### Step 3: Run Validation

**ALWAYS validate before publishing.**

```python
result = validate_workflow()

print(f"Valid: {result['valid']}")
print(f"Nodes: {result['node_count']}")
print(f"Edges: {result['edge_count']}")

if result["errors"]:
    print("\n❌ ERRORS (must fix):")
    for error in result["errors"]:
        print(f"  - [{error['type']}] {error['message']}")

if result["warnings"]:
    print("\n⚠️ WARNINGS (review):")
    for warning in result["warnings"]:
        print(f"  - [{warning['type']}] {warning['message']}")
```

### Step 4: Fix Any Issues

#### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `missing_start` | No start node | Add start node (usually auto-created) |
| `multiple_starts` | Multiple start nodes | Delete extra start nodes |
| `invalid_edge` | Edge references non-existent node | Remove orphan edges or add missing node |

#### Common Warnings

| Warning | Cause | Fix |
|---------|-------|-----|
| `missing_end` | No end/answer node | Add answer or end node |
| `disconnected_node` | Node not connected to flow | Connect node or delete if unused |

#### Fixing Disconnected Nodes

```python
# Find disconnected node
nodes = list_nodes()
edges = list_edges()

connected_ids = set()
for edge in edges:
    connected_ids.add(edge["source"])
    connected_ids.add(edge["target"])

for node in nodes:
    node_type = node["data"]["type"]
    if node_type not in ("start", "end", "answer"):
        if node["id"] not in connected_ids:
            print(f"Disconnected: {node['data']['title']} ({node['id']})")
            # Either connect or delete
            # connect_nodes(source_id="...", target_id=node["id"])
            # OR delete_node(node_id=node["id"])
```

### Step 5: Publish

Once validation passes:

```python
# Publish with version info
result = publish_workflow(
    name="v1.0",           # Optional: version name (max 20 chars)
    comment="Description"  # Optional: version comment (max 100 chars)
)

print(f"Published at: {result['created_at']}")
```

## Pre-Publish Checklist

Before publishing, verify:

### Structure
- [ ] Has exactly one `start` node
- [ ] Has at least one `answer` or `end` node
- [ ] All nodes are connected to the flow
- [ ] No orphan edges

### Configuration
- [ ] LLM nodes have valid models (from `list_models()`)
- [ ] Knowledge retrieval has valid datasets (from `list_datasets()`)
- [ ] HTTP requests have valid URLs
- [ ] Code nodes have valid syntax

### Testing
- [ ] Critical nodes tested with `run_node()`
- [ ] Expected outputs verified

### Best Practices
- [ ] Meaningful node titles
- [ ] Error handling for external calls
- [ ] Reasonable timeouts for HTTP requests

## Testing Before Publish

Test individual nodes:

```python
# Test an LLM node
result = run_node(
    node_id="llm-node-id",
    inputs={},
    query="Test question"
)
print(f"Status: {result['status']}")
print(f"Output: {result['outputs']}")

# Test a code node
result = run_node(
    node_id="code-node-id",
    inputs={"test_var": "test_value"}
)
```

## Version Management

### Naming Conventions

Use semantic versioning:
- `v1.0` - Major release
- `v1.1` - Minor update
- `v1.1-hotfix` - Bug fix

### Version Comments

Be descriptive:
- ✅ "Added RAG for product docs, improved error handling"
- ✅ "Fixed timeout issue in API calls"
- ❌ "Updated"
- ❌ "Changes"

## Post-Publish

After publishing:

1. **Test the published version** in the Pulse UI
2. **Monitor** for errors in production
3. **Keep draft updated** - continue editing draft for next version

## Rollback

If issues occur after publish:
1. The previous version remains available in Pulse
2. Use Pulse UI to rollback to previous version
3. Or fix issues and publish new version via MCP

## Error Handling

### Publish Fails

If publish fails:
```python
# Re-validate
validate_workflow()

# Check for sync issues (concurrent edits)
view_workflow()  # Get latest hash
```

### WorkflowNotSyncError

Workflow was modified elsewhere:
```python
# Fetch latest state
view_workflow()

# Re-apply your changes if needed
# Then try publish again
```

## References

For detailed information:
- [MCP Tools](../pulse/references/mcp-tools.md) - Complete tool reference
- [Examples](../pulse/references/examples.md) - Common patterns
