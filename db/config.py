import sqlite3
import json
import os
import pathlib

# Ensure data directory exists
db_dir = pathlib.Path(__file__).parent.parent / "data"
db_dir.mkdir(exist_ok=True)

DB_PATH = db_dir / "config.db"

def get_connection():
    """Return a connection to the database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable row factory for dict-like access
    return conn

def initialize_database():
    """Create the database schema if it doesn't exist"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # Create account table with name field
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS account (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,  -- Profile name for selection
            email TEXT NOT NULL,
            character TEXT NOT NULL,
            password TEXT NOT NULL,
            colors TEXT NOT NULL,
            description TEXT NOT NULL,
            owner TEXT NOT NULL
        )
        ''')
        
        # Create connection settings table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS connection (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            server TEXT NOT NULL,
            port INTEGER NOT NULL,
            FOREIGN KEY (account_id) REFERENCES account(id)
        )
        ''')
        
        conn.commit()
        
        # Check if we need to add the name column to existing table
        cursor.execute("PRAGMA table_info(account)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "name" not in columns:
            # Add name column to existing accounts
            cursor.execute("ALTER TABLE account ADD COLUMN name TEXT")
            cursor.execute("UPDATE account SET name = 'default' WHERE name IS NULL")
            conn.commit()
            
        # Check if we need to add the account_id column to connection table
        cursor.execute("PRAGMA table_info(connection)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "account_id" not in columns:
            # Update connection table
            cursor.execute("ALTER TABLE connection ADD COLUMN account_id INTEGER DEFAULT 1")
            cursor.execute("UPDATE connection SET account_id = 1 WHERE account_id IS NULL")
            conn.commit()
    finally:
        conn.close()

# Account configuration functions
def get_account(account_id=None, name=None):
    """Get account configuration by ID or name"""
    if account_id is None and name is None:
        # Default to ID 1 if neither specified
        account_id = 1
        
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if account_id is not None:
            cursor.execute("SELECT * FROM account WHERE id = ?", (account_id,))
        else:
            cursor.execute("SELECT * FROM account WHERE name = ?", (name,))
            
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        conn.close()

def list_accounts():
    """List all available accounts"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, character, owner, colors FROM account ORDER BY id")
        accounts = [dict(row) for row in cursor.fetchall()]
        return accounts
    finally:
        conn.close()

def set_account(email, character, password, colors, description, owner, name="default", account_id=None):
    """Set account configuration"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        if account_id is not None:
            # Update existing account by ID
            cursor.execute('''
            UPDATE account SET 
                name = ?,
                email = ?, 
                character = ?, 
                password = ?, 
                colors = ?, 
                description = ?,
                owner = ?
            WHERE id = ?
            ''', (name, email, character, password, colors, description, owner, account_id))
        else:
            # Check if account with this name already exists
            cursor.execute("SELECT id FROM account WHERE name = ?", (name,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing account by name
                cursor.execute('''
                UPDATE account SET 
                    email = ?, 
                    character = ?, 
                    password = ?, 
                    colors = ?, 
                    description = ?,
                    owner = ?
                WHERE name = ?
                ''', (email, character, password, colors, description, owner, name))
            else:
                # Create new account
                cursor.execute('''
                INSERT INTO account (
                    name, email, character, password, colors, description, owner
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (name, email, character, password, colors, description, owner))
        
        conn.commit()
        
        # Get the account ID for the connection
        if account_id is None:
            cursor.execute("SELECT id FROM account WHERE name = ?", (name,))
            account_id = cursor.fetchone()[0]
            
        return account_id
    except Exception as e:
        print(f"Error setting account: {e}")
        return None
    finally:
        conn.close()

def delete_account(account_id=None, name=None):
    """Delete an account by ID or name"""
    if account_id is None and name is None:
        return False
        
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # First get the account ID if name was provided
        if account_id is None:
            cursor.execute("SELECT id FROM account WHERE name = ?", (name,))
            row = cursor.fetchone()
            if not row:
                return False
            account_id = row[0]
        
        # Delete related connection configs
        cursor.execute("DELETE FROM connection WHERE account_id = ?", (account_id,))
        
        # Delete the account
        if account_id is not None:
            cursor.execute("DELETE FROM account WHERE id = ?", (account_id,))
        else:
            cursor.execute("DELETE FROM account WHERE name = ?", (name,))
            
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting account: {e}")
        return False
    finally:
        conn.close()

# Connection configuration functions
def get_connection_config(conn_id=None, account_id=None, account_name=None):
    """Get connection configuration"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        if conn_id is not None:
            cursor.execute("SELECT * FROM connection WHERE id = ?", (conn_id,))
        else:
            # Always get the first connection regardless of account
            cursor.execute("SELECT * FROM connection LIMIT 1")
            
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        conn.close()

def list_connection_configs():
    """List all connection configurations with account names"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.id, c.account_id, c.server, c.port, a.name as account_name
            FROM connection c
            JOIN account a ON c.account_id = a.id
            ORDER BY a.name
        """)
        connections = [dict(row) for row in cursor.fetchall()]
        return connections
    finally:
        conn.close()

def set_connection_config(server, port, account_id=None, account_name=None):
    """Set connection configuration for an account"""
    if account_name is not None and account_id is None:
        # Get account ID from name
        account = get_account(name=account_name)
        if account:
            account_id = account['id']
    
    if account_id is None:
        # Default to account ID 1
        account_id = 1
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # Check if connection exists for this account
        cursor.execute("SELECT id FROM connection WHERE account_id = ?", (account_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing connection
            cursor.execute('''
            UPDATE connection SET 
                server = ?, 
                port = ?
            WHERE account_id = ?
            ''', (server, port, account_id))
        else:
            # Create new connection
            cursor.execute('''
            INSERT INTO connection (
                account_id, server, port
            ) VALUES (?, ?, ?)
            ''', (account_id, server, port))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error setting connection: {e}")
        return False
    finally:
        conn.close()

# Migration from old key-value store to relational tables
def migrate_from_old_format():
    """Migrate from the old key-value format to the new relational format"""
    conn = get_connection()
    try:
        # Check if old table exists
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='config'")
        if not cursor.fetchone():
            print("Old config table not found, nothing to migrate")
            return False
            
        # Get data from old table
        cursor.execute("SELECT key, value FROM config")
        old_config = {}
        for key, value in cursor.fetchall():
            try:
                old_config[key] = json.loads(value)
            except:
                old_config[key] = value
                
        # Migrate account data
        account_id = None
        if 'account' in old_config and isinstance(old_config['account'], list) and len(old_config['account']) > 0:
            account = old_config['account'][0]
            account_id = set_account(
                name="default",
                email=account.get('email', ''),
                character=account.get('character', ''),
                password=account.get('password', ''),
                colors=account.get('colors', ''),
                description=account.get('desc', ''),
                owner=account.get('owner', '')
            )
            
        # Migrate connection data
        if 'connection' in old_config and isinstance(old_config['connection'], list) and len(old_config['connection']) > 0:
            connection = old_config['connection'][0]
            set_connection_config(
                server=connection.get('server', ''),
                port=connection.get('port', 0),
                account_id=account_id
            )
                
        # Rename old table for backup
        cursor.execute("ALTER TABLE config RENAME TO config_old")
        conn.commit()
        return True
    except Exception as e:
        print(f"Error migrating old format: {e}")
        return False
    finally:
        conn.close()

# Import from JSON file to relational structure
def import_from_json(json_path, profile_name="default"):
    """Import configuration from a JSON file"""
    try:
        with open(json_path, 'r') as f:
            config_data = json.load(f)
        
        conn = get_connection()
        try:
            conn.execute("BEGIN TRANSACTION")
            
            # Import account data
            account_id = None
            if 'account' in config_data and isinstance(config_data['account'], list) and len(config_data['account']) > 0:
                account = config_data['account'][0]
                account_id = set_account(
                    name=profile_name,
                    email=account.get('email', ''),
                    character=account.get('character', ''),
                    password=account.get('password', ''),
                    colors=account.get('colors', ''),
                    description=account.get('desc', ''),
                    owner=account.get('owner', '')
                )
                
            # Import connection data
            if 'connection' in config_data and isinstance(config_data['connection'], list) and len(config_data['connection']) > 0:
                connection = config_data['connection'][0]
                set_connection_config(
                    server=connection.get('server', ''),
                    port=connection.get('port', 0),
                    account_id=account_id
                )
                    
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Failed to import config: {e}")
            return False
        finally:
            conn.close()
    except Exception as e:
        print(f"Error reading config file: {e}")
        return False 