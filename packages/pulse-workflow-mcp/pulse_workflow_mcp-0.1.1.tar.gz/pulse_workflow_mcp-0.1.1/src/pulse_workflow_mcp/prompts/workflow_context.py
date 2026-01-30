"""MCP prompts for Dify workflow context."""

import json

from mcp.server import Server
from mcp.types import GetPromptResult, Prompt, PromptArgument, PromptMessage, TextContent

from ..dify_client import get_client
from ..resources.node_types import NODE_CATEGORIES, NODE_TYPES_SCHEMA


def register_workflow_prompts(server: Server) -> None:
    """Register workflow prompts with the MCP server."""

    @server.list_prompts()
    async def list_prompts() -> list[Prompt]:
        return [
            Prompt(
                name="workflow_context",
                description="Get full context about the current workflow for understanding and modifications",
                arguments=[
                    PromptArgument(
                        name="include_node_schemas",
                        description="Include node type schemas (default: false)",
                        required=False,
                    ),
                ],
            ),
            Prompt(
                name="discovery_workflow",
                description="Get the mandatory discovery workflow for building Pulse workflows from scratch",
                arguments=[],
            ),
            Prompt(
                name="add_rag_pipeline",
                description="Template for adding a RAG (Retrieval Augmented Generation) pipeline",
                arguments=[
                    PromptArgument(
                        name="dataset_id",
                        description="ID of the knowledge base to use",
                        required=True,
                    ),
                ],
            ),
            Prompt(
                name="add_llm_chain",
                description="Template for adding an LLM processing chain",
                arguments=[
                    PromptArgument(
                        name="provider",
                        description="Model provider (e.g., openai, anthropic)",
                        required=False,
                    ),
                    PromptArgument(
                        name="model",
                        description="Model name (e.g., gpt-4, claude-3-opus)",
                        required=False,
                    ),
                ],
            ),
        ]

    @server.get_prompt()
    async def get_prompt(name: str, arguments: dict[str, str] | None = None) -> GetPromptResult:
        arguments = arguments or {}

        if name == "workflow_context":
            return await _get_workflow_context_prompt(arguments)
        elif name == "discovery_workflow":
            return _get_discovery_workflow_prompt()
        elif name == "add_rag_pipeline":
            return _get_rag_pipeline_prompt(arguments)
        elif name == "add_llm_chain":
            return _get_llm_chain_prompt(arguments)

        raise ValueError(f"Unknown prompt: {name}")


