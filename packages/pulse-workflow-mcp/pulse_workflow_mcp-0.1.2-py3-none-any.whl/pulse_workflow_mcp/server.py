"""Main MCP server for Pulse workflow operations.

Optimized for Claude Code: concise responses, minimal tokens, high accuracy.
"""

import asyncio
import json
import logging
import sys
from collections.abc import Callable, Coroutine
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .config import init_config
from .dify_client import NodeType, PulseClient, PulseClientError, cleanup_client, get_client, init_client
from .prompts.workflow_context import register_workflow_prompts
from .resources.workflow_resource import register_workflow_resources

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

server = Server("pulse-workflow")

# Complete list of known node types (from NodeType enum)
ALL_NODE_TYPES = [t.value for t in NodeType]

# Guidance for nodes without default schemas
NODE_CONFIG_GUIDANCE: dict[str, str] = {
    "start": "Start node has no config. Use for workflow entry point. Outputs: sys.query, sys.files, sys.user_id, etc.",
    "end": "End node has no config. Connect final nodes here to end workflow.",
    "answer": "Config: {answer: string with {{variable}} refs}. Streams response to user.",
    "agent": """Config for agent node:
STEP 1: Use list_agent_strategies to find available strategy providers.
STEP 2: Use get_agent_strategy(provider_name) to get required parameters.

Required fields:
- agent_strategy_provider_name: e.g. 'langgenius/agent/cot_agent_with_memory'
- agent_strategy_name: e.g. 'cot_agent_with_memory'
- agent_strategy_label: e.g. 'CoT Agent'
- plugin_unique_identifier: From get_agent_strategy response
- agent_parameters: Strategy-specific parameters (get from get_agent_strategy)

Common agent_parameters (varies by strategy):
  instruction: {type: 'constant', value: 'Your system instructions here'}
  query: {type: 'mixed', value: '{{#sys.query#}}'}  # Reference start node input
  model: {type: 'constant', value: {provider, model, model_type: 'llm', mode: 'chat'}}

For tools parameter (multiToolSelector type):
  tools: {
    type: 'variable',
    value: [{
      provider_name: 'provider_id',
      provider_show_name: 'Provider Name',
      type: 'builtin|workflow|api|mcp',
      tool_name: 'tool_name',
      tool_label: 'Tool Label',
      tool_description: 'Description',
      enabled: true,
      settings: {[param]: {value: {type: 'constant', value: ...}}},
      parameters: {[param]: {auto: 1, value: null}},
      schemas: [{name, type, form: 'llm'|'form', required, ...}],
      extra: {description: '...'}
    }]
  }

Use list_tools(provider_id, type) to get tool schemas for the parameters/settings fields.""",
    "tool": "Config: {provider_id, provider_type, provider_name, tool_name, tool_parameters}. Use list_tool_providers + list_tools first.",
    "knowledge-retrieval": "Config: {dataset_ids: [...], retrieval_mode, query_variable_selector}. Use list_datasets first.",
    "if-else": "Config: {conditions: [{comparison_operator, variable_selector, value}], logical_operator}.",
    "variable-aggregator": "Config: {variables: [[node_id, var_name], ...], output_type}. Aggregates multiple variables.",
    "datasource": "Requires plugin_id, provider_name, action, action_parameters. Use list_tool_providers(type='builtin') for datasource plugins.",
    "human-input": "Pauses workflow for human input. Config: {input_config: {wait_timeout, ...}}.",
    "trigger-webhook": "Webhook trigger. Auto-configured, receives HTTP requests.",
    "trigger-schedule": "Cron trigger. Config: {schedule: cron_expression}.",
    "trigger-plugin": "Plugin trigger. Requires plugin_id, plugin_unique_identifier, trigger_name.",
    "list-operator": "Config: {variable_selector, filter, order_by, limit}. Operates on list variables.",
    "loop": "Config: {loop_count or iterator_selector, break_conditions}. Contains sub-workflow.",
}


def _compact_json(data: Any) -> str:
    """Return compact JSON without pretty-printing."""
    return json.dumps(data, separators=(",", ":"))


def _extract_text_from_lexical(lexical_json: str, max_len: int = 50) -> str:
    """Extract plain text preview from Lexical JSON format."""
    if not lexical_json:
        return ""

    try:
        data = json.loads(lexical_json)
        texts = []

        def extract_text(node: dict) -> None:
            if node.get("type") == "text":
                texts.append(node.get("text", ""))
            for child in node.get("children", []):
                if isinstance(child, dict):
                    extract_text(child)

        if "root" in data:
            extract_text(data["root"])

        result = " ".join(texts)
        if len(result) > max_len:
            result = result[:max_len] + "..."
        return result
    except (json.JSONDecodeError, TypeError):
        # Not valid Lexical JSON, return as-is (truncated)
        return lexical_json[:max_len] if len(lexical_json) > max_len else lexical_json


# Type alias for tool handlers
ToolHandler = Callable[[dict[str, Any], PulseClient], Coroutine[Any, Any, list[TextContent]]]


