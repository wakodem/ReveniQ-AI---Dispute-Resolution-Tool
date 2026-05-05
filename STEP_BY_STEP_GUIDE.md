# ReveniQ AI - Step-by-Step Implementation Guide

## Initial Goal Implementation Guide

This guide will help you implement the initial goal of ReveniQ AI: **Read CSV from local machine, categorize disputes based on memo text, and create a professional dashboard with dark theme.**

---

## 📋 Prerequisites

1. **Python 3.10 or higher** installed on your system
2. **CSV file** located at: `C:\Users\ashitaa\OneDrive - AMDOCS\Projects\TSA\ReveniQ AI\ReveniQ-AI\ReveniQ-AI\dispute_categorisation_60days.csv`
3. **Required columns in CSV:**
   - `DISPUTE_ID`
   - `STATUS`
   - `SYS_CREATION_DATE`
   - `AMOUNT`
   - `TAX_AMOUNT`
   - `CREDIT_LEVEL_CODE`
   - `CHARGE_CODE`
   - `MEMO_TEXT`

---

## 🚀 Step-by-Step Implementation

### Step 1: Verify Your Environment

1. Open PowerShell or Command Prompt
2. Navigate to your project directory:
   ```powershell
   cd "C:\Users\ashitaa\OneDrive - AMDOCS\Projects\TSA\ReveniQ AI\ReveniQ-AI\ReveniQ-AI"
   ```
3. Verify Python installation:
   ```powershell
   python --version
   ```
   Should show Python 3.10 or higher.

---

### Step 2: Set Up Virtual Environment (Recommended)

1. Create a virtual environment:
   ```powershell
   python -m venv .venv
   ```

2. Activate the virtual environment:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   If you get an execution policy error, run:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```
   Then try activating again.

3. You should see `(.venv)` in your prompt, indicating the virtual environment is active.

---

### Step 3: Install Dependencies

1. Install required packages:
   ```powershell
   pip install -r requirements.txt
   ```

2. This will install:
   - `pandas` (for data manipulation)
   - `streamlit` (for the dashboard)
   - `plotly` (for interactive charts)

3. Verify installation:
   ```powershell
   pip list
   ```
   You should see pandas, streamlit, and plotly in the list.

---

### Step 4: Verify CSV File Location

1. Check that your CSV file exists at:
   ```
   C:\Users\ashitaa\OneDrive - AMDOCS\Projects\TSA\ReveniQ AI\ReveniQ-AI\ReveniQ-AI\dispute_categorisation_60days.csv
   ```

2. The file path is already configured in `reveniq_ai/data_loader.py` as:
   ```python
   DEFAULT_CSV_DIR = Path(r"C:\Users\ashitaa\OneDrive - AMDOCS\Projects\TSA\ReveniQ AI\ReveniQ-AI\ReveniQ-AI")
   CSV_FILENAME = "dispute_categorisation_60days.csv"
   ```

---

### Step 5: Test Categorization (Optional)

Before running the dashboard, you can test if the categorization works:

```powershell
python -c "from reveniq_ai.data_loader import load_and_categorise; df = load_and_categorise(); print(f'Total disputes: {len(df)}'); print(f'Categories: {df[\"CATEGORY\"].nunique()}'); print(f'Uncategorised: {(df[\"CATEGORY\"] == \"Uncategorised\").sum()} ({(df[\"CATEGORY\"] == \"Uncategorised\").sum()/len(df)*100:.2f}%)'); print(df['CATEGORY'].value_counts().head(10))"
```

This will show:
- Total number of disputes
- Number of unique categories
- Number and percentage of uncategorised disputes (should be <5%)
- Top 10 categories

---

### Step 6: Run the Dashboard

1. Make sure you're in the project directory and virtual environment is activated
2. Run the Streamlit dashboard:
   ```powershell
   streamlit run dashboard.py
   ```

3. The dashboard will:
   - Automatically open in your default web browser
   - Show the URL (typically `http://localhost:8501`)
   - Load and categorize the CSV data

4. If the browser doesn't open automatically, copy the URL from the terminal and paste it in your browser.

---

### Step 7: Using the Dashboard

#### Dashboard Features:

1. **Top Section - KPIs:**
   - Total Disputes (filtered)
   - Number of Categories
   - Total Amount (R)
   - Uncategorised count and percentage (target: <5%)
   - Average Amount

2. **Top 5 Categories Section:**
   - Shows the 5 categories that need instant handling
   - Based on priority score (combination of count and amount)
   - Each card shows dispute count and total amount

3. **Tabs:**

   **📊 Overview Tab:**
   - Interactive bar chart: Disputes by Category
   - Pie chart: Disputes by Status
   - Bar chart: Total Amount by Category

   **🔍 Drill-Down Analysis Tab:**
   - **By Category:** Select a category to see detailed breakdown
     - Status distribution
     - Amount distribution histogram
     - Sample disputes
   - **By Status:** Select a status to see category breakdown
   - **By Top Categories:** Detailed analysis of top 5 categories

   **📄 Data Table Tab:**
   - Filterable data table
   - Option to include memo text snippets
   - Configurable row limit

