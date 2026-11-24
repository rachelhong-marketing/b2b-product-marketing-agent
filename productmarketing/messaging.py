"""Positioning and messaging, built only from evidence you supplied.

It picks messaging pillars from your claimed differentiators using three tests: is it unique among the competitors you track,
do your customers talk about the pain it answers, and do you have proof for it. A claim with no proof cannot be a pillar.
It writes structure and evidence. A person (or an AI assistant working in your voice) writes the final words."""
import json
from pathlib import Path

from . import icp
from .util import has_phrase, read_csv_rows

W = dict(unique=0.40, pain=0.35, proof=0.25)
MIN_PROOF = 2


def load_profile(path):
    p = json.loads(Path(path).read_text(encoding="utf-8"))
    missing = [k for k in ("brand", "product", "domain", "category", "differentiators", "avoid_words") if k not in p]
    if missing:
        raise ValueError(f"product profile is missing: {', '.join(missing)}")
    for d in p["differentiators"]:
        d.setdefault("tags", [])
        d.setdefault("answers", [])
        d.setdefault("proof", [])
    p.setdefault("topics", [])
    p.setdefault("known_acronyms", [])
    return p


def load(data):
    data = Path(data)
    def rows(rel):
        f = data / rel
        return read_csv_rows(f) if f.exists() else []
    return dict(profile=load_profile(data / "company" / "product-profile.json"), deals=rows("customers/deals.csv"),
                interviews=rows("customers/interviews.csv"), competitors=rows("market/competitors.csv"))


def overlap(diff, competitors):
    """Competitors (that you track) that claim any of this differentiator's tags."""
    tags = {t.lower() for t in diff["tags"]}
    return [c["name"] for c in competitors if tags & {t.strip().lower() for t in c.get("claim_tags", "").split(";") if t.strip()}]


def pain_hits(diff, interviews):
    ans = diff["answers"]
    return [i for i in interviews if any(has_phrase(i["pain"], a) for a in ans)]


def rank_differentiators(profile, interviews, competitors):
    out = []
    for d in profile["differentiators"]:
        ov = overlap(d, competitors)
        hits = pain_hits(d, interviews)
        uniq = 1.0 if not ov else (0.5 if len(ov) == 1 else 0.0)
        pain = len(hits) / len(interviews) if interviews else 0.0
        proof = min(1.0, len(d["proof"]) / MIN_PROOF)
        out.append(dict(d=d, overlap=ov, hits=hits, unique=uniq, pain=pain, proof=proof,
                        score=round(100 * (W["unique"] * uniq + W["pain"] * min(1.0, pain * 3) + W["proof"] * proof), 1)))
    return sorted(out, key=lambda x: -x["score"])


def analyze(data):
    c = load(data)
    ranked = rank_differentiators(c["profile"], c["interviews"], c["competitors"])
    pillars = [x for x in ranked if len(x["d"]["proof"]) >= 1][:3]
    no_proof = [x for x in ranked if not x["d"]["proof"]]
    segs = icp.segments(c["deals"])
    top_seg = next((s for s in segs if s["rankable"]), None)
    pers = icp.personas(c["deals"])
    pains = {}
    for role, _ in pers:
        ps = [i["pain"] for i in c["interviews"] if i["role"].lower() == role.lower()]
        pains[role] = sorted(set(ps), key=lambda x: (-ps.count(x), x))[0] if ps else None
    lc = icp.lost_competitors(c["deals"])
    return dict(c, ranked=ranked, pillars=pillars, no_proof=no_proof, segments=segs, top_segment=top_seg, personas=pers, pains=pains,
                lost_reasons=icp.lost_reasons(c["deals"]), lost_competitors=lc)


def statement_parts(ctx):
    """The positioning statement as labeled parts. The sentences are for a person to write; the evidence is filled in."""
    p = ctx["profile"]
    seg, pers = ctx["top_segment"], ctx["personas"]
    who = f"{pers[0][0]} at {seg['industry'].lower()} companies with {seg['size']} employees" if seg and pers else "[MISSING: ideal customer]"
    pain = next((v for v in ctx["pains"].values() if v), None) or "[MISSING: their main problem, from interviews]"
    alt = ctx["lost_competitors"][0][0] if ctx["lost_competitors"] else "[MISSING: the alternative buyers choose]"
    strong = ctx["pillars"][0]["d"]["claim"] if ctx["pillars"] else "[MISSING: a differentiator with proof]"
    only = next((x["d"]["claim"] for x in ctx["pillars"] if not x["overlap"]), "[MISSING: a claim no tracked competitor makes]")
    return [("For", who), ("Whose problem is", pain), (f"{p['product']} is", p["category"]),
            ("The main benefit (write one sentence)", f"[MISSING: write it. Strongest pillar: {strong}]"),
            ("Unlike (most named in lost deals)", alt), ("What only we do (write one sentence)", f"[MISSING: write it. Claim nobody tracked makes: {only}]")]


