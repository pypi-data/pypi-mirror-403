# MCP Tools Reference

Complete reference for Pulse Workflow MCP tools.

## Discovery Tools

### list_node_types
List all available node types.

```
list_node_types(app_id?)
```

**Parameters**:
- `app_id` (optional): App ID, uses selected app if not provided

**Returns**:
- `types`: Complete list of all node types (start, end, llm, agent, tool, etc.)
- `with_default_config`: Subset of types that have default configurations

**When to use**: Before adding any nodes to understand what's available

---

### get_node_schema
Get detailed schema for a specific node type.

```
get_node_schema(block_type, app_id?)
```

**Parameters**:
- `block_type` (required): Node type (e.g., "llm", "code", "http-request")
- `app_id` (optional): App ID

**Returns**:
- For nodes with default configs: Complete schema with all config options
- For complex nodes (agent, tool, etc.): Guidance note with required fields

**When to use**: Before configuring a node - ALWAYS call this first

**Note**: Some nodes (agent, tool, start, end, etc.) don't have default schemas. The response will include a guidance note explaining required configuration.

---

### list_tool_providers
List available tool/plugin providers.

```
list_tool_providers()
```

**Returns**: List of providers with:
- `id`: Provider ID (use for `list_tools` and agent configuration)
- `name`: Provider identifier
- `label`: Display name
- `type`: Provider type ("builtin", "api", "workflow", "mcp")
- `is_team_authorization`: Whether tool is authorized for use
- `plugin_unique_identifier`: Plugin identifier (for plugin tools)
- `tool_count`: Number of tools (only if populated)

**When to use**: Before configuring agent tools. Use `list_tools(provider_id, type)` to get full tool schemas.

---

### list_tools
List tools from a specific provider with full parameter schemas.

```
list_tools(provider_id?, tool_type?)
```

**Parameters**:
- `provider_id` (optional): Filter by provider
- `tool_type` (optional): "builtin", "workflow", "api", or "mcp" (default: "builtin")

**Returns**: List of tools with:
- `name`: Tool identifier
- `label`: Display name
- `description`: Tool description
- `parameters`: Array of parameter schemas:
  - `name`: Parameter name
  - `type`: Parameter type (string, number, boolean, select, etc.)
  - `form`: Parameter form ("llm" = LLM determines, "form" = user sets)
  - `required`: Whether parameter is required
  - `description`: Parameter description
  - `default`: Default value (if any)
  - `options`: Available options (for select types)

**When to use**: Get tool schemas for configuring agent tools. Parameters with `form: "llm"` go in `parameters`, those with `form: "form"` go in `settings`.

---

### list_models
List available AI models by type.

```
list_models(model_type?)
```

**Parameters**:
- `model_type` (optional): "llm", "text-embedding", "rerank", "speech2text", "tts" (default: "llm")

**Returns**: Models grouped by provider

**When to use**: Before configuring LLM nodes

---

### list_datasets
List available knowledge base datasets.

```
list_datasets(limit?)
```

**Parameters**:
- `limit` (optional): Max results (default: 50)

**Returns**: Datasets with IDs, names, descriptions, document counts

**When to use**: Before configuring knowledge-retrieval nodes

---

### get_dataset
Get detailed information about a specific dataset.

```
get_dataset(dataset_id)
```

**Parameters**:
- `dataset_id` (required): ID of the dataset

**Returns**: Dataset details including document count, word count, indexing technique, embedding model

**When to use**: To inspect a knowledge base before using it

---

### list_documents
List documents in a dataset.

```
list_documents(dataset_id, page?, limit?, keyword?)
```

**Parameters**:
- `dataset_id` (required): ID of the dataset
- `page` (optional): Page number (default: 1)
- `limit` (optional): Max results per page (default: 20)
- `keyword` (optional): Filter by keyword

**Returns**: Documents with IDs, names, word counts, indexing status

**When to use**: To explore contents of a knowledge base

---

### get_document
Get details of a specific document.

```
get_document(dataset_id, document_id)
```

**Parameters**:
- `dataset_id` (required): ID of the dataset
- `document_id` (required): ID of the document

**Returns**: Document details including word count, tokens, segments, status

---

### search_dataset
Search/query a dataset using retrieval (hit testing).

```
search_dataset(dataset_id, query, top_k?, search_method?)
```