async def _get_workflow_context_prompt(arguments: dict[str, str]) -> GetPromptResult:
    """Generate workflow context prompt."""
    client = get_client()
    workflow = await client.get_workflow()

    graph = workflow.get("graph", {"nodes": [], "edges": []})
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    features = workflow.get("features", {})

    context = "# Current Workflow Context\n\n"

    context += "## Overview\n\n"
    context += f"- **Hash:** `{workflow.get('hash', 'N/A')[:12]}...`\n"
    context += f"- **Nodes:** {len(nodes)}\n"
    context += f"- **Edges:** {len(edges)}\n\n"

    context += "## Nodes\n\n"
    for node in nodes:
        node_data = node.get("data", {})
        node_type = node_data.get("type", "unknown")
        title = node_data.get("title", "Untitled")
        context += f"### {title}\n"
        context += f"- **ID:** `{node['id']}`\n"
        context += f"- **Type:** `{node_type}`\n"
        pos = node.get("position", {})
        if pos:
            context += f"- **Position:** ({pos.get('x', 0)}, {pos.get('y', 0)})\n"

        config_keys = [k for k in node_data if k not in ("type", "title")]
        if config_keys:
            context += f"- **Config keys:** {', '.join(config_keys)}\n"
        context += "\n"

    context += "## Connections\n\n"
    node_titles = {n["id"]: n.get("data", {}).get("title", n["id"][:8]) for n in nodes}
    for edge in edges:
        source = node_titles.get(edge["source"], edge["source"][:8])
        target = node_titles.get(edge["target"], edge["target"][:8])
        context += f"- {source} → {target}\n"

    context += "\n## Features\n\n"
    context += f"```json\n{json.dumps(features, indent=2)}\n```\n"

    if arguments.get("include_node_schemas", "false").lower() == "true":
        context += "\n## Available Node Types\n\n"
        for category in NODE_CATEGORIES.values():
            context += f"### {category['name']}\n"
            context += f"{category['description']}\n\n"
            for node_type in category["nodes"]:
                if node_type in NODE_TYPES_SCHEMA:
                    schema = NODE_TYPES_SCHEMA[node_type]
                    context += f"- **{schema['name']}** (`{node_type}`): {schema['description']}\n"
            context += "\n"

    context += "\n## Instructions\n\n"
    context += """### CRITICAL RULES
1. NEVER assume available nodes, plugins, models, or configs.
2. ALWAYS discover capabilities at runtime using MCP tools.
3. NEVER hardcode node schemas or plugin-specific fields.
4. Use PATCH-style updates for node configuration (only change what is needed).
5. Validate workflows before publishing.
6. Prefer minimal, correct actions over bulk edits.

### DISCOVERY FLOW (MANDATORY)
Before creating or editing anything:
1. Call `list_node_types()` to discover available nodes.
2. For any node you plan to use, call `get_node_schema(block_type)` first.
3. Use schema defaults unless the user explicitly requests changes.

### WORKFLOW CREATION FLOW
When asked to create a workflow:
1. Call `create_app(name, mode)` if starting fresh
2. Call `list_node_types()` to see available node types
3. Call `get_node_schema(type)` for each node type you'll use
4. Add nodes one by one using `add_node(node_type, config, after_node_id)`
5. Connect nodes using `connect_nodes(source_id, target_id)`
6. Call `validate_workflow()`
7. Only publish after validation succeeds with `publish_workflow()`

### CONFIGURING NODES
- Call `list_models()` to discover available LLM models before configuring LLM nodes
- Call `list_datasets()` to discover knowledge bases before configuring knowledge-retrieval nodes
- Call `list_tool_providers()` and `list_tools(provider_id)` to discover available tools

Node IDs are UUIDs. When connecting nodes, reference them by their full ID."""

    return GetPromptResult(
        description="Current workflow context and modification guide",
        messages=[
            PromptMessage(
                role="user",
                content=TextContent(type="text", text=context),
            )
        ],
    )


