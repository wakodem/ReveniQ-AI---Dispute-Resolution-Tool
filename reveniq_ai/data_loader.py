"""
Load dispute CSV from local path and apply categorisation.
CSV path is configurable via environment variables or .env file.
Digital COE Gen AI Team
"""

import os
from pathlib import Path
from typing import Optional

import pandas as pd

from .categories import categorize_memo

# Project root (parent of reveniq_ai package)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load .env from project root if python-dotenv is available
try:
    from dotenv import load_dotenv
    _env_path = _PROJECT_ROOT / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
except ImportError:
    pass

# CSV path: REVENIQ_CSV_DIR (directory), REVENIQ_CSV_FILENAME (filename)
# Default dir = project root; default filename = dispute_categorisation_60days.csv
DEFAULT_CSV_DIR = Path(os.environ.get("REVENIQ_CSV_DIR", str(_PROJECT_ROOT)))
CSV_FILENAME = os.environ.get("REVENIQ_CSV_FILENAME", "dispute_categorisation_60days.csv")


def get_csv_path(csv_dir: Optional[str] = None, filename: Optional[str] = None) -> Path:
    """Resolve directory and CSV path."""
    base = Path(csv_dir) if csv_dir else DEFAULT_CSV_DIR
    name = filename or CSV_FILENAME
    return base / name


def load_and_categorise(
    csv_path: Optional[Path] = None,
    csv_dir: Optional[str] = None,
    filename: Optional[str] = None,
) -> pd.DataFrame:
    """
    Read dispute CSV from local machine and add CATEGORY column from MEMO_TEXT.
    Handles multi-line memo fields (quoted CSV).
    """
    path = csv_path or get_csv_path(csv_dir=csv_dir, filename=filename)
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")

    # Try encodings that handle common non-UTF-8 bytes (e.g. 0xa0 = non-breaking space)
    encodings = ["utf-8", "cp1252", "latin-1", "iso-8859-1"]
    last_error = None
    for encoding in encodings:
        try:
            df = pd.read_csv(
                path,
                encoding=encoding,
                dtype={
                    "DISPUTE_ID": "Int64",
                    "STATUS": "string",
                    "SYS_CREATION_DATE": "string",
                    "TAX_AMOUNT": "float",
                    "CREDIT_LEVEL_CODE": "string",
                    "CHARGE_CODE": "string",
                    "MEMO_TEXT": "string",
                },
                quoting=1,  # QUOTE_ALL
                on_bad_lines="warn",
            )
            break
        except UnicodeDecodeError as e:
            last_error = e
            continue
    else:
        if last_error:
            raise last_error

    # Normalise column names (strip whitespace; handle .AMOUNT -> AMOUNT)
    df.columns = df.columns.str.strip()
    if ".AMOUNT" in df.columns and "AMOUNT" not in df.columns:
        df = df.rename(columns={".AMOUNT": "AMOUNT"})
    if "AMOUNT" in df.columns:
        df["AMOUNT"] = pd.to_numeric(df["AMOUNT"], errors="coerce")

    if "MEMO_TEXT" not in df.columns:
        raise ValueError("CSV must contain column MEMO_TEXT")

    # Apply categorization with confidence scores (single pass over memos)
    categorization_results = df["MEMO_TEXT"].apply(categorize_memo)
    df["CATEGORY"] = [r[0] for r in categorization_results]
    df["CONFIDENCE_SCORE"] = [r[1] for r in categorization_results]

    # Required Action: vectorized (no DB at load). No row-by-row apply.
    _pending_db = "Outcome pending – DB check required."
    _pending_did = "Outcome pending – Dispute ID required for rule."
    _default = "Review dispute and apply standard resolution or escalate."
    is_rejection_fee = (df["CATEGORY"] == "Rejection Fee Dispute")
    is_late_payment = (df["CATEGORY"] == "Late Payment / Interest Dispute")
    has_rule_category = is_rejection_fee | is_late_payment
    has_did = df["DISPUTE_ID"].notna()
    df["REQUIRED_ACTION"] = _default
    df.loc[has_rule_category & ~has_did, "REQUIRED_ACTION"] = _pending_did
    df.loc[has_rule_category & has_did, "REQUIRED_ACTION"] = _pending_db

    return df
