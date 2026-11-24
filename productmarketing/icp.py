"""Ideal customer profile (ICP) from your closed deals: which segments you win, keep and close fastest.

A segment is an industry plus a company size band. It needs at least MIN_DEALS closed deals and MIN_WON wins to be ranked, so a lucky win
in a tiny group does not become your target. Scores compare segments within one run. They are not forecasts."""
from collections import Counter, defaultdict

from .util import minmax, to_number

MIN_DEALS = 5
MIN_WON = 3
W = dict(win_rate=0.35, acv=0.25, speed=0.20, retention=0.20)


def segments(deals):
    groups = defaultdict(list)
    for d in deals:
        groups[(d["industry"], d["company_size"])].append(d)
    out = []
    for (ind, size), ds in groups.items():
        won = [d for d in ds if d["outcome"].lower() == "won"]
        acvs = [to_number(d["acv"]) for d in won if to_number(d["acv"]) is not None]
        days = [to_number(d["days_to_close"]) for d in won if to_number(d["days_to_close"]) is not None]
        kept = [d["retained_12m"].lower() for d in won if d.get("retained_12m", "").lower() in ("yes", "no")]
        out.append(dict(industry=ind, size=size, deals=len(ds), won=len(won), win_rate=len(won) / len(ds),
                        acv=sum(acvs) / len(acvs) if acvs else None, days=sum(days) / len(days) if days else None,
                        retention=kept.count("yes") / len(kept) if kept else None, retention_n=len(kept), rankable=len(ds) >= MIN_DEALS and len(won) >= MIN_WON))
    ok = [s for s in out if s["rankable"]]
    sa, sd = minmax([s["acv"] for s in ok]), minmax([s["days"] for s in ok])
    for s in ok:
        parts = dict(win_rate=s["win_rate"], acv=sa(s["acv"]) if s["acv"] is not None else 0.0,
                     speed=1 - sd(s["days"]) if s["days"] is not None else 0.0, retention=s["retention"] if s["retention"] is not None else 0.5)
        s["score"] = round(100 * sum(W[k] * v for k, v in parts.items()), 1)
    return sorted(out, key=lambda s: (not s["rankable"], -(s.get("score") or 0), -s["deals"]))


def personas(deals, top=3):
    c = Counter(d["buyer_role"] for d in deals if d["outcome"].lower() == "won" and d["buyer_role"])
    return c.most_common(top)


def lost_reasons(deals, top=4):
    c = Counter(d["lost_reason"] for d in deals if d["outcome"].lower() == "lost" and d["lost_reason"])
    return c.most_common(top)


def lost_competitors(deals):
    c = Counter(d["competitor"] for d in deals if d["outcome"].lower() == "lost" and d["competitor"] and d["competitor"].lower() != "none")
    return c.most_common()


def table_lines(segs):
    L = ["| Segment | Closed deals | Win rate | Average contract value | Days to close | 12-month retention | Score | Note |", "|---|---|---|---|---|---|---|---|"]
    for s in segs:
        note = ""
        if s["deals"] < MIN_DEALS:
            note = f"too few deals (under {MIN_DEALS}); not ranked"
        elif s["won"] < MIN_WON:
            note = f"too few wins (under {MIN_WON}); not ranked"
        if s["rankable"] and s["retention"] is None and s["won"]:
            note = "retention [MISSING]"
        if s["rankable"] and s["retention_n"] and s["retention_n"] < 3:
            note = (note + "; " if note else "") + "retention from under 3 customers"
        none = "n/a (no wins)" if s["won"] == 0 else "[MISSING]"
        L.append(f"| {s['industry']}, {s['size']} employees | {s['deals']} | {100 * s['win_rate']:.0f}% | "
                 f"{'$' + format(s['acv'], ',.0f') if s['acv'] else none} | {format(s['days'], '.0f') if s['days'] else none} | "
                 f"{'%.0f%%' % (100 * s['retention']) if s['retention'] is not None else none} | {s.get('score', '')} | {note} |")
    return L
