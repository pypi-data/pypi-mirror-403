# Discovery Flow (Mandatory)

Before creating or editing ANY workflow, you MUST follow this discovery flow. Never assume what's available.

## Why Discovery Matters

The Pulse platform is dynamic:
- Different instances have different models configured
- Tool providers vary by workspace
- Datasets are user-specific
- Node types may have custom configurations

## Step 1: Select or Create App

```
# List available apps
list_apps(mode="workflow")

# Select an existing app
select_app(app_id="...")

# OR create a new app
create_app(name="My Workflow", mode="workflow")
```

## Step 2: Discover Node Types

```
# Get all available node types
list_node_types()
```

Returns node types with their default configurations. Common types:
- `start` - Entry point (required)
- `end` / `answer` - Exit points
- `llm` - Language model processing
- `code` - Python/JavaScript execution
- `knowledge-retrieval` - RAG retrieval
- `http-request` - External API calls
- `tool` - External tool integrations
- `if-else` - Conditional branching

## Step 3: Get Node Schema Before Using

For EVERY node type you plan to use:

```
# Get detailed schema
get_node_schema(block_type="llm")
get_node_schema(block_type="knowledge-retrieval")
get_node_schema(block_type="code")
```

The schema tells you:
- Required fields
- Optional fields with defaults
- Input/output variable definitions
- Connection rules (handles)

## Step 4: Discover Resources

### For LLM Nodes
```
# Get available models
list_models(model_type="llm")
```

Returns models grouped by provider (openai, anthropic, etc.)

### For Knowledge Retrieval Nodes
```
# Get available datasets
list_datasets()
```

Returns knowledge bases with IDs and document counts.

### For Tool Nodes
```
# Get tool providers
list_tool_providers()

# Get tools from a provider
list_tools(provider_id="...")
```

## Step 5: View Current State

```
# See current workflow structure
view_workflow()
```

Shows:
- All nodes with IDs, types, titles
- All edges/connections
- Current hash for sync

## Complete Discovery Example

```python
# 1. Select app
list_apps(mode="workflow")
select_app(app_id="abc123")

# 2. Discover capabilities
list_node_types()                           # What nodes exist?
get_node_schema(block_type="llm")           # How to configure LLM?
get_node_schema(block_type="knowledge-retrieval")  # How to configure RAG?
list_models(model_type="llm")               # What models available?
list_datasets()                             # What knowledge bases?

# 3. View current state
view_workflow()

# NOW you can safely build the workflow
```

## Anti-Patterns (Don't Do This)

```python
# BAD: Adding node without checking schema
add_node(
    node_type="llm",
    config={"model": {"provider": "openai", "name": "gpt-4"}}  # Assuming model exists!
)

# BAD: Hardcoding dataset ID
add_node(
    node_type="knowledge-retrieval",
    config={"dataset_ids": ["hardcoded-id"]}  # Dataset may not exist!
)

# BAD: Skipping discovery
add_node(node_type="custom-tool")  # Tool may not be available!
```

## Correct Pattern

```python
# GOOD: Discovery first
models = list_models(model_type="llm")
# Find the model you want from the response

schema = get_node_schema(block_type="llm")
# Use schema defaults, override only what's needed

add_node(
    node_type="llm",
    config={
        "model": {
            "provider": discovered_provider,
            "name": discovered_model
        }
        # Other fields use schema defaults
    }
)
```