def render(ctx):
    p = ctx["profile"]
    n_d, n_w = len(ctx["deals"]), sum(1 for d in ctx["deals"] if d["outcome"].lower() == "won")
    L = [f"# Positioning and messaging: {p['brand']}", "", f"Product: {p['product']}, {p['category']}.", "",
         "A starting point built from your deals, interviews and competitor list. Every claim below has its evidence next to it. Edit the wording in your own voice.", "",
         "## Data used", "", f"- Closed deals: {n_d or '[MISSING] none provided'} ({n_w} won)", f"- Customer interviews: {len(ctx['interviews']) or '[MISSING] none provided'}",
         f"- Competitors tracked: {len(ctx['competitors']) or '[MISSING] none provided'}", f"- Differentiators claimed: {len(p['differentiators'])}", "",
         "## Who we sell to (ideal customer profile)", ""]
    L += icp.table_lines(ctx["segments"])
    L += ["", "Scores compare segments within this run only. A segment needs at least 5 closed deals and 3 wins to be ranked.", ""]
    top = [s for s in ctx["segments"] if s["rankable"]][:2]
    L.append("Best-fit segments: " + ("; ".join(f"{s['industry']}, {s['size']} employees (score {s['score']}, {s['deals']} deals)" for s in top) or "[MISSING] not enough deals"))
    L += ["", "### Buyer personas", ""]
    for role, n in ctx["personas"]:
        pain = ctx["pains"].get(role)
        L.append(f"- **{role}**: {n} won deals. Main pain from interviews: {pain or '[MISSING] no interview with this role yet'}.")
    if not ctx["personas"]:
        L.append("- [MISSING] no won deals with a buyer role.")
    L += ["", "## Positioning statement (draft)", "", *[f"- **{k}:** {v}" for k, v in ctx["statement_parts"]], "",
          "## Messaging pillars", "", "Chosen from your claimed differentiators: no tracked competitor makes the claim (40%), customers talk about the pain it answers (35%), proof on file (25%).", ""]
    for i, x in enumerate(ctx["pillars"], 1):
        d = x["d"]
        L += [f"### Pillar {i}: {d['claim']}", "", f"- Score {x['score']}. " + ("No tracked competitor makes this claim." if not x["overlap"] else f"Also claimed by: {', '.join(x['overlap'])}."),
              f"- Pain it answers: {', '.join(d['answers']) or '[MISSING]'}. Mentioned in {len(x['hits'])} of {len(ctx['interviews'])} interviews."]
        for pr in d["proof"]:
            L.append(f"- Proof ({pr['type']}, source: {pr['source']}): {pr['text']}")
        if len(d["proof"]) < MIN_PROOF:
            L.append(f"- [MISSING] only {len(d['proof'])} proof point; add at least {MIN_PROOF} before using this in a campaign.")
        L.append("")
    if not ctx["pillars"]:
        L += ["[MISSING] no differentiator has proof, so there are no pillars yet.", ""]
    if ctx["no_proof"]:
        L += ["## Claims that cannot be pillars yet (no proof on file)", ""]
        L += [f"- {x['d']['claim']}: add a customer result, benchmark or third-party source." for x in ctx["no_proof"]] + [""]
    shared = [x for x in ctx["ranked"] if len(x["overlap"]) >= 2]
    if shared:
        L += ["## Claims others also make", ""]
        L += [f"- {x['d']['claim']}: also claimed by {', '.join(x['overlap'])}. Do not lead with it." for x in shared] + [""]
    L += ["## Objections to prepare for", "", "From lost deals. The responses are for sales to supply. They are not invented here.", ""]
    for reason, n in ctx["lost_reasons"]:
        L.append(f"- {reason} ({n} lost deals). Response: [MISSING: from sales and win-loss calls]")
    if ctx["lost_competitors"]:
        L.append("- Competitors named in lost deals: " + ", ".join(f"{c} ({n})" for c, n in ctx["lost_competitors"]))
    L += ["", "## Words to avoid", "", ", ".join(p["avoid_words"]) or "none set", ""]
    return "\n".join(L)
