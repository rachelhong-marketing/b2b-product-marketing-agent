"""Battlecards: one internal page per tracked competitor, built from public information and your own deals and notes.

Internal use only. Public information about the competitor only. Nothing here is invented: what they are strong at, how they position against you
and how to handle them come from people who talk to buyers, so those lines stay [MISSING] until a person supplies them."""
from collections import Counter

from . import decisions as decmod
from .util import has_phrase, slug


def proof_line(ctx, pid):
    p = ctx["proofs"].get(pid)
    if not p:
        return f"{pid} (not in the register)"
    return f"{p['text']} (source: {p['source'] or '[MISSING]'}; {p['reason']}) [{pid}]"


def build(ctx, comp):
    name = comp["name"]
    lost_all = [d for d in ctx["deals"] if d["outcome"].lower() == "lost"]
    lost = [d for d in lost_all if d.get("competitor", "").lower() == name.lower()]
    segs = Counter(f"{d['industry']}, {d['company_size']}" for d in lost)
    shared = [x for x in ctx["ranked"] if name in x["overlap"]]
    ours = [x for x in ctx["ranked"] if name not in x["overlap"] and x["usable"]]
    notes = [n["note"] for n in ctx["sales_notes"] if has_phrase(n.get("note", ""), name)][:3]
    L = [f"# Battlecard: {name}", "", f"Prepared as of {ctx['as_of'].isoformat()}. **Internal use only.** Do not share with customers. Public information about the competitor only.", "",
         "## What they say", "", f"- Their claim: {comp.get('claim') or '[MISSING]'}", f"- Price tier: {comp.get('price_tier') or '[MISSING]'}",
         f"- Source (public page): {comp.get('source_url') or '[MISSING]'}", f"- Claim tags: {comp.get('claim_tags') or '[MISSING]'}", "",
         "## Where they are strong", ""]
    L.append(f"- {comp['strengths']}" if comp.get("strengths") else "- [MISSING: what buyers say they do well, from win and loss calls or their public materials]")
    L += ["", "## Where we differ", ""]
    for x in ours:
        L.append(f"- {x['d']['claim']}. They do not claim this. Proof you can use: " + "; ".join(proof_line(ctx, pid) for pid in x["usable"]))
    if not ours:
        L.append("- [MISSING] no claim with usable proof that this competitor does not also make.")
    L += ["", "## Claims both of us make (do not lead with these)", ""]
    L += [f"- {x['d']['claim']} (also claimed by: {', '.join(x['overlap'])})" for x in shared] or ["- None found among the tags you track."]
    L += ["", "## Our record against them", ""]
    L.append(f"- Lost deals naming them: {len(lost)} of {len(lost_all)} lost deals" + (f" ({round(100 * len(lost) / len(lost_all))}%)." if lost_all else "."))
    if segs:
        L.append("- Where we lost to them: " + "; ".join(f"{s} ({n})" for s, n in segs.most_common()))
    L.append("- Deals we won against them: [MISSING] the deal data does not record the competitor on wins. Add it to learn what works.")
    L += ["", "## What sales said about them", ""]
    L += [f'- "{n}"' for n in notes] or ["- [MISSING] no sales notes mention this competitor."]
    L += ["", "## How to handle them", "", "- [MISSING: how to position when they come up, from sales and win-loss calls. Not invented here.]",
          "- [MISSING: questions to ask the buyer that bring out the difference, from sales.]", ""]
    return "\n".join(L)


def build_all(ctx):
    return {slug(c["name"]): build(ctx, c) for c in ctx["competitors"]}
