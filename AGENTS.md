# Project Guidelines & Skill Integration

## Frontend Design Skills (taste-skill)

The workspace is configured with the **taste-skill** suite under `.agents/skills/`. Whenever building, redesigning, or refining frontend code, UI layouts, styling, or animations for this project, activate and adhere to the appropriate taste skills:

- **Primary Frontend Skill (`design-taste-frontend`)**:
  Anti-slop frontend design framework. Infers design language, adjusts dials (`DESIGN_VARIANCE`, `MOTION_INTENSITY`, `VISUAL_DENSITY`), bans AI defaults, enforces GSAP/CSS spatial dynamics and crisp typography.

- **High-End Visual Design (`high-end-visual-design`)**:
  Applied for polished, agency-tier visual polish, soft glassmorphism, OLED dark mode, custom font choices, fluid spring motion, and premium card layouts.

- **Project Redesign & Audit (`redesign-existing-projects`)**:
  Applied when auditing or refactoring existing pages, component styling, layout hierarchy, and micro-interactions.

- **Stricter GPT/Codex Rules (`gpt-taste`)**:
  Applied for strict layout variance, motion choreography, and high-quality UI code generation.

- **Minimalist & Brutalist Variations (`minimalist-ui`, `industrial-brutalist-ui`)**:
  Applied when specific minimalist or industrial/brutalist design directions are requested.

- **Full Output Enforcement (`full-output-enforcement`)**:
  Ensures complete code outputs with zero placeholders or truncated sections.

- **Image-to-Code Pipeline (`image-to-code`, `imagegen-frontend-web`, `imagegen-frontend-mobile`, `brandkit`)**:
  Used when generating UI reference boards or implementing frontend components based on visual mocks.

## Execution Rules
- Always output a 1-line **Design Read** before generating major UI code changes.
- Avoid default AI visual slop (generic purple gradients, boring 3-card grids, Inter font defaults, instant state changes).
- Maintain responsive, dynamic design and rich aesthetics according to project context.
