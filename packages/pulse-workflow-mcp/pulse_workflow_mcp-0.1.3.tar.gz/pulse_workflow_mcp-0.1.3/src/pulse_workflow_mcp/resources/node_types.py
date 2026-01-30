"""Node type schemas for Dify workflows."""

NODE_TYPES_SCHEMA = {
    "start": {
        "name": "Start",
        "description": "Entry point of the workflow. Defines input variables.",
        "category": "control",
        "config_schema": {
            "type": "object",
            "properties": {
                "variables": {
                    "type": "array",
                    "description": "Input variables for the workflow",
                    "items": {
                        "type": "object",
                        "properties": {
                            "variable": {"type": "string"},
                            "type": {
                                "type": "string",
                                "enum": ["text", "paragraph", "number", "select", "file", "file-list"],
                            },
                            "label": {"type": "string"},
                            "required": {"type": "boolean"},
                            "options": {"type": "array", "items": {"type": "string"}},
                            "max_length": {"type": "integer"},
                        },
                        "required": ["variable", "type"],
                    },
                },
            },
        },
        "outputs": ["sys.query", "sys.files", "sys.conversation_id", "sys.user_id"],
    },
    "end": {
        "name": "End",
        "description": "Terminal node that ends the workflow execution.",
        "category": "control",
        "config_schema": {
            "type": "object",
            "properties": {
                "outputs": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "variable": {"type": "string"},
                            "value_selector": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                },
            },
        },
    },
    "answer": {
        "name": "Answer",
        "description": "Outputs a response to the user in streaming chat mode.",
        "category": "control",
        "config_schema": {
            "type": "object",
            "properties": {
                "answer": {
                    "type": "string",
                    "description": "Template for the answer output, supports variable references",
                },
            },
            "required": ["answer"],
        },
    },
    "llm": {
        "name": "LLM",
        "description": "Language model node for text generation, reasoning, and processing.",
        "category": "ai",
        "config_schema": {
            "type": "object",
            "properties": {
                "model": {
                    "type": "object",
                    "properties": {
                        "provider": {"type": "string"},
                        "name": {"type": "string"},
                        "mode": {"type": "string", "enum": ["chat", "completion"]},
                        "completion_params": {
                            "type": "object",
                            "properties": {
                                "temperature": {"type": "number", "minimum": 0, "maximum": 2},
                                "max_tokens": {"type": "integer"},
                                "top_p": {"type": "number"},
                                "presence_penalty": {"type": "number"},
                                "frequency_penalty": {"type": "number"},
                            },
                        },
                    },
                    "required": ["provider", "name"],
                },
                "prompt_template": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "role": {"type": "string", "enum": ["system", "user", "assistant"]},
                            "text": {"type": "string"},
                        },
                        "required": ["role", "text"],
                    },
                },
                "context": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "variable_selector": {"type": "array", "items": {"type": "string"}},
                    },
                },
                "vision": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "configs": {"type": "object"},
                    },
                },
                "memory": {
                    "type": "object",
                    "properties": {
                        "role_prefix": {
                            "type": "object",
                            "properties": {
                                "user": {"type": "string"},
                                "assistant": {"type": "string"},
                            },
                        },
                        "window": {
                            "type": "object",
                            "properties": {
                                "enabled": {"type": "boolean"},
                                "size": {"type": "integer"},
                            },
                        },
                    },
                },
            },
            "required": ["model", "prompt_template"],
        },
        "outputs": ["text"],
    },
    "code": {
        "name": "Code",
        "description": "Execute Python or JavaScript code for data processing.",
        "category": "transform",
        "config_schema": {
            "type": "object",
            "properties": {
                "code_language": {"type": "string", "enum": ["python3", "javascript"]},
                "code": {"type": "string"},
                "variables": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "variable": {"type": "string"},
                            "value_selector": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                },
                "outputs": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": [
                                    "string",
                                    "number",
                                    "object",
                                    "array[string]",
                                    "array[number]",
                                    "array[object]",
                                ],
                            },
                        },
                    },
                },
            },
            "required": ["code_language", "code"],
        },
    },
    "http-request": {
        "name": "HTTP Request",
        "description": "Make HTTP requests to external APIs.",
        "category": "external",
        "config_schema": {
            "type": "object",
            "properties": {
                "method": {"type": "string", "enum": ["GET", "POST", "PUT", "PATCH", "DELETE"]},
                "url": {"type": "string"},
                "headers": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "key": {"type": "string"},
                            "value": {"type": "string"},
                        },
                    },
                },
                "params": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "key": {"type": "string"},
                            "value": {"type": "string"},
                        },
                    },
                },
                "body": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["none", "form-data", "x-www-form-urlencoded", "raw-text", "json"],
                        },
                        "data": {"type": "string"},
                    },
                },
                "timeout": {"type": "integer"},
            },
            "required": ["method", "url"],
        },
        "outputs": ["status_code", "body", "headers"],
    },
    "knowledge-retrieval": {
        "name": "Knowledge Retrieval",
        "description": "Retrieve relevant documents from knowledge bases (RAG).",
        "category": "ai",
        "config_schema": {
            "type": "object",
            "properties": {
                "query_variable_selector": {"type": "array", "items": {"type": "string"}},
                "dataset_ids": {"type": "array", "items": {"type": "string"}},
                "retrieval_mode": {"type": "string", "enum": ["single", "multiple"]},
                "single_retrieval_config": {
                    "type": "object",
                    "properties": {
                        "model": {
                            "type": "object",
                            "properties": {
                                "provider": {"type": "string"},
                                "name": {"type": "string"},
                            },
                        },
                    },
                },
                "multiple_retrieval_config": {
                    "type": "object",
                    "properties": {
                        "top_k": {"type": "integer"},
                        "score_threshold": {"type": "number"},
                        "reranking_model": {"type": "object"},
                    },
                },
            },
            "required": ["query_variable_selector", "dataset_ids"],
        },
        "outputs": ["result"],
    },
    "tool": {
        "name": "Tool",
        "description": "Use built-in or custom tools/plugins.",
        "category": "external",
        "config_schema": {
            "type": "object",
            "properties": {
                "provider_id": {"type": "string"},
                "provider_type": {"type": "string"},
                "provider_name": {"type": "string"},
                "tool_name": {"type": "string"},
                "tool_label": {"type": "string"},
                "tool_configurations": {"type": "object"},
                "tool_parameters": {"type": "object"},
            },
            "required": ["provider_id", "provider_type", "tool_name"],
        },
    },
    "if-else": {
        "name": "If/Else",
        "description": "Conditional branching based on conditions.",
        "category": "control",
        "config_schema": {
            "type": "object",
            "properties": {
                "conditions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "variable_selector": {"type": "array", "items": {"type": "string"}},
                            "comparison_operator": {
                                "type": "string",
                                "enum": [
                                    "=",
                                    "!=",
                                    ">",
                                    "<",
                                    ">=",
                                    "<=",
                                    "contains",
                                    "not contains",
                                    "start with",
                                    "end with",
                                    "is",
                                    "is not",
                                    "empty",
                                    "not empty",
                                ],
                            },
                            "value": {"type": "string"},
                        },
                    },
                },
                "logical_operator": {"type": "string", "enum": ["and", "or"]},
            },
        },
        "outputs": ["true", "false"],
    },
    "variable-assigner": {
        "name": "Variable Assigner",
        "description": "Assign values to conversation variables.",
        "category": "transform",
        "config_schema": {
            "type": "object",
            "properties": {
                "output_type": {"type": "string"},
                "variables": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "variable": {"type": "string"},
                            "value_selector": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                },
            },
        },
    },
    "variable-aggregator": {
        "name": "Variable Aggregator",
        "description": "Aggregate multiple variables into one.",
        "category": "transform",
        "config_schema": {
            "type": "object",
            "properties": {
                "output_type": {"type": "string"},
                "variables": {
                    "type": "array",
                    "items": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
    },
    "template-transform": {
        "name": "Template Transform",
        "description": "Transform data using Jinja2 templates.",
        "category": "transform",
        "config_schema": {
            "type": "object",
            "properties": {
                "template": {"type": "string"},
                "variables": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "variable": {"type": "string"},
                            "value_selector": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                },
            },
            "required": ["template"],
        },
        "outputs": ["output"],
    },
    "question-classifier": {
        "name": "Question Classifier",
        "description": "Classify user input into predefined categories using LLM.",
        "category": "ai",
        "config_schema": {
            "type": "object",
            "properties": {
                "query_variable_selector": {"type": "array", "items": {"type": "string"}},
                "model": {
                    "type": "object",
                    "properties": {
                        "provider": {"type": "string"},
                        "name": {"type": "string"},
                    },
                },
                "classes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                        },
                    },
                },
                "instruction": {"type": "string"},
            },
            "required": ["query_variable_selector", "model", "classes"],
        },
    },
    "iteration": {
        "name": "Iteration",
        "description": "Iterate over an array, processing each item.",
        "category": "control",
        "config_schema": {
            "type": "object",
            "properties": {
                "iterator_selector": {"type": "array", "items": {"type": "string"}},
                "output_selector": {"type": "array", "items": {"type": "string"}},
                "output_type": {"type": "string"},
                "is_parallel": {"type": "boolean"},
                "parallel_nums": {"type": "integer"},
            },
            "required": ["iterator_selector"],
        },
    },
    "loop": {
        "name": "Loop",
        "description": "Loop execution with break conditions.",
        "category": "control",
        "config_schema": {
            "type": "object",
            "properties": {
                "loop_count": {"type": "integer"},
                "break_conditions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "variable_selector": {"type": "array", "items": {"type": "string"}},
                            "comparison_operator": {"type": "string"},
                            "value": {"type": "string"},
                        },
                    },
                },
            },
        },
    },
    "parameter-extractor": {
        "name": "Parameter Extractor",
        "description": "Extract structured parameters from text using LLM.",
        "category": "ai",
        "config_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "array", "items": {"type": "string"}},
                "model": {
                    "type": "object",
                    "properties": {
                        "provider": {"type": "string"},
                        "name": {"type": "string"},
                    },
                },
                "parameters": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "type": {"type": "string"},
                            "description": {"type": "string"},
                            "required": {"type": "boolean"},
                        },
                    },
                },
                "instruction": {"type": "string"},
            },
            "required": ["query", "model", "parameters"],
        },
    },
    "document-extractor": {
        "name": "Document Extractor",
        "description": "Extract text content from uploaded documents.",
        "category": "transform",
        "config_schema": {
            "type": "object",
            "properties": {
                "variable_selector": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["variable_selector"],
        },
        "outputs": ["text"],
    },
    "list-filter": {
        "name": "List Filter",
        "description": "Filter items in a list based on conditions.",
        "category": "transform",
        "config_schema": {
            "type": "object",
            "properties": {
                "variable": {"type": "array", "items": {"type": "string"}},
                "filter_by": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "conditions": {"type": "array"},
                    },
                },
                "order_by": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "key": {"type": "string"},
                        "value": {"type": "string", "enum": ["asc", "desc"]},
                    },
                },
                "limit": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "size": {"type": "integer"},
                    },
                },
            },
            "required": ["variable"],
        },
    },
    "assigner": {
        "name": "Assigner",
        "description": "Assign or modify variable values.",
        "category": "transform",
        "config_schema": {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "variable": {"type": "array", "items": {"type": "string"}},
                            "operation": {
                                "type": "string",
                                "enum": ["set", "clear", "append", "extend"],
                            },
                            "value": {"type": "string"},
                        },
                    },
                },
            },
        },
    },
    "agent": {
        "name": "Agent",
        "description": "Autonomous agent using strategy plugins. Use list_agent_strategies and get_agent_strategy to configure.",
        "category": "ai",
        "config_schema": {
            "type": "object",
            "properties": {
                "agent_strategy_provider_name": {
                    "type": "string",
                    "description": "Strategy provider name (e.g., 'langgenius/agent/cot_agent_with_memory')",
                },
                "agent_strategy_name": {
                    "type": "string",
                    "description": "Strategy name within the provider",
                },
                "agent_strategy_label": {
                    "type": "string",
                    "description": "Display label for the strategy",
                },
                "plugin_unique_identifier": {
                    "type": "string",
                    "description": "Plugin unique identifier from get_agent_strategy",
                },
                "agent_parameters": {
                    "type": "object",
                    "description": "Strategy-specific parameters. Use get_agent_strategy to get required params.",
                    "additionalProperties": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "enum": ["constant", "variable", "mixed"]},
                            "value": {},
                        },
                    },
                },
                "memory": {
                    "type": "object",
                    "description": "Optional memory configuration",
                },
                "output_schema": {
                    "type": "object",
                    "description": "Output schema for structured outputs",
                },
            },
            "required": [
                "agent_strategy_provider_name",
                "agent_strategy_name",
                "agent_strategy_label",
                "agent_parameters",
            ],
        },
        "outputs": ["text", "files"],
    },
}

# Category descriptions for grouping
NODE_CATEGORIES = {
    "control": {
        "name": "Control Flow",
        "description": "Nodes that control workflow execution flow",
        "nodes": ["start", "end", "answer", "if-else", "iteration", "loop"],
    },
    "ai": {
        "name": "AI & ML",
        "description": "Nodes that use AI/ML models",
        "nodes": ["llm", "agent", "knowledge-retrieval", "question-classifier", "parameter-extractor"],
    },
    "transform": {
        "name": "Data Transform",
        "description": "Nodes for data manipulation and transformation",
        "nodes": [
            "code",
            "template-transform",
            "variable-assigner",
            "variable-aggregator",
            "document-extractor",
            "list-filter",
            "assigner",
        ],
    },
    "external": {
        "name": "External Services",
        "description": "Nodes for interacting with external services",
        "nodes": ["http-request", "tool"],
    },
}