# ============================================================
# Tool Handlers
# ============================================================


async def handle_list_apps(args: dict[str, Any], client: PulseClient) -> list[TextContent]:
    result = await client.list_apps(
        limit=args.get("limit", 20),
        mode=args.get("mode"),
        name=args.get("name"),
    )
    apps = [{"id": a["id"], "name": a.get("name", ""), "mode": a.get("mode", "")} for a in result.get("data", [])]
    selected = client.app_id
    return [
        TextContent(
            type="text",
            text=_compact_json({"apps": apps, "total": result.get("total", len(apps)), "selected": selected}),
        )
    ]


async def handle_select_app(args: dict[str, Any], client: PulseClient) -> list[TextContent]:
    app_id = args["app_id"]
    app_detail = await client.get_app_detail(app_id)
    client.set_app_id(app_id)
    return [
        TextContent(
            type="text",
            text=_compact_json({"selected": app_id, "name": app_detail.get("name"), "mode": app_detail.get("mode")}),
        )
    ]


async def handle_create_app(args: dict[str, Any], client: PulseClient) -> list[TextContent]:
    app_mode = args.get("mode", "workflow")
    result = await client.create_app(
        name=args["name"],
        mode=app_mode,
        description=args.get("description", ""),
        icon=args.get("icon", "\U0001f916"),
    )
    app_id = result.get("id", "")
    if app_id:
        client.set_app_id(app_id)

    response: dict[str, Any] = {"id": app_id, "name": result.get("name"), "mode": app_mode}

    # Auto-initialize workflow
    if app_mode in ("workflow", "advanced-chat") and app_id:
        try:
            init_result = await client.initialize_workflow(app_id)
            response["start_node_id"] = init_result.get("start_node_id")
            response["initialized"] = True
        except PulseClientError as e:
            response["initialized"] = False
            response["init_error"] = str(e)

    return [TextContent(type="text", text=_compact_json(response))]


async def handle_initialize_workflow(args: dict[str, Any], client: PulseClient) -> list[TextContent]:
    result = await client.initialize_workflow(args.get("app_id"))
    return [
        TextContent(
            type="text",
            text=_compact_json(
                {
                    "start_node_id": result.get("start_node_id"),
                    "node_count": len(result.get("graph", {}).get("nodes", [])),
                }
            ),
        )
    ]


async def handle_view_workflow(args: dict[str, Any], client: PulseClient) -> list[TextContent]:
    workflow = await client.get_workflow(args.get("app_id"))
    graph = workflow.get("graph", {"nodes": [], "edges": []})

    nodes = [
        {"id": n["id"], "type": n.get("data", {}).get("type"), "title": n.get("data", {}).get("title")}
        for n in graph.get("nodes", [])
    ]
    edges = [
        {
            "source": e["source"],
            "target": e["target"],
            "source_handle": e.get("sourceHandle"),
            "target_handle": e.get("targetHandle"),
        }
        for e in graph.get("edges", [])
    ]

    response: dict[str, Any] = {"nodes": nodes, "edges": edges, "hash": workflow.get("hash", "")[:12]}

    if args.get("include_details"):
        response["full"] = workflow

    return [TextContent(type="text", text=_compact_json(response))]


async def handle_validate_workflow(_args: dict[str, Any], client: PulseClient) -> list[TextContent]:
    result = await client.validate_workflow()
    return [
        TextContent(
            type="text",
            text=_compact_json({"valid": result["valid"], "errors": result["errors"], "warnings": result["warnings"]}),
        )
    ]


async def handle_publish_workflow(args: dict[str, Any], client: PulseClient) -> list[TextContent]:
    result = await client.publish_workflow(name=args.get("name"), comment=args.get("comment"))
    return [TextContent(type="text", text=_compact_json({"published": True, "created_at": result.get("created_at")}))]


async def handle_add_node(args: dict[str, Any], client: PulseClient) -> list[TextContent]:
    result = await client.add_node(
        node_type=args["node_type"],
        title=args.get("title"),
        config=args.get("config"),
        position=args.get("position"),
        after_node_id=args.get("after_node_id"),
        source_handle=args.get("source_handle", "source"),
        target_handle=args.get("target_handle", "target"),
    )
    return [TextContent(type="text", text=_compact_json({"node_id": result["node_id"]}))]


async def handle_edit_node(args: dict[str, Any], client: PulseClient) -> list[TextContent]:
    updates: dict[str, Any] = {}
    for key in ["title", "config", "position"]:
        if key in args:
            updates[key] = args[key]
    await client.edit_node(node_id=args["node_id"], updates=updates)
    return [TextContent(type="text", text=_compact_json({"updated": args["node_id"]}))]


async def handle_delete_node(args: dict[str, Any], client: PulseClient) -> list[TextContent]:
    await client.delete_node(node_id=args["node_id"])
    return [TextContent(type="text", text=_compact_json({"deleted": args["node_id"]}))]


