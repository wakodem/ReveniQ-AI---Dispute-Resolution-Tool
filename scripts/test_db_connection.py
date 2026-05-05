"""
Test Oracle DB connection and Rejection Fee rule (AI-generated SQL from RAG).
Run from project root: python scripts/test_db_connection.py [dispute_id]
Uses .env for REVENIQ_DB_* (copy .env.example to .env and set password).
Requires Ollama + RAG for rule outcome when dispute_id is provided.
Digital COE Gen AI Team
"""

import sys
from pathlib import Path

# Add project root so reveniq_ai is importable
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Load .env from project root
_env = ROOT / ".env"
if _env.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env)
    except ImportError:
        pass


def main():
    from reveniq_ai.db import test_connection, get_connection, is_configured
    from reveniq_ai.ai_sql_runner import get_rule_outcome_via_ai_sql

    print("ReveniQ AI – Oracle DB connection test")
    print("=" * 50)

    if not is_configured():
        print("DB not configured. Set in .env:")
        print("  REVENIQ_DB_USER, REVENIQ_DB_PASSWORD, REVENIQ_DB_HOST, REVENIQ_DB_PORT, REVENIQ_DB_SID")
        return 1

    ok, msg = test_connection()
    if not ok:
        print("Connection failed:", msg)
        if "DPY-3015" in msg:
            print("  -> Use thick mode: set REVENIQ_DB_USE_THICK=1 in .env and install Oracle Instant Client.")
        if "DPI-1047" in msg or "Cannot locate" in msg:
            print("  -> Install Oracle Instant Client 64-bit and add to PATH or set REVENIQ_DB_ORACLE_HOME.")
        print("  See docs/DB_SETUP.md for details.")
        return 1
    print("Connection:", msg)

    dispute_id_arg = sys.argv[1] if len(sys.argv) > 1 else None
    dispute_id = None
    if dispute_id_arg:
        try:
            dispute_id = int(dispute_id_arg)
        except ValueError:
            print("Invalid dispute_id (use integer):", dispute_id_arg)
            return 1

    if dispute_id is not None:
        print()
        print("Running Rejection Fee rule (AI SQL from RAG) for dispute_id =", dispute_id)
        print("-" * 50)
        try:
            conn = get_connection()
            try:
                result = get_rule_outcome_via_ai_sql(conn, dispute_id, category="Rejection Fee Dispute")
                for d in result.get("details", []):
                    print(" ", d)
                if result.get("error"):
                    print("Error:", result["error"])
                if result.get("outcome"):
                    print("Outcome:", result["outcome"])
                print("Success:", result.get("success", False))
            finally:
                conn.close()
        except Exception as e:
            print("Rule run failed:", e)
            return 1
    else:
        print()
        print("Optional: run rule for a dispute: python scripts/test_db_connection.py <dispute_id>")
        print("Example: python scripts/test_db_connection.py 1234567")
        print("(Requires Ollama + RAG docs for AI-generated SQL.)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
