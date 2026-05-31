import requests
import json
import time

# 常見藥品類別關鍵字
keywords = [
    'acetaminophen', 'ibuprofen', 'aspirin', 'amoxicillin', 'metformin',
    'lisinopril', 'atorvastatin', 'omeprazole', 'metoprolol', 'amlodipine',
    'losartan', 'gabapentin', 'sertraline', 'fluoxetine', 'prednisone',
    'albuterol', 'montelukast', 'cetirizine', 'loratadine', 'diphenhydramine',
    'codeine', 'tramadol', 'morphine', 'oxycodone', 'hydrocodone',
    'warfarin', 'clopidogrel', 'insulin', 'levothyroxine', 'azithromycin'
]

all_concepts = []
for kw in keywords:
    url = f"https://rxnav.nlm.nih.gov/REST/drugs.json?name={kw}"
    res = requests.get(url)
    if res.status_code == 200:
        data = res.json()
        for group in data.get('drugGroup', {}).get('conceptGroup', []):
            for concept in group.get('conceptProperties', []):
                all_concepts.append(concept)
        print(f"{kw}: {len(all_concepts)} 筆累計")
    time.sleep(0.3)

with open('rxnorm_all.json', 'w') as f:
    json.dump({'concepts': all_concepts}, f)
print(f"完成，共 {len(all_concepts)} 筆")
