# Agent spec: product marketing agent

| Part | Decision |
|---|---|
| Role | Assists a product marketer. Drafts ideal customer profile (ICP) hypotheses, persona guides, positioning and pillars, keeps the proof-point register honest, and says what the evidence cannot support. The product marketer decides the ICP, the positioning and which claims are approved. |
| Tools | Read, Write, Bash (runs `python3 -m productmarketing`), Glob, Grep. No web access, no posting, no email. |
| Input | A private data folder: product profile, proof-point register, deals, target accounts, sales notes, interviews, competitors, decision record. |
| Workflow | Check data age → build → read → check → list the decisions and approvals only a person can make. |
| Decisions | Recorded in `decisions/icp-decisions.csv` by `decide` and `decisions/launch-decisions.csv` by `decide-launch`, only with a decision and a name. Until one segment is confirmed, every output says ICP: DRAFT. |
| Memory | None between runs except the decision record and the proof-point register, which are files the product marketer owns. |
| Output | `positioning-and-messaging.md`, `positioning.json` (for the campaign assistant), `brand-profile.json` (for the content strategy assistant), plus battlecards, persona field guides, one-sheet drafts, a playbook outline and launch triage. |
| Guardrails | Evidence next to every claim; no usable proof, no pillar; a target list is not proof of fit; small segments not ranked; public competitor data only; nothing invented; nothing sent. |
| Error handling | Missing or malformed files are named, not guessed around. A failed check twice stops the run with the remaining FAILs shown. |
| Asset rules | One-sheets are external: no internal research, only usable proof. Battlecards are internal and use public competitor information. `check-asset` enforces the proof, avoid-list and acronym rules. |
| Human steps | Export deals and the account list, collect sales input, run interviews, decide the ICP, approve and refresh proof points, write the final wording, supply objection responses. |

## Three ways to use it
1. **Skill:** ask Claude Code to build positioning from a data folder and walk through the decisions. Uses `.claude/skills/product-marketing/SKILL.md`.
2. **Agent:** `.claude/agents/product-marketing-agent.md`, started with `prompts/refresh.md`.
3. **Copilot:** `copilot/agent-instructions.md`. Copilot cannot run Python, so you paste the built document in and it does the judgment work only.
