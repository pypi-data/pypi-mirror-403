"""MemoryLayer LangChain Integration - Persistent memory for LangChain agents."""

from .chat_message_history import MemoryLayerChatMessageHistory
from .memory import MemoryLayerConversationSummaryMemory, MemoryLayerMemory
from .sync_client import SyncMemoryLayerClient, sync_client

__version__ = "0.0.1"

__all__ = [
    # LangChain Chat History (LCEL compatible)
    "MemoryLayerChatMessageHistory",
    # Legacy BaseMemory implementations
    "MemoryLayerMemory",
    "MemoryLayerConversationSummaryMemory",
    # Synchronous client utilities
    "SyncMemoryLayerClient",
    "sync_client",
]
