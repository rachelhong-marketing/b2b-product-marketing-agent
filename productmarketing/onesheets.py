"""One-sheet drafts: a one-page external description for a persona, built only from approved messaging and usable proof.

The body is for customers, so it carries no interview counts or internal research and only proof points that are usable today.
The words themselves are slots for a person to write. Everything the writer needs is in the notes at the end, to delete before publishing."""
from . import battlecards

NOTES = "## Writer's notes (delete before publishing)"


def build(ctx, p):
    p_name, product = p["name"], ctx["profile"]["product"]
    lead = [x for _, x in p["lead"]][:3]
    L = [f"# {product}: one-sheet draft for {p_name}", "", f"Draft. A person writes the words. Every proof point below is usable as of {ctx['as_of'].isoformat()}.", "",
         "## Headline", "", "[MISSING: headline, written by a person]", "", "## The problem", "", "[MISSING: one or two sentences in the buyer's own words]", "",
         f"## What {product} does", ""]
    L += [f"- {x['d']['claim']}" for x in lead] or ["- [MISSING] no pillar answers this persona's pains yet."]
    L += ["", "## Proof", ""]
    shown = []
    for x in lead:
        for pid in x["usable"]:
            if pid not in shown:
                shown.append(pid)
    for pid in shown:
        pr = ctx["proofs"][pid]
        L.append(f"- {pr['text']} ({pr['source']}) [{pid}]")
    if not shown:
        L.append("- [MISSING] no usable proof point for these claims.")
    L += ["", "## Customer quote", "", "[MISSING: an approved customer quote]", "", "## Next step", "", "[MISSING: call to action]", "", "---", "", NOTES, ""]
    L.append(f"- Written for: {p_name} ({', '.join(p['titles'])}).")
    for h, x in p["lead"][:3]:
        L.append(f"- Buyers describe the problem this answers as: " + ", ".join(f'"{a}"' for a in x["d"]["answers"]) + ".")
    soon = [pid for pid in shown if "expires soon" in ctx["proofs"][pid]["reason"]]
    if soon:
        L.append("- Proof points expiring within 60 days: " + ", ".join(f"{pid} ({ctx['proofs'][pid]['reason']})" for pid in soon) + ". Refresh before this goes to print.")
    if p["avoid"]:
        L.append("- Do not lead with: " + "; ".join(x["d"]["claim"] for x in p["avoid"]) + " (competitors make the same claim).")
    L.append("")
    return "\n".join(L)
