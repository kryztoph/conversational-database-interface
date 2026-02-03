# Credential Management Best Practices for Python Applications

A comprehensive guide to externalizing and securing credentials in Python applications.

## 📋 Table of Contents

1. [Current Implementation](#current-implementation)
2. [Best Practices by Use Case](#best-practices-by-use-case)
3. [Technique 1: Environment Variables (Current)](#1-environment-variables-dotenv-current)
4. [Technique 2: System Keyring](#2-system-keyring)
5. [Technique 3: Configuration Files](#3-configuration-files-with-encryption)
6. [Technique 4: Secret Management Services](#4-secret-management-services)
7. [Technique 5: Docker Secrets](#5-docker-secrets)
8. [Technique 6: Vault Integration](#6-hashicorp-vault)
9. [Security Comparison](#security-comparison)
10. [Migration Guide](#migration-guide)

---

## Current Implementation

**Status:** ✅ Already using environment variables via `python-dotenv`

**Current code in chat.py:**
```python
from dotenv import load_dotenv
load_dotenv()

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "cgipass")
```

**Files:**
- `.env` - Contains actual credentials (gitignored)
- `.env.example` - Template without secrets (in git)

**Security Level:** 🟡 Good for development, adequate for single-user deployments

---

## Best Practices by Use Case

### Development (Local Machine)
✅ **Environment Variables** (.env file)
- Simple, fast to set up
- Good developer experience
- Already implemented

### Production (Single Server)
✅ **System Keyring** or **Encrypted Config Files**
- OS-level credential storage
- Better security than plain .env files
- No external dependencies

### Production (Cloud/Containerized)
✅ **Cloud Secret Manager** or **Docker Secrets**
- Centralized secret management
- Audit logs and rotation
- Integration with cloud platforms

### Production (Enterprise)
✅ **HashiCorp Vault** or **AWS Secrets Manager**
- Dynamic secrets
- Encryption at rest and in transit
- Access control and auditing

---

## 1. Environment Variables (dotenv) [CURRENT]

### Pros
- ✅ Simple and widely understood
- ✅ No additional dependencies beyond python-dotenv
- ✅ Easy to switch between environments
- ✅ Already implemented and working

### Cons
- ❌ Credentials stored in plaintext on disk
- ❌ Can be accidentally committed to git
- ❌ Visible in process environment

### Current Implementation

**File: .env** (gitignored)
```bash
POSTGRES_PASSWORD=cgipass
POSTGRES_USER=cgiuser
LLAMA_API_URL=http://localhost:8080
```

**File: chat.py**
```python
from dotenv import load_dotenv
import os

load_dotenv()  # Loads .env file
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
```

### Security Improvements

**Better .gitignore:**
```bash
# Secrets
.env
.env.local
.env.*.local
*.pem
*.key
secrets/
```

**File Permissions:**
```bash
# Make .env readable only by owner
chmod 600 .env
```

**Validation:**
```python
# Fail fast if critical credentials are missing
REQUIRED_VARS = ["POSTGRES_PASSWORD", "POSTGRES_USER", "POSTGRES_HOST"]
missing = [var for var in REQUIRED_VARS if not os.getenv(var)]
if missing:
    raise EnvironmentError(f"Missing required environment variables: {missing}")
```

---

## 2. System Keyring

Uses the operating system's native credential storage (e.g., macOS Keychain, Windows Credential Locker, Linux Secret Service).

### Pros
- ✅ OS-level encryption
- ✅ No plaintext files on disk
- ✅ Integrates with system security
- ✅ Simple Python API

### Cons
- ❌ Requires initial setup/population
- ❌ Different behavior per OS
- ❌ Harder to automate in CI/CD

### Implementation

**Install:**
```bash
pip install keyring
```

**Store credentials (one-time setup):**
```python
import keyring

# Store credentials
keyring.set_password("cgi_chat", "postgres_user", "cgiuser")
keyring.set_password("cgi_chat", "postgres_password", "cgipass")
```

**Updated chat.py:**
```python
import keyring
import os

def get_credential(service, key, fallback_env=None):
    """Get credential from keyring, fallback to env var"""
    value = keyring.get_password(service, key)
    if not value and fallback_env:
        value = os.getenv(fallback_env)
    return value

# Configuration
POSTGRES_USER = get_credential("cgi_chat", "postgres_user", "POSTGRES_USER")
POSTGRES_PASSWORD = get_credential("cgi_chat", "postgres_password", "POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")  # Non-sensitive
```

**Setup script (credentials.py):**
```python
#!/usr/bin/env python3
"""Setup credentials in system keyring"""
import keyring
import getpass

def setup_credentials():
    print("CGI Chat - Credential Setup")
    print("=" * 50)
    
    service = "cgi_chat"
    
    credentials = [
        ("postgres_user", "PostgreSQL Username"),
        ("postgres_password", "PostgreSQL Password"),
    ]
    
    for key, description in credentials:
        value = getpass.getpass(f"{description}: ")
        keyring.set_password(service, key, value)
        print(f"✓ Stored {description}")
    
    print("\n✓ All credentials stored securely in system keyring")

if __name__ == "__main__":
    setup_credentials()
```

**Usage:**
```bash
# One-time setup
python credentials.py

# Run application (reads from keyring)
python chat.py
```

---

## 3. Configuration Files with Encryption

Store credentials in an encrypted configuration file.

### Pros
- ✅ Encrypted at rest
- ✅ Portable across systems
- ✅ Can version control (encrypted file)
- ✅ Supports multiple environments

### Cons
- ❌ Need to manage encryption key
- ❌ More complex implementation
- ❌ Key distribution problem

### Implementation

**Install:**
```bash
pip install cryptography pyyaml
```

**Create encrypted config manager (config_manager.py):**
```python
#!/usr/bin/env python3
"""Encrypted configuration manager"""
import yaml
from cryptography.fernet import Fernet
from pathlib import Path
import os

class EncryptedConfig:
    def __init__(self, config_file="config.enc.yaml", key_file=".config.key"):
        self.config_file = Path(config_file)
        self.key_file = Path(key_file)
        self.fernet = self._load_or_create_key()
    
    def _load_or_create_key(self):
        """Load encryption key or create new one"""
        if self.key_file.exists():
            key = self.key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            self.key_file.write_bytes(key)
            self.key_file.chmod(0o600)  # Owner read/write only
        return Fernet(key)
    
    def encrypt_config(self, config_dict):
        """Encrypt and save config"""
        yaml_data = yaml.dump(config_dict)
        encrypted = self.fernet.encrypt(yaml_data.encode())
        self.config_file.write_bytes(encrypted)
    
    def decrypt_config(self):
        """Load and decrypt config"""
        if not self.config_file.exists():
            return {}
        encrypted = self.config_file.read_bytes()
        decrypted = self.fernet.decrypt(encrypted)
        return yaml.safe_load(decrypted)
    
    def get(self, key, default=None):
        """Get value from config"""
        config = self.decrypt_config()
        return config.get(key, default)

# Setup script
def setup_config():
    config = EncryptedConfig()
    
    credentials = {
        "postgres_host": input("PostgreSQL Host [localhost]: ") or "localhost",
        "postgres_port": input("PostgreSQL Port [5432]: ") or "5432",
        "postgres_user": input("PostgreSQL User: "),
        "postgres_password": input("PostgreSQL Password: "),
        "postgres_db": input("PostgreSQL Database: "),
        "llama_api_url": input("Llama API URL [http://localhost:8080]: ") or "http://localhost:8080",
    }
    
    config.encrypt_config(credentials)
    print("✓ Configuration encrypted and saved")
    print(f"✓ Config file: {config.config_file}")
    print(f"✓ Key file: {config.key_file} (keep this secure!)")

if __name__ == "__main__":
    setup_config()
```

**Updated chat.py:**
```python
from config_manager import EncryptedConfig

# Load encrypted config
config = EncryptedConfig()

POSTGRES_HOST = config.get("postgres_host", "localhost")
POSTGRES_PORT = config.get("postgres_port", "5432")
POSTGRES_USER = config.get("postgres_user")
POSTGRES_PASSWORD = config.get("postgres_password")
POSTGRES_DB = config.get("postgres_db")
```

**Usage:**
```bash
# One-time setup
python config_manager.py

# Add to .gitignore
echo ".config.key" >> .gitignore

# Run application
python chat.py
```

---

## 4. Secret Management Services

Use cloud-based secret management services.

### AWS Secrets Manager

**Install:**
```bash
pip install boto3
```

**Implementation:**
```python
import boto3
import json

def get_secret(secret_name, region_name="us-east-1"):
    """Get secret from AWS Secrets Manager"""
    client = boto3.client('secretsmanager', region_name=region_name)
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Usage
secrets = get_secret("cgi-chat/database")
POSTGRES_USER = secrets['username']
POSTGRES_PASSWORD = secrets['password']
POSTGRES_HOST = secrets['host']
```

### Google Cloud Secret Manager

**Install:**
```bash
pip install google-cloud-secret-manager
```

**Implementation:**
```python
from google.cloud import secretmanager

def get_secret(project_id, secret_id, version="latest"):
    """Get secret from GCP Secret Manager"""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version}"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

# Usage
POSTGRES_PASSWORD = get_secret("my-project", "postgres-password")
```

### Azure Key Vault

**Install:**
```bash
pip install azure-keyvault-secrets azure-identity
```

**Implementation:**
```python
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

def get_secret(vault_url, secret_name):
    """Get secret from Azure Key Vault"""
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=vault_url, credential=credential)
    return client.get_secret(secret_name).value

# Usage
VAULT_URL = "https://my-vault.vault.azure.net/"
POSTGRES_PASSWORD = get_secret(VAULT_URL, "postgres-password")
```

---

## 5. Docker Secrets

For containerized applications running in Docker Swarm or Kubernetes.

### Docker Swarm Secrets

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  app:
    image: cgi-chat
    secrets:
      - postgres_password
      - postgres_user
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
      POSTGRES_USER_FILE: /run/secrets/postgres_user

secrets:
  postgres_password:
    file: ./secrets/postgres_password.txt
  postgres_user:
    file: ./secrets/postgres_user.txt
```

**Updated chat.py:**
```python
import os

def read_secret(secret_name, default=None):
    """Read Docker secret from file"""
    secret_file = os.getenv(f"{secret_name}_FILE")
    if secret_file and os.path.exists(secret_file):
        with open(secret_file) as f:
            return f.read().strip()
    return os.getenv(secret_name, default)

# Usage
POSTGRES_USER = read_secret("POSTGRES_USER")
POSTGRES_PASSWORD = read_secret("POSTGRES_PASSWORD")
```

### Kubernetes Secrets

**secret.yaml:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: cgi-chat-secrets
type: Opaque
stringData:
  postgres-user: cgiuser
  postgres-password: cgipass
```

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cgi-chat
spec:
  template:
    spec:
      containers:
      - name: app
        env:
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: cgi-chat-secrets
              key: postgres-user
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: cgi-chat-secrets
              key: postgres-password
```

---

## 6. HashiCorp Vault

Enterprise-grade secret management with dynamic secrets, encryption, and access control.

**Install:**
```bash
pip install hvac
```

**Implementation:**
```python
import hvac
import os

class VaultClient:
    def __init__(self):
        self.client = hvac.Client(
            url=os.getenv('VAULT_ADDR', 'http://localhost:8200'),
            token=os.getenv('VAULT_TOKEN')
        )
    
    def get_secret(self, path):
        """Get secret from Vault"""
        response = self.client.secrets.kv.v2.read_secret_version(path=path)
        return response['data']['data']
    
    def get_database_credentials(self, role):
        """Get dynamic database credentials"""
        response = self.client.secrets.database.generate_credentials(name=role)
        return response['data']

# Usage
vault = VaultClient()

# Static secrets
secrets = vault.get_secret('cgi-chat/config')
POSTGRES_HOST = secrets['host']
LLAMA_API_URL = secrets['llama_url']

# Dynamic database credentials (automatically rotated)
db_creds = vault.get_database_credentials('cgi-readonly')
POSTGRES_USER = db_creds['username']
POSTGRES_PASSWORD = db_creds['password']
```

---

## Security Comparison

| Technique | Security Level | Complexity | Best For | Rotation | Audit Log |
|-----------|---------------|------------|----------|----------|-----------|
| **Environment Variables** | 🟡 Medium | Low | Development | Manual | No |
| **System Keyring** | 🟢 Good | Low | Desktop apps | Manual | OS-dependent |
| **Encrypted Config** | 🟢 Good | Medium | Portable apps | Manual | No |
| **Docker Secrets** | 🟢 Good | Medium | Containers | Manual | No |
| **Cloud Secret Manager** | 🟢 Excellent | Medium | Cloud deployments | Auto | Yes |
| **HashiCorp Vault** | 🟢 Excellent | High | Enterprise | Auto | Yes |

---

## Migration Guide

### From .env to System Keyring

1. **Install keyring:**
   ```bash
   pip install keyring
   ```

2. **Create setup script:**
   ```bash
   cp .env .env.backup
   python credentials.py  # Interactive setup
   ```

3. **Update chat.py:**
   ```python
   # Add keyring fallback
   import keyring
   import os
   
   def get_config(key, keyring_service="cgi_chat"):
       # Try keyring first
       value = keyring.get_password(keyring_service, key.lower())
       if value:
           return value
       # Fallback to environment variable
       return os.getenv(key)
   
   POSTGRES_PASSWORD = get_config("POSTGRES_PASSWORD")
   ```

4. **Test thoroughly**

5. **Remove .env file:**
   ```bash
   shred -u .env  # Secure deletion
   ```

---

## Recommendations for CGI Chat

### Current Status: ✅ Good enough for development

**Immediate improvements (5 minutes):**
```bash
# Set proper file permissions
chmod 600 .env

# Validate required variables
# (add to chat.py)
```

**For production deployment (30 minutes):**
- Use **System Keyring** for single-user desktop deployment
- Use **Docker Secrets** if already using Docker Compose
- Use **Cloud Secret Manager** if deploying to cloud

**For enterprise (varies):**
- Implement HashiCorp Vault for dynamic secrets
- Add secret rotation policies
- Enable audit logging

---

## Additional Resources

- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [12-Factor App: Config](https://12factor.net/config)
- [Python Keyring Documentation](https://pypi.org/project/keyring/)
- [AWS Secrets Manager Best Practices](https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html)

---

**Generated:** 2026-02-03  
**For:** CGI Chat - Conversational Database Interface
