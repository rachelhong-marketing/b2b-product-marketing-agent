"""Customer research plan: where the evidence is thin, who to talk to, what to ask, and a short survey.

The questions are neutral drafts for the product marketer to edit. The plan only says where more evidence would change a decision; it invents no findings.
Answers go back into customers/interviews.csv (using the same pain wording so they can be counted) and the proof register."""
from collections import Counter

from .util import has_phrase

MIN_INTERVIEWS = 5
MIN_NOTES = 3
MIN_PAIN = 3
BIG_OBJECTION = 3
SURVEY_NOTE = "Keep it short, offer an anonymous option, and do not send the same person more than two surveys a year. Treat a handful of replies as stories, not statistics."

Q = dict(
    persona=["Tell me about your role and what you are measured on.", "Tell me about the last time you dealt with this: \"{topic}\". What happened?",
             "What did you try first, and what happened?", "What does it cost you when it goes wrong, in time or in decisions?",
             "Who else gets involved, and what do they care about?", "What would have to be true for you to change how you handle it?",
             "What should I have asked that I did not?"],
    segment=["What triggered the search?", "Who owned the decision, and who could stop it?", "What did you compare against?", "What almost stopped the purchase?",
             "What would you tell a peer who is starting the same search?"],
    proof=["What changed after you started using it?", "What did it look like before, in numbers if you have them?", "How did you measure the change, and who checked it?",
           "Can we use this, with your name or without? Who has to approve it on your side?"],
    pillar=["When you run into \"{topic}\", how do you find out, and how long does it take?", "What do you do about it today?", "How often does it come up?", "What have you tried that did not work?"],
    objection=["What were you going to do instead?", "What was the deciding concern?", "What would have changed your mind?"],
    competitor=["Why did you look at {name}?", "What did they do well?", "What made you choose, or not choose, them?"],
)


def gaps(ctx):
    G = []
    pillar_topics = [a for x in ctx["pillars"] for a in x["d"]["answers"]]
    for p in ctx["personas"]:
        if p["interviews"] < MIN_INTERVIEWS:
            topic = p["pains"][0][0] if p["pains"] else (pillar_topics[0] if pillar_topics else "unreliable customer data")
            G.append(dict(kind="persona", priority=1 if p["interviews"] == 0 else 2, title=f"Persona: {p['name']}",
                          why=f"{p['interviews']} interviews with this persona (aim for at least {MIN_INTERVIEWS}). Their field guide rests on thin evidence.",
                          who=f"{p['name']} ({', '.join(p['titles'])})", topic=topic, adds="the field guide, the persona's pains and triggers, the pillars to lead with"))
    for x in ctx["pillars"] + ctx["no_proof"]:
        if len(x["usable"]) < 2:
            G.append(dict(kind="proof", priority=2, title=f"Proof: {x['d']['claim']}",
                          why=f"{len(x['usable'])} usable proof point(s); a pillar needs 2. " + ("; ".join(f"{pid}: {r}" for pid, r in x["unusable"]) or "None on file."),
                          who="A customer who has used this and can speak to a result, plus the person who approves it", topic=(x["d"]["answers"] or ["the result"])[0],
                          adds="new proof points in the register once the customer and the product marketer approve them"))
    for x in ctx["pillars"]:
        if 0 < len(x["hits"]) < MIN_PAIN or not x["hits"]:
            G.append(dict(kind="pillar", priority=3, title=f"Pain behind a pillar: {x['d']['claim']}", why=f"Mentioned in {len(x['hits'])} of {len(ctx['interviews'])} interviews (aim for at least {MIN_PAIN}).",
                          who="Buyers in the confirmed or leading segments", topic=(x["d"]["answers"] or ["this problem"])[0], adds="the case for leading with this pillar"))
    undecided = [s for s in ctx["segments"] if s["rankable"]]
    for s in undecided:
        n_int = sum(1 for i in ctx["interviews"] if has_phrase(i.get("industry", ""), s["industry"]))
        n_notes = ctx["sales_by_seg"].get((s["industry"], s["size"]), {}).get("n", 0)
        if n_int < MIN_PAIN and n_notes < MIN_NOTES:
            G.append(dict(kind="segment", priority=3, title=f"Segment: {s['industry']}, {s['size']}", why=f"{n_int} interviews and {n_notes} sales notes for a segment with {s['deals']} deals. Not enough to decide it with confidence.",
                          who=f"Buyers at {s['industry'].lower()} companies with {s['size']} employees, won and lost", topic="", adds="the ICP decision for this segment"))
    for reason, n in ctx["lost_reasons"]:
        if n >= BIG_OBJECTION:
            G.append(dict(kind="objection", priority=4, title=f"Objection: {reason}", why=f"{n} lost deals gave this reason and the response is still missing.",
                          who="People who passed on the product for this reason", topic=reason, adds="the objection response, from the buyer's side, for sales to write"))
    for name, n in ctx["lost_competitors"]:
        c = next((c for c in ctx["competitors"] if c["name"] == name), None)
        if c and not c.get("strengths"):
            G.append(dict(kind="competitor", priority=4, title=f"Competitor: {name}", why=f"Named in {n} lost deal(s) and the battlecard has no strengths yet.", who=f"Buyers who chose or seriously considered {name}",
                          topic="", name=name, adds="the battlecard's strengths and how to handle them, from buyers"))
    G.sort(key=lambda g: (g["priority"], g["title"]))
    return G


