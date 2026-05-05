# ReveniQ AI – Step-by-Step Guide: Initial Goal

This guide walks you through achieving the **Initial Goal** only: read CSV, categorize disputes from **full memo text** (up to 80 categories, &lt;5% uncategorised), and run a professional dashboard with top 5 categories, drill-down, and memo text in the Data Table.

---

## Initial Goal (Summary)

| Requirement | How it’s done |
|-------------|----------------|
| Read CSV from local machine | Path: `C:\Users\ashitaa\OneDrive - AMDOCS\Projects\TSA\ReveniQ AI\ReveniQ-AI\ReveniQ-AI` |
| Columns | DISPUTE_ID, STATUS, SYS_CREATION_DATE, AMOUNT (or .AMOUNT), TAX_AMOUNT, CREDIT_LEVEL_CODE, CHARGE_CODE, MEMO_TEXT |
| Categorisation | Based on **full** MEMO_TEXT; broad, wide categorisation |
| Max categories | Up to 80 |
| Uncategorised | Not more than 5% of total disputes |
| Dashboard | Professional, easy to use, attractive, dark text |
| Top 5 categories | Shown one after another; need instant handling |
| Categorisation display | Drill-down structure |
| Data Table tab | Shows memo text along with other details |

---

## Step 1: Prerequisites

1. **Python 3.10+**  
   ```powershell
   python --version
   ```

2. **CSV file** in the project folder with columns:  
   `DISPUTE_ID`, `STATUS`, `SYS_CREATION_DATE`, `AMOUNT` or `.AMOUNT`, `TAX_AMOUNT`, `CREDIT_LEVEL_CODE`, `CHARGE_CODE`, `MEMO_TEXT`.

3. **Project path**  
   ```powershell
   cd "C:\Users\ashitaa\OneDrive - AMDOCS\Projects\TSA\ReveniQ AI\ReveniQ-AI\ReveniQ-AI"
   ```

---

## Step 2: Environment Setup

1. Create and activate a virtual environment (recommended):
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
   If you see an execution policy error:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
   This installs: `pandas`, `streamlit`, `plotly`, and (if present) `openpyxl`.

---

## Step 3: How Categorisation Works (Full Memo Text)

- The loader reads the CSV and keeps **full** `MEMO_TEXT` (no truncation).
- Each row’s **entire** memo text is passed to the categorisation logic in `reveniq_ai/categories.py`.
- Keywords are matched against the full text (case-insensitive); the best-matching category and a confidence score are assigned.
- **Target:** ≤80 categories and &lt;5% of rows left as “Uncategorised”.

**Relevant files:**
- `reveniq_ai/data_loader.py` – reads CSV, normalises columns (e.g. `.AMOUNT` → `AMOUNT`), runs categorisation on full `MEMO_TEXT`.
- `reveniq_ai/categories.py` – category rules and keyword logic.

---

## Step 4: Ensure ≤80 Categories and &lt;5% Uncategorised

1. Open `reveniq_ai/categories.py`.
2. Count categories in `CATEGORY_RULES`. If there are more than 80, merge or remove categories until you have ≤80 (e.g. combine similar billing/payment/device categories).
3. Keep keyword coverage broad so that uncategorised stays &lt;5%. Add or broaden keywords for patterns that currently fall into “Uncategorised”.

---

## Step 5: Run the Dashboard

1. From the project directory (with venv active if you use it):
   ```powershell
   streamlit run dashboard.py
   ```
2. Or use the script:
   ```powershell
   .\run_dashboard.ps1
   ```
3. Open the URL shown (e.g. `http://localhost:8501`).

---

## Step 6: Load Data in the Dashboard

1. In the sidebar, set **CSV folder** and **CSV filename** if different from default.
2. Click **“Load & Categorise”**.
3. The app reads the CSV from the local path, runs categorisation on **full memo text**, and shows KPIs (total disputes, categories, amounts, uncategorised %, average amount).

---

## Step 7: Verify Initial Goal Features

Use this checklist:

- **KPIs (top row)**  
  Total Disputes, Categories, Total Amount (R), Uncategorised (&lt;5%), Avg Amount.

