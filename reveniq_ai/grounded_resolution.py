"""
RAG-driven SQL-grounded dispute resolution: one generic engine, category rules in docs/rag/grounded_specs.json.
Add new categories by editing JSON only (no new Python file per category).
Digital COE Gen AI Team
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Optional

try:
    from dotenv import load_dotenv
    _root = Path(__file__).resolve().parent.parent
    load_dotenv(_root / ".env")
except Exception:
    pass

_SPECS_CACHE: Optional[dict[str, Any]] = None


def _env_flag(name: str, default: bool = True) -> bool:
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return default
    return raw in ("1", "true", "yes", "on")


def _env_sql_grounded_resolution() -> bool:
    raw = os.environ.get("REVENIQ_SQL_GROUNDED_RESOLUTION", "").strip().lower()
    if not raw:
        return True
    return raw in ("1", "true", "yes", "on")


def _env_grounded_llm_refine() -> bool:
    """When True, Ollama rewrites SQL-grounded text after templates (decision stays SQL-backed)."""
    return os.environ.get("REVENIQ_GROUNDED_LLM_REFINE", "").strip().lower() in ("1", "true", "yes", "on")


def _rule_line_from_sql_decision(decision: str) -> str:
    d = (decision or "").strip().upper()
    if d == "APPROVE":
        return "Recommendation: Approve — per SQL evidence."
    if d == "REJECT":
        return "Recommendation: Do not approve — charge stands per SQL evidence."
    return "Recommendation: Manual review / escalate — per SQL evidence."


def _refine_grounded_with_llm(
    out: dict[str, Any],
    ctx: dict[str, Any],
    memo_text: str,
    category: str,
    rag_snippets: str,
) -> dict[str, Any]:
    """
    Optional LLM pass: clearer prose while SQL decision and evidence remain authoritative.
    On parse failure or decision mismatch, returns ``out`` unchanged.
    """
    try:
        from .genai_resolution import _apply_rule_override, _call_ollama
    except Exception:
        return out

    def _parse_refinement_json(text: str) -> dict[str, Any]:
        t = (text or "").strip()
        if not t:
            raise ValueError("empty")
        if t.startswith("```"):
            t = re.sub(r"^```(?:json)?\s*", "", t)
            t = re.sub(r"\s*```\s*$", "", t)
        return json.loads(t)

    decision = (ctx.get("decision") or "MANUAL_REVIEW").strip()
    ev = out.get("sql_evidence") or {}
    try:
        ev_json = json.dumps(ev, default=str, ensure_ascii=False)[:8000]
    except Exception:
        ev_json = str(ev)[:8000]

    rs = (out.get("resolution_summary") or "").strip()
    ra = (out.get("recommended_action") or "").strip()
    rag = (rag_snippets or "").strip()[:2500]
    memo = (memo_text or "").strip()[:1500]

    prompt = f"""You are editing telco dispute resolution output. The decision and evidence below come from the billing database and MUST NOT be contradicted.

**Authoritative SQL decision (must match your decision_confirm exactly):** {decision}

**Evidence (JSON, do not invent facts beyond this):**
{ev_json}

**Category:** {category}

**Memo (customer context):**
{memo}

**Policy excerpts (reference only):**
{rag if rag else "(none)"}

**Original resolution summary (improve clarity and tone; keep meaning):**
{rs}

**Original recommended action (improve wording; keep operational meaning):**
{ra}

Respond with a single JSON object only (no markdown fences), with exactly these keys:
- "resolution_summary": string, 2–6 short paragraphs max, professional; must align with decision {decision}.
- "recommended_action": string, operational steps consistent with decision {decision}.
- "decision_confirm": must be exactly one of: APPROVE, REJECT, MANUAL_REVIEW — and MUST equal: {decision}

