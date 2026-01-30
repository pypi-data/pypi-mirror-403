"""Pulse API client for workflow operations."""

import json
import uuid
from enum import StrEnum
from typing import Any

import httpx

from .config import get_config


class NodeType(StrEnum):
    """Valid workflow node types."""

    START = "start"
    END = "end"
    ANSWER = "answer"
    LLM = "llm"
    KNOWLEDGE_RETRIEVAL = "knowledge-retrieval"
    KNOWLEDGE_INDEX = "knowledge-index"
    IF_ELSE = "if-else"
    CODE = "code"
    TEMPLATE_TRANSFORM = "template-transform"
    QUESTION_CLASSIFIER = "question-classifier"
    HTTP_REQUEST = "http-request"
    TOOL = "tool"
    DATASOURCE = "datasource"
    VARIABLE_AGGREGATOR = "variable-aggregator"
    LOOP = "loop"
    ITERATION = "iteration"
    PARAMETER_EXTRACTOR = "parameter-extractor"
    ASSIGNER = "assigner"
    DOCUMENT_EXTRACTOR = "document-extractor"
    LIST_OPERATOR = "list-operator"
    AGENT = "agent"
    TRIGGER_WEBHOOK = "trigger-webhook"
    TRIGGER_SCHEDULE = "trigger-schedule"
    TRIGGER_PLUGIN = "trigger-plugin"
    HUMAN_INPUT = "human-input"


class NoteTheme(StrEnum):
    """Valid sticky note themes."""

    BLUE = "blue"
    CYAN = "cyan"
    GREEN = "green"
    YELLOW = "yellow"
    PINK = "pink"
    VIOLET = "violet"


