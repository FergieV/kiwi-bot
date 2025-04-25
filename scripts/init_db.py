#!/usr/bin/env python3
import sys
import os
import pathlib

# Add project root to path to import db.config
sys.path.append(str(pathlib.Path(__file__).parent.parent))
from db.config import initialize_database, set_account, set_connection_config

def main():
    """Initialize the database with default template"""
    print("Initializing KiwiBot database...")
    
    # Initialize database schema
    initialize_database()
    
    # Create default account
    account_id = set_account(
        name="default",
        email="your@email.com",
        character="YourBotName",
        password="your_password",
        colors="nynn",
        description="A friendly bot",
        owner="YourCharacterName"
    )
    
    if not account_id:
        print("Failed to create default account")
        return 1
    
    # Create default connection
    success = set_connection_config(
        server="lightbringer.furcadia.com",
        port=6500,
        account_id=account_id
    )
    
    if not success:
        print("Failed to create default connection")
        return 1
    
    print("\nDatabase initialized successfully!")
    print("\nNext steps:")
    print("1. Edit the default account using the web interface or command line:")
    print("   - Web: cd admin && python app.py")
    print("   - CLI: python scripts/account_manager.py edit --name default")
    print("\n2. Start the bot:")
    print("   python main.py --profile default")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 