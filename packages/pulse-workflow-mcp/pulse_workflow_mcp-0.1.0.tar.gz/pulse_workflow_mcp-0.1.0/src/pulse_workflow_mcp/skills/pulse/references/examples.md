# Workflow Examples

Common workflow patterns with step-by-step implementation.

## Simple Chatbot

Basic LLM-powered chatbot that responds to user queries.

### Steps

```python
# 1. Discovery
list_apps(mode="workflow")
select_app(app_id="...")  # or create_app(name="Simple Chatbot")

list_models(model_type="llm")
get_node_schema(block_type="llm")

# 2. View current state (likely just start node)
view_workflow()

# 3. Find start node
nodes = list_nodes()
start_node_id = [n for n in nodes if n["data"]["type"] == "start"][0]["id"]

# 4. Add LLM node
add_node(
    node_type="llm",
    title="Chat Response",
    config={
        "model": {
            "provider": "openai",  # from list_models
            "name": "gpt-4",
            "mode": "chat"
        },
        "prompt_template": [
            {"role": "system", "text": "You are a helpful assistant."},
            {"role": "user", "text": "{{#sys.query#}}"}
        ]
    },
    after_node_id=start_node_id
)
# Returns: {"node_id": "llm-node-id"}

# 5. Add answer node
add_node(
    node_type="answer",
    title="Response",
    config={
        "answer": "{{#llm-node-id.text#}}"
    },
    after_node_id="llm-node-id"
)

# 6. Validate and publish
validate_workflow()
publish_workflow(name="v1.0", comment="Initial chatbot")
```

---

## RAG Chatbot

Chatbot that retrieves context from a knowledge base.

### Steps

```python
# 1. Discovery
select_app(app_id="...")
list_datasets()  # Find your knowledge base
list_models(model_type="llm")
get_node_schema(block_type="knowledge-retrieval")
get_node_schema(block_type="llm")

# 2. Get start node
nodes = list_nodes()
start_id = [n for n in nodes if n["data"]["type"] == "start"][0]["id"]

# 3. Add knowledge retrieval
add_node(
    node_type="knowledge-retrieval",
    title="Knowledge Search",
    config={
        "query_variable_selector": ["sys", "query"],
        "dataset_ids": ["your-dataset-id"],  # from list_datasets
        "retrieval_mode": "multiple",
        "multiple_retrieval_config": {
            "top_k": 5,
            "score_threshold": 0.5
        }
    },
    after_node_id=start_id
)
# Returns: {"node_id": "knowledge-node-id"}

# 4. Add LLM with context
add_node(
    node_type="llm",
    title="RAG Response",
    config={
        "model": {"provider": "openai", "name": "gpt-4", "mode": "chat"},
        "prompt_template": [
            {
                "role": "system",
                "text": "Answer based on the following context:\n\n{{#context#}}\n\nIf the context doesn't contain relevant information, say so."
            },
            {"role": "user", "text": "{{#sys.query#}}"}
        ],
        "context": {
            "enabled": True,
            "variable_selector": ["knowledge-node-id", "result"]
        }
    },
    after_node_id="knowledge-node-id"
)

# 5. Add answer
add_node(
    node_type="answer",
    config={"answer": "{{#llm-node-id.text#}}"},
    after_node_id="llm-node-id"
)

# 6. Validate and publish
validate_workflow()
publish_workflow(name="v1.0")
```

---

## Intent Classification with Routing

Route users to different paths based on intent.

### Steps

```python
# 1. Discovery
get_node_schema(block_type="question-classifier")
get_node_schema(block_type="llm")

# 2. Add classifier after start
add_node(
    node_type="question-classifier",
    title="Intent Classifier",
    config={
        "query_variable_selector": ["sys", "query"],
        "model": {"provider": "openai", "name": "gpt-4", "mode": "chat"},
        "classes": [
            {"id": "sales", "name": "Sales Inquiry"},
            {"id": "support", "name": "Support Request"},
            {"id": "general", "name": "General Question"}
        ]
    },
    after_node_id=start_id
)
# Returns: {"node_id": "classifier-id"}

# 3. Add LLM for each branch
# Note: classifier has handles "sales", "support", "general"

add_node(
    node_type="llm",
    title="Sales Response",
    config={
        "model": {"provider": "openai", "name": "gpt-4", "mode": "chat"},
        "prompt_template": [
            {"role": "system", "text": "You are a sales assistant..."},
            {"role": "user", "text": "{{#sys.query#}}"}
        ]
    },
    position={"x": 400, "y": 0}
)
connect_nodes(
    source_id="classifier-id",
    target_id="sales-llm-id",
    source_handle="sales"
)

add_node(
    node_type="llm",
    title="Support Response",
    config={
        "prompt_template": [
            {"role": "system", "text": "You are a support agent..."},
            {"role": "user", "text": "{{#sys.query#}}"}
        ]
    },
    position={"x": 400, "y": 200}
)
connect_nodes(
    source_id="classifier-id",
    target_id="support-llm-id",
    source_handle="support"
)

# 4. Add answer nodes for each path
# Then connect all to a common end or separate answers
```

