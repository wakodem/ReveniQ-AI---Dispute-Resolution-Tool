"""
Export all uncategorised disputes to Excel (with MEMO_TEXT).
Run from project root: python export_uncategorised.py
Digital COE Gen AI Team
"""

from pathlib import Path

from reveniq_ai.data_loader import load_and_categorise, DEFAULT_CSV_DIR

OUTPUT_FILENAME = "uncategorised_disputes.xlsx"


def main():
    print("Loading and categorising disputes...")
    df = load_and_categorise()
    uncat = df[df["CATEGORY"] == "Uncategorised"].copy()
    n = len(uncat)
    print(f"Found {n:,} uncategorised disputes.")

    out_path = Path(DEFAULT_CSV_DIR) / OUTPUT_FILENAME
    cols = [
        "DISPUTE_ID",
        "STATUS",
        "SYS_CREATION_DATE",
        "AMOUNT",
        "TAX_AMOUNT",
        "CREDIT_LEVEL_CODE",
        "CHARGE_CODE",
        "MEMO_TEXT",
        "CATEGORY",
        "CONFIDENCE_SCORE",
    ]
    uncat = uncat[[c for c in cols if c in uncat.columns]]

    print(f"Writing to {out_path}...")
    uncat.to_excel(out_path, index=False, engine="openpyxl")
    print(f"Done. Excel saved: {out_path}")


if __name__ == "__main__":
    main()
