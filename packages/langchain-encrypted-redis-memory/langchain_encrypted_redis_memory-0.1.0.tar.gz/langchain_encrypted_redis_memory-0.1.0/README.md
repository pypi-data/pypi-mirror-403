# langchain-encrypted-redis-memory

A secure, encrypted Redis chat message history for LangChain applications. This package extends `RedisChatMessageHistory` to provide AES-128 encryption for all stored messages, ensuring sensitive conversation data remains protected at rest.

## Features

- **AES-128 Encryption** - Messages encrypted using Fernet (AES-128 CBC with PKCS7 padding)
- **HMAC-SHA256 Integrity** - Cryptographic verification of message integrity
- **URL-safe Base64** - Encrypted data stored in URL-safe format
- **Drop-in Replacement** - Compatible with LangChain's chat memory interface
- **TTL Support** - Optional time-to-live for automatic message expiration
- **Type Filtering** - Supports human, AI, and system message types

## Installation

```bash
pip install langchain-encrypted-redis-memory
```

Or install from source:

```bash
git clone https://github.com/HATAKEkakshi/langchain-encrypted-redis-memory.git
cd langchain-encrypted-redis-memory
pip install -e .
```

## Requirements

- Python >= 3.8
- Redis server
- Environment variable `ENCRYPTION_KEY` (32-byte URL-safe base64 key)

### Generate Encryption Key

```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())  # Add this to your .env file
```

Or via command line:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Quick Start

### Basic Usage

```python
from langchain_encrypted_redis_memory import EncryptedRedisChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage

# Create encrypted history
history = EncryptedRedisChatMessageHistory(
    session_id="user-123",
    url="redis://localhost:6379"
)

# Add messages (automatically encrypted)
history.add_message(HumanMessage(content="Hello, how are you?"))
history.add_message(AIMessage(content="I'm doing great, thank you!"))

# Retrieve messages (automatically decrypted)
messages = history.messages
for msg in messages:
    print(f"{msg.type}: {msg.content}")
```

### With TTL (Auto-expiry)

```python
# Messages expire after 1 hour
history = EncryptedRedisChatMessageHistory(
    session_id="user-123",
    url="redis://localhost:6379",
    ttl=3600  # seconds
)
```

### With LangChain ConversationBufferMemory

```python
from langchain.memory import ConversationBufferMemory
from langchain_encrypted_redis_memory import EncryptedRedisChatMessageHistory

history = EncryptedRedisChatMessageHistory(
    session_id="user-123",
    url="redis://localhost:6379"
)

memory = ConversationBufferMemory(
    chat_memory=history,
    return_messages=True
)
```

### Reset Session History

```python
# Clear history for a specific session
EncryptedRedisChatMessageHistory.reset_session_history(
    url="redis://localhost:6379",
    session_id="user-123"
)
```

## Configuration

### Environment Variables

Create a `.env` file in your project root:

```env
ENCRYPTION_KEY=your-32-byte-url-safe-base64-key
```

### Redis Connection

The `url` parameter accepts standard Redis connection strings:

```python
# Local Redis
url="redis://localhost:6379"

# With password
url="redis://:password@localhost:6379"

# With database selection
url="redis://localhost:6379/1"

# Redis Sentinel
url="redis+sentinel://localhost:26379/mymaster/0"
```

## API Reference

### EncryptedRedisChatMessageHistory

#### Constructor

```python
EncryptedRedisChatMessageHistory(
    session_id: str,
    url: str,
    ttl: Optional[int] = None,
    key_prefix: str = "message_store:"
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | `str` | Unique identifier for the chat session |
| `url` | `str` | Redis connection URL |
| `ttl` | `int` | Optional TTL in seconds for message expiration |
| `key_prefix` | `str` | Prefix for Redis keys (default: `message_store:`) |

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `messages` | `List[BaseMessage]` | List of decrypted messages |

#### Methods

| Method | Description |
|--------|-------------|
| `add_message(message)` | Encrypt and store a message |
| `clear()` | Delete all messages for this session |
| `reset_session_history(url, session_id)` | Static method to clear a session |

## Security

### Encryption Details

- **Algorithm**: AES-128 in CBC mode with PKCS7 padding
- **Key Derivation**: Fernet specification (URL-safe base64)
- **Integrity**: HMAC-SHA256 for authentication
- **IV**: Randomly generated for each encryption operation

### Best Practices

1. **Key Management**: Store `ENCRYPTION_KEY` securely (secrets manager, environment variable)
2. **Key Rotation**: Implement key rotation for long-lived applications
3. **Network Security**: Use TLS for Redis connections in production
4. **Access Control**: Use Redis ACLs to limit access

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/HATAKEkakshi/langchain-encrypted-redis-memory.git
cd langchain-encrypted-redis-memory

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# With verbose output
pytest -v

# With coverage
pytest --cov=langchain_encrypted_redis_memory

# Skip integration tests
pytest -m "not integration"
```

### Code Quality

```bash
# Format code
black langchain_encrypted_redis_memory tests

# Lint
flake8 langchain_encrypted_redis_memory tests

# Type check
mypy langchain_encrypted_redis_memory
```

## Project Structure

```
langchain-encrypted-redis-memory/
├── langchain_encrypted_redis_memory/
│   ├── __init__.py
│   └── EncryptedRedisChatMemory.py
├── tests/
│   ├── __init__.py
│   └── test_encrypted_redis_chat_memory.py
├── .gitignore
├── .env.example
├── LICENSE
├── README.md
├── pyproject.toml
├── pytest.ini
├── requirements.txt
└── setup.cfg
```

## Dependencies

- [langchain](https://github.com/langchain-ai/langchain) - LLM application framework
- [langchain-community](https://github.com/langchain-ai/langchain) - Community integrations
- [redis](https://github.com/redis/redis-py) - Redis Python client
- [mores-encryption](https://github.com/HATAKEkakshi/mores-encryption) - Encryption utilities

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Author

**Hemant Kumar** - [GitHub](https://github.com/HATAKEkakshi)

## Acknowledgments

- [LangChain](https://github.com/langchain-ai/langchain) for the excellent LLM framework
- [cryptography](https://cryptography.io/) for secure encryption primitives
