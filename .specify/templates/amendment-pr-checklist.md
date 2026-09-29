# Amendment Proposal: <title>

<!-- Fill in all required fields below before opening a PR. -->
<!-- The amendment-gate CI job validates this metadata. -->

## Metadata

| Field           | Value                                      |
|-----------------|--------------------------------------------|
| **id**          | `YYYY-MM-DD-<short-slug>`                  |
| **proposer**    | @github-username                           |
| **date**        | YYYY-MM-DD                                 |
| **target_version** | v0.X.Y                                  |
| **status**      | draft \| review \| ratified \| superseded |
| **reviewers**   | @reviewer1, @reviewer2                     |

---

## Rationale

<!-- Why is this amendment needed? What problem does it solve?
     Be specific: cite constitution section(s), failing tests, or user-facing issues. -->

### Problem Statement

> _Describe the gap or issue in the current constitution._

### Proposed Change

> _One-sentence summary of what this amendment adds, removes, or modifies._

---

## Diff Summary

<!-- List the exact sections being changed in constitution.md. -->

### Sections Modified

- [ ] Section X — _section name_: _brief description of change_
- [ ] Section Y — _section name_: _brief description of change_

### New Sections Added

- [ ] Section Z — _section name_: _brief description_

### Sections Removed / Deprecated

- [ ] Section W — _section name_: _reason for removal_

---

## Tests

<!-- List tests that validate this amendment's enforcement. All tests must pass before ratification. -->

| Test File | Description | Status |
|-----------|-------------|--------|
| `tests/unit/test_<slug>.sh` | Unit: _what it tests_ | ⬜ pending |
| `tests/integration/test_<slug>.sh` | Integration: _what it tests_ | ⬜ pending |

### Test Execution

```bash
# Run all amendment-related tests
bash tests/unit/test_<slug>.sh
bash tests/integration/test_<slug>.sh
```

---

## Impact Assessment

### Compatibility

- [ ] No breaking changes to existing rules or hooks
- [ ] Breaking changes present — migration guide provided below

### Migration Guide (if breaking)

> _If existing users need to update their config, hooks, or rules.xml, explain how._

### Affected Components

- [ ] `rules.xml` / `rules-schema.xsd`
- [ ] `bin/drift-engine` / `src/drift/drift_engine.sh`
- [ ] `src/vibe/` (nudge/personality system)
- [ ] `bin/specfarm-pre-commit`
- [ ] `.specify/` configuration files
- [ ] CI workflows (`.github/workflows/`)
- [ ] Other: ___

---

## Checklist

### Proposer

- [ ] Amendment id follows naming convention (`YYYY-MM-DD-<slug>`)
- [ ] `target_version` is a valid semver bump from current constitution version
- [ ] All modified/added sections are listed in the Diff Summary
- [ ] All tests are listed in the Tests table
- [ ] Tests pass locally (`bash tests/unit/test_<slug>.sh && bash tests/integration/test_<slug>.sh`)
- [ ] No breaking changes OR migration guide is provided
- [ ] Amendment file placed in `.specify/amendments/YYYY-MM-DD-<slug>.md`

### Reviewer

- [ ] Rationale is clear and justified
- [ ] Diff accurately reflects what changed in `constitution.md`
- [ ] Tests cover the new/changed behaviour
- [ ] No unintended side-effects on other constitution sections
- [ ] `target_version` is appropriate for scope of change
- [ ] CI `amendment-gate` job passes (requires `.github/workflows/phase4-compliance.yml`; see `specs/004-specfarm-phase-4/tasks.md#T140`)

---

## References

- Related issue / PR: #
- Constitution section(s): Section X, Section Y
- Phase: Phase _N_
- Related tasks: T___
