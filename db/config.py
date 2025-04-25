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
    return sqlite3.connect(DB_PATH)

def initialize_database():
    """Create the database schema if it doesn't exist"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        ''')
        conn.commit()
    finally:
        conn.close()

def get_config(key):
    """Get a configuration value by key"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
        row = cursor.fetchone()
        return json.loads(row[0]) if row else None
    finally:
        conn.close()

def get_all_config():
    """Get all configuration as a dictionary"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM config")
        config = {}
        for key, value in cursor.fetchall():
            config[key] = json.loads(value)
        return config
    finally:
        conn.close()

def set_config(key, value):
    """Set a configuration value"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        string_value = json.dumps(value)
        cursor.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
            (key, string_value)
        )
        conn.commit()
    finally:
        conn.close()

def import_from_json(json_path):
    """Import configuration from a JSON file"""
    try:
        with open(json_path, 'r') as f:
            config_data = json.load(f)
        
        conn = get_connection()
        try:
            conn.execute("BEGIN TRANSACTION")
            for key, value in config_data.items():
                set_config(key, value)
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