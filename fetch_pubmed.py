import requests
import json
import time

keywords = [
    'headache treatment', 'pain relief medication', 'antibiotic treatment',
    'hypertension drug therapy', 'diabetes medication', 'antihistamine allergy',
    'gastric ulcer treatment', 'fever medication', 'anticoagulant therapy',
    'antidepressant medication'
]

all_articles = []

for kw in keywords:
    # 搜尋文章 ID
    search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={kw}&retmax=50&retmode=json"
    res = requests.get(search_url)
    ids = res.json().get('esearchresult', {}).get('idlist', [])
    
    if not ids:
        continue

    # 抓摘要
    fetch_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={','.join(ids)}&retmode=json&rettype=abstract"
    res = requests.get(fetch_url)
    
    # 用另一個 API 抓結構化資料
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

with open('pubmed.json', 'w') as f:
    json.dump({'articles': all_articles}, f)
print(f"完成，共 {len(all_articles)} 筆")
