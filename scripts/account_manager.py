#!/usr/bin/env python3
import sys
import os
import pathlib
import argparse

# Add project root to path to import db.config
sys.path.append(str(pathlib.Path(__file__).parent.parent))
from db.config import (
    initialize_database, get_account, get_connection_config, 
    set_account, set_connection_config, list_accounts, delete_account
)

def display_accounts():
    """Display all configured accounts"""
    accounts = list_accounts()
    
    if not accounts:
        print("\nNo accounts configured.")
        return False
    
    print("\nConfigured accounts:")
    print("------------------")
    for account in accounts:
        print(f"  {account['id']}: {account['name']} ({account['character']})")
    return True

def create_account(name):
    """Create a new account interactively"""
    # Check if account with this name already exists
    existing = get_account(name=name)
    if existing:
        print(f"Account '{name}' already exists.")
        overwrite = input("Do you want to update it? (y/n): ").strip().lower() == 'y'
        if not overwrite:
            return False
    
    print("\n--- Account Configuration ---")
    email = input("Email: ").strip()
    character = input("Character name: ").strip()
    password = input("Password: ").strip()
    colors = input("Colors (leave blank for default): ").strip() or "nynn"
    description = input("Character description: ").strip()
    owner = input("Owner's character name (for commands): ").strip()
    
    print("\n--- Connection Configuration ---")
    server = input("Server (default: lightbringer.furcadia.com): ").strip() or "lightbringer.furcadia.com"
    port = input("Port (default: 6500): ").strip() or "6500"
    
    try:
        port = int(port)
    except ValueError:
        print("Invalid port number, using default 6500")
        port = 6500
    
    # Save account configuration
    if existing:
        account_id = existing['id']
        account_id = set_account(
            email=email,
            character=character,
            password=password,
            colors=colors,
            description=description,
            owner=owner,
            name=name,
            account_id=account_id
        )
    else:
        account_id = set_account(
            email=email,
            character=character,
            password=password,
            colors=colors,
            description=description,
            owner=owner,
            name=name
        )
    
    if not account_id:
        print("Failed to save account configuration.")
        return False
    
    # Save connection configuration
    success = set_connection_config(
        server=server,
        port=port,
        account_id=account_id
    )
    
    if not success:
        print("Failed to save connection configuration.")
        return False
    
    print(f"\nAccount '{name}' successfully {'updated' if existing else 'created'}!")
    print(f"You can now run the bot with: python main.py --profile {name}")
    return True

def edit_account(name=None, account_id=None):
    """Edit an existing account"""
    # Get the account
    account = None
    if name:
        account = get_account(name=name)
        if not account:
            print(f"Account '{name}' not found.")
            return False
    elif account_id:
        account = get_account(account_id=account_id)
        if not account:
            print(f"Account with ID {account_id} not found.")
            return False
    else:
        print("Please specify an account name or ID.")
        return False
    
    # Get connection configuration
    connection = get_connection_config(account_id=account['id'])
    if not connection:
        # Create a default connection if none exists
        connection = {'server': 'lightbringer.furcadia.com', 'port': 6500}
    
    print(f"\nEditing account: {account['name']} ({account['character']})")
    print("Press Enter to keep existing values")
    
    # Get new values
    email = input(f"Email [{account['email']}]: ").strip() or account['email']
    character = input(f"Character [{account['character']}]: ").strip() or account['character']
    password = input(f"Password [{account['password']}]: ").strip() or account['password']
    colors = input(f"Colors [{account['colors']}]: ").strip() or account['colors']
    description = input(f"Description [{account['description']}]: ").strip() or account['description']
    owner = input(f"Owner [{account['owner']}]: ").strip() or account['owner']
    
    server = input(f"Server [{connection['server']}]: ").strip() or connection['server']
    port_str = input(f"Port [{connection['port']}]: ").strip() or str(connection['port'])
    try:
        port = int(port_str)
    except ValueError:
        print(f"Invalid port number, using {connection['port']}")
        port = connection['port']
    
    # Update account
    account_id = set_account(
        email=email,
        character=character,
        password=password,
        colors=colors,
        description=description,
        owner=owner,
        name=account['name'],
        account_id=account['id']
    )
    
    if not account_id:
        print("Failed to update account configuration.")
        return False
    
    # Update connection
    success = set_connection_config(
        server=server,
        port=port,
        account_id=account_id
    )
    
    if not success:
        print("Failed to update connection configuration.")
        return False
    
    print(f"\nAccount '{account['name']}' successfully updated!")
    return True

