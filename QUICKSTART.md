# Quick Start Guide

## Project Initialized Successfully ✓

All features have been implemented and dependencies are installed.

## What You Have

```
cgi/
├── chat.py                  # Main CLI application (18KB, 400+ lines)
├── docker-compose.yml       # Container orchestration
├── Dockerfile              # Python app container
├── postgres/init.sql       # Database with sample e-commerce data
├── requirements.txt        # Python dependencies (installed in .venv)
├── .env.example           # Configuration template
├── README.md              # Full documentation
└── .venv/                 # Virtual environment (ready to use)
```

## Features Implemented

✓ **Natural Language to SQL** - Ask questions, get SQL queries and results
✓ **Chat History** - Persistent conversation storage in PostgreSQL  
✓ **RAG with pgvector** - Vector search over knowledge base
✓ **Interactive CLI** - Rich terminal interface with commands

## Next Steps to Run

### Option 1: Docker (Recommended)

1. **Download a model** (4B-8B params)
   ```bash
   mkdir -p models
   cd models
   # Example: Download Phi-3 Mini (4B)
   wget https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf
   cd ..
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and set MODEL_FILE=Phi-3-mini-4k-instruct-q4.gguf
   ```

3. **Start services**
   ```bash
   docker-compose up -d
   ```

4. **Run chat**
   ```bash
   docker-compose exec app python chat.py
   ```

### Option 2: Local (Database Only)

1. **Start only PostgreSQL**
   ```bash
   docker-compose up -d postgres
   ```

2. **Configure .env for local**
   ```bash
   cp .env.example .env
   # Set:
   # POSTGRES_HOST=localhost
   # LLAMA_API_URL=http://localhost:8080 (if running llama.cpp separately)
   ```

3. **Activate venv and run**
   ```bash
   source .venv/bin/activate
   python chat.py
   ```

   Note: You'll need a local llama.cpp server running on port 8080.

## Testing Without LLM

To test the database connection without an LLM server, you can modify chat.py to skip the LLM test or start just PostgreSQL and check the database:

```bash
# Start PostgreSQL only
docker-compose up -d postgres

# Connect to database
docker-compose exec postgres psql -U cgiuser -d cgidb

# Check sample data
\dt                           # List tables
SELECT * FROM customers;      # View customers
SELECT * FROM products;       # View products
```

## Sample Commands

Once running:

- `/sql Show me all customers who spent more than $1000`
- `/ask What is your return policy?`
- `/chat Tell me about the database`
- `/schema` - View database schema
- `/history` - View chat history
- `/help` - Show all commands
- `/quit` - Exit

## Database Contents

- **Customers**: 5 sample customers
- **Products**: 10 sample products (Electronics, Furniture, Accessories)
- **Orders**: 5 sample orders
- **Documents**: 8 policy/info documents for RAG
- **Views**: Pre-built analytics queries

## Troubleshooting

- **No model**: Download a GGUF model first
- **Port conflicts**: Change ports in docker-compose.yml
- **Memory issues**: Use smaller model or reduce GPU_LAYERS
- **Import errors**: All dependencies are installed in .venv

See README.md for full documentation.
