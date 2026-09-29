---
security_level: INTERNAL
leak_class: formation_leftover
kernel_fit: keep_architecture
---

# Repo Landscape Deck (Reporting)

## 1. Skill Signature

Read a repository's documents (README, specs, docs, skills, stack reports, governance notes) and produce a **landscape** slide deck: first as reviewable Markdown, then as HTML, exportable to **PDF** or **PowerPoint**.

**Intake lane:** `repo_landscape_deck` — not stack fingerprint (`repo-stack-inspect`), not borrow queue (`skill-borrowing-hopper`), not PDF render QA (`pdf-report-review`).

**Invoke:** `-ex @repo-landscape-deck <path-or-slug>` · companion template: [repo-landscape-deck-template.md](repo-landscape-deck-template.md)

**Deploy to target repos:** `speckit-bootstrap.sh --target <path> --withskills` copies this skill from `.github/dist/repo-skills/` (catalog: `manifest.json`) into `.github/skills/core-operations/reporting/` on the target.

## 2. Rationale

Operators need a fast way to turn scattered repo knowledge into a presenter-ready landscape deck without hand-building slides from scratch. Markdown prototypes keep iteration cheap; HTML plus export paths keep delivery flexible (browser PDF print, Marp, or Pandoc PPTX).

## 3. Input-Schema

```json
{
  "target_repository_path": "string (required)",
  "repository_slug": "string (optional; inferred from git remote or dirname)",
  "audience": "operator | stakeholder | technical (default: operator)",
  "depth": "executive | standard | deep (default: standard)",
  "output_dir": "string (default: <repo>/docs/presentations/<slug>-landscape/)",
  "phase": "markdown_only | html | export (default: markdown_only)"
}
```

**Example Input:**

```json
{
  "target_repository_path": "/path/to/SkillStack2",
  "repository_slug": "skillstack2",
  "audience": "stakeholder",
  "depth": "standard",
  "phase": "markdown_only"
}
```

## 4. Output-Schema

```json
{
  "landscape_deck": {
    "markdown_path": "string",
    "html_path": "string | null",
    "pdf_path": "string | null",
    "pptx_path": "string | null",
    "source_index": ["string (paths read)"],
    "slide_count": "number",
    "verdict": "string (one line)"
  }
}
```

## 5. Workflow

### Phase A — Discover (read-only)

1. Confirm `target_repository_path` exists and list candidate sources in priority order:
   - Root `README.md`, `docs/README.md`, `docs/**/*.md`
   - `specs/**/spec.md`, `specs/**/quickstart.md`
   - `.github/skills/**/README.md`, skill bodies referenced by indexes
   - Stack reports (`**/stack-report.md`, `docs/projects/*/stack-report.md`)
   - Governance / intake notes only when they change the story (`docs/intake/*.md`)
2. Record every file read in `source_index`. MUST NOT invent facts not supported by those files.
3. If `repo-stack-inspect` output exists for the repo, MAY cite its resume one-liner and execution path — do not duplicate a full stack report unless `depth` is `deep`.

### Phase B — Markdown prototype (default stop)

1. Write `landscape-deck.md` under `output_dir` using [repo-landscape-deck-template.md](repo-landscape-deck-template.md).
2. **One idea per slide.** Use `---` horizontal rules between slides (Marp-compatible).
3. Landscape intent: design for 16:9; avoid long paragraphs; prefer bullets, tables, and diagrams.
4. Title slide MUST name the repo, audience, and date. Closing slide MUST list `source_index` paths (abbreviated if > 12).
5. Stop after Markdown unless `phase` is `html` or `export`. State a one-line verdict.

### Phase C — HTML (when `phase` is `html` or `export`)

1. Split `landscape-deck.md` on `---` into slides.
2. Emit `landscape-deck.html`: single file, embedded CSS, `@page { size: landscape; }`, each slide in `<section class="slide">`.
3. Default viewport: 1920×1080 logical; `overflow: hidden` per slide; system font stack.
4. MUST NOT depend on a CDN for first render. Optional: add Reveal.js only if operator asks for live presenter mode.

### Phase D — Export (when `phase` is `export`)

Pick the first tool that is available; report which was used in `verdict`:

| Target | Preferred command | Fallback |
|--------|-------------------|----------|
| PDF | `npx @marp-team/marp-cli landscape-deck.md --pdf -o landscape-deck.pdf` | Open HTML in headless Chrome / `playwright pdf` with landscape print CSS |
| PPTX | `npx @marp-team/marp-cli landscape-deck.md --pptx -o landscape-deck.pptx` | `pandoc landscape-deck.md -o landscape-deck.pptx` |

After export, if a PDF exists and the target repo ships a PDF render-review skill, run it before delivery.

## 6. Deployment (`--withskills`)

Target repos that already use SkillStack bootstrap get this skill from the repo-skills catalog:

1. Canonical copies live in `.github/dist/repo-skills/repo-landscape-deck.md` and `repo-landscape-deck-template.md` (synced from this path).
2. `manifest.json` maps them to `.github/skills/core-operations/reporting/` on the target.
3. Operator runs:

```bash
.github/skills/skillstack/speckit-bootstrap.sh --target /path/to/project --withskills
```

4. On the target, invoke `-ex @repo-landscape-deck .` with default output `docs/presentations/<slug>-landscape/`.
5. Deck artifacts stay in the target repo working tree; catalog copy does not auto-commit.

Register via classify-transfer before changing the catalog. Bump `entity-registry.json` when adding the registry row.

## 7. Constraints

- MUST prototype in Markdown before HTML or export unless operator explicitly skips (`phase` override with written reason).
- MUST keep slides landscape-oriented (16:9). Portrait decks are out of scope.
- MUST NOT paste secrets, credentials, or denylist tokens from `test_soul_export_leakage.sh` into slides.
- MUST NOT auto-commit deck artifacts unless operator asks.
- Customer/repo-specific nouns stay in the deck body; this skill file stays generic.

## 8. Skeptic lenses

| Lens | Check |
|------|-------|
| Strategy | Does the deck answer why this repo exists for the stated `audience`? |
| Pivot | Is every slide traceable to a `source_index` path? |
| Skeptic | Are we summarizing docs, not inventing architecture? |
