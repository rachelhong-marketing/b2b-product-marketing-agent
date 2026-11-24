# Data guide

All sample files are made up. Fernhill Software is a fictional company. Use your own data in your own private folder, never in a public repo.

## `customers/deals.csv` (from your CRM, one row per closed deal)

| Column | Meaning |
|---|---|
| deal_id | Any id. Do not put customer names in this file |
| industry, company_size | Your own groupings, for example "B2B SaaS" and "200-1000" |
| buyer_role | The job title of the person who signed or led the buying |
| outcome | won or lost |
| acv | Annual contract value for won deals |
| days_to_close | Days from first meeting to decision |
| use_case | What they bought it for, from your own short list |
| retained_12m | For won deals older than a year: yes or no |
| lost_reason, competitor | For lost deals: the reason from the CRM, and the competitor named (or none) |

Export it from your CRM as a report. Strip names, emails and company names before saving.

## `customers/interviews.csv` (from your own interview notes)

One row per interview: role, industry, the pain in their words (short), the trigger event, what they use today, and one short quote. Only use quotes people agreed to share. Mark made-up ones as made-up.

## `market/competitors.csv` (public information only)

Name, the claim from their own site, tags you assign (semicolon separated, the same tags as in your differentiators), price tier and the page you read. Do not use confidential or leaked material.

## `company/product-profile.json`

- `differentiators`: each claim, its `tags`, the customer pains it `answers` (the same words your interviews use), and `proof` entries (type, text, source). A claim with no proof cannot become a messaging pillar.
- `topics`: the content themes you want to be known for, with `trigger` phrases and the `use_case` they match. These become the starter brand profile for the content strategy assistant.
- `avoid_words`, `known_acronyms`, `voice`.

## How the scores work

- **Segment score (ideal customer profile):** win rate 35%, average contract value 25%, speed to close 20%, 12-month retention 20%. Each part is scaled across the ranked segments in the same run. A segment needs 5 closed deals and 3 wins to be ranked.
- **Pillar score:** no tracked competitor makes the claim 40% (0.5 if one does, 0 if two or more do), customers mention the pain it answers 35%, proof on file 25% (2 proof points is full marks).

Scores compare options within one run. They are not forecasts.
