"""Positioning and messaging, built only from evidence you supplied, for a product marketer to review and decide.

The agent drafts and checks. The product marketer decides the ideal customer profile (ICP), the final positioning and which claims are approved.
Pillars are picked from your claimed differentiators with three tests: does no tracked competitor make the claim, do customers talk about the pain
it answers, and is there usable proof in the proof-point register. A claim with no usable proof cannot be a pillar.
It writes structure and evidence. A person (or an AI assistant working in your voice) writes the final words."""
import json
from datetime import date
from pathlib import Path

from . import accounts as acctmod, decisions as decmod, icp, personas as personamod, proofs as proofmod, sales as salesmod
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
        if any(not isinstance(x, str) for x in d["proof"]):
            raise ValueError(f"differentiator {d.get('id', '')}: 'proof' must be a list of proof ids from company/proof-points.csv")
    p.setdefault("topics", [])
    p.setdefault("personas", [])
    p.setdefault("known_acronyms", [])
    return p


def load(data):
    data = Path(data)

    def rows(rel):
        f = data / rel
        return read_csv_rows(f) if f.exists() else []
    return dict(profile=load_profile(data / "company" / "product-profile.json"), deals=rows("customers/deals.csv"),
                interviews=rows("customers/interviews.csv"), competitors=rows("market/competitors.csv"),
                accounts=acctmod.load(data), sales_notes=salesmod.load(data), proof_rows=proofmod.load(data), decisions=decmod.load(data))


def overlap(diff, competitors):
    """Competitors (that you track) that claim any of this differentiator's tags."""
    tags = {t.lower() for t in diff["tags"]}
    return [c["name"] for c in competitors if tags & {t.strip().lower() for t in c.get("claim_tags", "").split(";") if t.strip()}]


def pain_hits(diff, interviews):
    ans = diff["answers"]
    return [i for i in interviews if any(has_phrase(i["pain"], a) for a in ans)]


def rank_differentiators(profile, interviews, competitors, idx):
    out = []
    for d in profile["differentiators"]:
        ov = overlap(d, competitors)
        hits = pain_hits(d, interviews)
        usable = [pid for pid in d["proof"] if idx.get(pid, {}).get("state") == "valid"]
        unusable = [(pid, idx[pid]["reason"] if pid in idx else "not in the proof-point register") for pid in d["proof"] if pid not in usable]
        uniq = 1.0 if not ov else (0.5 if len(ov) == 1 else 0.0)
        pain = len(hits) / len(interviews) if interviews else 0.0
        proof = min(1.0, len(usable) / MIN_PROOF)
        out.append(dict(d=d, overlap=ov, hits=hits, unique=uniq, pain=pain, proof=proof, usable=usable, unusable=unusable,
                        score=round(100 * (W["unique"] * uniq + W["pain"] * min(1.0, pain * 3) + W["proof"] * proof), 1)))
    return sorted(out, key=lambda x: -x["score"])


def analyze(data, as_of=None):
    as_of = as_of or date.today()
    c = load(data)
    idx = proofmod.index(c["proof_rows"], as_of)
    ranked = rank_differentiators(c["profile"], c["interviews"], c["competitors"], idx)
    pillars = [x for x in ranked if x["usable"]][:3]
    no_proof = [x for x in ranked if not x["usable"]]
    segs = icp.segments(c["deals"])
    list_counts = acctmod.segment_counts(c["accounts"])
    no_wins, wins_off_list = acctmod.compare_with_wins(segs, c["accounts"])
    pers = personamod.build(c["profile"], c["deals"], c["interviews"], pillars, ranked, idx)
    used_by = {}
    for x in ranked:
        for pid in x["d"]["proof"]:
            used_by.setdefault(pid, []).append(x["d"]["claim"].split(":")[0])
    lc = icp.lost_competitors(c["deals"])
    return dict(c, as_of=as_of, proofs=idx, used_by=used_by, ranked=ranked, pillars=pillars, no_proof=no_proof, segments=segs,
                list_counts=list_counts, list_common=acctmod.common(c["accounts"]), list_patterns=acctmod.patterns(c["accounts"]),
                no_wins=no_wins, wins_off_list=wins_off_list, sales_by_seg=salesmod.by_segment(c["sales_notes"], c["deals"]),
                icp_status=decmod.status(c["decisions"]), personas=pers, lost_reasons=icp.lost_reasons(c["deals"]), lost_competitors=lc)


def confirmed_segment(ctx):
    for s in ctx["segments"]:
        d = decmod.of(ctx["decisions"], decmod.label(s))
        if d and d["decision"] == "confirmed":
            return s
    return None


