---
security_level: INTERNAL
leak_class: formation_leftover
kernel_fit: keep_architecture
---

# Repo Landscape Deck — Markdown template

Copy into `<output_dir>/landscape-deck.md`. Replace bracketed placeholders. One slide per `---` block.

```markdown
---
marp: true
theme: default
size: 16:9
paginate: true
---

# [Repository display name]

**Audience:** [operator | stakeholder | technical]  
**Date:** [YYYY-MM-DD]  
**One-liner:** [from README or stack report, < 25 tokens]

---

## What this repo is

- [Purpose bullet — cite README or spec]
- [Primary user or operator]
- [What is explicitly out of scope]

---

## Document landscape

| Area | Key files | Takeaway |
|------|-----------|----------|
| Entry | `README.md` | [one line] |
| Specs | `specs/...` | [one line] |
| Docs | `docs/...` | [one line] |
| Skills | `.github/skills/...` | [one line] |

---

## Architecture (as documented)

```mermaid
flowchart LR
  A[Source docs] --> B[Synthesis]
  B --> C[Landscape deck]
```

- [Component or boundary from specs/docs]
- [Integration or dependency called out in docs]

---

## How work gets done

| Move | Evidence |
|------|----------|
| [e.g. CI / scripts / skills invoked] | `[path]` |
| [e.g. governance loop] | `[path]` |

---

## Risks and gaps

- [Missing doc, stale spec, or untested claim — cite path or "not found"]
- [Open question for operator]

---

## Next hops

1. [Concrete follow-up tied to repo docs]
2. [Optional export: HTML → PDF / PPTX]

---

## Sources

- `[relative/path/from/repo/root]`
- `[...]`
```

## HTML shell (when promoting past Markdown)

Minimal single-file pattern. Split Markdown slides on `---`, wrap each in `<section class="slide">`, inject this CSS:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>[slug] landscape deck</title>
  <style>
    @page { size: landscape; margin: 0.5in; }
    * { box-sizing: border-box; }
    body { margin: 0; font-family: system-ui, sans-serif; background: #111; color: #eee; }
    .slide {
      width: 100vw; height: 100vh; padding: 3rem 4rem;
      display: flex; flex-direction: column; justify-content: center;
      page-break-after: always;
    }
    h1 { font-size: 2.4rem; margin: 0 0 1rem; }
    h2 { font-size: 1.8rem; margin: 0 0 0.75rem; }
    table { border-collapse: collapse; width: 100%; font-size: 0.95rem; }
    th, td { border: 1px solid #444; padding: 0.4rem 0.6rem; text-align: left; }
    code { background: #222; padding: 0.1rem 0.3rem; border-radius: 3px; }
  </style>
</head>
<body>
  <!-- one <section class="slide"> per Markdown slide -->
</body>
</html>
```

Print to PDF from the browser with landscape orientation, or use Marp CLI for PDF/PPTX from the Markdown source.
