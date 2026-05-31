import requests
import json
import time

all_results = []
skip = 0
limit = 100
target = 25000

while len(all_results) < target:
    url = f"https://api.fda.gov/drug/enforcement.json?limit={limit}&skip={skip}"
    res = requests.get(url)
    if res.status_code != 200:
        print(f"停止，狀態碼：{res.status_code}")
        break
    data = res.json()
    results = data.get('results', [])
    if not results:
        print("沒有更多資料")
        break
    all_results.extend(results)
    skip += limit
    print(f"已抓取 {len(all_results)} 筆...")
    time.sleep(0.3)

with open('fda_safety.json', 'w') as f:
    json.dump({'results': all_results}, f)
print(f"完成，共 {len(all_results)} 筆")