Rules: Do not invent dates, amounts, table names, or payment events not present in the evidence JSON. If something is missing in evidence, say escalation/manual review rather than guessing."""

    base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").strip()
    model = (os.environ.get("OLLAMA_MODEL") or "llama3.2").strip() or "llama3.2"
    try:
        text = _call_ollama(prompt, model, base_url)
        parsed = _parse_refinement_json(text)
    except Exception:
        return out

    confirm = (parsed.get("decision_confirm") or "").strip().upper().replace(" ", "_")
    # Allow MANUAL REVIEW vs MANUAL_REVIEW
    if confirm == "MANUAL REVIEW":
        confirm = "MANUAL_REVIEW"
    dec_upper = decision.upper()
    if confirm != dec_upper:
        return out

    new_rs = (parsed.get("resolution_summary") or "").strip()
    new_ra = (parsed.get("recommended_action") or "").strip()
    if not new_rs:
        return out

    refined: dict[str, Any] = {
        **out,
        "resolution_summary": new_rs,
        "recommended_action": new_ra or ra,
        "confidence": out.get("confidence") or "high",
        "error": None,
    }
    rule_line = _rule_line_from_sql_decision(decision)
    refined = _apply_rule_override(refined, rule_line)

    if decision == "MANUAL_REVIEW":
        rlow = (refined.get("recommended_action") or "").lower()
        if "manual" not in rlow and "escalat" not in rlow:
            refined["recommended_action"] = ra

    refined["sql_grounded"] = True
    refined["sql_grounded_llm_refined"] = True
    return refined


def _fmt_date(val: Any) -> Optional[str]:
    if val is None:
        return None
    if hasattr(val, "strftime"):
        try:
            return val.strftime("%Y-%m-%d")
        except Exception:
            pass
    s = str(val).strip()
    return s[:10] if s else None


def _yes_no(b: bool) -> str:
    return "yes" if b else "no"


def _row_to_dict(cursor, row: Optional[tuple]) -> dict[str, Any]:
    if not row or not cursor.description:
        return {}
    out: dict[str, Any] = {}
    for i, desc in enumerate(cursor.description):
        name = (desc[0] or "").lower()
        out[name] = row[i]
    return out


def _load_specs_path() -> Path:
    override = os.environ.get("REVENIQ_GROUNDED_SPECS", "").strip()
    if override:
        return Path(override)
    try:
        from .rag import get_rag_docs_dir
        return get_rag_docs_dir() / "grounded_specs.json"
    except ImportError:
        return Path(__file__).resolve().parent.parent / "docs" / "rag" / "grounded_specs.json"


def load_grounded_specs() -> dict[str, Any]:
    """Load and cache grounded_specs.json (all categories)."""
    global _SPECS_CACHE
    if _SPECS_CACHE is not None:
        return _SPECS_CACHE
    path = _load_specs_path()
    if not path.is_file():
        _SPECS_CACHE = {"version": 1, "categories": {}}
        return _SPECS_CACHE
    try:
        raw = path.read_text(encoding="utf-8")
        _SPECS_CACHE = json.loads(raw)
    except Exception:
        _SPECS_CACHE = {"version": 1, "categories": {}}
    return _SPECS_CACHE


def get_grounded_spec_for_category(category: str) -> Optional[dict[str, Any]]:
    cat = (category or "").strip()
    if not cat:
        return None
    specs = load_grounded_specs()
    cats = specs.get("categories") or {}
    return cats.get(cat)


def _resolve_binds(bind_map: dict[str, str], ctx: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for sql_key, ctx_key in bind_map.items():
        if ctx_key not in ctx:
            raise KeyError(f"Missing context key '{ctx_key}' for bind :{sql_key}")
        out[sql_key] = ctx[ctx_key]
    return out


def _apply_memo_patterns(memo_text: str, spec: dict[str, Any]) -> bool:
    mm = spec.get("memo_manual_review") or {}
    env_name = (mm.get("env_disable") or "").strip()
    if env_name and not _env_flag(env_name, True):
        return False
    patterns = mm.get("patterns") or []
    if not memo_text or not patterns:
        return False
    m = memo_text
    for p in patterns:
        try:
            if re.search(p, m, re.IGNORECASE | re.DOTALL):
                return True
        except re.error:
            continue
    return False


def _run_pipeline(conn, dispute_id: int, spec: dict[str, Any]) -> dict[str, Any]:
    ctx: dict[str, Any] = {
        "success": False,
        "error": None,
        "dispute_id": dispute_id,
        "sql_steps_executed": [],
    }
    pipeline = spec.get("pipeline") or []
    cur = conn.cursor()
    try:
        for step in pipeline:
            step_id = step.get("id", "?")
            sql = (step.get("sql") or "").strip()
            if not sql:
                continue
            ctx["sql_steps_executed"].append(str(step_id))
            bind_map = step.get("bind") or {}
            binds = _resolve_binds(bind_map, ctx)
            cur.execute(sql, binds)
            row = cur.fetchone()

            # No row at all (e.g. Step 1 miss). Aggregates like MIN(...) still return one row (possibly NULL).
            if row is None:
                oe = step.get("on_empty")
                if oe:
                    for k, v in (oe.get("set") or {}).items():
                        ctx[k] = v
                    if oe.get("return"):
                        ctx["success"] = True
                        return ctx
                continue

            row_dict = _row_to_dict(cur, row)
            store = step.get("store_from_row") or {}
            for ctx_key, col_name in store.items():
                ctx[ctx_key] = row_dict.get((col_name or "").lower())

            for k, v in (step.get("post_store") or {}).items():
                ctx[k] = v

            for check in (step.get("post_store_checks") or []):
                cond = check.get("condition", "")
                field = check.get("field", "")
                val = ctx.get(field)
                triggered = False
                if cond == "balance_gt_zero" and val is not None:
                    try:
                        triggered = float(val) > 0
                    except (ValueError, TypeError):
                        pass
                elif cond == "restriction_gt_zero" and val is not None:
                    try:
                        triggered = float(val) > 0
                    except (ValueError, TypeError):
                        pass
                if triggered:
                    for k, v in (check.get("set") or {}).items():
                        if isinstance(v, str):
                            v = v.format(**{kk: ctx.get(kk, "—") for kk in ctx})
                        ctx[k] = v
                    if check.get("return"):
                        ctx["success"] = True
                        return ctx

            if step.get("post_store_check_null_dates"):
                ex = ctx.get("extract_date_raw")
                du = ctx.get("due_date_raw")
                if ex is None or du is None:
                    ctx["decision"] = "MANUAL_REVIEW"
                    ctx["escalation_reason"] = "Step 5c — extract_date or due_date is null."
                    ctx["audit_notes"] = ctx["escalation_reason"]
                    ctx["success"] = True
                    return ctx

        ctx["success"] = True
        return ctx
    except Exception as e:
        ctx["error"] = str(e)
        ctx["audit_notes"] = f"Evidence SQL error: {e}"
        ctx["success"] = False
        return ctx
    finally:
        cur.close()


def _finalize_cash_window(ctx: dict[str, Any], fin: dict[str, Any]) -> None:
    cash = ctx.get(fin.get("cash_field") or "cash_payment_date")
    if cash is not None:
        ctx["cash_in_window"] = True
        ctx["decision"] = "APPROVE"
        ctx["audit_notes"] = (fin.get("approve_audit") or "").format(
            cash_payment_date=_fmt_date(cash) or "—",
            extract_date=_fmt_date(ctx.get("extract_date_raw")) or ctx.get("extract_date") or "—",
            due_date=_fmt_date(ctx.get("due_date_raw")) or ctx.get("due_date") or "—",
        )
    else:
        ctx["cash_in_window"] = False
        ctx["decision"] = "REJECT"
        ctx["audit_notes"] = (fin.get("reject_audit") or "").format(
            extract_date=_fmt_date(ctx.get("extract_date_raw")) or ctx.get("extract_date") or "—",
            due_date=_fmt_date(ctx.get("due_date_raw")) or ctx.get("due_date") or "—",
        )


def _finalize_late_payment(ctx: dict[str, Any], fin: dict[str, Any]) -> None:
    """Compare payment_creation_date against due_date to decide APPROVE or REJECT."""
    pmt_field = fin.get("payment_date_field") or "payment_creation_date"
    due_field = fin.get("due_date_field") or "due_date_raw"
    charge_field = fin.get("charge_id_field") or "charge_id"

    pmt_date = ctx.get(pmt_field)
    due_date = ctx.get(due_field)

    if pmt_date is None or due_date is None:
        ctx["decision"] = "MANUAL_REVIEW"
        ctx["escalation_reason"] = "Payment date or due date is null; cannot determine timing."
        ctx["reason_code"] = "MISSING_DATES"
        ctx["audit_notes"] = "Finalize: payment_creation_date or due_date is null."
        return

    if pmt_date <= due_date:
        ctx["payment_on_time"] = True
        ctx["decision"] = "APPROVE"
        ctx["audit_notes"] = (fin.get("approve_audit") or "").format(
            payment_creation_date=_fmt_date(pmt_date) or "—",
            due_date=_fmt_date(due_date) or "—",
            charge_id=ctx.get(charge_field) or "—",
        )
    else:
        ctx["payment_on_time"] = False
        ctx["decision"] = "REJECT"
        ctx["audit_notes"] = (fin.get("reject_audit") or "").format(
            payment_creation_date=_fmt_date(pmt_date) or "—",
            due_date=_fmt_date(due_date) or "—",
            charge_id=ctx.get(charge_field) or "—",
        )


def _apply_date_fields(ctx: dict[str, Any], fields: list[str]) -> None:
    for f in fields:
        if f.endswith("_raw"):
            continue
        if f in ctx and ctx[f] is not None:
            ctx[f] = _fmt_date(ctx[f]) or ctx[f]


def _apply_memo_override(ctx: dict[str, Any], memo_text: str, spec: dict[str, Any]) -> None:
    if not _apply_memo_patterns(memo_text, spec):
        return
    mm = spec.get("memo_manual_review") or {}
    prev = ctx.get("decision")
    ctx["decision"] = "MANUAL_REVIEW"
    ctx["memo_manual_override"] = True
    msg = mm.get("short_explanation_memo") or "Escalate for manual review per policy."
    ctx["escalation_reason"] = f"{msg} (SQL path would have been {prev})." if prev else msg
    base = (ctx.get("audit_notes") or "").strip()
    ctx["audit_notes"] = (base + " " if base else "") + "Memo override: manual review triggers detected."


def _short_explanation(ctx: dict[str, Any], spec: dict[str, Any]) -> str:
    dec = ctx.get("decision") or "MANUAL_REVIEW"
    short = spec.get("short_explanations") or {}
    if ctx.get("memo_manual_override"):
        mm = spec.get("memo_manual_review") or {}
        return mm.get("short_explanation_memo") or short.get("MANUAL_REVIEW", "")
    if dec in short:
        return short[dec]
    esc = (ctx.get("escalation_reason") or "").strip()
    if dec == "MANUAL_REVIEW" and esc and len(esc) < 220:
        return esc
    return short.get("MANUAL_REVIEW", "")


def _customer_lines(ctx: dict[str, Any]) -> tuple[str, str, str]:
    lb = ctx.get("last_bck_payment_date") or "—"
    ex = ctx.get("extract_date") or "—"
    du = ctx.get("due_date") or "—"
    if ctx.get("bck_found") and lb != "—":
        line_bck = f"The bank recorded a direct debit rejection on {lb}."
    else:
        line_bck = "We did not find a bank payment backout (BCK) event for this dispute on your account."
    if ctx.get("dck_found"):
        line_dck = "A rejection fee (DCK) was applied to your account."
    else:
        line_dck = "We did not find a rejection fee (DCK) charge matching this dispute."
    if ex != "—" and du != "—":
        line_cash = f"We looked for a cash payment before the Billing Due Date {du}."
    else:
        line_cash = "We could not confirm the direct debit extract-to-due date window from billing records."
    return line_bck, line_dck, line_cash


def _late_payment_customer_lines(ctx: dict[str, Any]) -> tuple[str, str, str]:
    charge_id = ctx.get("charge_id") or "—"
    balance = ctx.get("balance")
    pmt_date = ctx.get("payment_creation_date") or "—"
    due_date = ctx.get("due_date") or "—"

    if charge_id != "—":
        line_charge = f"A late payment fee (LATE_PYM) was found on charge {charge_id}."
    else:
        line_charge = "We did not find a late payment fee (LATE_PYM) charge for this dispute on your account."

    if balance is not None:
        try:
            bal_val = float(balance)
            if bal_val > 0:
                line_balance = f"Outstanding balance of R {bal_val:,.2f} remains on the account."
            else:
                line_balance = "The account balance is fully settled (zero balance)."
        except (ValueError, TypeError):
            line_balance = f"Account balance: {balance}."
    else:
        line_balance = "We could not determine the account balance from billing records."

    if pmt_date != "—" and due_date != "—":
        line_payment = f"Payment was recorded on {pmt_date}; the billing due date was {due_date}."
    else:
        line_payment = "We could not confirm the payment timing relative to the due date."

    return line_charge, line_balance, line_payment


def _fill_template(tpl: str, facts: dict[str, Any]) -> str:
    out = tpl
    for k, v in facts.items():
        placeholder = "{{" + k + "}}"
        if placeholder in out:
            out = out.replace(placeholder, "" if v is None else str(v))
    return out


def build_grounded_output(ctx: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    """Turn context + spec templates into resolution_summary / recommended_action."""
    templates = spec.get("templates") or {}
    dec = ctx.get("decision") or "MANUAL_REVIEW"

    fin_type = (spec.get("finalize") or {}).get("type", "")
    facts: dict[str, Any] = dict(ctx)
    facts["short_explanation"] = _short_explanation(ctx, spec)
    facts["sql_steps_executed"] = "[" + ", ".join(str(x) for x in (ctx.get("sql_steps_executed") or [])) + "]"
    esc = (ctx.get("escalation_reason") or "").strip()
    aud = (ctx.get("audit_notes") or "").strip()
    facts["escalation_or_audit"] = esc or aud or "—"

    if fin_type == "late_payment_decision":
        line_charge, line_balance, line_payment = _late_payment_customer_lines(ctx)
        facts["payment_after_due_yesno"] = _yes_no(not bool(ctx.get("payment_on_time")))
        facts["line_charge"] = line_charge
        facts["line_balance"] = line_balance
        facts["line_payment"] = line_payment
        for f in ("charge_id", "charge_creation_date", "due_date", "payment_creation_date",
                  "payment_amount", "balance", "restriction_amount", "reason_code",
                  "account_id", "dispute_id"):
            if facts.get(f) is None:
                facts[f] = "—"
    else:
        line_bck, line_dck, line_cash = _customer_lines(ctx)
        facts["bck_yesno"] = _yes_no(bool(ctx.get("bck_found")))
        facts["dck_yesno"] = _yes_no(bool(ctx.get("dck_found")))
        facts["cash_yesno"] = _yes_no(bool(ctx.get("cash_in_window")))
        facts["line_bck"] = line_bck
        facts["line_dck"] = line_dck
        facts["line_cash"] = line_cash
        for f in ("last_bck_payment_date", "dck_effective_date", "extract_date", "due_date", "cash_payment_date", "account_id", "dispute_id"):
            if facts.get(f) is None:
                facts[f] = "—"

    agent = _fill_template(templates.get("agent_summary") or "", facts)
    cust = _fill_template(templates.get("customer_explanation") or "", facts)

    if dec == "APPROVE":
        rec = _fill_template(templates.get("recommended_approve") or "", facts)
    elif dec == "REJECT":
        rec = _fill_template(templates.get("recommended_reject") or "", facts)
    else:
        rec = _fill_template(templates.get("recommended_manual") or "", facts)

    resolution_summary = agent + "\n\n" + cust

    audit_facts = {k: v for k, v in ctx.items() if not str(k).endswith("_raw")}
    return {
        "resolution_summary": resolution_summary,
        "recommended_action": rec,
        "confidence": "high",
        "error": None,
        "sql_grounded": True,
        "sql_evidence": audit_facts,
    }


def fetch_evidence_for_category(conn, dispute_id: int, category: str) -> dict[str, Any]:
    """Run pipeline + finalize from RAG JSON spec."""
    spec = get_grounded_spec_for_category(category)
    if not spec:
        return {"success": False, "error": "no_spec"}
    ctx = _run_pipeline(conn, dispute_id, spec)
    if ctx.get("error") and not ctx.get("success"):
        return ctx

    fin = spec.get("finalize") or {}
    ftype = fin.get("type")
    if ftype == "cash_window_decision" and not ctx.get("decision"):
        _finalize_cash_window(ctx, fin)
    elif ftype == "late_payment_decision" and not ctx.get("decision"):
        _finalize_late_payment(ctx, fin)

    date_fields = spec.get("date_fields") or []
    _apply_date_fields(ctx, date_fields)

    return ctx


def try_grounded_resolution(
    memo_text: str,
    category: str,
    dispute_id: Optional[int],
) -> Optional[dict[str, Any]]:
    """
    If category has a grounded_specs.json entry and DB is available, return deterministic output.
    """
    if not _env_sql_grounded_resolution():
        return None
    if dispute_id is None:
        return None
    spec = get_grounded_spec_for_category(category)
    if not spec:
        return None
    try:
        from .db import is_configured, get_connection
    except ImportError:
        return None
    if not is_configured():
        return None
    try:
        conn = get_connection()
        try:
            ctx = fetch_evidence_for_category(conn, int(dispute_id), category)
        finally:
            conn.close()
    except Exception:
        return None

    if ctx.get("error") and not ctx.get("success"):
        return None

    _apply_memo_override(ctx, memo_text, spec)
    out = build_grounded_output(ctx, spec)
    try:
        from .rag import is_rag_disabled, retrieve

        if not is_rag_disabled():
            q = f"dispute policy excerpt {category} {memo_text[:200]}"
            snippets = retrieve(q, category=category, top_k=2) or ""
            if snippets.strip():
                out["rag_snippets"] = snippets
    except Exception:
        pass
    if _env_grounded_llm_refine():
        out = _refine_grounded_with_llm(
            out,
            ctx,
            memo_text,
            category,
            out.get("rag_snippets") or "",
        )
    return out


def clear_grounded_specs_cache() -> None:
    global _SPECS_CACHE
    _SPECS_CACHE = None
