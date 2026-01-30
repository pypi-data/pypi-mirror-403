"""MCP resource for current workflow state."""

import json

from mcp.server import Server
from mcp.types import Resource, TextResourceContents

from ..dify_client import get_client
from .node_types import NODE_TYPES_SCHEMA


def register_workflow_resources(server: Server) -> None:
    """Register workflow resources with the MCP server."""

    @server.list_resources()
    async def list_resources() -> list[Resource]:
        return [
            Resource(
                uri="pulse://workflow/current",
                name="Current Workflow",
                description="The current draft workflow structure including nodes, edges, and configuration",
                mimeType="application/json",
            ),
            Resource(
                uri="pulse://workflow/node-types",
                name="Available Node Types",
                description="List of available node types with their configuration schemas",
                mimeType="application/json",
            ),
            Resource(
                uri="pulse://workflow/summary",
                name="Workflow Summary",
                description="Human-readable summary of the current workflow",
                mimeType="text/markdown",
            ),
        ]

    @server.read_resource()
    async def read_resource(uri: str) -> str | TextResourceContents:
        client = get_client()

        if uri == "pulse://workflow/current":
            workflow = await client.get_workflow()
            return json.dumps(workflow, indent=2)

        elif uri == "pulse://workflow/node-types":
            return json.dumps(NODE_TYPES_SCHEMA, indent=2)

        elif uri == "pulse://workflow/summary":
            workflow = await client.get_workflow()
            graph = workflow.get("graph", {"nodes": [], "edges": []})
            nodes = graph.get("nodes", [])
            edges = graph.get("edges", [])

            summary = "# Workflow Summary\n\n"
            summary += f"**Hash:** `{workflow.get('hash', 'N/A')[:12]}...`\n"
            summary += f"**Total Nodes:** {len(nodes)}\n"
            summary += f"**Total Edges:** {len(edges)}\n\n"

            node_by_type: dict[str, list[dict]] = {}
            for node in nodes:
                node_type = node.get("data", {}).get("type", "unknown")
                if node_type not in node_by_type:
                    node_by_type[node_type] = []
                node_by_type[node_type].append(node)

            summary += "## Nodes by Type\n\n"
            for node_type, type_nodes in sorted(node_by_type.items()):
                summary += f"### {node_type} ({len(type_nodes)})\n\n"
                for node in type_nodes:
                    node_data = node.get("data", {})
                    title = node_data.get("title", "Untitled")
                    summary += f"- **{title}** (`{node['id']}`)\n"

            summary += "\n## Flow\n\n"
            node_titles = {n["id"]: n.get("data", {}).get("title", n["id"][:8]) for n in nodes}

            start_nodes = [n for n in nodes if n.get("data", {}).get("type") == "start"]
            if start_nodes:
                summary += "```\n"
                visited = set()

                def trace_flow(node_id: str, indent: int = 0) -> None:
                    nonlocal summary
                    if node_id in visited:
                        return
                    visited.add(node_id)

                    title = node_titles.get(node_id, node_id[:8])
                    summary += "  " * indent + f"└─ {title}\n"

                    outgoing = [e for e in edges if e["source"] == node_id]
                    for edge in outgoing:
                        trace_flow(edge["target"], indent + 1)

                for start in start_nodes:
                    trace_flow(start["id"])
                summary += "```\n"

            return summary

        raise ValueError(f"Unknown resource URI: {uri}")
