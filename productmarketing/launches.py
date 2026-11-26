"""Launch triage: should a new product or feature get a market launch, a sales launch, or neither?

Seven questions, each answered low, medium or high (or few/some/many, small/medium/large, no/partly/yes). Each answer is worth 0, 1 or 2 points.
The result is a suggestion with the reasons shown. The product marketer decides, and the decision is recorded in decisions/launch-decisions.csv.
A market launch markets directly to customers. A sales launch is internal: enablement and internal communication."""
import csv
from datetime import date, timedelta
from pathlib import Path

from .util import read_csv_rows

QUESTIONS = [
    ("customers_impacted", "How many customers does it affect?", {"few": 0, "some": 1, "many": 2}),
    ("customer_ask", "How big is the customer ask?", {"small": 0, "medium": 1, "large": 2}),
    ("value_to_prospects", "How much value does it bring prospects?", {"low": 0, "medium": 1, "high": 2}),
    ("differentiation", "How different is it from what the market offers?", {"low": 0, "medium": 1, "high": 2}),
    ("revenue_impact", "What is the revenue impact?", {"low": 0, "medium": 1, "high": 2}),
    ("usage_impact", "What is the impact on product usage?", {"low": 0, "medium": 1, "high": 2}),
    ("roadmap_fit", "Does it fit the product roadmap?", {"no": 0, "partly": 1, "yes": 2}),
]
MARKET_MIN, SALES_MIN, MIN_ANSWERED = 9, 5, 5
REVIEW_DAYS = 180
VALID = ("market", "sales", "none")
DEC_FIELDS = ["launch_id", "decision", "decided_by", "date", "note"]


def load(data):
    p = Path(data) / "launches" / "launch-requests.csv"
    return read_csv_rows(p) if p.exists() else []


def decisions_path(data):
    return Path(data) / "decisions" / "launch-decisions.csv"


def load_decisions(data):
    p = decisions_path(data)
    if not p.exists():
        return {}
    with open(p, newline="", encoding="utf-8") as fh:
        return {r["launch_id"]: {k: (v or "").strip() for k, v in r.items()} for r in csv.DictReader(fh) if r.get("launch_id")}


def add_decision(data, launch_id, decision, decided_by, note="", on=None):
    if decision not in VALID:
        raise ValueError(f"decision must be one of: {', '.join(VALID)}")
    if not (decided_by or "").strip():
        raise ValueError("a named person must make the decision (decided_by is empty)")
    p = decisions_path(data)
    p.parent.mkdir(parents=True, exist_ok=True)
    new = not p.exists()
    with open(p, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=DEC_FIELDS)
        if new:
            w.writeheader()
        w.writerow(dict(launch_id=launch_id, decision=decision, decided_by=decided_by.strip(), date=on or date.today().isoformat(), note=note.strip()))


def score(row):
    pts, missing = {}, []
    for key, _, scale in QUESTIONS:
        v = (row.get(key) or "").strip().lower()
        if v in scale:
            pts[key] = scale[v]
        else:
            pts[key] = None
            missing.append(key)
    total = sum(v for v in pts.values() if v is not None)
    answered = len(QUESTIONS) - len(missing)
    if answered < MIN_ANSWERED:
        path, why = "undetermined", f"only {answered} of {len(QUESTIONS)} questions answered (needs {MIN_ANSWERED})"
    elif total >= MARKET_MIN and (row.get("revenue_impact", "").lower() in ("medium", "high")):
        path, why = "market launch", f"{total} of 14 points, with a medium or high revenue impact"
    elif total >= SALES_MIN:
        path, why = "sales launch", f"{total} of 14 points"
    else:
        path, why = "no launch", f"{total} of 14 points; support through existing enablement"
    return dict(points=pts, missing=missing, total=total, answered=answered, path=path, why=why)


def review_date(row):
    try:
        return (date.fromisoformat(row.get("target_date", "")) + timedelta(days=REVIEW_DAYS)).isoformat()
    except ValueError:
        return "[MISSING: needs a valid target date, YYYY-MM-DD]"


def render(ctx, rows, decisions):
    L = ["# Launch triage", "", f"Prepared as of {ctx['as_of'].isoformat()}. A suggestion for each launch request, with the reasons. The product marketer decides.", "",
         "How it works: seven questions, 0 to 2 points each (14 in all). 9 or more points with a medium or high revenue impact suggests a market launch. 5 to 8 suggests a sales launch. Fewer suggests no launch. Fewer than 5 answers means the result is undetermined.", ""]
    if not rows:
        return "\n".join(L + ["[MISSING] no launch requests provided (launches/launch-requests.csv)."])
    for r in rows:
        s = score(r)
        d = decisions.get(r["launch_id"])
        L += [f"## {r.get('name') or r['launch_id']} ({r['launch_id']})", "", f"- Requested by: {r.get('requested_by') or '[MISSING]'}. Target date: {r.get('target_date') or '[MISSING]'}.",
              "", "| Question | Answer | Points |", "|---|---|---|"]
        for key, q, _ in QUESTIONS:
            L.append(f"| {q} | {r.get(key) or '[MISSING: answer]'} | {s['points'][key] if s['points'][key] is not None else '-'} |")
        L += ["", f"- Suggested path: **{s['path']}** ({s['why']}).", f"- Unanswered: {len(s['missing'])}." + (" Confidence is low." if s["missing"] else "")]
        if d:
            L.append(f"- Decision: {d['decision']} ({d['decided_by']}, {d['date']}). {d.get('note', '')}".rstrip())
        else:
            L.append("- Decision: [needs product marketer decision]")
        L += ["", "### Launch plan skeleton", ""]
        L += _checklist(ctx, r, d["decision"] if d else s["path"])
        L.append("")
    return "\n".join(L)


def _checklist(ctx, r, path):
    ids = [x.strip() for x in (r.get("claims") or "").split(";") if x.strip()]
    by = {x["d"]["id"]: x for x in ctx["ranked"]}
    L = []
    for i in ids:
        x = by.get(i)
        if not x:
            L.append(f"- [ ] Claim {i}: not found in the product profile.")
        elif len(x["usable"]) >= 2:
            L.append(f"- [x] Claim \"{x['d']['claim']}\": {len(x['usable'])} usable proof points ({', '.join(x['usable'])}).")
        else:
            bad = ", ".join(f"{pid} ({why})" for pid, why in x["unusable"]) or "none on file"
            L.append(f"- [ ] Claim \"{x['d']['claim']}\": {len(x['usable'])} usable proof point(s); needs 2. Not usable: {bad}.")
    if not ids:
        L.append("- [ ] Link the claims this launch rests on (the `claims` column) so proof can be checked.")
    L += ["- [ ] Field guide updated for each affected persona.", "- [ ] One-sheet drafted from approved messaging and usable proof.",
          "- [ ] Measurement plan: [MISSING: goals and how they will be measured]"]
    if path == "market launch" or path == "market":
        L += ["- [ ] Campaign theme, plan and master brief (Campaign Assistant, step 2).", "- [ ] Content topics and drafts (Content Strategy Assistant, step 3).",
              "- [ ] Paid media plan and tracking (Paid Media Planner, step 4).", "- [ ] Sales enablement and talk track."]
    elif path == "sales launch" or path == "sales":
        L += ["- [ ] Internal announcement.", "- [ ] Training outline and talk track for sales.", "- [ ] Update the sales playbook and battlecards."]
    else:
        L.append("- [ ] Confirm the path with the product marketer before planning anything.")
    L.append(f"- [ ] Review the results on {review_date(r)} (180 days after the target date).")
    return L