---

## API Integration Workflow

Workflow that calls an external API.

### Steps

```python
# 1. Discovery
get_node_schema(block_type="http-request")
get_node_schema(block_type="code")

# 2. Add HTTP request node
add_node(
    node_type="http-request",
    title="Fetch Weather",
    config={
        "method": "GET",
        "url": "https://api.weather.com/v1/current?city={{#sys.query#}}",
        "headers": [
            {"key": "Authorization", "value": "Bearer {{#env.WEATHER_API_KEY#}}"}
        ],
        "timeout": 30
    },
    after_node_id=start_id
)

# 3. Add code node to process response
add_node(
    node_type="code",
    title="Process Weather",
    config={
        "code_language": "python3",
        "code": """
def main(response):
    data = response.get("body", {})
    temp = data.get("temperature", "N/A")
    condition = data.get("condition", "N/A")
    return {
        "summary": f"Temperature: {temp}°C, Condition: {condition}"
    }
""",
        "variables": [
            {"variable": "response", "value_selector": ["http-node-id", "body"]}
        ],
        "outputs": [
            {"variable": "summary", "type": "string"}
        ]
    },
    after_node_id="http-node-id"
)

# 4. Add answer
add_node(
    node_type="answer",
    config={"answer": "{{#code-node-id.summary#}}"},
    after_node_id="code-node-id"
)
```

---

## Iterating Over Results

Process each item in an array.

### Steps

```python
# 1. After getting array data (e.g., from knowledge retrieval or API)

# 2. Add iteration node
add_node(
    node_type="iteration",
    title="Process Each Result",
    config={
        "iterator_selector": ["knowledge-node-id", "result"]
    },
    after_node_id="knowledge-node-id"
)

# 3. Add processing inside iteration
add_node(
    node_type="llm",
    title="Summarize Item",
    config={
        "prompt_template": [
            {"role": "user", "text": "Summarize: {{#iteration.item#}}"}
        ]
    }
)
connect_nodes(
    source_id="iteration-id",
    target_id="llm-id",
    source_handle="source"  # Loop body
)

# 4. Connect iteration completion to answer
add_node(node_type="answer", ...)
connect_nodes(
    source_id="iteration-id",
    target_id="answer-id",
    source_handle="source-1"  # Done handle
)
```

---

## Knowledge Base Search

Test and explore knowledge bases before building RAG workflows.

### Steps

```python
# 1. List available knowledge bases
list_datasets()

# 2. Get details of a specific dataset
get_dataset(dataset_id="your-dataset-id")

# 3. Browse documents in the dataset
list_documents(dataset_id="your-dataset-id", limit=10)

# 4. Test retrieval with a search query
search_dataset(
    dataset_id="your-dataset-id",
    query="How do I configure authentication?",
    top_k=5,
    search_method="semantic_search"
)
# Returns: Matched segments with relevance scores

# 5. Try different search methods
search_dataset(
    dataset_id="your-dataset-id",
    query="authentication",
    search_method="full_text_search"
)

# 6. Get specific document details
get_document(
    dataset_id="your-dataset-id",
    document_id="doc-id-from-list"
)
```

**Use cases**:
- Test retrieval quality before building RAG
- Find relevant documents for a topic
- Debug poor retrieval results
- Explore dataset contents

---

## Documenting Workflows with Sticky Notes

Add annotations and documentation directly on the canvas.

### Steps

```python
# 1. Add a note explaining a section
add_note(
    text="This section handles user authentication via OAuth2",
    theme="blue",
    position={"x": 100, "y": 50}
)

# 2. Add a warning note
add_note(
    text="⚠️ TODO: Add rate limiting before production",
    theme="pink",
    author="Developer",
    show_author=True
)

# 3. List all notes in workflow
list_notes()

# 4. Update a note
edit_note(
    note_id="note-id",
    text="Updated: Rate limiting added in v2.0",
    theme="green"
)

# 5. Remove completed TODOs
delete_note(note_id="todo-note-id")
```

**Theme colors**:
- 🔵 `blue` - Architecture/design notes
- 🩵 `cyan` - Technical details
- 🟢 `green` - Completed/verified
- 🟡 `yellow` - General notes (default)
- 🩷 `pink` - Warnings/TODOs
- 🟣 `violet` - Important notices

---

## Best Practices

1. **Always discover first** - Never hardcode model names, dataset IDs, or tool configs
2. **Build incrementally** - Add one node, verify, then add the next
3. **Use meaningful titles** - Makes debugging easier
4. **Validate before publish** - Always run validate_workflow()
5. **Handle errors** - Add if-else for error conditions in complex workflows
6. **Use code nodes** - For complex data transformations
7. **Test with run_node** - Test individual nodes before full workflow
8. **Test retrieval** - Use search_dataset before building RAG workflows
9. **Document your work** - Add sticky notes for complex logic
