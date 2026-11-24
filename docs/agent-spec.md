# Agent spec: product marketing agent

| Part | Decision |
|---|---|
| Role | Turns deals, interviews, competitor claims and proof into the ideal customer profile, positioning and messaging pillars, and says what the evidence cannot support. |
| Tools | Read, Write, Bash (runs `python3 -m productmarketing`), Glob, Grep. No web access, no posting, no email. |
| Input | A private data folder: product profile, deals, interviews, competitors. |
| Workflow | Check data age → build → read → check → list what the user must supply. |
| Memory | None between runs. Keep the previous output file and compare by hand. |
| Output | `positioning-and-messaging.md`, `positioning.json` (for the campaign assistant), `brand-profile.json` (for the content strategy assistant). |
| Guardrails | Evidence next to every claim; no proof, no pillar; small segments not ranked; public competitor data only; nothing invented; nothing sent. |
| Error handling | Missing or malformed files are named, not guessed around. A failed check twice stops the run with the remaining FAILs shown. |
| Human steps | Export deals, run interviews, supply proof and objection responses, write the final wording, decide the ideal customer. |

## Three ways to use it
1. **Skill:** ask Claude Code to build positioning from a data folder. Uses `.claude/skills/product-marketing/SKILL.md`.
2. **Agent:** `.claude/agents/product-marketing-agent.md`, started with `prompts/refresh.md`.
3. **Copilot:** `copilot/agent-instructions.md`. Copilot cannot run Python, so you paste the built document in and it does the judgment work only.
