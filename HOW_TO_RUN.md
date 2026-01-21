# How to Run CGI Chat

## Quick Start (2 Terminals)

### Terminal 1: Start the LLM Server

```bash
./start.sh
```

Wait until you see:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080
```

This takes about 30-60 seconds to load the model into memory.

### Terminal 2: Run the Chat Application

```bash
source .venv/bin/activate
python chat.py
```

## Example Session

```
You: /schema

You: /sql Show me all customers who spent more than $1000

You: /ask What is your return policy?

You: How many products do we have?

You: /history

You: /quit
```

## Available Commands

| Command | Description |
|---------|-------------|
| `/sql <question>` | Generate SQL query from natural language |
| `/ask <question>` | Query knowledge base using RAG |
| `/chat <message>` | General conversation with context |
| `/schema` | Show database schema |
| `/history` | Show recent chat history |
| `/help` | Show all commands |
| `/quit` or `/exit` | Exit the application |

## Testing Components Separately

### Test Database Only

```bash
docker exec -it cgi-postgres psql -U cgiuser -d cgidb

# Try some queries:
SELECT * FROM customers;
SELECT * FROM customer_order_summary;
\q
```

### Test LLM Server Only

```bash
# Start the server
./start.sh

# In another terminal, test with curl:
curl http://localhost:8080/v1/models

# Or test chat completion:
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "local",
    "messages": [{"role": "user", "content": "Say hello"}],
    "max_tokens": 50
  }'
```

## Troubleshooting

### Port 8080 Already in Use

```bash
# Find what's using port 8080
lsof -i :8080

# Kill it or change the port in start.sh and .env
```

### Model Loading Slowly

- **Normal**: First load takes 30-60 seconds on CPU
- **Expected**: ~2-3GB RAM usage
- **If too slow**: Consider using GPU or a smaller model

### "Connection refused" Error

Make sure the LLM server is running:
```bash
ps aux | grep llama_cpp
curl http://localhost:8080/health
```

### Database Connection Error

```bash
# Check PostgreSQL is running
docker ps | grep cgi-postgres

# Restart if needed
docker-compose restart postgres
```

## Performance Tips

- **CPU Mode** (current): 30-60 seconds load time, 1-5 sec/response
- **GPU Mode**: Change `GPU_LAYERS=0` to `GPU_LAYERS=35` in `.env` and `start.sh`
- **Smaller Model**: Use a 1B-3B model for faster responses
- **Larger Context**: Increase `--n_ctx` in `start.sh` for longer conversations

## Stopping Everything

```bash
# Stop LLM server: Ctrl+C in Terminal 1
# Stop chat app: /quit or Ctrl+C in Terminal 2
# Stop PostgreSQL:
docker-compose down
```

## Background Mode

To run the LLM server in the background:

```bash
nohup ./start.sh > llama.log 2>&1 &

# Check it's running
tail -f llama.log

# Stop it later
pkill -f "llama_cpp.server"
```

## Next Steps

1. Try the example queries above
2. Explore the database schema with `/schema`
3. Ask natural language questions with `/sql`
4. Query policies with `/ask`
5. Have conversations with `/chat`

Enjoy! 🚀
