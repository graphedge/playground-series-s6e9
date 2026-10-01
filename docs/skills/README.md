# Kaggle Playground Skills

Reusable skill documents for Kaggle Playground Series competitions and general tabular ML workflows.

## Available Skills

### 1. [Playground OG-data Stack](./playground-og-data-stack.md)

**When to use**: Tabular Playground contests where an "original" or parent public dataset exists (e.g., S6E10 airline dataset aligned with Invistico/TJ Klein's public data).

**What it covers**:
- Aligning original dataset columns to competition train schema
- Marking original rows with `is_original` flag
- Combining datasets safely (no leakage, no double-counting)
- Training strategies: single model, dual models + blend, or stacking
- Validation checklist for distribution shift and ID overlap

**Expected lift**: +0.001 to +0.01 AUC depending on OG data quality and size.

---

### 2. [Arrival-Delay / Sparse Continuous Missingness](./arrival-delay-missingness.md)

**When to use**: Continuous operational features where `NaN` has semantic meaning distinct from zero (e.g., S6E10 `Arrival_Delay_in_Minutes`: `NaN` = not recorded, `0` = on-time, `>0` = late).

**What it covers**:
- Creating missing indicators before imputation
- Fold-safe imputation strategies (no target leakage)
- Optional delay gap features (arrival − departure)
- Distinguishing zero vs NA in operational contexts
- Generalization to other sparse continuous features

**Expected lift**: +0.001 to +0.005 AUC when missingness is informative.

---

## Usage

These skills are written for **agents and practitioners** working on Kaggle Playground Series competitions. Each skill includes:

- **When to Use This Skill**: Clear signals to trigger the pattern
- **Step-by-Step Execution**: Code templates and reproducible workflows
- **Common Pitfalls**: Table of mistakes, symptoms, and fixes
- **Validation Checklist**: Pre-submission verification steps

## Smoke Test

A lightweight validation suite is available to test both skills with synthetic data (no competition data required):

```bash
python3 docs/skills/test_skills_smoke.py
```

**Tests included**:
1. OG-data stack: column alignment, `is_original` flag, stratified folds
2. Arrival-delay missingness: missing indicator, fold-safe imputation, zero vs NA distinction
3. No target leakage validation

Expected: All assertions pass in <1 second.

## Context

These skills were created in the **playground-series-s6e9** repository but are designed to be **reusable across Playground competitions**. While S6E9 (Electric Vehicle Purchases) did not require these patterns, they support upcoming contests like **S6E10 (Airline Satisfaction)** which features:
- Original dataset integration (Invistico airline dataset)
- Arrival delay missingness pattern

## Related Files

- `/scripts/03_baselines.py` — Standard 5-fold CV baseline pattern (extend with these skills)
- `/docs/RESULTS.md` — Local experiment results and next-step candidates
- `/README.md` — Main repository README with getting-started guide

## Contributing

To add a new skill:
1. Follow the SKILL-style markdown format (see existing skills for template)
2. Include: When to Use, Step-by-Step Execution, Common Pitfalls, Validation Checklist
3. Provide code templates and concrete examples
4. Update this README with a summary entry

---

**Status**: Active  
**Owner**: EV/playground-series-s6e9  
**Last Updated**: 2026-10-01
