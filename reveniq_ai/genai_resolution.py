"""
GenAI-based dispute resolution and action recommendation via Ollama (local).
Digital COE Gen AI Team
"""

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any, Optional

try:
    from dotenv import load_dotenv
    from pathlib import Path
    _root = Path(__file__).resolve().parent.parent
    load_dotenv(_root / ".env")
except Exception:
    pass


def is_configured() -> bool:
    """True when local Ollama can be used (no API key required)."""
    return True


DEFAULT_RESPONSE = {
    "resolution_summary": "AI recommendation not available.",
    "recommended_action": "Review dispute manually.",
    "confidence": "low",
    "error": None,
}


def _ollama_timeout() -> int:
    """HTTP wait for Ollama /api/generate (seconds). Override with OLLAMA_TIMEOUT_SECONDS."""
    try:
        return max(60, int(os.environ.get("OLLAMA_TIMEOUT_SECONDS", "600")))
    except ValueError:
        return 600


def get_ollama_parallel_workers() -> int:
    try:
        n = int(os.environ.get("OLLAMA_PARALLEL_WORKERS", "4"))
        return max(1, min(8, n))
    except ValueError:
        return 4


def _ollama_temperature() -> Optional[float]:
    """Optional Ollama sampling temperature from OLLAMA_TEMPERATURE."""
    raw = os.environ.get("OLLAMA_TEMPERATURE")
    if raw is None or not str(raw).strip():
        return None
    try:
        v = float(raw)
        return max(0.0, min(2.0, v))
    except ValueError:
        return None


def _ollama_seed() -> Optional[int]:
    """Optional Ollama deterministic seed from OLLAMA_SEED."""
    raw = os.environ.get("OLLAMA_SEED")
    if raw is None or not str(raw).strip():
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _ollama_top_p() -> Optional[float]:
    """Nucleus sampling from OLLAMA_TOP_P (0.0–1.0). Omit from request if unset."""
    raw = os.environ.get("OLLAMA_TOP_P")
    if raw is None or not str(raw).strip():
        return None
    try:
        v = float(raw)
        return max(0.0, min(1.0, v))
    except ValueError:
        return None


def _ollama_top_k() -> Optional[int]:
    """Top-k token cap from OLLAMA_TOP_K (>=1). Omit from request if unset."""
    raw = os.environ.get("OLLAMA_TOP_K")
    if raw is None or not str(raw).strip():
        return None
    try:
        v = int(raw)
        return max(1, v)
    except ValueError:
        return None


def _call_ollama(prompt: str, model: str, base_url: str, timeout: Optional[int] = None) -> str:
    if timeout is None:
        timeout = _ollama_timeout()
    url = f"{base_url.rstrip('/')}/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": False}
    options = {}
    temp = _ollama_temperature()
    seed = _ollama_seed()
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
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return (data.get("response") or "").strip()


