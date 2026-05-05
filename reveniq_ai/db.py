"""
Oracle DB connection for ReveniQ AI (required-action rules).
Credentials from environment variables; do not hardcode passwords.
Digital COE Gen AI Team
"""

import os
from pathlib import Path
from typing import Optional, Any

# Project root - load .env from here
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
try:
    from dotenv import load_dotenv
    _env_path = _PROJECT_ROOT / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
except ImportError:
    pass

# DB config from environment (set in .env or shell)
REVENIQ_DB_USER = os.environ.get("REVENIQ_DB_USER", "").strip()
REVENIQ_DB_PASSWORD = os.environ.get("REVENIQ_DB_PASSWORD", "").strip()
REVENIQ_DB_HOST = os.environ.get("REVENIQ_DB_HOST", "").strip()
REVENIQ_DB_PORT = os.environ.get("REVENIQ_DB_PORT", "1521").strip()
REVENIQ_DB_SID = os.environ.get("REVENIQ_DB_SID", "").strip()
# Use thick mode (Oracle Instant Client) if server uses verifier not supported by thin (e.g. DPY-3015)
REVENIQ_DB_USE_THICK = os.environ.get("REVENIQ_DB_USE_THICK", "").strip().lower() in ("1", "true", "yes")

_thick_init_done = False


def _ensure_oracle_client():
    """Initialize Oracle thick mode once if REVENIQ_DB_USE_THICK is set."""
    global _thick_init_done
    if not _thick_init_done and REVENIQ_DB_USE_THICK:
        import oracledb
        lib_dir = os.environ.get("REVENIQ_DB_ORACLE_HOME", "").strip() or None
        oracledb.init_oracle_client(lib_dir=lib_dir)
        _thick_init_done = True


def get_dsn() -> str:
    """Build DSN for Oracle (host:port/sid)."""
    if not REVENIQ_DB_HOST or not REVENIQ_DB_SID:
        return ""
    return f"{REVENIQ_DB_HOST}:{REVENIQ_DB_PORT}/{REVENIQ_DB_SID}"


def is_configured() -> bool:
    """Return True if DB credentials are set (password can be empty for external auth)."""
    return bool(REVENIQ_DB_USER and REVENIQ_DB_HOST and REVENIQ_DB_SID)


def get_connection():
    """
    Return a new Oracle connection. Caller must close it.
    Requires: oracledb, and REVENIQ_DB_* env vars set.
    If REVENIQ_DB_USE_THICK=1, uses Oracle Instant Client (needed for DPY-3015).
    """
    import oracledb
    _ensure_oracle_client()
    dsn = get_dsn()
    if not dsn or not REVENIQ_DB_USER:
        raise ValueError(
            "Oracle DB not configured. Set REVENIQ_DB_USER, REVENIQ_DB_HOST, REVENIQ_DB_SID (and REVENIQ_DB_PASSWORD) in .env"
        )
    return oracledb.connect(
        user=REVENIQ_DB_USER,
        password=REVENIQ_DB_PASSWORD,
        dsn=dsn,
    )


def test_connection() -> tuple[bool, str]:
    """
    Try to connect and run SELECT 1 FROM DUAL. Returns (success, message).
    """
    if not is_configured():
        return False, "DB not configured: set REVENIQ_DB_USER, REVENIQ_DB_HOST, REVENIQ_DB_SID in .env"
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM DUAL")
                cur.fetchone()
        finally:
            conn.close()
        return True, "Connection successful."
    except Exception as e:
        return False, str(e)