async def handle_get_node(args: dict[str, Any], client: PulseClient) -> list[TextContent]:
    node = await client.get_node(node_id=args["node_id"])
    if node is None:
        return [TextContent(type="text", text=_compact_json({"error": "not_found"}))]
    return [TextContent(type="text", text=_compact_json(node))]


async def handle_list_nodes(args: dict[str, Any], client: PulseClient) -> list[TextContent]:
    nodes = await client.list_nodes(filter_type=args.get("filter_type"))
    result = [
        {"id": n["id"], "type": n.get("data", {}).get("type"), "title": n.get("data", {}).get("title")} for n in nodes
    ]
    return [TextContent(type="text", text=_compact_json(result))]


async def handle_batch_add_nodes(args: dict[str, Any], client: PulseClient) -> list[TextContent]:
    workflow = await client.get_workflow()
    graph = workflow.get("graph", {"nodes": [], "edges": []})
    features = workflow.get("features")
    current_hash = workflow.get("hash")

    new_node_ids = []
    for node_spec in args.get("nodes", []):
        new_node = client.create_node(
            node_type=node_spec["node_type"],
            title=node_spec.get("title"),
            config=node_spec.get("config"),
            position=node_spec.get("position"),
            graph=graph,
        )
        graph["nodes"].append(new_node)
        new_node_ids.append(new_node["id"])

    # Process connections
    for conn in args.get("connections", []):
        # Resolve source (index or ID)
        source = conn.get("source_idx")
        if source is not None:
            source_id = new_node_ids[source]
        else:
            source_id = conn.get("source_id", "")

        # Resolve target (index or ID)
        target = conn.get("target_idx")
        if target is not None:
            target_id = new_node_ids[target]
        else:
            target_id = conn.get("target_id", "")

        if source_id and target_id:
            edge = client.create_edge(
                source_id,
                target_id,
                conn.get("source_handle", "source"),
                conn.get("target_handle", "target"),
            )
            graph["edges"].append(edge)

    await client.sync_workflow(graph, features, hash_value=current_hash)
    return [TextContent(type="text", text=_compact_json({"node_ids": new_node_ids}))]


async def handle_add_note(args: dict[str, Any], client: PulseClient) -> list[TextContent]:
    result = await client.add_note(
        text=args["text"],
        theme=args.get("theme", "yellow"),
        position=args.get("position"),
        author=args.get("author", ""),
        show_author=args.get("show_author", False),
        width=args.get("width", 240),
        height=args.get("height", 88),
    )
    return [TextContent(type="text", text=_compact_json({"note_id": result["note_id"]}))]


async def handle_edit_note(args: dict[str, Any], client: PulseClient) -> list[TextContent]:
    await client.edit_note(
        note_id=args["note_id"],
        text=args.get("text"),
        theme=args.get("theme"),
        author=args.get("author"),
        show_author=args.get("show_author"),
        position=args.get("position"),
        width=args.get("width"),
        height=args.get("height"),
    )
    return [TextContent(type="text", text=_compact_json({"updated": args["note_id"]}))]


async def handle_list_notes(_args: dict[str, Any], client: PulseClient) -> list[TextContent]:
    notes = await client.list_notes()
    result = [
        {
            "id": n["id"],
            "theme": n.get("data", {}).get("theme"),
            "text": _extract_text_from_lexical(n.get("data", {}).get("text", "")),
        }
        for n in notes
    ]
    return [TextContent(type="text", text=_compact_json(result))]


async def handle_delete_note(args: dict[str, Any], client: PulseClient) -> list[TextContent]:
    await client.delete_note(note_id=args["note_id"])
    return [TextContent(type="text", text=_compact_json({"deleted": args["note_id"]}))]


async def handle_connect_nodes(args: dict[str, Any], client: PulseClient) -> list[TextContent]:
    result = await client.connect_nodes(
        source_id=args["source_id"],
        target_id=args["target_id"],
        source_handle=args.get("source_handle", "source"),
        target_handle=args.get("target_handle", "target"),
    )
    return [
        TextContent(
            type="text", text=_compact_json({"edge_id": result["edge_id"], "existed": result.get("existed", False)})
        )
    ]


async def handle_disconnect_nodes(args: dict[str, Any], client: PulseClient) -> list[TextContent]:
    result = await client.disconnect_nodes(
        source_id=args["source_id"],
        target_id=args["target_id"],
        source_handle=args.get("source_handle"),
        target_handle=args.get("target_handle"),
    )
    return [TextContent(type="text", text=_compact_json({"removed": result["removed_count"]}))]


async def handle_list_edges(_args: dict[str, Any], client: PulseClient) -> list[TextContent]:
    edges = await client.list_edges()
    result = [{"id": e["id"], "source": e["source"], "target": e["target"]} for e in edges]
    return [TextContent(type="text", text=_compact_json(result))]


