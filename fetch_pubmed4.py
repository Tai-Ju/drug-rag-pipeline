import requests
import json
import time

keywords = [
    'drug therapy clinical trial', 'medication adverse effects',
    'pharmacotherapy guidelines', 'drug dosage optimization',
    'antibiotic clinical outcome', 'cardiovascular drug therapy',
    'neurological medication treatment', 'psychiatric drug therapy',
    'oncology chemotherapy protocol', 'infectious disease antibiotic',
    'respiratory medication therapy', 'gastrointestinal drug treatment',
    'endocrine hormone therapy', 'autoimmune disease medication',
    'pain management opioid', 'analgesia clinical study',
    'antiviral hepatitis treatment', 'HIV antiretroviral therapy',
    'tuberculosis drug regimen', 'malaria antimalarial treatment',
    'vaccine immunization clinical', 'allergy immunotherapy drug',
    'dermatology topical medication', 'ophthalmology eye drops therapy',
    'nephrology renal drug therapy', 'hematology blood disorder medication',
    'orthopedic bone medication', 'dental antibiotic prophylaxis',
    'emergency medication protocol', 'ICU critical care drug',
    'pediatric antibiotic dosing', 'geriatric polypharmacy management',
    'drug pharmacokinetics study', 'bioavailability drug absorption',
    'drug metabolism liver enzyme', 'renal drug clearance',
    'drug protein binding', 'blood brain barrier drug',
    'drug resistance mechanism', 'drug synergy combination therapy'
]

all_articles = []

for kw in keywords:
    search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={kw}&retmax=200&retmode=json"
    res = requests.get(search_url)
    ids = res.json().get('esearchresult', {}).get('idlist', [])
    if not ids:
        continue

    # 分批抓 summary（每次最多 200）
    for i in range(0, len(ids), 100):
        batch_ids = ids[i:i+100]
        summary_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={','.join(batch_ids)}&retmode=json"
        res = requests.get(summary_url)
        data = res.json().get('result', {})
        for pid in batch_ids:
            if pid in data:
                article = data[pid]
                title = article.get('title', '')
                source = article.get('source', '')
                pubdate = article.get('pubdate', '')
                authors = ', '.join([a.get('name', '') for a in article.get('authors', [])[:3]])
                if title:
                    all_articles.append({
                        'title': title,
                        'journal': source,
                        'date': pubdate,
                        'authors': authors,
                        'keyword': kw,
                        'pmid': pid
                    })
        time.sleep(0.3)

    print(f"{kw}: 共 {len(all_articles)} 筆累計")
    time.sleep(0.5)

with open('pubmed.json') as f:
    old = json.load(f)['articles']

all_articles = old + all_articles

seen = set()
unique = []
for a in all_articles:
    if a['pmid'] not in seen:
        seen.add(a['pmid'])
        unique.append(a)

with open('pubmed.json', 'w') as f:
    json.dump({'articles': unique}, f)
print(f"完成，共 {len(unique)} 筆")
