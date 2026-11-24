# B2B Product Marketing Agent

> **B2B Campaign Lifecycle Toolkit**, step 1 of 7
>
> **1. Position** → [2. Plan](https://github.com/rachelhong-marketing/b2b-campaign-assistant) → [3. Content](https://github.com/rachelhong-marketing/b2b-content-strategy-assistant) → [4. Set up](https://github.com/rachelhong-marketing/b2b-paid-media-planner) → [5. Test](https://github.com/rachelhong-marketing/b2b-campaign-test-planner) → [6. Report](https://github.com/rachelhong-marketing/b2b-campaign-reporting-agent) → [7. Prove](https://github.com/rachelhong-marketing/b2b-pipeline-attribution-tool)

An AI agent for the work that comes before any campaign: who you sell to, what you say, and why anyone should believe it. It reads your closed deals, customer interviews and competitor list, then drafts the ideal customer profile (ICP), a positioning statement and messaging pillars, with the evidence next to every claim. It hands those to the Campaign Assistant (step 2) and the Content Strategy Assistant (step 3). It runs as a Claude Code skill and agent, with a small Python tool (standard library only) that does the counting and the checking.

All data here is made up. Fernhill Software is a fictional company that sells software to clean up duplicate and messy customer records in a customer relationship management (CRM) system.

## Why this exists

Campaigns fail upstream. If the team has not agreed on who the buyer is and what is true about the product, the theme, the content and the ads all inherit the guesswork. This tool puts the evidence on the table first: which segments you actually win and keep, what buyers say hurts, what competitors already claim, and which of your claims you can prove.

## What it does

```
Closed deals  +  customer interviews  +  competitor list  +  your claims and proof
        |
   rank segments  -->  find personas  -->  pick pillars  -->  flag gaps
        |
Positioning and messaging document  +  positioning.json  +  starter brand profile
```

| You ask | You get |
|---|---|
| "Who is our ideal customer?" | Segments ranked by win rate, contract value, speed and retention, with small groups marked "not ranked" |
| "Who do we sell to inside those companies?" | Buyer personas from won deals, with their main pain from interviews |
| "What should we say?" | A positioning statement with the evidence filled in and the sentences left for you, plus up to 3 messaging pillars with proof |
| "What can we not claim yet?" | Claims with no proof, and claims competitors also make |
| "What will buyers push back on?" | Objections from lost deals, with the responses left for sales to supply |

## Quick start

```bash
python3 -m productmarketing build --data sample-data --out-dir output
python3 -m productmarketing check output/positioning-and-messaging.md --profile sample-data/company/product-profile.json
python3 -m productmarketing icp --data sample-data
python3 -m unittest discover -s tests
```

`check` fails on a fresh build on purpose. It passes only when every [MISSING] slot is filled, every pillar has at least 2 sourced proof points, no word from your avoid list appears, and every acronym is spelled out.

## Inputs

See [docs/data-guide.md](docs/data-guide.md) for columns and how to export. Short version: `customers/deals.csv`, `customers/interviews.csv`, `market/competitors.csv`, `company/product-profile.json`.

## Example output

From the sample data (full file: [docs/example-positioning-and-messaging.md](docs/example-positioning-and-messaging.md)). The sample is the same fictional company, product, buyers and competitors as the [Campaign Assistant](https://github.com/rachelhong-marketing/b2b-campaign-assistant), so the toolkit tells one story. The deal and interview data are made up, and the results were built into them.

| Segment | Closed deals | Win rate | Average contract value | Days to close | 12-month retention | Score |
|---|---|---|---|---|---|---|
| Financial services, 1000-10000 employees | 12 | 58% | $94,643 | 120 | 71% | 59.7 |
| Retail, 1000-10000 employees | 14 | 64% | $69,463 | 87 | 78% | 58.6 |
| Healthcare, 1000-10000 employees | 8 | 38% | $68,850 | 98 | 67% | 40.0 |

```
### Pillar 1: Keep them out: monitoring so duplicate records don't come back

- Score 100.0. No tracked competitor makes this claim.
- Pain it answers: duplicates come back after cleanup. Mentioned in 11 of 30 interviews.
- Proof (customer survey, source: 2025 customer survey, n=120): Teams spend 30% of their week fixing data
- Proof (customer survey, source: 2025 customer survey, n=120): Customers cut data cleanup time by 40%
```

## Hand-off to the next steps

| File | Goes to | What it carries |
|---|---|---|
| `positioning.json` | [Campaign Assistant](https://github.com/rachelhong-marketing/b2b-campaign-assistant) (step 2) | ICP, personas, pillars with proof ids, competitors, words to avoid |
| `brand-profile.json` | [Content Strategy Assistant](https://github.com/rachelhong-marketing/b2b-content-strategy-assistant) (step 3) | Audiences, themes with trigger phrases and fit, competitors, words to avoid. The campaign block is added after step 2 |

A test loads the exported profile into the Content Strategy Assistant to make sure the two fit.

## Three ways to use it

| Way | What you do | Files |
|---|---|---|
| Skill (on demand) | Ask Claude Code to build positioning from a data folder, then write the sentences in your voice | `.claude/skills/product-marketing/SKILL.md` |
| Agent (refresh each quarter or after a big change) | Copy `.claude/agents/product-marketing-agent.md` into your project | `.claude/agents/`, `prompts/refresh.md`, `docs/agent-spec.md` |
| Copilot (judgment only) | Paste the document into a Copilot agent; no code runs | `copilot/` |

## Guardrails and limits

- **Evidence first.** Every pillar shows its proof and source. Gaps are [MISSING]. Objection responses and the positioning sentences are left for people. They are never invented.
- **No proof, no pillar.** A claim with no sourced proof cannot be a messaging pillar.
- **Small groups are not ranked.** A segment needs 5 closed deals and 3 wins.
- **Scores compare options in one run.** They are not forecasts, and a few deals move them a lot.
- **Competitor data is public information only.** Do not use confidential or leaked material.
- **Customer privacy.** Keep names out of the files. Keep your own data in a private folder, not in this repo.
- A human still decides the ideal customer, writes the words in the brand voice and checks every claim.

## Repo layout

```
.claude/skills/product-marketing/SKILL.md   the skill
.claude/agents/product-marketing-agent.md   the agent
prompts/refresh.md                          refresh prompt
copilot/                                    Copilot instructions and setup
productmarketing/                           icp, messaging, export, check, cli
sample-data/                                made-up deals, interviews, competitors, product profile
docs/                                       data guide, example outputs, agent spec
tests/                                      18 tests
```

## The B2B Campaign Lifecycle Toolkit

Seven tools, one per step of a B2B campaign, from positioning to proving pipeline. Each works on its own; together they cover the whole cycle. All sample data is made up.

| Step | Tool | What it does |
|---|---|---|
| 1. Position | **B2B Product Marketing Agent** (this repo) | Define who you sell to and what you say: ideal customer profile, positioning, messaging pillars and proof points, checked for gaps before any campaign starts. |
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
