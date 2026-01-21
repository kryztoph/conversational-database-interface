# CGI Chat - Conversational Database Interface

A powerful CLI tool that combines natural language to SQL generation, conversational memory, and RAG (Retrieval-Augmented Generation) using PostgreSQL, llama.cpp, and Python.

## Features

- **Natural Language to SQL**: Ask questions in plain English and get SQL queries generated and executed
- **Chat History**: Persistent conversation storage across sessions
- **RAG with pgvector**: Vector similarity search over knowledge base documents
- **Interactive CLI**: Rich terminal interface with command support
- **Sample Database**: Pre-populated e-commerce database for testing

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Python    │◄────►│  llama.cpp   │      │ PostgreSQL  │
│  CLI App    │      │    Server    │      │  + pgvector │
│             │◄─────────────────────────►│             │
└─────────────┘      └──────────────┘      └─────────────┘
```

## Prerequisites

- Docker and Docker Compose
- A GGUF model file (4B-8B parameters recommended)

## Quick Start

### 1. Download a Model

Download a GGUF model and place it in the `models` directory. Recommended options:

**Small (4B params, faster)**
```bash
mkdir -p models
cd models
# Download Phi-3 Mini (4B)
wget https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf
cd ..
```

**Medium (7-8B params, balanced)**
```bash
mkdir -p models
cd models
# Download Llama 3.2 (8B)
# Visit: https://huggingface.co/models?search=llama-3.2-8b-gguf
# Download your preferred quantization
cd ..
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and update the `MODEL_FILE` to match your downloaded model:

```bash
MODEL_FILE=Phi-3-mini-4k-instruct-q4.gguf
```

If you have a GPU, increase `GPU_LAYERS`:
```bash
GPU_LAYERS=35  # Adjust based on your GPU VRAM
```

### 3. Start Services

```bash
docker-compose up -d
```

This will:
- Start PostgreSQL with pgvector extension
- Initialize the database with sample data
- Start the llama.cpp server
- Start the Python chat application

### 4. Connect to Chat Interface

```bash
docker-compose exec app python chat.py
```

Or run locally (after installing dependencies):

```bash
# Activate venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Update .env with localhost settings
# POSTGRES_HOST=localhost
# LLAMA_API_URL=http://localhost:8080

# Run chat
python chat.py
```

## Usage

### Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/sql <question>` | Generate and execute SQL query | `/sql Show top 5 customers by spending` |
| `/ask <question>` | Ask using RAG knowledge base | `/ask What is your return policy?` |
| `/chat <message>` | General conversation | `/chat How does this system work?` |
| `/history` | Show chat history | `/history` |
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

### Examples

**SQL Query Generation**
```
You: /sql Show me all products in the Electronics category

Generating SQL query...

Generated Query:
┌─────────────────────────────────────────┐
│ SELECT * FROM products                  │
│ WHERE category = 'Electronics'          │
│ ORDER BY product_name;                  │
└─────────────────────────────────────────┘

Execute this query? (y/n): y

Query Results:
┌────────────┬─────────────────┬──────────────┬────────┬────────────────┐
│ product_id │ product_name    │ category     │ price  │ stock_quantity │
├────────────┼─────────────────┼──────────────┼────────┼────────────────┤
│ 1          │ Laptop Pro 15"  │ Electronics  │ 1299.99│ 25             │
│ 2          │ Wireless Mouse  │ Electronics  │ 29.99  │ 150            │
│ ...        │ ...             │ ...          │ ...    │ ...            │
└────────────┴─────────────────┴──────────────┴────────┴────────────────┘
```

**RAG Knowledge Base**
```
You: /ask What is your return policy?

Searching knowledge base...

Answer:
Our company offers a 30-day return policy on all products. Items must be
unused and in original packaging to be eligible for returns.
```

**General Chat**
```
You: /chat Can you help me understand what data we have?

Thinking...