"""Synchronous wrapper for MemoryLayer SDK.

This module provides a synchronous interface to the async MemoryLayer client,
enabling use of the SDK in synchronous contexts like LangChain's BaseMemory.
"""

import logging
from contextlib import contextmanager
from typing import Any, Generator, Optional

import httpx

logger = logging.getLogger(__name__)


class SyncMemoryLayerClient:
    """
    Synchronous client for MemoryLayer.ai API.

    This is a synchronous wrapper around the MemoryLayer SDK, providing
    the same functionality in a blocking manner. It is designed for use
    in synchronous contexts like LangChain's legacy BaseMemory classes.

    For async contexts, use the async MemoryLayerClient from the memorylayer SDK instead.

    Usage:
        from memorylayer_langchain.sync_client import SyncMemoryLayerClient

        # As a context manager (recommended)
        with SyncMemoryLayerClient(
            base_url="http://localhost:8080",
            api_key="your-api-key",
            workspace_id="ws_123"
        ) as client:
            # Store a memory
            memory = client.remember(
                content="User prefers Python",
                type="semantic",
                importance=0.8
            )

            # Search memories
            results = client.recall("coding preferences")

            # Reflect on memories
            reflection = client.reflect("summarize user preferences")

        # Or create and manage lifecycle manually
        client = SyncMemoryLayerClient(
            base_url="http://localhost:8080",
            api_key="your-api-key",
            workspace_id="ws_123"
        )
        client.connect()
        try:
            memory = client.remember(content="Test")
        finally:
            client.close()
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        api_key: Optional[str] = None,
        workspace_id: Optional[str] = None,
        timeout: float = 30.0,
    ) -> None:
        """
        Initialize synchronous MemoryLayer client.

        Args:
            base_url: API base URL (default: http://localhost:8080)
            api_key: API key for authentication
            workspace_id: Default workspace ID for operations
            timeout: Request timeout in seconds (default: 30.0)
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.workspace_id = workspace_id
        self.timeout = timeout
        self._client: Optional[httpx.Client] = None

    def __enter__(self) -> "SyncMemoryLayerClient":
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()

    def connect(self) -> None:
        """Initialize the HTTP client."""
        if self._client is not None:
            return

        headers: dict[str, str] = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if self.workspace_id:
            headers["X-Workspace-ID"] = self.workspace_id

        self._client = httpx.Client(
            base_url=f"{self.base_url}/v1",
            headers=headers,
            timeout=self.timeout,
        )

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def _ensure_client(self) -> httpx.Client:
        """Ensure the client is initialized."""
        if self._client is None:
            raise RuntimeError(
                "Client not initialized. Use 'with' context manager or call connect() first."
            )
        return self._client

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Make HTTP request to MemoryLayer API.

        Args:
            method: HTTP method
            path: API path
            json: JSON body
            params: Query parameters

        Returns:
            Response JSON

        Raises:
            httpx.HTTPStatusError: For HTTP errors
        """
        client = self._ensure_client()

        response = client.request(method, path, json=json, params=params)
        response.raise_for_status()

        if response.status_code == 204:
            return {}

        return response.json()

    # Core memory operations

    def remember(
        self,
        content: str,
        type: Optional[str] = None,
        subtype: Optional[str] = None,
        importance: float = 0.5,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        space_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Store a new memory.

        Args:
            content: Memory content to store
            type: Cognitive memory type (episodic, semantic, procedural, working)
            subtype: Domain subtype (Solution, Problem, etc.)
            importance: Importance score 0.0-1.0 (default: 0.5)
            tags: Tags for categorization
            metadata: Additional metadata
            space_id: Optional memory space ID

        Returns:
            Created memory as dict

        Example:
            memory = client.remember(
                content="User prefers concise code comments",
                type="semantic",
                importance=0.8,
                tags=["preferences", "coding-style"]
            )
        """
        payload: dict[str, Any] = {
            "content": content,
            "importance": importance,
        }
        if type:
            payload["type"] = type
        if subtype:
            payload["subtype"] = subtype
        if tags:
            payload["tags"] = tags
        if metadata:
            payload["metadata"] = metadata
        if space_id:
            payload["space_id"] = space_id

        return self._request("POST", "/memories", json=payload)

    def recall(
        self,
        query: str,
        types: Optional[list[str]] = None,
        subtypes: Optional[list[str]] = None,
        tags: Optional[list[str]] = None,
        mode: str = "rag",
        limit: int = 10,
        min_relevance: float = 0.5,
        tolerance: str = "moderate",
        include_associations: bool = False,
    ) -> dict[str, Any]:
        """
        Search memories by semantic query.

        Args:
            query: Natural language search query
            types: Filter by cognitive memory types
            subtypes: Filter by domain subtypes
            tags: Filter by tags
            mode: Retrieval mode (rag, llm, hybrid)
            limit: Maximum memories to return (default: 10)
            min_relevance: Minimum relevance score 0.0-1.0 (default: 0.5)
            tolerance: Search tolerance (loose, moderate, strict)
            include_associations: Include linked memories (default: False)

        Returns:
            Recall results with memories

        Example:
            results = client.recall(
                query="what are the user's coding preferences?",
                types=["semantic", "procedural"],
                limit=5,
                min_relevance=0.7
            )
        """
        payload: dict[str, Any] = {
            "query": query,
            "mode": mode,
            "limit": limit,
            "min_relevance": min_relevance,
            "tolerance": tolerance,
            "include_associations": include_associations,
        }
        if types:
            payload["types"] = types
        if subtypes:
            payload["subtypes"] = subtypes
        if tags:
            payload["tags"] = tags

        return self._request("POST", "/memories/recall", json=payload)

    def reflect(
        self,
        query: str,
        max_tokens: int = 500,
        include_sources: bool = True,
    ) -> dict[str, Any]:
        """
        Synthesize and summarize memories.

        Args:
            query: What to reflect on
            max_tokens: Maximum tokens in reflection (default: 500)
            include_sources: Include source memory IDs (default: True)

        Returns:
            Reflection result with synthesis

        Example:
            reflection = client.reflect(
                query="summarize everything about user's development workflow",
                max_tokens=300
            )
        """
        payload = {
            "query": query,
            "max_tokens": max_tokens,
            "include_sources": include_sources,
        }

        return self._request("POST", "/memories/reflect", json=payload)

    def forget(
        self,
        memory_id: str,
        hard: bool = False,
    ) -> bool:
        """
        Delete or soft-delete a memory.

        Args:
            memory_id: ID of memory to forget
            hard: Permanently delete (default: False for soft delete)

        Returns:
            True if successful

        Example:
            client.forget("mem_123", hard=False)
        """
        params = {"hard": "true" if hard else "false"}
        self._request("DELETE", f"/memories/{memory_id}", params=params)
        return True

    def get_memory(self, memory_id: str) -> dict[str, Any]:
        """
        Get a specific memory by ID.

        Args:
            memory_id: Memory ID

        Returns:
            Memory object

        Example:
            memory = client.get_memory("mem_123")
        """
        return self._request("GET", f"/memories/{memory_id}")

    def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        importance: Optional[float] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Update an existing memory.

        Args:
            memory_id: Memory ID
            content: New content (optional)
            importance: New importance score (optional)
            tags: New tags (optional)
            metadata: New metadata (optional)

        Returns:
            Updated memory

        Example:
            memory = client.update_memory(
                "mem_123",
                importance=0.9,
                tags=["preferences", "high-priority"]
            )
        """
        payload: dict[str, Any] = {}
        if content is not None:
            payload["content"] = content
        if importance is not None:
            payload["importance"] = importance
        if tags is not None:
            payload["tags"] = tags
        if metadata is not None:
            payload["metadata"] = metadata

        return self._request("PATCH", f"/memories/{memory_id}", json=payload)

    # Association methods

    def associate(
        self,
        source_id: str,
        target_id: str,
        relationship: str,
        strength: float = 0.5,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Link two memories with a relationship.

        Args:
            source_id: Source memory ID
            target_id: Target memory ID
            relationship: Relationship type
            strength: Relationship strength 0.0-1.0 (default: 0.5)
            metadata: Additional metadata

        Returns:
            Created association

        Example:
            assoc = client.associate(
                source_id="mem_123",
                target_id="mem_456",
                relationship="solves",
                strength=0.9
            )
        """
        payload: dict[str, Any] = {
            "target_id": target_id,
            "relationship": relationship,
            "strength": strength,
        }
        if metadata:
            payload["metadata"] = metadata

        return self._request("POST", f"/memories/{source_id}/associate", json=payload)

    def get_associations(
        self,
        memory_id: str,
        direction: str = "both",
    ) -> dict[str, Any]:
        """
        Get associations for a memory.

        Args:
            memory_id: Memory ID
            direction: "outgoing", "incoming", or "both" (default: "both")

        Returns:
            Dictionary containing list of associations

        Example:
            associations = client.get_associations("mem_123")
        """
        params = {"direction": direction}
        return self._request("GET", f"/memories/{memory_id}/associations", params=params)

    # Session methods

    def create_session(self, ttl_seconds: int = 3600) -> dict[str, Any]:
        """
        Create a new working memory session.

        Args:
            ttl_seconds: Time to live in seconds (default: 3600 = 1 hour)

        Returns:
            Created session

        Example:
            session = client.create_session(ttl_seconds=7200)
        """
        payload = {"ttl_seconds": ttl_seconds}
        return self._request("POST", "/sessions", json=payload)

    def get_session(self, session_id: str) -> dict[str, Any]:
        """
        Get a session by ID.

        Args:
            session_id: Session ID

        Returns:
            Session object
        """
        return self._request("GET", f"/sessions/{session_id}")

    def set_context(
        self,
        session_id: str,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """
        Set a context value in a session.

        Args:
            session_id: Session ID
            key: Context key
            value: Context value (any JSON-serializable object)
            ttl_seconds: Optional TTL for this key

        Example:
            client.set_context(
                "sess_123",
                "current_file",
                {"path": "auth.py", "line": 42}
            )
        """
        payload: dict[str, Any] = {
            "key": key,
            "value": value,
        }
        if ttl_seconds is not None:
            payload["ttl_seconds"] = ttl_seconds

        self._request("POST", f"/sessions/{session_id}/context", json=payload)

    def get_context(
        self,
        session_id: str,
        keys: list[str],
    ) -> dict[str, Any]:
        """
        Get context values from a session.

        Args:
            session_id: Session ID
            keys: List of keys to retrieve

        Returns:
            Dictionary of key-value pairs

        Example:
            context = client.get_context(
                "sess_123",
                ["current_file", "user_intent"]
            )
        """
        params = {"keys": ",".join(keys)}
        data = self._request("GET", f"/sessions/{session_id}/context", params=params)
        return data.get("context", {})

    def get_briefing(self, lookback_hours: int = 24) -> dict[str, Any]:
        """
        Get a session briefing with recent activity and context.

        Args:
            lookback_hours: How far back to look for activity (default: 24)

        Returns:
            Session briefing

        Example:
            briefing = client.get_briefing(lookback_hours=48)
        """
        params = {"lookback_hours": lookback_hours}
        return self._request("GET", "/sessions/briefing", params=params)

    # Workspace methods

    def create_workspace(self, name: str) -> dict[str, Any]:
        """
        Create a new workspace.

        Args:
            name: Workspace name

        Returns:
            Created workspace

        Example:
            workspace = client.create_workspace("my-project")
        """
        payload = {"name": name}
        return self._request("POST", "/workspaces", json=payload)

    def get_workspace(self, workspace_id: Optional[str] = None) -> dict[str, Any]:
        """
        Get workspace details.

        Args:
            workspace_id: Workspace ID (uses default if not provided)

        Returns:
            Workspace object

        Example:
            workspace = client.get_workspace()
        """
        ws_id = workspace_id or self.workspace_id
        if not ws_id:
            raise ValueError("workspace_id must be provided or set on client")

        return self._request("GET", f"/workspaces/{ws_id}")


@contextmanager
def sync_client(
    base_url: str = "http://localhost:8080",
    api_key: Optional[str] = None,
    workspace_id: Optional[str] = None,
    timeout: float = 30.0,
) -> Generator[SyncMemoryLayerClient, None, None]:
    """
    Context manager for creating a SyncMemoryLayerClient.

    This is a convenience function that creates a client, connects it,
    and ensures proper cleanup.

    Args:
        base_url: API base URL (default: http://localhost:8080)
        api_key: API key for authentication
        workspace_id: Default workspace ID for operations
        timeout: Request timeout in seconds (default: 30.0)

    Yields:
        Connected SyncMemoryLayerClient instance

    Example:
        from memorylayer_langchain.sync_client import sync_client

        with sync_client(api_key="your-key") as client:
            client.remember(content="Hello world")
    """
    with SyncMemoryLayerClient(
        base_url=base_url,
        api_key=api_key,
        workspace_id=workspace_id,
        timeout=timeout,
    ) as client:
        yield client
