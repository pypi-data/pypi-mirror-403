# Node Types Reference

Always call `get_node_schema(block_type)` to get the actual schema. This reference provides an overview.

## Control Nodes

### start
Entry point for the workflow. Every workflow must have exactly one.
- **Outputs**: `sys.query`, `sys.user_id`, `sys.conversation_id`, `sys.files`
- **Handles**: `source` (outgoing only)

### end
Terminates workflow execution. Use for workflows without direct user response.
- **Inputs**: Output variables to return
- **Handles**: `target` (incoming only)

### answer
Returns a response to the user. Use for chat/conversational workflows.
- **Config**: `answer` - The response content (supports variable references)
- **Handles**: `target` (incoming), `source` (outgoing for chaining)

### if-else
Conditional branching based on conditions.
- **Config**: `conditions` - Array of condition groups
- **Handles**: `target`, multiple `source` handles for branches (true, false, elif)

### iteration
Loop over array items.
- **Config**: `iterator_selector` - Variable containing array
- **Handles**: `target`, `source` (loop body), `source` (done)

### loop
Repeat until condition met.
- **Config**: `loop_count`, `break_condition`
- **Handles**: Similar to iteration

## AI Nodes

### llm
Language model processing - the most commonly used node.

**Key Config**:
```yaml
model:
  provider: "openai"       # From list_models()
  name: "gpt-4"
  mode: "chat"
  completion_params:
    temperature: 0.7
    max_tokens: 2000

prompt_template:
  - role: "system"
    text: "You are a helpful assistant."
  - role: "user"
    text: "{{#sys.query#}}"

context:                   # For RAG
  enabled: true
  variable_selector: ["knowledge_node_id", "result"]

memory:                    # For conversation history
  role_prefix:
    user: "User"
    assistant: "Assistant"
  window:
    enabled: true
    size: 10

vision:                    # For image input
  enabled: true
```

### knowledge-retrieval
Retrieve from knowledge bases (RAG).

**Key Config**:
```yaml
query_variable_selector: ["start", "sys.query"]
dataset_ids: ["from-list_datasets"]
retrieval_mode: "multiple"  # or "single"
multiple_retrieval_config:
  top_k: 5
  score_threshold: 0.5
  reranking_model:
    provider: "..."
    name: "..."
```

### question-classifier
Classify user intent into categories.

**Key Config**:
```yaml
query_variable_selector: ["start", "sys.query"]
model: { ... }
classes:
  - id: "class1"
    name: "Sales Inquiry"
  - id: "class2"
    name: "Support Request"
```

### parameter-extractor
Extract structured parameters from text.

**Key Config**:
```yaml
query_variable_selector: ["start", "sys.query"]
model: { ... }
parameters:
  - name: "email"
    type: "string"
    required: true
    description: "User's email address"
```

## Transform Nodes

### code
Execute Python or JavaScript code.

**Key Config**:
```yaml
code_language: "python3"  # or "javascript"
code: |
  def main(arg1, arg2):
      return {"result": arg1 + arg2}
variables:
  - variable: "arg1"
    value_selector: ["previous_node", "output"]
outputs:
  - variable: "result"
    type: "string"
```

### template-transform
Transform data using Jinja2 templates.

**Key Config**:
```yaml
template: "Hello, {{name}}! Your order {{order_id}} is ready."
variables:
  - variable: "name"
    value_selector: ["start", "sys.user_name"]
  - variable: "order_id"
    value_selector: ["order_node", "id"]
```

### variable-assigner
Assign values to conversation variables.

**Key Config**:
```yaml
items:
  - variable_selector: ["conversation_var_name"]
    value: "static value"
    # OR
    input_variable_selector: ["other_node", "output"]
```

### variable-aggregator
Merge multiple variables into one.

**Key Config**:
```yaml
aggregation_mode: "concat"  # or "merge"
variable_selectors:
  - ["node1", "output"]
  - ["node2", "output"]
output_variable: "merged_result"
```

### document-extractor
Extract text from uploaded documents.

**Key Config**:
```yaml
variable_selector: ["start", "sys.files"]
```

### list-filter
Filter array items based on conditions.

**Key Config**:
```yaml
variable_selector: ["iteration", "item"]
filter_by:
  enabled: true
  conditions: [...]
```

## External Nodes

### http-request
Make HTTP API calls.

**Key Config**:
```yaml
method: "POST"
url: "https://api.example.com/endpoint"
headers:
  - key: "Authorization"
    value: "Bearer {{#api_key#}}"
body:
  type: "json"
  data: '{"query": "{{#sys.query#}}"}'
timeout: 30
```

### tool
Call external tools/plugins.

**Key Config**:
```yaml
provider_id: "from-list_tool_providers"
provider_type: "builtin"
tool_name: "from-list_tools"
tool_parameters:
  param1: "{{#variable#}}"
```

## Variable Reference Syntax

Reference variables from other nodes using:
- `{{#node_id.variable_name#}}` in templates
- `["node_id", "variable_name"]` in selectors

Special system variables:
- `sys.query` - User input
- `sys.user_id` - User identifier
- `sys.conversation_id` - Conversation identifier
- `sys.files` - Uploaded files

## Connection Handles

Common handles:
- `source` - Default output handle
- `target` - Default input handle
- `true` / `false` - if-else branch outputs
- `source-0`, `source-1` - Multiple outputs (iteration)

Check `get_node_schema()` for node-specific handles.
