# ReveniQ AI - Initial Goal: Step-by-Step Implementation Guide

## 🎯 Initial Goal Overview

**Objective:** Read CSV, categorize disputes based on memo text (up to 100 categories), and create a professional dashboard.

---

## 📋 Step 1: Environment Setup

### 1.1 Verify Python Installation
```powershell
python --version
```
Should show Python 3.10 or higher.

### 1.2 Navigate to Project Directory
```powershell
cd "C:\Users\ashitaa\OneDrive - AMDOCS\Projects\TSA\ReveniQ AI\ReveniQ-AI\ReveniQ-AI"
```

### 1.3 Create Virtual Environment (Recommended)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If you get execution policy error:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 1.4 Install Dependencies
```powershell
pip install -r requirements.txt
```

Required packages:
- pandas
- streamlit
- plotly

---

## 📋 Step 2: Verify CSV File

### 2.1 Check CSV Location
Ensure your CSV file exists at:
```
C:\Users\ashitaa\OneDrive - AMDOCS\Projects\TSA\ReveniQ AI\ReveniQ-AI\ReveniQ-AI\dispute_categorisation_60days.csv
```

### 2.2 Verify CSV Columns
Your CSV should have these columns:
- DISPUTE_ID
- STATUS
- SYS_CREATION_DATE
- AMOUNT
- TAX_AMOUNT
- CREDIT_LEVEL_CODE
- CHARGE_CODE
- MEMO_TEXT

---

## 📋 Step 3: Understanding the Categorization System

### 3.1 Category Structure
- **Up to 100 categories** for broad and wide categorization
- Categories are based on **memo text** analysis
- **Target: <5% uncategorised** disputes

### 3.2 How It Works
1. System reads MEMO_TEXT from each dispute
2. Matches keywords/patterns to categories
3. Assigns category with confidence score
4. Uncategorised disputes are flagged for review

### 3.3 Category Examples
- Payment Allocation / POP
- Refund Request
- Credit Limit Increase
- Account Suspension / Lift Suspension
- Billing Disputes
- Service Cancellation
- And 90+ more categories...

---

## 📋 Step 4: Run the Dashboard

### 4.1 Start the Dashboard
```powershell
streamlit run dashboard.py
```

Or use the script:
```powershell
.\run_dashboard.ps1
```

### 4.2 Access the Dashboard
- Dashboard opens automatically in your browser
- URL: `http://localhost:8501`
- If not auto-opened, copy the URL from terminal

---

## 📋 Step 5: Using the Dashboard

### 5.1 Load Data
1. Click "🔄 Load & Categorise" button in sidebar
2. Wait for categorization to complete
3. Data loads automatically

### 5.2 Dashboard Features

#### **Top Section - KPIs:**
- Total Disputes
- Total Amount
- Number of Categories
- Uncategorised Count & Percentage

#### **Top 5 Categories Section:**
- Shows categories needing instant handling
- Based on volume + amount priority
- Each card shows dispute count and total amount

#### **Charts & Visualizations:**
- Disputes by Category (bar chart)
- Disputes by Status (pie chart)
- Amount by Category (bar chart)

#### **Drill-Down Structure:**
- Click on any category to see details
- View sub-categories and related disputes
- Filter by status or search memo text

### 5.3 Filters (Sidebar)
- **Category Filter:** Filter by specific category
- **Status Filter:** Filter by dispute status
- **Search:** Search within memo text

---

## 📋 Step 6: Understanding Results

### 6.1 Categorization Quality
- Check "% Uncategorised" KPI
- Should be **<5%** of total disputes
- If higher, review uncategorised disputes

### 6.2 Top 5 Categories
- These categories need **immediate attention**
- Prioritized by:
  - High volume (number of disputes)
  - High amount (total financial impact)

### 6.3 Drill-Down Analysis
- Click any category to see:
  - Sub-categories breakdown
  - Status distribution
  - Sample disputes
  - Amount distribution

---

## 📋 Step 7: Troubleshooting

### Issue: CSV Not Found
**Solution:**
1. Check file path in sidebar
2. Verify CSV filename is correct
3. Ensure file exists at specified location

### Issue: High Uncategorised %
**Solution:**
1. Review uncategorised disputes in dashboard
2. Check memo text patterns
3. Categories can be enhanced (see Step 8)

### Issue: Dashboard Not Loading
**Solution:**
1. Check if Streamlit is installed: `pip show streamlit`
2. Check terminal for error messages
3. Try clearing browser cache
4. Restart Streamlit server

### Issue: Charts Not Displaying
**Solution:**
1. Ensure plotly is installed: `pip show plotly`
2. Check browser console for errors
3. Try different browser

---

## 📋 Step 8: Customizing Categories (Optional)

### 8.1 Add New Categories
Edit `reveniq_ai/categories.py`:
```python
("Your New Category", [
    "keyword1", "keyword2", "keyword3",
]),
```

### 8.2 Modify Existing Categories
- Find category in `categories.py`
- Add/remove keywords as needed
- Save and reload dashboard

### 8.3 Best Practices
- Use specific keywords for better accuracy
- Test with sample data before deploying
- Document new categories for audit

---

## 📋 Step 9: Export Results (Optional)

### 9.1 Export Categorised Data
You can export the categorised data to CSV:
```python
from reveniq_ai.data_loader import load_and_categorise
df = load_and_categorise()
df.to_csv("categorised_disputes.csv", index=False)
```

---

## ✅ Success Checklist

- [ ] Python 3.10+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed
- [ ] CSV file exists at correct location
- [ ] Dashboard runs without errors
- [ ] Data loads successfully
- [ ] Categorization completes
- [ ] Uncategorised % < 5%
- [ ] Top 5 categories display correctly
- [ ] Drill-down structure works
- [ ] Charts display properly
- [ ] Filters work correctly

---

## 🎯 Next Steps (End Goal - Future)

Once initial goal is working, you can proceed with:
- Automated dispute triage
- AI-powered investigation
- Action recommendations
- Fraud/duplicate detection
- System issue identification
- Support team notifications

---

## 📞 Support

For issues:
1. Check this guide's troubleshooting section
2. Review terminal/console error messages
3. Verify all file paths are correct
4. Ensure all dependencies are installed

---

**Created by:** Digital COE Gen AI Team  
**Project:** ReveniQ AI - Initial Goal  
**Version:** 1.0

