# 🤖 ReveniQ AI - Dispute Resolution Intelligence

**AI-powered dispute categorization and dashboard for automated dispute handling**

---
   
## 🎯 Initial Goal - Quick Start

### Prerequisites
- Python 3.10+
- A dispute CSV file (see **Configuration** below for path)

### Quick Start (3 Steps)

1. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

2. **Run the dashboard:**
   ```powershell
   streamlit run dashboard.py
   ```
   Or use the PowerShell script:
   ```powershell
   .\run_dashboard.ps1
   ```

3. **Open your browser** - The dashboard will automatically open at `http://localhost:8501`

---

## 📊 Features

✅ **Automatic Categorization** - Categorizes disputes based on memo text  
✅ **Dark Theme Dashboard** - Professional, modern UI with dark colors  
✅ **Top 5 Categories** - Highlights categories needing instant handling  
✅ **Drill-Down Analysis** - Deep dive into categories, statuses, and top issues  
✅ **Interactive Charts** - Plotly-powered visualizations  
✅ **Smart Filtering** - Filter by category, status, or search memo text  
✅ **<5% Uncategorised** - Enhanced categorization rules ensure minimal uncategorised disputes  

---

## 📁 Project Structure

```
ReveniQ-AI/
├── dashboard.py                 # Main Streamlit dashboard
├── requirements.txt             # Python dependencies
├── run_dashboard.ps1           # Quick start script
├── STEP_BY_STEP_GUIDE.md       # Detailed implementation guide
├── dispute_categorisation_60days.csv  # Input CSV file
└── reveniq_ai/
    ├── __init__.py
    ├── data_loader.py          # CSV loading and categorization
    └── categories.py           # Categorization rules
```

---

## 🔧 Configuration

### CSV path (no code changes)

By default the app looks for `dispute_categorisation_60days.csv` in the **project root** (the ReveniQ-AI folder).

To use a different location or filename:

1. **Option A – Environment variables**  
   Set before running:
   - `REVENIQ_CSV_DIR` – directory containing the CSV (e.g. `C:\Users\mangeshw\ReveniQ-AI` or your data folder)
   - `REVENIQ_CSV_FILENAME` – filename (default: `dispute_categorisation_60days.csv`)

2. **Option B – .env file (recommended)**  
   - Copy `.env.example` to `.env` in the project root.
   - Set `REVENIQ_CSV_DIR` and optionally `REVENIQ_CSV_FILENAME` in `.env`.  
   Do not commit `.env` (it is for your machine only).

Example `.env`:
```env
REVENIQ_CSV_DIR=C:\Users\mangeshw\ReveniQ-AI
REVENIQ_CSV_FILENAME=dispute_categorisation_60days.csv
```

### AI resolution & recommended action (Open Dispute Analysis)

The dashboard can suggest a **resolution summary** and **recommended action** per dispute using an LLM.

- **Ollama (recommended, no quota)** – Local, free, no API key or rate limits.

  **Use Ollama in ReveniQ (step-by-step):**
  1. **Start Ollama** – In PowerShell: `ollama run llama3.2` (leave the window open or minimize it).
  2. **Set backend** – In `.env`: `REVENIQ_LLM_BACKEND=ollama` (optional: `OLLAMA_BASE_URL=http://localhost:11434`, `OLLAMA_MODEL=llama3.2`).
  3. **Start dashboard** – `streamlit run dashboard.py`
  4. **In the app** – Open the **Open Dispute Analysis** tab → confirm **"AI backend: Ollama (local)"** → click **Get AI resolution & recommendation**.

  If you see "Ollama not reachable", ensure step 1 is running.

  **Scaling to 50–100 disputes (faster runs):**
  - Use a **faster/smaller model**: `ollama run phi` (or `llama3.2:1b`), then in `.env`: `OLLAMA_MODEL=phi`.
  - Run **more in parallel**: in `.env` set `OLLAMA_PARALLEL_WORKERS=6` (or 8 on a strong machine). Default is 4.
  - In the dashboard choose **Max disputes to send to AI per run** = 50 or 100. Results are cached so you can run in batches (e.g. 50 + 50) and re-run without re-processing.
  - Expect roughly **10–20 minutes for 100 disputes** with `phi` and 6 workers; longer with larger models.

  **RAG (mandatory for AI resolution unless disabled):**
  - RAG injects relevant snippets from your policy/playbook docs into every AI prompt. Set **`REVENIQ_RAG_DISABLED=1`** only for local testing without embeddings.
  - Add `.txt` or `.md` files under **`docs/rag/`** (e.g. dispute resolution policy, rejection fee rules, escalation criteria).
  - Optional: `REVENIQ_RAG_DOCS_DIR=docs/rag`, `OLLAMA_EMBED_MODEL=nomic-embed-text`.
  - Run the embedding model once: `ollama run nomic-embed-text`. Then restart the dashboard. The first run builds the index.
  - **Literal rule SQL:** add a `.sql` file or a fenced `sql` code block in a `.md`/`.txt` doc, starting with `-- REVENIQ_CATEGORY: <exact category name>` and a single `SELECT` using bind `:did`. That query runs against Oracle before any LLM-generated SQL fallback (see `.env.example`).

### Modify categories
Edit `reveniq_ai/categories.py` to add/remove categorization rules.

---

## 📖 Documentation

- **Detailed Guide:** See `STEP_BY_STEP_GUIDE.md` for comprehensive instructions
- **Troubleshooting:** Check the guide for common issues and solutions

---

## 🎨 Dashboard Sections

1. **KPIs** - Total disputes, categories, amounts, uncategorised %
2. **Top 5 Categories** - Priority categories requiring immediate attention
3. **Overview Tab** - Charts showing disputes by category and status
4. **Drill-Down Tab** - Detailed analysis by category, status, or top categories
5. **Data Table Tab** - Filterable table with all dispute details

---

## 🚀 End Goal (Future)

The end goal includes:
- Automated dispute triage
- AI-powered investigation
- Action recommendations with explainability
- Fraud/duplicate detection
- System issue identification
- Support team notifications

---

## 👥 Credits

**Digital COE Gen AI Team**  
**Amdocs – make it amazing**

---

## 📝 License

Internal use - Amdocs Digital COE Gen AI Team

