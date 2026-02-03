# Keyring Integration Example

How to upgrade chat.py to use system keyring while maintaining backward compatibility.

## Option 1: Drop-in Replacement (Minimal Changes)

### Current code (chat.py):
```python
from dotenv import load_dotenv
import os

load_dotenv()

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_USER = os.getenv("POSTGRES_USER", "cgiuser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "cgipass")
POSTGRES_DB = os.getenv("POSTGRES_DB", "cgidb")
LLAMA_API_URL = os.getenv("LLAMA_API_URL", "http://localhost:8080")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
```

### Updated code (chat.py):
```python
# Add this at the top
import sys
sys.path.insert(0, 'tools')  # Add tools directory to path

from config_loader import ConfigLoader

# Initialize config loader
config = ConfigLoader()

# Replace all os.getenv calls with config.get
POSTGRES_HOST = config.get("postgres_host", "localhost", "POSTGRES_HOST")
POSTGRES_PORT = config.get("postgres_port", "5432", "POSTGRES_PORT")
POSTGRES_USER = config.get("postgres_user", "cgiuser", "POSTGRES_USER")
POSTGRES_PASSWORD = config.get("postgres_password", "cgipass", "POSTGRES_PASSWORD")
POSTGRES_DB = config.get("postgres_db", "cgidb", "POSTGRES_DB")
LLAMA_API_URL = config.get("llama_api_url", "http://localhost:8080", "LLAMA_API_URL")
EMBEDDING_MODEL = config.get("embedding_model", "all-MiniLM-L6-v2", "EMBEDDING_MODEL")
```

**That's it!** Your code now uses keyring if available, falls back to .env if not.

## Option 2: Cleaner Approach (More Changes)

### Updated code (chat.py):
```python
import sys
sys.path.insert(0, 'tools')
from config_loader import ConfigLoader

# Initialize once
config = ConfigLoader()

# Use convenience methods
db_config = config.get_database_config()
llm_config = config.get_llama_config()
emb_config = config.get_embedding_config()

# Then in DatabaseManager.__init__:
def connect(self):
    self.conn = psycopg2.connect(**db_config)
    # ...
```

## Usage Instructions

### 1. Install keyring (optional):
```bash
cd /home/fox/Projects/cgi
source .venv/bin/activate
pip install keyring
pip freeze > requirements.txt  # Update requirements
```

### 2. Set up credentials in keyring:
```bash
python tools/credentials_setup.py
```

Follow the prompts:
```
CGI Chat - Secure Credential Setup
======================================================================
Credentials will be stored in your system keyring:
Service: cgi_chat

Press Enter to use default values shown in [brackets]

PostgreSQL Host [localhost]: 
PostgreSQL Port [5432]: 
PostgreSQL Username [cgiuser]: 
PostgreSQL Password: ********
PostgreSQL Database [cgidb]: 

======================================================================
✓ All credentials stored securely in system keyring
======================================================================
```

### 3. Update chat.py (choose Option 1 or 2 above)

### 4. Run the application:
```bash
python chat.py
```

It now reads from keyring first, falls back to .env if keyring isn't set up.

## Verification

Test which source is being used:
```bash
python tools/config_loader.py
```

Output:
```
======================================================================
CGI Chat - Configuration Loader Demo
======================================================================

🔧 Configuration Sources:
  ✓ System Keyring: cgi_chat
  ✓ Environment Variables: .env file
  ✓ Default values: Fallback

📊 Database Configuration:
  Host: localhost
  Port: 5432
  User: cgiuser
  Password: ********
  Database: cgidb

🤖 LLM Configuration:
  API URL: http://localhost:8080

📚 Embedding Configuration:
  Model: all-MiniLM-L6-v2

✓ All configurations loaded successfully
```

## Management Commands

```bash
# List stored credentials
python tools/credentials_setup.py list

# Update credentials
python tools/credentials_setup.py setup

# Delete all credentials
python tools/credentials_setup.py delete
```

## Backward Compatibility

✅ **100% backward compatible**
- If keyring isn't installed → uses .env (current behavior)
- If keyring is installed but not set up → uses .env
- If keyring is set up → uses keyring, .env as fallback

You can even mix and match:
- Store passwords in keyring
- Keep non-sensitive values in .env

## Security Benefits

**Before (current):**
```bash
$ cat .env
POSTGRES_PASSWORD=cgipass  # ⚠️ Plaintext on disk
```

**After (with keyring):**
```bash
$ cat .env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
# Password is in system keyring, not here! ✓
```

**Keyring storage:**
- Linux: Secret Service (GNOME Keyring, KWallet)
- macOS: Keychain
- Windows: Credential Locker
- All encrypted at OS level

## Migration Path

### Phase 1: Add support (no breaking changes)
1. Install keyring
2. Add config_loader.py
3. Update chat.py imports
4. Test with existing .env file

### Phase 2: Migrate credentials
5. Run credentials_setup.py
6. Remove passwords from .env
7. Keep .env for non-sensitive values

### Phase 3: Optional cleanup
8. Make keyring required in production
9. Add to deployment scripts
10. Update documentation

## Troubleshooting

**"ModuleNotFoundError: No module named 'keyring'"**
```bash
pip install keyring
```

**"keyring not installed" warning**
- This is normal if keyring isn't installed
- App will use .env file as before

**"Required configuration 'postgres_password' not found"**
- Neither keyring nor .env has the password
- Run: `python tools/credentials_setup.py`
- Or: Set in .env file

**Linux: "Failed to unlock the collection!"**
- Your desktop keyring is locked
- Log in to your desktop session first
- Or use encrypted config file instead

## Alternative: If keyring doesn't work

Use encrypted config file approach instead (see CREDENTIAL_MANAGEMENT.md, Section 3).
