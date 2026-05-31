import requests
import json
import time

guidelines = []

# FDA Approved Drugs - 抓全部
print("抓取 FDA Approved Drugs...")
skip = 0
limit = 100
while True:
    url = f"https://api.fda.gov/drug/drugsfda.json?limit={limit}&skip={skip}"
    res = requests.get(url)
    if res.status_code != 200:
        print(f"停止，狀態碼：{res.status_code}")
        break
    data = res.json()
    results = data.get('results', [])
    if not results:
        print("沒有更多資料")
        break
    for item in results:
        products = item.get('products', [])
        submissions = item.get('submissions', [])
        sub_text = ''
        for s in submissions[:3]:
            sub_text += f"submission_type: {s.get('submission_type','')}, submission_status: {s.get('submission_status','')}\n"
        for p in products:
            text = f"brand_name: {p.get('brand_name','')}\ndosage_form: {p.get('dosage_form','')}\nroute: {p.get('route','')}\nmarketing_status: {p.get('marketing_status','')}\nreference_drug: {p.get('reference_drug','')}\n{sub_text}"
            if text.strip():
                guidelines.append({
                    'text': text,
                    'source': 'FDA Approved Drugs',
                    'name': p.get('brand_name', 'Unknown')[:50]
                })
    skip += limit
    print(f"已抓取 {len(guidelines)} 筆...")
    time.sleep(0.3)

print(f"FDA Approved Drugs: {len(guidelines)} 筆")

# WHO Drug Information API
print("抓取 WHO Drug Information...")
who_drugs = ['aspirin', 'ibuprofen', 'metformin', 'amoxicillin', 'atorvastatin',
             'omeprazole', 'lisinopril', 'amlodipine', 'warfarin', 'insulin',
             'salbutamol', 'prednisolone', 'ciprofloxacin', 'fluconazole', 'metronidazole',
             'diazepam', 'morphine', 'paracetamol', 'cotrimoxazole', 'doxycycline']

for drug in who_drugs:
    url = f"https://rxnav.nlm.nih.gov/REST/drugs.json?name={drug}"
    res = requests.get(url)
    if res.status_code == 200:
        data = res.json()
        for group in data.get('drugGroup', {}).get('conceptGroup', []):
            for concept in group.get('conceptProperties', []):
                text = f"drug_name: {concept['name']}\nrxcui: {concept['rxcui']}\nwho_essential: true\n"
                guidelines.append({
                    'text': text,
                    'source': 'WHO Essential Medicines',
                    'name': concept['name'][:50]
                })
    print(f"WHO {drug}: 共 {len(guidelines)} 筆累計")
    time.sleep(0.3)

with open('guidelines.json', 'w') as f:
    json.dump({'guidelines': guidelines}, f)
print(f"完成，共 {len(guidelines)} 筆")
