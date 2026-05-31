from flask import Flask, request, jsonify, render_template_string
import chromadb
from sentence_transformers import SentenceTransformer
import ollama

app = Flask(__name__)

print("⏳ 載入資料庫...")
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("drugs")
model = SentenceTransformer('all-MiniLM-L6-v2')
print(f"✅ 資料庫載入完成，共 {collection.count()} 筆")

SOURCE_BADGE = {
    'FDA Label': 'badge-fda',
    'RxNorm': 'badge-rxnorm',
    'FDA Adverse Events': 'badge-adverse',
    'PubMed': 'badge-pubmed',
    'FDA Safety': 'badge-safety',
    'FDA Approved Drugs': 'badge-approved',
    'WHO Essential Medicines': 'badge-who'
}

HTML = '''
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>地端用藥建議系統</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, sans-serif; background: #f0f4f8; min-height: 100vh; padding: 24px 16px; }
        h1 { font-size: 22px; color: #1a202c; margin-bottom: 4px; text-align: center; }
        .subtitle { color: #718096; font-size: 13px; text-align: center; margin-bottom: 24px; }
        .input-area { background: white; border-radius: 16px; padding: 24px; max-width: 900px; margin: 0 auto 24px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }
        textarea { width: 100%; padding: 14px; border: 2px solid #e2e8f0; border-radius: 10px; font-size: 15px; resize: none; height: 90px; outline: none; transition: border 0.2s; font-family: inherit; }
        textarea:focus { border-color: #4299e1; }
        button { width: 100%; padding: 13px; background: #4299e1; color: white; border: none; border-radius: 10px; font-size: 15px; cursor: pointer; margin-top: 10px; transition: background 0.2s; }
        button:hover { background: #3182ce; }
        button:disabled { background: #a0aec0; cursor: not-allowed; }
        .loading { text-align: center; color: #718096; margin-top: 12px; display: none; font-size: 14px; }
        .results { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; max-width: 1400px; margin: 0 auto; }
        .card { background: white; border-radius: 14px; padding: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); display: none; }
        .card-header { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; padding-bottom: 12px; border-bottom: 2px solid #e2e8f0; }
        .model-badge { padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; color: white; }
        .badge-llama { background: #4299e1; }
        .badge-qwen { background: #48bb78; }
        .badge-gemma { background: #9f7aea; }
        .rag-tag { font-size: 11px; padding: 2px 8px; border-radius: 8px; background: #ebf8ff; color: #2b6cb0; border: 1px solid #bee3f8; }
        .no-rag-tag { font-size: 11px; padding: 2px 8px; border-radius: 8px; background: #fff5f5; color: #c53030; border: 1px solid #fed7d7; }
        .answer { color: #2d3748; line-height: 1.8; white-space: pre-wrap; font-size: 14px; margin-bottom: 14px; }
        .sources { padding: 10px; background: #f7fafc; border-radius: 8px; }
        .sources h4 { font-size: 12px; color: #4a5568; margin-bottom: 8px; }
        .source-item { display: flex; align-items: center; padding: 4px 0; font-size: 12px; color: #4a5568; border-bottom: 1px solid #e2e8f0; }
        .source-item:last-child { border-bottom: none; }
        .src-badge { display: inline-block; font-size: 10px; padding: 1px 6px; border-radius: 6px; margin-right: 6px; color: white; white-space: nowrap; }
        .badge-fda { background: #4299e1; }
        .badge-rxnorm { background: #48bb78; }
        .badge-adverse { background: #ed8936; }
        .badge-pubmed { background: #9f7aea; }
        .badge-safety { background: #f56565; }
        .badge-approved { background: #38b2ac; }
        .badge-who { background: #667eea; }
        .disclaimer { text-align: center; font-size: 12px; color: #a0aec0; margin-top: 20px; }
        .quick-btns { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
        .quick-btn { padding: 6px 12px; background: #ebf8ff; border: 1px solid #bee3f8; border-radius: 20px; font-size: 12px; color: #2b6cb0; cursor: pointer; transition: all 0.2s; }
        .quick-btn:hover { background: #bee3f8; }
        @media (max-width: 768px) { .results { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <h1>💊 地端用藥建議系統</h1>
    <p class="subtitle">LLaMA 3 · Qwen3:8b · Gemma3:27b · RAG 檢索增強生成 · 68,674 筆藥品資料</p>

    <div class="input-area">
        <textarea id="question" placeholder="請輸入症狀或問題，例如：Ibuprofen 400mg TID for a patient with CKD eGFR 42, is this safe?"></textarea>
        <div class="quick-btns">
            <span class="quick-btn" onclick="setQ('我有高血壓，適合吃什麼藥？有什麼副作用？')">高血壓用藥</span>
            <span class="quick-btn" onclick="setQ('Ibuprofen 400mg TID for a patient with CKD eGFR 42, is this safe?')">CKD用藥安全</span>
            <span class="quick-btn" onclick="setQ('Can Metformin and Ibuprofen be used together in diabetic patients?')">藥物交互作用</span>
            <span class="quick-btn" onclick="setQ('我頭痛可以吃什麼藥？有什麼注意事項？')">頭痛用藥</span>
            <span class="quick-btn" onclick="setQ('What are alternatives to NSAIDs for pain in CKD patients?')">CKD止痛替代</span>
        </div>
        <button id="btn" onclick="ask()">查詢用藥建議（四模型並排比較）</button>
        <div class="loading" id="loading">⏳ 四個模型同時查詢中，請稍候...</div>
    </div>

    <div class="results">
        <div class="card" id="card0">
            <div class="card-header">
                <span class="model-badge badge-llama">LLaMA 3</span>
                <span class="rag-tag">✓ 有 RAG</span>
            </div>
            <div class="answer" id="ans0"></div>
            <div class="sources"><h4>📚 參考來源</h4><div id="src0"></div></div>
        </div>
        <div class="card" id="card1">
            <div class="card-header">
                <span class="model-badge badge-llama">LLaMA 3</span>
                <span class="no-rag-tag">✗ 無 RAG</span>
            </div>
            <div class="answer" id="ans1"></div>
            <div class="sources" id="srcbox1" style="display:none"><h4>📚 參考來源</h4><div id="src1"></div></div>
        </div>
        <div class="card" id="card2">
            <div class="card-header">
                <span class="model-badge badge-qwen">Qwen3:8b</span>
                <span class="rag-tag">✓ 有 RAG</span>
            </div>
            <div class="answer" id="ans2"></div>
            <div class="sources"><h4>📚 參考來源</h4><div id="src2"></div></div>
        </div>
        <div class="card" id="card3">
            <div class="card-header">
                <span class="model-badge badge-gemma">Gemma3:27b</span>
                <span class="rag-tag">✓ 有 RAG</span>
            </div>
            <div class="answer" id="ans3"></div>
            <div class="sources"><h4>📚 參考來源</h4><div id="src3"></div></div>
        </div>
    </div>
    <p class="disclaimer">⚠️ 本系統僅供參考，請諮詢醫師或藥師後再用藥</p>

    <script>
        function setQ(q) { document.getElementById('question').value = q; }

        async function ask() {
            const q = document.getElementById('question').value.trim();
            if (!q) return;
            document.getElementById('btn').disabled = true;
            document.getElementById('loading').style.display = 'block';
            for (let i = 0; i < 4; i++) {
                document.getElementById('card' + i).style.display = 'none';
                document.getElementById('ans' + i).textContent = '';
            }

            const res = await fetch('/ask', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({question: q})
            });
            const data = await res.json();

            for (let i = 0; i < 4; i++) {
                document.getElementById('ans' + i).textContent = data.results[i].answer;
                document.getElementById('card' + i).style.display = 'block';
                if (data.results[i].sources) {
                    const html = data.results[i].sources.map(s =>
                        `<div class="source-item"><span class="src-badge ${s.badge}">${s.source}</span></div>`
                    ).join('');
                    document.getElementById('src' + i).innerHTML = html;
                }
                if (i === 1) document.getElementById('srcbox1').style.display = 'none';
            }

            document.getElementById('loading').style.display = 'none';
            document.getElementById('btn').disabled = false;
        }
    </script>
</body>
</html>
'''

