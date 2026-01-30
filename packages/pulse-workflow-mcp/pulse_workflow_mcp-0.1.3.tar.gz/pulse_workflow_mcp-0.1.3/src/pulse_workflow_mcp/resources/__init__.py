"""MCP resources for Dify workflow state."""

from .node_types import NODE_TYPES_SCHEMA
from .workflow_resource import register_workflow_resources

__all__ = [
    "register_workflow_resources",
    "NODE_TYPES_SCHEMA",
]
