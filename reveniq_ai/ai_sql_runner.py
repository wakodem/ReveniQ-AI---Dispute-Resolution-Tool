"""
Run dispute rules (Rejection Fee and future categories) using AI-generated SQL from RAG policy text.
The LLM produces a single SELECT from policy; we validate and execute it.
Digital COE Gen AI Team
"""

import json
import os
import re
from typing import Any, List, Optional

# Outcome messages for required action (used by dashboard and required_action_rules)
OUTCOME_NO_DCK = "Recommendation: Do not approve. No rejection fee was created for this dispute."
OUTCOME_CASH_AFTER_DD = "Recommendation: Do not approve. A cash payment was received after the direct debit due date; the rejection fee is valid."
OUTCOME_NO_CASH_FEE_CORRECT = "Recommendation: Do not approve. No cash payment was received after the due date; the rejection fee was applied correctly."
OUTCOME_APPROVE = "Recommendation: Approve."
OUTCOME_ERROR = "Unable to run the rule. Please check the dispute data or try again."

OUTCOME_LATE_PYM_BALANCE = "Recommendation: Do not approve. Outstanding balance remains unpaid; the late payment fee is valid."
OUTCOME_LATE_PYM_CREDIT_EXISTS = "Recommendation: Do not approve. A credit has already been applied to this charge."
OUTCOME_LATE_PYM_PAID_LATE = "Recommendation: Do not approve. Payment was received after the due date; the late payment fee is valid."
OUTCOME_LATE_PYM_NO_CHARGE = "Recommendation: Manual review. No matching late payment charge found for this dispute."
OUTCOME_LATE_PYM_NO_PAYMENT = "Recommendation: Manual review. No payment record found after the due date."

# Categories that support AI-generated SQL from RAG. Add more as you add sections in docs/rag.
# Override via env: REVENIQ_AI_SQL_CATEGORIES=Rejection Fee Dispute,Duplicate Billing
_DEFAULT_AI_SQL_CATEGORIES = ["Rejection Fee Dispute", "Late Payment / Interest Dispute"]

# Only these tables may appear in generated SQL (case-insensitive). Expand per category if needed.
ALLOWED_TABLES = {
    "ar1_dispute",
    "ar1_payment_activity",
    "ar1_pay_channel",
    "bl1_charge_request",
    "ar1_payment",
    "ar1_payment_details",
    "ar1_direct_debit_request",
    "ar1_charges",
    "ar1_charge_group",
}

FORBIDDEN_SQL_PATTERNS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|CREATE|ALTER|EXECUTE|EXEC|;)\b",
    re.IGNORECASE,
)


def _get_ollama_model() -> str:
    return (os.environ.get("OLLAMA_MODEL") or "llama3.2").strip() or "llama3.2"


def _get_ollama_base_url() -> str:
    return (os.environ.get("OLLAMA_BASE_URL") or "http://localhost:11434").strip()


def _get_ollama_timeout() -> int:
    try:
        return max(60, int(os.environ.get("OLLAMA_TIMEOUT_SECONDS", "600")))
    except ValueError:
        return 600


def _get_ollama_temperature() -> Optional[float]:
    raw = os.environ.get("OLLAMA_TEMPERATURE")
    if raw is None or not str(raw).strip():
        return None
    try:
        v = float(raw)
        return max(0.0, min(2.0, v))
    except ValueError:
        return None


def _get_ollama_seed() -> Optional[int]:
    raw = os.environ.get("OLLAMA_SEED")
    if raw is None or not str(raw).strip():
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _call_ollama(prompt: str) -> str:
    """Call Ollama /api/generate; return response text."""
    import urllib.request

    from .genai_resolution import _ollama_top_k, _ollama_top_p

    url = f"{_get_ollama_base_url().rstrip('/')}/api/generate"
    payload = {
        "model": _get_ollama_model(),
        "prompt": prompt,
        "stream": False,
    }
    options = {}
    temp = _get_ollama_temperature()
    seed = _get_ollama_seed()
    top_p = _ollama_top_p()
    top_k = _ollama_top_k()
    if temp is not None:
        options["temperature"] = temp
    if seed is not None:
        options["seed"] = seed
    if top_p is not None:
        options["top_p"] = top_p
    if top_k is not None:
        options["top_k"] = top_k
    if options:
        payload["options"] = options
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=_get_ollama_timeout()) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return (data.get("response") or "").strip()