async def handle_list_node_types(args: dict[str, Any], client: PulseClient) -> list[TextContent]:
    node_types = await client.list_node_types(args.get("app_id"))

    # Extract types that have default configs from API response
    types_with_config: set[str] = set()
    if isinstance(node_types, dict):
        types_with_config = set(node_types.keys())
    elif isinstance(node_types, list):
        for t in node_types:
            if isinstance(t, dict):
                node_type = t.get("type")
                if node_type and isinstance(node_type, str):
                    types_with_config.add(node_type)
            elif isinstance(t, str):
                types_with_config.add(t)

    result = {"types": ALL_NODE_TYPES, "with_default_config": sorted(types_with_config)}
    return [TextContent(type="text", text=_compact_json(result))]


async def handle_get_node_schema(args: dict[str, Any], client: PulseClient) -> list[TextContent]:
    block_type = args["block_type"]
    schema = await client.get_node_schema(block_type, args.get("app_id"))
    if not schema:
        guidance = NODE_CONFIG_GUIDANCE.get(block_type)
        if guidance:
            return [TextContent(type="text", text=_compact_json({"note": guidance}))]
        return [
            TextContent(
                type="text",
                text=_compact_json(
                    {"note": f"No default schema for '{block_type}'. Check existing workflows for examples."}
                ),
            )
        ]
    return [TextContent(type="text", text=_compact_json(schema))]


async def handle_list_models(args: dict[str, Any], client: PulseClient) -> list[TextContent]:
    models = await client.list_models(args.get("model_type", "llm"))
    result = [
        {
            "provider": m.get("provider", m.get("provider_name")),
            "model": m.get("model", m.get("name")),
            "type": m.get("model_type"),
        }
        for m in models
    ]
    return [TextContent(type="text", text=_compact_json(result))]


async def handle_list_tool_providers(_args: dict[str, Any], client: PulseClient) -> list[TextContent]:
    providers = await client.list_tool_providers()
    result = []
    for p in providers:
        provider_type = p.get("type", "builtin")
        tools_list = p.get("tools", [])
        label = p.get("label") or {}
        if isinstance(label, dict):
            label = label.get("en_US") or label.get("zh_Hans") or p.get("name")
        entry: dict[str, Any] = {
            "id": p.get("id", p.get("name")),
            "name": p.get("name"),
            "label": label,
            "type": provider_type,
            "is_team_authorization": p.get("is_team_authorization", False),
        }
        if p.get("plugin_unique_identifier"):
            entry["plugin_unique_identifier"] = p.get("plugin_unique_identifier")
        if tools_list:
            entry["tool_count"] = len(tools_list)
        result.append(entry)
    return [TextContent(type="text", text=_compact_json(result))]


async def handle_list_tools(args: dict[str, Any], client: PulseClient) -> list[TextContent]:
    tools = await client.list_tools(args.get("provider_id"), args.get("tool_type", "builtin"))
    result = []
    for t in tools:
        desc = t.get("description") or ""
        if isinstance(desc, dict):
            desc = desc.get("en_US") or desc.get("zh_Hans") or str(desc)
        label = t.get("label") or {}
        if isinstance(label, dict):
            label = label.get("en_US") or label.get("zh_Hans") or t.get("name") or "unknown"

        params = []
        for p in t.get("parameters") or []:
            param_info: dict[str, Any] = {
                "name": p.get("name"),
                "type": p.get("type"),
                "form": p.get("form"),
                "required": p.get("required", False),
            }
            p_desc = p.get("human_description") or p.get("llm_description") or ""
            if isinstance(p_desc, dict):
                p_desc = p_desc.get("en_US") or p_desc.get("zh_Hans") or ""
            if p_desc:
                param_info["description"] = p_desc[:100]
            if p.get("default") is not None:
                param_info["default"] = p.get("default")
            if p.get("options"):
                param_info["options"] = [
                    {"value": o.get("value"), "label": o.get("label", {}).get("en_US") or o.get("value")}
                    for o in p.get("options", [])
                ]
            params.append(param_info)

        tool_info: dict[str, Any] = {
            "name": t.get("name"),
            "label": label,
            "description": desc[:200] if isinstance(desc, str) else str(desc)[:200],
        }
        if params:
            tool_info["parameters"] = params
        result.append(tool_info)
    return [TextContent(type="text", text=_compact_json(result))]


async def handle_list_agent_strategies(_args: dict[str, Any], client: PulseClient) -> list[TextContent]:
    providers = await client.list_agent_strategies()
    result = []
    for p in providers:
        declaration = p.get("declaration", {})
        identity = declaration.get("identity", {})
        label = identity.get("label", {})
        if isinstance(label, dict):
            label = label.get("en_US") or label.get("zh_Hans") or identity.get("name", "")
        strategies = []
        for s in declaration.get("strategies", []):
            s_identity = s.get("identity", {})
            s_label = s_identity.get("label", {})
            if isinstance(s_label, dict):
                s_label = s_label.get("en_US") or s_label.get("zh_Hans") or s_identity.get("name", "")
            strategies.append({"name": s_identity.get("name"), "label": s_label})
        result.append(
            {
                "provider": p.get("provider"),
                "plugin_id": p.get("plugin_id"),
                "plugin_unique_identifier": p.get("plugin_unique_identifier"),
                "label": label,
                "strategies": strategies,
            }
        )
    return [TextContent(type="text", text=_compact_json(result))]


