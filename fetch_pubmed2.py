import requests
import json
import time

keywords = [
    'antibiotic resistance treatment', 'cholesterol lowering medication',
    'asthma inhaler therapy', 'anxiety medication treatment',
    'insomnia sleep medication', 'anti-inflammatory drug therapy',
    'antifungal medication', 'antiviral medication treatment',
    'chemotherapy side effects', 'immunosuppressant drug therapy',
    'thyroid medication treatment', 'osteoporosis drug therapy',
    'migraine medication treatment', 'epilepsy anticonvulsant therapy',
    'kidney disease medication', 'liver disease drug therapy',
    'heart failure medication', 'stroke prevention medication',
    'rheumatoid arthritis treatment', 'COVID antiviral treatment'
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

# 合併第一批
with open('pubmed.json') as f:
    old = json.load(f)['articles']

all_articles = old + all_articles

# 去重
seen = set()
unique = []
for a in all_articles:
    if a['pmid'] not in seen:
        seen.add(a['pmid'])
        unique.append(a)

with open('pubmed.json', 'w') as f:
    json.dump({'articles': unique}, f)
print(f"完成，共 {len(unique)} 筆")