4. **Sidebar Filters:**
   - Category filter
   - Status filter
   - Search in memo text
   - All filters apply to all views simultaneously

---

### Step 8: Understanding Categorization

The categorization is based on keyword matching in the `MEMO_TEXT` column. Categories include:

- **Refund request**
- **Payment allocation / POP**
- **Payment extension**
- **Credit limit increase**
- **Account suspension / lift suspension**
- **Cancellation or 30-day notice**
- **Incorrect device / device return**
- **Duplicate or incorrect billing**
- **Events Billing**
- **Rejection fee dispute**
- **Late payment / interest dispute**
- **Device obligation / insurance dispute**
- **Failed debit / bank charge dispute**
- **General credit request**
- **Paid-up / delisting letter**
- **Fraud or identity dispute**
- **Re-logged / referral**
- **FA / account update request**
- **Service activation / deactivation**
- **Account balance / statement query**
- **Billing period / date dispute**
- **Service upgrade / downgrade**
- **Customer service / complaint**
- **Payment method / banking update**
- **Uncategorised** (for disputes that don't match any pattern)

To modify categories, edit `reveniq_ai/categories.py` and add/remove keyword patterns in the `CATEGORY_RULES` list.

---

### Step 9: Troubleshooting

#### Issue: CSV file not found
- **Solution:** Check the file path in `reveniq_ai/data_loader.py`
- Or use the sidebar in the dashboard to specify the correct path

#### Issue: Encoding errors when reading CSV
- **Solution:** The code automatically tries multiple encodings (UTF-8, CP1252, Latin-1, ISO-8859-1)
- If issues persist, check the CSV file encoding

#### Issue: Uncategorised disputes > 5%
- **Solution:** Review uncategorised disputes in the dashboard
- Add new keyword patterns to `reveniq_ai/categories.py` based on common patterns in uncategorised memos

#### Issue: Dashboard not loading
- **Solution:** 
  1. Check if Streamlit is installed: `pip show streamlit`
  2. Check for errors in the terminal
  3. Try clearing browser cache
  4. Restart the Streamlit server

#### Issue: Charts not displaying
- **Solution:**
  1. Ensure plotly is installed: `pip show plotly`
  2. Check browser console for JavaScript errors
  3. Try a different browser

---

### Step 10: Customization

#### Change CSV Path:
Edit `reveniq_ai/data_loader.py`:
```python
DEFAULT_CSV_DIR = Path(r"YOUR_PATH_HERE")
CSV_FILENAME = "your_file.csv"
```

#### Add/Modify Categories:
Edit `reveniq_ai/categories.py`:
```python
CATEGORY_RULES = [
    ("Your Category Name", [
        "keyword1", "keyword2", "keyword3",
    ]),
    # ... more categories
]
```

#### Customize Dashboard Colors:
Edit the CSS in `dashboard.py` (look for the `st.markdown("""<style>...`) section)

---

## ✅ Success Criteria

Your implementation is successful when:

1. ✅ CSV file loads without errors
2. ✅ All disputes are categorized (uncategorised < 5%)
3. ✅ Dashboard displays with dark theme
4. ✅ All KPIs show correct values
5. ✅ Top 5 categories section displays
6. ✅ Drill-down functionality works for categories and statuses
7. ✅ Charts are interactive and display correctly
8. ✅ Filters work across all views

---

## 📊 Expected Results

After successful implementation, you should see:

- **Dashboard with dark theme** (dark blue gradient background, light text)
- **Top 5 categories** prominently displayed with red/orange cards
- **Interactive charts** using Plotly
- **Drill-down capability** to analyze specific categories or statuses
- **Uncategorised disputes < 5%** of total (shown in KPI section)

---

## 🔄 Next Steps (End Goal - Future Implementation)

Once the initial goal is achieved, you can proceed with the end goal features:

1. **Triage disputes** on open disputes
2. **Investigate disputes** using AI
3. **Recommend actions** with explainability
4. **Flag fraud/duplicates**
5. **Identify system issues** and quantify them
6. **Notify support team** about potential revenue issues

---

## 📝 Notes

- The dashboard uses caching to improve performance (data is cached for 5 minutes)
- All text uses dark colors as per requirements
- The design is professional and modern with gradient backgrounds
- Drill-down structure allows deep analysis of categorization
- Top 5 categories are calculated using a priority score (60% count, 40% amount)

---

## 🆘 Support

If you encounter any issues:

1. Check the terminal/console for error messages
2. Verify all dependencies are installed correctly
3. Ensure the CSV file path is correct
4. Review the categorization rules if uncategorised % is too high
5. Check Streamlit and Plotly documentation for advanced customization

---

**Created by:** Digital COE Gen AI Team  
**Project:** ReveniQ AI  
**Version:** Initial Goal Implementation

