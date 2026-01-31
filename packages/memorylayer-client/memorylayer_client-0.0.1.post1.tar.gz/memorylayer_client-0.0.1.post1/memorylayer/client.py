"""Main client for MemoryLayer.ai SDK."""

import logging
from typing import Any, Optional

import httpx
from pydantic import TypeAdapter

from .exceptions import (
    AuthenticationError,
    MemoryLayerError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from .models import (
    Association,
    Memory,
    RecallResult,
    ReflectResult,
    Session,
    SessionBriefing,
    Workspace,
)
from .types import (
    MemorySubtype,
    MemoryType,
    RecallMode,
    RelationshipType,
    SearchTolerance,
)

logger = logging.getLogger(__name__)


class MemoryLayerClient:
    """
    Python client for MemoryLayer.ai API.

    Usage:
        async with MemoryLayerClient(
            base_url="https://api.memorylayer.ai",
            api_key="your-api-key",
            workspace_id="ws_123"
        ) as client:
            # Store a memory
            memory = await client.remember(
                content="User prefers Python",
                type=MemoryType.SEMANTIC,
                importance=0.8
            )

            # Search memories
            results = await client.recall("coding preferences")

            # Reflect on memories
            reflection = await client.reflect("summarize user preferences")
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        api_key: Optional[str] = None,
        workspace_id: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """
        Initialize MemoryLayer client.

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
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "MemoryLayerClient":
        """Async context manager entry."""
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if self.workspace_id:
            headers["X-Workspace-ID"] = self.workspace_id

        self._client = httpx.AsyncClient(
            base_url=f"{self.base_url}/v1",
            headers=headers,
            timeout=self.timeout,
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure client is initialized."""
        if self._client is None:
            raise RuntimeError("Client not initialized. Use async with context manager.")
        return self._client

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Make HTTP request with error handling.

        Args:
            method: HTTP method
            path: API path
            json: JSON body
            params: Query parameters

        Returns:
            Response JSON

        Raises:
            AuthenticationError: Authentication failed (401)
            NotFoundError: Resource not found (404)
            ValidationError: Validation failed (422)
            RateLimitError: Rate limit exceeded (429)
            ServerError: Server error (5xx)
            MemoryLayerError: Other errors
        """
        client = self._ensure_client()

        try:
            response = await client.request(method, path, json=json, params=params)

            # Handle errors
            if response.status_code == 401:
                raise AuthenticationError(response.json().get("detail", "Authentication failed"))
            elif response.status_code == 404:
                raise NotFoundError(response.json().get("detail", "Resource not found"))
            elif response.status_code == 422:
                raise ValidationError(response.json().get("detail", "Validation error"))
            elif response.status_code == 429:
                raise RateLimitError(response.json().get("detail", "Rate limit exceeded"))
            elif response.status_code >= 500:
                raise ServerError(
                    response.json().get("detail", "Server error"),
                    status_code=response.status_code,
                )
            elif response.status_code >= 400:
                raise MemoryLayerError(
                    response.json().get("detail", "Request failed"),
                    status_code=response.status_code,
                )

            response.raise_for_status()

            # Handle No Content responses
            if response.status_code == 204:
                return {}

            return response.json()

        except httpx.TimeoutException as e:
            raise MemoryLayerError(f"Request timeout: {e}") from e
        except httpx.HTTPError as e:
            raise MemoryLayerError(f"HTTP error: {e}") from e

    # Core memory operations

    async def remember(
        self,
        content: str,
        type: Optional[MemoryType] = None,
        subtype: Optional[MemorySubtype] = None,
        importance: float = 0.5,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        space_id: Optional[str] = None,
    ) -> Memory:
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
            Created memory

        Example:
            memory = await client.remember(
                content="User prefers concise code comments",
                type=MemoryType.SEMANTIC,
                subtype=MemorySubtype.PREFERENCE,
                importance=0.8,
                tags=["preferences", "coding-style"]
            )
        """
        payload = {
            "content": content,
            "importance": importance,
        }
        if type:
            payload["type"] = type.value
        if subtype:
            payload["subtype"] = subtype.value
        if tags:
            payload["tags"] = tags
        if metadata:
            payload["metadata"] = metadata
        if space_id:
            payload["space_id"] = space_id

        data = await self._request("POST", "/memories", json=payload)
        return Memory(**data)

    async def recall(
        self,
        query: str,
        types: Optional[list[MemoryType]] = None,
        subtypes: Optional[list[MemorySubtype]] = None,
        tags: Optional[list[str]] = None,
        mode: RecallMode = RecallMode.RAG,
        limit: int = 10,
        min_relevance: float = 0.5,
        tolerance: SearchTolerance = SearchTolerance.MODERATE,
        include_associations: bool = False,
    ) -> RecallResult:
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
            results = await client.recall(
                query="what are the user's coding preferences?",
                types=[MemoryType.SEMANTIC, MemoryType.PROCEDURAL],
                limit=5,
                min_relevance=0.7
            )
        """
        payload = {
            "query": query,
            "mode": mode.value,
            "limit": limit,
            "min_relevance": min_relevance,
            "tolerance": tolerance.value,
            "include_associations": include_associations,
        }
        if types:
            payload["types"] = [t.value for t in types]
        if subtypes:
            payload["subtypes"] = [s.value for s in subtypes]
        if tags:
            payload["tags"] = tags

        data = await self._request("POST", "/memories/recall", json=payload)

        # Parse memories
        memories_adapter = TypeAdapter(list[Memory])
        memories = memories_adapter.validate_python(data.get("memories", []))

        return RecallResult(
            memories=memories,
            total_count=data.get("total_count", len(memories)),
            query_tokens=data.get("query_tokens"),
            search_latency_ms=data.get("search_latency_ms"),
        )

    async def reflect(
        self,
        query: str,
        max_tokens: int = 500,
        include_sources: bool = True,
    ) -> ReflectResult:
        """
        Synthesize and summarize memories.

        Args:
            query: What to reflect on
            max_tokens: Maximum tokens in reflection (default: 500)
            include_sources: Include source memory IDs (default: True)

        Returns:
            Reflection result with synthesis

        Example:
            reflection = await client.reflect(
                query="summarize everything about user's development workflow",
                max_tokens=300
            )
        """
        payload = {
            "query": query,
            "max_tokens": max_tokens,
            "include_sources": include_sources,
        }

        data = await self._request("POST", "/memories/reflect", json=payload)
        return ReflectResult(**data)

    async def forget(
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
            await client.forget("mem_123", hard=False)
        """
        params = {"hard": "true" if hard else "false"}
        await self._request("DELETE", f"/memories/{memory_id}", params=params)
        return True

    async def get_memory(self, memory_id: str) -> Memory:
        """
        Get a specific memory by ID.

        Args:
            memory_id: Memory ID

        Returns:
            Memory object

        Example:
            memory = await client.get_memory("mem_123")
        """
        data = await self._request("GET", f"/memories/{memory_id}")
        return Memory(**data)

    async def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        importance: Optional[float] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Memory:
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
            memory = await client.update_memory(
                "mem_123",
                importance=0.9,
                tags=["preferences", "high-priority"]
            )
        """
        payload = {}
        if content is not None:
            payload["content"] = content
        if importance is not None:
            payload["importance"] = importance
        if tags is not None:
            payload["tags"] = tags
        if metadata is not None:
            payload["metadata"] = metadata

        data = await self._request("PATCH", f"/memories/{memory_id}", json=payload)
        return Memory(**data)

    # Association methods

    async def associate(
        self,
        source_id: str,
        target_id: str,
        relationship: RelationshipType,
        strength: float = 0.5,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Association:
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
            assoc = await client.associate(
                source_id="mem_123",
                target_id="mem_456",
                relationship=RelationshipType.SOLVES,
                strength=0.9
            )
        """
        payload = {
            "target_id": target_id,
            "relationship": relationship.value,
            "strength": strength,
        }
        if metadata:
            payload["metadata"] = metadata

        data = await self._request("POST", f"/memories/{source_id}/associate", json=payload)
        return Association(**data)

    async def get_associations(
        self,
        memory_id: str,
        direction: str = "both",
    ) -> list[Association]:
        """
        Get associations for a memory.

        Args:
            memory_id: Memory ID
            direction: "outgoing", "incoming", or "both" (default: "both")

        Returns:
            List of associations

        Example:
            associations = await client.get_associations("mem_123")
        """
        params = {"direction": direction}
        data = await self._request("GET", f"/memories/{memory_id}/associations", params=params)

        associations_adapter = TypeAdapter(list[Association])
        return associations_adapter.validate_python(data.get("associations", []))

    # Session methods

    async def create_session(self, ttl_seconds: int = 3600) -> Session:
        """
        Create a new working memory session.

        Args:
            ttl_seconds: Time to live in seconds (default: 3600 = 1 hour)

        Returns:
            Created session

        Example:
            session = await client.create_session(ttl_seconds=7200)
        """
        payload = {"ttl_seconds": ttl_seconds}
        data = await self._request("POST", "/sessions", json=payload)
        return Session(**data)

    async def get_session(self, session_id: str) -> Session:
        """
        Get a session by ID.

        Args:
            session_id: Session ID

        Returns:
            Session object
        """
        data = await self._request("GET", f"/sessions/{session_id}")
        return Session(**data)

    async def set_context(
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
            await client.set_context(
                "sess_123",
                "current_file",
                {"path": "auth.py", "line": 42}
            )
        """
        payload = {
            "key": key,
            "value": value,
        }
        if ttl_seconds is not None:
            payload["ttl_seconds"] = ttl_seconds

        await self._request("POST", f"/sessions/{session_id}/context", json=payload)

    async def get_context(
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
            context = await client.get_context(
                "sess_123",
                ["current_file", "user_intent"]
            )
        """
        params = {"keys": ",".join(keys)}
        data = await self._request("GET", f"/sessions/{session_id}/context", params=params)
        return data.get("context", {})

    async def get_briefing(self, lookback_hours: int = 24) -> SessionBriefing:
        """
        Get a session briefing with recent activity and context.

        Args:
            lookback_hours: How far back to look for activity (default: 24)

        Returns:
            Session briefing

        Example:
            briefing = await client.get_briefing(lookback_hours=48)
        """
        params = {"lookback_hours": lookback_hours}
        data = await self._request("GET", "/sessions/briefing", params=params)
        return SessionBriefing(**data)

    # Workspace methods

    async def create_workspace(self, name: str) -> Workspace:
        """
        Create a new workspace.

        Args:
            name: Workspace name

        Returns:
            Created workspace

        Example:
            workspace = await client.create_workspace("my-project")
        """
        payload = {"name": name}
        data = await self._request("POST", "/workspaces", json=payload)
        return Workspace(**data)

    async def get_workspace(self, workspace_id: Optional[str] = None) -> Workspace:
        """
        Get workspace details.

        Args:
            workspace_id: Workspace ID (uses default if not provided)

        Returns:
            Workspace object

        Example:
            workspace = await client.get_workspace()
        """
        ws_id = workspace_id or self.workspace_id
        if not ws_id:
            raise ValueError("workspace_id must be provided or set on client")

        data = await self._request("GET", f"/workspaces/{ws_id}")
        return Workspace(**data)
