"""Tests for langchain-encrypted-redis-memory package."""
import json
import logging
import pytest
from unittest.mock import MagicMock, patch

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# Import the class to test
from langchain_encrypted_redis_memory import EncryptedRedisChatMessageHistory


class TestEncryptedRedisChatMessageHistory:
    """Test suite for EncryptedRedisChatMessageHistory."""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis instance."""
        return MagicMock()

    @pytest.fixture
    def history_with_mocks(self, mock_redis):
        """Create history with mocked Redis and encryption."""
        with patch(
            "langchain_encrypted_redis_memory.EncryptedRedisChatMemory.encryption_service"
        ) as mock_encryption:
            # Configure encrypt_json to return a predictable encrypted string
            mock_encryption.encrypt_json.side_effect = lambda x: f"ENCRYPTED:{json.dumps(x)}"
            # Configure decrypt_json to reverse the encryption
            mock_encryption.decrypt_json.side_effect = lambda x: json.loads(
                x.replace("ENCRYPTED:", "")
            )
            
            with patch("redis.Redis.from_url", return_value=mock_redis):
                history = EncryptedRedisChatMessageHistory(
                    session_id="test-session",
                    url="redis://localhost:6379"
                )
                yield history, mock_redis, mock_encryption

    # -------------------------------------------------------------------------
    # add_message Tests
    # -------------------------------------------------------------------------

    def test_add_message_encrypts_and_stores(self, history_with_mocks):
        """Test that add_message encrypts the message and stores it in Redis."""
        history, mock_redis, mock_encryption = history_with_mocks
        message = HumanMessage(content="Hello, world!")

        history.add_message(message)

        # Verify encryption was called
        mock_encryption.encrypt_json.assert_called_once()
        call_args = mock_encryption.encrypt_json.call_args[0][0]
        assert call_args["type"] == "human"
        assert call_args["data"]["content"] == "Hello, world!"

        # Verify Redis rpush was called
        mock_redis.rpush.assert_called_once()

    def test_add_message_sets_ttl_when_configured(self, mock_redis):
        """Test that TTL is set when configured."""
        with patch(
            "langchain_encrypted_redis_memory.EncryptedRedisChatMemory.encryption_service"
        ) as mock_encryption:
            mock_encryption.encrypt_json.return_value = "encrypted_data"
            
            with patch("redis.Redis.from_url", return_value=mock_redis):
                history = EncryptedRedisChatMessageHistory(
                    session_id="test-session",
                    url="redis://localhost:6379",
                    ttl=3600
                )
                message = HumanMessage(content="Test")
                history.add_message(message)

        mock_redis.expire.assert_called_once()
        assert mock_redis.expire.call_args[0][1] == 3600

    def test_add_message_raises_on_encryption_failure(self, history_with_mocks):
        """Test that add_message raises exception on encryption failure."""
        history, mock_redis, mock_encryption = history_with_mocks
        mock_encryption.encrypt_json.side_effect = Exception("Encryption failed")
        message = HumanMessage(content="Test")

        with pytest.raises(Exception, match="Encryption failed"):
            history.add_message(message)

    def test_add_message_raises_on_redis_failure(self, history_with_mocks):
        """Test that add_message raises exception on Redis failure."""
        history, mock_redis, mock_encryption = history_with_mocks
        mock_redis.rpush.side_effect = Exception("Redis connection failed")
        message = HumanMessage(content="Test")

        with pytest.raises(Exception, match="Redis connection failed"):
            history.add_message(message)

    # -------------------------------------------------------------------------
    # messages Property Tests
    # -------------------------------------------------------------------------

    def test_messages_retrieves_and_decrypts(self, history_with_mocks):
        """Test that messages property retrieves and decrypts messages."""
        history, mock_redis, mock_encryption = history_with_mocks
        
        # Setup mock data
        encrypted_messages = [
            'ENCRYPTED:{"type": "human", "data": {"content": "Hello"}}',
            'ENCRYPTED:{"type": "ai", "data": {"content": "Hi there!"}}',
        ]
        mock_redis.lrange.return_value = encrypted_messages

        messages = history.messages

        assert len(messages) == 2
        assert isinstance(messages[0], HumanMessage)
        assert isinstance(messages[1], AIMessage)
        assert messages[0].content == "Hello"
        assert messages[1].content == "Hi there!"

    def test_messages_handles_bytes_input(self, history_with_mocks):
        """Test that messages handles bytes input from Redis."""
        history, mock_redis, mock_encryption = history_with_mocks
        
        encrypted_bytes = b'ENCRYPTED:{"type": "human", "data": {"content": "Test"}}'
        mock_redis.lrange.return_value = [encrypted_bytes]

        messages = history.messages

        assert len(messages) == 1
        assert messages[0].content == "Test"

    def test_messages_filters_invalid_types(self, history_with_mocks, caplog):
        """Test that messages skips invalid message types."""
        history, mock_redis, mock_encryption = history_with_mocks
        
        encrypted_messages = [
            'ENCRYPTED:{"type": "human", "data": {"content": "Valid"}}',
            'ENCRYPTED:{"type": "unknown", "data": {"content": "Invalid"}}',
        ]
        mock_redis.lrange.return_value = encrypted_messages

        with caplog.at_level(logging.WARNING):
            messages = history.messages

        assert len(messages) == 1
        assert messages[0].content == "Valid"
        assert "Skipping unsupported message type" in caplog.text

    def test_messages_handles_system_messages(self, history_with_mocks):
        """Test that system messages are properly handled."""
        history, mock_redis, mock_encryption = history_with_mocks
        
        encrypted_messages = [
            'ENCRYPTED:{"type": "system", "data": {"content": "You are a helpful assistant"}}',
        ]
        mock_redis.lrange.return_value = encrypted_messages

        messages = history.messages

        assert len(messages) == 1
        assert isinstance(messages[0], SystemMessage)

    def test_messages_returns_empty_on_retrieval_failure(self, history_with_mocks, caplog):
        """Test that messages returns empty list on Redis failure."""
        history, mock_redis, mock_encryption = history_with_mocks
        mock_redis.lrange.side_effect = Exception("Redis error")

        with caplog.at_level(logging.ERROR):
            messages = history.messages

        assert messages == []
        assert "Failed to retrieve messages" in caplog.text

    def test_messages_skips_corrupted_items(self, history_with_mocks, caplog):
        """Test that corrupted items are skipped with warning."""
        history, mock_redis, mock_encryption = history_with_mocks
        
        mock_redis.lrange.return_value = [
            'ENCRYPTED:{"type": "human", "data": {"content": "Valid"}}',
            "CORRUPTED_DATA",
        ]
        
        # Make decrypt fail for corrupted data
        def decrypt_side_effect(x):
            if "CORRUPTED" in x:
                raise Exception("Decryption failed")
            return json.loads(x.replace("ENCRYPTED:", ""))

        mock_encryption.decrypt_json.side_effect = decrypt_side_effect

        with caplog.at_level(logging.WARNING):
            messages = history.messages

        assert len(messages) == 1
        assert "Error processing history item" in caplog.text

    # -------------------------------------------------------------------------
    # clear Method Tests
    # -------------------------------------------------------------------------

    def test_clear_deletes_session_key(self, history_with_mocks):
        """Test that clear deletes the session key from Redis."""
        history, mock_redis, mock_encryption = history_with_mocks
        
        history.clear()

        mock_redis.delete.assert_called_once()

    def test_clear_raises_on_redis_failure(self, history_with_mocks, caplog):
        """Test that clear raises exception on Redis failure."""
        history, mock_redis, mock_encryption = history_with_mocks
        mock_redis.delete.side_effect = Exception("Redis delete failed")

        with caplog.at_level(logging.ERROR):
            with pytest.raises(Exception, match="Redis delete failed"):
                history.clear()

        assert "Failed to clear history" in caplog.text

    # -------------------------------------------------------------------------
    # reset_session_history Tests
    # -------------------------------------------------------------------------

    def test_reset_session_history_clears_session(self, mock_redis, caplog):
        """Test that reset_session_history clears the specified session."""
        with patch(
            "langchain_encrypted_redis_memory.EncryptedRedisChatMemory.encryption_service"
        ):
            with patch("redis.Redis.from_url", return_value=mock_redis):
                with caplog.at_level(logging.INFO):
                    EncryptedRedisChatMessageHistory.reset_session_history(
                        url="redis://localhost:6379",
                        session_id="test-session"
                    )

        mock_redis.delete.assert_called_once()
        assert "Session history reset for" in caplog.text

    def test_reset_session_history_raises_on_failure(self, mock_redis, caplog):
        """Test that reset_session_history raises exception on failure."""
        mock_redis.delete.side_effect = Exception("Clear failed")
        
        with patch(
            "langchain_encrypted_redis_memory.EncryptedRedisChatMemory.encryption_service"
        ):
            with patch("redis.Redis.from_url", return_value=mock_redis):
                with caplog.at_level(logging.ERROR):
                    with pytest.raises(Exception, match="Clear failed"):
                        EncryptedRedisChatMessageHistory.reset_session_history(
                            url="redis://localhost:6379",
                            session_id="test-session"
                        )

        assert "Failed to reset session history" in caplog.text

    # -------------------------------------------------------------------------
    # Allowed Message Types Tests
    # -------------------------------------------------------------------------

    def test_allowed_message_types_is_frozenset(self):
        """Test that _ALLOWED_MESSAGE_TYPES is a frozenset."""
        assert isinstance(
            EncryptedRedisChatMessageHistory._ALLOWED_MESSAGE_TYPES, frozenset
        )

    def test_allowed_message_types_contains_expected_types(self):
        """Test that _ALLOWED_MESSAGE_TYPES contains human, ai, and system."""
        expected = {"human", "ai", "system"}
        assert EncryptedRedisChatMessageHistory._ALLOWED_MESSAGE_TYPES == expected


class TestEncryptionIntegration:
    """Integration tests with real encryption (requires mores-encryption)."""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis instance."""
        mock = MagicMock()
        mock.lrange.return_value = []
        return mock

    @pytest.mark.integration
    def test_encryption_roundtrip(self, mock_redis):
        """Test that messages can be encrypted and decrypted correctly."""
        stored_data = []
        
        def capture_rpush(key, data):
            stored_data.append(data)
        
        mock_redis.rpush.side_effect = capture_rpush
        
        with patch("redis.Redis.from_url", return_value=mock_redis):
            history = EncryptedRedisChatMessageHistory(
                session_id="test-session",
                url="redis://localhost:6379"
            )
            
            # Add a message
            message = HumanMessage(content="Secret message")
            history.add_message(message)
            
            # Verify data was encrypted (not plaintext)
            assert len(stored_data) == 1
            assert "Secret message" not in stored_data[0]
            
            # Now retrieve and verify decryption
            mock_redis.lrange.return_value = stored_data
            messages = history.messages
            
            assert len(messages) == 1
            assert messages[0].content == "Secret message"


# -------------------------------------------------------------------------
# Conftest-style fixtures for pytest
# -------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def setup_logging():
    """Configure logging for tests."""
    logging.basicConfig(level=logging.DEBUG)
    yield
