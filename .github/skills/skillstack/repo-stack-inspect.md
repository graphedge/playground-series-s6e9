---
security_level: INTERNAL
leak_class: formation_leftover
kernel_fit: keep_architecture
---

# Repo Stack Inspect Skill (Lane 1 Adjacent)

## 1. Skill Signature

Inspect any local repository and emit a stack report: **resume one-liner** (required, < 25 tokens), tech stack inventory, and **how we got it done** (execution path — not product purpose).

**Intake lane:** `stack_inspect` — not governance onboarding (`repo-onboarding`), not codebase learning (`project-onboarding`), not tactical branch progress (`dev-progress-status`).

**Invoke:** `/stack-inspect` · `-ex @stack-inspect <path-or-slug>` · **`repostackreport <path> [--playwright] [--cdp] ...`**

**Generator:** `.github/skills/skillstack/repo-stack-inspect.sh` · **`bin/repostackreport`**

## 2. Rationale

Project profiles capture strategic **Role** (purpose). Dev-progress tracks branch-level tactics. Neither records a concise stack fingerprint plus the execution moves that shipped the work. This skill fills that gap for any local checkout without Lane 1 manifest prerequisites.

## 3. Input-Schema

```json
{
  "target_repository_path": "string (required)",
  "repository_slug": "string (optional; inferred from git remote or dirname)",
  "focus_lenses": ["playwright | cdp | persistent-profile | ci | all-patterns (optional; implies patterns section scope)"],
  "output_mode": "agent_only | skillstack | both (default: both in SkillStack2 workspace, else agent_only)",
  "confidence_threshold": "number (default: 0.70)"
}
```

**Example Input**:

```json
{
  "target_repository_path": "/path/to/alert-agent",
  "repository_slug": "alert-agent",
  "focus_lenses": ["playwright", "cdp", "persistent-profile"],
  "output_mode": "both"
}
```

## 4. Output-Schema

```json
{
  "stack_report": {
    "path": "docs/projects/<slug>/stack-report.md",
    "format": "markdown",
    "generated_at": "ISO 8601 timestamp",
    "source_artifacts": ["string"]
  },
  "resume_oneliner": {
    "text": "string (< 25 whitespace-separated tokens)",
    "token_count": "integer"
  },
  "patterns_and_problems": [
    {
      "pattern_or_problem": "string",
      "what_we_did": "string",
      "tradeoff": "string",
      "evidence": "string",
      "confidence": "high | medium | low"
    }
  ],
  "fingerprint": {
    "path": "string (optional JSON sidecar path)",
    "format": "json"
  },
  "audit_log": {
    "files_scanned": "number",
    "signals_found": "number",
    "warnings": ["string"]
  }
}
```

## 5. Execution-Logic

### Step 1: Fingerprint (deterministic)

**Preferred CLI** (focus lenses imply patterns-solved scope):

```bash
repostackreport <target_repository_path> --playwright --cdp --persistent-profile \
  --json-out /tmp/stack-fingerprint.json
```

**Low-level wrapper:**

```bash
sh .github/skills/skillstack/repo-stack-inspect.sh \
  --path <target_repository_path> \
  --slug <repository_slug> \
  --focus playwright,cdp \
  --strict-focus \
  --json-out /tmp/stack-fingerprint.json
```

The shell script scans manifest files, nested manifests, languages, CI workflows, execution evidence paths, and automation pattern signals. No network access.

**Focus lenses** (Claude Code-style agent settings):

| Flag | Lens | Mines |
|------|------|-------|
| `--playwright` | Playwright | `playwright`, `launch_persistent`, `headed`, automation scripts |
| `--cdp` | CDP | `cdp`, `SESSION_MODE`, `remote-debugging`, liveops docs |
| `--persistent-profile` | Persistent Profile | `user_data_dir`, session profiles |
| `--ci` | CI | `ci_workflows`, Makefile/Actions gates |
| `--all-patterns` | All | full `pattern_signals` scan (no filter) |

No focus flags → **auto-detect** from `pattern_signals`. Explicit lenses → **always** emit patterns section with derived title (e.g. `## Playwright + CDP — Patterns Solved`). Omit section when auto mode finds no signals.

### Step 2: Synthesize report (agent)

Merge fingerprint JSON with narrative synthesis. **Do not** restate product purpose, audience, or project-profile `Role`.

### Step 2b: Extract patterns and problems (focus-implied)

When fingerprint `patterns_section.required` is true, populate the section using fingerprint `patterns_section.title` and scoped `pattern_signals` / `scoped_ci_workflows`.

