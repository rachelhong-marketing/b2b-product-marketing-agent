"""The product marketer's decision record for the ideal customer profile.

File: <data>/decisions/icp-decisions.csv with columns segment, decision, decided_by, date, note.
decision is confirmed, rejected or watch. The agent never writes a decision on its own: `decide` records one only when a named person gives it.
Until at least one segment is confirmed, everything downstream says the ICP is a DRAFT."""
import csv
from datetime import date
from pathlib import Path

VALID = ("confirmed", "rejected", "watch")
FIELDS = ["segment", "decision", "decided_by", "date", "note"]


def path(data):
    return Path(data) / "decisions" / "icp-decisions.csv"


def load(data):
    """Latest row per segment wins."""
    p = path(data)
    if not p.exists():
        return {}
    with open(p, newline="", encoding="utf-8") as fh:
        rows = [{k: (v or "").strip() for k, v in r.items()} for r in csv.DictReader(fh)]
    return {r["segment"].lower(): r for r in rows if r.get("segment") and r.get("decision", "").lower() in VALID}


def label(s):
    return f"{s['industry']}, {s['size']}"


def of(decisions, segment_label):
    return decisions.get(segment_label.lower())


def status(decisions):
    return "CONFIRMED" if any(r["decision"].lower() == "confirmed" for r in decisions.values()) else "DRAFT"


def add(data, segment, decision, decided_by, note="", on=None):
    if decision.lower() not in VALID:
        raise ValueError(f"decision must be one of: {', '.join(VALID)}")
    if not (decided_by or "").strip():
        raise ValueError("a named person must make the decision (decided_by is empty)")
    if not (segment or "").strip():
        raise ValueError("segment is empty")
    p = path(data)
    p.parent.mkdir(parents=True, exist_ok=True)
    new = not p.exists()
    with open(p, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow(dict(segment=segment.strip(), decision=decision.lower(), decided_by=decided_by.strip(), date=on or date.today().isoformat(), note=note.strip()))
