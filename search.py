#!/usr/bin/env python3
"""
文獻搜尋腳本：Local LLM + RAG + 住院藥局用藥建議
來源：PubMed、Web of Science、Scopus
輸出：CSV 格式
"""

import requests
import csv
import time
import os
import json
from datetime import datetime

# ── 設定 ──────────────────────────────────────────────────────────────────────
OUTPUT_DIR = "/Users/ruru/RuDatas/國北護/00.畢業論文/02.報告/1150515"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, f"literature_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

PUBMED_KEY = "9dac2a19d96ed694a128d242664f6c9b5608"
WOS_KEY    = "2080c67ce7d5fcf30aab6ef258a034e18a9993f3"
SCOPUS_KEY = "dee2e311a0b562b50f23e2b4f00b63d6"

# ── 搜尋查詢 ──────────────────────────────────────────────────────────────────
QUERIES = {
    "module1_local_llm": [
        "on-premise LLM deployment healthcare architecture",
        "local large language model hospital system design",
        "Ollama medical deployment framework",
        "private LLM clinical environment",
        "edge LLM healthcare infrastructure",
    ],
    "module2_rag": [
        "retrieval augmented generation clinical knowledge base design",
        "RAG pipeline medical document system",
        "vector database healthcare knowledge retrieval",
        "RAG pharmacy knowledge base implementation",
        "medical document chunking embedding strategy",
    ],
    "module3_evaluation": [
        "LLM medication recommendation output evaluation",
        "SOAP note generation LLM quality assessment",
        "pharmacist expert evaluation LLM output",
        "drug recommendation text quality rubric",
        "medication counseling AI quality framework",
    ],
    "module4_pharmacy": [
        "local LLM inpatient pharmacy implementation",
        "on-premise AI pharmacy clinical support",
        "medication information extraction local LLM",
        "hospital pharmacy AI system prototype",
        "pharmacy LLM deployment case study",
    ],
}

CSV_FIELDS = ["title", "authors", "year", "journal_source", "abstract", "doi", "keywords", "source_db"]

# ── PubMed ────────────────────────────────────────────────────────────────────
def search_pubmed(query, max_results=500):
    results = []
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    # 搜尋 ID
    search_url = f"{base}/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": f"({query}) AND (2022:2026[pdat])",
        "retmax": max_results,
        "api_key": PUBMED_KEY,
        "retmode": "json",
    }
    try:
        r = requests.get(search_url, params=params, timeout=30)
        ids = r.json().get("esearchresult", {}).get("idlist", [])
        print(f"  PubMed [{query[:40]}...]: {len(ids)} 筆")
    except Exception as e:
        print(f"  PubMed 搜尋失敗: {e}")
        return results

    if not ids:
        return results

    # 批次抓摘要
    batch_size = 100
    for i in range(0, len(ids), batch_size):
        batch = ids[i:i+batch_size]
        fetch_url = f"{base}/efetch.fcgi"
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(batch),
            "rettype": "xml",
            "retmode": "xml",
            "api_key": PUBMED_KEY,
        }
        try:
            fr = requests.get(fetch_url, params=fetch_params, timeout=60)
            import xml.etree.ElementTree as ET
            root = ET.fromstring(fr.content)
            for article in root.findall(".//PubmedArticle"):
                try:
                    title = article.findtext(".//ArticleTitle", "")
                    abstract = " ".join([t.text or "" for t in article.findall(".//AbstractText")])
                    year = article.findtext(".//PubDate/Year", "")
                    journal = article.findtext(".//Journal/Title", "")
                    doi = article.findtext(".//ELocationID[@EIdType='doi']", "")
                    authors_list = []
                    for a in article.findall(".//Author"):
                        ln = a.findtext("LastName", "")
                        fn = a.findtext("ForeName", "")
                        if ln:
                            authors_list.append(f"{ln} {fn}".strip())
                    authors = "; ".join(authors_list[:5])
                    keywords = "; ".join([k.text or "" for k in article.findall(".//Keyword")])
                    results.append({
                        "title": title,
                        "authors": authors,
                        "year": year,
                        "journal_source": journal,
                        "abstract": abstract[:1000],
                        "doi": doi,
                        "keywords": keywords,
                        "source_db": "PubMed",
                    })
                except:
                    pass
            time.sleep(0.4)
        except Exception as e:
            print(f"  PubMed fetch 失敗: {e}")

    return results