def remove_account(name=None, account_id=None):
    """Delete an account"""
    # Verify account exists
    account = None
    if name:
        account = get_account(name=name)
        if not account:
            print(f"Account '{name}' not found.")
            return False
    elif account_id:
        account = get_account(account_id=account_id)
        if not account:
            print(f"Account with ID {account_id} not found.")
            return False
    else:
        print("Please specify an account name or ID.")
        return False
    
    # Confirm deletion
    confirm = input(f"Are you sure you want to delete account '{account['name']}' ({account['character']})? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Operation cancelled.")
        return False
    
    # Delete account
    success = delete_account(account_id=account['id'])
    if success:
        print(f"Account '{account['name']}' successfully deleted.")
        return True
    else:
        print(f"Failed to delete account '{account['name']}'.")
        return False

def show_account_details(name=None, account_id=None):
    """Show detailed information about an account"""
    # Get the account
    account = None
    if name:
        account = get_account(name=name)
        if not account:
            print(f"Account '{name}' not found.")
            return False
    elif account_id:
        account = get_account(account_id=account_id)
        if not account:
            print(f"Account with ID {account_id} not found.")
            return False
    else:
        print("Please specify an account name or ID.")
        return False
    
    # Get connection configuration
    connection = get_connection_config(account_id=account['id'])
    if not connection:
        connection = {'server': 'Not configured', 'port': 'Not configured'}
    
    print("\nAccount Details:")
    print("--------------")
    print(f"ID:          {account['id']}")
    print(f"Name:        {account['name']}")
    print(f"Character:   {account['character']}")
    print(f"Email:       {account['email']}")
    print(f"Password:    {account['password']}")
    print(f"Colors:      {account['colors']}")
    print(f"Description: {account['description']}")
    print(f"Owner:       {account['owner']}")
    print("\nConnection:")
    print(f"Server:      {connection['server']}")
    print(f"Port:        {connection['port']}")
    
    return True

def main():
    parser = argparse.ArgumentParser(description=f"Account Manager for KiwiBot")
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all accounts')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new account')
    create_parser.add_argument('name', help='Name for the new account profile')
    
    # Edit command
    edit_parser = subparsers.add_parser('edit', help='Edit an existing account')
    edit_group = edit_parser.add_mutually_exclusive_group(required=True)
    edit_group.add_argument('-n', '--name', help='Account profile name')
    edit_group.add_argument('-i', '--id', type=int, help='Account ID')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete an account')
    delete_group = delete_parser.add_mutually_exclusive_group(required=True)
    delete_group.add_argument('-n', '--name', help='Account profile name')
    delete_group.add_argument('-i', '--id', type=int, help='Account ID')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show account details')
    show_group = show_parser.add_mutually_exclusive_group(required=True)
    show_group.add_argument('-n', '--name', help='Account profile name')
    show_group.add_argument('-i', '--id', type=int, help='Account ID')
    
    args = parser.parse_args()
    
    # Initialize database
    initialize_database()
    
    # Process commands
    if args.command == 'list' or not args.command:
        # Default to list if no command specified
        if not display_accounts():
            print("\nNo accounts configured. Use 'create' command to add one.")
    
    elif args.command == 'create':
        create_account(args.name)
    
    elif args.command == 'edit':
        edit_account(name=args.name, account_id=args.id)
    
    elif args.command == 'delete':
        remove_account(name=args.name, account_id=args.id)
    
    elif args.command == 'show':
        show_account_details(name=args.name, account_id=args.id)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 