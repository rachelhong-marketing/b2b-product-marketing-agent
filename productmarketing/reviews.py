"""Post-launch review: goals against results, one section per launch.

File: <data>/launches/launch-results.csv with columns launch_id, goal_metric, goal_value, actual_value, direction, measured_on, source, notes.
direction is higher (more is better, the default) or lower. Results are what was measured, not proof that the launch caused them."""
from datetime import date
from pathlib import Path

from . import launches
from .util import read_csv_rows, to_number


def load(data):
    p = Path(data) / "launches" / "launch-results.csv"
    return read_csv_rows(p) if p.exists() else []


def status(goal, actual, direction):
    if goal is None or actual is None:
        return "no result yet", None
    if direction == "lower":
        pct = goal / actual if actual else None
        return ("met" if actual <= goal else "partly met" if actual <= 1.5 * goal else "missed"), pct
    pct = actual / goal if goal else None
    return ("met" if pct is not None and pct >= 1 else "partly met" if pct is not None and pct >= 0.5 else "missed"), pct


def render(ctx, launch_rows, results, decisions):
    by = {}
    for r in results:
        by.setdefault(r["launch_id"], []).append(r)
    L = ["# Post-launch review", "", f"Prepared as of {ctx['as_of'].isoformat()}. Goals against results. A result is what was measured. It is not proof that the launch caused it.", ""]
    if not launch_rows:
        return "\n".join(L + ["[MISSING] no launches provided (launches/launch-requests.csv)."])
    shown = 0
    for r in launch_rows:
        rows = by.get(r["launch_id"], [])
        d = decisions.get(r["launch_id"])
        rd = launches.review_date(r)
        if not rows and not d:
            continue
        shown += 1
        due = ""
        try:
            due = "Review date reached." if ctx["as_of"] >= date.fromisoformat(rd) else f"Not due until {rd}. Results so far are early."
        except ValueError:
            due = "[MISSING] no valid review date."
        L += [f"## {r.get('name') or r['launch_id']} ({r['launch_id']})", "", f"- Path decided: {d['decision'] + ' (' + d['decided_by'] + ', ' + d['date'] + ')' if d else '[needs product marketer decision]'}.",
              f"- Target date: {r.get('target_date') or '[MISSING]'}. {due}", ""]
        L += ["| Goal | Target | Actual | Against target | Status | Measured on | Source |", "|---|---|---|---|---|---|---|"]
        for g in rows:
            goal, act = to_number(g.get("goal_value")), to_number(g.get("actual_value"))
            st, pct = status(goal, act, (g.get("direction") or "higher").lower())
            L.append(f"| {g.get('goal_metric') or '[MISSING]'} | {g.get('goal_value') or '[MISSING]'} | {g.get('actual_value') or '[MISSING: result]'} | "
                     f"{('%d%%' % round(100 * pct)) + (' (lower is better)' if (g.get('direction') or '').lower() == 'lower' else '') if pct is not None else '-'} | {st} | {g.get('measured_on') or '[MISSING]'} | {g.get('source') or '[MISSING]'} |")
        if not rows:
            L.append("| [MISSING: goals were not recorded] | | | | | | |")
        ids = [x.strip() for x in (r.get("claims") or "").split(";") if x.strip()]
        by_id = {x["d"]["id"]: x for x in ctx["ranked"]}
        L += ["", "Claims the launch rested on, and their proof today:", ""]
        for i in ids:
            x = by_id.get(i)
            L.append(f"- {x['d']['claim']}: {len(x['usable'])} usable proof point(s)" + (f"; not usable: {', '.join(p + ' (' + w + ')' for p, w in x['unusable'])}" if x["unusable"] else "") if x else f"- {i}: not found in the product profile")
        L += ["", "What worked: [MISSING: the product marketer's view, from the results and from sales]", "What did not: [MISSING]",
              "What to change next time: [MISSING]", "Decision: [MISSING: continue, adjust or stop, decided by the product marketer]", ""]
    if not shown:
        L.append("No launch has a recorded decision or results yet. Add goals and results to launches/launch-results.csv.")
    return "\n".join(L)