**Parameters**:
- `dataset_id` (required): ID of the dataset to search
- `query` (required): Search query
- `top_k` (optional): Number of results (default: 5)
- `search_method` (optional): "semantic_search", "full_text_search", or "hybrid_search" (default: "semantic_search")

**Returns**: Matched segments with scores and content

**When to use**: Test retrieval quality, find relevant content before building RAG

---

## App Management Tools

### list_apps
List available Pulse apps.

```
list_apps(mode?, name?, limit?)
```

**Parameters**:
- `mode` (optional): "workflow", "advanced-chat", "chat", "completion", "agent-chat"
- `name` (optional): Filter by name (partial match)
- `limit` (optional): Max results (default: 20)

**Returns**: Apps with IDs, names, modes, descriptions

---

### select_app
Select an app for subsequent operations.

```
select_app(app_id)
```

**Parameters**:
- `app_id` (required): ID of app to select

**Effect**: All subsequent operations target this app

---

### create_app
Create a new app.

```
create_app(name, mode?, description?, icon?)
```

**Parameters**:
- `name` (required): App name
- `mode` (optional): App mode (default: "workflow")
- `description` (optional): App description
- `icon` (optional): Emoji icon (default: "🤖")

**Returns**: Created app details with ID

**Effect**: Auto-selects the newly created app, auto-initializes workflow

---

### initialize_workflow
Initialize a draft workflow for a newly created app.

```
initialize_workflow(app_id?)
```

**Parameters**:
- `app_id` (optional): App ID (uses selected app if not provided)

**Returns**: Initialized workflow with start node ID

**Note**: Automatically called by create_app for workflow/advanced-chat modes. Also auto-triggered if any workflow operation detects an uninitialized draft. You rarely need to call this manually.

---

## Workflow Operations

### view_workflow
View current workflow structure.

```
view_workflow(app_id?, include_details?)
```

**Parameters**:
- `app_id` (optional): App ID
- `include_details` (optional): Include full configs (default: false)

**Returns**: Nodes, edges, hash, overview

---

### validate_workflow
Check workflow for errors and warnings.

```
validate_workflow()
```

**Returns**:
- `valid`: Boolean
- `errors`: List of errors (missing start, invalid edges, etc.)
- `warnings`: List of warnings (disconnected nodes, etc.)
- `node_count`, `edge_count`: Counts

**When to use**: ALWAYS before publishing

---

### publish_workflow
Publish draft workflow as new version.

```
publish_workflow(name?, comment?)
```

**Parameters**:
- `name` (optional): Version name (max 20 chars)
- `comment` (optional): Version comment (max 100 chars)

**Returns**: Success status, created_at

**Precondition**: Must pass validate_workflow() first

---

## Node Operations

### add_node
Add a new node to the workflow.

```
add_node(node_type, title?, config?, position?, after_node_id?, source_handle?, target_handle?)
```

**Parameters**:
- `node_type` (required): Type from list_node_types
- `title` (optional): Display title
- `config` (optional): Node-specific config (from get_node_schema)
- `position` (optional): {x, y} coordinates (auto-calculated if omitted)
- `after_node_id` (optional): Connect from this node
- `source_handle` (optional): Handle on source (default: "source")
- `target_handle` (optional): Handle on target (default: "target")

**Returns**: node_id, node object

---

### edit_node
Modify an existing node.

```
edit_node(node_id, title?, config?, position?)
```

**Parameters**:
- `node_id` (required): ID of node to edit
- `title` (optional): New title
- `config` (optional): Config updates (PATCH-style, only changed fields)
- `position` (optional): New position

**Returns**: Updated node

**Best practice**: Use PATCH-style - only include fields you're changing

---

### delete_node
Remove a node and its connected edges.

```
delete_node(node_id)
```

**Parameters**:
- `node_id` (required): ID of node to delete

**Effect**: Also removes all edges connected to this node

---

### get_node
Get details of a specific node.

```
get_node(node_id)
```

**Returns**: Full node object or null if not found

---

### list_nodes
List all nodes in workflow.

```
list_nodes(filter_type?)
```

**Parameters**:
- `filter_type` (optional): Filter by node type

**Returns**: List of nodes

---

## Edge Operations

### connect_nodes
Create a connection between nodes.

```
connect_nodes(source_id, target_id, source_handle?, target_handle?)
```