def statement_parts(ctx):
    """The positioning statement as labeled parts. The sentences are for a person to write; the evidence is filled in."""
    p = ctx["profile"]
    seg = confirmed_segment(ctx)
    if seg:
        roles = icp.personas([d for d in ctx["deals"] if (d["industry"], d["company_size"]) == (seg["industry"], seg["size"])])
        who = f"{roles[0][0] if roles else '[MISSING: buyer role]'} at {seg['industry'].lower()} companies with {seg['size']} employees"
    else:
        draft = next((s for s in ctx["segments"] if s["rankable"]), None)
        who = ("[MISSING: ideal customer. The ICP is not confirmed by the product marketer. Draft suggestion: "
               + (f"{draft['industry'].lower()} companies with {draft['size']} employees]" if draft else "none, not enough deals]"))
    pain = next((n for pr in ctx["personas"] for n, _ in pr["pains"][:1]), None) or "[MISSING: their main problem, from interviews]"
    alt = ctx["lost_competitors"][0][0] if ctx["lost_competitors"] else "[MISSING: the alternative buyers choose]"
    strong = ctx["pillars"][0]["d"]["claim"] if ctx["pillars"] else "[MISSING: a differentiator with usable proof]"
    only = next((x["d"]["claim"] for x in ctx["pillars"] if not x["overlap"]), "[MISSING: a claim no tracked competitor makes]")
    return [("For", who), ("Whose problem is", pain), (f"{p['product']} is", p["category"]),
            ("The main benefit (write one sentence)", f"[MISSING: write it. Strongest pillar: {strong}]"),
            ("Unlike (most named in lost deals)", alt), ("What only we do (write one sentence)", f"[MISSING: write it. Claim nobody tracked makes: {only}]")]


def icp_lines(ctx):
    d = ctx["decisions"]
    confirmed = [r for r in d.values() if r["decision"] == "confirmed"]
    undecided = [s for s in ctx["segments"] if s["rankable"] and not decmod.of(d, decmod.label(s))]
    L = ["## Who we sell to: ideal customer profile (ICP) hypotheses for the product marketer to decide", "",
         "The agent ranks segments from closed deals and shows what the target account list and sales notes say. It does not decide the ICP. "
         "Record each decision with `decide`. Until at least one segment is confirmed, the profile stays a draft.", ""]
    if confirmed:
        L.append(f"ICP status: CONFIRMED by the product marketer. Confirmed: " + "; ".join(f"{r['segment']} ({r['decided_by']}, {r['date']})" for r in confirmed) + ".")
    else:
        L.append("ICP status: DRAFT. No product marketer decision recorded.")
    L.append("")
    L += icp.table_lines(ctx["segments"], ctx["list_counts"] if ctx["accounts"] else None, d)
    L += ["", "Scores compare segments within this run only. A segment needs at least 5 closed deals and 3 wins to be ranked.", ""]
    L += ["### Patterns in the target account list", ""]
    if not ctx["accounts"]:
        L.append("[MISSING] no target account list provided.")
    elif len(ctx["accounts"]) < acctmod.MIN_LIST:
        L.append(f"[MISSING] the list has {len(ctx['accounts'])} accounts, too few to show patterns (needs {acctmod.MIN_LIST}).")
    else:
        n = len(ctx["accounts"])
        L.append(f"{n} accounts. Values shared by at least {round(100 * acctmod.COMMON_SHARE)}% of them:")
        L += [f"- {f.replace('_', ' ')}: {v} ({k} of {n}, {round(100 * s)}%)" for f, v, k, s in ctx["list_common"]] or ["- none"]
        L.append("")
        L.append("Caution: a target list reflects the filters used to build it, so a pattern here is not proof of buyer fit. Check it against wins below.")
    L += ["", "### Target list compared with wins", ""]
    if not ctx["accounts"]:
        L.append("[MISSING] needs the target account list.")
    else:
        for x in ctx["no_wins"]:
            L.append(f"- On the list, no wins: {x['segment']} ({x['accounts']} accounts, {x['deals']} closed deals). Ask why before spending on it.")
        for x in ctx["wins_off_list"]:
            L.append(f"- Winning where the list barely looks: {x['segment']} ({x['wins']} wins, {x['accounts']} on the list).")
        if not ctx["no_wins"] and not ctx["wins_off_list"]:
            L.append("- No mismatch found between the list and the wins.")
    L += ["", "### What sales said", ""]
    if not ctx["sales_notes"]:
        L.append("[MISSING] no sales input provided (customers/sales-input.csv).")
    else:
        for s in [s for s in ctx["segments"] if (s["industry"], s["size"]) in ctx["sales_by_seg"]][:4]:
            o = ctx["sales_by_seg"][(s["industry"], s["size"])]
            kinds = ", ".join(f"{k} {n}" for k, n in o["types"].most_common())
            L.append(f"- {decmod.label(s)}: {o['n']} notes from {len(o['reps'])} rep(s) ({kinds}). Examples: " + " / ".join(f'"{e}"' for e in o["examples"]))
    L += ["", "### Decisions needed", ""]
    L += [f"- {decmod.label(s)}: needs a decision (score {s['score']}, {s['deals']} deals)" for s in undecided] or ["- None. Every ranked segment has a decision."]
    L.append("")
    return L


