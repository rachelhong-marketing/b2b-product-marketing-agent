"""Persona field guides: one page per buyer persona saying who they are, what hurts, what to lead with and what proof to use.

Evidence filled in from interviews, deals and the proof register. The words to say are left for a person to write."""
from . import battlecards


def build(ctx, p):
    L = [f"# Field guide: {p['name']}", "", f"Prepared as of {ctx['as_of'].isoformat()}. Internal use. The evidence is filled in; the words to say are for a person to write.", "",
         "## Who they are", "", f"- Titles: {', '.join(p['titles'])}",
         f"- Evidence base: {p['won']} won and {p['lost']} lost deals, {p['interviews'] or '[MISSING] no'} interviews. Counts are internal, not proof points for external copy.", "",
         "## What hurts (in their words, from interviews)", ""]
    L += [f"- {t} ({n} interviews)" for t, n in p["pains"]] or ["- [MISSING] no interviews with this persona yet."]
    L += ["", "## What starts a search", ""]
    L += [f"- {t}" for t in p["triggers"]] or ["- [MISSING]"]
    L += ["", "## What they use today", ""]
    L += [f"- {a}" for a in p["alternatives"]] or ["- [MISSING]"]
    L += ["", "## What to lead with", ""]
    for h, x in p["lead"]:
        L.append(f"- {x['d']['claim']} (answers {h} interview pains)")
    if not p["lead"]:
        L.append("- [MISSING] no pillar answers this persona's pains yet.")
    L += ["", "## Proof you can use", ""]
    L += [f"- {battlecards.proof_line(ctx, pid)}" for pid in p["proof_ids"]] or ["- [MISSING] no usable proof for the pillars above."]
    L += ["", "## Do not lead with", ""]
    L += [f"- {x['d']['claim']} (competitors make the same claim: {', '.join(x['overlap'])})" for x in p["avoid"]] or ["- Nothing flagged."]
    L += ["", "## Objections you will hear", ""]
    L += [f"- {r} ({n} lost deals). Response: [MISSING: from sales and win-loss calls]" for r, n in p["objections"]] or ["- [MISSING] no lost deals with this persona."]
    L += ["", "## What to say", "", "[MISSING: one sentence for this persona, written by a person from the evidence above]", "",
          "## Questions to ask in the first call", "", "[MISSING: two or three questions, from sales]", ""]
    return "\n".join(L)
