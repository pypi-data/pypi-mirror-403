# LangChain-Encrypted-Redis-Memory
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/langchain-encrypted-redis-memory.svg)](https://pypi.org/project/langchain-encrypted-redis-memory/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**A Secure, Encrypted Redis Chat Memory for LangChain Applications**

LangChain-Encrypted-Redis-Memory extends `RedisChatMessageHistory` to provide **AES-128 encryption** for all stored messages. Built on top of [mores-encryption](https://pypi.org/project/mores-encryption/), it ensures sensitive conversation data remains protected at rest.

Perfect for securing chat histories containing PII, medical data, financial information, or any sensitive conversation data in your LangChain applications.

LangChain-Encrypted-Redis-Memory removes the cryptographic complexity so you can focus on building — not configuring.

---

## Features

- **AES-128 Encryption** — Messages encrypted using Fernet (AES-128 CBC with PKCS7 padding)
- **HMAC-SHA256 Integrity** — Cryptographic verification of message integrity
- **URL-safe Base64 Output** — Encrypted data stored in URL-safe format
- **Drop-in Replacement** — Compatible with LangChain's chat memory interface
- **TTL Support** — Optional time-to-live for automatic message expiration
- **Type Filtering** — Supports human, AI, and system message types
- **Zero-Config Encryption** — Automatic key handling via mores-encryption

---

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

---

## Setup

### Generate Encryption Key

Run this command in your terminal:

```bash
python -c "from cryptography.fernet import Fernet; print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())"
```

### Save to .env

Copy the output and save it in your `.env` file:

```env
ENCRYPTION_KEY=your_generated_key_here
```

---

## Usage

### 1. Basic Usage

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

### 2. With TTL (Auto-expiry)

```python
# Messages expire after 1 hour
history = EncryptedRedisChatMessageHistory(
    session_id="user-123",
    url="redis://localhost:6379",
    ttl=3600  # seconds
)
```

### 3. Reset Session History

```python
# Clear history for a specific session
EncryptedRedisChatMessageHistory.reset_session_history(
    url="redis://localhost:6379",
    session_id="user-123"
)
```

---

## Why Use LangChain-Encrypted-Redis-Memory?

**Because securing chat history shouldn't be painful.**

Most developers store sensitive conversation data in Redis without encryption — exposing PII, medical records, and confidential information to potential breaches.

LangChain-Encrypted-Redis-Memory gives you:

- **Automatic Encryption** — Messages encrypted before storage
- **Transparent Decryption** — Seamless retrieval without extra code
- **LangChain Compatible** — Works with all LangChain memory patterns
- **Production Ready** — Built on proven cryptographic standards
- **Minimal Code Changes** — Drop-in replacement for RedisChatMessageHistory

---

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `ENCRYPTION_KEY` | Base64-encoded 32-byte Fernet key | No (Auto-generated if missing) | N/A |

### Redis Connection URLs

```python
# Local Redis
url="redis://localhost:6379"

# With password
url="redis://:password@localhost:6379"

# With database selection
url="redis://localhost:6379/1"

# TLS connection
url="rediss://localhost:6379"
```

### Key Generation

Run these commands to generate secure values for your `.env` file:

**Generate Encryption Key:**
```bash
python -c "from cryptography.fernet import Fernet; print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())"
```

---

## API Reference

### EncryptedRedisChatMessageHistory

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

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `messages` | `List[BaseMessage]` | List of decrypted messages |

### Methods

| Method | Description |
|--------|-------------|
| `add_message(message)` | Encrypt and store a message |
| `clear()` | Delete all messages for this session |
| `reset_session_history(url, session_id)` | Static method to clear a session |

---

## Security Implementation Details

- **Encryption:** `cryptography.fernet.Fernet` (AES-128 CBC with PKCS7 padding, HMAC-SHA256 for integrity)
- **Key Management:** Automatic loading from `ENCRYPTION_KEY` environment variable
- **Encoding:** All outputs are URL-safe Base64 encoded strings
- **Library:** Built on [mores-encryption](https://pypi.org/project/mores-encryption/) for proven security

---

## Development

### Setup

```bash
git clone https://github.com/HATAKEkakshi/langchain-encrypted-redis-memory.git
cd langchain-encrypted-redis-memory
python -m venv venv
source venv/bin/activate
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

---

## Documentation & Source Code

- **GitHub:** [https://github.com/HATAKEkakshi/langchain-encrypted-redis-memory](https://github.com/HATAKEkakshi/langchain-encrypted-redis-memory)
- **PyPI:** [https://pypi.org/project/langchain-encrypted-redis-memory/](https://pypi.org/project/langchain-encrypted-redis-memory/)
- **mores-encryption:** [https://pypi.org/project/mores-encryption/](https://pypi.org/project/mores-encryption/)

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Author

**Hemant Kumar** — [GitHub](https://github.com/HATAKEkakshi)

---

## Acknowledgments

- [LangChain](https://github.com/langchain-ai/langchain) for the excellent LLM framework
- [mores-encryption](https://github.com/HATAKEkakshi/mores-encryption) for encryption utilities
- [cryptography](https://cryptography.io/) for secure encryption primitives