async def handle_get_agent_strategy(args: dict[str, Any], client: PulseClient) -> list[TextContent]:
    provider_name = args["provider_name"]
    strategy_data = await client.get_agent_strategy(provider_name)
    declaration = strategy_data.get("declaration", {})
    result: dict[str, Any] = {
        "provider": strategy_data.get("provider"),
        "plugin_unique_identifier": strategy_data.get("plugin_unique_identifier"),
        "strategies": [],
    }
    for s in declaration.get("strategies", []):
        s_identity = s.get("identity", {})
        s_label = s_identity.get("label", {})
        if isinstance(s_label, dict):
            s_label = s_label.get("en_US") or s_label.get("zh_Hans") or s_identity.get("name", "")
        params = []
        for p in s.get("parameters", []):
            p_label = p.get("label", {})
            if isinstance(p_label, dict):
                p_label = p_label.get("en_US") or p_label.get("zh_Hans") or p.get("name", "")
            p_help = p.get("help", {})
            if isinstance(p_help, dict):
                p_help = p_help.get("en_US") or p_help.get("zh_Hans") or ""
            param_info: dict[str, Any] = {
                "name": p.get("name"),
                "label": p_label,
                "type": p.get("type"),
                "required": p.get("required", False),
            }
            if p_help:
                param_info["help"] = p_help[:100]
            if p.get("default") is not None:
                param_info["default"] = p.get("default")
            if p.get("options"):
                param_info["options"] = p.get("options")
            params.append(param_info)
        result["strategies"].append(
            {
                "name": s_identity.get("name"),
                "label": s_label,
                "parameters": params,
                "output_schema": s.get("output_schema"),
            }
        )
    return [TextContent(type="text", text=_compact_json(result))]


async def handle_list_datasets(args: dict[str, Any], client: PulseClient) -> list[TextContent]:
    result = await client.list_datasets(limit=args.get("limit", 50))
    datasets = [
        {"id": d["id"], "name": d.get("name"), "docs": d.get("document_count", 0)} for d in result.get("data", [])
    ]
    return [TextContent(type="text", text=_compact_json({"datasets": datasets, "total": result.get("total")}))]


async def handle_get_dataset(args: dict[str, Any], client: PulseClient) -> list[TextContent]:
    dataset = await client.get_dataset(args["dataset_id"])
    return [
        TextContent(
            type="text",
            text=_compact_json(
                {
                    "id": dataset.get("id"),
                    "name": dataset.get("name"),
                    "docs": dataset.get("document_count"),
                    "words": dataset.get("word_count"),
                    "indexing": dataset.get("indexing_technique"),
                    "embedding_model": dataset.get("embedding_model"),
                }
            ),
        )
    ]


async def handle_list_documents(args: dict[str, Any], client: PulseClient) -> list[TextContent]:
    result = await client.list_documents(
        dataset_id=args["dataset_id"],
        page=args.get("page", 1),
        limit=args.get("limit", 20),
        keyword=args.get("keyword"),
    )
    docs = [
        {"id": d["id"], "name": d.get("name"), "words": d.get("word_count"), "status": d.get("indexing_status")}
        for d in result.get("data", [])
    ]
    return [
        TextContent(
            type="text",
            text=_compact_json({"docs": docs, "total": result.get("total"), "has_more": result.get("has_more")}),
        )
    ]


async def handle_get_document(args: dict[str, Any], client: PulseClient) -> list[TextContent]:
    doc = await client.get_document(args["dataset_id"], args["document_id"])
    return [
        TextContent(
            type="text",
            text=_compact_json(
                {
                    "id": doc.get("id"),
                    "name": doc.get("name"),
                    "words": doc.get("word_count"),
                    "tokens": doc.get("tokens"),
                    "segments": doc.get("segment_count"),
                    "status": doc.get("indexing_status"),
                }
            ),
        )
    ]


async def handle_search_dataset(args: dict[str, Any], client: PulseClient) -> list[TextContent]:
    retrieval_model = {
        "search_method": args.get("search_method", "semantic_search"),
        "reranking_enable": False,
        "top_k": args.get("top_k", 5),
        "score_threshold_enabled": False,
    }
    result = await client.search_dataset(
        dataset_id=args["dataset_id"],
        query=args["query"],
        retrieval_model=retrieval_model,
        top_k=args.get("top_k", 5),
    )
    records = [
        {
            "score": round(r.get("score", 0), 4),
            "content": r.get("segment", {}).get("content", "")[:200],
            "doc": r.get("document_name"),
        }
        for r in result.get("records", [])
    ]
    return [TextContent(type="text", text=_compact_json({"results": records}))]


async def handle_get_features(_args: dict[str, Any], client: PulseClient) -> list[TextContent]:
    features = await client.get_features()
    return [TextContent(type="text", text=_compact_json(features))]


async def handle_update_features(args: dict[str, Any], client: PulseClient) -> list[TextContent]:
    features_update = {k: v for k, v in args.items() if v is not None}
    await client.update_features(features_update)
    return [TextContent(type="text", text=_compact_json({"updated": True}))]


