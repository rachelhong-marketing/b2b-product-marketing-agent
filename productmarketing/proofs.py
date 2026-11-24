"""The proof-point register: every number or result you may use in copy, with its source, who approved it and when it expires.

File: <data>/company/proof-points.csv with columns id, type, text, source, approved_by, approved_on, expires_on, notes.
A proof point is usable only if it has a source, an approver and approval date, and has not expired. A claim needs at least 2 usable proof points to be a pillar."""
from datetime import date, timedelta
from pathlib import Path

from .util import read_csv_rows

SOON_DAYS = 60


def load(data):
    p = Path(data) / "company" / "proof-points.csv"
    return read_csv_rows(p) if p.exists() else []


def _d(s):
    try:
        return date.fromisoformat(s)
    except (TypeError, ValueError):
        return None


def status(p, as_of):
    """Returns (state, reason). state is 'valid' or 'unusable'."""
    if not p.get("source"):
        return "unusable", "no source"
    if not p.get("approved_by") or not p.get("approved_on"):
        return "unusable", "not approved"
    exp = p.get("expires_on", "")
    if exp:
        e = _d(exp)
        if e is None:
            return "unusable", "expiry date is not valid (use YYYY-MM-DD)"
        if as_of > e:
            return "unusable", f"expired {exp}"
        if as_of + timedelta(days=SOON_DAYS) >= e:
            return "valid", f"expires soon ({exp})"
        return "valid", f"valid until {exp}"
    return "valid", "no expiry set"


def index(proofs, as_of):
    out = {}
    for p in proofs:
        st, why = status(p, as_of)
        out[p["id"]] = dict(p, state=st, reason=why)
    return out


def register_lines(idx, used_by):
    L = ["| Ref | Proof | Type | Source | Approved by | Status | Used by |", "|---|---|---|---|---|---|---|"]
    for pid, p in idx.items():
        used = ", ".join(used_by.get(pid, [])) or "none yet"
        L.append(f"| {pid} | {p['text']} | {p.get('type', '')} | {p.get('source') or '[MISSING]'} | {p.get('approved_by') or 'not approved'} | "
                 f"{'usable' if p['state'] == 'valid' else 'Not usable'}: {p['reason']} | {used} |")
    return L
