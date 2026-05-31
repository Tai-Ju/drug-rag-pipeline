import requests
import json
import time

keywords = [
    'drug interaction clinical', 'pediatric medication dosage',
    'elderly drug therapy', 'pregnancy medication safety',
    'anticoagulant warfarin therapy', 'opioid pain management',
    'antihypertensive drug comparison', 'statin cardiovascular therapy',
    'proton pump inhibitor therapy', 'beta blocker heart therapy',
    'ACE inhibitor kidney protection', 'diuretic fluid therapy',
    'benzodiazepine anxiety treatment', 'SSRI depression treatment',
    'antipsychotic schizophrenia therapy', 'mood stabilizer bipolar',
    'corticosteroid inflammation therapy', 'insulin diabetes management',
    'bronchodilator COPD treatment', 'antiplatelet stroke prevention',
    'calcium channel blocker therapy', 'ARB hypertension treatment',
    'fibrate cholesterol therapy', 'H2 blocker acid therapy',
    'antiepileptic seizure treatment', 'NSAID inflammation pain',
    'muscle relaxant therapy', 'antiemetic nausea treatment',
    'laxative constipation therapy', 'antiparasitic infection treatment'
]

all_articles = []

for kw in keywords:
    search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={kw}&retmax=50&retmode=json"
    res = requests.get(search_url)
    ids = res.json().get('esearchresult', {}).get('idlist', [])
    if not ids:
        continue

    summary_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={','.join(ids)}&retmode=json"
    res = requests.get(summary_url)
    data = res.json().get('result', {})

    for pid in ids:
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
