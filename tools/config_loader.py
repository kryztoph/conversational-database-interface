"""
Flexible configuration loader for CGI Chat
Supports multiple credential sources with fallback chain:
1. System Keyring (most secure)
2. Environment Variables (.env file)
3. Default values
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Try to import keyring (optional dependency)
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
    print("⚠️  keyring not installed. Install with: pip install keyring")

# Load .env file
load_dotenv()

SERVICE_NAME = "cgi_chat"


class ConfigLoader:
    """Load configuration from multiple sources with fallback"""
    
    def __init__(self, service_name: str = SERVICE_NAME, use_keyring: bool = True):
        """
        Initialize config loader
        
        Args:
            service_name: Name of keyring service
            use_keyring: Whether to try keyring (if available)
        """
        self.service_name = service_name
        self.use_keyring = use_keyring and KEYRING_AVAILABLE
        self._cache = {}
    
    def get(self, key: str, default: Optional[str] = None, 
            env_var: Optional[str] = None) -> Optional[str]:
        """
        Get configuration value with fallback chain
        
        Args:
            key: Configuration key (for keyring lookup)
            default: Default value if not found
            env_var: Environment variable name (if different from key)
        
        Returns:
            Configuration value or None
        """
        # Use cache if available
        if key in self._cache:
            return self._cache[key]
        
        value = None
        
        # 1. Try keyring first
        if self.use_keyring:
            try:
                value = keyring.get_password(self.service_name, key.lower())
                if value:
                    self._cache[key] = value
                    return value
            except Exception:
                pass  # Keyring failed, continue to next source
        
        # 2. Try environment variable
        env_key = env_var or key.upper()
        value = os.getenv(env_key)
        if value:
            self._cache[key] = value
            return value
        
        # 3. Use default
        if default is not None:
            self._cache[key] = default
            return default
        
        return None
    
    def require(self, key: str, env_var: Optional[str] = None) -> str:
        """
        Get required configuration value, raise if not found
        
        Args:
            key: Configuration key
            env_var: Environment variable name (if different from key)
        
        Returns:
            Configuration value
        
        Raises:
            ValueError: If value not found
        """
        value = self.get(key, env_var=env_var)
        if value is None:
            raise ValueError(
                f"Required configuration '{key}' not found. "
                f"Set it in keyring or {env_var or key.upper()} environment variable."
            )
        return value
    
    def get_database_config(self):
        """Get database configuration as dict"""
        return {
            "host": self.get("postgres_host", "localhost", "POSTGRES_HOST"),
            "port": int(self.get("postgres_port", "5432", "POSTGRES_PORT")),
            "user": self.require("postgres_user", "POSTGRES_USER"),
            "password": self.require("postgres_password", "POSTGRES_PASSWORD"),
            "database": self.get("postgres_db", "cgidb", "POSTGRES_DB"),
        }
    
    def get_llama_config(self):
        """Get LLM server configuration"""
        return {
            "api_url": self.get("llama_api_url", "http://localhost:8080", "LLAMA_API_URL"),
            "model_file": self.get("model_file", env_var="MODEL_FILE"),
        }
    
    def get_embedding_config(self):
        """Get embedding model configuration"""
        return {
            "model": self.get("embedding_model", "all-MiniLM-L6-v2", "EMBEDDING_MODEL"),
        }
    
    def print_config_sources(self):
        """Print which config sources are being used"""
        print("\n🔧 Configuration Sources:")
        if self.use_keyring:
            print(f"  ✓ System Keyring: {self.service_name}")
        else:
            print("  ✗ System Keyring: Not available")
        print("  ✓ Environment Variables: .env file")
        print("  ✓ Default values: Fallback\n")


# Global instance (convenience)
config = ConfigLoader()


def get_config(key: str, default: Optional[str] = None, 
               env_var: Optional[str] = None) -> Optional[str]:
    """Convenience function to get config value"""
    return config.get(key, default, env_var)


def require_config(key: str, env_var: Optional[str] = None) -> str:
    """Convenience function to get required config value"""
    return config.require(key, env_var)


# Example usage
if __name__ == "__main__":
    # Demo the config loader
    print("=" * 70)
    print("CGI Chat - Configuration Loader Demo")
    print("=" * 70)
    
    loader = ConfigLoader()
    loader.print_config_sources()
    
    try:
        # Database config
        db_config = loader.get_database_config()
        print("📊 Database Configuration:")
        print(f"  Host: {db_config['host']}")
        print(f"  Port: {db_config['port']}")
        print(f"  User: {db_config['user']}")
        print(f"  Password: {'*' * len(db_config['password'])}")
        print(f"  Database: {db_config['database']}")
        
        # LLM config
        print("\n🤖 LLM Configuration:")
        llm_config = loader.get_llama_config()
        print(f"  API URL: {llm_config['api_url']}")
        if llm_config['model_file']:
            print(f"  Model File: {llm_config['model_file']}")
        
        # Embedding config
        print("\n📚 Embedding Configuration:")
        emb_config = loader.get_embedding_config()
        print(f"  Model: {emb_config['model']}")
        
        print("\n✓ All configurations loaded successfully")
        
    except ValueError as e:
        print(f"\n❌ Error: {e}")
        print("\nRun 'python tools/credentials_setup.py' to set up credentials")