def _parse_ai_response(text: str) -> dict[str, Any]:
    if not text:
        raise ValueError("Empty response")
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```\s*$", "", text)
    data = json.loads(text)
    return {
        "resolution_summary": data.get("resolution_summary", DEFAULT_RESPONSE["resolution_summary"]),
        "recommended_action": data.get("recommended_action", DEFAULT_RESPONSE["recommended_action"]),
        "confidence": data.get("confidence", "medium"),
        "error": None,
    }


def _looks_like_approve_action(text: str) -> bool:
    t = (text or "").strip().lower()
    if not t:
        return False
    if "do not approve" in t or "recommendation: do not" in t:
        return False
    return t.startswith("recommendation: approve") or t.startswith("approve") or " approve" in t[:40]


def _looks_like_reject_action(text: str) -> bool:
    t = (text or "").strip().lower()
    return "do not approve" in t or "recommendation: do not" in t or t.startswith("reject")


def _append_rule_alignment_to_summary(resolution_summary: str, rule_outcome: str) -> str:
    """Append a single authoritative line so the narrative matches the action column after override."""
    body = (resolution_summary or "").rstrip()
    footer = (
        "\n\n---\n**Final recommendation (aligned with rule engine):** "
        + (rule_outcome or "").strip()
    )
    if "**Final recommendation (aligned with rule engine):**" in body:
        return body
    return body + footer


def _apply_rule_override(out: dict[str, Any], rule_outcome: Optional[str]) -> dict[str, Any]:
    """
    If the model contradicts the deterministic rule outcome, force recommended_action to the rule.
    Also extend resolution_summary so it does not still say Approve while the action says Do not approve.
    """
    if not rule_outcome or not (out.get("recommended_action") or "").strip():
        return out
    r = (rule_outcome or "").strip().lower()
    a = (out.get("recommended_action") or "").strip().lower()
    rule_line = (rule_outcome or "").strip()
    summary = out.get("resolution_summary") or ""

    mismatch = False
    # Rule says do not approve — model said approve (or similar)
    if "do not approve" in r or "recommendation: do not" in r:
        if _looks_like_approve_action(a):
            mismatch = True
    # Rule says approve — model said do not approve
    elif "recommendation: approve" in r or r.rstrip(".") == "approve":
        if _looks_like_reject_action(a):
            mismatch = True

    if not mismatch:
        return out

    new_summary = _append_rule_alignment_to_summary(summary, rule_line)
    return {
        **out,
        "recommended_action": rule_line,
        "resolution_summary": new_summary,
        "rule_override_applied": True,
    }


def get_ai_resolution(
    memo_text: str,
    category: str,
    rule_outcome: Optional[str] = None,
    dispute_id: Optional[int] = None,
    amount: Optional[float] = None,
    status: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get resolution summary and recommended action for a dispute.

    When a category is defined in docs/rag/grounded_specs.json and DB is configured, uses
    SQL evidence and templates from that file (no LLM) if REVENIQ_SQL_GROUNDED_RESOLUTION is
    enabled — avoids hallucinated dates and misaligned actions. Otherwise uses Ollama + RAG.

    When rule_outcome is None (REVENIQ_AI_USE_RULE_OUTCOME=0), AI uses only RAG doc + memo.
    """
    memo = (memo_text or "").strip()[:2000]
    if not memo:
        return {
            "resolution_summary": "No memo text provided.",
            "recommended_action": "Review dispute manually.",
            "confidence": "low",
            "error": None,
        }
    try:
        from .grounded_resolution import try_grounded_resolution

        grounded = try_grounded_resolution(memo, category, dispute_id)
    except ImportError:
        grounded = None
    if grounded is not None:
        return grounded

    rule_line = f"Rule outcome (if any): {rule_outcome}" if rule_outcome else "Rule outcome: None. Base your recommendation only on the policy/guidance and memo below."
    amount_line = f"Amount: R {amount:,.2f}" if amount is not None else ""
    status_line = f"Status: {status}" if status else ""
    dispute_line = f"Dispute ID: {dispute_id}" if dispute_id is not None else ""

    rag_snippets_used = ""
    rag_block = ""
    try:
        from .rag import is_rag_disabled, is_rag_enabled, retrieve

        if is_rag_disabled():
            rag_block = ""
        elif not is_rag_enabled():
            return {
                "resolution_summary": "RAG knowledge base folder is missing or invalid.",
                "recommended_action": "Create the folder docs/rag (or set REVENIQ_RAG_DOCS_DIR) with at least one .txt or .md policy file.",
                "confidence": "low",
                "error": "Mandatory RAG: configure docs/rag. Or set REVENIQ_RAG_DISABLED=1 only for local testing without policy retrieval.",
            }
        else:
            rag_snippets_used = retrieve(memo, category=category, top_k=3) or ""
            if not (rag_snippets_used or "").strip():
                return {
                    "resolution_summary": "RAG is required but no policy snippets could be retrieved.",
                    "recommended_action": "Add searchable policy text under docs/rag, run ollama pull nomic-embed-text and ollama serve, then retry.",
                    "confidence": "low",
                    "error": "Mandatory RAG: empty retrieval. Ensure .txt/.md content exists and Ollama embedding (OLLAMA_EMBED_MODEL) is reachable.",
                }
            rag_block = "\n\n" + rag_snippets_used + "\n\n"
    except Exception as e:
        return {
            "resolution_summary": "RAG retrieval failed.",
            "recommended_action": "Check docs/rag, Ollama, and OLLAMA_EMBED_MODEL.",
            "confidence": "low",
            "error": f"Mandatory RAG: {e}",
        }

    rule_instruction = ""
    if rule_outcome and str(rule_outcome).strip():
        if "do not approve" in str(rule_outcome).lower() or "recommendation: do not" in str(rule_outcome).lower():
            rule_instruction = "\nImportant: The rule outcome above says DO NOT APPROVE. Your recommended_action MUST be Do not approve (use the same or similar reason from the rule). Do NOT recommend Approve.\n"
        else:
            rule_instruction = "\nImportant: Your recommended_action MUST align with the rule outcome above. Do not contradict it.\n"

    category_grounding = ""
    cat_stripped = (category or "").strip()
    if cat_stripped == "Rejection Fee Dispute":
        category_grounding = """
GROUNDING (mandatory for this category): SQL-backed evidence was not available for this request.
- Do NOT invent dates, payment amounts, charge codes, or account events that are not explicitly stated in the memo or rule outcome line below.
- Your resolution_summary must not claim specific calendar dates unless they appear in the memo text or rule outcome.
- Your recommended_action MUST be operationally consistent with resolution_summary and with any rule outcome line (approve vs do not approve).
- If details are missing, state that manual review is needed rather than fabricating facts.
"""
    elif cat_stripped == "Late Payment / Interest Dispute":
        category_grounding = """
GROUNDING (mandatory for this category): SQL-backed evidence was not available for this request.
- This dispute is about a late payment fee (charge_code = 'LATE_PYM'). The key question is whether the payment was received on or before the billing due date.
- Do NOT invent dates, payment amounts, charge IDs, balances, or account events that are not explicitly stated in the memo or rule outcome line below.
- Your resolution_summary must not claim specific calendar dates unless they appear in the memo text or rule outcome.
- Your recommended_action MUST be operationally consistent with resolution_summary and with any rule outcome line (approve vs do not approve).
- If details are missing, state that manual review is needed rather than fabricating facts.
"""

    prompt = f"""You are a dispute resolution expert for a telco/billing operations team. Based on the dispute details below, provide a short resolution summary and a clear recommended action. Do not invent facts; base your answer only on the provided text, any rule outcome (if given), and any relevant policy/guidance below.
{category_grounding}
{rag_block}
Dispute category: {category}
{dispute_line}
{status_line}
{amount_line}
{rule_line}
{rule_instruction}
Memo text:
{memo}

Respond with a single JSON object only (no markdown, no extra text), with exactly these keys:
- "resolution_summary": 1-3 sentences describing what the dispute is about and how to resolve it (or what to tell the customer). If a rule outcome line is provided above, the resolution_summary MUST end with the same approve/reject stance as that rule (never conclude Approve when the rule says Do not approve).
- "recommended_action": One line recommendation. If a rule outcome says "Do not approve", your recommended_action MUST be Do not approve (repeat or paraphrase the rule reason). If the rule outcome says "Recommendation: Approve", you may recommend Approve. Never recommend Approve when the rule says Do not approve. If no rule outcome is given, use only the policy/guidance and memo above.
- "confidence": One of "high", "medium", "low".

Example format:
{{"resolution_summary": "...", "recommended_action": "Recommendation: ...", "confidence": "high"}}
"""

    base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").strip()
    model = (os.environ.get("OLLAMA_MODEL") or "llama3.2").strip() or "llama3.2"
    try:
        text = _call_ollama(prompt, model, base_url)
        out = _parse_ai_response(text)
        out = _apply_rule_override(out, rule_outcome)
        if rag_snippets_used:
            out["rag_snippets"] = rag_snippets_used
        return out
    except json.JSONDecodeError as e:
        return {
            "resolution_summary": "Could not parse AI response.",
            "recommended_action": "Review dispute manually.",
            "confidence": "low",
            "error": f"Parse error: {e}",
        }
    except urllib.error.URLError as e:
        err_msg = str(e).lower()
        if "timed out" in err_msg or "timeout" in err_msg:
            return {
                "resolution_summary": "Ollama request timed out.",
                "recommended_action": "Review dispute manually.",
                "confidence": "low",
                "error": f"Timed out. Try fewer rows or set OLLAMA_TIMEOUT_SECONDS=600. {e}",
            }
        return {
            "resolution_summary": "Ollama not reachable.",
            "recommended_action": "Review dispute manually.",
            "confidence": "low",
            "error": f"Start Ollama and run: ollama run {model}. {e}",
        }
    except Exception as e:
        return {
            "resolution_summary": "AI recommendation failed.",
            "recommended_action": "Review dispute manually.",
            "confidence": "low",
            "error": str(e),
        }
