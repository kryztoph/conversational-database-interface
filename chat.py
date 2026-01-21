#!/usr/bin/env python3
"""
CGI Chat - Conversational Database Interface
Combines SQL generation, chat history, and RAG capabilities
"""

import os
import sys
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Tuple

import psycopg2
from psycopg2.extras import RealDictCursor
from openai import OpenAI
from sentence_transformers import SentenceTransformer
import numpy as np
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize console for rich output
console = Console()

# Configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_USER = os.getenv("POSTGRES_USER", "cgiuser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "cgipass")
POSTGRES_DB = os.getenv("POSTGRES_DB", "cgidb")
LLAMA_API_URL = os.getenv("LLAMA_API_URL", "http://localhost:8080")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Session ID for chat history
SESSION_ID = str(uuid.uuid4())


class DatabaseManager:
    """Manages PostgreSQL database connections and operations"""

    def __init__(self):
        self.conn = None
        self.embedding_model = None

    def connect(self):
        """Establish connection to PostgreSQL"""
        try:
            self.conn = psycopg2.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                database=POSTGRES_DB
            )
            console.print("[green]✓ Connected to PostgreSQL[/green]")
            return True
        except Exception as e:
            console.print(f"[red]✗ Database connection failed: {e}[/red]")
            return False

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """Execute a SQL query and return results"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                if cur.description:  # SELECT query
                    return [dict(row) for row in cur.fetchall()]
                else:  # INSERT/UPDATE/DELETE
                    self.conn.commit()
                    return [{"affected_rows": cur.rowcount}]
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Query execution failed: {str(e)}")

    def get_schema_info(self) -> str:
        """Get database schema information"""
        query = """
        SELECT
            table_name,
            column_name,
            data_type,
            is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position;
        """
        results = self.execute_query(query)

        schema_text = "Database Schema:\n\n"
        current_table = None
        for row in results:
            if row['table_name'] != current_table:
                current_table = row['table_name']
                schema_text += f"\nTable: {current_table}\n"
            schema_text += f"  - {row['column_name']}: {row['data_type']}"
            if row['is_nullable'] == 'NO':
                schema_text += " (NOT NULL)"
            schema_text += "\n"

        return schema_text

    def save_chat_message(self, role: str, content: str):
        """Save a chat message to history"""
        query = """
        INSERT INTO chat_history (session_id, role, content)
        VALUES (%s, %s, %s)
        """
        self.execute_query(query, (SESSION_ID, role, content))

    def get_chat_history(self, limit: int = 10) -> List[Dict]:
        """Retrieve recent chat history"""
        query = """
        SELECT role, content, timestamp
        FROM chat_history
        WHERE session_id = %s
        ORDER BY timestamp DESC
        LIMIT %s
        """
        results = self.execute_query(query, (SESSION_ID, limit))
        return list(reversed(results))

    def init_embedding_model(self):
        """Initialize the embedding model for RAG"""
        if self.embedding_model is None:
            console.print(f"[yellow]Loading embedding model: {EMBEDDING_MODEL}...[/yellow]")
            self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
            console.print("[green]✓ Embedding model loaded[/green]")

    def search_documents(self, query: str, top_k: int = 3) -> List[Dict]:
        """Search documents using vector similarity"""
        self.init_embedding_model()

        # Generate query embedding
        query_embedding = self.embedding_model.encode(query).tolist()

        # Search using cosine similarity
        search_query = """
        SELECT content, metadata, 1 - (embedding <=> %s::vector) AS similarity
        FROM documents
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> %s::vector
        LIMIT %s
        """
        return self.execute_query(search_query, (query_embedding, query_embedding, top_k))

    def embed_documents(self):
        """Generate embeddings for documents that don't have them"""
        self.init_embedding_model()

        # Get documents without embeddings
        query = "SELECT id, content FROM documents WHERE embedding IS NULL"
        docs = self.execute_query(query)

        if not docs:
            return

        console.print(f"[yellow]Generating embeddings for {len(docs)} documents...[/yellow]")

        for doc in docs:
            embedding = self.embedding_model.encode(doc['content']).tolist()
            update_query = "UPDATE documents SET embedding = %s WHERE id = %s"
            self.execute_query(update_query, (embedding, doc['id']))

        self.conn.commit()
        console.print("[green]✓ Embeddings generated[/green]")

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