class PulseClientError(Exception):
    """Base exception for Pulse client errors."""

    def __init__(self, message: str, status_code: int | None = None, response: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class WorkflowNotSyncError(PulseClientError):
    """Raised when workflow hash doesn't match (concurrent edit detected)."""

    pass


# Constants
MAX_RETRIES = 3
RETRY_DELAY = 0.5  # seconds
CUSTOM_NODE_TYPE = "custom"
CUSTOM_NOTE_TYPE = "custom-note"

# Default configs for node types with required fields
# These ensure nodes are valid even when config is not provided
# Matches frontend defaults from web/app/components/workflow/nodes/*/default.ts
NODE_DEFAULT_CONFIGS: dict[str, dict] = {
    # Control flow nodes
    "start": {"variables": []},
    "end": {"outputs": []},
    "answer": {"variables": [], "answer": ""},
    "if-else": {
        "_targetBranches": [{"id": "true", "name": "IF"}, {"id": "false", "name": "ELSE"}],
        "cases": [{"case_id": "true", "logical_operator": "and", "conditions": []}],
    },
    "iteration": {
        "start_node_id": "",
        "iterator_selector": [],
        "output_selector": [],
        "_children": [],
        "_isShowTips": False,
        "is_parallel": False,
        "parallel_nums": 10,
        "error_handle_mode": "terminated",
        "flatten_output": True,
    },
    "loop": {
        "start_node_id": "",
        "break_conditions": [],
        "loop_count": 10,
        "_children": [],
        "logical_operator": "and",
    },
    # AI nodes
    "llm": {
        "model": {"provider": "", "name": "", "mode": "chat", "completion_params": {"temperature": 0.7}},
        "prompt_template": [{"role": "system", "text": ""}],
        "context": {"enabled": False, "variable_selector": []},
        "vision": {"enabled": False},
    },
    "agent": {"agent_parameters": {}, "tool_node_version": "2"},
    "knowledge-retrieval": {
        "query_variable_selector": [],
        "query_attachment_selector": [],
        "dataset_ids": [],
        "retrieval_mode": "multiple",
        "multiple_retrieval_config": {
            "top_k": 3,
            "score_threshold": None,
            "reranking_enable": False,
        },
    },
    "question-classifier": {
        "query_variable_selector": [],
        "model": {"provider": "", "name": "", "mode": "chat", "completion_params": {"temperature": 0.7}},
        "classes": [{"id": "1", "name": ""}, {"id": "2", "name": ""}],
        "_targetBranches": [{"id": "1", "name": ""}, {"id": "2", "name": ""}],
        "vision": {"enabled": False},
    },
    "parameter-extractor": {
        "query": [],
        "model": {"provider": "", "name": "", "mode": "chat", "completion_params": {"temperature": 0.7}},
        "parameters": [],
        "reasoning_mode": "prompt",
        "vision": {"enabled": False},
    },
    # Transform nodes
    "code": {"code_language": "python3", "code": "", "variables": [], "outputs": {}},
    "template-transform": {"template": "", "variables": []},
    "document-extractor": {"variable_selector": [], "is_array_file": False},
    "list-operator": {
        "variable": [],
        "filter_by": {"enabled": False, "conditions": []},
        "extract_by": {"enabled": False, "serial": "1"},
        "order_by": {"enabled": False, "key": "", "value": "asc"},
        "limit": {"enabled": False, "size": 10},
    },
    "assigner": {"version": "2", "items": []},
    "variable-assigner": {"output_type": "any", "variables": []},
    "variable-aggregator": {"output_type": "any", "variables": []},
    # External service nodes
    "tool": {"tool_parameters": {}, "tool_configurations": {}, "tool_node_version": "2"},
    "http-request": {
        "variables": [],
        "method": "GET",
        "url": "",
        "authorization": {"type": "no-auth", "config": None},
        "headers": "",
        "params": "",
        "body": {"type": "none", "data": []},
        "ssl_verify": True,
        "timeout": {"max_connect_timeout": 0, "max_read_timeout": 0, "max_write_timeout": 0},
        "retry_config": {"retry_enabled": True, "max_retries": 3, "retry_interval": 100},
    },
    "data-source": {"datasource_parameters": {}, "datasource_configurations": {}},
    # Knowledge base
    "knowledge-base": {
        "index_chunk_variable_selector": [],
        "keyword_number": 10,
        "retrieval_model": {"top_k": 3, "score_threshold_enabled": False, "score_threshold": 0.5},
    },
    # Trigger nodes
    "trigger-plugin": {"plugin_id": "", "event_name": "", "event_parameters": {}, "config": {}},
    "trigger-webhook": {
        "webhook_url": "",
        "method": "POST",
        "content_type": "application/json",
        "headers": [],
        "params": [],
        "body": [],
        "async_mode": True,
        "status_code": 200,
        "response_body": "",
        "variables": [],
    },
    "trigger-schedule": {"mode": "cron", "cron_expression": "", "timezone": "UTC"},
}


class PulseClient:
    """Client for interacting with Pulse workflow API.

    This client manages HTTP connections efficiently by reusing a single
    httpx.AsyncClient instance. Use as an async context manager for proper cleanup:

        async with PulseClient() as client:
            apps = await client.list_apps()

    Or manually manage lifecycle:

        client = PulseClient()
        try:
            apps = await client.list_apps()
        finally:
            await client.close()
    """

    def __init__(
        self,
        api_url: str | None = None,
        api_key: str | None = None,
        app_id: str | None = None,
        timeout: float | None = None,
    ):
        config = get_config()
        self.api_url = api_url or config.api_url
        self.api_key = api_key or config.api_key
        self.app_id = app_id or config.app_id
        self.timeout = timeout or config.timeout

        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Create a reusable HTTP client for connection pooling
        self._http_client: httpx.AsyncClient | None = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client (lazy initialization)."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=self._headers,
                http2=True,  # Enable HTTP/2 for better performance
            )
        return self._http_client

    async def close(self) -> None:
        """Close the HTTP client and release resources."""
        if self._http_client is not None and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None

    async def __aenter__(self) -> "PulseClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit - ensures client cleanup."""
        await self.close()

    def set_app_id(self, app_id: str) -> None:
        """Set the current app ID for subsequent operations."""
        self.app_id = app_id

    def _get_app_id(self, app_id: str | None = None) -> str:
        """Get the app ID to use for an operation."""
        target_app_id = app_id or self.app_id
        if not target_app_id:
            raise PulseClientError(
                "No app_id provided and no default configured. Use list_apps to see available apps, then select one."
            )
        return target_app_id

    @property
    def _console_api_base(self) -> str:
        return f"{self.api_url}/console/api"

    def _workflow_draft_url_for(self, app_id: str | None = None) -> str:
        return f"{self._console_api_base}/apps/{self._get_app_id(app_id)}/workflows/draft"

    @property
    def _workflow_draft_url(self) -> str:
        return self._workflow_draft_url_for()

    async def _request(
        self,
        method: str,
        url: str,
        json_data: dict | None = None,
        params: dict | None = None,
    ) -> dict | None:
        """Make an HTTP request to the Pulse API with retry logic."""
        client = await self._get_http_client()
        last_error: Exception | None = None

        for attempt in range(MAX_RETRIES):
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    json=json_data,
                    params=params,
                )

                if response.status_code == 204:
                    return None

                try:
                    data = response.json()
                except json.JSONDecodeError:
                    data = {"raw": response.text}

                if response.status_code >= 400:
                    error_message = data.get("message", str(data))

                    if "not sync" in error_message.lower() or "hash" in error_message.lower():
                        raise WorkflowNotSyncError(error_message, status_code=response.status_code, response=data)

                    raise PulseClientError(error_message, status_code=response.status_code, response=data)

                return data

            except (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout) as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    import asyncio

                    await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                continue

        raise PulseClientError(f"Request failed after {MAX_RETRIES} retries: {last_error}")

    # ============================================================
    # App Operations
    # ============================================================

    async def list_apps(
        self,
        page: int = 1,
        limit: int = 100,
        mode: str | None = None,
        name: str | None = None,
    ) -> dict:
        """List available apps.

        Args:
            page: Page number
            limit: Items per page (max 100)
            mode: Filter by app mode ('workflow', 'advanced-chat', 'chat', etc.)
            name: Filter by name (partial match)

        Returns:
            Paginated list of apps with id, name, mode, and description
        """
        url = f"{self._console_api_base}/apps"
        params: dict[str, Any] = {"page": page, "limit": min(limit, 100)}
        if mode:
            params["mode"] = mode
        if name:
            params["name"] = name

        result = await self._request("GET", url, params=params)
        return result or {"data": [], "page": page, "limit": limit, "has_more": False, "total": 0}

    async def get_app_detail(self, app_id: str | None = None) -> dict:
        """Get details of a specific app.

        Args:
            app_id: ID of the app (uses default if not provided)

        Returns:
            App details including name, mode, description, etc.
        """
        target_app_id = self._get_app_id(app_id)
        url = f"{self._console_api_base}/apps/{target_app_id}"
        result = await self._request("GET", url)
        return result or {}

    # ============================================================
    # Workflow Operations
    # ============================================================

    async def get_workflow(self, app_id: str | None = None, auto_init: bool = True) -> dict:
        """Get the current draft workflow.

        Args:
            app_id: Optional app ID (uses default if not provided)
            auto_init: If True, automatically initialize workflow if draft doesn't exist

        Returns:
            Workflow object containing graph, features, variables, etc.
        """
        try:
            result = await self._request("GET", self._workflow_draft_url_for(app_id))
            return result or {}
        except PulseClientError as e:
            # Auto-initialize if draft doesn't exist
            if auto_init and "need to be initialized" in str(e).lower():
                init_result = await self.initialize_workflow(app_id)
                # Return the initialized workflow
                return {
                    "graph": init_result.get("graph", {"nodes": [], "edges": []}),
                    "features": init_result.get("features", {}),
                    "hash": init_result.get("result", {}).get("hash", ""),
                }
            raise

    async def sync_workflow(
        self,
        graph: dict,
        features: dict | None = None,
        environment_variables: list[dict] | None = None,
        conversation_variables: list[dict] | None = None,
        hash_value: str | None = None,
    ) -> dict:
        """Sync (create/update) the draft workflow.

        Args:
            graph: The workflow graph containing nodes and edges
            features: Optional workflow features configuration
            environment_variables: Optional environment variables
            conversation_variables: Optional conversation variables
            hash_value: Optional hash for optimistic locking

        Returns:
            Response containing result, hash, and updated_at
        """
        payload: dict[str, Any] = {"graph": graph}

        if features is not None:
            payload["features"] = features
        if environment_variables is not None:
            payload["environment_variables"] = environment_variables
        if conversation_variables is not None:
            payload["conversation_variables"] = conversation_variables
        if hash_value is not None:
            payload["hash"] = hash_value

        try:
            result = await self._request("POST", self._workflow_draft_url, json_data=payload)
            return result or {}
        except PulseClientError as e:
            # If draft needs to be initialized, do so first then retry
            if "need to be initialized" in str(e).lower():
                # Initialize workflow first (this creates the draft)
                await self.initialize_workflow()
                # Now retry the sync without hash (since it's a fresh workflow)
                payload.pop("hash", None)
                result = await self._request("POST", self._workflow_draft_url, json_data=payload)
                return result or {}
            raise

    async def initialize_workflow(self, app_id: str | None = None) -> dict:
        """Initialize a draft workflow for a new app.

        This must be called before adding nodes to a newly created app.
        Creates the initial workflow structure with a start node.

        Args:
            app_id: Optional app ID (uses default if not provided)

        Returns:
            Response containing result, hash, and the initialized workflow
        """
        target_app_id = self._get_app_id(app_id)

        # Get app details to determine mode
        app_detail = await self.get_app_detail(target_app_id)
        app_mode = app_detail.get("mode", "workflow")

        # Create start node
        start_node_id = uuid.uuid4().hex
        start_position = {"x": 80, "y": 282}
        start_node = {
            "id": start_node_id,
            "type": CUSTOM_NODE_TYPE,
            "data": {
                "type": NodeType.START,
                "title": "Start",
                "desc": "",
                "selected": False,
                "variables": [],
            },
            "position": start_position,
            "positionAbsolute": start_position,
            "sourcePosition": "right",
            "targetPosition": "left",
            "selected": False,
        }

        # Initialize graph with start node
        graph: dict[str, Any] = {
            "nodes": [start_node],
            "edges": [],
            "viewport": {"x": 0, "y": 0, "zoom": 1},
        }

        # Default features
        features: dict[str, Any] = {
            "retriever_resource": {"enabled": True},
        }

        # For advanced-chat mode (chatflow), add LLM + answer nodes
        if app_mode == "advanced-chat":
            llm_node_id = uuid.uuid4().hex
            answer_node_id = uuid.uuid4().hex
            llm_position = {"x": 400, "y": 282}
            answer_position = {"x": 720, "y": 282}

            llm_node = {
                "id": llm_node_id,
                "type": CUSTOM_NODE_TYPE,
                "data": {
                    "type": NodeType.LLM,
                    "title": "LLM",
                    "desc": "",
                    "selected": False,
                    "model": {
                        "provider": "",
                        "name": "",
                        "mode": "chat",
                        "completion_params": {},
                    },
                    "prompt_template": [
                        {"role": "system", "text": ""},
                        {"role": "user", "text": "{{#sys.query#}}"},
                    ],
                    "memory": {
                        "role_prefix": {"user": "", "assistant": ""},
                        "window": {"enabled": False, "size": 10},
                    },
                    "context": {"enabled": False, "variable_selector": []},
                    "vision": {"enabled": False},
                    "variables": [],
                },
                "position": llm_position,
                "positionAbsolute": llm_position,
                "sourcePosition": "right",
                "targetPosition": "left",
                "selected": False,
            }

            answer_node = {
                "id": answer_node_id,
                "type": CUSTOM_NODE_TYPE,
                "data": {
                    "type": NodeType.ANSWER,
                    "title": "Answer",
                    "desc": "",
                    "selected": False,
                    "answer": f"{{{{#{llm_node_id}.text#}}}}",
                    "variables": [],
                },
                "position": answer_position,
                "positionAbsolute": answer_position,
                "sourcePosition": "right",
                "targetPosition": "left",
                "selected": False,
            }

            graph["nodes"].extend([llm_node, answer_node])
            graph["edges"] = [
                {
                    "id": f"{start_node_id}-source-{llm_node_id}-target",
                    "type": CUSTOM_NODE_TYPE,
                    "source": start_node_id,
                    "target": llm_node_id,
                    "sourceHandle": "source",
                    "targetHandle": "target",
                    "data": {
                        "isInIteration": False,
                        "isInLoop": False,
                        "sourceType": NodeType.START,
                        "targetType": NodeType.LLM,
                    },
                    "zIndex": 0,
                },
                {
                    "id": f"{llm_node_id}-source-{answer_node_id}-target",
                    "type": CUSTOM_NODE_TYPE,
                    "source": llm_node_id,
                    "target": answer_node_id,
                    "sourceHandle": "source",
                    "targetHandle": "target",
                    "data": {
                        "isInIteration": False,
                        "isInLoop": False,
                        "sourceType": NodeType.LLM,
                        "targetType": NodeType.ANSWER,
                    },
                    "zIndex": 0,
                },
            ]

            # Advanced chat features
            features["opening_statement"] = ""
            features["suggested_questions"] = []
            features["speech_to_text"] = {"enabled": False}
            features["text_to_speech"] = {"enabled": False}
            features["file_upload"] = {
                "enabled": False,
                "allowed_file_types": [],
                "allowed_file_extensions": [],
                "allowed_file_upload_methods": ["local_file"],
                "number_limits": 1,
            }

        # Sync the initial workflow
        url = self._workflow_draft_url_for(target_app_id)
        payload = {
            "graph": graph,
            "features": features,
            "environment_variables": [],
            "conversation_variables": [],
        }

        result = await self._request("POST", url, json_data=payload)

        return {
            "success": True,
            "result": result,
            "graph": graph,
            "features": features,
            "start_node_id": start_node_id,
        }

    async def publish_workflow(self, name: str | None = None, comment: str | None = None) -> dict:
        """Publish the draft workflow.

        Args:
            name: Optional version name (max 20 chars)
            comment: Optional version comment (max 100 chars)

        Returns:
            Response containing result and created_at
        """
        url = f"{self._console_api_base}/apps/{self.app_id}/workflows/publish"
        payload = {}
        if name:
            payload["marked_name"] = name[:20]
        if comment:
            payload["marked_comment"] = comment[:100]

        result = await self._request("POST", url, json_data=payload)
        return result or {}

    async def get_published_workflow(self) -> dict | None:
        """Get the currently published workflow."""
        url = f"{self._console_api_base}/apps/{self.app_id}/workflows/publish"
        try:
            return await self._request("GET", url)
        except PulseClientError as e:
            if e.status_code == 404:
                return None
            raise

    async def list_workflows(self, page: int = 1, limit: int = 10, named_only: bool = False) -> dict:
        """List all published workflows.

        Args:
            page: Page number
            limit: Items per page
            named_only: Only return named versions

        Returns:
            Paginated list of workflows
        """
        url = f"{self._console_api_base}/apps/{self.app_id}/workflows"
        params = {"page": page, "limit": limit, "named_only": named_only}
        result = await self._request("GET", url, params=params)
        return result or {"items": [], "page": page, "limit": limit, "has_more": False}

    # ============================================================
    # Node Operations
    # ============================================================

    async def add_node(
        self,
        node_type: str,
        title: str | None = None,
        config: dict | None = None,
        position: dict | None = None,
        after_node_id: str | None = None,
        source_handle: str = "source",
        target_handle: str = "target",
    ) -> dict:
        """Add a new node to the workflow.

        Args:
            node_type: Type of node (llm, code, http-request, etc.)
            title: Optional node title (defaults to node type)
            config: Optional node-specific configuration
            position: Optional position {x, y}
            after_node_id: Optional node ID to connect from
            source_handle: Handle on source node for edge
            target_handle: Handle on target node for edge

        Returns:
            Result with new node_id
        """
        workflow = await self.get_workflow()
        graph = workflow.get("graph", {"nodes": [], "edges": []})
        features = workflow.get("features")
        current_hash = workflow.get("hash")

        new_node = self.create_node(node_type, title, config, position, graph)
        graph["nodes"].append(new_node)

        if after_node_id:
            source_type = self._get_node_type(graph, after_node_id)
            new_edge = self.create_edge(
                after_node_id,
                new_node["id"],
                source_handle,
                target_handle,
                source_type=source_type,
                target_type=node_type,
            )
            graph["edges"].append(new_edge)

        await self.sync_workflow(graph, features, hash_value=current_hash)

        return {"success": True, "node_id": new_node["id"], "node": new_node}

    async def edit_node(self, node_id: str, updates: dict) -> dict:
        """Edit an existing node.

        Args:
            node_id: ID of the node to edit
            updates: Dictionary of updates to apply

        Returns:
            Result with updated node
        """
        workflow = await self.get_workflow()
        graph = workflow.get("graph", {"nodes": [], "edges": []})
        features = workflow.get("features")
        current_hash = workflow.get("hash")

        node_found = False
        for node in graph["nodes"]:
            if node["id"] == node_id:
                node_found = True
                if "title" in updates:
                    node["data"]["title"] = updates["title"]
                if "config" in updates:
                    node["data"].update(updates["config"])
                if "position" in updates:
                    node["position"] = updates["position"]
                break

        if not node_found:
            raise PulseClientError(f"Node not found: {node_id}")

        await self.sync_workflow(graph, features, hash_value=current_hash)

        updated_node = next(n for n in graph["nodes"] if n["id"] == node_id)
        return {"success": True, "node_id": node_id, "node": updated_node}

    async def delete_node(self, node_id: str) -> dict:
        """Delete a node and its connected edges.

        Args:
            node_id: ID of the node to delete

        Returns:
            Result indicating success
        """
        workflow = await self.get_workflow()
        graph = workflow.get("graph", {"nodes": [], "edges": []})
        features = workflow.get("features")
        current_hash = workflow.get("hash")

        original_count = len(graph["nodes"])
        graph["nodes"] = [n for n in graph["nodes"] if n["id"] != node_id]

        if len(graph["nodes"]) == original_count:
            raise PulseClientError(f"Node not found: {node_id}")

        graph["edges"] = [e for e in graph["edges"] if e["source"] != node_id and e["target"] != node_id]

        await self.sync_workflow(graph, features, hash_value=current_hash)

        return {"success": True, "node_id": node_id}

    async def get_node(self, node_id: str) -> dict | None:
        """Get a specific node by ID.

        Args:
            node_id: ID of the node

        Returns:
            Node object or None if not found
        """
        workflow = await self.get_workflow()
        graph = workflow.get("graph", {"nodes": [], "edges": []})

        for node in graph["nodes"]:
            if node["id"] == node_id:
                return node

        return None

    async def list_nodes(self, filter_type: str | None = None) -> list[dict]:
        """List all nodes in the workflow.

        Args:
            filter_type: Optional node type to filter by

        Returns:
            List of nodes
        """
        workflow = await self.get_workflow()
        graph = workflow.get("graph", {"nodes": [], "edges": []})
        nodes = graph["nodes"]

        if filter_type:
            nodes = [n for n in nodes if n.get("data", {}).get("type") == filter_type]

        return nodes

    # ============================================================
    # StickyNote Operations
    # ============================================================

    def _text_to_lexical(self, text: str) -> str:
        """Convert plain text to Lexical editor JSON format.

        The note editor uses Lexical rich text editor which expects JSON format.
        This converts plain text (with optional newlines) to valid Lexical state.
        """
        if not text:
            # Empty state
            return json.dumps(
                {
                    "root": {
                        "children": [],
                        "direction": None,
                        "format": "",
                        "indent": 0,
                        "type": "root",
                        "version": 1,
                    }
                }
            )

        # Check if already in Lexical format
        if text.strip().startswith("{"):
            try:
                parsed = json.loads(text)
                if "root" in parsed:
                    return text  # Already Lexical format
            except json.JSONDecodeError:
                pass  # Not valid JSON, treat as plain text

        # Convert plain text to Lexical format
        # Split by newlines to create paragraphs
        lines = text.split("\n")
        children = []

        for line in lines:
            if line:
                # Non-empty line becomes a paragraph with text
                children.append(
                    {
                        "children": [
                            {
                                "detail": 0,
                                "format": 0,
                                "mode": "normal",
                                "style": "",
                                "text": line,
                                "type": "text",
                                "version": 1,
                            }
                        ],
                        "direction": "ltr",
                        "format": "",
                        "indent": 0,
                        "type": "paragraph",
                        "version": 1,
                    }
                )
            else:
                # Empty line becomes empty paragraph
                children.append(
                    {
                        "children": [],
                        "direction": None,
                        "format": "",
                        "indent": 0,
                        "type": "paragraph",
                        "version": 1,
                    }
                )

        return json.dumps(
            {
                "root": {
                    "children": children,
                    "direction": "ltr",
                    "format": "",
                    "indent": 0,
                    "type": "root",
                    "version": 1,
                }
            }
        )

    def _is_note_node(self, node: dict) -> bool:
        """Check if a node is a sticky note."""
        return node.get("type") == CUSTOM_NOTE_TYPE

    async def add_note(
        self,
        text: str,
        theme: str = "yellow",
        position: dict | None = None,
        author: str = "",
        show_author: bool = False,
        width: int = 240,
        height: int = 88,
    ) -> dict:
        """Add a sticky note to the workflow canvas.

        Sticky notes are visual-only elements for documentation/annotation.
        They don't participate in workflow execution.

        Args:
            text: Note content (plain text)
            theme: Color theme ('blue', 'cyan', 'green', 'yellow', 'pink', 'violet')
            position: Position {x, y} on canvas
            author: Author name
            show_author: Whether to display author
            width: Note width in pixels
            height: Note height in pixels

        Returns:
            Result with note_id and note data
        """
        workflow = await self.get_workflow()
        graph = workflow.get("graph", {"nodes": [], "edges": []})
        features = workflow.get("features")
        current_hash = workflow.get("hash")

        note_id = uuid.uuid4().hex

        if position is None:
            position = self.calculate_position(graph)

        # Validate theme
        valid_themes = [t.value for t in NoteTheme]
        if theme not in valid_themes:
            theme = NoteTheme.YELLOW

        # Convert plain text to Lexical format for the rich text editor
        lexical_text = self._text_to_lexical(text)

        note_node = {
            "id": note_id,
            "type": CUSTOM_NOTE_TYPE,
            "data": {
                "type": "",
                "title": "",
                "desc": "",
                "text": lexical_text,
                "theme": theme,
                "author": author,
                "showAuthor": show_author,
                "selected": False,
                "width": width,
                "height": height,
            },
            "position": position,
            "positionAbsolute": position,
            "width": width,
            "height": height,
            "sourcePosition": "right",
            "targetPosition": "left",
            "selected": False,
        }

        graph["nodes"].append(note_node)
        await self.sync_workflow(graph, features, hash_value=current_hash)

        return {"success": True, "note_id": note_id, "note": note_node}

    async def edit_note(
        self,
        note_id: str,
        text: str | None = None,
        theme: str | None = None,
        author: str | None = None,
        show_author: bool | None = None,
        position: dict | None = None,
        width: int | None = None,
        height: int | None = None,
    ) -> dict:
        """Edit an existing sticky note.

        Args:
            note_id: ID of the note to edit
            text: New text content
            theme: New color theme
            author: New author name
            show_author: Whether to display author
            position: New position {x, y}
            width: New width
            height: New height

        Returns:
            Result with updated note
        """
        workflow = await self.get_workflow()
        graph = workflow.get("graph", {"nodes": [], "edges": []})
        features = workflow.get("features")
        current_hash = workflow.get("hash")

        note_found = False
        for node in graph["nodes"]:
            if node["id"] == note_id and self._is_note_node(node):
                note_found = True
                if text is not None:
                    # Convert plain text to Lexical format
                    node["data"]["text"] = self._text_to_lexical(text)
                if theme is not None:
                    valid_themes = [t.value for t in NoteTheme]
                    if theme in valid_themes:
                        node["data"]["theme"] = theme
                if author is not None:
                    node["data"]["author"] = author
                if show_author is not None:
                    node["data"]["showAuthor"] = show_author
                if position is not None:
                    node["position"] = position
                if width is not None:
                    node["data"]["width"] = width
                if height is not None:
                    node["data"]["height"] = height
                break

        if not note_found:
            raise PulseClientError(f"Note not found: {note_id}")

        await self.sync_workflow(graph, features, hash_value=current_hash)

        updated_note = next(n for n in graph["nodes"] if n["id"] == note_id)
        return {"success": True, "note_id": note_id, "note": updated_note}

    async def list_notes(self) -> list[dict]:
        """List all sticky notes in the workflow.

        Returns:
            List of sticky note nodes
        """
        workflow = await self.get_workflow()
        graph = workflow.get("graph", {"nodes": [], "edges": []})
        return [n for n in graph["nodes"] if self._is_note_node(n)]

    async def delete_note(self, note_id: str) -> dict:
        """Delete a sticky note from the workflow.

        Args:
            note_id: ID of the note to delete

        Returns:
            Result indicating success
        """
        workflow = await self.get_workflow()
        graph = workflow.get("graph", {"nodes": [], "edges": []})
        features = workflow.get("features")
        current_hash = workflow.get("hash")

        # Find and verify it's a note
        note_exists = any(n["id"] == note_id and self._is_note_node(n) for n in graph["nodes"])
        if not note_exists:
            raise PulseClientError(f"Note not found: {note_id}")

        graph["nodes"] = [n for n in graph["nodes"] if n["id"] != note_id]

        await self.sync_workflow(graph, features, hash_value=current_hash)

        return {"success": True, "note_id": note_id}

    # ============================================================
    # Edge Operations
    # ============================================================

    async def connect_nodes(
        self,
        source_id: str,
        target_id: str,
        source_handle: str = "source",
        target_handle: str = "target",
    ) -> dict:
        """Create an edge between two nodes.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            source_handle: Handle on source node
            target_handle: Handle on target node

        Returns:
            Result with edge_id
        """
        workflow = await self.get_workflow()
        graph = workflow.get("graph", {"nodes": [], "edges": []})
        features = workflow.get("features")
        current_hash = workflow.get("hash")

        node_ids = {n["id"] for n in graph["nodes"]}
        if source_id not in node_ids:
            raise PulseClientError(f"Source node not found: {source_id}")
        if target_id not in node_ids:
            raise PulseClientError(f"Target node not found: {target_id}")

        for edge in graph["edges"]:
            if (
                edge["source"] == source_id
                and edge["target"] == target_id
                and edge.get("sourceHandle") == source_handle
                and edge.get("targetHandle") == target_handle
            ):
                return {"success": True, "edge_id": edge["id"], "edge": edge, "existed": True}

        source_type = self._get_node_type(graph, source_id)
        target_type = self._get_node_type(graph, target_id)
        new_edge = self.create_edge(
            source_id,
            target_id,
            source_handle,
            target_handle,
            source_type=source_type,
            target_type=target_type,
        )
        graph["edges"].append(new_edge)

        await self.sync_workflow(graph, features, hash_value=current_hash)

        return {"success": True, "edge_id": new_edge["id"], "edge": new_edge}

    async def disconnect_nodes(
        self,
        source_id: str,
        target_id: str,
        source_handle: str | None = None,
        target_handle: str | None = None,
    ) -> dict:
        """Remove edges between two nodes.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            source_handle: Optional - only remove edge with this source handle
            target_handle: Optional - only remove edge with this target handle

        Returns:
            Result with number of edges removed
        """
        workflow = await self.get_workflow()
        graph = workflow.get("graph", {"nodes": [], "edges": []})
        features = workflow.get("features")
        current_hash = workflow.get("hash")

        original_count = len(graph["edges"])

        def should_remove(edge: dict) -> bool:
            if edge["source"] != source_id or edge["target"] != target_id:
                return False
            if source_handle and edge.get("sourceHandle") != source_handle:
                return False
            return not (target_handle and edge.get("targetHandle") != target_handle)

        graph["edges"] = [e for e in graph["edges"] if not should_remove(e)]
        removed_count = original_count - len(graph["edges"])

        if removed_count > 0:
            await self.sync_workflow(graph, features, hash_value=current_hash)

        return {"success": True, "removed_count": removed_count}

    async def list_edges(self) -> list[dict]:
        """List all edges in the workflow.

        Returns:
            List of edges
        """
        workflow = await self.get_workflow()
        graph = workflow.get("graph", {"nodes": [], "edges": []})
        return graph["edges"]

    # ============================================================
    # Node Execution
    # ============================================================

    async def run_node(self, node_id: str, inputs: dict | None = None, query: str | None = None) -> dict:
        """Execute a single node in the draft workflow.

        Args:
            node_id: ID of the node to run
            inputs: Input values for the node
            query: Optional query string

        Returns:
            Node execution result
        """
        url = f"{self._workflow_draft_url}/nodes/{node_id}/run"
        payload: dict[str, Any] = {"inputs": inputs or {}}
        if query:
            payload["query"] = query

        result = await self._request("POST", url, json_data=payload)
        return result or {}

    async def get_node_last_run(self, node_id: str) -> dict | None:
        """Get the last execution result for a node.

        Args:
            node_id: ID of the node

        Returns:
            Last execution result or None
        """
        url = f"{self._workflow_draft_url}/nodes/{node_id}/last-run"
        try:
            return await self._request("GET", url)
        except PulseClientError as e:
            if e.status_code == 404:
                return None
            raise

    # ============================================================
    # Features & Variables
    # ============================================================

    async def get_features(self) -> dict:
        """Get workflow features configuration.

        Returns:
            Features configuration
        """
        workflow = await self.get_workflow()
        return workflow.get("features", {})

    async def update_features(self, features: dict) -> dict:
        """Update workflow features.

        Args:
            features: Features to update (partial update)

        Returns:
            Result with updated features
        """
        workflow = await self.get_workflow()
        graph = workflow.get("graph", {"nodes": [], "edges": []})
        current_features = workflow.get("features", {})
        current_hash = workflow.get("hash")

        merged_features = {**current_features, **features}

        await self.sync_workflow(graph, merged_features, hash_value=current_hash)

        return {"success": True, "features": merged_features}

    async def get_variables(self) -> dict:
        """Get all workflow variables.

        Returns:
            Dictionary with environment_variables and conversation_variables
        """
        workflow = await self.get_workflow()
        return {
            "environment_variables": workflow.get("environment_variables", []),
            "conversation_variables": workflow.get("conversation_variables", []),
        }

    # ============================================================
    # Validation
    # ============================================================

    async def validate_workflow(self) -> dict:
        """Validate the current workflow.

        Returns:
            Validation result with any errors found
        """
        workflow = await self.get_workflow()
        graph = workflow.get("graph", {"nodes": [], "edges": []})

        errors: list[dict[str, str]] = []
        warnings: list[dict[str, str]] = []

        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        node_ids = {n["id"] for n in nodes}

        start_nodes = [n for n in nodes if n.get("data", {}).get("type") == NodeType.START]
        if not start_nodes:
            errors.append({"type": "missing_start", "message": "Workflow must have a start node"})
        elif len(start_nodes) > 1:
            errors.append({"type": "multiple_starts", "message": "Workflow can only have one start node"})

        end_nodes = [n for n in nodes if n.get("data", {}).get("type") in (NodeType.END, NodeType.ANSWER)]
        if not end_nodes:
            warnings.append({"type": "missing_end", "message": "Workflow has no end/answer node"})

        for edge in edges:
            if edge["source"] not in node_ids:
                errors.append(
                    {
                        "type": "invalid_edge",
                        "message": f"Edge references non-existent source node: {edge['source']}",
                    }
                )
            if edge["target"] not in node_ids:
                errors.append(
                    {
                        "type": "invalid_edge",
                        "message": f"Edge references non-existent target node: {edge['target']}",
                    }
                )

        connected_nodes = set()
        for edge in edges:
            connected_nodes.add(edge["source"])
            connected_nodes.add(edge["target"])

        for node in nodes:
            node_type = node.get("data", {}).get("type")
            # Skip start/end/answer nodes and sticky notes from disconnected check
            if (
                node_type not in (NodeType.START, NodeType.END, NodeType.ANSWER)
                and not self._is_note_node(node)
                and node["id"] not in connected_nodes
            ):
                warnings.append(
                    {
                        "type": "disconnected_node",
                        "message": f"Node '{node.get('data', {}).get('title', node['id'])}' is not connected",
                    }
                )

        # Count only workflow nodes (exclude sticky notes)
        workflow_nodes = [n for n in nodes if not self._is_note_node(n)]
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "node_count": len(workflow_nodes),
            "edge_count": len(edges),
        }

    # ============================================================
    # Discovery Operations
    # ============================================================

    async def list_node_types(self, app_id: str | None = None) -> dict | list:
        """List all available node types and their default configurations.

        Args:
            app_id: Optional app ID (uses default if not provided)

        Returns:
            Node types - either a dict mapping names to configs, or a list of type objects
        """
        target_app_id = self._get_app_id(app_id)
        url = f"{self._console_api_base}/apps/{target_app_id}/workflows/default-workflow-block-configs"
        result = await self._request("GET", url)
        return result or {}

    async def get_node_schema(self, block_type: str, app_id: str | None = None) -> dict:
        """Get the schema and default configuration for a specific node type.

        Args:
            block_type: The node type (e.g., 'llm', 'code', 'http-request')
            app_id: Optional app ID (uses default if not provided)

        Returns:
            Node type schema with default configuration, inputs, and outputs
        """
        target_app_id = self._get_app_id(app_id)
        url = f"{self._console_api_base}/apps/{target_app_id}/workflows/default-workflow-block-configs/{block_type}"
        result = await self._request("GET", url)
        return result or {}

    async def list_tool_providers(self) -> list[dict]:
        """List all available tool/plugin providers.

        Returns:
            List of tool providers with their metadata
        """
        url = f"{self._console_api_base}/workspaces/current/tool-providers"
        result = await self._request("GET", url)
        return result if isinstance(result, list) else []

    async def list_agent_strategies(self) -> list[dict]:
        """List all available agent strategy providers.

        Returns:
            List of agent strategy providers with their strategies
        """
        url = f"{self._console_api_base}/workspaces/current/agent-providers"
        result = await self._request("GET", url)
        return result if isinstance(result, list) else []

    async def get_agent_strategy(self, provider_name: str) -> dict:
        """Get details of an agent strategy provider including parameters.

        Args:
            provider_name: The agent provider name (e.g., 'langgenius/agent/cot_agent_with_memory')

        Returns:
            Strategy provider details with declaration containing strategies and their parameters
        """
        url = f"{self._console_api_base}/workspaces/current/agent-provider/{provider_name}"
        result = await self._request("GET", url)
        return result or {}

    async def list_tools(
        self,
        provider_id: str | None = None,
        tool_type: str = "builtin",
    ) -> list[dict]:
        """List available tools, optionally filtered by provider.

        Args:
            provider_id: Optional provider ID to filter by
            tool_type: Type of tools to list ('builtin', 'workflow', 'api', 'mcp')

        Returns:
            List of tools with their input/output schemas
        """
        if provider_id:
            # Different endpoints for different tool types
            if tool_type == "api":
                # API tools use query parameter
                url = f"{self._console_api_base}/workspaces/current/tool-provider/api/tools"
                result = await self._request("GET", url, params={"provider": provider_id})
            elif tool_type == "workflow":
                # Workflow tools use query parameter
                url = f"{self._console_api_base}/workspaces/current/tool-provider/workflow/tools"
                result = await self._request("GET", url, params={"workflow_tool_id": provider_id})
            elif tool_type == "mcp":
                # MCP tools use path parameter
                url = f"{self._console_api_base}/workspaces/current/tool-provider/mcp/tools/{provider_id}"
                result = await self._request("GET", url)
            else:
                # Builtin tools (including plugins) use path parameter
                url = f"{self._console_api_base}/workspaces/current/tool-provider/builtin/{provider_id}/tools"
                result = await self._request("GET", url)
        else:
            url = f"{self._console_api_base}/workspaces/current/tools/{tool_type}"
            result = await self._request("GET", url)
        return result if isinstance(result, list) else []

    async def list_models(self, model_type: str = "llm") -> list[dict]:
        """List available models by type.

        Args:
            model_type: Type of models to list ('llm', 'text-embedding', 'rerank', 'speech2text', 'tts')

        Returns:
            List of available models with provider info
        """
        url = f"{self._console_api_base}/workspaces/current/models/model-types/{model_type}"
        result = await self._request("GET", url)
        # The API returns a dict with 'data' key containing the models list
        if isinstance(result, dict):
            return result.get("data", [])
        return result if isinstance(result, list) else []

    async def list_datasets(
        self,
        page: int = 1,
        limit: int = 100,
    ) -> dict:
        """List available datasets (knowledge bases).

        Args:
            page: Page number
            limit: Items per page

        Returns:
            Paginated list of datasets
        """
        url = f"{self._console_api_base}/datasets"
        params = {"page": page, "limit": limit}
        result = await self._request("GET", url, params=params)
        return result or {"data": [], "page": page, "limit": limit, "has_more": False, "total": 0}

    async def get_dataset(self, dataset_id: str) -> dict:
        """Get details of a specific dataset.

        Args:
            dataset_id: ID of the dataset

        Returns:
            Dataset details including name, description, document count, etc.
        """
        url = f"{self._console_api_base}/datasets/{dataset_id}"
        result = await self._request("GET", url)
        return result or {}

    async def list_documents(
        self,
        dataset_id: str,
        page: int = 1,
        limit: int = 20,
        keyword: str | None = None,
    ) -> dict:
        """List documents in a dataset.

        Args:
            dataset_id: ID of the dataset
            page: Page number
            limit: Items per page
            keyword: Optional search keyword

        Returns:
            Paginated list of documents
        """
        url = f"{self._console_api_base}/datasets/{dataset_id}/documents"
        params: dict[str, Any] = {"page": page, "limit": limit}
        if keyword:
            params["keyword"] = keyword
        result = await self._request("GET", url, params=params)
        return result or {"data": [], "page": page, "limit": limit, "has_more": False, "total": 0}

    async def get_document(self, dataset_id: str, document_id: str) -> dict:
        """Get details of a specific document.

        Args:
            dataset_id: ID of the dataset
            document_id: ID of the document

        Returns:
            Document details including name, word count, segments, etc.
        """
        url = f"{self._console_api_base}/datasets/{dataset_id}/documents/{document_id}"
        result = await self._request("GET", url)
        return result or {}

    async def search_dataset(
        self,
        dataset_id: str,
        query: str,
        retrieval_model: dict | None = None,
        top_k: int = 5,
    ) -> dict:
        """Search/query a dataset using hit testing (retrieval).

        Args:
            dataset_id: ID of the dataset to search
            query: The search query
            retrieval_model: Optional retrieval configuration
            top_k: Number of results to return (default: 5)

        Returns:
            Search results with matched segments and scores
        """
        url = f"{self._console_api_base}/datasets/{dataset_id}/hit-testing"
        payload: dict[str, Any] = {
            "query": query,
        }
        if retrieval_model:
            payload["retrieval_model"] = retrieval_model
        else:
            # Default retrieval model
            payload["retrieval_model"] = {
                "search_method": "semantic_search",
                "reranking_enable": False,
                "top_k": top_k,
                "score_threshold_enabled": False,
            }

        result = await self._request("POST", url, json_data=payload)
        return result or {"records": []}

    async def create_app(
        self,
        name: str,
        mode: str = "workflow",
        icon_type: str = "emoji",
        icon: str = "\U0001f916",
        icon_background: str = "#FFEAD5",
        description: str = "",
    ) -> dict:
        """Create a new app.

        Args:
            name: App name
            mode: App mode ('workflow', 'advanced-chat', 'chat', 'completion', 'agent-chat')
            icon_type: Icon type ('emoji' or 'image')
            icon: Icon emoji or image URL
            icon_background: Background color for icon
            description: App description

        Returns:
            Created app details including ID
        """
        url = f"{self._console_api_base}/apps"
        payload = {
            "name": name,
            "mode": mode,
            "icon_type": icon_type,
            "icon": icon,
            "icon_background": icon_background,
            "description": description,
        }
        result = await self._request("POST", url, json_data=payload)
        return result or {}

    # ============================================================
    # Public Helpers (for batch operations in server.py)
    # ============================================================

    def create_node(
        self,
        node_type: str,
        title: str | None,
        config: dict | None,
        position: dict | None,
        graph: dict,
    ) -> dict:
        """Create a new node object.

        Args:
            node_type: Type of the node (e.g., 'llm', 'code')
            title: Node title (defaults to formatted node_type)
            config: Node-specific configuration
            position: Position {x, y} on canvas
            graph: Current workflow graph (used for position calculation)

        Returns:
            New node object ready to be added to graph
        """
        node_id = uuid.uuid4().hex

        if position is None:
            position = self.calculate_position(graph)

        node_data = {
            "type": node_type,
            "title": title or node_type.replace("-", " ").replace("_", " ").title(),
            "desc": "",
            "selected": False,
        }

        # Apply default config for node types with required fields
        if node_type in NODE_DEFAULT_CONFIGS:
            node_data.update(NODE_DEFAULT_CONFIGS[node_type])

        # User config overrides defaults
        if config:
            node_data.update(config)

        # ReactFlow uses "custom" as outer type for all workflow nodes
        # The actual node type is in data.type
        return {
            "id": node_id,
            "type": CUSTOM_NODE_TYPE,
            "data": node_data,
            "position": position,
            "positionAbsolute": position,
            "sourcePosition": "right",
            "targetPosition": "left",
            "selected": False,
        }

    def create_edge(
        self,
        source_id: str,
        target_id: str,
        source_handle: str,
        target_handle: str,
        source_type: str = "",
        target_type: str = "",
    ) -> dict:
        """Create a new edge object.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            source_handle: Handle on source node
            target_handle: Handle on target node
            source_type: Type of source node (for edge metadata)
            target_type: Type of target node (for edge metadata)

        Returns:
            New edge object ready to be added to graph
        """
        return {
            "id": f"{source_id}-{source_handle}-{target_id}-{target_handle}",
            "type": CUSTOM_NODE_TYPE,
            "source": source_id,
            "target": target_id,
            "sourceHandle": source_handle,
            "targetHandle": target_handle,
            "data": {
                "isInIteration": False,
                "isInLoop": False,
                "sourceType": source_type,
                "targetType": target_type,
            },
            "zIndex": 0,
        }

    def calculate_position(self, graph: dict) -> dict:
        """Calculate a reasonable position for a new node.

        Args:
            graph: Current workflow graph

        Returns:
            Position dict with x and y coordinates
        """
        nodes = graph.get("nodes", [])

        if not nodes:
            return {"x": 100, "y": 100}

        max_x = max(n.get("position", {}).get("x", 0) for n in nodes)
        avg_y = sum(n.get("position", {}).get("y", 100) for n in nodes) / len(nodes)

        return {"x": max_x + 250, "y": avg_y}

    def _get_node_type(self, graph: dict, node_id: str) -> str:
        """Get the type of a node from the graph."""
        for node in graph.get("nodes", []):
            if node.get("id") == node_id:
                return node.get("data", {}).get("type", "")
        return ""


# Module-level client management
_client: PulseClient | None = None


def get_client() -> PulseClient:
    """Get the global Pulse client instance."""
    global _client
    if _client is None:
        _client = PulseClient()
    return _client


def init_client() -> PulseClient:
    """Initialize the global Pulse client."""
    global _client
    _client = PulseClient()
    return _client


async def cleanup_client() -> None:
    """Clean up the global client resources."""
    global _client
    if _client is not None:
        await _client.close()
        _client = None
