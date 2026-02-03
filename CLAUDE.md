# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CGI Chat is a conversational database interface that combines:
- **Natural Language to SQL**: LLM-powered SQL generation from plain English
- **RAG (Retrieval-Augmented Generation)**: Vector similarity search over knowledge base using pgvector
- **Persistent Chat History**: Conversation storage across sessions in PostgreSQL

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Python    │◄────►│  llama.cpp   │      │ PostgreSQL  │
│  CLI App    │      │    Server    │      │  + pgvector │
│  (chat.py)  │◄─────────────────────────►│             │
└─────────────┘      └──────────────┘      └─────────────┘
```

**chat.py** contains three main classes:
- `DatabaseManager`: PostgreSQL operations, embeddings, and chat history
- `LLMClient`: OpenAI-compatible client for llama.cpp server
- `ChatInterface`: CLI loop with command handling and mode detection

## Commands

### Run with Docker (full stack)
```bash
docker-compose up -d
docker-compose exec app python chat.py
```

### Run locally (development)
```bash
source .venv/bin/activate
pip install -r requirements.txt

# Start PostgreSQL and llama.cpp externally, then:
# Set POSTGRES_HOST=localhost and LLAMA_API_URL=http://localhost:8080 in .env
python chat.py
```

### Database operations
```bash
# Reset database (drop and recreate)
docker-compose down -v && docker-compose up -d

# Connect directly to PostgreSQL
docker-compose exec postgres psql -U cgiuser -d cgidb
```

## Configuration

Environment variables in `.env`:
- `MODEL_FILE`: Name of GGUF model in `models/` directory
- `GPU_LAYERS`: GPU layer offload (0=CPU only)
- `EMBEDDING_MODEL`: Sentence transformer model (default: all-MiniLM-L6-v2, 384 dimensions)

The embedding dimension (384) is hardcoded in `postgres/init.sql` for the vector column. If changing `EMBEDDING_MODEL` to one with different dimensions, update the schema.

## Database Schema

Key tables in `postgres/init.sql`:
- `chat_history`: Session-based conversation storage
- `documents`: RAG knowledge base with 384-dim vector embeddings
- `customers`, `products`, `orders`, `order_items`: Sample e-commerce data
- Views: `customer_order_summary`, `product_sales_summary`

## LLM Integration

Uses OpenAI-compatible API to communicate with llama.cpp server. The `LLMClient` class wraps the OpenAI Python client pointing to `LLAMA_API_URL/v1`. No API key required.