class LLMClient:
    """Manages communication with llama.cpp server via OpenAI-compatible API"""

    def __init__(self):
        self.client = OpenAI(
            base_url=f"{LLAMA_API_URL}/v1",
            api_key="not-needed"  # llama.cpp doesn't require API key
        )

    def test_connection(self) -> bool:
        """Test connection to LLM server"""
        try:
            # Try a simple completion
            response = self.client.completions.create(
                model="local-model",
                prompt="Hello",
                max_tokens=5
            )
            console.print("[green]✓ Connected to LLM server[/green]")
            return True
        except Exception as e:
            console.print(f"[red]✗ LLM server connection failed: {e}[/red]")
            return False

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Send chat messages to LLM and get response"""
        try:
            response = self.client.chat.completions.create(
                model="local-model",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"LLM request failed: {str(e)}")


class ChatInterface:
    """Main chat interface combining SQL generation, RAG, and conversation"""

    def __init__(self):
        self.db = DatabaseManager()
        self.llm = LLMClient()
        self.history = InMemoryHistory()

    def initialize(self) -> bool:
        """Initialize all components"""
        console.print(Panel.fit("[bold cyan]CGI Chat - Conversational Database Interface[/bold cyan]"))

        # Connect to database
        if not self.db.connect():
            return False

        # Test LLM connection
        if not self.llm.test_connection():
            return False

        # Generate embeddings for documents
        self.db.embed_documents()

        console.print(f"\n[dim]Session ID: {SESSION_ID}[/dim]\n")
        return True

    def generate_sql_query(self, user_question: str) -> Tuple[str, str]:
        """Generate SQL query from natural language"""
        schema = self.db.get_schema_info()

        prompt = f"""You are a SQL expert. Given the following database schema and user question, generate a valid PostgreSQL query.

{schema}

User Question: {user_question}

Generate ONLY the SQL query, without any explanation or markdown formatting. The query should be ready to execute.
"""

        messages = [
            {"role": "system", "content": "You are a helpful SQL expert assistant."},
            {"role": "user", "content": prompt}
        ]

        sql_query = self.llm.chat(messages, temperature=0.2, max_tokens=500)

        # Clean up the response
        sql_query = sql_query.strip()
        # Remove markdown code blocks if present
        if sql_query.startswith("```"):
            lines = sql_query.split("\n")
            sql_query = "\n".join(lines[1:-1])

        return sql_query.strip()

    def answer_with_rag(self, user_question: str) -> str:
        """Answer question using RAG from documents"""
        # Search for relevant documents
        relevant_docs = self.db.search_documents(user_question, top_k=3)

        if not relevant_docs:
            return "I couldn't find any relevant information in the knowledge base."

        # Build context from documents
        context = "\n\n".join([
            f"Document {i+1}: {doc['content']}"
            for i, doc in enumerate(relevant_docs)
        ])

        # Get chat history
        history = self.db.get_chat_history(limit=5)
        history_text = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in history
        ])

        prompt = f"""Based on the following information, answer the user's question.

Context from knowledge base:
{context}

Recent conversation:
{history_text}

User Question: {user_question}

Provide a helpful and accurate answer based on the context provided.
"""

        messages = [
            {"role": "system", "content": "You are a helpful assistant with access to a knowledge base."},
            {"role": "user", "content": prompt}
        ]

        return self.llm.chat(messages, temperature=0.7, max_tokens=500)

    def handle_sql_mode(self, user_input: str):
        """Handle SQL query generation and execution"""
        console.print("\n[cyan]Generating SQL query...[/cyan]")

        try:
            sql_query = self.generate_sql_query(user_input)

            console.print("\n[yellow]Generated Query:[/yellow]")
            console.print(Panel(sql_query, style="dim"))

            # Ask for confirmation
            confirm = prompt("\nExecute this query? (y/n): ").lower()

            if confirm == 'y':
                results = self.db.execute_query(sql_query)

                if results:
                    # Display results in a table
                    if len(results) > 0 and isinstance(results[0], dict):
                        table = Table(show_header=True)

                        # Add columns
                        for key in results[0].keys():
                            table.add_column(str(key))

                        # Add rows (limit to first 50)
                        for row in results[:50]:
                            table.add_row(*[str(v) for v in row.values()])

                        console.print("\n[green]Query Results:[/green]")
                        console.print(table)

                        if len(results) > 50:
                            console.print(f"\n[dim]Showing 50 of {len(results)} rows[/dim]")
                    else:
                        console.print(f"\n[green]✓ Query executed: {results}[/green]")
                else:
                    console.print("\n[yellow]Query returned no results[/yellow]")
            else:
                console.print("[dim]Query cancelled[/dim]")

        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")

    def handle_rag_mode(self, user_input: str):
        """Handle RAG-based question answering"""
        console.print("\n[cyan]Searching knowledge base...[/cyan]")

        try:
            answer = self.answer_with_rag(user_input)
            console.print("\n[green]Answer:[/green]")
            console.print(Markdown(answer))
        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")

    def handle_chat_mode(self, user_input: str):
        """Handle general chat conversation"""
        # Get recent chat history
        history = self.db.get_chat_history(limit=10)

        messages = [
            {"role": "system", "content": "You are a helpful assistant for a database chat system. You can help users understand their data, answer questions, and provide guidance."}
        ]

        # Add history
        for msg in history:
            messages.append({"role": msg['role'], "content": msg['content']})

        # Add current message
        messages.append({"role": "user", "content": user_input})

        try:
            console.print("\n[cyan]Thinking...[/cyan]")
            response = self.llm.chat(messages, temperature=0.8, max_tokens=800)

            console.print("\n[green]Assistant:[/green]")
            console.print(Markdown(response))

            # Save to history
            self.db.save_chat_message("assistant", response)
        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")

    def print_help(self):
        """Print help information"""
        help_text = """