- **Top 5 categories**  
  Shown one after another (e.g. in a row of 5 cards); these are the ones needing instant handling (priority by count + amount).

- **Overview tab**  
  Charts for category distribution, status, and amount.

- **Drill-Down Analysis tab**  
  Expandable sections per category (count, amount, status breakdown, amount distribution, sample rows).

- **Data Table tab**  
  Disputes table **includes memo text** (MEMO_TEXT) along with DISPUTE_ID, STATUS, SYS_CREATION_DATE, AMOUNT, TAX_AMOUNT, CATEGORY, CONFIDENCE_SCORE, CHARGE_CODE.

- **Dark theme**  
  Dark background, light/dark text as designed; professional look.

- **Filters**  
  Category, Status, and search in memo text apply across the dashboard.

---

## Step 8: If Uncategorised &gt; 5%

1. In the dashboard, filter by category **“Uncategorised”**.
2. In the Data Table tab, review **MEMO_TEXT** for common phrases.
3. In `reveniq_ai/categories.py`, add new keywords to the right categories (or add a new category if needed, keeping total ≤80).
4. Reload data in the dashboard and recheck the uncategorised %.

---

## Step 9: Optional – Export Uncategorised to Excel

To get an Excel of all uncategorised disputes with memo text:

1. Install Excel support:
   ```powershell
   pip install openpyxl
   ```
2. Run:
   ```powershell
   python export_uncategorised.py
   ```
3. Open `uncategorised_disputes.xlsx` in the project folder (same path as the CSV).

---

## Success Criteria (Initial Goal)

- CSV loads from the given path; columns include DISPUTE_ID, STATUS, SYS_CREATION_DATE, AMOUNT, TAX_AMOUNT, CREDIT_LEVEL_CODE, CHARGE_CODE, MEMO_TEXT.
- Categorisation uses **full** memo text; categories ≤80; uncategorised &lt;5%.
- Dashboard is professional, attractive, with dark theme and clear text.
- Top 5 categories are shown one after another; drill-down by category works.
- Data Table tab shows memo text with other details.
- Filters (category, status, memo search) work across the app.

---

## End Goal (Reference – Not Implemented in Initial Goal)

For later phases, ReveniQ AI is intended to be an **agentic, end-to-end disputing intelligence** solution that:

- **Title:** TSA – AI powered Dispute resolution & system improvement  
- **Subtitle:** Leverage AI to automate dispute handling, enhance resolution consistency, and uncover systemic issues—reducing operational costs and improving customer satisfaction.

**Planned sections:**

1. **Problem Statement** (e.g. red/orange box, left): manual effort, long resolution cycle, revenue loss, fraud risk, lack of visibility into systemic issues.
2. **The Idea: AI-Powered Dispute Resolution** (e.g. red/orange box, centre): automate categorisation (e.g. from ar1_memo), predict actions, discover root causes, human-in-the-loop.
3. **Business Value** (e.g. red/orange box, right): revenue saving, 50%+ triage time reduction, standardized resolutions, early detection of systemic issues, feedback-driven retraining.
4. **Workflow Timeline** (e.g. bottom row): Categorise → Identify patterns → Investigate via billing data → Generate patterns → Suggestive actions → Query/scan for similar issues → Report frauds/discrepancies.
5. **Branding:** Amdocs – make it amazing (e.g. bottom-right).

**Capabilities (for later):** Triage open disputes, investigate, recommend safe & explainable actions, flag fraud/duplicates, identify and quantify system issues, notify support of revenue issues.

---

## Quick Reference

| What | Where |
|------|--------|
| CSV path / filename | `reveniq_ai/data_loader.py` (`DEFAULT_CSV_DIR`, `CSV_FILENAME`) |
| Category rules (≤80) | `reveniq_ai/categories.py` (`CATEGORY_RULES`) |
| Full-memo categorisation | `reveniq_ai/data_loader.py` (no truncation); `reveniq_ai/categories.py` (`categorize_memo`) |
| Dashboard UI, Top 5, drill-down, Data Table with memo | `dashboard.py` |
| Export uncategorised to Excel | `export_uncategorised.py` |

---

**ReveniQ AI – Initial Goal · Digital COE Gen AI Team · Amdocs – make it amazing**
