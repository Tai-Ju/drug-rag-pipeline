import json
import requests
import time

all_results = []
skip = 0
limit = 100

while True:
    url = f"https://api.fda.gov/drug/label.json?limit={limit}&skip={skip}"
    res = requests.get(url)
    if res.status_code != 200:
        break
    data = res.json()
    results = data.get('results', [])
    if not results:
        break
    all_results.extend(results)
    skip += limit
    print(f"已抓取 {len(all_results)} 筆...")
    time.sleep(0.5)  # 避免被限速

with open('fda_all.json', 'w') as f:
    json.dump({'results': all_results}, f)
print(f"完成，共 {len(all_results)} 筆")
