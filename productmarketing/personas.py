"""Persona field guides: for each buyer persona, what they struggle with, what to lead with, and what not to lead with.

Built from interviews, deals and the pillars. The persona groups come from the product profile (`personas`: name and titles).
If none are given, each of the three most common buyer titles in won deals becomes a persona. The words to say to each persona are left as [MISSING] for a person to write."""
from collections import Counter

from .util import has_phrase


def groups(profile, deals):
    if profile.get("personas"):
        return [dict(name=p["name"], titles=p["titles"]) for p in profile["personas"]]
    c = Counter(d["buyer_role"] for d in deals if d["outcome"].lower() == "won" and d["buyer_role"])
    return [dict(name=r, titles=[r]) for r, _ in c.most_common(3)]


def build(profile, deals, interviews, pillars, ranked, idx):
    out = []
    for g in groups(profile, deals):
        titles = {t.lower() for t in g["titles"]}
        mine_i = [i for i in interviews if i["role"].lower() in titles]
        mine_d = [d for d in deals if d["buyer_role"].lower() in titles]
        won = [d for d in mine_d if d["outcome"].lower() == "won"]
        lost = [d for d in mine_d if d["outcome"].lower() == "lost"]
        pains = Counter(i["pain"] for i in mine_i if i.get("pain"))
        trig = Counter(i["trigger"] for i in mine_i if i.get("trigger"))
        alt = Counter(i["current_alternative"] for i in mine_i if i.get("current_alternative"))
        lead = []
        for x in pillars:
            hits = sum(n for p, n in pains.items() if any(has_phrase(p, a) for a in x["d"]["answers"]))
            if hits:
                lead.append((hits, x))
        lead.sort(key=lambda t: -t[0])
        avoid = []
        for x in ranked:
            if len(x["overlap"]) >= 2 and any(has_phrase(p, a) for p in pains for a in x["d"]["answers"]):
                avoid.append(x)
        proof_ids = []
        for _, x in lead:
            for pid in x["d"]["proof"]:
                if idx.get(pid, {}).get("state") == "valid" and pid not in proof_ids:
                    proof_ids.append(pid)
        out.append(dict(name=g["name"], titles=g["titles"], won=len(won), lost=len(lost), interviews=len(mine_i),
                        pains=pains.most_common(3), triggers=[t for t, _ in trig.most_common(2)], alternatives=[a for a, _ in alt.most_common(2)],
                        lead=[(h, x) for h, x in lead], avoid=avoid, proof_ids=proof_ids,
                        objections=Counter(d["lost_reason"] for d in lost if d["lost_reason"]).most_common(3)))
    out.sort(key=lambda p: -p["won"])
    return out


def lines(personas):
    L = []
    for p in personas:
        L += [f"### {p['name']} ({', '.join(p['titles'])})", ""]
        L.append(f"- Won deals: {p['won']}. Lost deals: {p['lost']}. Interviews: {p['interviews'] or '[MISSING] none with this persona'}.")
        L.append("- Main pains (interviews): " + ("; ".join(f"{t} ({n})" for t, n in p["pains"]) if p["pains"] else "[MISSING] no interviews with this persona"))
        if p["triggers"]:
            L.append("- What triggers a search: " + "; ".join(p["triggers"]))
        if p["alternatives"]:
            L.append("- What they use today: " + "; ".join(p["alternatives"]))
        L.append("- Lead with: " + ("; ".join(f"{x['d']['claim']} (answers {h} interview pains)" for h, x in p["lead"]) if p["lead"] else "[MISSING] no pillar answers this persona's pains yet"))
        if p["proof_ids"]:
            L.append("- Usable proof: " + ", ".join(p["proof_ids"]))
        if p["avoid"]:
            L.append("- Do not lead with (competitors make the same claim): " + "; ".join(x["d"]["claim"] for x in p["avoid"]))
        if p["objections"]:
            L.append("- Objections in lost deals: " + "; ".join(f"{r} ({n})" for r, n in p["objections"]))
        L += ["- Message in your voice: [MISSING: one sentence for this persona, written by a person from the evidence above]", ""]
    return L
