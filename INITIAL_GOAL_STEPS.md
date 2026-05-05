# ReveniQ AI – Step-by-step guide: Initial goal

**Initial goal:** Read CSV from local machine, categorise by memo text, then create a dashboard.

**Creator:** Digital COE Gen AI Team

---

## Step 1 – Environment setup

1. **Python**  
   Ensure Python 3.10+ is installed:
   ```powershell
   python --version
   ```

2. **Open project folder**  
   Use the folder that contains the CSV and the `reveniq_ai` package:
   ```powershell
   cd C:\Users\mangeshw\ReveniQ-AI
   ```

3. **Create virtual environment (recommended)**  
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

4. **Install dependencies**  
   ```powershell
   pip install -r requirements.txt
   ```
   This installs `pandas` and `streamlit`.

---

## Step 2 – CSV and columns

- **Path:** `C:\Users\mangeshw\ReveniQ-AI\dispute_categorisation_60days.csv`
- **Columns used:**  
  `DISPUTE_ID`, `STATUS`, `SYS_CREATION_DATE`, `AMOUNT`, `TAX_AMOUNT`, `CREDIT_LEVEL_CODE`, `CHARGE_CODE`, `MEMO_TEXT`
- Categorisation is done from **MEMO_TEXT** only. The code reads the CSV with quoted fields so multi-line memos are handled correctly.

---

## Step 3 – How categorisation works

- **Module:** `reveniq_ai/categories.py`  
  Defines categories and keyword rules (e.g. “credit limit”, “payment allocation”, “suspension lift”).
- **Module:** `reveniq_ai/data_loader.py`  
  - Loads the CSV from the path above (configurable).  
  - Adds a **CATEGORY** column by applying `categorize_memo()` to each `MEMO_TEXT`.
- **Categories (examples):**  
  Credit limit, Payment allocation, Suspension lift, Cancellation / 30-day notice, Billing dispute / Incorrect charge, Delisting / Paid-up letter, Rejection fee / Contract fee, Fraud / Discrepancy, Uncategorised.

To change or add categories, edit the `CATEGORY_RULES` list in `reveniq_ai/categories.py`.

---

## Step 4 – Run the dashboard

From `C:\Users\mangeshw\ReveniQ-AI`:

```powershell
streamlit run dashboard.py
```

Or use the script:

```powershell
.\run_dashboard.ps1
```

- The app loads the CSV, runs categorisation, and shows:
  - **KPIs:** Total disputes, number of categories, total amount, uncategorised count.
  - **Charts:** Disputes by category, by status, amount by category.
  - **Table:** Filterable by category and status (sample of rows).
- **Sidebar:** You can change “CSV folder” and “CSV filename”, then click **Load & categorise** to refresh.

---

## Step 5 – Optional: run only categorisation (no UI)

To test load + categorisation without the dashboard:

```powershell
cd C:\Users\mangeshw\ReveniQ-AI
python -c "from reveniq_ai.data_loader import load_and_categorise; df = load_and_categorise(); print(df[['DISPUTE_ID','CATEGORY']].head(20))"
```

To save the categorised data to a new CSV:

```python
from reveniq_ai.data_loader import load_and_categorise
df = load_and_categorise()
df.to_csv(r"C:\Users\mangeshw\ReveniQ-AI\disputes_categorised.csv", index=False)
```

---

## Checklist – Initial goal

| Step | Action |
|------|--------|
| 1 | Python 3.10+ and `cd C:\Users\mangeshw\ReveniQ-AI` |
| 2 | `pip install -r requirements.txt` |
| 3 | Ensure `dispute_categorisation_60days.csv` is in that folder |
| 4 | `streamlit run dashboard.py` and open the URL in the browser |
| 5 | Optionally adjust categories in `reveniq_ai/categories.py` and reload |

---

## Next (end goal – not in scope for “initial goal”)

Later phases will add: triage, investigation, recommended actions, fraud/duplicate flagging, system-issue detection, and support notifications. This guide covers only: **read CSV → categorise by memo → dashboard.**
