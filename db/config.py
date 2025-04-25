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
        
        # Create account table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS account (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            server TEXT NOT NULL,
            port INTEGER NOT NULL
        )
        ''')
        
        conn.commit()
    finally:
        conn.close()

# Account configuration functions
def get_account(account_id=1):
    """Get account configuration"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM account WHERE id = ?", (account_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        conn.close()

def set_account(email, character, password, colors, description, owner, account_id=1):
    """Set account configuration"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # First check if account exists
        cursor.execute("SELECT COUNT(*) FROM account WHERE id = ?", (account_id,))
        exists = cursor.fetchone()[0] > 0
        
        if exists:
            cursor.execute('''
            UPDATE account SET 
                email = ?, 
                character = ?, 
                password = ?, 
                colors = ?, 
                description = ?,
                owner = ?
            WHERE id = ?
            ''', (email, character, password, colors, description, owner, account_id))
        else:
            cursor.execute('''
            INSERT INTO account (
                email, character, password, colors, description, owner, id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (email, character, password, colors, description, owner, account_id))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error setting account: {e}")
        return False
    finally:
        conn.close()

# Connection configuration functions
def get_connection_config(conn_id=1):
    """Get connection configuration"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM connection WHERE id = ?", (conn_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        conn.close()

def set_connection_config(server, port, conn_id=1):
    """Set connection configuration"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # First check if connection exists
        cursor.execute("SELECT COUNT(*) FROM connection WHERE id = ?", (conn_id,))
        exists = cursor.fetchone()[0] > 0
        
        if exists:
            cursor.execute('''
            UPDATE connection SET 
                server = ?, 
                port = ?
            WHERE id = ?
            ''', (server, port, conn_id))
        else:
            cursor.execute('''
            INSERT INTO connection (
                server, port, id
            ) VALUES (?, ?, ?)
            ''', (server, port, conn_id))
        
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
        if 'account' in old_config and isinstance(old_config['account'], list) and len(old_config['account']) > 0:
            account = old_config['account'][0]
            set_account(
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
                port=connection.get('port', 0)
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
def import_from_json(json_path):
    """Import configuration from a JSON file"""
    try:
        with open(json_path, 'r') as f:
            config_data = json.load(f)
        
        conn = get_connection()
        try:
            conn.execute("BEGIN TRANSACTION")
            
            # Import account data
            if 'account' in config_data and isinstance(config_data['account'], list) and len(config_data['account']) > 0:
                account = config_data['account'][0]
                set_account(
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
                    port=connection.get('port', 0)
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