**Parameters**:
- `source_id` (required): Source node ID
- `target_id` (required): Target node ID
- `source_handle` (optional): Handle on source (default: "source")
- `target_handle` (optional): Handle on target (default: "target")

**Returns**: edge_id, edge object

---

### disconnect_nodes
Remove connection(s) between nodes.

```
disconnect_nodes(source_id, target_id, source_handle?, target_handle?)
```

**Parameters**:
- `source_id` (required): Source node ID
- `target_id` (required): Target node ID
- `source_handle` (optional): Only remove edge with this source handle
- `target_handle` (optional): Only remove edge with this target handle

**Returns**: removed_count

---

### list_edges
List all edges in workflow.

```
list_edges()
```

**Returns**: List of edges with IDs, source, target, handles

---

## Feature Operations

### get_features
Get workflow feature configuration.

```
get_features()
```

**Returns**: Features object (file upload, opening statement, suggested questions, etc.)

---

### update_features
Update workflow features (partial update).

```
update_features(file_upload?, opening_statement?, suggested_questions?)
```

**Parameters**: Only include fields to update

**Returns**: Updated features

---

### get_variables
Get all workflow variables.

```
get_variables()
```

**Returns**:
- `environment_variables`: List
- `conversation_variables`: List

---

## Node Testing

### run_node
Execute a single node for testing.

```
run_node(node_id, inputs?, query?)
```

**Parameters**:
- `node_id` (required): Node to execute
- `inputs` (optional): Input values
- `query` (optional): Query string

**Returns**: Execution result with outputs, status, elapsed_time

---

## Sticky Notes

Sticky notes are visual-only elements for documentation and annotation. They don't participate in workflow execution.

### add_note
Add a sticky note to the workflow canvas.

```
add_note(text, theme?, position?, author?, show_author?, width?, height?)
```

**Parameters**:
- `text` (required): Note content (plain text, newlines create paragraphs)
- `theme` (optional): Color theme - "blue", "cyan", "green", "yellow", "pink", "violet" (default: "yellow")
- `position` (optional): {x, y} coordinates
- `author` (optional): Author name
- `show_author` (optional): Display author name (default: false)
- `width` (optional): Note width in pixels (default: 240, min: 240)
- `height` (optional): Note height in pixels (default: 88, min: 88)

**Returns**: note_id, note object

---

### edit_note
Update an existing sticky note.

```
edit_note(note_id, text?, theme?, position?, author?, show_author?, width?, height?)
```

**Parameters**:
- `note_id` (required): ID of note to edit
- `text` (optional): New content (plain text, newlines create paragraphs)
- `theme` (optional): Color theme
- `position` (optional): {x, y} coordinates
- `author` (optional): Author name
- `show_author` (optional): Display author name
- `width` (optional): Note width in pixels
- `height` (optional): Note height in pixels

**Returns**: Updated note

---

### list_notes
List all sticky notes in the workflow.

```
list_notes()
```

**Returns**: List of notes with IDs, themes, text previews, authors

---

### delete_note
Remove a sticky note.

```
delete_note(note_id)
```

**Parameters**:
- `note_id` (required): ID of note to delete

---

## Node Type Reference

### Nodes with Default Schemas
These nodes return full configuration schemas from `get_node_schema`:
- `llm`, `code`, `http-request`, `template-transform`, `question-classifier`
- `iteration`, `parameter-extractor`, `trigger-webhook`, `trigger-schedule`, `trigger-plugin`

### Nodes without Default Schemas
These nodes require manual configuration. Use `get_node_schema` for guidance:

| Node | Key Config Fields |
|------|------------------|
| `start` | No config needed. Entry point with sys.query, sys.files outputs |
| `end` | No config needed. Connect final nodes here |
| `answer` | `answer`: string with `{{#node.variable#}}` refs |
| `agent` | `agent_strategy_provider_name`, `agent_strategy_name`, `plugin_unique_identifier`, `agent_parameters` |
| `tool` | `provider_id`, `provider_type`, `provider_name`, `tool_name`, `tool_parameters` |
| `knowledge-retrieval` | `dataset_ids`, `retrieval_mode`, `query_variable_selector` |
| `if-else` | `conditions`, `logical_operator` |
| `variable-aggregator` | `variables` (array of selectors), `output_type` |
| `loop` | `loop_count` or `iterator_selector`, `break_conditions` |

### Agent Node Configuration

