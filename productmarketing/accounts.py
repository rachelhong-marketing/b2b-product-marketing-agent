"""The target account list: what its accounts have in common, and how it compares with who you actually win.

Caution built into the output: a target list reflects how the list was BUILT (the filters sales operations used), so a pattern
in it is not proof of buyer fit. Compare it with wins before trusting it. These are hypotheses for the product marketer to decide."""
from collections import Counter
from pathlib import Path

from .util import read_csv_rows

MIN_LIST = 10      # a list shorter than this is too small to show patterns
COMMON_SHARE = 0.30


def load(data):
    p = Path(data) / "accounts" / "target-accounts.csv"
    return read_csv_rows(p) if p.exists() else []


def _split(v):
    return [x.strip() for x in (v or "").split(";") if x.strip()]


def patterns(accts):
    """For each field, values with their count and share of accounts. Multi-valued fields are split on ';'."""
    n = len(accts)
    out = {}
    for field, multi in (("industry", False), ("company_size", False), ("region", False), ("tech_stack", True), ("intent_topics", True)):
        c = Counter()
        for a in accts:
            for v in (_split(a.get(field)) if multi else [a.get(field, "").strip()]):
                if v:
                    c[v] += 1
        out[field] = [(v, k, k / n) for v, k in c.most_common(5)] if n else []
    return out


def common(accts):
    """Values shared by at least 30 percent of accounts, if the list is big enough to say anything."""
    if len(accts) < MIN_LIST:
        return []
    return [(f, v, k, s) for f, vals in patterns(accts).items() for v, k, s in vals if s >= COMMON_SHARE]


def segment_counts(accts):
    return Counter((a.get("industry", ""), a.get("company_size", "")) for a in accts)


def compare_with_wins(segs, accts):
    """Two warnings: segments on the list with no wins, and segments with wins that the list barely covers."""
    counts = segment_counts(accts)
    by = {(s["industry"], s["size"]): s for s in segs}
    no_wins, wins_off_list = [], []
    for (ind, size), n in counts.most_common():
        s = by.get((ind, size))
        won = s["won"] if s else 0
        deals = s["deals"] if s else 0
        if n >= 5 and won == 0:
            no_wins.append(dict(segment=f"{ind}, {size}", accounts=n, deals=deals))
    for s in segs:
        n = counts.get((s["industry"], s["size"]), 0)
        if s["won"] >= 3 and n < 3:
            wins_off_list.append(dict(segment=f"{s['industry']}, {s['size']}", wins=s["won"], accounts=n))
    return no_wins, wins_off_list
