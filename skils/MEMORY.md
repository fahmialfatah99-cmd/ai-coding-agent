# 🧠 Project Knowledge & Learned Conventions

### 📌 Superpowers Methodology and Skill Creation (Recorded: 2026-08-31 07:57)
Superpowers is a complete software development methodology for coding agents. It uses a set of composable skills and instructions to guide agents.

Key concepts:
- **Skills**: Reusable techniques, patterns, tools, or reference guides.
- **Skill Priority**: Process skills (brainstorming, debugging) come first, followed by implementation skills.
- **The Rule**: Agents MUST invoke relevant or requested skills BEFORE any response or action.
- **Skill Structure**: Flat namespace directory with YAML frontmatter.
- **Description Field**: Must start with "Use when..." and describe triggering conditions ONLY.
- **TDD for Skills**: RED-GREEN-REFACTOR cycle tested with pressure scenarios.

---

### 🎨 UI/UX Pro Max Design Intelligence (Recorded: 2026-08-31 08:06)
Complete design intelligence system for modern web, mobile, and desktop applications.

#### 1. Prioritized Design Categories & Rules:
1. **Accessibility (CRITICAL)**: WCAG AA contrast ratio ≥ 4.5:1 for normal text, 3:1 for large text. Proper `aria-label`, visible focus indicators (never remove focus rings), keyboard navigable (`Tab` & `Enter`).
2. **Touch & Interaction Targets (CRITICAL)**: Minimum interactive target size 44×44px with ≥8px spacing. Immediate visual state feedback on click/press.
3. **Performance (HIGH)**: Modern image formats (WebP/AVIF), lazy loading below the fold, zero Cumulative Layout Shift (CLS < 0.1).
4. **Style Selection & Visual Hierarchy (HIGH)**: Semantic SVG icons with meaningful labels (no emoji as primary UI icons). Cohesive visual style (Minimalism, Bento Grids, Glassmorphism, Brutalism, Neo-Brutalism).
5. **Responsive Layouts (HIGH)**: Mobile-first responsive breakpoints (`sm: 640px`, `md: 768px`, `lg: 1024px`, `xl: 1280px`). No horizontal overflow.
6. **Typography & Color Tokens (MEDIUM)**: Base body font 16px, line-height 1.5, headings line-height 1.2. Semantic CSS variables/tokens instead of hardcoded hex codes.
7. **Animation & Motion Physics (MEDIUM)**: Spring physics, exit animations faster than enter animations (e.g. enter 200ms, exit 150ms). Respect `prefers-reduced-motion`.
8. **Forms & Error Feedback (MEDIUM)**: Persistent floating or top labels (never placeholder-only labels), inline validation directly adjacent to fields, clear error summaries.
9. **Navigation Patterns (HIGH)**: Predictable back behavior, bottom navigation tabs limited to ≤ 5 items.
10. **Data Visualization & Charts (LOW)**: Accessible color palettes, interactive tooltips, and explicit legends.
