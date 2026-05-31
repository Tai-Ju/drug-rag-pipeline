# 💊 地端用藥建議系統

基於本地大型語言模型（LLM）與檢索增強生成（RAG）的用藥建議系統，全程離線運行，無需雲端 API。

 
🌐 **Portfolio 網站：[https://tai-ju.github.io/drug-rag-pipeline/](https://tai-ju.github.io/drug-rag-pipeline/)**
⚡ **互動 Demo：[https://tai-ju.github.io/drug-rag-pipeline/demo.html](https://tai-ju.github.io/drug-rag-pipeline/demo.html)**

---

## 系統架構

```
使用者問題
    ↓
翻譯為英文關鍵字（LLaMA 3）
    ↓
向量檢索（ChromaDB + SentenceTransformer）
    ↓
注入 Prompt → 三模型並行推論
    ↓
四欄並排顯示（含 RAG vs 無 RAG 對照）
```

**資料來源（68,674 筆）**

| 來源 | 說明 |
|------|------|
| FDA Label | 藥品仿單 |
| FDA Adverse Events | 不良事件通報 |
| FDA Safety | 安全警示 |
| FDA Approved Drugs | 核准藥品清單 |
| PubMed | 醫學文獻摘要 |
| RxNorm | 藥品標準化名稱 |
| WHO Essential Medicines | 世界衛生組織基本藥物清單 |

---

## 使用模型

| 模型 | 用途 |
|------|------|
| `llama3` | 查詢翻譯 + RAG 推論 + 無 RAG 對照 |
| `qwen3:8b` | RAG 推論 |
| `gemma3:27b` | RAG 推論 |

---

## 安裝與執行

### 1. 安裝依賴

```bash
pip install flask chromadb sentence-transformers ollama
```

### 2. 安裝 Ollama 並拉取模型

```bash
# 安裝 Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 拉取三個模型
ollama pull llama3
ollama pull qwen3:8b
ollama pull gemma3:27b
```

### 3. 建立向量資料庫

```bash
# 抓取原始資料
python fetch_all_fda.py
python fetch_pubmed.py
python fetch_rxnorm.py
python fetch_guidelines2.py

# 建立 ChromaDB
python build_db_final.py
```

### 4. 啟動系統

```bash
python app.py
```

瀏覽器開啟 `http://localhost:8000`

---

## 功能展示

- 支援中英文混合問題輸入
- 四欄並排比較：LLaMA3+RAG / LLaMA3 無 RAG / Qwen3 / Gemma3
- 每個回答附參考來源標籤
- 快捷問題按鈕（高血壓、CKD、藥物交互作用等）

---

## 專案結構

```
drug_rag/
├── app.py                  # Flask 主程式 + 前端 UI
├── build_db_final.py       # 建立 ChromaDB 向量資料庫
├── search.py               # 向量搜尋測試工具
├── fetch_all_fda.py        # 抓取 FDA 完整資料
├── fetch_adverse.py        # FDA 不良事件
├── fetch_fda_safety2.py    # FDA 安全警示
├── fetch_pubmed.py         # PubMed 文獻（批次 1）
├── fetch_pubmed2.py        # PubMed 文獻（批次 2）
├── fetch_pubmed3.py        # PubMed 文獻（批次 3）
├── fetch_pubmed4.py        # PubMed 文獻（批次 4）
├── fetch_rxnorm.py         # RxNorm 藥品名稱
├── fetch_guidelines2.py    # WHO Essential Medicines
├── .gitignore
└── README.md
```

> `chroma_db/` 與所有 `.json` 原始資料不包含在 repo 中，執行 fetch 腳本後自動產生。

---

## 技術棧

- **LLM 推論**：[Ollama](https://ollama.com)
- **向量資料庫**：[ChromaDB](https://www.trychroma.com)
- **嵌入模型**：`all-MiniLM-L6-v2`（SentenceTransformer）
- **後端**：Flask
- **全程離線**：無需 OpenAI / 雲端 API

---

## 注意事項

> ⚠️ 本系統僅供學術研究與教學參考，請勿作為實際醫療診斷依據，用藥前請諮詢醫師或藥師。