# ── Scopus (SDOL) ─────────────────────────────────────────────────────────────
def search_scopus(query, max_results=500):
    results = []
    url = "https://api.elsevier.com/content/search/scopus"
    headers = {"X-ELS-APIKey": SCOPUS_KEY, "Accept": "application/json"}
    
    start = 0
    count = 25
    fetched = 0
    
    while fetched < max_results:
        params = {
            "query": f"TITLE-ABS-KEY({query}) AND PUBYEAR > 2021 AND PUBYEAR < 2027",
            "count": count,
            "start": start,
            "field": "dc:title,dc:creator,prism:coverDate,prism:publicationName,dc:description,prism:doi,authkeywords",
        }
        try:
            r = requests.get(url, headers=headers, params=params, timeout=30)
            data = r.json()
            entries = data.get("search-results", {}).get("entry", [])
            if not entries:
                break
            
            total = int(data.get("search-results", {}).get("opensearch:totalResults", 0))
            if start == 0:
                print(f"  Scopus [{query[:40]}...]: 共 {total} 筆，抓取前 {min(total, max_results)} 筆")
            
            for e in entries:
                year = (e.get("prism:coverDate", "")[:4])
                results.append({
                    "title": e.get("dc:title", ""),
                    "authors": e.get("dc:creator", ""),
                    "year": year,
                    "journal_source": e.get("prism:publicationName", ""),
                    "abstract": e.get("dc:description", "")[:1000],
                    "doi": e.get("prism:doi", ""),
                    "keywords": e.get("authkeywords", ""),
                    "source_db": "Scopus",
                })
            
            fetched += len(entries)
            start += count
            if fetched >= total:
                break
            time.sleep(0.5)
        except Exception as e:
            print(f"  Scopus 失敗: {e}")
            break
    
    return results


# ── Web of Science ─────────────────────────────────────────────────────────────
def search_wos(query, max_results=500):
    results = []
    url = "https://api.clarivate.com/apis/wos-starter/v1/documents"
    headers = {"X-ApiKey": WOS_KEY, "Accept": "application/json"}
    
    page = 1
    limit = 50
    fetched = 0
    
    while fetched < max_results:
        params = {
            "q": f"TS=({query})",
            "db": "WOS",
            "limit": limit,
            "page": page,
            "publishTimeSpan": "2022-01-01+2026-12-31",
        }
        try:
            r = requests.get(url, headers=headers, params=params, timeout=30)
            if r.status_code != 200:
                print(f"  WOS 錯誤 {r.status_code}: {r.text[:200]}")
                break
            data = r.json()
            hits = data.get("hits", [])
            if not hits:
                break
            
            total = data.get("metadata", {}).get("total", 0)
            if page == 1:
                print(f"  WOS [{query[:40]}...]: 共 {total} 筆")
            
            for h in hits:
                names = h.get("names", {})
                authors = "; ".join([a.get("displayName", "") for a in names.get("authors", [])[:5]])
                source = h.get("source", {})
                identifiers = h.get("identifiers", {})
                doi = next((i.get("value", "") for i in identifiers.get("doi", [])), "")
                keywords = "; ".join(h.get("keywords", {}).get("authorKeywords", []))
                results.append({
                    "title": h.get("title", ""),
                    "authors": authors,
                    "year": str(source.get("publishYear", "")),
                    "journal_source": source.get("sourceTitle", ""),
                    "abstract": h.get("abstract", "")[:1000],
                    "doi": doi,
                    "keywords": keywords,
                    "source_db": "WOS",
                })
            
            fetched += len(hits)
            page += 1
            if fetched >= total:
                break
            time.sleep(0.5)
        except Exception as e:
            print(f"  WOS 失敗: {e}")
            break
    
    return results


# ── 主程式 ─────────────────────────────────────────────────────────────────────
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    all_results = []
    seen_titles = set()

    for module, queries in QUERIES.items():
        print(f"\n{'='*50}")
        print(f"模組：{module}")
        print('='*50)
        for q in queries:
            print(f"\n查詢：{q}")
            for fn in [search_pubmed, search_scopus, search_wos]:
                try:
                    res = fn(q, max_results=200)
                    for r in res:
                        title_key = r["title"].lower().strip()
                        if title_key and title_key not in seen_titles:
                            seen_titles.add(title_key)
                            all_results.append(r)
                except Exception as e:
                    print(f"  錯誤: {e}")
            time.sleep(1)

    # 輸出 CSV
    print(f"\n\n總計去重後：{len(all_results)} 筆")
    print(f"寫入：{OUTPUT_FILE}")
    
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(all_results)
    
    print("✅ 完成")


if __name__ == "__main__":
    main()
