# Credentials Management - Quick Start

**Current Status:** ✅ Your app uses .env files (good for development)

**Want better security?** Follow this guide.

---

## 🎯 Recommended Upgrade: System Keyring

### Why?
- ✅ Passwords encrypted by your OS
- ✅ No plaintext files on disk  
- ✅ 100% backward compatible with .env
- ✅ Takes 5 minutes to set up

### How?

**1. Install keyring:**
```bash
cd /home/fox/Projects/cgi
source .venv/bin/activate
pip install keyring
```

**2. Store credentials:**
```bash
python tools/credentials_setup.py
```

**3. Update chat.py:** (2 lines to change)
```python
# Replace this:
from dotenv import load_dotenv
import os
load_dotenv()
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "cgipass")

# With this:
import sys
sys.path.insert(0, 'tools')
from config_loader import config
POSTGRES_PASSWORD = config.get("postgres_password", "cgipass", "POSTGRES_PASSWORD")
```

**4. Done!** Your app now uses keyring but still works with .env

---

## 📚 Full Documentation

- **CREDENTIAL_MANAGEMENT.md** - Complete guide to all techniques
- **KEYRING_INTEGRATION_EXAMPLE.md** - Detailed integration steps
- **tools/credentials_setup.py** - Interactive setup tool
- **tools/config_loader.py** - Configuration loader module

---

## 🔒 Security Levels

| Method | Security | Setup Time | Best For |
|--------|----------|------------|----------|
| **.env files** (current) | 🟡 Medium | 0 min | Development |
| **System Keyring** | 🟢 Good | 5 min | Desktop/single-user |
| **Docker Secrets** | 🟢 Good | 10 min | Containers |
| **Cloud Secret Manager** | 🟢 Excellent | 30 min | Cloud production |
| **HashiCorp Vault** | 🟢 Excellent | 2-4 hours | Enterprise |

---

## ❓ FAQ

**Q: Will this break my existing setup?**  
A: No! It's 100% backward compatible. If keyring isn't available, it uses .env

**Q: Can I use .env for some values and keyring for others?**  
A: Yes! It tries keyring first, then .env, then defaults.

**Q: What if I don't want to use keyring?**  
A: Don't install it. Your app works exactly as before with .env files.

**Q: Is .env secure enough?**  
A: For development: Yes. For production: Use keyring or cloud secrets.

---

## 🚀 Next Steps

1. Read **CREDENTIAL_MANAGEMENT.md** for overview of all options
2. Try **keyring** upgrade (5 minutes, fully reversible)
3. For production: Consider Docker Secrets or Cloud Secret Manager

**Questions?** Check the full documentation in `docs/`
