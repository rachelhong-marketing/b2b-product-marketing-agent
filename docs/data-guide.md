# Data guide

All sample files are made up. Fernhill Software is a fictional company, the same one used across the toolkit. Use your own data in your own private folder, never in a public repo. Keep customer and account names out of every file.

## `customers/deals.csv` (from your CRM, one row per closed deal)

| Column | Meaning |
|---|---|
| deal_id | Any id. Do not put customer names in this file |
| industry, company_size | Your own groupings, for example "Retail" and "1000-10000" |
| buyer_role | The job title of the person who signed or led the buying |
| outcome | won or lost |
| acv | Annual contract value for won deals |
| days_to_close | Days from first meeting to decision |
| use_case | What they bought it for, from your own short list |
| retained_12m | For won deals older than a year: yes or no |
| lost_reason, competitor | For lost deals: the reason from the CRM, and the competitor named (or none) |

## `accounts/target-accounts.csv` (the target account list)

`account_id, industry, company_size, region, tech_stack, intent_topics, status`. Use ids, not names. `tech_stack` and `intent_topics` take several values separated by semicolons. Use the same industry and size groupings as `deals.csv`, so the two can be compared. The list needs at least 10 accounts to show patterns.

A target list reflects the filters used to build it. The document shows what the accounts have in common and then compares the list with your wins. Treat a pattern as a question to ask, not an answer.

## `customers/sales-input.csv` (short notes from sales)

`deal_id, rep_id, note_type, note, date`. `note_type` is why-won, why-lost, objection, trigger or other. Link every note to a `deal_id` from `deals.csv`, so notes can be counted by segment. Use rep ids, not names. Keep each note to one sentence. Mark made-up notes as made-up.

## `launches/launch-requests.csv` (new products or features waiting for a launch decision)

`launch_id, name, requested_by, target_date, claims, customers_impacted, customer_ask, value_to_prospects, differentiation, revenue_impact, usage_impact, roadmap_fit, notes`. Answers use few, some, many (customers_impacted); small, medium, large (customer_ask); low, medium, high (the next four); and no, partly, yes (roadmap_fit). `claims` is a list of differentiator ids separated by semicolons, so the plan can check their proof. `target_date` is YYYY-MM-DD and sets the 180-day review date. Leave an answer blank if it is unknown. Fewer than 5 answers means the result is undetermined.

## `launches/launch-results.csv` (goals and results for launches that have run)

`launch_id, goal_metric, goal_value, actual_value, direction, measured_on, source, notes`. One row per goal. `direction` is higher (more is better, the default) or lower. Give the source of every result. A result is what was measured, not proof the launch caused it. The review counts a goal as met at 100% or more of target, partly met from 50%, and missed below that (for "lower is better" goals: met at or under target, partly met up to 1.5 times the target).

## `company/approved-copy/` and `company/terminology.csv` (for the brand voice guide)

Put copy that is already approved and published in `approved-copy/` as `.md` or `.txt` files, one piece each. Under 1,000 words the guide labels the sample thin. `terminology.csv` has `use, dont_use, note`. Mark made-up copy as made-up.

## `customers/interviews.csv` (from your own interview notes)

`interview_id, source, role, industry, pain, trigger, current_alternative, quote`. One row per interview or customer call. Keep the pain short and in the customer's words. Use the same pain wording across rows so they can be counted. Only use quotes people agreed to share.

## `market/competitors.csv` (public information only)

Name, the claim from their own site, tags you assign (semicolon separated, the same tags as in your differentiators), price tier, the page you read, and optionally `strengths` (what buyers or their public materials say they do well). Leave `strengths` blank if you do not know; the battlecard will say it is missing. Do not use confidential or leaked material.

## `company/proof-points.csv` (the proof-point register)

`id, type, text, source, approved_by, approved_on, expires_on, notes`. A proof point is usable only if it has a source, an approver, an approval date, and has not expired. The document flags expired ones, ones expiring within 60 days and ones not yet approved. Only a person can approve a proof point.

## `company/product-profile.json`

- `differentiators`: each claim, its `tags`, the customer pains it `answers` (the same words your interviews use) and `proof` (a list of ids from the register). A claim with no usable proof cannot become a messaging pillar.
- `personas`: each persona's name and the buyer titles that belong to it. If you leave this out, each of the three most common buyer titles in won deals becomes a persona.
- `topics`: the content themes you want to be known for, with trigger phrases and the use case they match. These become the starter brand profile for the content strategy assistant.
- `avoid_words`, `known_acronyms`, `voice`.

## `decisions/icp-decisions.csv` (the product marketer's decisions)

`segment, decision, decided_by, date, note`. Written by `decide`. `decision` is confirmed, rejected or watch. The latest row for a segment wins. Until at least one segment is confirmed, every output says the ICP is a DRAFT.

## Launch triage points

Each of the seven answers is worth 0, 1 or 2 points. 9 or more points with a medium or high revenue impact suggests a market launch (marketing direct to customers). 5 to 8 suggests a sales launch (internal enablement and communication). Fewer suggests no launch. This is a suggestion. The product marketer decides.

## How the scores work

- **Segment score:** win rate 35%, average contract value 25%, speed to close 20%, 12-month retention 20%. Each part is scaled across the ranked segments in the same run. A segment needs 5 closed deals and 3 wins to be ranked.
- **Pillar score:** no tracked competitor makes the claim 40% (0.5 if one does, 0 if two or more do), customers mention the pain it answers 35%, usable proof on file 25% (2 usable proof points is full marks).

Scores compare options within one run. They are not forecasts.
