"""Hand-off files for the next steps: positioning.json (for the campaign assistant) and a starter brand profile
(for the content strategy assistant)."""
from collections import Counter

from . import decisions as decmod


def positioning(ctx):
    conf = [r for r in ctx["decisions"].values() if r["decision"] == "confirmed"]
    return {
        "brand": ctx["profile"]["brand"], "product": ctx["profile"]["product"], "category": ctx["profile"]["category"],
        "as_of": ctx["as_of"].isoformat(),
        "statement_parts": [{"label": k, "text": v} for k, v in ctx["statement_parts"]],
        "icp_status": ctx["icp_status"],
        "icp_confirmed": [dict(segment=r["segment"], decided_by=r["decided_by"], date=r["date"], note=r["note"]) for r in conf],
        "icp_hypotheses": [dict(segment=decmod.label(s), deals=s["deals"], score=s.get("score"), decision=(decmod.of(ctx["decisions"], decmod.label(s)) or {}).get("decision", "needs decision"))
                           for s in ctx["segments"] if s["rankable"]][:5],
        "personas": [dict(name=p["name"], titles=p["titles"], won_deals=p["won"], main_pains=[t for t, _ in p["pains"]],
                          lead_with=[x["d"]["claim"] for _, x in p["lead"]], usable_proof=p["proof_ids"]) for p in ctx["personas"]],
        "pillars": [dict(claim=x["d"]["claim"], pain_answered=x["d"]["answers"], usable_proof=x["usable"], only_us=not x["overlap"]) for x in ctx["pillars"]],
        "proof_register": [dict(id=pid, usable=p["state"] == "valid", status=p["reason"]) for pid, p in ctx["proofs"].items()],
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
    note = "Starter profile exported by the product marketing agent. Review before use."
    if ctx["icp_status"] != "CONFIRMED":
        note += " The ideal customer profile is still a DRAFT: no product marketer decision recorded."
    return {"brand": p["brand"], "product": p["product"], "note": note, "domain": p["domain"],
            "audiences": [f"{x['name']} ({', '.join(x['titles'])})" for x in ctx["personas"]], "voice": p.get("voice", ""), "avoid_words": p["avoid_words"],
            "known_acronyms": p["known_acronyms"], "themes": themes, "competitors": [{"name": c["name"], "note": c.get("claim", "")} for c in ctx["competitors"]]}
