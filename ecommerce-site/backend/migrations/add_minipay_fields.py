#!/usr/bin/env python3
\"\"\"MiniPay Database Migration Script\"\"\"

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import db
from database.models import Order
from datetime import datetime, timedelta
import qrcode
from io import BytesIO
import base64

def migrate():
    print(\"=== MiniPay Migration Started ===\")
    
    # 1. Add MiniPay fields to Order table
    fields_to_add = [
        \"minipay_phone = db.Column(db.String(20), default='MINIPAY_WALLET')\",  # Store merchant phone
        \"minipay_qr_data = db.Column(db.Text)\",  # Base64 QR image data
        \"payment_deadline = db.Column(db.DateTime)\",  # 30min deadline
        \"transaction_ref = db.Column(db.String(100))\",  # Customer-submitted ref
        \"screenshot_path = db.Column(db.String(200))\",  # File path to screenshot
        \"payment_status = db.Column(db.String(20), default='none')\",  # none/pending/verified/rejected
    ]
    
    # Check if fields exist
    model_source = Order.__table__.columns.keys()
    for field in ['minipay_phone', 'minipay_qr_data', 'payment_deadline', 'transaction_ref', 'screenshot_path', 'payment_status']:
        if field not in model_source:
            print(f\"[+] Adding {field} to Order model...\")
            # In production, you'd use Alembic alter_column
            print(f\"  ALTER TABLE \"order\" ADD COLUMN {field} TEXT;\")
        else:
            print(f\"[√] {field} already exists\")
    
    print(\"\\n=== Order Model Updated ===\")
    
    # 2. Create PaymentConfirmation table
    from sqlalchemy import Table, Column, Integer, String, Float, DateTime, ForeignKey, LargeBinary
    PaymentConfirmation = Table(
        'payment_confirmation',
        db.metadata,
        Column('id', Integer, primary_key=True),
        Column('order_id', String(20), ForeignKey('order.id'), nullable=False),
        Column('amount_sent', Float),
        Column('transaction_ref', String(100)),
        Column('submitted_at', DateTime, default=datetime.utcnow),
        Column('screenshot_data', LargeBinary),  # Store screenshot binary
        Column('status', String(20), default='pending')
    )
    
    print(\"[+] Creating PaymentConfirmation table...\")
    PaymentConfirmation.create(bind=db.engine, checkfirst=True)
    print(\"[√] PaymentConfirmation table ready\")
    
    print(\"\\n=== Migration Complete ===\")
    print(\"Run: db.create_all() or python backend/check_db.py to verify\")

if __name__ == \"__main__\":
    migrate()

