"""langchain-encrypted-redis-memory - Encrypted chat history for LangChain.

A LangChain-compatible Redis chat message history with AES-128 encryption.
"""
from .EncryptedRedisChatMemory import EncryptedRedisChatMessageHistory

__version__ = "0.1.0"
__all__ = ["EncryptedRedisChatMessageHistory"]
