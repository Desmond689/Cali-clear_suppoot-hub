import requests
import json

def call(path):
    r = requests.get('http://localhost:5000' + path, headers={'X-Admin-Bypass':'admin-panel-direct-access'})
    return {'path':path,'status':r.status_code,'text':r.text[:200]}

results = []
for p in ['/api/admin/analytics?days=30','/api/admin/orders?page=1&per_page=10','/api/admin/users/2']:
    results.append(call(p))

with open('endpoint_results.json','w') as f:
    json.dump(results,f)
