#!/usr/bin/env python3
"""Add screenshot_data column to Message table"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import db
from database.models import Message
from sqlalchemy import text

def migrate():
    print("=== Message Screenshot Migration Started ===")

    # Check if screenshot_data column exists
    model_columns = Message.__table__.columns.keys()
    if 'screenshot_data' in model_columns:
        print("[OK] screenshot_data already exists in Message model")
    else:
        print("[!] screenshot_data should be in model but isn't detected")
        print("    This is expected if using the updated models.py")

    # Add column via raw SQL (safe if column already exists)
    try:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE message ADD COLUMN screenshot_data TEXT"))
            conn.commit()
        print("[+] Added screenshot_data column to message table")
    except Exception as e:
        if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
            print("[OK] screenshot_data column already exists in database")
        else:
            print(f"[!] Error: {e}")

    print("\n=== Migration Complete ===")
    print("Run: db.create_all() or python backend/check_db.py to verify")

if __name__ == "__main__":
    # Need to create Flask app context
    from app import create_app
    app = create_app()
    with app.app_context():
        migrate()