def _get_discovery_workflow_prompt() -> GetPromptResult:
    """Generate discovery workflow instructions prompt."""
    template = """# Pulse Workflow MCP - Discovery Workflow

## GOAL
MCP can do everything a human can do in the Pulse workflow UI:
- Create workflows
- Add / edit / delete nodes
- Connect and disconnect edges
- Configure node settings
- Validate and publish workflows

## CRITICAL RULES
1. **NEVER** assume available nodes, plugins, models, or configs.
2. **ALWAYS** discover capabilities at runtime using MCP tools.
3. **NEVER** hardcode node schemas or plugin-specific fields.
4. Use **PATCH-style updates** for node configuration (only change what is needed).
5. **Validate workflows** before publishing.
6. Prefer **minimal, correct actions** over bulk edits.

## DISCOVERY FLOW (MANDATORY)

Before creating or editing anything:

### Step 1: Discover Available Node Types
```
list_node_types()
```
Returns all available node types with their default configurations.

### Step 2: Get Node Schema Before Using
```
get_node_schema(block_type="llm")
get_node_schema(block_type="code")
get_node_schema(block_type="knowledge-retrieval")
```
Returns the complete schema including:
- Required and optional fields
- Default values
- Input/output variable definitions
- Connection rules

### Step 3: Discover Resources
```
# For LLM nodes - discover available models
list_models(model_type="llm")

# For knowledge-retrieval nodes - discover datasets
list_datasets()

# For tool nodes - discover available tools
list_tool_providers()
list_tools(provider_id="...")
```

## WORKFLOW CREATION FLOW

When asked to create a workflow:

### 1. Create App (if needed)
```
create_app(name="My Workflow", mode="workflow")
```

### 2. Or Select Existing App
```
list_apps(mode="workflow")
select_app(app_id="...")
```

### 3. View Current State
```
view_workflow()
```

### 4. Add Nodes One by One
```
# Get schema first
get_node_schema(block_type="llm")

# Then add with proper config
add_node(
    node_type="llm",
    title="My LLM",
    config={...},  # Use schema defaults, override only what's needed
    after_node_id="start-node-id"
)
```

### 5. Connect Nodes
```
connect_nodes(source_id="...", target_id="...")
```

### 6. Validate
```
validate_workflow()
```

### 7. Publish (only after validation succeeds)
```
publish_workflow(name="v1.0", comment="Initial version")
```

## CONFIGURING NODES

### LLM Node
```
# First discover models
list_models(model_type="llm")

# Then get schema
get_node_schema(block_type="llm")

# Add with discovered model
add_node(
    node_type="llm",
    config={
        "model": {
            "provider": "openai",
            "name": "gpt-4",
            "mode": "chat"
        },
        "prompt_template": [...]
    }
)
```

### Knowledge Retrieval Node
```
# First discover datasets
list_datasets()

# Then get schema
get_node_schema(block_type="knowledge-retrieval")

# Add with discovered dataset
add_node(
    node_type="knowledge-retrieval",
    config={
        "dataset_ids": ["discovered-dataset-id"],
        "retrieval_mode": "multiple"
    }
)
```

### Tool Node
```
# First discover tools
list_tool_providers()
list_tools(provider_id="...")

# Then get schema
get_node_schema(block_type="tool")

# Add with discovered tool
add_node(
    node_type="tool",
    config={
        "provider_id": "...",
        "tool_name": "...",
        "tool_parameters": {...}
    }
)
```

## EDITING NODES

Use PATCH-style updates - only specify fields you want to change:

```
# First get current node state
get_node(node_id="...")

# Then update only what's needed
edit_node(
    node_id="...",
    config={
        "model": {"name": "gpt-4-turbo"}  # Only changing model name
    }
)
```

## AVAILABLE TOOLS REFERENCE

### App Operations
- `list_apps(mode?, name?, limit?)` - List available apps
- `select_app(app_id)` - Select app for subsequent operations
- `create_app(name, mode?, description?, icon?)` - Create new app

### Discovery
- `list_node_types(app_id?)` - List all available node types
- `get_node_schema(block_type, app_id?)` - Get detailed node schema
- `list_tool_providers()` - List available tool providers
- `list_tools(provider_id?, tool_type?)` - List tools from provider
- `list_models(model_type?)` - List available AI models
- `list_datasets(limit?)` - List knowledge base datasets

### Node Operations
- `add_node(node_type, title?, config?, position?, after_node_id?)` - Add node
- `edit_node(node_id, title?, config?, position?)` - Edit node
- `delete_node(node_id)` - Delete node
- `get_node(node_id)` - Get node details
- `list_nodes(filter_type?)` - List all nodes

### Edge Operations
- `connect_nodes(source_id, target_id, source_handle?, target_handle?)` - Create edge
- `disconnect_nodes(source_id, target_id, source_handle?, target_handle?)` - Remove edge
- `list_edges()` - List all edges

### Workflow Operations
- `view_workflow(app_id?, include_details?)` - View workflow structure
- `validate_workflow()` - Validate for errors
- `publish_workflow(name?, comment?)` - Publish draft
- `run_node(node_id, inputs?, query?)` - Test single node

### Features & Variables
- `get_features()` - Get workflow features
- `update_features(...)` - Update features
- `get_variables()` - Get workflow variables
"""

    return GetPromptResult(
        description="Mandatory discovery workflow for building Pulse workflows",
        messages=[
            PromptMessage(
                role="user",
                content=TextContent(type="text", text=template),
            )
        ],
    )


