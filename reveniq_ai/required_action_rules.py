"""
Required Action rules for Open Disputes by category.
ReveniQ suggests the required action (outcome only) for CSRs to approve or reject.
Digital COE Gen AI Team
"""

from typing import Optional

# ---------------------------------------------------------------------------
# Rule definitions per category (used by rule runners; UI shows outcome only)
# ---------------------------------------------------------------------------

REJECTION_FEE_DISPUTE_RULE = {
    "category": "Rejection Fee Dispute",
    "steps": [],
    "outcomes": [],
}

# Short messages when outcome cannot be computed (no DB, no dispute_id, or rule failed)
_PENDING_DB = "Outcome pending – DB check required."
_PENDING_DISPUTE_ID = "Outcome pending – Dispute ID required for rule."
_RULE_FAILED = "Rule check failed – verify manually."

# Fallback for categories without a runnable rule
_DEFAULT_ACTION = "Review dispute and apply standard resolution or escalate."


def get_required_action_outcome(
    category: str,
    dispute_id: Optional[int] = None,
    status: Optional[str] = None,
    run_db: bool = True,
) -> str:
    """
    Return only the outcome for CSR (approve/reject).
    When run_db=True and DB is configured, runs rule via AI-generated SQL from RAG for categories in get_categories_with_rules().
    When run_db=False (e.g. at load time), returns pending message to keep load fast.
    """
    if not category or not str(category).strip():
        return _DEFAULT_ACTION
    cat = str(category).strip()

    try:
        from .ai_sql_runner import get_categories_with_ai_sql_rules, get_rule_outcome_via_ai_sql
        ai_sql_cats = get_categories_with_ai_sql_rules()
    except ImportError:
        ai_sql_cats = []
        get_rule_outcome_via_ai_sql = None

    has_rule = cat == "Rejection Fee Dispute" or cat == "Late Payment / Interest Dispute" or cat in ai_sql_cats
    if not has_rule:
        return _DEFAULT_ACTION

    if dispute_id is None:
        return _PENDING_DISPUTE_ID
    if not run_db:
        return _PENDING_DB
    try:
        from .db import is_configured, get_connection
    except ImportError:
        return _PENDING_DB
    if not is_configured():
        return _PENDING_DB

    if cat in ai_sql_cats and get_rule_outcome_via_ai_sql:
        try:
            conn = get_connection()
            try:
                result = get_rule_outcome_via_ai_sql(conn, dispute_id, category=cat)
                if result.get("success") and result.get("outcome"):
                    return result["outcome"]
                return result.get("error") or _RULE_FAILED
            finally:
                conn.close()
        except Exception:
            return _PENDING_DB

    return _DEFAULT_ACTION


def get_required_action(
    category: str,
    dispute_id: Optional[int] = None,
    status: Optional[str] = None,
    run_db: bool = True,
) -> str:
    """
    Same as get_required_action_outcome: returns outcome only for CSR.
    Use run_db=False at load time to avoid slow DB calls for every row.
    """
    return get_required_action_outcome(category, dispute_id, status, run_db)


def get_categories_with_rules() -> list:
    """Return list of category names that have a runnable required-action rule (Rejection Fee + any AI SQL categories)."""
    try:
        from .ai_sql_runner import get_categories_with_ai_sql_rules
        ai_cats = get_categories_with_ai_sql_rules()
    except ImportError:
        ai_cats = []
    base = ["Rejection Fee Dispute", "Late Payment / Interest Dispute"]
    for c in ai_cats:
        if c not in base:
            base.append(c)
    return base
