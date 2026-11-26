"""Sales playbook outline: a draft structure for sales, filled with evidence and left open where sales must write.

The playbook belongs to sales and the product marketer. This builds the skeleton and the evidence, not the talk tracks."""
from . import decisions as decmod
from .util import slug


def build(ctx):
    L = ["# Sales playbook outline (draft)", "", f"Prepared as of {ctx['as_of'].isoformat()}. Internal. A person writes the talk tracks.", "", "## Who to call", ""]
    conf = [r for r in ctx["decisions"].values() if r["decision"] == "confirmed"]
    if conf:
        L += [f"- {r['segment']} (confirmed by {r['decided_by']}, {r['date']})" for r in conf]
    else:
        L.append("- [MISSING] the ideal customer profile is not confirmed by the product marketer yet.")
    if ctx["list_common"]:
        L.append("- Target list shared traits (a pattern in how the list was built, not proof of fit): " + "; ".join(f"{v} ({round(100 * s)}%)" for _, v, _, s in ctx["list_common"][:6]))
    L += ["", "## Who you talk to", ""]
    for p in ctx["personas"]:
        top = p["lead"][0][1]["d"]["claim"] if p["lead"] else "[MISSING]"
        L.append(f"- {p['name']} ({', '.join(p['titles'])}). Lead with: {top}. See field-guides/{slug(p['name'])}.md")
    L += ["", "## What starts a conversation", ""]
    trig = []
    for p in ctx["personas"]:
        trig += [t for t in p["triggers"] if t not in trig]
    L += [f"- {t}" for t in trig] or ["- [MISSING]"]
    L += ["", "## What to ask about in discovery", "", "Topics only. Sales writes the questions in their own words.", ""]
    seen = []
    for p in ctx["personas"]:
        for t, n in p["pains"]:
            if t not in seen:
                seen.append(t)
                L.append(f"- {t} (raised in {n} interviews)")
    if not seen:
        L.append("- [MISSING]")
    L += ["", "## What to say and prove", ""]
    for x in ctx["pillars"]:
        L.append(f"- {x['d']['claim']}. Usable proof: " + (", ".join(x["usable"]) or "[MISSING]"))
    L += ["", "## Competitors", ""]
    L += [f"- {c['name']}: battlecards/{slug(c['name'])}.md" for c in ctx["competitors"]] or ["- [MISSING]"]
    L += ["", "## Objections", ""]
    L += [f"- {r} ({n} lost deals). Response: [MISSING: from sales and win-loss calls]" for r, n in ctx["lost_reasons"]] or ["- [MISSING]"]
    L += ["", "## How we will know it is working", ""]
    for s in ctx["segments"]:
        d = decmod.of(ctx["decisions"], decmod.label(s))
        if d and d["decision"] == "confirmed":
            L.append(f"- {decmod.label(s)}: win rate {round(100 * s['win_rate'])}% over {s['deals']} deals, about {round(s['days'])} days to close." if s["days"] else f"- {decmod.label(s)}: win rate {round(100 * s['win_rate'])}% over {s['deals']} deals.")
    L += ["- Targets for the next quarter: [MISSING: set by the product marketer and sales]", "", "## Handoffs and next steps", "", "- [MISSING: from sales operations: who owns a lead after each stage]", ""]
    return "\n".join(L)
