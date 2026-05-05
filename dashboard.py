"""
ReveniQ AI – Initial Goal Dashboard
Professional dashboard for dispute categorization and analysis.
Run: streamlit run dashboard.py
Digital COE Gen AI Team
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from reveniq_ai.data_loader import load_and_categorise, DEFAULT_CSV_DIR, CSV_FILENAME

st.set_page_config(
    page_title="ReveniQ AI – Dispute Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Dark Theme CSS with Dark Text Colors ---
st.markdown("""
<style>
    /* Main background - dark theme */
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    }
    
    /* Main container */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1600px;
        background: rgba(26, 26, 46, 0.9);
        border-radius: 15px;
    }
    
    /* Main content + sidebar text (avoid div,span so dropdown option text is not overridden) */
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, .stText, 
    .stSelectbox label, .stTextInput label, .stMetric label, .stMetric .value,
    .stDataFrame, .stDataFrame th, .stDataFrame td,
    .block-container, .stApp [data-testid="stSidebar"] *,
    .stApp .main .block-container * {
        color: #e0e0e0 !important;
    }
    
    /* Dropdown lists: force dark text on light background (all popovers/menus) */
    [data-baseweb="popover"],
    [data-baseweb="popover"] *,
    [data-baseweb="menu"],
    [data-baseweb="menu"] *,
    [data-baseweb="select"] [role="listbox"],
    [data-baseweb="select"] [role="listbox"] *,
    [data-baseweb="popover"] [role="listbox"],
    [data-baseweb="popover"] [role="listbox"] *,
    [role="listbox"],
    [role="listbox"] *,
    [data-baseweb="option"],
    [data-baseweb="option"] * {
        color: #1a1a2e !important;
    }
    [data-baseweb="popover"],
    [data-baseweb="popover"] [role="listbox"],
    [role="listbox"] {
        background-color: #ffffff !important;
    }
    [role="option"]:hover,
    [role="listbox"] [role="option"]:hover,
    [role="listbox"] li:hover,
    [data-baseweb="option"]:hover {
        background-color: #e0e8f0 !important;
        color: #1a1a2e !important;
    }
    /* Selectbox trigger/input: dark text so "All", "J", etc. are readable */
    [data-baseweb="select"] input,
    .stSelectbox input,
    [data-baseweb="select"] > div,
    .stSelectbox > div {
        color: #1a1a2e !important;
        background-color: #ffffff !important;
    }
    
    /* KPI cards */
    .kpi-card {
        background: linear-gradient(135deg, #2d3561 0%, #1e2746 100%);
        border-radius: 12px;
        padding: 1.5rem;
        border-left: 5px solid #00d4ff;
        box-shadow: 0 4px 15px rgba(0, 212, 255, 0.2);
        margin-bottom: 1rem;
        transition: transform 0.3s ease;
    }
    
    .kpi-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 20px rgba(0, 212, 255, 0.3);
    }
    
    .kpi-card .label {
        font-size: 0.85rem;
        color: #a0aec0;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.5rem;
    }
    
    .kpi-card .value {
        font-size: 2rem;
        color: #00d4ff;
        font-weight: 700;
    }
    
    /* Top 5 row: single row, equal width */
    .top5-row {
        display: flex;
        flex-wrap: nowrap;
        gap: 1rem;
        width: 100%;
        margin-bottom: 1rem;
    }
    .top5-row .top-category-card {
        flex: 1 1 0;
        min-width: 0;
    }
    /* Top 5 category cards */
    .top-category-card {
        background: linear-gradient(135deg, #e94560 0%, #c73650 100%);
        border-radius: 10px;
        padding: 1.25rem;
        margin-bottom: 0;
        border-left: 4px solid #ff6b9d;
        box-shadow: 0 4px 12px rgba(233, 69, 96, 0.3);
        transition: transform 0.3s ease;
    }
    
    .top-category-card:hover {
        transform: translateX(5px);
        box-shadow: 0 6px 18px rgba(233, 69, 96, 0.4);
    }
    
    .top-category-card .category-name {
        font-size: 1.1rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 0.5rem;
    }
    
    .top-category-card .category-stats {
        font-size: 0.9rem;
        color: #ffe0e6;
    }
    
    /* Equal-width columns for top 5 cards */
    [data-testid="column"]:has(.top-category-card) {
        min-width: 0;
    }
    
    /* Section headers */
    .section-header {
        font-size: 1.4rem;
        color: #00d4ff;
        margin-bottom: 1rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        border-bottom: 2px solid #00d4ff;
        padding-bottom: 0.5rem;
    }
    
    /* Drill-down cards */
    .drill-down-card {
        background: rgba(45, 53, 97, 0.6);
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #3a4a6b;
        color: #e0e0e0;
    }
    
    .drill-down-card .category-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #00d4ff;
        margin-bottom: 0.75rem;
    }
    
    .drill-down-card .category-info {
        color: #a0aec0;
        font-size: 0.95rem;
    }
    
    /* Footer */
    .reveniq-footer {
        text-align: center;
        color: #a0aec0;
        font-size: 0.9rem;
        margin-top: 3rem;
        padding-top: 1.5rem;
        border-top: 2px solid #2d3561;
    }
    
    /* Tables */
    .dataframe {
        background-color: #1e2746;
        color: #e0e0e0;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%);
        color: #ffffff;
        border: none;
        border-radius: 8px;
        font-weight: 600;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #1a1a2e;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=600)
def get_categorised_data(csv_dir_str: str, csv_filename: str):
    """Load and categorise CSV. Cached 10 min so reload is fast."""
    return load_and_categorise(csv_dir=csv_dir_str, filename=csv_filename)


def calculate_top_categories_by_status(df: pd.DataFrame, status: str) -> pd.DataFrame:
    """Top 5 categories by revenue (AMOUNT sum) for the given status."""
    if not status or df.empty:
        return pd.DataFrame(columns=["Category", "Count", "Total_Amount"])
    df_status = df[df["STATUS"].str.strip() == status]
    if df_status.empty:
        return pd.DataFrame(columns=["Category", "Count", "Total_Amount"])
    category_stats = df_status.groupby("CATEGORY").agg({
        "DISPUTE_ID": "count",
        "AMOUNT": "sum",
    }).reset_index()
    category_stats.columns = ["Category", "Count", "Total_Amount"]
    return category_stats.nlargest(5, "Total_Amount")


def status_label(status: str) -> str:
    """Return user-friendly status label from status code."""
    status_map = {
        "R": "Rejected",
        "J": "Justified",
        "O": "Open",
    }
    cleaned = str(status).strip()
    return status_map.get(cleaned, cleaned)


def apply_filters(df: pd.DataFrame, category: str, status: str, search: str) -> pd.DataFrame:
    """Apply sidebar filters to dataframe."""
    out = df.copy()
    if category and category != "All":
        out = out[out["CATEGORY"] == category]
    if status and status != "All":
        out = out[out["STATUS"].str.strip() == status]
    if search and search.strip():
        mask = out["MEMO_TEXT"].fillna("").str.lower().str.contains(search.lower(), regex=False)
        out = out[mask]
    return out


def get_suggested_resolution(category: str) -> str:
    """Return suggested resolution text for a dispute category."""
    resolutions = {
        "Payment Allocation / POP": "Verify proof of payment; allocate to correct FA/account; update billing system.",
        "Payment Extension Request": "Assess payment history; approve or decline extension with new due date; document reason.",
        "Failed Debit / Bank Charge": "Confirm bank rejection reason; request updated banking details; retry or waive fee if bank error.",
        "Rejection Fee Dispute": "Review debit date and rejection reason; waive or reduce fee if justified; update customer if fee upheld.",
        "Refund Request": "Verify overpayment or eligibility; process refund to provided banking details; close dispute with confirmation.",
        "Credit Limit Increase": "Check credit assessment and account conduct; approve increase within policy or decline with reason.",
        "Account Suspension / Lift Suspension": "Confirm payment received or arrangement; lift suspension and notify customer.",
        "Duplicate or Incorrect Billing": "Verify duplicate/error; credit or adjust invoice; ensure no double charge.",
        "Late Payment / Interest Dispute": "Check payment dates and terms; waive or reduce interest/fees if policy allows; document decision.",
        "Cancellation or 30-Day Notice": "Confirm cancellation request and date; stop billing after notice period; send final invoice.",
        "Discount / Settlement Offer (EDC)": "Apply approved discount/settlement; update balance; confirm in system and with customer.",
        "Bad Debt / Final Account Clearance": "Apply write-off or clearance per policy; update account status; close dispute.",
        "Prescribed Debt / Prescription Claim": "Verify prescription eligibility and dates; write off if prescribed; update account.",
        "Penalty / Clawback": "Review contract and penalty clause; waive or uphold; document and notify.",
        "Fraud or Identity Dispute": "Escalate to fraud team; verify identity and documents; block if confirmed fraud.",
        "General Dispute / Other": "Review memo and account; apply standard resolution or escalate; document outcome.",
    }
    for key, resolution in resolutions.items():
        if key in category or category in key:
            return resolution
    return "Review dispute details and account history; apply standard resolution or escalate; document outcome."


def get_defect_analysis(memo: str, category: str) -> str:
    """Derive defect analysis from memo text (keyword-based logic)."""
    if not memo or not str(memo).strip():
        return "No memo text provided."
    text = str(memo).lower().strip()[:500]
    # Keyword-based defect analysis
    if "refund" in text or "return" in text:
        return "Customer requesting refund or return of funds."
    if "payment not reflected" in text or "not reflecting" in text or "allocate" in text or "pop" in text:
        return "Payment allocation issue; payment not reflected on account."
    if "rejection fee" in text or "rejection fee" in text or "r202" in text:
        return "Rejection/debit order fee disputed."
    if "credit limit" in text or "increase credit" in text:
        return "Credit limit or credit increase request."
    if "suspended" in text or "unsuspend" in text or "lift" in text:
        return "Account suspension or request to lift suspension."
    if "duplicate" in text or "billed twice" in text or "double debit" in text:
        return "Duplicate or incorrect billing claimed."
    if "late payment" in text or "interest" in text or "reconnection fee" in text:
        return "Late payment, interest, or reconnection fee dispute."
    if "cancel" in text or "cancellation" in text or "30 day" in text:
        return "Cancellation or 30-day notice dispute."
    if "discount" in text or "settlement" in text:
        return "Discount or settlement offer / EDC related."
    if "bad debt" in text or "clear" in text and "acc" in text:
        return "Bad debt or final account clearance."
    if "prescribed" in text or "prescription" in text:
        return "Prescribed debt or prescription claim."
    if "penalty" in text or "clawback" in text:
        return "Penalty or clawback dispute."
    if "fraud" in text or "identity" in text:
        return "Potential fraud or identity dispute."
    if "wrong fa" in text or "wrong account" in text:
        return "Payment to wrong FA/account."
    if "mandate" in text or "bank detail" in text:
        return "Bank mandate or details update required."
    # Default: short summary from memo
    snippet = text[:120].replace("\n", " ")
    return f"Dispute raised: {snippet}{'…' if len(text) > 120 else ''}"


def create_category_chart(df: pd.DataFrame, title: str):
    """Create an interactive bar chart with dark theme."""
    category_counts = df["CATEGORY"].value_counts().head(20).reset_index()
    category_counts.columns = ["Category", "Count"]
    
    fig = px.bar(
        category_counts,
        x="Category",
        y="Count",
        title=title,
        color="Count",
        color_continuous_scale="Blues",
        text="Count"
    )
    fig.update_layout(
        plot_bgcolor="rgba(30, 39, 70, 0.8)",
        paper_bgcolor="rgba(26, 26, 46, 0.5)",
        font=dict(color="#e0e0e0", size=12),
        title_font=dict(color="#00d4ff", size=16),
        xaxis=dict(
            gridcolor="#3a4a6b",
            title="",
            tickfont=dict(color="#f8fafc", size=13),
            automargin=True,
        ),
        yaxis=dict(gridcolor="#3a4a6b", title="Count"),
        showlegend=False
    )
    fig.update_traces(textposition="outside", textfont=dict(color="#e0e0e0"))
    fig.update_xaxes(tickangle=-45)
    return fig


def main():
    # --- Sidebar ---
    st.sidebar.header("📁 Data Source")
    csv_dir = st.sidebar.text_input("CSV folder", value=str(DEFAULT_CSV_DIR), key="csv_dir")
    csv_name = st.sidebar.text_input("CSV filename", value=CSV_FILENAME, key="csv_name")
    load_btn = st.sidebar.button("🔄 Load & Categorise", type="primary", use_container_width=True)

    should_load = load_btn or "df" not in st.session_state
    if should_load:
        with st.spinner("Loading CSV and running categorisation…"):
            try:
                df = get_categorised_data(csv_dir, csv_name)
                st.session_state["df"] = df
                st.rerun()
            except FileNotFoundError as e:
                st.error(str(e))
                st.info("Use the sidebar to set the correct CSV folder and filename.")
                return
            except Exception as e:
                st.error(f"Error loading data: {e}")
                return

    df = st.session_state.get("df")
    if df is None or df.empty:
        st.warning("Load data using the sidebar.")
        return

    # Filters
    st.sidebar.header("🔍 Filters")
    categories = ["All"] + sorted(df["CATEGORY"].unique().tolist())
    statuses = ["All"] + sorted(df["STATUS"].str.strip().dropna().unique().tolist())
    sel_cat = st.sidebar.selectbox("Category", categories, key="filter_cat")
    sel_status = st.sidebar.selectbox(
        "Status",
        statuses,
        key="filter_status",
        format_func=lambda s: "All" if s == "All" else status_label(s),
    )
    search = st.sidebar.text_input("Search in memo text", placeholder="e.g. refund, credit limit", key="search_memo")
    st.sidebar.caption("Filters apply to all charts and tables.")

    filtered = apply_filters(df, sel_cat, sel_status, search)

    # --- Header ---
    st.markdown("# 🤖 ReveniQ AI")
    st.markdown("### **Dispute Categorisation Dashboard**")
    st.markdown("*Where disputes end—and revenue stays protected*")
    st.divider()

    # --- KPI Row ---
    total = len(filtered)
    total_amt = filtered["AMOUNT"].fillna(0).sum()
    n_cat = filtered["CATEGORY"].nunique()
    uncat = (filtered["CATEGORY"] == "Uncategorised").sum()
    pct_uncat = (uncat / total * 100) if total else 0
    avg_amt = (total_amt / total) if total else 0

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.metric("📊 Total Disputes", f"{total:,}", help="Count after applying filters")
    with k2:
        st.metric("📁 Categories", f"{n_cat}", help="Unique categories in filtered set")
    with k3:
        st.metric(
            "💰 Total Amount (R)",
            f"{total_amt:,.0f}",
            help=f"Sum of AMOUNT in filtered set. Full amount: R {total_amt:,.2f}",
        )
    with k4:
        delta_color = "inverse" if pct_uncat > 5 else "normal"
        st.metric("❓ Uncategorised", f"{uncat:,}", 
                 delta=f"{pct_uncat:.1f}%", 
                 delta_color=delta_color,
                 help="Uncategorised disputes (target: <5%)")
    with k5:
        st.metric("📈 Avg Amount (R)", f"{avg_amt:,.0f}" if total else "—", help="Average dispute amount")

    st.divider()

    # --- Top 5 Categories Needing Instant Handling ---
    st.markdown('<div class="section-header">🚨 Top 5 Categories Requiring Instant Handling</div>', unsafe_allow_html=True)
    
    statuses_top5 = sorted(df["STATUS"].str.strip().dropna().unique().tolist())
    default_index = 0
    if statuses_top5 and "J" in statuses_top5:
        default_index = statuses_top5.index("J")
    selected_status_top5 = st.selectbox(
        "Status",
        statuses_top5,
        index=default_index,
        key="top5_status_filter",
        format_func=lambda s: status_label(s),
        help="Show top 5 categories by revenue for the selected status.",
    )
    top_categories = calculate_top_categories_by_status(df, selected_status_top5)
    
    if not top_categories.empty:
        cols = st.columns(5)
        for i, (_, row) in enumerate(top_categories.iterrows()):
            if i >= 5:
                break
            with cols[i]:
                st.markdown(f"""
                <div class="top-category-card">
                    <div class="category-name">#{i + 1} {row['Category']}</div>
                    <div class="category-stats">
                        📊 {int(row['Count']):,} disputes<br>
                        💰 R {row['Total_Amount']:,.0f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        st.caption(
            f"Top 5 by revenue for status **{status_label(selected_status_top5)}**."
        )
    else:
        st.info(
            f"No categories to display for status **{status_label(selected_status_top5)}**."
        )

    st.divider()

    # --- Tabs: Overview | Drill-Down | Data ---
    tab_overview, tab_drilldown, tab_open_analysis, tab_data = st.tabs([
        "📊 Overview", "🔍 Drill-Down Analysis", "📋 Open Dispute Analysis", "📄 Data Table"
    ])

    with tab_overview:
        st.markdown('<div class="section-header">Overview Analytics</div>', unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Disputes by Category (Top 20)")
            fig_cat = create_category_chart(filtered, "Disputes by Category")
            st.plotly_chart(fig_cat, use_container_width=True)
        
        with c2:
            st.markdown("#### Disputes by Status")
            status_counts = filtered["STATUS"].str.strip().value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]
            status_counts["Status"] = status_counts["Status"].apply(status_label)
            
            fig_status = px.pie(
                status_counts,
                values="Count",
                names="Status",
                title="Status Distribution",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_status.update_layout(
                plot_bgcolor="rgba(30, 39, 70, 0.8)",
                paper_bgcolor="rgba(26, 26, 46, 0.5)",
                font=dict(color="#e0e0e0", size=12),
                title_font=dict(color="#00d4ff", size=16),
                showlegend=True,
                legend=dict(font=dict(color="#e0e0e0"))
            )
            st.plotly_chart(fig_status, use_container_width=True)

        st.markdown("#### Amount by Category (Top 20)")
        amt_cat = filtered.groupby("CATEGORY")["AMOUNT"].sum().sort_values(ascending=False).head(20).reset_index()
        amt_cat.columns = ["Category", "Total_Amount"]
        
        fig_amt = px.bar(
            amt_cat,
            x="Category",
            y="Total_Amount",
            title="Total Amount by Category",
            color="Total_Amount",
            color_continuous_scale="Viridis",
            text="Total_Amount"
        )
        fig_amt.update_layout(
            plot_bgcolor="rgba(30, 39, 70, 0.8)",
            paper_bgcolor="rgba(26, 26, 46, 0.5)",
            font=dict(color="#e0e0e0", size=12),
            title_font=dict(color="#00d4ff", size=16),
            xaxis=dict(
                gridcolor="#3a4a6b",
                title="",
                tickfont=dict(color="#f8fafc", size=13),
                automargin=True,
            ),
            yaxis=dict(gridcolor="#3a4a6b", title="Amount (R)"),
            showlegend=False
        )
        fig_amt.update_traces(texttemplate="R %{text:,.0f}", textposition="outside", textfont=dict(color="#e0e0e0"))
        fig_amt.update_xaxes(tickangle=-45)
        st.plotly_chart(fig_amt, use_container_width=True)

    with tab_drilldown:
        st.markdown('<div class="section-header">Drill-Down Analysis by Category</div>', unsafe_allow_html=True)
        
        # Group by category for drill-down
        category_summary = filtered.groupby("CATEGORY").agg({
            "DISPUTE_ID": "count",
            "AMOUNT": ["sum", "mean"],
        }).reset_index()
        category_summary.columns = ["Category", "Count", "Total_Amount", "Avg_Amount"]
        category_summary = category_summary.sort_values("Category", ascending=True)
        
        # Create expandable sections for each category
        for _, row in category_summary.iterrows():
            cat_name = row["Category"]
            cat_data = filtered[filtered["CATEGORY"] == cat_name]
            
            with st.expander(
                f"📁 {cat_name} - {int(row['Count']):,} disputes (R {row['Total_Amount']:,.0f}) | "
                f"Avg: R {row['Avg_Amount']:,.0f}",
                expanded=False
            ):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Disputes", f"{int(row['Count']):,}")
                with col2:
                    st.metric("Total Amount", f"R {row['Total_Amount']:,.0f}")
                with col3:
                    st.metric("Avg Amount", f"R {row['Avg_Amount']:,.0f}")
                
                st.markdown("---")
                
                # Status breakdown
                col_stat, col_amt = st.columns(2)
                with col_stat:
                    st.markdown("##### Status Breakdown")
                    status_breakdown = cat_data["STATUS"].str.strip().value_counts().reset_index()
                    status_breakdown.columns = ["Status", "Count"]
                    status_breakdown["Status"] = status_breakdown["Status"].apply(status_label)
                    st.dataframe(status_breakdown, use_container_width=True, height=200)
                
                with col_amt:
                    st.markdown("##### Amount Distribution")
                    if len(cat_data) > 0:
                        fig_dist = px.histogram(
                            cat_data,
                            x="AMOUNT",
                            nbins=20,
                            title=f"Amount Distribution - {cat_name}",
                            color_discrete_sequence=["#00d4ff"]
                        )
                        fig_dist.update_layout(
                            plot_bgcolor="rgba(30, 39, 70, 0.8)",
                            paper_bgcolor="rgba(26, 26, 46, 0.5)",
                            font=dict(color="#e0e0e0", size=12),
                            title_font=dict(color="#00d4ff", size=14),
                            xaxis=dict(gridcolor="#3a4a6b", title="Amount (R)"),
                            yaxis=dict(gridcolor="#3a4a6b", title="Count"),
                            showlegend=False
                        )
                        st.plotly_chart(fig_dist, use_container_width=True)
                
                # Sample disputes
                st.markdown("##### Sample Disputes (First 10)")
                sample_cols = ["DISPUTE_ID", "STATUS", "AMOUNT", "SYS_CREATION_DATE"]
                sample_df = cat_data[sample_cols].head(10).copy()
                sample_df["STATUS"] = sample_df["STATUS"].apply(status_label)
                st.dataframe(sample_df, use_container_width=True, height=250)

    with tab_open_analysis:
        st.markdown('<div class="section-header">📋 Open Dispute Analysis</div>', unsafe_allow_html=True)
        st.caption(
            "Dispute-level analysis for **open** disputes only (status **O**). "
            "Policy retrieval (**RAG**) is **required** for AI resolution: place `.txt` / `.md` under `docs/rag` "
            "and keep Ollama embedding available, unless you set **REVENIQ_RAG_DISABLED=1** for local testing only. "
            "Executable rule SQL can live in `docs/rag` as `.sql` files or ```sql blocks with `-- REVENIQ_CATEGORY: …` (see `.env.example` and `reveniq_ai/ai_sql_runner.py`)."
        )
        # Only show open disputes (status O); fallback to "Open" if O not present in data
        status_col = df["STATUS"].str.strip()
        analysis_df = df[status_col == "O"]
        if analysis_df.empty and (status_col == "Open").any():
            analysis_df = df[status_col == "Open"]
        if analysis_df.empty:
            st.info("No open disputes (status O) in the loaded data.")
        else:
            # Build row-level table: dispute id, category, memo_text, Defect Analysis, Required Action (rule-based)
            open_table = analysis_df[["DISPUTE_ID", "CATEGORY", "MEMO_TEXT"]].copy()
            open_table["MEMO_TEXT"] = open_table["MEMO_TEXT"].fillna("").astype(str).str.replace("\n", " ")
            open_table["Defect Analysis"] = open_table.apply(
                lambda r: get_defect_analysis(r["MEMO_TEXT"], r["CATEGORY"]), axis=1
            )
            # Required Action from per-category rules (REQUIRED_ACTION column set in data_loader)
            open_table["Required Action"] = analysis_df["REQUIRED_ACTION"].values

            # 0) Filter by category (so table and AI resolution only show/use selected categories)
            all_categories = sorted(open_table["CATEGORY"].dropna().unique().astype(str).tolist())
            default_cats = [c for c in ["Rejection Fee Dispute", "Late Payment / Interest Dispute"] if c in all_categories] or (all_categories[:1] if all_categories else [])
            selected_categories = st.multiselect(
                "Filter by category",
                options=all_categories,
                default=default_cats,
                key="open_analysis_category_filter",
                help="Only these categories are shown in the table and sent to AI for resolution. Choose one or more.",
            )
            if selected_categories:
                open_table = open_table[open_table["CATEGORY"].astype(str).isin(selected_categories)]

            # 1) Search by Dispute ID
            dispute_id_search = st.text_input(
                "Search by Dispute ID",
                placeholder="Enter Dispute ID (e.g. 1799594)",
                key="open_analysis_dispute_id_search",
                help="Filter table to show only this dispute. Leave empty to see all.",
            )
            if dispute_id_search and str(dispute_id_search).strip():
                search_str = str(dispute_id_search).strip()
                open_table = open_table[
                    open_table["DISPUTE_ID"].astype(str).str.contains(search_str, regex=False, na=False)
                ]

            # 2) Rows to show: include "All" to see every dispute
            row_options = [100, 250, 500, 1000, 2000, "All"]
            row_limit_analysis = st.selectbox(
                "Rows to show",
                row_options,
                index=1,
                key="open_analysis_rows",
                format_func=lambda x: str(x) if x != "All" else "All (show every dispute)",
            )
            if row_limit_analysis != "All":
                open_table = open_table.head(int(row_limit_analysis))

            # Override Required Action with cached outcomes (from "Get AI resolution" when REVENIQ_AI_USE_RULE_OUTCOME=1)
            outcomes_cache = st.session_state.get("required_action_outcomes") or {}
            if outcomes_cache:
                def _action(row):
                    did = row["DISPUTE_ID"]
                    if pd.notna(did) and int(did) in outcomes_cache:
                        return outcomes_cache[int(did)]
                    return row["Required Action"]
                open_table["Required Action"] = open_table.apply(_action, axis=1)

            # --- AI resolution & recommendation (Ollama) ---
            try:
                from reveniq_ai.genai_resolution import get_ollama_parallel_workers
            except ImportError:
                def get_ollama_parallel_workers():
                    try:
                        n = int(os.environ.get("OLLAMA_PARALLEL_WORKERS", "4"))
                        return max(1, min(8, n))
                    except ValueError:
                        return 4
            _n_workers = get_ollama_parallel_workers()
            _ = _n_workers  # keep computed for internal logic without showing UI caption
            ai_max_rows = st.selectbox(
                "Max disputes to send to AI per run",
                [5, 10, 15, 25, 50, 100],
                index=0,
                key="ai_max_rows",
                help="For 50–100: use OLLAMA_PARALLEL_WORKERS=6 and a fast model (phi). Results cached.",
            )
            run_ai_btn = st.button(
                "✨ Get AI resolution & recommendation",
                key="open_analysis_run_ai",
                type="primary",
                help=f"Uses Ollama (local). Up to {ai_max_rows} rows. Results cached.",
            )
            if run_ai_btn:
                from reveniq_ai.genai_resolution import get_ai_resolution
                to_process = open_table.head(ai_max_rows)
                cache = st.session_state.get("ai_resolution_cache") or {}
                # Build list of rows that need an AI call
                todo = []
                for idx, row in to_process.iterrows():
                    did = row["DISPUTE_ID"]
                    key = int(did) if pd.notna(did) else f"memo_{hash(str(row['MEMO_TEXT'])[:300])}"
                    if key in cache:
                        continue
                    todo.append((key, idx, row))
                if not todo:
                    st.info("All visible rows already have AI results. Change filters or clear cache by reloading data.")
                else:
                    # When REVENIQ_AI_USE_RULE_OUTCOME=0, AI uses only RAG doc + memo (no Required Action). Set =1 to pass rule outcome to AI.
                    use_rule_outcome = (os.environ.get("REVENIQ_AI_USE_RULE_OUTCOME", "0").strip() in ("1", "true", "yes"))
                    rule_outcomes = {}
                    if use_rule_outcome:
                        try:
                            from reveniq_ai.required_action_rules import get_categories_with_rules
                            rule_cats = get_categories_with_rules()
                        except Exception:
                            rule_cats = ["Rejection Fee Dispute"]
                        rule_todo = [(key, idx, row) for key, idx, row in todo if row.get("CATEGORY") in rule_cats and pd.notna(row.get("DISPUTE_ID"))]
                    else:
                        rule_todo = []
                    if rule_todo:
                        try:
                            from reveniq_ai.db import is_configured as db_configured, get_connection
                            if db_configured():
                                with st.spinner("Running rules (AI-generated SQL from RAG) so AI gets real outcomes…"):
                                    conn = get_connection()
                                    try:
                                        from reveniq_ai.ai_sql_runner import get_rule_outcome_via_ai_sql
                                        for key, idx, row in rule_todo:
                                            did = int(row["DISPUTE_ID"])
                                            cat = row.get("CATEGORY") or "Rejection Fee Dispute"
                                            res = get_rule_outcome_via_ai_sql(conn, did, category=cat)
                                            rule_outcomes[key] = res["outcome"] if res.get("success") and res.get("outcome") else (res.get("error") or "Rule check failed.")
                                    finally:
                                        conn.close()
                            prev = st.session_state.get("required_action_outcomes") or {}
                            for key, idx, row in rule_todo:
                                if key in rule_outcomes and pd.notna(row.get("DISPUTE_ID")):
                                    prev[int(row["DISPUTE_ID"])] = rule_outcomes[key]
                            st.session_state["required_action_outcomes"] = prev
                        except Exception:
                            pass
                    n_workers = get_ollama_parallel_workers()
                    progress_bar = st.progress(0.0, text=f"AI resolution: 0 / {len(todo)}")
                    try:
                        from concurrent.futures import ThreadPoolExecutor, as_completed
                        def run_one(item):
                            key, idx, row = item
                            did = row["DISPUTE_ID"]
                            rule_outcome = (rule_outcomes.get(key) if key in rule_outcomes else row.get("Required Action")) if use_rule_outcome else None
                            res = get_ai_resolution(
                                memo_text=row["MEMO_TEXT"],
                                category=row["CATEGORY"],
                                rule_outcome=rule_outcome,
                                dispute_id=int(did) if pd.notna(did) else None,
                                amount=analysis_df.loc[idx, "AMOUNT"] if "AMOUNT" in analysis_df.columns and idx in analysis_df.index else None,
                                status=analysis_df.loc[idx, "STATUS"] if "STATUS" in analysis_df.columns and idx in analysis_df.index else None,
                            )
                            if use_rule_outcome:
                                res["_rule_outcome_used"] = rule_outcome
                            return key, res
                        done = 0
                        with ThreadPoolExecutor(max_workers=n_workers) as ex:
                            futures = {ex.submit(run_one, item): item for item in todo}
                            for fut in as_completed(futures):
                                key, res = fut.result()
                                cache[key] = res
                                done += 1
                                progress_bar.progress(done / len(todo), text=f"AI resolution: {done} / {len(todo)}")
                    except Exception as e:
                        st.error(str(e))
                    finally:
                        progress_bar.empty()
                    st.session_state["ai_resolution_cache"] = cache
                    st.rerun()

            ai_cache = st.session_state.get("ai_resolution_cache") or {}
            if ai_cache:
                def _ai_resolution(row):
                    did = row["DISPUTE_ID"]
                    key = int(did) if pd.notna(did) else f"memo_{hash(str(row['MEMO_TEXT'])[:300])}"
                    c = ai_cache.get(key)
                    if c:
                        summary = c.get("resolution_summary") or "—"
                        err = c.get("error")
                        if err:
                            short_err = (err.split("\n")[0].strip())[:120]
                            summary = f"{summary} [Error: {short_err}]"
                        return summary
                    return ""
                def _ai_action(row):
                    did = row["DISPUTE_ID"]
                    key = int(did) if pd.notna(did) else f"memo_{hash(str(row['MEMO_TEXT'])[:300])}"
                    c = ai_cache.get(key)
                    if c:
                        return c.get("recommended_action") or "—"
                    return ""
                def _ai_confidence(row):
                    did = row["DISPUTE_ID"]
                    key = int(did) if pd.notna(did) else f"memo_{hash(str(row['MEMO_TEXT'])[:300])}"
                    c = ai_cache.get(key)
                    if c:
                        return c.get("confidence") or "—"
                    return ""
                open_table["AI Resolution"] = open_table.apply(_ai_resolution, axis=1)
                open_table["AI Recommended Action"] = open_table.apply(_ai_action, axis=1)
                open_table["AI Confidence"] = open_table.apply(_ai_confidence, axis=1)

            # Hide internal helper columns from the UI table
            display_table = open_table.drop(columns=["Defect Analysis", "Required Action"], errors="ignore")

            col_config = {
                "DISPUTE_ID": st.column_config.NumberColumn("Dispute ID", format="%d"),
                "CATEGORY": st.column_config.TextColumn("Category", width="medium"),
                "MEMO_TEXT": st.column_config.TextColumn("Memo Text", width="large"),
            }
            if ai_cache:
                col_config["AI Resolution"] = st.column_config.TextColumn("AI Resolution", width="large")
                col_config["AI Recommended Action"] = st.column_config.TextColumn("AI Recommended Action", width="large")
                col_config["AI Confidence"] = st.column_config.TextColumn("AI Confidence", width="small")
            st.dataframe(
                display_table,
                column_config=col_config,
                use_container_width=True,
                height=450,
                hide_index=True,
            )
            # AI recommendation analysis: why did the AI recommend this for a given dispute?
            if ai_cache:
                with st.expander("🔍 AI recommendation analysis (why did the AI recommend this?)"):
                    lookup_did = st.number_input(
                        "Dispute ID",
                        min_value=0,
                        value=0,
                        step=1,
                        key="open_analysis_why_did",
                        help="Enter a dispute ID (e.g. 1806421) to see what the AI used to make its recommendation.",
                    )
                    if lookup_did and int(lookup_did) > 0:
                        kid = int(lookup_did)
                        c = ai_cache.get(kid)
                        if c:
                            st.markdown("**1. Rule outcome sent to the AI (if any):**")
                            rule_used = c.get("_rule_outcome_used") or c.get("rule_outcome_used") or "(None – AI used only RAG policy + memo)"
                            st.text(rule_used)
                            st.markdown("**2. RAG policy snippets used:**")
                            rag = c.get("rag_snippets") or "(Not stored or RAG disabled)"
                            st.text_area("Policy text the AI saw", value=rag[:8000] if isinstance(rag, str) else str(rag), height=150, key="open_analysis_rag_display", disabled=True)
                            st.markdown("**3. AI resolution summary:**")
                            st.text(c.get("resolution_summary") or "—")
                            st.markdown("**4. AI recommended action:**")
                            st.text(c.get("recommended_action") or "—")
                            st.caption(
                                "For Rejection Fee: 'Do not approve' usually means the policy conditions for approval were not met "
                                "(e.g. no BCK/DCK, or cash payment after DD due date, or no cash in the extract–due window). "
                                "The AI follows the RAG policy and memo; if a rule outcome was sent, it aligns with that."
                            )
                        else:
                            st.info(f"No AI result in cache for dispute ID {lookup_did}. Run 'Get AI resolution' including this dispute, then check again.")
            st.download_button(
                "Download analysis (CSV)",
                open_table.to_csv(index=False),
                file_name="open_dispute_analysis.csv",
                mime="text/csv",
                key="download_open_analysis",
            )

    with tab_data:
        st.markdown('<div class="section-header">Data Table</div>', unsafe_allow_html=True)
        
        # Category filter for Data Table
        table_categories = ["All"] + sorted(filtered["CATEGORY"].unique().tolist())
        selected_table_cat = st.selectbox(
            "Filter by Category",
            table_categories,
            key="data_table_category_filter",
            help="Filter the table by dispute category.",
        )
        table_filtered = filtered if selected_table_cat == "All" else filtered[filtered["CATEGORY"] == selected_table_cat]
        
        table_cols = ["DISPUTE_ID", "STATUS", "AMOUNT", "TAX_AMOUNT", "CATEGORY", "CHARGE_CODE"]
        display = table_filtered[table_cols].copy()
        display.insert(
            display.columns.get_loc("CATEGORY") + 1,
            "MEMO_TEXT",
            table_filtered["MEMO_TEXT"].fillna("").astype(str).str.replace("\n", " ")
        )
        
        row_limit = st.selectbox("Rows to show", [100, 250, 500, 1000, 5000], index=1, key="row_limit")
        display = display.head(row_limit)
        
        st.dataframe(
            display,
            use_container_width=True,
            height=500,
            hide_index=True
        )
        st.caption(f"Showing **{len(display):,}** of **{len(table_filtered):,}** disputes. Category filter: **{selected_table_cat}**. Sidebar filters also apply.")

    st.divider()
    st.markdown(
        '<div class="reveniq-footer">🤖 ReveniQ AI · Amdocs – make it amazing<br>'
        f'Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>',
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