def _extract_sql_from_response(text: str) -> Optional[str]:
    """Get SQL from JSON key 'sql' or from a markdown code block."""
    if not text or not text.strip():
        return None
    # Try JSON first
    try:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```\s*$", "", cleaned)
        obj = json.loads(cleaned)
        sql = (obj.get("sql") or obj.get("query") or "").strip()
        if sql:
            return sql
    except (json.JSONDecodeError, TypeError):
        pass
    # Fallback: first ```sql ... ``` or ``` ... ``` block
    m = re.search(r"```(?:sql)?\s*\n?(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return None


def validate_sql(sql: str) -> tuple[bool, str]:
    """
    Ensure SQL is a single SELECT and only references allowed tables.
    Returns (ok, error_message).
    """
    if not sql or not sql.strip():
        return False, "Empty SQL."
    s = sql.strip().upper()
    if not s.startswith("SELECT"):
        return False, "Only SELECT statements are allowed."
    if FORBIDDEN_SQL_PATTERNS.search(sql):
        return False, "Statement must not contain DML/DDL or semicolon."
    # Heuristic: find table names (FROM and JOIN clauses)
    from_match = re.findall(r"\bFROM\s+([a-zA-Z0-9_]+)", sql, re.IGNORECASE)
    join_match = re.findall(r"\bJOIN\s+([a-zA-Z0-9_]+)", sql, re.IGNORECASE)
    tables = {t.lower() for t in from_match + join_match}
    disallowed = tables - ALLOWED_TABLES
    if disallowed:
        return False, f"Only allowed tables may be used. Disallowed: {disallowed}."
    return True, ""


_category_sql_cache: Optional[dict[str, str]] = None


def clear_literal_sql_cache() -> None:
    """Clear cached literal SQL map (after editing docs/rag)."""
    global _category_sql_cache
    _category_sql_cache = None


def _split_reveniq_category_header(sql: str) -> tuple[Optional[str], str]:
    """
    Strip leading Oracle-style comments -- REVENIQ_CATEGORY: <name>.
    Returns (category_name or None, remaining SQL body).
    """
    lines = sql.strip().splitlines()
    cat: Optional[str] = None
    idx = 0
    while idx < len(lines):
        m = re.match(r"^\s*--\s*REVENIQ_CATEGORY:\s*(.+?)\s*$", lines[idx], re.IGNORECASE)
        if m:
            cat = m.group(1).strip()
            idx += 1
            continue
        break
    body = "\n".join(lines[idx:]).strip()
    return cat, body


def _iter_fenced_sql_blocks(text: str):
    for m in re.finditer(r"```(?:sql)?\s*\n(.*?)```", text, re.DOTALL | re.IGNORECASE):
        yield m.group(1).strip()


def load_literal_sql_by_category() -> dict[str, str]:
    """
    Load executable SELECT statements from docs/rag:
    - Any .sql file whose body starts with -- REVENIQ_CATEGORY: <exact category column value>
    - Any ```sql ... ``` block in .md / .txt with the same header line inside the block.
    Last occurrence wins if the same category appears twice.
    """
    global _category_sql_cache
    if _category_sql_cache is not None:
        return _category_sql_cache
    try:
        from .rag import get_rag_docs_dir
    except ImportError:
        _category_sql_cache = {}
        return _category_sql_cache
    docs_dir = get_rag_docs_dir()
    out: dict[str, str] = {}
    if not docs_dir.is_dir():
        _category_sql_cache = {}
        return _category_sql_cache
    for path in sorted(docs_dir.glob("*.sql")):
        try:
            raw = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        cat, body = _split_reveniq_category_header(raw)
        if not cat or not body:
            continue
        ok, _ = validate_sql(body)
        if ok:
            out[cat] = body
    for ext in ("*.md", "*.txt"):
        for path in docs_dir.glob(ext):
            try:
                raw = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for block in _iter_fenced_sql_blocks(raw):
                cat, body = _split_reveniq_category_header(block)
                if not cat or not body:
                    continue
                ok, _ = validate_sql(body)
                if ok:
                    out[cat] = body
    _category_sql_cache = out
    return _category_sql_cache


def get_literal_sql_for_category(category: str) -> Optional[str]:
    """Return validated literal SELECT for this dispute category, if defined in docs/rag."""
    if not category or not str(category).strip():
        return None
    m = load_literal_sql_by_category()
    return m.get(str(category).strip())


def _scalar_result(cursor) -> Optional[str]:
    """Return first row first column as string, or None."""
    row = cursor.fetchone()
    if not row:
        return None
    val = row[0]
    if val is None:
        return None
    return str(val).strip().upper()


def _outcome_from_code(code: Optional[str], category: str) -> str:
    """Map AI-returned code to required-action outcome message. Category-specific for Rejection Fee; generic otherwise."""
    if not code:
        if category and "Rejection Fee" in category:
            return OUTCOME_NO_CASH_FEE_CORRECT
        return "Recommendation: Review dispute manually (no outcome from rule)."
    c = code.upper().strip()
    if c == "APPROVE":
        return OUTCOME_APPROVE
    if category and "Rejection Fee" in category:
        if c in ("NO_DCK", "NOT_FOUND", "NO_OPEN_DISPUTE"):
            return OUTCOME_NO_DCK
        if c in ("CASH_AFTER_DD", "CASH_AFTER_DUE"):
            return OUTCOME_CASH_AFTER_DD
        if c in ("NO_CASH_FEE_CORRECT", "DO_NOT_APPROVE"):
            return OUTCOME_NO_CASH_FEE_CORRECT
        return OUTCOME_NO_CASH_FEE_CORRECT
    if category and "Late Payment" in category:
        if c in ("BALANCE_OUTSTANDING", "BALANCE_GT_ZERO"):
            return OUTCOME_LATE_PYM_BALANCE
        if c in ("CREDIT_EXISTS", "RESTRICTION_GT_ZERO"):
            return OUTCOME_LATE_PYM_CREDIT_EXISTS
        if c in ("PAID_LATE", "PAYMENT_AFTER_DUE", "DO_NOT_APPROVE"):
            return OUTCOME_LATE_PYM_PAID_LATE
        if c in ("NO_CHARGE_FOUND", "NOT_FOUND", "NO_LATE_PYM"):
            return OUTCOME_LATE_PYM_NO_CHARGE
        if c in ("NO_PAYMENT_FOUND", "NO_PAYMENT"):
            return OUTCOME_LATE_PYM_NO_PAYMENT
        return OUTCOME_LATE_PYM_PAID_LATE
    # Other categories: pass through short message or map APPROVE / DO_NOT_APPROVE
    if c == "DO_NOT_APPROVE" or c.startswith("REJECT"):
        return "Recommendation: Do not approve. " + (code if len(code) < 100 else "")
    if c == "APPROVE" or c.startswith("APPROVE"):
        return OUTCOME_APPROVE
    return "Recommendation: " + (code if len(code) < 200 else code[:200])


def get_categories_with_ai_sql_rules() -> List[str]:
    """Categories that support AI-generated SQL from RAG. Add more in RAG doc and here (or via REVENIQ_AI_SQL_CATEGORIES)."""
    raw = os.environ.get("REVENIQ_AI_SQL_CATEGORIES", "").strip()
    if raw:
        return [c.strip() for c in raw.split(",") if c.strip()]
    return list(_DEFAULT_AI_SQL_CATEGORIES)


def get_rule_outcome_via_ai_sql(
    conn,
    dispute_id: int,
    category: str = "Rejection Fee Dispute",
    rag_policy_text: Optional[str] = None,
) -> dict[str, Any]:
    """
    Prefer literal SELECT from docs/rag (-- REVENIQ_CATEGORY); else use RAG policy + LLM-generated SQL.
    Returns one outcome code; we map to required-action message.
    conn: oracledb connection (caller owns lifecycle).
    category: dispute category (used for RAG retrieval and outcome mapping).
    rag_policy_text: if None, we retrieve from RAG using category.
    """
    details: List[str] = []

    literal_sql = get_literal_sql_for_category(category)
    if literal_sql and literal_sql.strip():
        ok, err = validate_sql(literal_sql)
        if not ok:
            return {
                "success": False,
                "outcome": None,
                "details": [f"Literal RAG SQL validation failed: {err}"],
                "error": err,
            }
        details.append("Executed literal SELECT from docs/rag (REVENIQ_CATEGORY header).")
        try:
            cur = conn.cursor()
            try:
                cur.execute(literal_sql, {"did": dispute_id})
                code = _scalar_result(cur)
            finally:
                cur.close()
            outcome = _outcome_from_code(code, category)
            details.append(f"SQL result code: {code!r}")
            return {
                "success": True,
                "outcome": outcome,
                "details": details,
                "error": None,
            }
        except Exception as e:
            return {
                "success": False,
                "outcome": None,
                "details": details + [str(e)],
                "error": f"Literal RAG SQL execution failed: {e}",
            }

    if not rag_policy_text or not rag_policy_text.strip():
        try:
            from .rag import is_rag_disabled, retrieve

            if is_rag_disabled():
                rag_policy_text = ""
            else:
                query = f"SQL validation steps tables dispute policy {category}"
                rag_policy_text = retrieve(query, category=category, top_k=5) or ""
        except Exception as e:
            return {
                "success": False,
                "outcome": None,
                "details": [f"RAG retrieval failed: {e}"],
                "error": "Could not load policy text for SQL generation.",
            }
        if not rag_policy_text.strip():
            return {
                "success": False,
                "outcome": None,
                "details": [
                    "No RAG policy text and no valid literal SQL for this category.",
                ],
                "error": (
                    "Mandatory RAG: add policy text in docs/rag, or add a ```sql block / .sql file "
                    "with -- REVENIQ_CATEGORY: <category> and a single SELECT using bind :did. "
                    "Or set REVENIQ_RAG_DISABLED=1 for local dev."
                ),
            }

    is_rejection_fee = category and "Rejection Fee" in category
    is_late_payment = category and "Late Payment" in category
    if is_rejection_fee:
        prompt = f"""You are an expert at writing Oracle SQL for dispute rules. Based ONLY on the following policy text, write a single Oracle SELECT statement that determines the outcome for a rejection fee dispute.

Policy and validation steps:
{rag_policy_text}

Rules:
- Use bind variable :did for dispute_id (number).
- In ar1_dispute, open disputes have status = 'O' (not 'OPEN').
- The query must return exactly one row with one column: a single outcome code. Allowed codes: APPROVE, NO_DCK, CASH_AFTER_DD, NO_CASH_FEE_CORRECT, NOT_FOUND.
- Use only these tables: ar1_dispute, ar1_payment_activity, ar1_pay_channel, bl1_charge_request, ar1_payment, ar1_payment_details, ar1_direct_debit_request.
- Logic: APPROVE only if a cash payment (PAYMENT_METHOD = 'CA') exists between DD extract_date and due_date; NO_DCK if no DCK charge or no BCK; CASH_AFTER_DD if cash after due date; NO_CASH_FEE_CORRECT if no cash in window; NOT_FOUND if dispute not open.

Respond with a JSON object only (no markdown), with key "sql" containing the single SELECT statement. Example:
{{"sql": "SELECT 'NO_DCK' FROM dual WHERE NOT EXISTS (SELECT 1 FROM ar1_dispute WHERE dispute_id = :did AND status = 'O')"}}
"""
    elif is_late_payment:
        prompt = f"""You are an expert at writing Oracle SQL for dispute rules. Based ONLY on the following policy text, write a single Oracle SELECT statement that determines the outcome for a late payment / interest dispute.

Policy and validation steps:
{rag_policy_text}

Rules:
- Use bind variable :did for dispute_id (number).
- The query must return exactly one row with one column: a single outcome code. Allowed codes: APPROVE, BALANCE_OUTSTANDING, CREDIT_EXISTS, PAID_LATE, NO_CHARGE_FOUND, NO_PAYMENT_FOUND.
- Use only these tables: ar1_dispute, ar1_charges, ar1_charge_group, ar1_payment_details.
- Logic:
  - NO_CHARGE_FOUND if no LATE_PYM charge exists for the dispute account.
  - BALANCE_OUTSTANDING if charge group BALANCE > 0.
  - CREDIT_EXISTS if RESTRICTION_AMOUNT > 0 on the charge.
  - Find the first payment after the due date; APPROVE if its SYS_CREATION_DATE <= DUE_DATE; PAID_LATE if after.
  - NO_PAYMENT_FOUND if no payment record exists after the due date.

Respond with a JSON object only (no markdown), with key "sql" containing the single SELECT statement. Example:
{{"sql": "SELECT 'NO_CHARGE_FOUND' FROM dual WHERE NOT EXISTS (SELECT 1 FROM ar1_charges WHERE account_id IN (SELECT account_id FROM ar1_dispute WHERE dispute_id = :did) AND charge_code = 'LATE_PYM')"}}
"""
    else:
        prompt = f"""You are an expert at writing Oracle SQL for dispute rules. For the category "{category}", based ONLY on the following policy text, write a single Oracle SELECT that determines the outcome.

Policy and validation steps:
{rag_policy_text}

Rules:
- Use bind variable :did for dispute_id (number).
- In ar1_dispute, open disputes have status = 'O'.
- The query must return exactly one row with one column: an outcome code (e.g. APPROVE, DO_NOT_APPROVE, or a short policy-based code).
- Use only these tables: ar1_dispute, ar1_payment_activity, ar1_pay_channel, bl1_charge_request, ar1_payment, ar1_payment_details, ar1_direct_debit_request.

Respond with a JSON object only (no markdown), with key "sql" containing the single SELECT statement.
"""

    try:
        raw = _call_ollama(prompt)
        sql = _extract_sql_from_response(raw)
        if not sql:
            return {
                "success": False,
                "outcome": None,
                "details": [f"Could not parse SQL from model. Raw: {raw[:500]}"],
                "error": "AI did not return valid SQL.",
            }
        details.append("Generated SQL (validated).")

        ok, err = validate_sql(sql)
        if not ok:
            return {
                "success": False,
                "outcome": None,
                "details": [f"Validation: {err}", f"SQL: {sql[:300]}"],
                "error": err,
            }

        cur = conn.cursor()
        try:
            cur.execute(sql, {"did": dispute_id})
            code = _scalar_result(cur)
        finally:
            cur.close()

        outcome = _outcome_from_code(code, category)
        details.append(f"Result code: {code or 'NULL'} -> {outcome[:50]}...")
        return {
            "success": True,
            "outcome": outcome,
            "details": details,
            "error": None,
        }
    except Exception as e:
        return {
            "success": False,
            "outcome": None,
            "details": details,
            "error": str(e),
        }


def use_ai_sql() -> bool:
    """True if rule outcome should be computed via AI-generated SQL from RAG (no effect when hardcoded runner removed)."""
    return os.environ.get("REVENIQ_USE_AI_SQL", "").strip().lower() in ("1", "true", "yes")
