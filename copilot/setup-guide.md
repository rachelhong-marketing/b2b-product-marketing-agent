# Copilot setup guide

1. In Microsoft Copilot Studio (or a Copilot agent builder), create a new agent named "Positioning reviewer".
2. Paste the text of `agent-instructions.md` into the instructions box.
3. Turn off web search and any connectors you do not need.
4. Run the tool on your computer first (`python3 -m productmarketing build ...`), then paste `positioning-and-messaging.md` into the Copilot chat.
5. Test with `docs/example-positioning-and-messaging.md`: the agent should flag the third pillar's missing proof and the expired proof point, point out the segment that needs a decision and the list-versus-wins warnings, leave the objection responses as [MISSING], and not invent any proof or record a decision for you.

What Copilot cannot do: run the Python tool, read your CRM export, or check acronyms and avoid words for you. Run `check` on your computer for that.