**Required fields:**
- `agent_strategy_provider_name`: e.g., `"pulse/agent/agent"`
- `agent_strategy_name`: e.g., `"function_calling"`
- `agent_strategy_label`: e.g., `"FunctionCalling"`
- `plugin_unique_identifier`: e.g., `"pulse/agent:0.1.0@..."`
- `agent_parameters`: Strategy-specific parameters

**Basic Example (with model only):**
```json
{
  "agent_strategy_provider_name": "pulse/agent/agent",
  "agent_strategy_name": "function_calling",
  "agent_strategy_label": "FunctionCalling",
  "plugin_unique_identifier": "pulse/agent:0.1.0@...",
  "agent_parameters": {
    "model": {
      "type": "constant",
      "value": {
        "provider": "pulse/openrouter/openrouter",
        "model": "anthropic/claude-sonnet-4.5",
        "model_type": "llm",
        "mode": "chat"
      }
    }
  }
}
```

**Full Example (with tools):**
```json
{
  "agent_strategy_provider_name": "pulse/agent/agent",
  "agent_strategy_name": "function_calling",
  "agent_strategy_label": "FunctionCalling",
  "plugin_unique_identifier": "pulse/agent:0.1.0@...",
  "agent_parameters": {
    "model": {
      "type": "constant",
      "value": {
        "provider": "pulse/openrouter/openrouter",
        "model": "anthropic/claude-sonnet-4.5",
        "model_type": "llm",
        "mode": "chat"
      }
    },
    "tools": {
      "type": "variable",
      "value": [{
        "provider_name": "google/google_search",
        "provider_show_name": "Google Search",
        "type": "builtin",
        "tool_name": "google_search",
        "tool_label": "Google Search",
        "tool_description": "Search the web using Google",
        "enabled": true,
        "settings": {},
        "parameters": {
          "query": { "auto": 1, "value": null },
          "num_results": { "auto": 0, "value": { "type": "constant", "value": 5 } }
        },
        "schemas": [
          { "name": "query", "type": "string", "form": "llm", "required": true },
          { "name": "num_results", "type": "number", "form": "llm", "required": false }
        ],
        "extra": { "description": "Search the web using Google" }
      }]
    }
  }
}
```

**Tool Parameter Structure:**

| Field | Description |
|-------|-------------|
| `provider_name` | Provider ID from `list_tool_providers` |
| `provider_show_name` | Display name of provider |
| `type` | `"builtin"`, `"workflow"`, `"api"`, or `"mcp"` |
| `tool_name` | Tool name from `list_tools` |
| `tool_label` | Display label for the tool |
| `enabled` | Whether tool is active |
| `settings` | Form parameters (non-LLM): `{[param]: {value: {type, value}}}` |
| `parameters` | LLM parameters: `{[param]: {auto: 0\|1, value: {type, value}\|null}}` |
| `schemas` | Parameter schemas from `list_tools` |

**Parameter auto/value:**
- `auto: 1, value: null` - Let LLM determine the value
- `auto: 0, value: {type: 'constant', value: ...}` - Fixed value
- `auto: 0, value: {type: 'variable', value: ['node_id', 'var']}` - Reference variable
- `auto: 0, value: {type: 'mixed', value: 'text {{#node.var#}}'}` - Mixed text/variable

**Mapping list_tools output to tool configuration:**

1. Call `list_tool_providers()` to get provider info
2. Call `list_tools(provider_id, type)` to get tool schemas
3. Map the response to tool configuration:

| From `list_tools` | To Tool Config |
|-------------------|----------------|
| `name` | `tool_name` |
| `label` | `tool_label` |
| `description` | `tool_description`, `extra.description` |
| `parameters` where `form: "llm"` | `parameters` object |
| `parameters` where `form: "form"` | `settings` object |
| Full `parameters` array | `schemas` |

From `list_tool_providers`:
| Field | To Tool Config |
|-------|----------------|
| `id` | `provider_name` |
| `label` | `provider_show_name` |
| `type` | `type` |
| `is_team_authorization` | `enabled` (initial value) |

---

## Error Handling

Common errors:
- **WorkflowNotSyncError**: Concurrent edit detected - fetch latest and retry
- **PulseClientError**: API error with status code
- **No app selected**: Call list_apps + select_app first
- **Node not found**: Verify node_id with list_nodes

Always check error responses and handle gracefully.
