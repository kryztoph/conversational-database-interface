#!/usr/bin/env python3
"""
Credential Setup Utility for CGI Chat
Stores credentials in system keyring for enhanced security
"""

import keyring
import getpass
import sys

SERVICE_NAME = "cgi_chat"

CREDENTIALS = [
    {
        "key": "postgres_host",
        "prompt": "PostgreSQL Host",
        "default": "localhost",
        "secret": False
    },
    {
        "key": "postgres_port",
        "prompt": "PostgreSQL Port",
        "default": "5432",
        "secret": False
    },
    {
        "key": "postgres_user",
        "prompt": "PostgreSQL Username",
        "default": "cgiuser",
        "secret": False
    },
    {
        "key": "postgres_password",
        "prompt": "PostgreSQL Password",
        "default": None,
        "secret": True
    },
    {
        "key": "postgres_db",
        "prompt": "PostgreSQL Database",
        "default": "cgidb",
        "secret": False
    },
]


def setup_credentials():
    """Interactive credential setup"""
    print("=" * 70)
    print("CGI Chat - Secure Credential Setup")
    print("=" * 70)
    print(f"\nCredentials will be stored in your system keyring:")
    print(f"Service: {SERVICE_NAME}")
    print("\nPress Enter to use default values shown in [brackets]\n")
    
    for cred in CREDENTIALS:
        key = cred["key"]
        prompt_text = cred["prompt"]
        default = cred["default"]
        is_secret = cred["secret"]
        
        # Build prompt
        if default:
            full_prompt = f"{prompt_text} [{default}]: "
        else:
            full_prompt = f"{prompt_text}: "
        
        # Get value
        if is_secret:
            value = getpass.getpass(full_prompt)
        else:
            value = input(full_prompt)
        
        # Use default if empty
        if not value and default:
            value = default
        
        # Validate required fields
        if not value:
            print(f"❌ {prompt_text} is required!")
            sys.exit(1)
        
        # Store in keyring
        keyring.set_password(SERVICE_NAME, key, value)
        
        # Show confirmation (mask secrets)
        if is_secret:
            display_value = "*" * 8
        else:
            display_value = value
        
        print(f"✓ Stored {prompt_text}: {display_value}")
    
    print("\n" + "=" * 70)
    print("✓ All credentials stored securely in system keyring")
    print("=" * 70)
    print("\nYou can now run chat.py with keyring support")
    print("To update credentials, run this script again")


def list_credentials():
    """List stored credentials (without showing values)"""
    print("=" * 70)
    print("Stored Credentials")
    print("=" * 70)
    
    for cred in CREDENTIALS:
        key = cred["key"]
        value = keyring.get_password(SERVICE_NAME, key)
        
        if value:
            if cred["secret"]:
                display = "********"
            else:
                display = value
            print(f"✓ {cred['prompt']}: {display}")
        else:
            print(f"✗ {cred['prompt']}: Not set")


def delete_credentials():
    """Delete all stored credentials"""
    confirm = input("\n⚠️  Delete all stored credentials? (yes/no): ")
    if confirm.lower() != "yes":
        print("Cancelled")
        return
    
    print("\nDeleting credentials...")
    for cred in CREDENTIALS:
        try:
            keyring.delete_password(SERVICE_NAME, cred["key"])
            print(f"✓ Deleted {cred['prompt']}")
        except keyring.errors.PasswordDeleteError:
            print(f"  (not found: {cred['prompt']})")
    
    print("\n✓ All credentials deleted")


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "list":
            list_credentials()
        elif command == "delete":
            delete_credentials()
        elif command == "setup":
            setup_credentials()
        else:
            print(f"Unknown command: {command}")
            print("\nUsage:")
            print("  python credentials_setup.py [setup|list|delete]")
            print("\nCommands:")
            print("  setup   - Interactive credential setup (default)")
            print("  list    - List stored credentials")
            print("  delete  - Delete all stored credentials")
    else:
        # Default: setup
        setup_credentials()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
