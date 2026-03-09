import sqlite3, os
path=os.path.join('backend','instance','ecommerce.db')
print('DB path', path, 'exists', os.path.exists(path))
if not os.path.exists(path):
    raise SystemExit('database missing')
conn=sqlite3.connect(path)
c=conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table';")
print('tables',c.fetchall())
c.execute("PRAGMA table_info('user')")
print('schema',c.fetchall())
try:
    c.execute("ALTER TABLE user ADD COLUMN is_active BOOLEAN DEFAULT 1")
    print('added column')
except Exception as e:
    print('alter error', e)
conn.commit()
conn.close()