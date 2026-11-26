"""Small shared helpers. Standard library only."""
import csv
import re


def read_csv_rows(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return [{k.strip(): (v or "").strip() for k, v in row.items() if k} for row in csv.DictReader(fh)]


def to_number(v):
    s = re.sub(r"[,$\s]", "", str(v or ""))
    try:
        return float(s)
    except ValueError:
        return None


def has_phrase(text, phrase):
    return re.search(r"\b" + re.escape(phrase.lower()) + r"\b", (text or "").lower()) is not None


def minmax(values):
    """Scale to 0..1 across the given values. A single value, or all equal, scales to 0.5."""
    vals = [v for v in values if v is not None]
    if not vals or max(vals) == min(vals):
        return lambda v: 0.5
    lo, hi = min(vals), max(vals)
    return lambda v: (v - lo) / (hi - lo)


def slug(text, n=60):
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s if len(s) <= n else s[:n].rsplit("-", 1)[0]
