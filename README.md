# B2B Product Marketing Agent

> **B2B Campaign Lifecycle Toolkit**, step 1 of 7
>
> **1. Position** → [2. Plan](https://github.com/rachelhong-marketing/b2b-campaign-assistant) → [3. Content](https://github.com/rachelhong-marketing/b2b-content-strategy-assistant) → [4. Set up](https://github.com/rachelhong-marketing/b2b-paid-media-planner) → [5. Test](https://github.com/rachelhong-marketing/b2b-campaign-test-planner) → [6. Report](https://github.com/rachelhong-marketing/b2b-campaign-reporting-agent) → [7. Prove](https://github.com/rachelhong-marketing/b2b-pipeline-attribution-tool)

An assistant for the product marketer, for the work that comes before any campaign: who you sell to, what you say, and why anyone should believe it. It drafts and checks. **The product marketer decides.** It reads your closed deals, target account list, sales notes, customer interviews, competitor list and approved proof points, then produces ideal customer profile (ICP) hypotheses, persona field guides, a positioning statement draft and messaging pillars, with the evidence next to every claim. It hands those to the Campaign Assistant (step 2) and the Content Strategy Assistant (step 3). It runs as a Claude Code skill and agent, with a small Python tool (standard library only) that does the counting and the checking.

All data here is made up. Fernhill Software is a fictional company. It sells the Fernhill Data Quality Platform, which finds and merges duplicate customer records across systems. The same company, product, buyers and competitors appear across the toolkit.

## Why this exists

Campaigns fail upstream. If the team has not agreed on who the buyer is and what is true about the product, the theme, the content and the ads all inherit the guesswork. This tool puts the evidence on the table first: which segments you actually win and keep, what the target list and the sales team say, what buyers say hurts, what competitors already claim, and which of your claims you can prove today.

It does not replace the product marketer. The ideal customer profile, the final positioning and the approval of every claim stay with a person. The agent does the reading, counting, drafting and checking that takes the most time.

## What the agent does and what the product marketer decides

| Job | The agent | The product marketer |
|---|---|---|
| Ideal customer profile (ICP) | Ranks segments from closed deals, finds patterns in the target account list, compares the list with wins, counts sales notes, and says how many deals each pattern rests on | Decides which segments are the ICP and records it. Until then the profile is marked DRAFT everywhere |
| Persona field guides | Fills in each persona's pains, triggers and objections from interviews and deals, and what to lead with | Writes the message for each persona |
| Positioning and messaging | Drafts the statement parts and picks pillars from claims that have usable proof and that no tracked competitor makes | Writes the sentences and signs off |
| Proof points | Keeps a register with source, approver and expiry date, and flags anything unusable | Approves each proof point |
| Competitors | Flags claims competitors also make so you do not lead with them | Chooses what to claim |
| Objections | Lists them from lost deals | Supplies the responses with sales |

## What it produces

| Output | Command | Built from | A person adds |
|---|---|---|---|
| Positioning and messaging document, with ICP hypotheses | `build` | Deals, target accounts, sales notes, interviews, competitors, proof register | The ICP decision, the positioning sentences, approvals |
| Persona field guides | `fieldguides` | Interviews, deals, pillars, usable proof | The message for each persona, first-call questions |
| One-sheet drafts (external) | `onesheets` | Approved pillars and usable proof only | Headline, problem, customer quote, call to action |
| Battlecards (internal) | `battlecards` | Public competitor claims, your deals and sales notes | Strengths, how to handle them, from sales |
| Launch triage and plan skeletons | `launches` | Seven answers per launch request, linked claims | The answers, the market or sales launch decision, measurement goals |
| Sales playbook outline | `playbook` | The confirmed ICP, personas, pillars, objections | The talk tracks, handoff rules |
| Asset check | `check-asset` | The proof register and your avoid list | Fixes |

In terms of what a product marketing team does: it supports **positioning** (personas, differentiation, field guides, one-sheets), **market intelligence** (win and loss counts, gaps, battlecards) and **launches** (triage and plan skeletons), and it drafts the skeleton for **enablement** (the playbook outline). It does not make decks, training courses, demos, email nurtures or customer surveys. Examples of each output are in `docs/examples/`.

## What it does

```
Closed deals + target accounts + sales notes + interviews + competitors + proof register
        |
   rank segments --> compare with target list --> persona guides --> pillars --> flag gaps
        |
Positioning and messaging document  +  positioning.json  +  starter brand profile
        |
Product marketer records decisions (decide)  -->  ICP status becomes CONFIRMED
```

## Quick start

```bash
python3 -m productmarketing build --data sample-data --out-dir output --as-of 2026-11-24
python3 -m productmarketing check output/positioning-and-messaging.md --profile sample-data/company/product-profile.json
python3 -m productmarketing icp --data sample-data
python3 -m productmarketing proofs --data sample-data --as-of 2026-11-24
python3 -m productmarketing battlecards --data sample-data --out-dir output --as-of 2026-11-24
python3 -m productmarketing fieldguides --data sample-data --out-dir output --as-of 2026-11-24
python3 -m productmarketing onesheets --data sample-data --out-dir output --as-of 2026-11-24
python3 -m productmarketing launches --data sample-data --out-dir output --as-of 2026-11-24
python3 -m productmarketing playbook --data sample-data --out-dir output --as-of 2026-11-24
python3 -m productmarketing check-asset output/one-sheets/data-leader.md --data sample-data --as-of 2026-11-24
python3 -m productmarketing decide-launch --data my-data --launch L1 --decision market --by "Your Name"
python3 -m productmarketing decide --data my-data --segment "Retail, 1000-10000" --decision confirmed --by "Your Name"
python3 -m unittest discover -s tests
```

`check` fails on a fresh build on purpose. It passes only when the ICP has a recorded decision, every [MISSING] slot is filled, every pillar has at least 2 usable proof points, no word from your avoid list appears, and every acronym is spelled out. `decide` records a decision only when it is given a decision and a name.

## Inputs

See [docs/data-guide.md](docs/data-guide.md) for columns and how to export each one.

| File | What it is |
|---|---|
| `customers/deals.csv` | Closed deals from your CRM, names removed |
| `accounts/target-accounts.csv` | The target account list (ids and attributes, no names) |
| `customers/sales-input.csv` | Short notes from sales, tied to a deal |
| `customers/interviews.csv` | Customer interview and call notes |
| `market/competitors.csv` | Public competitor claims |
| `company/product-profile.json` | Differentiators, personas, content topics, words to avoid |
| `company/proof-points.csv` | The proof-point register |
| `launches/launch-requests.csv` | Launch requests with the seven triage answers and the claims each rests on |
| `decisions/icp-decisions.csv` | The product marketer's ICP decisions (written by `decide`) |
| `decisions/launch-decisions.csv` | The product marketer's launch decisions (written by `decide-launch`) |

## Example output

From the sample data (full file: [docs/example-positioning-and-messaging.md](docs/example-positioning-and-messaging.md)). The sample is the same fictional company, product, buyers and competitors as the [Campaign Assistant](https://github.com/rachelhong-marketing/b2b-campaign-assistant). The data is made up, and the results were built into it.

| Segment | Closed deals | Win rate | Average contract value | Days to close | 12-month retention | Score | On target list | Product marketer decision | Note |
|---|---|---|---|---|---|---|---|---|---|
| Financial services, 1000-10000 employees | 12 | 58% | $94,643 | 120 | 71% | 59.7 | 19 | confirmed (Sample Product Marketer, 2026-11-10) |  |
| Retail, 1000-10000 employees | 14 | 64% | $69,463 | 87 | 78% | 58.6 | 22 | confirmed (Sample Product Marketer, 2026-11-10) |  |
| Healthcare, 1000-10000 employees | 8 | 38% | $68,850 | 98 | 67% | 40.0 | 1 | needs decision |  |

### Target list compared with wins

- On the list, no wins: Insurance, 1000-10000 (6 accounts, 0 closed deals). Ask why before spending on it.
- Winning where the list barely looks: Healthcare, 1000-10000 (3 wins, 1 on the list).


Proof-point register (as of 2026-11-24):

| Ref | Proof | Type | Source | Approved by | Status | Used by |
|---|---|---|---|---|---|---|
| p1 | Teams spend 30% of their week fixing data | customer survey | 2025 customer survey, n=120 | Sample Product Marketer | usable: expires soon (2026-12-31) | Keep them out |
| p2 | Customers cut data cleanup time by 40% | customer survey | 2025 customer survey, n=120 | Sample Product Marketer | usable: expires soon (2026-12-31) | Keep them out, Merge them |
| p3 | Setup in under two weeks | implementation records | Implementation records, 2025 median | Sample Product Marketer | usable: expires soon (2026-12-31) | Set up in under two weeks |
| p4 | Made-up: a regional bank merged its customer records and month-end reports did not change | customer result | made-up customer webinar | Sample Product Marketer | usable: valid until 2027-06-30 | Merge them |
| p5 | Made-up: duplicate count shown within one day of connecting a system | benchmark | made-up implementation note | Sample Product Marketer | usable: valid until 2027-05-01 | Find them |
| p6 | Made-up: the first scan found duplicates in all 20 pilot accounts | benchmark | made-up pilot summary | Sample Product Marketer | Not usable: expired 2026-09-30 | Find them |
| p7 | Made-up: a retailer cut duplicate customer records by half in one quarter | customer result | made-up customer story | not approved | Not usable: not approved | none yet |

## Hand-off to the next steps

| File | Goes to | What it carries |
|---|---|---|
| `positioning.json` | [Campaign Assistant](https://github.com/rachelhong-marketing/b2b-campaign-assistant) (step 2) | ICP status and confirmed segments, personas with what to lead with, pillars with usable proof, the proof register status, competitors, words to avoid |
| `brand-profile.json` | [Content Strategy Assistant](https://github.com/rachelhong-marketing/b2b-content-strategy-assistant) (step 3) | Audiences, themes with trigger phrases and fit, competitors, words to avoid. The campaign block is added after step 2 |

If the ICP is still a DRAFT, the exported files say so. A test loads the exported profile into the Content Strategy Assistant to make sure the two fit.

## Three ways to use it

| Way | What you do | Files |
|---|---|---|
| Skill (on demand) | Ask Claude Code to build positioning from a data folder, then work through the decisions with you | `.claude/skills/product-marketing/SKILL.md` |
| Agent (refresh each quarter or after a big change) | Copy `.claude/agents/product-marketing-agent.md` into your project | `.claude/agents/`, `prompts/refresh.md`, `docs/agent-spec.md` |
| Copilot (judgment only) | Paste the document into a Copilot agent; no code runs | `copilot/` |

## Guardrails and limits

- **The product marketer decides.** The agent never records an ICP decision, never approves a proof point and never signs off a claim. `decide` refuses an empty name.
- **Evidence first.** Every pillar shows its proof and source. Gaps are [MISSING]. Objection responses and the positioning sentences are left for people. They are never invented.
- **No usable proof, no pillar.** Proof must have a source, an approver and an approval date, and be in date.
- **One-sheets are for customers, so they are stricter.** The body carries no interview counts or internal research, only proof points that are usable today. `check-asset` fails a one-sheet that breaks this.
- **Battlecards are internal and use public information about competitors only.** What a competitor is good at and how to handle them are left [MISSING] for sales to supply.
- **Launch triage is a suggestion.** It shows the points behind it, marks unanswered questions, and a person records the decision.
- **A target list is not proof of fit.** It reflects how the list was built. The document compares it with wins before anyone relies on it.
- **Small groups are not ranked.** A segment needs 5 closed deals and 3 wins. Sales notes are counted by segment and show how many reps said it.
- **Scores compare options in one run.** They are not forecasts, and a few deals move them a lot.
- **Competitor data is public information only.** Do not use confidential or leaked material.
- **Customer privacy.** Keep names out of the files. Keep your own data in a private folder, not in this repo.

## Repo layout

```
.claude/skills/product-marketing/SKILL.md   the skill
.claude/agents/product-marketing-agent.md   the agent
prompts/refresh.md                          refresh prompt
copilot/                                    Copilot instructions and setup
productmarketing/                           icp, accounts, sales, decisions, proofs, personas, messaging, battlecards,
                                            fieldguides, onesheets, launches, playbook, export, check, cli
sample-data/                                made-up deals, accounts, notes, interviews, competitors, proof points, launches, decisions
docs/                                       data guide, example outputs (docs/examples), agent spec
tests/                                      63 tests
```

## The B2B Campaign Lifecycle Toolkit

Seven tools, one per step of a B2B campaign, from positioning to proving pipeline. Each works on its own; together they cover the whole cycle. All sample data is made up.

| Step | Tool | What it does |
|---|---|---|
| 1. Position | **B2B Product Marketing Agent** (this repo) | Assist the product marketer: draft ideal customer profile hypotheses from deals, target accounts and sales notes, plus persona guides, positioning and messaging pillars backed by approved proof. The product marketer decides. |
| 2. Plan | [B2B Campaign Assistant](https://github.com/rachelhong-marketing/b2b-campaign-assistant) | Turn the positioning into a campaign theme, write the campaign plan and master brief, then draft channel briefs, keywords, landing page and ad copy, all checked before launch. |
| 3. Content | [B2B Content Strategy Assistant](https://github.com/rachelhong-marketing/b2b-content-strategy-assistant) | Pick content topics inside the campaign theme from audience questions, news, competitors and keyword data, outline and check each piece so search and AI answer tools can quote it, and log whether AI answers cite you. |
| 4. Set up | [B2B Paid Media Planner](https://github.com/rachelhong-marketing/b2b-paid-media-planner) | Plan channels and retargeting, then build and check tracking links before launch. |
| 5. Test | [B2B Campaign Test Planner](https://github.com/rachelhong-marketing/b2b-campaign-test-planner) | Plan tests in waves, let the ad platform call the winner, check MQLs, and size tests when volume is small. |
| 6. Report | [B2B Campaign Reporting Agent](https://github.com/rachelhong-marketing/b2b-campaign-reporting-agent) | Consolidate ad platform and CRM data into one file, check every channel and funnel stage for gaps, and draft insights. |
| 7. Prove | [B2B Pipeline Attribution Tool](https://github.com/rachelhong-marketing/b2b-pipeline-attribution-tool) | Check the CRM data can be trusted, then show sourced and influenced pipeline. |

### Which tool is for your role

Teams are organized by function, and the steps cut across them. Start here:

| If you are a... | Start with |
|---|---|
| Product marketer | [1. Product Marketing Agent](https://github.com/rachelhong-marketing/b2b-product-marketing-agent) |
| Demand gen or campaign manager | [2. Campaign Assistant](https://github.com/rachelhong-marketing/b2b-campaign-assistant), [4. Paid Media Planner](https://github.com/rachelhong-marketing/b2b-paid-media-planner), [5. Campaign Test Planner](https://github.com/rachelhong-marketing/b2b-campaign-test-planner) |
| Content marketer | [3. Content Strategy Assistant](https://github.com/rachelhong-marketing/b2b-content-strategy-assistant) |
| Paid media manager | [4. Paid Media Planner](https://github.com/rachelhong-marketing/b2b-paid-media-planner), [5. Campaign Test Planner](https://github.com/rachelhong-marketing/b2b-campaign-test-planner) |
| Marketing operations or analytics | [5. Campaign Test Planner](https://github.com/rachelhong-marketing/b2b-campaign-test-planner), [6. Campaign Reporting Agent](https://github.com/rachelhong-marketing/b2b-campaign-reporting-agent), [7. Pipeline Attribution Tool](https://github.com/rachelhong-marketing/b2b-pipeline-attribution-tool) |

## About the author

**Rachel Hong** has worked in B2B demand generation and marketing analytics for more than ten years, at marketing and advertising technology companies. She builds campaigns, reporting and the AI workflows that help marketing teams plan and measure them.

[LinkedIn](https://www.linkedin.com/in/rachelhongatbaruch/)

## License

MIT. See `LICENSE`.