def get_context_and_sources(question_en):
    q_embedding = model.encode([question_en]).tolist()
    all_sources = ['FDA Label', 'PubMed', 'FDA Safety', 'FDA Approved Drugs', 'WHO Essential Medicines']
    context_parts = []
    sources = []
    seen = set()

    results = collection.query(query_embeddings=q_embedding, n_results=5)
    for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
        context_parts.append(doc)
        sources.append({'source': meta['source'], 'badge': SOURCE_BADGE.get(meta['source'], 'badge-fda')})
        seen.add(meta['source'])

    for source in all_sources:
        if source not in seen:
            r = collection.query(query_embeddings=q_embedding, n_results=1, where={'source': source})
            if r['documents'][0]:
                context_parts.append(r['documents'][0][0])
                meta = r['metadatas'][0][0]
                sources.append({'source': meta['source'], 'badge': SOURCE_BADGE.get(meta['source'], 'badge-fda')})

    return "\n---\n".join(context_parts[:8]), sources

def translate_query(question_zh):
    translated = ollama.chat(model='llama3', messages=[{
        'role': 'user',
        'content': f"Translate this medical question to English keywords only (5 words max): {question_zh}"
    }])
    return translated['message']['content']

def ask_with_rag(model_name, question_zh, context):
    prompt = f"""你是一個用藥建議助理。根據以下英文藥品資料回答問題，請用繁體中文回答。

藥品資料：
{context}

問題：{question_zh}

請說明可以用什麼藥、用法用量、以及注意事項。最後加一行免責聲明：本系統僅供參考，請諮詢醫師或藥師。"""
    response = ollama.chat(model=model_name, messages=[{'role': 'user', 'content': prompt}])
    return response['message']['content']

def ask_without_rag(question_zh):
    prompt = f"""你是一個用藥建議助理，請用繁體中文回答以下問題。

問題：{question_zh}

請說明可以用什麼藥、用法用量、以及注意事項。最後加一行免責聲明：本系統僅供參考，請諮詢醫師或藥師。"""
    response = ollama.chat(model='llama3', messages=[{'role': 'user', 'content': prompt}])
    return response['message']['content']

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/ask', methods=['POST'])
def ask():
    question_zh = request.json['question']
    question_en = translate_query(question_zh)
    context, sources = get_context_and_sources(question_en)

    results = [
        {'answer': ask_with_rag('llama3', question_zh, context), 'sources': sources},
        {'answer': ask_without_rag(question_zh), 'sources': None},
        {'answer': ask_with_rag('qwen3:8b', question_zh, context), 'sources': sources},
        {'answer': ask_with_rag('gemma3:27b', question_zh, context), 'sources': sources},
    ]
    return jsonify({'results': results})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)