# Commands

- `/sql <question>` - Generate and execute SQL query
- `/ask <question>` - Ask about policies/info using RAG
- `/chat <message>` - General conversation
- `/history` - Show chat history
- `/schema` - Show database schema
- `/help` - Show this help
- `/quit` or `/exit` - Exit the application

# Default Mode

Without a command prefix, the system will:
1. Check if your input looks like a database question → use SQL mode
2. Otherwise → use chat mode

# Examples

```
/sql Show me all customers who spent more than $1000
/ask What is your return policy?
/chat Can you explain how to use this system?
How many products are in stock?
```
"""
        console.print(Markdown(help_text))

    def run(self):
        """Main chat loop"""
        if not self.initialize():
            console.print("[red]Failed to initialize. Exiting.[/red]")
            return

        console.print("[dim]Type /help for commands or just start chatting![/dim]\n")

        while True:
            try:
                # Get user input
                user_input = prompt("You: ", history=self.history).strip()

                if not user_input:
                    continue

                # Handle commands
                if user_input.startswith("/"):
                    parts = user_input.split(maxsplit=1)
                    command = parts[0].lower()
                    content = parts[1] if len(parts) > 1 else ""

                    if command in ["/quit", "/exit"]:
                        console.print("\n[cyan]Goodbye![/cyan]")
                        break
                    elif command == "/help":
                        self.print_help()
                    elif command == "/sql":
                        if content:
                            self.db.save_chat_message("user", user_input)
                            self.handle_sql_mode(content)
                        else:
                            console.print("[yellow]Usage: /sql <your question>[/yellow]")
                    elif command == "/ask":
                        if content:
                            self.db.save_chat_message("user", user_input)
                            self.handle_rag_mode(content)
                        else:
                            console.print("[yellow]Usage: /ask <your question>[/yellow]")
                    elif command == "/chat":
                        if content:
                            self.db.save_chat_message("user", content)
                            self.handle_chat_mode(content)
                        else:
                            console.print("[yellow]Usage: /chat <your message>[/yellow]")
                    elif command == "/history":
                        history = self.db.get_chat_history(limit=20)
                        console.print("\n[cyan]Recent Chat History:[/cyan]")
                        for msg in history:
                            console.print(f"[bold]{msg['role'].title()}:[/bold] {msg['content'][:100]}...")
                    elif command == "/schema":
                        schema = self.db.get_schema_info()
                        console.print(Markdown(f"```\n{schema}\n```"))
                    else:
                        console.print(f"[red]Unknown command: {command}[/red]")
                        console.print("[dim]Type /help for available commands[/dim]")
                else:
                    # Auto-detect mode based on content
                    self.db.save_chat_message("user", user_input)

                    # Simple heuristic: if it mentions tables/data/query keywords, use SQL
                    sql_keywords = ["show", "list", "how many", "count", "total", "find", "get", "customers", "products", "orders"]
                    if any(keyword in user_input.lower() for keyword in sql_keywords):
                        self.handle_sql_mode(user_input)
                    else:
                        self.handle_chat_mode(user_input)

                console.print()  # Add spacing

            except KeyboardInterrupt:
                console.print("\n\n[cyan]Goodbye![/cyan]")
                break
            except EOFError:
                console.print("\n[cyan]Goodbye![/cyan]")
                break
            except Exception as e:
                console.print(f"\n[red]Error: {e}[/red]\n")

        # Cleanup
        self.db.close()


if __name__ == "__main__":
    chat = ChatInterface()
    chat.run()