def render(ctx):
    p = ctx["profile"]
    n_d, n_w = len(ctx["deals"]), sum(1 for d in ctx["deals"] if d["outcome"].lower() == "won")
    L = [f"# Positioning and messaging: {p['brand']}", "", f"Product: {p['product']}, {p['category']}.", "",
         f"Prepared as of {ctx['as_of'].isoformat()}. A starting point for the product marketer: the agent drafts and checks, and the product marketer decides. "
         "Every claim below has its evidence next to it. Edit the wording in your own voice.", "",
         "## Data used", "", f"- Closed deals: {n_d or '[MISSING] none provided'} ({n_w} won)", f"- Customer interviews: {len(ctx['interviews']) or '[MISSING] none provided'}",
         f"- Target accounts: {len(ctx['accounts']) or '[MISSING] none provided'}", f"- Sales notes: {len(ctx['sales_notes']) or '[MISSING] none provided'}",
         f"- Competitors tracked: {len(ctx['competitors']) or '[MISSING] none provided'}", f"- Differentiators claimed: {len(p['differentiators'])}",
         f"- Proof points in the register: {len(ctx['proofs']) or '[MISSING] none provided'}", f"- Ideal customer profile decisions recorded: {len(ctx['decisions'])}", ""]
    L += icp_lines(ctx)
    L += ["## Persona field guides (drafts)", "", "One guide per buyer persona. The evidence is filled in; the words to say to each persona are for a person to write.", ""]
    L += personamod.lines(ctx["personas"]) or ["[MISSING] no personas."]
    L += ["## Positioning statement (draft)", "", *[f"- **{k}:** {v}" for k, v in ctx["statement_parts"]], "",
          "## Messaging pillars", "", "Chosen from your claimed differentiators: no tracked competitor makes the claim (40%), customers talk about the pain it answers (35%), usable proof on file (25%).", ""]
    for i, x in enumerate(ctx["pillars"], 1):
        d = x["d"]
        L += [f"### Pillar {i}: {d['claim']}", "", f"- Score {x['score']}. " + ("No tracked competitor makes this claim." if not x["overlap"] else f"Also claimed by: {', '.join(x['overlap'])}."),
              f"- Pain it answers: {', '.join(d['answers']) or '[MISSING]'}. Mentioned in {len(x['hits'])} of {len(ctx['interviews'])} interviews."]
        for pid in x["usable"]:
            pr = ctx["proofs"][pid]
            L.append(f"- Proof ({pr.get('type', '')}, source: {pr['source']}, {pr['reason']}): {pr['text']} [{pid}]")
        for pid, why in x["unusable"]:
            L.append(f"- Not usable ({why}): {ctx['proofs'][pid]['text'] if pid in ctx['proofs'] else pid} [{pid}]")
        if len(x["usable"]) < MIN_PROOF:
            L.append(f"- [MISSING] only {len(x['usable'])} usable proof point(s); add at least {MIN_PROOF} before using this in a campaign.")
        L.append("")
    if not ctx["pillars"]:
        L += ["[MISSING] no differentiator has usable proof, so there are no pillars yet.", ""]
    L += ["## Proof-point register", "", f"Status as of {ctx['as_of'].isoformat()}. A proof point is usable only with a source, an approver and an approval date, and before it expires.", ""]
    L += proofmod.register_lines(ctx["proofs"], ctx["used_by"]) if ctx["proofs"] else ["[MISSING] no proof-point register provided (company/proof-points.csv)."]
    L.append("")
    if ctx["no_proof"]:
        L += ["## Claims that cannot be pillars yet (no usable proof)", ""]
        for x in ctx["no_proof"]:
            why = "; ".join(f"{pid}: {r}" for pid, r in x["unusable"]) or "no proof on file"
            L.append(f"- {x['d']['claim']}: {why}. Add a customer result, benchmark or third-party source, approved and in date.")
        L.append("")
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
