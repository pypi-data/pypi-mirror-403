---
name: pulse-create
description: Create Pulse workflows from natural language descriptions using MCP tools. Handles discovery, app creation, node configuration, and connections. Triggers on /pulse-create, "create workflow", "build workflow", "new pulse app", or requests to build AI pipelines, chatbots, RAG systems, or automation workflows.
---

# Create Pulse Workflow

Build a complete workflow from a description. Uses discovery-first approach.

## Usage

```
/pulse-create <description>
```

Example:
```
/pulse-create customer support chatbot with knowledge base
/pulse-create RAG pipeline for product documentation
/pulse-create API integration that fetches weather data
```

## Workflow Creation Process

### Phase 1: Discovery (MANDATORY)

Before creating anything, discover available capabilities:

```python
# 1. List/select or create app
list_apps(mode="workflow")
# If existing app: select_app(app_id="...")
# If new: create_app(name="<from description>", mode="workflow")

# 2. Discover what's available
list_node_types()                    # Available node types
list_models(model_type="llm")        # Available AI models
list_datasets()                      # Available knowledge bases (if RAG needed)
list_tool_providers()                # Available tools (if integrations needed)

# 3. Get schemas for nodes you'll use
get_node_schema(block_type="llm")
get_node_schema(block_type="knowledge-retrieval")  # if RAG
get_node_schema(block_type="http-request")         # if API
get_node_schema(block_type="code")                 # if transform
```

### Phase 2: Plan the Workflow

Based on the description, identify:

1. **Entry point**: Always `start` node (usually exists)
2. **Processing nodes**: What processing is needed?
   - Simple chat → `llm`
   - RAG → `knowledge-retrieval` → `llm`
   - Classification → `question-classifier` → branches
   - API call → `http-request` → `code` (transform)
3. **Exit point**: `answer` (chat) or `end` (return data)

### Phase 3: Build Incrementally

**Critical Rule**: Add ONE node at a time, verify, then continue.

```python
# Get current state
view_workflow()
nodes = list_nodes()
start_id = <find start node id>

# Add first processing node
result = add_node(
    node_type="...",
    title="...",
    config={...},  # From schema, use defaults where possible
    after_node_id=start_id
)
node1_id = result["node_id"]

# Verify it was added
view_workflow()

# Add second node
result = add_node(
    node_type="...",
    config={...},
    after_node_id=node1_id
)
node2_id = result["node_id"]

# Continue until complete...

# Add answer/end node
add_node(
    node_type="answer",
    config={"answer": "{{#<last_node_id>.output#}}"},
    after_node_id=node2_id
)
```

### Phase 4: Validate

```python
result = validate_workflow()
if not result["valid"]:
    # Fix errors
    for error in result["errors"]:
        print(error["message"])
```

## Common Workflow Patterns

### Simple Chatbot
```
start → llm → answer
```

### RAG Chatbot
```
start → knowledge-retrieval → llm (with context) → answer
```

### Intent Router
```
start → question-classifier → [branch1: llm] → answer
                            → [branch2: llm] → answer
```

### API Integration
```
start → http-request → code (transform) → answer
```

### Multi-step Processing
```
start → llm (extract) → code (process) → llm (respond) → answer
```

## Configuration Tips

### LLM Node
- Always get model from `list_models()`, don't assume
- Use `{{#sys.query#}}` for user input
- Enable `context` if using with knowledge retrieval
- Enable `memory` for conversation history

### Knowledge Retrieval
- Get dataset_ids from `list_datasets()`
- Set appropriate `top_k` (3-5 for most cases)
- Use `score_threshold` to filter low-quality results

### HTTP Request
- Store API keys in environment variables: `{{#env.API_KEY#}}`
- Set reasonable `timeout` (30s default)
- Use code node to transform response

### Code Node
- Use for data transformation
- Define clear `inputs` and `outputs`
- Test with `run_node()` before connecting

## Error Handling

If `add_node` fails:
1. Check node type exists: `list_node_types()`
2. Check schema: `get_node_schema(block_type)`
3. Check source node exists: `list_nodes()`

If connection fails:
1. Check both nodes exist
2. Check handle names (use schema)
3. View current edges: `list_edges()`

## References

For detailed information:
- [Discovery Flow](../pulse/references/discovery-flow.md)
- [Node Types](../pulse/references/node-types.md)
- [MCP Tools](../pulse/references/mcp-tools.md)
- [Examples](../pulse/references/examples.md)
