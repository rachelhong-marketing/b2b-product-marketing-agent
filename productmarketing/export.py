"""Hand-off files for the next steps: positioning.json (for the campaign assistant) and a starter brand profile
(for the content strategy assistant)."""
from collections import Counter

from . import icp


def positioning(ctx):
    return {
        "brand": ctx["profile"]["brand"], "product": ctx["profile"]["product"], "category": ctx["profile"]["category"], "statement_parts": [{"label": k, "text": v} for k, v in ctx["statement_parts"]],
        "icp": [dict(industry=s["industry"], company_size=s["size"], deals=s["deals"], score=s.get("score")) for s in ctx["segments"] if s["rankable"]][:3],
        "personas": [dict(role=r, won_deals=n, main_pain=ctx["pains"].get(r)) for r, n in ctx["personas"]],
        "pillars": [dict(claim=x["d"]["claim"], pain_answered=x["d"]["answers"], proof=[pr["id"] for pr in x["d"]["proof"]], only_us=not x["overlap"]) for x in ctx["pillars"]],
        "competitors": [c["name"] for c in ctx["competitors"]], "avoid_words": ctx["profile"]["avoid_words"],
    }


def brand_profile(ctx):
    """A starting brand profile for the content strategy assistant. Fit comes from how many won deals used each use case."""
    won = [d for d in ctx["deals"] if d["outcome"].lower() == "won"]
    use = Counter(d["use_case"] for d in won if d.get("use_case"))
    top = max(use.values()) if use else 0
    themes = {}
    for t in ctx["profile"]["topics"]:
        themes[t["theme"]] = {"fit": round(use.get(t.get("use_case", ""), 0) / top, 2) if top else 0.5, "triggers": t["triggers"]}
    p = ctx["profile"]
    return {"brand": p["brand"], "product": p["product"], "note": "Starter profile exported by the product marketing agent. Review before use.", "domain": p["domain"],
            "audiences": [r for r, _ in ctx["personas"]], "voice": p.get("voice", ""), "avoid_words": p["avoid_words"], "known_acronyms": p["known_acronyms"],
            "themes": themes, "competitors": [{"name": c["name"], "note": c.get("claim", "")} for c in ctx["competitors"]]}
