---
name: product-marketing
description: B2B go-to-market foundations. Builds the ideal customer profile (ICP), buyer personas, positioning statement and messaging pillars from closed deals, customer interviews, competitor claims and proof points, with the evidence next to every claim. Use when someone needs to define who to sell to, how to position a product, what the messaging pillars are, what claims can be proven, or needs the input for a campaign theme.
---

# Product Marketing Agent

Step 1 of the B2B Campaign Lifecycle Toolkit. It comes before the campaign assistant (theme, plan, master brief) and the content strategy assistant. You do the thinking and the writing in the brand's voice. The Python tool in this repo does the counting and the checking.

## Steps

1. **Collect inputs** (see `docs/data-guide.md`). Ask for: a closed-deals export from the CRM (names stripped), interview notes the user took, and public competitor pages. Help draft `company/product-profile.json` from the user's product material: the differentiators (claim, tags, the pains it answers, proof with a source) and the content topics. Show it for approval.
   - Never invent a deal, a quote, a customer result, a benchmark or a proof point. If the user has none, leave `proof` empty. The tool will say the claim cannot be a pillar yet.
2. **Build:** `python3 -m productmarketing build --data <folder> --out-dir output`
3. **Add judgment.** Read `positioning-and-messaging.md`.
   - Write the two open sentences of the positioning statement in the brand's voice, using only the evidence shown.
   - Check the ideal customer profile against what the user knows. If a segment is not ranked because of too few deals, say that plainly and do not argue it into the profile.
   - For each pillar, write a one-line pillar statement and one line per persona. Keep the proof exactly as given.
   - Objection responses come from sales and win-loss calls. Ask for them. Do not write them yourself.
4. **Check it:** `python3 -m productmarketing check output/positioning-and-messaging.md --profile <product-profile.json>`. Fix every FAIL. Run it again.
5. **Hand off.** `positioning.json` goes to the campaign assistant. `brand-profile.json` is the starter brand profile for the content strategy assistant: review it, add the campaign block after the campaign assistant has produced the master brief.
6. Show the whole updated document after any change, not only the changed part.

## Rules
- Every claim needs its evidence next to it. Missing evidence is written [MISSING].
- No proof, no pillar. Claims competitors also make are not the lead.
- Scores compare options in one run. They are not forecasts, and small groups are not ranked.
- Competitor information is public information only.
- Keep customer names out of every file. Keep real data out of the public repo.
- Keep the user's tone rules (words to avoid, plain language). Spell out every acronym on first use. Sound human, not polished.
