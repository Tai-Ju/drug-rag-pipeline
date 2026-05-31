import json
import chromadb
from sentence_transformers import SentenceTransformer
from collections import Counter

docs = []
idx = 0

# 1. FDA 藥品仿單
print("載入 FDA 仿單...")
for filename in ['drug_labels.json', 'drug_labels2.json', 'fda_all.json']:
    try:
        with open(filename) as f:
            data = json.load(f)
        for drug in data['results']:
            text = ''
            for field in ['active_ingredient', 'indications_and_usage', 'dosage_and_administration', 'warnings', 'do_not_use']:
                if field in drug:
                    text += f'{field}: {drug[field][0][:500]}\n'
            if text.strip():
                openfda = drug.get('openfda', {})
                name = (openfda.get('brand_name') or openfda.get('generic_name') or openfda.get('substance_name') or openfda.get('manufacturer_name') or ['Unknown'])[0]
                docs.append({'id': str(idx), 'text': text, 'source': 'FDA Label', 'drug_name': name})
                idx += 1
    except FileNotFoundError:
        print(f"找不到 {filename}，跳過")

# 2. RxNorm
print("載入 RxNorm...")
for filename in ['rxnorm.json', 'rxnorm_all.json']:
    try:
        with open(filename) as f:
            data = json.load(f)
        concepts = data.get('concepts', [])
        if not concepts:
            for group in data.get('drugGroup', {}).get('conceptGroup', []):
                concepts.extend(group.get('conceptProperties', []))
        for concept in concepts:
            text = f"drug_name: {concept['name']}\nrxcui: {concept['rxcui']}\n"
            docs.append({'id': str(idx), 'text': text, 'source': 'RxNorm', 'drug_name': concept['name'][:50]})
            idx += 1
    except FileNotFoundError:
        print(f"找不到 {filename}，跳過")

# 3. Adverse Events
print("載入不良反應...")
for filename in ['adverse_events.json', 'adverse_events_all.json']:
    try:
        with open(filename) as f:
            data = json.load(f)
        for event in data['results']:
            patient = event.get('patient', {})
            drugs = patient.get('drug', [])
            reactions = patient.get('reaction', [])
            if not drugs or not reactions:
                continue
            drug_names = ', '.join([d.get('medicinalproduct', '') for d in drugs if d.get('medicinalproduct')])
            reaction_names = ', '.join([r.get('reactionmeddrapt', '') for r in reactions if r.get('reactionmeddrapt')])
            if drug_names and reaction_names:
                text = f"drug_name: {drug_names}\nadverse_reactions: {reaction_names}\nserious: {event.get('serious', 'unknown')}\n"
                docs.append({'id': str(idx), 'text': text, 'source': 'FDA Adverse Events', 'drug_name': drug_names[:50]})
                idx += 1
    except FileNotFoundError:
        print(f"找不到 {filename}，跳過")

# 4. PubMed
print("載入 PubMed...")
with open('pubmed.json') as f:
    data = json.load(f)
for article in data['articles']:
    text = f"title: {article['title']}\njournal: {article['journal']}\ndate: {article['date']}\nauthors: {article['authors']}\nkeyword: {article['keyword']}\n"
    docs.append({'id': str(idx), 'text': text, 'source': 'PubMed', 'drug_name': article['journal'][:50]})
    idx += 1

# 5. FDA Safety
print("載入 FDA Safety...")
with open('fda_safety.json') as f:
    data = json.load(f)
for item in data['results']:
    product = item.get('product_description', '')
    reason = item.get('reason_for_recall', '')
    classification = item.get('classification', '')
    if product and reason:
        text = f"product: {product[:300]}\nreason_for_recall: {reason[:300]}\nclassification: {classification}\n"
        docs.append({'id': str(idx), 'text': text, 'source': 'FDA Safety', 'drug_name': product[:50]})
        idx += 1

# 6. Guidelines
print("載入 Guidelines...")
with open('guidelines.json') as f:
    data = json.load(f)
for item in data['guidelines']:
    docs.append({'id': str(idx), 'text': item['text'], 'source': item['source'], 'drug_name': item['name']})
    idx += 1

# 去重
print("去重中...")
seen = set()
unique_docs = []
for d in docs:
    if d['text'] not in seen:
        seen.add(d['text'])
        unique_docs.append(d)

for i, d in enumerate(unique_docs):
    d['id'] = str(i)

# 建向量資料庫
print("建立向量資料庫...")
client = chromadb.PersistentClient(path="./chroma_db")
try:
    client.delete_collection("drugs")
except:
    pass
collection = client.create_collection("drugs")
model = SentenceTransformer('all-MiniLM-L6-v2')

batch_size = 100
for i in range(0, len(unique_docs), batch_size):
    batch = unique_docs[i:i+batch_size]
    embeddings = model.encode([d['text'] for d in batch]).tolist()
    collection.add(
        documents=[d['text'] for d in batch],
        embeddings=embeddings,
        ids=[d['id'] for d in batch],
        metadatas=[{'source': d['source'], 'drug_name': d['drug_name']} for d in batch]
    )
    if i % 5000 == 0:
        print(f"進度：{min(i+batch_size, len(unique_docs))}/{len(unique_docs)}")

print(f"\n✅ 完成，共 {len(unique_docs)} 筆資料")
counter = Counter(d['source'] for d in unique_docs)
for source, count in counter.items():
    print(f"  {source}: {count} 筆")