async def handle_get_variables(_args: dict[str, Any], client: PulseClient) -> list[TextContent]:
    variables = await client.get_variables()
    return [TextContent(type="text", text=_compact_json(variables))]


async def handle_run_node(args: dict[str, Any], client: PulseClient) -> list[TextContent]:
    result = await client.run_node(
        node_id=args["node_id"],
        inputs=args.get("inputs"),
        query=args.get("query"),
    )
    return [
        TextContent(
            type="text",
            text=_compact_json(
                {
                    "status": result.get("status"),
                    "elapsed": result.get("elapsed_time"),
                    "outputs": result.get("outputs"),
                }
            ),
        )
    ]


# ============================================================
# Tool Dispatch Table
# ============================================================

TOOL_HANDLERS: dict[str, ToolHandler] = {
    # App Management
    "list_apps": handle_list_apps,
    "select_app": handle_select_app,
    "create_app": handle_create_app,
    "initialize_workflow": handle_initialize_workflow,
    # Workflow Operations
    "view_workflow": handle_view_workflow,
    "validate_workflow": handle_validate_workflow,
    "publish_workflow": handle_publish_workflow,
    # Node Operations
    "add_node": handle_add_node,
    "edit_node": handle_edit_node,
    "delete_node": handle_delete_node,
    "get_node": handle_get_node,
    "list_nodes": handle_list_nodes,
    # Batch Operations
    "batch_add_nodes": handle_batch_add_nodes,
    # Sticky Notes
    "add_note": handle_add_note,
    "edit_note": handle_edit_note,
    "list_notes": handle_list_notes,
    "delete_note": handle_delete_note,
    # Edge Operations
    "connect_nodes": handle_connect_nodes,
    "disconnect_nodes": handle_disconnect_nodes,
    "list_edges": handle_list_edges,
    # Discovery
    "list_node_types": handle_list_node_types,
    "get_node_schema": handle_get_node_schema,
    "list_models": handle_list_models,
    "list_tool_providers": handle_list_tool_providers,
    "list_tools": handle_list_tools,
    # Agent Strategies
    "list_agent_strategies": handle_list_agent_strategies,
    "get_agent_strategy": handle_get_agent_strategy,
    # Knowledge Base
    "list_datasets": handle_list_datasets,
    "get_dataset": handle_get_dataset,
    "list_documents": handle_list_documents,
    "get_document": handle_get_document,
    "search_dataset": handle_search_dataset,
    # Features & Variables
    "get_features": handle_get_features,
    "update_features": handle_update_features,
    "get_variables": handle_get_variables,
    # Testing
    "run_node": handle_run_node,
}


