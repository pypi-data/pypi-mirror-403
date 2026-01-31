import logging
from typing import List
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.messages import BaseMessage, messages_from_dict, message_to_dict
from mores_encryption.encryption import encryption_service

logger = logging.getLogger(__name__)


class EncryptedRedisChatMessageHistory(RedisChatMessageHistory):
    """Encrypted Redis Chat Message History for LangChain.

    Provides encrypted message storage and retrieval for chat history
    using Redis as the backend. Encryption is handled by mores-encryption
    (AES-128 via Fernet with HMAC-SHA256 integrity verification).
    
    Extends RedisChatMessageHistory to encrypt all messages before storage
    and decrypt them on retrieval. Ensures sensitive conversation data
    remains protected at rest.
    
    Encryption Details:
        - Algorithm: AES-128 CBC with PKCS7 padding (Fernet)
        - Integrity: HMAC-SHA256
        - Output: URL-safe Base64 encoded strings
    
    Attributes:
        Inherits all attributes from RedisChatMessageHistory.
    
    Example:
        history = EncryptedRedisChatMessageHistory(
            session_id="user-123",
            url="redis://localhost:6379"
        )
        history.add_message(HumanMessage(content="Hello"))
        messages = history.messages
    """

    # Valid message types for filtering
    _ALLOWED_MESSAGE_TYPES = frozenset({'human', 'ai', 'system'})

    def add_message(self, message: BaseMessage) -> None:
        """Encrypt and store a message in Redis.
        
        Args:
            message: The LangChain message to store.
            
        Raises:
            Exception: If encryption or Redis operation fails.
        """
        try:
            message_dict = message_to_dict(message)
            encrypted_data = encryption_service.encrypt_json(message_dict)
            
            self.redis_client.rpush(self.key, encrypted_data)
            
            if self.ttl:
                self.redis_client.expire(self.key, self.ttl)
                
        except Exception as e:
            logger.error("Failed to add encrypted message: %s", e)
            raise

    @property
    def messages(self) -> List[BaseMessage]:
        """Retrieve and decrypt all messages from Redis.
        
        Returns:
            List of decrypted BaseMessage objects. Returns empty list
            if retrieval fails.
        """
        try:
            raw_items = self.redis_client.lrange(self.key, 0, -1)
            decrypted_messages = []
            
            for item in raw_items:
                try:
                    if isinstance(item, bytes):
                        item = item.decode("utf-8")
                    
                    decrypted_dict = encryption_service.decrypt_json(item)
                    
                    if not decrypted_dict or not isinstance(decrypted_dict, dict):
                        logger.warning("Skipping invalid message format in history")
                        continue
                    
                    msg_type = decrypted_dict.get("type", "").lower()
                    if msg_type not in self._ALLOWED_MESSAGE_TYPES:
                        logger.warning("Skipping unsupported message type: %s", msg_type)
                        continue

                    decrypted_messages.append(decrypted_dict)
                    
                except Exception as e:
                    logger.warning("Error processing history item: %s", e)
                    continue

            return messages_from_dict(decrypted_messages)
            
        except Exception as e:
            logger.error("Failed to retrieve messages: %s", e)
            return []

    def clear(self) -> None:
        """Delete all messages for this session from Redis.
        
        Raises:
            Exception: If Redis delete operation fails.
        """
        try:
            self.redis_client.delete(self.key)
        except Exception as e:
            logger.error("Failed to clear history: %s", e)
            raise

    @staticmethod
    def reset_session_history(url: str, session_id: str) -> None:
        """Clear history for a specific session.
        
        Utility method to reset conversation history, useful when
        switching contexts or starting a new conversation.
        
        Args:
            url: Redis connection URL.
            session_id: The session identifier to clear.
            
        Raises:
            Exception: If session reset fails.
        """
        try:
            temp_history = EncryptedRedisChatMessageHistory(
                session_id=session_id, 
                url=url
            )
            temp_history.clear()
            logger.info("Session history reset for: %s", session_id)
        except Exception as e:
            logger.error("Failed to reset session history: %s", e)
            raise
