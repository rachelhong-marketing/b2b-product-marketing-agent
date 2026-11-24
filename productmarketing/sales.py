"""Sales input: short notes from the people who talk to buyers, tied to a deal so they can be counted by segment.

File: <data>/customers/sales-input.csv with columns deal_id, rep_id, note_type, note, date.
note_type is one of why-won, why-lost, objection, trigger, other. Keep rep ids, not names. Keep notes short."""
from collections import Counter, defaultdict
from pathlib import Path

from .util import read_csv_rows

TYPES = ("why-won", "why-lost", "objection", "trigger", "other")


def load(data):
    p = Path(data) / "customers" / "sales-input.csv"
    return read_csv_rows(p) if p.exists() else []


def by_segment(notes, deals):
    seg_of = {d["deal_id"]: (d["industry"], d["company_size"]) for d in deals}
    out = defaultdict(lambda: dict(n=0, types=Counter(), examples=[], reps=set()))
    for nt in notes:
        seg = seg_of.get(nt.get("deal_id", ""))
        if not seg:
            continue
        o = out[seg]
        o["n"] += 1
        o["types"][nt.get("note_type", "other")] += 1
        o["reps"].add(nt.get("rep_id", ""))
        if len(o["examples"]) < 2:
            o["examples"].append(nt.get("note", ""))
    return out
