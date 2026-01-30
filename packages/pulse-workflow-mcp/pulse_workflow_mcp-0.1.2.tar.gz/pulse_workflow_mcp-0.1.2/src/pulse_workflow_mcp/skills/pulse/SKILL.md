---
name: pulse
description: Main entry point for Pulse workflow development with MCP tools. Shows available commands and core concepts. Triggers on /pulse, "pulse workflow", "workflow help", or when user asks about Pulse workflow capabilities. Use this skill to understand the Pulse workflow system before creating, editing, or publishing workflows.
---

# Pulse Workflow Development

Build and manage Pulse (Dify) workflows using MCP tools directly from Claude Code.

## Available Commands

| Command | Description |
|---------|-------------|
| `/pulse` | This help - overview and concepts |
| `/pulse-create` | Create a new workflow from description |
| `/pulse-edit` | Edit an existing workflow |
| `/pulse-publish` | Validate and publish workflow |

## Quick Start

```
1. /pulse-create customer support chatbot with RAG
2. /pulse-edit                    # Make changes
3. /pulse-publish                 # Validate & publish
```

## Core Concepts

### Workflows
Workflows are visual pipelines of connected nodes that process user input and generate responses. Each workflow belongs to an **app**.

### Nodes
Processing units in a workflow:
- **Control**: start, end, answer, if-else, iteration, loop
- **AI**: llm, knowledge-retrieval, question-classifier, parameter-extractor
- **Transform**: code, template-transform, variable-assigner, variable-aggregator
- **External**: http-request, tool

### Edges
Connections between nodes defining data flow. Each edge connects a source node's output handle to a target node's input handle.

## MCP Tools Available

The `pulse-workflow` MCP server provides these tools:

### Discovery (ALWAYS use first)
- `list_node_types` - Get available node types
- `get_node_schema` - Get node configuration schema
- `list_models` - Get available AI models
- `list_datasets` - Get knowledge bases
- `list_tool_providers` / `list_tools` - Get external tools

### App Management
- `list_apps` - List available apps
- `select_app` - Select app to work with
- `create_app` - Create new app
- `initialize_workflow` - Initialize workflow for new app (auto-called by create_app)

### Workflow Operations
- `view_workflow` - See current structure
- `validate_workflow` - Check for errors
- `publish_workflow` - Publish draft

### Node Operations
- `add_node` - Add node to workflow
- `edit_node` - Modify node config
- `delete_node` - Remove node
- `get_node` / `list_nodes` - View nodes
- `batch_add_nodes` - Add multiple nodes in one call (efficient)

### Edge Operations
- `connect_nodes` - Create connection
- `disconnect_nodes` - Remove connection
- `list_edges` - View connections

### Knowledge Operations
- `get_dataset` - Get dataset details
- `list_documents` - List documents in a dataset
- `get_document` - Get document details
- `search_dataset` - Query/search a knowledge base

### Sticky Notes
- `add_note` - Add documentation note to canvas
- `edit_note` - Update note content/theme
- `list_notes` - List all sticky notes
- `delete_note` - Remove sticky note

### Features & Variables
- `get_features` - Get workflow feature config (opening statement, file upload, etc.)
- `update_features` - Update workflow features
- `get_variables` - Get environment and conversation variables

### Testing
- `run_node` - Execute single node for testing

## Critical Rules

1. **NEVER assume** available nodes, models, or tools - always discover first
2. **ALWAYS call** `list_node_types()` before adding nodes
3. **ALWAYS call** `get_node_schema(type)` before configuring a node
4. **Build incrementally** - one node at a time, validate each step
5. **Validate before publishing** - always run `validate_workflow()` first

## References

- [Discovery Flow](references/discovery-flow.md) - Mandatory discovery workflow
- [Node Types](references/node-types.md) - Available nodes and their configs
- [MCP Tools](references/mcp-tools.md) - Complete tool reference
- [Examples](references/examples.md) - Common workflow patterns