**Explicit focus lenses** (`repostackreport --playwright --cdp`): mine only evidence for those lenses; section title is derived from lens labels.

**Auto mode** (no flags): emit section only when `pattern_signals` non-empty; title is `Patterns and Problems Solved`.

**Mining order (read-only):**

1. `specs/prompts/*liveops*`, `research-liveops*`, `handoff-*`, `todo-*` prompts
2. Env/config surfaces: `**/config.py`, `*.env.example`, README ops sections
3. Automation backends: `**/backends/*.py`, `**/session/*.py`, `scripts/*.ps1`
4. Tests naming the fix: `test_*_pick_page*`, `test_*_config*`, smoke scripts

**Do not** duplicate feature rows from How We Got It Done — patterns are cross-cutting (e.g. session mode applies across multiple features).

**Required report structure** — resume one-liner is the first content block after the title:

```markdown
# Stack Report: <Display Name>

> **Resume one-liner** (< 25 tokens): <how this stack shipped work — not why it exists>

**Slug**: `<slug>`
**Generated**: <ISO 8601>
**Source**: repo-stack-inspect-v1.2; <evidence paths> or focus flags used
**Repository**: <local path or remote URL>

## How We Got It Done

Do **not** restate product purpose, audience, or Board Role.

| What we had to get done | How we did it | Constraints / tradeoffs | Evidence | Confidence |
|-------------------------|---------------|-------------------------|----------|------------|
| ... | ... | ... | specs/001-foo/plan.md | high |

## <Focus Labels> — Patterns Solved

(Required when `patterns_section.required` is true; omit entirely in auto mode with no signals.)

Reusable execution patterns and fixes — not product purpose.

| Pattern or problem | What we did | Tradeoff / residual risk | Evidence | Confidence |
|--------------------|-------------|--------------------------|----------|------------|
| ... | ... | ... | scripts/start-chrome-cdp.ps1 | high |

## Tech Stack

| Layer | Technology | Version | Evidence |
|-------|------------|---------|----------|
| Language | ... | ... | ... |

## Architecture Summary

(≤200 words: entry points, key modules, data flow)

## Gaps and Review Items

- `[REVIEW REQUIRED: ...]` where evidence is thin

## Audit

- files_scanned, signals_found, warnings[]
```

**Resume one-liner rules:**

- Exactly one line, immediately under the `#` title (blockquote format above).
- **< 25 tokens** (whitespace-separated words; same family as 014 subfeature cap).
- Resume voice: how work shipped, not mission/why.
- Contract fail if missing, wrapped across lines, or ≥ 25 tokens.

Example: `Shipped POSIX kernel export plus frozen registry gates without network deps.`

### Step 3: Write artifacts

| Mode | Destination |
|------|-------------|
| `agent_only` | Conversation output only |
| `skillstack` / `both` | `docs/projects/<slug>/stack-report.md` (+ optional `stack-report.json`) |
| Target repo (`--withskills`) | Local draft `.specify/onboarding/stack-report.md` — operator handoff to SkillStack2 |

Do **not** modify strategic profile `Role`. Optional later: cross-link from Lane 1 Record.

### Inspection sources (read-only)

| Signal | Sources |
|--------|---------|
| Languages | extensions, `.gitattributes` |
| Dependencies | `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `Gemfile`, `requirements*.txt` |
| Runtime / infra | `Dockerfile`, `docker-compose*.yml`, `Procfile`, `fly.toml` |
| CI/CD | `.github/workflows/`, `.gitlab-ci.yml`, `Makefile`, `justfile` |
| How it got done | `CHANGELOG*`, `specs/**/{spec,plan,tasks,research}.md`, `RUN.md`, `git log --oneline -30` — **not** README mission copy |
| Architecture | `bin/`, `src/`, `cmd/`, `app/` entry points |

## 6. Constraints

- **SkillStack operator only** (Constitution I.B): lives under `.github/skills/skillstack/`.
- **No Lane 1 manifest required** for inspection.
- **No purpose/Role restatement** in stack reports.
- **Resume one-liner required** on every report; < 25 tokens.
- **No network** in fingerprint script.
- **No third-party packages** in fingerprint script.
- Stack reports are **unregistered sidecars** in v1; register only when exporting to `gbsoul-internal`.
- PUBLIC `grokbot-soul` export of stack reports is out of scope (INTERNAL ceiling).

**Contract:** `specs/025-repo-stack-inspect/contracts/stack-report-contract.md`  
**Quickstart:** `specs/025-repo-stack-inspect/quickstart.md`  
**Owner:** SkillStack  
**Status:** Active
