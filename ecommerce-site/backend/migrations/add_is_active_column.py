"""
Migration script to add is_active column to user table.
Run this script to fix the database schema.
"""
import sys
import os

# Add the backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db import db
from app import app

def migrate():
    with app.app_context():
        # Check if column exists
        conn = db.engine.connect()
        try:
            conn.execute(db.text("SELECT is_active FROM user LIMIT 1"))
            print("Column 'is_active' already exists in user table.")
        except Exception:
            print("Adding 'is_active' column to user table...")
            conn.execute(db.text("ALTER TABLE user ADD COLUMN is_active BOOLEAN DEFAULT 1"))
            conn.commit()
            print("Successfully added 'is_active' column!")
        finally:
            conn.close()

if __name__ == "__main__":
    migrate()
