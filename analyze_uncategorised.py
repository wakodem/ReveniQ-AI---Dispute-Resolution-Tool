"""
Analyze uncategorised disputes: sample memos and word/phrase frequency.
Output: uncategorised_analysis.txt (samples + common terms).
Run: python analyze_uncategorised.py
"""
import re
from pathlib import Path
from collections import Counter

from reveniq_ai.data_loader import load_and_categorise, DEFAULT_CSV_DIR, get_csv_path

# Write to same dir as CSV or cwd
_csv_path = get_csv_path()
OUTPUT_FILE = _csv_path.parent / "uncategorised_analysis.txt"
if not _csv_path.exists():
    OUTPUT_FILE = Path(__file__).resolve().parent / "uncategorised_analysis.txt"


def normalize(t: str) -> str:
    t = (t or "").lower().strip()
    t = re.sub(r"[\r\n\t]+", " ", t)
    t = re.sub(r"[\.,;:!?\-_'\"\/()\[\]]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def main():
    print("Loading and categorising...")
    try:
        df = load_and_categorise()
    except FileNotFoundError:
        # Try current directory
        p = Path(__file__).resolve().parent / "dispute_categorisation_60days.csv"
        if p.exists():
            df = load_and_categorise(csv_path=p)
        else:
            raise
    uncat = df[df["CATEGORY"] == "Uncategorised"]
    n = len(uncat)
    print(f"Uncategorised: {n}")

    lines = []
    lines.append(f"Uncategorised count: {n}\n")
    lines.append("=" * 60 + "\nSample MEMO_TEXT (first 300):\n")

    for i, row in uncat.head(300).iterrows():
        memo = (row.get("MEMO_TEXT") or "").strip()
        if not memo:
            continue
        snippet = memo[:500].replace("\n", " ")
        lines.append(f"\n---\n{snippet}\n")

    lines.append("\n" + "=" * 60 + "\nWord frequency (2- and 3-word phrases, top 150):\n")
    all_text = " ".join(uncat["MEMO_TEXT"].fillna("").astype(str).apply(normalize))
    words = all_text.split()
    two_grams = [" ".join(words[i : i + 2]) for i in range(len(words) - 1) if len(words[i]) > 2]
    three_grams = [" ".join(words[i : i + 3]) for i in range(len(words) - 2) if len(words[i]) > 2]
    cnt = Counter(two_grams + three_grams)
    for phrase, c in cnt.most_common(150):
        if c >= 2 and len(phrase) > 4:
            lines.append(f"  {c:5d}  {phrase}\n")

    out = OUTPUT_FILE
    out.write_text("".join(lines), encoding="utf-8")
    print(f"Written: {out}")


if __name__ == "__main__":
    main()
