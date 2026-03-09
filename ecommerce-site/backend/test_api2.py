import requests

base = 'http://localhost:5000'
headers = {'X-Admin-Bypass': 'admin-panel-direct-access'}

def req(path):
    try:
        r = requests.get(base + path, headers=headers)
        print(path, r.status_code, r.text[:500])
    except Exception as e:
        print('error', path, e)

req('/api/admin/analytics?days=30')
req('/api/admin/orders?page=1&per_page=10')
req('/api/admin/users/2')
