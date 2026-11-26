---
name: studio
description: Creative and content production for claude.ai. Triggers on design, brand, art, theme, style, "write a doc", "draft content", "create a presentation", "internal update", "newsletter", resume, GIF, image, canvas, visual, poster, blog post, or any request to produce a polished creative deliverable. Routes to the right combination of claude.ai's tools: visualize:show_widget for inline diagrams/mockups/art, the docx/pptx/pdf skills for formal deliverables, frontend-design skill for HTML/React artifacts, image_search for reference imagery. Single-instance, no external services, no Ollama, no bespoke pipelines — just the right tool stack picked for the request.
---

# Studio — claude.ai Creative Production

The job: produce the polished thing the user actually wants. This skill is a router that picks the right claude.ai tool stack and ensures the relevant downstream skill is read before the work starts.

The Claude Code original absorbed twelve sub-skills (brand-guidelines, canvas-design, theme-factory, algorithmic-art, artifacts-builder, web-artifacts-builder, doc-coauthoring, image-enhancer, slack-gif-creator, internal-comms, content-research-writer, tailored-resume-generator). The concepts all survive. The plumbing is replaced by claude.ai's actual tools.

---

## Routing

| Request | Tool stack |
|---|---|
| Inline diagram (flowchart, system, sequence) | `visualize:show_widget` (diagram module) |
| Inline mockup (UI, dashboard, form) | `visualize:show_widget` (mockup module) |
| Inline interactive demo (widget, calculator, viz) | `visualize:show_widget` (interactive module) |
| Inline chart from data | `visualize:show_widget` (chart module) |
| Inline algorithmic / generative art | `visualize:show_widget` (art module) |
| Standalone HTML/React component | `frontend-design` skill + `create_file` to outputs |
| Word document (formal report, letter) | `docx` skill |
| Presentation (slide deck) | `pptx` skill |
| PDF deliverable (one-pager, formal doc) | `pdf` skill |
| Spreadsheet | `xlsx` skill |
| Blog post / article / essay | `create_file` as `.md`, then `present_files` |
| Long-form creative writing | `create_file` as `.md` |
| Reference imagery for any of the above | `image_search` |
| Resume | `docx` skill, content tailored to the job description |
| Internal update / newsletter | `.md` for chat consumption; `.docx` if formal |
| Slack GIF / animated visual | static SVG via `visualize:show_widget`; for actual animated GIF, bash sandbox with Pillow |

This skill doesn't *make* the deliverable — it picks the right downstream skill. Read the downstream `SKILL.md` before producing output, every time. The skills encode environment-specific constraints (available CSS classes, font availability, output paths) that won't be in your training data.

---

## Brand defaults

If the user is producing something for personal/general use and hasn't specified colors, a clean neutral palette works:

```
Background:  #faf9f5  (warm off-white)
Text:        #141413  (near-black)
Mid:         #b0aea5  (warm gray)
Accent:      #d97757  (warm orange) — use sparingly
Link/blue:   #3b82f6
```

If the user names a brand or specifies their own colors, use those. Don't override.

For data viz: avoid red-green-only color encoding (colorblind issue). Default to a colorblind-safe sequential palette like Viridis, or a small qualitative palette like Tableau 10.

---

## Workflow

### Step 1 — Clarify the format target

Before producing anything, confirm what format ships:
- "Inline" (renders in chat) → visualizer
- "File I can download / share / open later" → docx / pptx / pdf / xlsx / md / html
- "Interactive thing I can click" → frontend-design artifact (.jsx or .html)
- Ambiguous → ask once, briefly

A blog post is `.md` (or `.docx` if the user said "send to a client"). A "quick visual" is the visualizer. A "presentation for my team" is `.pptx`. Don't put a deck in markdown.

### Step 2 — Read the downstream SKILL.md

Always. Even if you're confident you know the format. The skills encode small constraints (e.g., pptx skill specifies which fonts ship in the container, frontend-design specifies which Tailwind classes are pre-compiled) that you'll get wrong if you skip the read.

### Step 3 — Produce

For longer deliverables, work iteratively: outline → flesh out → review → polish. Don't try to one-shot a 5-page document.

For visual deliverables, do a quick "is this any good" review pass before shipping. If it's ugly, fix it. If it's wrong-typeface or wrong-spacing, fix that. Polish is the deliverable, not an optional extra.

### Step 4 — Present

`present_files` on the deliverable. Brief one-paragraph summary of what's in it (not a recap of the content — the user will read the file).

---

## Reference imagery

When producing creative content that benefits from visual reference:

- Use `image_search` for: how does X actually look, what does this style of design typically include, examples of Y for inspiration
- Don't use `image_search` for: copyrighted characters, branded IP, celebrity photos, sports/movie/TV content, fashion magazines (these are blocked anyway)

For algorithmic/generative art the user wants original (no reference imagery), go straight to `visualize:show_widget` (art module).

---

## What got stripped from v1

- **theme-factory engine** — replaced by reading the relevant skill's design-tokens (frontend-design has them; pptx has them; docx has them)
- **canvas-design auto-generation pipeline** — replaced by `visualize:show_widget` modules
- **slack-gif-creator with FFmpeg pipeline** — bash sandbox can install FFmpeg for actual animated GIFs if requested; otherwise an animated SVG is usually a faster substitute
- **image-enhancer with local model** — claude.ai has no local image model; for image enhancement, suggest the user use an actual image tool (Photoshop, GIMP, Pixelmator, online enhancer)
- **tailored-resume-generator with ATS optimization model** — done by Claude reading the job description and tailoring content; the docx skill produces the file
- **content-research-writer with deep-research subroutine** — research uses `web_search` + `web_fetch`; writing uses `create_file`. No subroutines.
- **doc-coauthoring real-time collaboration** — claude.ai isn't real-time multi-user; it's turn-based with one user. Iteration happens turn by turn.

---

## Anti-patterns

- **Markdown for what should be a real file**: a "presentation" delivered as a markdown file with `## Slide 1` headers is not a presentation. Make a `.pptx`.
- **Visual without polish pass**: produce → check → fix → ship. Skipping the check produces draft-looking output.
- **Filler imagery**: don't add stock images for decoration. If an image isn't earning its place, leave it out.
- **Color spam**: a brand has 2–3 accent colors. If you're using 7 different colors in a single deliverable, the design has lost its anchor.
- **Skipping the downstream skill read**: this is the failure mode that produces "looked right in the preview but broke when opened" outputs.

---

## Tool reference

| Need | Tool |
|---|---|
| Inline visual (any kind) | `visualize:read_me` first, then `visualize:show_widget` |
| Reference imagery | `image_search` |
| Word doc | read `/mnt/skills/public/docx/SKILL.md`, then build |
| Presentation | read `/mnt/skills/public/pptx/SKILL.md`, then build |
| PDF | read `/mnt/skills/public/pdf/SKILL.md`, then build |
| Spreadsheet | read `/mnt/skills/public/xlsx/SKILL.md`, then build |
| HTML/React artifact | read `/mnt/skills/public/frontend-design/SKILL.md`, then build |
| Markdown deliverable | `create_file` directly |
| Present | `present_files` on the deliverable |