def guide(ctx):
    G = gaps(ctx)
    pains = sorted({i["pain"] for i in ctx["interviews"] if i.get("pain")})
    L = ["# Customer research plan: interview guide", "", f"Prepared as of {ctx['as_of'].isoformat()}. Draft questions for the product marketer to edit. Each section says where the evidence is thin and what the answers would change.", "",
         "Before you start: get consent, say how the notes will be used, and only quote someone who has agreed. Ask open questions and do not suggest the answer. Do not offer anything beyond what your policy allows.", ""]
    if not G:
        L.append("No gaps found against the minimums (5 interviews per persona, 3 for a pillar's pain, 2 usable proof points per pillar). Run this again after new data.")
    for i, g in enumerate(G, 1):
        L += [f"## {i}. {g['title']}", "", f"- Why: {g['why']}", f"- Who to talk to: {g['who']}", f"- What the answers feed: {g['adds']}", "", "Questions:", ""]
        for n, q in enumerate(Q[g["kind"]], 1):
            L.append(f"{n}. {q.format(topic=g['topic'] or 'this problem', name=g.get('name', ''))}")
        L.append("")
    L += ["## After each conversation", "",
          "Add one row to `customers/interviews.csv`: `interview_id, source, role, industry, pain, trigger, current_alternative, quote`. Reuse these pain labels where they fit, so the counts stay comparable:", ""]
    L += [f"- {p}" for p in pains] or ["- [MISSING] no pain labels yet; write each pain short and in the customer's words."]
    L += ["", "New proof points go in `company/proof-points.csv` only with a source, an approver and an expiry date. Only the product marketer approves them.", ""]
    return "\n".join(L)


def survey(ctx):
    roles = sorted({t for p in ctx["personas"] for t in p["titles"]})
    sizes = sorted({d["company_size"] for d in ctx["deals"] if d.get("company_size")})
    inds = sorted({d["industry"] for d in ctx["deals"] if d.get("industry")})
    pains = [t for t, _ in Counter(i["pain"] for i in ctx["interviews"] if i.get("pain")).most_common()]
    alts = [t for t, _ in Counter(i["current_alternative"] for i in ctx["interviews"] if i.get("current_alternative")).most_common()]
    opt = lambda xs: "; ".join(xs + ["Other (please say)"]) if xs else "[MISSING: options]"
    L = ["# Customer survey: question set", "", f"Prepared as of {ctx['as_of'].isoformat()}. Eight questions. Options come from the pains, alternatives, roles and segments already in your data. {SURVEY_NOTE}", ""]
    Qs = [("Which best describes your role?", "choose one", opt(roles)), ("How many employees does your company have?", "choose one", "; ".join(sizes) or "[MISSING: options]"),
          ("Which industry are you in?", "choose one", opt(inds)), ("Which of these problems matters most to you right now?", "choose one", opt(pains)),
          ("How do you handle it today?", "choose one", opt(alts)), ("How often does it cause a problem?", "choose one", "Every week; Every month; Every quarter; Rarely or never"),
          ("What is the biggest obstacle to fixing it?", "open answer", "-"), ("May we contact you for a short follow-up conversation?", "choose one", "Yes; No")]
    L += ["| # | Question | Type | Options |", "|---|---|---|---|"]
    L += [f"| {i} | {q} | {t} | {o} |" for i, (q, t, o) in enumerate(Qs, 1)]
    L += ["", "Survey owner: [MISSING: who sends it, and from which list]. Collection window: [MISSING]. Anything offered in return: [MISSING: decided by the product marketer, within company policy].", ""]
    return "\n".join(L)
