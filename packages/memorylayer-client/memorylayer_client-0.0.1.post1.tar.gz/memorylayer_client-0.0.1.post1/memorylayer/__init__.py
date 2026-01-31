"""MemoryLayer.ai Python SDK - Memory infrastructure for AI agents."""

from .client import MemoryLayerClient
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
    RelationshipCategory,
    RelationshipType,
    SearchTolerance,
)

__version__ = "0.1.0"

__all__ = [
    # Main client
    "MemoryLayerClient",
    # Models
    "Memory",
    "RecallResult",
    "ReflectResult",
    "Association",
    "Session",
    "SessionBriefing",
    "Workspace",
    # Types
    "MemoryType",
    "MemorySubtype",
    "RecallMode",
    "SearchTolerance",
    "RelationshipType",
    "RelationshipCategory",
    # Exceptions
    "MemoryLayerError",
    "AuthenticationError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "ServerError",
]
