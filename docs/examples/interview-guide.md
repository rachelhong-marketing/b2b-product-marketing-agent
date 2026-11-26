# Customer research plan: interview guide

Prepared as of 2026-11-24. Draft questions for the product marketer to edit. Each section says where the evidence is thin and what the answers would change.

Before you start: get consent, say how the notes will be used, and only quote someone who has agreed. Ask open questions and do not suggest the answer. Do not offer anything beyond what your policy allows.

## 1. Persona: Finance leader

- Why: 3 interviews with this persona (aim for at least 5). Their field guide rests on thin evidence.
- Who to talk to: Finance leader (CFO, VP Finance)
- What the answers feed: the field guide, the persona's pains and triggers, the pillars to lead with

Questions:

1. Tell me about your role and what you are measured on.
2. Tell me about the last time you dealt with this: "duplicates come back after cleanup". What happened?
3. What did you try first, and what happened?
4. What does it cost you when it goes wrong, in time or in decisions?
5. Who else gets involved, and what do they care about?
6. What would have to be true for you to change how you handle it?
7. What should I have asked that I did not?

## 2. Proof: Find them: see how many duplicate records you have across systems

- Why: 1 usable proof point(s); a pillar needs 2. p6: expired 2026-09-30
- Who to talk to: A customer who has used this and can speak to a result, plus the person who approves it
- What the answers feed: new proof points in the register once the customer and the product marketer approve them

Questions:

1. What changed after you started using it?
2. What did it look like before, in numbers if you have them?
3. How did you measure the change, and who checked it?
4. Can we use this, with your name or without? Who has to approve it on your side?

## 3. Proof: Works across customer relationship management (CRM), billing and support systems

- Why: 0 usable proof point(s); a pillar needs 2. None on file.
- Who to talk to: A customer who has used this and can speak to a result, plus the person who approves it
- What the answers feed: new proof points in the register once the customer and the product marketer approve them

Questions:

1. What changed after you started using it?
2. What did it look like before, in numbers if you have them?
3. How did you measure the change, and who checked it?
4. Can we use this, with your name or without? Who has to approve it on your side?

## 4. Segment: Healthcare, 1000-10000

- Why: 2 interviews and 2 sales notes for a segment with 8 deals. Not enough to decide it with confidence.
- Who to talk to: Buyers at healthcare companies with 1000-10000 employees, won and lost
- What the answers feed: the ICP decision for this segment

Questions:

1. What triggered the search?
2. Who owned the decision, and who could stop it?
3. What did you compare against?
4. What almost stopped the purchase?
5. What would you tell a peer who is starting the same search?

## 5. Competitor: Datavault Pro

- Why: Named in 1 lost deal(s) and the battlecard has no strengths yet.
- Who to talk to: Buyers who chose or seriously considered Datavault Pro
- What the answers feed: the battlecard's strengths and how to handle them, from buyers

Questions:

1. Why did you look at Datavault Pro?
2. What did they do well?
3. What made you choose, or not choose, them?

## 6. Objection: chose a competitor

- Why: 8 lost deals gave this reason and the response is still missing.
- Who to talk to: People who passed on the product for this reason
- What the answers feed: the objection response, from the buyer's side, for sales to write

Questions:

1. What were you going to do instead?
2. What was the deciding concern?
3. What would have changed your mind?

## 7. Objection: doing it ourselves

- Why: 23 lost deals gave this reason and the response is still missing.
- Who to talk to: People who passed on the product for this reason
- What the answers feed: the objection response, from the buyer's side, for sales to write

Questions:

1. What were you going to do instead?
2. What was the deciding concern?
3. What would have changed your mind?

## 8. Objection: no budget

- Why: 6 lost deals gave this reason and the response is still missing.
- Who to talk to: People who passed on the product for this reason
- What the answers feed: the objection response, from the buyer's side, for sales to write

Questions:

1. What were you going to do instead?
2. What was the deciding concern?
3. What would have changed your mind?

## After each conversation

Add one row to `customers/interviews.csv`: `interview_id, source, role, industry, pain, trigger, current_alternative, quote`. Reuse these pain labels where they fit, so the counts stay comparable:

- duplicates come back after cleanup
- merging will break reports
- reports do not match
- which record is the right one

New proof points go in `company/proof-points.csv` only with a source, an approver and an expiry date. Only the product marketer approves them.