def _get_all_tools() -> list[Tool]:
    """Get all available tools with concise descriptions."""
    return [
        # === App Management ===
        Tool(
            name="list_apps",
            description="List apps. Returns: [{id, name, mode}]",
            inputSchema={
                "type": "object",
                "properties": {
                    "mode": {
                        "type": "string",
                        "enum": ["workflow", "advanced-chat", "chat", "completion", "agent-chat"],
                    },
                    "name": {"type": "string", "description": "Filter by name"},
                    "limit": {"type": "integer", "default": 20},
                },
            },
        ),
        Tool(
            name="select_app",
            description="Select app for subsequent operations",
            inputSchema={
                "type": "object",
                "properties": {"app_id": {"type": "string"}},
                "required": ["app_id"],
            },
        ),
        Tool(
            name="create_app",
            description="Create app and auto-initialize workflow. Returns: {id, name, mode, start_node_id}",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "mode": {"type": "string", "enum": ["workflow", "advanced-chat"], "default": "workflow"},
                    "description": {"type": "string"},
                    "icon": {"type": "string", "default": "\U0001f916"},
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="initialize_workflow",
            description="Initialize workflow draft (auto-called by create_app)",
            inputSchema={
                "type": "object",
                "properties": {"app_id": {"type": "string"}},
            },
        ),
        # === Workflow Operations ===
        Tool(
            name="view_workflow",
            description="View workflow structure. Returns: {nodes:[{id,type,title}], edges:[{source,target}]}",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_id": {"type": "string"},
                    "include_details": {"type": "boolean", "default": False},
                },
            },
        ),
        Tool(
            name="validate_workflow",
            description="Check for errors. Returns: {valid, errors[], warnings[]}",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="publish_workflow",
            description="Publish draft as new version",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "maxLength": 20},
                    "comment": {"type": "string", "maxLength": 100},
                },
            },
        ),
        # === Node Operations ===
        Tool(
            name="add_node",
            description="Add node. Returns: {node_id}. Use get_node_schema first for config format.",
            inputSchema={
                "type": "object",
                "properties": {
                    "node_type": {"type": "string", "enum": ALL_NODE_TYPES},
                    "title": {"type": "string"},
                    "config": {"type": "object"},
                    "position": {"type": "object", "properties": {"x": {"type": "number"}, "y": {"type": "number"}}},
                    "after_node_id": {"type": "string", "description": "Connect from this node"},
                    "source_handle": {"type": "string", "default": "source"},
                    "target_handle": {"type": "string", "default": "target"},
                },
                "required": ["node_type"],
            },
        ),
        Tool(
            name="edit_node",
            description="Update node (PATCH-style, only include changed fields)",
            inputSchema={
                "type": "object",
                "properties": {
                    "node_id": {"type": "string"},
                    "title": {"type": "string"},
                    "config": {"type": "object"},
                    "position": {"type": "object"},
                },
                "required": ["node_id"],
            },
        ),
        Tool(
            name="delete_node",
            description="Delete node and its edges",
            inputSchema={
                "type": "object",
                "properties": {"node_id": {"type": "string"}},
                "required": ["node_id"],
            },
        ),
        Tool(
            name="get_node",
            description="Get node details",
            inputSchema={
                "type": "object",
                "properties": {"node_id": {"type": "string"}},
                "required": ["node_id"],
            },
        ),
        Tool(
            name="list_nodes",
            description="List nodes. Returns: [{id, type, title}]",
            inputSchema={
                "type": "object",
                "properties": {"filter_type": {"type": "string"}},
            },
        ),
        # === Batch Operations ===
        Tool(
            name="batch_add_nodes",
            description="Add multiple nodes at once. More efficient than multiple add_node calls.",
            inputSchema={
                "type": "object",
                "properties": {
                    "nodes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "node_type": {"type": "string"},
                                "title": {"type": "string"},
                                "config": {"type": "object"},
                                "position": {"type": "object"},
                            },
                            "required": ["node_type"],
                        },
                    },
                    "connections": {
                        "type": "array",
                        "description": "Edges to create: [{source_idx|source_id, target_idx|target_id, source_handle?, target_handle?}]",
                        "items": {"type": "object"},
                    },
                },
                "required": ["nodes"],
            },
        ),
        # === Sticky Notes ===
        Tool(
            name="add_note",
            description="Add documentation note to canvas (visual only, not executed). Text supports newlines for paragraphs.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Note content (plain text, newlines create paragraphs)"},
                    "theme": {
                        "type": "string",
                        "enum": ["blue", "cyan", "green", "yellow", "pink", "violet"],
                        "default": "yellow",
                    },
                    "position": {"type": "object"},
                    "author": {"type": "string"},
                    "show_author": {"type": "boolean", "default": False},
                    "width": {"type": "integer", "default": 240, "description": "Note width in pixels (min 240)"},
                    "height": {"type": "integer", "default": 88, "description": "Note height in pixels (min 88)"},
                },
                "required": ["text"],
            },
        ),
        Tool(
            name="edit_note",
            description="Update sticky note",
            inputSchema={
                "type": "object",
                "properties": {
                    "note_id": {"type": "string"},
                    "text": {"type": "string"},
                    "theme": {"type": "string", "enum": ["blue", "cyan", "green", "yellow", "pink", "violet"]},
                    "position": {"type": "object"},
                    "author": {"type": "string"},
                    "show_author": {"type": "boolean"},
                    "width": {"type": "integer", "description": "Note width in pixels (min 240)"},
                    "height": {"type": "integer", "description": "Note height in pixels (min 88)"},
                },
                "required": ["note_id"],
            },
        ),
        Tool(
            name="list_notes",
            description="List sticky notes",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="delete_note",
            description="Delete sticky note",
            inputSchema={
                "type": "object",
                "properties": {"note_id": {"type": "string"}},
                "required": ["note_id"],
            },
        ),
        # === Edge Operations ===
        Tool(
            name="connect_nodes",
            description="Create edge between nodes",
            inputSchema={
                "type": "object",
                "properties": {
                    "source_id": {"type": "string"},
                    "target_id": {"type": "string"},
                    "source_handle": {"type": "string", "default": "source"},
                    "target_handle": {"type": "string", "default": "target"},
                },
                "required": ["source_id", "target_id"],
            },
        ),
        Tool(
            name="disconnect_nodes",
            description="Remove edge between nodes",
            inputSchema={
                "type": "object",
                "properties": {
                    "source_id": {"type": "string"},
                    "target_id": {"type": "string"},
                    "source_handle": {"type": "string"},
                    "target_handle": {"type": "string"},
                },
                "required": ["source_id", "target_id"],
            },
        ),
        Tool(
            name="list_edges",
            description="List edges. Returns: [{id, source, target}]",
            inputSchema={"type": "object", "properties": {}},
        ),
        # === Discovery (call before configuring nodes) ===
        Tool(
            name="list_node_types",
            description="REQUIRED before add_node. Lists available node types.",
            inputSchema={
                "type": "object",
                "properties": {"app_id": {"type": "string"}},
            },
        ),
        Tool(
            name="get_node_schema",
            description="REQUIRED before configuring a node. Get config schema for node type.",
            inputSchema={
                "type": "object",
                "properties": {
                    "block_type": {"type": "string", "description": "e.g., 'llm', 'code', 'http-request'"},
                    "app_id": {"type": "string"},
                },
                "required": ["block_type"],
            },
        ),
        Tool(
            name="list_models",
            description="List AI models for LLM nodes. Returns: [{provider, model, model_type}]",
            inputSchema={
                "type": "object",
                "properties": {
                    "model_type": {
                        "type": "string",
                        "enum": ["llm", "text-embedding", "rerank", "speech2text", "tts"],
                        "default": "llm",
                    },
                },
            },
        ),
        Tool(
            name="list_tool_providers",
            description="List external tool providers",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="list_tools",
            description="List tools from a provider with full schemas for agent configuration. Returns tool names, parameters (with form type, required, defaults).",
            inputSchema={
                "type": "object",
                "properties": {
                    "provider_id": {"type": "string", "description": "Provider ID (e.g., 'pulse/btf/btf' for plugins)"},
                    "tool_type": {
                        "type": "string",
                        "enum": ["builtin", "workflow", "api", "mcp"],
                        "default": "builtin",
                    },
                },
            },
        ),
        # === Agent Strategies ===
        Tool(
            name="list_agent_strategies",
            description="List agent strategy providers for agent nodes. Returns providers with strategy names. Use get_agent_strategy for parameters.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_agent_strategy",
            description="Get agent strategy details including required parameters (instruction, query, model, tools, etc.) for agent_parameters config.",
            inputSchema={
                "type": "object",
                "properties": {
                    "provider_name": {
                        "type": "string",
                        "description": "Provider name (e.g., 'langgenius/agent/cot_agent_with_memory')",
                    },
                },
                "required": ["provider_name"],
            },
        ),
        # === Knowledge Base ===
        Tool(
            name="list_datasets",
            description="List knowledge bases for RAG",
            inputSchema={
                "type": "object",
                "properties": {"limit": {"type": "integer", "default": 50}},
            },
        ),
        Tool(
            name="get_dataset",
            description="Get dataset details",
            inputSchema={
                "type": "object",
                "properties": {"dataset_id": {"type": "string"}},
                "required": ["dataset_id"],
            },
        ),
        Tool(
            name="list_documents",
            description="List documents in dataset",
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_id": {"type": "string"},
                    "page": {"type": "integer", "default": 1},
                    "limit": {"type": "integer", "default": 20},
                    "keyword": {"type": "string"},
                },
                "required": ["dataset_id"],
            },
        ),
        Tool(
            name="get_document",
            description="Get document details",
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_id": {"type": "string"},
                    "document_id": {"type": "string"},
                },
                "required": ["dataset_id", "document_id"],
            },
        ),
        Tool(
            name="search_dataset",
            description="Query knowledge base (hit testing). Returns: [{score, content, document_name}]",
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_id": {"type": "string"},
                    "query": {"type": "string"},
                    "top_k": {"type": "integer", "default": 5},
                    "search_method": {
                        "type": "string",
                        "enum": ["semantic_search", "full_text_search", "hybrid_search"],
                        "default": "semantic_search",
                    },
                },
                "required": ["dataset_id", "query"],
            },
        ),
        # === Features & Variables ===
        Tool(
            name="get_features",
            description="Get workflow features config",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="update_features",
            description="Update features (partial)",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_upload": {"type": "object"},
                    "opening_statement": {"type": "string"},
                    "suggested_questions": {"type": "array", "items": {"type": "string"}},
                },
            },
        ),
        Tool(
            name="get_variables",
            description="Get environment and conversation variables",
            inputSchema={"type": "object", "properties": {}},
        ),
        # === Testing ===
        Tool(
            name="run_node",
            description="Execute single node for testing",
            inputSchema={
                "type": "object",
                "properties": {
                    "node_id": {"type": "string"},
                    "inputs": {"type": "object"},
                    "query": {"type": "string"},
                },
                "required": ["node_id"],
            },
        ),
    ]


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools."""
    return _get_all_tools()


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
    """Handle tool calls using dispatch table."""
    # Ensure arguments is a dict
    if arguments is None:
        arguments = {}
    elif not isinstance(arguments, dict):
        return [
            TextContent(
                type="text", text=_compact_json({"error": f"Invalid arguments type: {type(arguments).__name__}"})
            )
        ]

    client = get_client()

    # Look up handler in dispatch table
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        return [TextContent(type="text", text=_compact_json({"error": f"Unknown tool: {name}"}))]

    try:
        return await handler(arguments, client)
    except PulseClientError as e:
        return [TextContent(type="text", text=_compact_json({"error": str(e), "status": e.status_code}))]


# Register resources and prompts
register_workflow_resources(server)
register_workflow_prompts(server)


async def run_server() -> None:
    """Run the MCP server."""
    try:
        config = init_config()
        logger.info(f"Connecting to Pulse at {config.api_url}")
        if config.app_id:
            logger.info(f"Default app ID: {config.app_id}")
        else:
            logger.info("No default app ID. Use list_apps and select_app.")

        init_client()

        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Server stopped")
    finally:
        # Clean up HTTP client resources
        await cleanup_client()


def main() -> None:
    """Entry point for the MCP server."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
