# CGI Chat - Conversational Database Interface

A powerful CLI tool that combines natural language to SQL generation, conversational memory, and RAG (Retrieval-Augmented Generation) with security-first design using PostgreSQL, llama.cpp, and Python.

[![Security](https://img.shields.io/badge/Security-Read--Only%20SQL-green)](https://github.com/kryztoph/conversational-database-interface)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)

> **Note:** See [`CLAUDE.md`](CLAUDE.md) for architecture details and developer guidance.

## 📋 Table of Contents

- [Features](#features)
- [Security](#️-security)
- [Architecture](#️-architecture)
- [Quick Start](#-quick-start)
- [Usage](#-usage)
- [Database Schema](#-database-schema)
- [Configuration](#️-configuration)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)
- [Development](#-development)

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

✅ **SQL Injection Protection** - Keyword filtering, multi-statement blocking, query normalization  
✅ **Read-Only Enforcement** - Only SELECT queries execute; all write operations blocked  
✅ **Defense in Depth** - LLM instruction → query validation → execution validation → user confirmation  
✅ **LLM Prompt Injection Protection** - 8 real-world attack scenarios tested and blocked  
✅ **Credential Management** - Environment variables, system keyring, Docker Secrets support  

### Security Testing

All 22 SQL injection tests pass ✅. All 8 LLM prompt injection tests pass ✅.

```bash
# Run security test suites
python test_validation_only.py
python test_llm_prompt_injection.py
```

**Quick security demo:**
```bash
# ✅ Allowed
/sql Show me all users

# ❌ Blocked
/sql DELETE FROM users WHERE id = 1
/sql DROP TABLE users
/sql SELECT 1; DROP TABLE users;  # Multi-statement injection
```

### Production Hardening

1. **Read-Only Database User** (Recommended) ⭐
   ```bash
   docker exec -it cgi-postgres psql -U postgres -d cgidb \
     -f /docker-entrypoint-initdb.d/create_readonly_user.sql
   ```

2. **Secure Credential Storage** - Use system keyring instead of .env files
   ```bash
   pip install keyring && python tools/credentials_setup.py
   ```

📄 **Full security documentation**: 
- [`SECURITY_CHANGES.md`](SECURITY_CHANGES.md) - Detailed protection mechanisms
- [`docs/LLM_SECURITY.md`](docs/LLM_SECURITY.md) - LLM prompt injection analysis
- [`docs/CREDENTIAL_MANAGEMENT.md`](docs/CREDENTIAL_MANAGEMENT.md) - Credential security guide

---

## 🚀 Quick Start

### Prerequisites

- Docker with Compose plugin
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
docker compose up -d

# Run the chat interface
docker compose exec app python chat.py
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

---

## 📊 Database Schema

### Tables

**Core Business Data**
- `customers` - Customer information
- `products` - Product catalog with categories
- `orders` - Order header information
- `order_items` - Order line items

**Application Data**
- `chat_history` - Conversation history (session-based)
- `documents` - RAG knowledge base with 384-dim vector embeddings

**Analytics Views**
- `customer_order_summary` - Customer spending totals
- `product_sales_summary` - Product sales statistics

### Sample Data

- 5 customers
- 10 products (Electronics, Furniture, Accessories)
- 5 orders
- 8 knowledge base documents

**Schema Details**: Run `/schema` command in the app or check `postgres/init.sql`

---

## ⚙️ Configuration

### Environment Variables (`.env`)

```bash
# Database
POSTGRES_HOST=postgres      # Use 'localhost' for local development
POSTGRES_PORT=5432
POSTGRES_USER=cgiuser
POSTGRES_PASSWORD=cgipass
POSTGRES_DB=cgidb
POSTGRES_ADMIN_PASSWORD=    # Optional: for auto-recovery if cgiuser gets dropped

# LLM Server
LLAMA_API_URL=http://llama:8080  # Use 'http://localhost:8080' for local
MODEL_FILE=Phi-3-mini-4k-instruct-q4.gguf
GPU_LAYERS=0                      # 0=CPU only, 35=Most 8B models on 8GB GPU
CONTEXT_SIZE=4096

# Embedding Model
EMBEDDING_MODEL=all-MiniLM-L6-v2  # Sentence transformer (384 dimensions)
```

**Important**: If you change `EMBEDDING_MODEL` to one with different dimensions, you must update the vector column dimension in `postgres/init.sql` and recreate the database.

**Auto-Recovery**: The application automatically checks for the database user on startup. If `cgiuser` is missing and `POSTGRES_ADMIN_PASSWORD` is set, it will be recreated automatically.

### Docker Compose

**GPU Support**: Uncomment the `deploy` section in `docker compose.yml` if you have NVIDIA GPU:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

**Ports**:
- PostgreSQL: 5432
- llama.cpp: 8080

---

## 🧪 Testing

### Security Tests

Run the comprehensive security test suites:

```bash
# SQL injection tests (no database required)
python test_validation_only.py
# Expected: 22/22 tests pass ✅

# LLM prompt injection tests (no database required)
python test_llm_prompt_injection.py
# Expected: 8/8 attacks blocked ✅

# Full integration tests (requires running database)
source .venv/bin/activate
python test_security.py
```

### Database Testing

Connect directly to PostgreSQL:

```bash
# Connect to database
docker exec -it cgi-postgres psql -U cgiuser -d cgidb

# Run queries
SELECT * FROM customers;
SELECT * FROM products;
SELECT * FROM customer_order_summary;

# Check schema
\dt          # List tables
\d customers # Describe customers table
\q           # Quit
```

### LLM Server Testing

Test the llama.cpp server directly:

```bash
# Check models endpoint
curl http://localhost:8080/v1/models

# Test completion
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "local",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 50
  }'
```

---

## 🔧 Troubleshooting

### Common Issues

**"Connection refused" to LLM server**
```bash
# Check if server is running
curl http://localhost:8080/health

# Check logs
docker compose logs llama

# Restart
docker compose restart llama
```

**"Connection refused" to PostgreSQL**
```bash
# Check if database is running
docker ps | grep cgi-postgres

# Check logs
docker compose logs postgres

# Restart
docker compose restart postgres
```

**Port 8080 already in use**
```bash
# Find what's using it
lsof -i :8080

# Kill it or change port in docker compose.yml
```

**Slow model loading**
- Normal: First load takes 30-60 seconds on CPU
- Expected: ~2-3GB RAM usage
- Solution: Use GPU or smaller model

**Import errors**
```bash
# Reinstall dependencies
source .venv/bin/activate
pip install -r requirements.txt
```

### Performance Tips

- **CPU Mode** (default): 30-60s load time, 1-5s/response
- **GPU Mode**: Change `GPU_LAYERS=0` to `GPU_LAYERS=35` in `.env`
- **Smaller Model**: Use 1B-3B model for faster responses
- **Larger Context**: Increase `CONTEXT_SIZE` in `.env` for longer conversations

### Getting Help

1. Check existing documentation files
2. Run `/help` in the application
3. Check logs: `docker compose logs`
4. Open an issue on GitHub

---

## 👨‍💻 Development

### Project Structure

```
cgi/
├── chat.py                          # Main CLI application
├── docker compose.yml               # Container orchestration
├── Dockerfile                       # Python app container
├── .env                             # Configuration
├── .env.example                     # Config template
├── postgres/
│   ├── init.sql                     # Database schema & sample data
│   └── create_readonly_user.sql     # Read-only user setup
├── models/
│   └── *.gguf                       # LLM models
├── tools/
│   ├── credentials_setup.py         # Credential setup utility
│   └── config_loader.py             # Configuration loader
├── docs/
│   ├── LLM_SECURITY.md              # LLM prompt injection analysis
│   ├── CREDENTIAL_MANAGEMENT.md     # Credential security guide
│   ├── CREDENTIALS_QUICKSTART.md    # Quick credential reference
│   └── KEYRING_INTEGRATION_EXAMPLE.md  # Keyring integration
├── .venv/                           # Python virtual environment
├── requirements.txt                 # Python dependencies
├── test_validation_only.py          # SQL injection tests (22 tests)
├── test_llm_prompt_injection.py     # LLM prompt injection tests (8 tests)
├── test_security.py                 # Full security tests
├── SECURITY_CHANGES.md              # Security changelog
├── CLAUDE.md                        # AI assistant guidance
└── README.md                        # This file
```

### Running Locally

```bash
# Install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start only PostgreSQL in Docker
docker compose up -d postgres

# Run llama.cpp separately
pip install 'llama-cpp-python[server]'
python -m llama_cpp.server --model models/Phi-3-mini-4k-instruct-q4.gguf --host 0.0.0.0 --port 8080

# Update .env for localhost
POSTGRES_HOST=localhost
LLAMA_API_URL=http://localhost:8080

# Run app
python chat.py
```

### Modifying the Schema

1. Edit `postgres/init.sql`
2. Recreate database:
   ```bash
   docker compose down -v
   docker compose up -d
   ```

### Adding New Commands

Edit `chat.py`, look for the `handle_` methods in `ChatInterface` class and add your command handler.

---

## 📝 License

[Add your license here]

## 🙏 Acknowledgments

- **llama.cpp** - Fast, lightweight LLM inference
- **pgvector** - PostgreSQL vector similarity search
- **sentence-transformers** - Embedding models
- **rich** - Beautiful terminal formatting
- **prompt_toolkit** - Interactive CLI

---

## 📚 Additional Documentation

### Security Documentation
- [`SECURITY_CHANGES.md`](SECURITY_CHANGES.md) - SQL injection protection details
- [`docs/LLM_SECURITY.md`](docs/LLM_SECURITY.md) - LLM prompt injection analysis & defense
- [`docs/CREDENTIAL_MANAGEMENT.md`](docs/CREDENTIAL_MANAGEMENT.md) - Complete credential security guide
- [`docs/CREDENTIALS_QUICKSTART.md`](docs/CREDENTIALS_QUICKSTART.md) - Quick reference for credential security
- [`docs/KEYRING_INTEGRATION_EXAMPLE.md`](docs/KEYRING_INTEGRATION_EXAMPLE.md) - System keyring integration guide

### Tools & Scripts
- [`tools/credentials_setup.py`](tools/credentials_setup.py) - Interactive credential setup for system keyring
- [`tools/config_loader.py`](tools/config_loader.py) - Flexible configuration loader with fallback chain
- [`test_validation_only.py`](test_validation_only.py) - SQL injection test suite (22 tests)
- [`test_llm_prompt_injection.py`](test_llm_prompt_injection.py) - LLM prompt injection test suite (8 tests)
- [`postgres/create_readonly_user.sql`](postgres/create_readonly_user.sql) - Create read-only database user

### Other Documentation
- [`CLAUDE.md`](CLAUDE.md) - Claude Code AI assistant guidance
- [`postgres/init.sql`](postgres/init.sql) - Database schema and sample data

---

**Made with 🛡️ security-first approach**

Repository: [github.com/kryztoph/conversational-database-interface](https://github.com/kryztoph/conversational-database-interface)
