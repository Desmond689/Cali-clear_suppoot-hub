# Migration script to add tracking_number and carrier fields to Order table
# Run this script once after deploying the code changes

from database.db import db
from database.models import Order

def upgrade():
    # For SQLite, we can add columns using raw SQL since it's simple
    # In production, use proper migration tools like Alembic
    with db.engine.connect() as conn:
        conn.execute(db.text("ALTER TABLE order ADD COLUMN tracking_number VARCHAR(100)"))
        conn.execute(db.text("ALTER TABLE order ADD COLUMN carrier VARCHAR(50)"))
        conn.commit()
    print("Migration completed: Added tracking_number and carrier to Order table")

if __name__ == "__main__":
    from app import app
    with app.app_context():
        upgrade()
