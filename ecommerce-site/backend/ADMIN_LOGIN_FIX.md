# Admin Login Troubleshooting Guide

## The Problem
When you click "Login" on the admin page, it doesn't work. This is usually because:
1. **No admin user exists in the database** - The database hasn't been initialized
2. **The backend isn't running** - The Flask server isn't accessible
3. **The database isn't set up properly** - SQLite database file doesn't exist

## Quick Fix - Run These Commands

### Step 1: Open PowerShell in the backend folder
```powershell
cd "c:\Users\DESMOND\Desktop\cali clear\ecommerce-site\backend"
```

### Step 2: Initialize the database and create admin
Run this Python command to set up everything:

```powershell
python -c "
import sqlite3
import os
from werkzeug.security import generate_password_hash

db_path = 'ecommerce.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Create user table
c.execute('''CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)''')

# Create admin user
email = 'desmondhenry446@gmail.com'
password = 'desmond12345\$'
password_hash = generate_password_hash(password)

try:
    c.execute('INSERT INTO user (email, password_hash, is_admin, is_active) VALUES (?, ?, 1, 1)', (email, password_hash))
    print('Admin user created!')
except:
    print('Admin already exists')

conn.commit()
conn.close()
print('Database initialized!')
"
```

### Step 3: Start the Flask backend
```powershell
python app.py
```

You should see output like:
```
 * Running on http://0.0.0.0:5000
```

### Step 4: Test the login
Open http://localhost:5000/admin.html in your browser and try:
- **Email:** desmondhenry446@gmail.com
- **Password:** desmond12345$

Or use the "Quick Dev Login" button if the database setup worked.

---

## Still Not Working?

If you're still having issues, run this Python diagnostic:

```powershell
python -c "
import sqlite3
import os

for db_file in ['ecommerce.db', 'ecommerce_new.db']:
    if os.path.exists(db_file):
        print(f'Found database: {db_file}')
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM user')
        count = c.fetchone()[0]
        print(f'  Users in database: {count}')
        c.execute('SELECT email, is_admin FROM user WHERE is_admin=1')
        admins = c.fetchall()
        for admin in admins:
            print(f'  Admin: {admin[0]}')
        conn.close()
else:
    print('No database files found!')
"
```

This will tell you:
- If the database exists
- How many users are in it
- Which users are admins

---

## Port Already in Use?

If port 5000 is already in use, run on a different port:

```powershell
$env:FLASK_ENV="production"; python -c "from app import app; app.run(host='0.0.0.0', port=8000, debug=False)"
```

Then visit: http://localhost:8000/admin.html

---

## Direct Database Query

If you need to check the database directly:

```powershell
python -c "
import sqlite3
conn = sqlite3.connect('ecommerce.db')
c = conn.cursor()
c.execute('.tables')  # List all tables
c.execute('SELECT * FROM user LIMIT 5')  # Show first 5 users
for row in c.fetchall():
    print(row)
conn.close()
"
```