def _get_rag_pipeline_prompt(arguments: dict[str, str]) -> GetPromptResult:
    """Generate RAG pipeline template prompt."""
    dataset_id = arguments.get("dataset_id", "<DATASET_ID>")

    template = f"""# Add RAG Pipeline

To add a RAG (Retrieval Augmented Generation) pipeline to this workflow:

## Step 1: Add Knowledge Retrieval Node

```
add_node(
    node_type="knowledge-retrieval",
    title="Knowledge Retrieval",
    config={{
        "query_variable_selector": ["start", "sys.query"],
        "dataset_ids": ["{dataset_id}"],
        "retrieval_mode": "multiple",
        "multiple_retrieval_config": {{
            "top_k": 5,
            "score_threshold": 0.5
        }}
    }},
    after_node_id="<START_NODE_ID>"
)
```

## Step 2: Add LLM Node with Context

```
add_node(
    node_type="llm",
    title="RAG Response",
    config={{
        "model": {{
            "provider": "openai",
            "name": "gpt-4",
            "mode": "chat"
        }},
        "prompt_template": [
            {{
                "role": "system",
                "text": "You are a helpful assistant. Use the following context to answer the user's question:\\n\\n{{{{#context#}}}}"
            }},
            {{
                "role": "user",
                "text": "{{{{#sys.query#}}}}"
            }}
        ],
        "context": {{
            "enabled": true,
            "variable_selector": ["<KNOWLEDGE_NODE_ID>", "result"]
        }}
    }},
    after_node_id="<KNOWLEDGE_NODE_ID>"
)
```

## Step 3: Connect to Answer/End Node

```
connect_nodes(
    source_id="<LLM_NODE_ID>",
    target_id="<END_NODE_ID>"
)
```

Replace the placeholder IDs with actual node IDs from the workflow."""

    return GetPromptResult(
        description="Template for adding a RAG pipeline",
        messages=[
            PromptMessage(
                role="user",
                content=TextContent(type="text", text=template),
            )
        ],
    )


def _get_llm_chain_prompt(arguments: dict[str, str]) -> GetPromptResult:
    """Generate LLM chain template prompt."""
    provider = arguments.get("provider", "openai")
    model = arguments.get("model", "gpt-4")

    template = f"""# Add LLM Processing Chain

To add an LLM node for processing:

## Basic LLM Node

```
add_node(
    node_type="llm",
    title="LLM Processor",
    config={{
        "model": {{
            "provider": "{provider}",
            "name": "{model}",
            "mode": "chat",
            "completion_params": {{
                "temperature": 0.7,
                "max_tokens": 2000
            }}
        }},
        "prompt_template": [
            {{
                "role": "system",
                "text": "You are a helpful assistant."
            }},
            {{
                "role": "user",
                "text": "{{{{#sys.query#}}}}"
            }}
        ]
    }},
    after_node_id="<PREVIOUS_NODE_ID>"
)
```

## LLM with Memory (Conversation History)

```
add_node(
    node_type="llm",
    title="Chat LLM",
    config={{
        "model": {{
            "provider": "{provider}",
            "name": "{model}",
            "mode": "chat"
        }},
        "prompt_template": [
            {{
                "role": "system",
                "text": "You are a helpful assistant."
            }},
            {{
                "role": "user",
                "text": "{{{{#sys.query#}}}}"
            }}
        ],
        "memory": {{
            "role_prefix": {{
                "user": "User",
                "assistant": "Assistant"
            }},
            "window": {{
                "enabled": true,
                "size": 10
            }}
        }}
    }},
    after_node_id="<PREVIOUS_NODE_ID>"
)
```

## LLM with Vision (Image Input)

```
add_node(
    node_type="llm",
    title="Vision LLM",
    config={{
        "model": {{
            "provider": "{provider}",
            "name": "{model}",
            "mode": "chat"
        }},
        "prompt_template": [
            {{
                "role": "user",
                "text": "Describe this image: {{{{#sys.files#}}}}"
            }}
        ],
        "vision": {{
            "enabled": true
        }}
    }},
    after_node_id="<PREVIOUS_NODE_ID>"
)
```

Replace placeholder IDs with actual node IDs from the workflow."""

    return GetPromptResult(
        description="Template for adding an LLM processing chain",
        messages=[
            PromptMessage(
                role="user",
                content=TextContent(type="text", text=template),
            )
        ],
    )
