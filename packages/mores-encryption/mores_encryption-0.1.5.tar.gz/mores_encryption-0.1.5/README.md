# 🟦 Mores-Encryption

![Python](https://img.shields.io/badge/Language-Python-blue?style=for-the-badge&logo=python&logoColor=white)
![Encryption](https://img.shields.io/badge/Encryption-AES--128-green?style=for-the-badge)
[![PyPI](https://img.shields.io/badge/PyPI-View_Package-blue?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/mores-encryption/)

**A Lightweight, Production-Ready Encryption Library for Python**

Mores-Encryption is a clean, minimal, plug-and-play encryption library designed to make securing sensitive data effortless.
Built on top of industry-standard AES-128 (Fernet), it provides simple helpers for:

✔ Encrypting & decrypting strings  
✔ Deterministic hashing (searchable encryption)  
✔ Secure JSON encryption  
✔ Automatic key handling  
✔ URL-safe output

Perfect for securing PII, emails, IDs, session tokens, API keys, medical data, or database fields across any Python backend.

Mores-Encryption removes the repetitive boilerplate and cryptographic complexity so you can focus on building — not configuring.

---

## 🔒 Features

### 🔐 Simple AES-128 Encryption
One-line methods: `encrypt()` and `decrypt()`

### 🔎 Deterministic Hashing for Search
Search encrypted fields using `hash()`  
(same input + same salt = same output)

### 📦 JSON Encryption Support
Encrypt entire dictionaries with `encrypt_json()` and `decrypt_json()`

### ⚙️ Automatic Key Management
Loads `ENCRYPTION_KEY` from environment or generates a secure key if missing

### 🪶 Lightweight & Zero-Config
Only one dependency: `cryptography`

### 🌐 Works Everywhere
FastAPI, Django, Flask, LangChain, Redis, MongoDB, SQL, background jobs — plug it into anything.

---

## 📦 Installation

```bash
pip install mores-encryption
```

---

## ⚙️ Setup

Generate a secure encryption key:

```bash
python -c "from cryptography.fernet import Fernet; print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())"
```

Save it in `.env`:

```
ENCRYPTION_KEY=your_generated_key_here
```

---

## 🚀 Usage

### 1. Encrypt & Decrypt

```python
from mores_encryption.encryption import encryption_service

secret = "My Secret Data"

encrypted = encryption_service.encrypt(secret)
print("Encrypted:", encrypted)

decrypted = encryption_service.decrypt(encrypted)
print("Decrypted:", decrypted)
```

### 2. Deterministic Hashing

Perfect for searching encrypted emails, IDs, etc.

```python
email = "user@example.com"
salt = "my_static_salt"

hashed = encryption_service.hash(email, salt)
print(hashed)
```

### 3. JSON Encryption

```python
data = {"card": "1234-5678-9012-3456"}

encrypted = encryption_service.encrypt_json(data)
print(encrypted)

decrypted = encryption_service.decrypt_json(encrypted)
print(decrypted)
```

---

## 🧪 Why Use Mores-Encryption?

**Because encryption shouldn't be painful.**

Most developers struggle with cryptographic setup — salts, key formats, byte handling, serialization, JSON encoding, PBKDF2 — and end up copying the same boilerplate between projects.

Mores-Encryption gives you:

- Clean API
- Strong security defaults
- Minimal code surface
- Reusable across all your projects
- Faster development + fewer mistakes

---

## Configuration

The library uses environment variables for configuration. You can set these in your `.env` file or export them in your shell.

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `ENCRYPTION_KEY` | Base64-encoded 32-byte Fernet key. | No (Auto-generated if missing) | N/A |

### Key & Salt Generation

Run these commands in your terminal to generate secure values for your `.env` file:

**Generate Encryption Key:**
```bash
python -c "from cryptography.fernet import Fernet; print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())"
```

**Generate Salt (for deterministic hashing):**
```bash
python -c "import secrets; print('EMAIL_SALT=' + secrets.token_urlsafe(16))"
```

**Step-by-Step Setup:**
1. Run the commands above.
2. Copy the output (e.g., `ENCRYPTION_KEY=...`).
3. Paste it into your `.env` file in the project root.

> **Note**: For a complete integration example, refer to `integration.ipynb` (if included in the examples).

---

## Security Implementation Details

- **Encryption**: `cryptography.fernet.Fernet` (AES-128 CBC with PKCS7 padding, HMAC-SHA256 for integrity).
- **Hashing**: PBKDF2HMAC-SHA256 with configurable iterations (default: 200,000) and a 32-byte output length.
- **Encoding**: All outputs are URL-safe Base64 encoded strings.

---

## 📚 Documentation & Source Code

**GitHub**: [https://github.com/HATAKEkakshi/mores-encryption](https://github.com/HATAKEkakshi/mores-encryption)

---

## License

MIT License
