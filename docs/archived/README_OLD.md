# CGI Chat - Conversational Database Interface

A powerful CLI tool that combines natural language to SQL generation, conversational memory, and RAG (Retrieval-Augmented Generation) with security-first design using PostgreSQL, llama.cpp, and Python.

[![Security](https://img.shields.io/badge/Security-Read--Only%20SQL-green)](https://github.com/kryztoph/conversational-database-interface)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)

## 📋 Table of Contents

- [Features](#features)
- [Security](#security)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
- [Database Schema](#database-schema)
- [Configuration](#configuration)
- [Development](#development)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

---

## ✨ Features

- **🔒 Secure by Default**: Read-only SQL mode with comprehensive SQL injection protection
- **💬 Natural Language to SQL**: Ask questions in plain English, get SQL queries generated and executed
- **📚 RAG with pgvector**: Vector similarity search over knowledge base documents
- **💾 Chat History**: Persistent conversation storage across sessions
- **🎨 Interactive CLI**: Rich terminal interface with beautiful formatting
- **📊 Sample Database**: Pre-populated e-commerce database for testing
- **🤖 LLM Agnostic**: Works with any OpenAI-compatible API (llama.cpp, Ollama, etc.)

---

## 🛡️ Security

**Latest Update (2026-02-03)**: Application hardened to prevent SQL injection and enforce read-only database access.

### Security Features

✅ **SQL Injection Protection**
- Keyword-based filtering prevents dangerous operations
- Multi-statement execution is blocked
- Query normalization prevents bypass attempts

✅ **Read-Only Enforcement**
- Only SELECT queries can execute
- All write operations blocked (INSERT/UPDATE/DELETE/DROP/ALTER/CREATE/TRUNCATE)
- System operations prevented (GRANT/REVOKE/EXECUTE)

✅ **Defense in Depth**
1. LLM is instructed to only generate SELECT queries
2. Generated queries are validated before execution
3. Database execution layer validates again
4. User must confirm before execution

### Security Testing

All 22 security tests pass ✅. Run the test suite:

```bash
python test_validation_only.py
```

Try these examples to see protection in action:

```bash
# ✅ Allowed - READ operations
/sql Show me all users
/sql SELECT * FROM products WHERE price > 100

# ❌ Blocked - WRITE operations
/sql DELETE FROM users WHERE id = 1
/sql UPDATE users SET password = 'hacked'
/sql DROP TABLE users
/sql SELECT 1; DROP TABLE users;  # Multi-statement injection
```

---

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Python    │◄────►│  llama.cpp   │      │ PostgreSQL  │
│  CLI App    │      │    Server    │      │  + pgvector │
│  (chat.py)  │◄─────────────────────────►│             │
└─────────────┘      └──────────────┘      └─────────────┘
```

### Components

**chat.py** - Main application with three classes:
- `DatabaseManager`: PostgreSQL operations, embeddings, chat history, and security validation
- `LLMClient`: OpenAI-compatible client for llama.cpp server
- `ChatInterface`: CLI loop with command handling and mode detection

**PostgreSQL + pgvector**: Database with vector extensions for semantic search

**llama.cpp Server**: Local LLM inference with OpenAI-compatible API

---

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- A GGUF model file (4B-8B parameters recommended)
- ~4GB RAM minimum, 8GB recommended

### 3-Step Setup

#### 1. Download a Model

```bash
mkdir -p models
cd models

# Option A: Phi-3 Mini (4B) - Fast and efficient
wget https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf

# Option B: Llama 3.2 (8B) - Better quality
# Visit: https://huggingface.co/models?search=llama-3.2-8b-gguf
# Download your preferred quantization

cd ..
```

#### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and update MODEL_FILE to match your downloaded model
```

**Example .env settings:**
```bash
MODEL_FILE=Phi-3-mini-4k-instruct-q4.gguf
GPU_LAYERS=0  # Set to 35 if you have a GPU with 8GB+ VRAM
POSTGRES_HOST=postgres
LLAMA_API_URL=http://llama:8080
```

#### 3. Start and Run

```bash
# Start all services
docker-compose up -d

# Run the chat interface
docker-compose exec app python chat.py
```

That's it! You should see:

```
╭─────────────────────────────────────────────────╮
│ CGI Chat - Conversational Database Interface   │
│ 🛡️ Security Mode: READ-ONLY SQL Queries        │
╰─────────────────────────────────────────────────╯

✓ Connected to PostgreSQL
✓ Connected to LLM server
✓ SQL injection protection enabled
✓ Write operations blocked (SELECT only)

Type /help for commands or just start chatting!

You: _
```

---

## 💻 Installation

### Option 1: Docker (Recommended)

Use the Quick Start guide above. This runs everything in containers.

### Option 2: Local Development

**Requirements:**
- Python 3.10+
- PostgreSQL 15+ with pgvector extension
- llama.cpp server running separately

**Setup:**

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL (Docker)
docker-compose up -d postgres

# Update .env for localhost
cp .env.example .env
# Edit: POSTGRES_HOST=localhost, LLAMA_API_URL=http://localhost:8080

# Run chat
python chat.py
```

### Option 3: LLM Server Options

**llama-cpp-python (Easiest for Python devs):**
```bash
pip install 'llama-cpp-python[server]'
python -m llama_cpp.server \
  --model models/Phi-3-mini-4k-instruct-q4.gguf \
  --host 0.0.0.0 --port 8080 --n_ctx 4096
```

**llama.cpp binary (Best performance):**
```bash
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp && make
./llama-server -m ../models/Phi-3-mini-4k-instruct-q4.gguf \
  --host 0.0.0.0 --port 8080 -c 4096
```

**Ollama (Easiest overall):**
```bash
# Install from https://ollama.ai
ollama serve  # Runs on port 11434
# Update .env: LLAMA_API_URL=http://localhost:11434
```

---

## 📖 Usage

### Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/sql <question>` | Generate and execute SQL query (read-only) | `/sql Show top 5 customers by spending` |
| `/ask <question>` | Ask using RAG knowledge base | `/ask What is your return policy?` |
| `/chat <message>` | General conversation with context | `/chat How does this system work?` |
| `/history` | Show recent chat history | `/history` |
| `/schema` | Display database schema | `/schema` |
| `/help` | Show help information | `/help` |
| `/quit` or `/exit` | Exit application | `/quit` |

### Auto-Detection Mode

Without a command prefix, the system automatically detects your intent:

```
You: How many customers do we have?
→ Automatically uses SQL mode

You: Tell me about your company
→ Automatically uses chat mode
```

### Example Session

**SQL Query Generation (Read-Only)**
```
You: /sql Show me all products in the Electronics category

Generating SQL query (read-only mode)...

Generated Query:
┌────────────────────────────────────────────────────┐
│ SELECT product_id, product_name, category, price, │
│        stock_quantity                              │
│ FROM products                                      │
│ WHERE category = 'Electronics'                     │
│ ORDER BY product_name;                             │
└────────────────────────────────────────────────────┘

🛡️ Security: Only SELECT queries are allowed

Execute this query? (y/n): y

Query Results:
┌────────────┬─────────────────┬──────────────┬────────┬────────────────┐
│ product_id │ product_name    │ category     │ price  │ stock_quantity │
├────────────┼─────────────────┼──────────────┼────────┼────────────────┤
│ 1          │ Laptop Pro 15"  │ Electronics  │ 1299.99│ 25             │
│ 2          │ Wireless Mouse  │ Electronics  │ 29.99  │ 150            │
└────────────┴─────────────────┴──────────────┴────────┴────────────────┘
```

**RAG Knowledge Base**
```
You: /ask What is your return policy?

Searching knowledge base...

Answer:
Our company offers a 30-day return policy on all products. Items must be
unused and in original packaging. Refunds are processed within 5-7 business
days after receiving the returned item.
```

**General Chat**
```
You: /chat What kind of data do we have in the database?

Thinking...