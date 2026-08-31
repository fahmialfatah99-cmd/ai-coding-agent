# 🧠 Project Knowledge & Learned Conventions


### 📌 Superpowers Methodology and Skill Creation (Recorded: 2026-08-31 07:57)
Superpowers is a complete software development methodology for coding agents. It uses a set of composable skills and instructions to guide agents.

Key concepts:
- **Skills**: Reusable techniques, patterns, tools, or reference guides. They are NOT narratives.
- **Skill Priority**: Process skills (like brainstorming, systematic-debugging) come first, followed by implementation skills.
- **The Rule**: Agents MUST invoke relevant or requested skills BEFORE any response or action.
- **Skill Structure**: Skills live in a flat namespace directory (e.g., `skills/skill-name/SKILL.md`). They require YAML frontmatter with `name` and `description`.
- **Description Field**: Must start with "Use when..." and describe triggering conditions ONLY. NEVER summarize the skill's process or workflow in the description.
- **TDD for Skills**: Writing skills follows a RED-GREEN-REFACTOR cycle. You must test the skill with subagents (pressure scenarios) to ensure they follow the rules before deploying.
- **Bulletproofing**: For discipline-enforcing skills, explicitly close loopholes, build a rationalization table, and create a red flags list.
- **Flowcharts**: Use only for non-obvious decision points, not for reference material or linear instructions.
