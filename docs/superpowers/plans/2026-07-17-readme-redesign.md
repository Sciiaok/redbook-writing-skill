# README Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite the repository README so a Xiaohongshu operator immediately understands the value, terminology, proof, and first-use path, while an engineer can verify every major claim.

**Architecture:** Keep the installable Skill unchanged and make `README.md` the product-facing layer. The README will move from feature inventory to a funnel: operator pain → evidence-led workflow → professional vocabulary → concrete scenarios → install/run → proof and boundaries. A separate design spec remains the source for the information architecture.

**Tech Stack:** GitHub-flavored Markdown, Mermaid flowchart, existing Markdown/CSV/YAML repository artifacts, Python unittest and the existing strict validator.

## Global Constraints

- Primary audience: Xiaohongshu content operators and creators; secondary audience: Agent/Skill developers.
- Use real repository facts only: 7 references, 13 assets, 130 source rows, 75 claim rows, 59 query rows, 84 passing tests, and strict validation with 0 errors / 0 warnings.
- Explain professional terms in plain Chinese; never turn CES, a fixed traffic pool, publishing frequency, or conversion rate into a platform fact.
- Do not change files under `redbook-writing/`; the README refresh must not change Skill behavior or the frozen Skill bundle hash.
- Do not claim user counts, install counts, success rates, platform approval, or guaranteed reach.
- Keep sensitive-content, authenticity, commercial-eligibility, comment, and cross-platform boundaries visible.

---

### Task 1: Rewrite the README around the operator decision path

**Files:**
- Modify: `README.md`
- Reference: `docs/superpowers/specs/2026-07-17-readme-redesign-design.md`
- Reference: `redbook-writing/SKILL.md`, `redbook-writing/references/*.md`, `tests/evals/forward-results.json`

**Interfaces:**
- Consumes: existing Skill routes, templates, evidence snapshot, evaluation artifacts, and repository commands.
- Produces: a GitHub-facing README whose first screen answers what it is, who it is for, why it is credible, and how to start.

- [ ] **Step 1: Replace the current feature-list opening with the approved hero and proof bar.**

Use the positioning line “把‘找爆款’变成可复核的内容实验”, explain the operator outcome in one short paragraph, and show only verified proof points: 7 references, 13 assets, 130 source rows, 75 claim rows, 59 query rows, 84/84 tests, and strict validation 0 error / 0 warning.

- [ ] **Step 2: Add the operator pain-to-method table and vocabulary glossary.**

Define CES, fixed traffic-pool claims, cold start, account baseline, median, counterexample, `primary_job`, primary/ proxy metric, `directional` attribution, `SKU × offer × platform × account_scope × surface`, and the four run modes. Each term gets a plain-language interpretation and a boundary.

- [ ] **Step 3: Add the end-to-end workflow diagram.**

Use a Mermaid flowchart with these nodes in order: problem definition → query tree → notes-first sampling → author reverse lookup → baseline/high/low/counterexample → evidence-bound topic → six gates → draft double review → primary metric experiment. The diagram must make clear that a failed gate stops downstream production.

- [ ] **Step 4: Add three scenario cards with concrete prompts and outputs.**

Cover: CES/200 exposure folklore, zero-sample gay-category discovery, and cross-platform adult-product acquisition. Each card must state the correct Skill behavior, not invent a success story.

- [ ] **Step 5: Add the shortest install and first-run template.**

Keep the copy-paste install path, then provide a prompt template containing category, audience situation, primary job, available evidence/materials, commercial goal, and content boundaries. Link directly to the Skill and the relevant templates.

- [ ] **Step 6: Close with proof links and explicit boundaries.**

Link to the Skill, research snapshot, strict validator, tests, evaluation rubric, and draft-quality reference. Present “不会做什么” as product capabilities: no fake-real stories, fake tests, fabricated metrics, competitor poaching, login/captcha bypass, or unapproved commercial CTA.

### Task 2: Review the README as product copy and as repository documentation

**Files:**
- Modify: `README.md` only if review finds a concrete issue.
- Check: all Markdown links in `README.md`.

**Interfaces:**
- Consumes: Task 1 README and the same repository facts.
- Produces: a concise, credible README with no unsupported claims, broken links, contradictory terminology, or unreadable sections.

- [ ] **Step 1: Run a claim audit.**

Check every number and superlative against repository files. Remove any unsupported “第一、最强、保证、爆款、智能” phrasing unless it is clearly framed as positioning rather than a factual performance claim.

- [ ] **Step 2: Run a terminology audit.**

For every black word, confirm that the README distinguishes official fact, supported experience, hypothesis, contradicted evidence, and unknown. Confirm `primary_job` is singular and that `directional` is not presented as user-level attribution.

- [ ] **Step 3: Run a link and Markdown audit.**

Verify repository-relative links exist, Mermaid fences close, tables render, headings have a logical hierarchy, and the first screen is readable without loading reference files.

### Task 3: Validate, commit, and publish the README refresh

**Files:**
- Check: `README.md`, `docs/superpowers/specs/2026-07-17-readme-redesign.md`, `redbook-writing/`, `tests/`, `evidence-snapshots/`.

**Interfaces:**
- Consumes: completed README and unchanged frozen Skill bundle.
- Produces: a clean commit with passing tests and a pushed GitHub branch/main update if the user authorizes the repository update.

- [ ] **Step 1: Run the existing tests and strict evidence validator.**

Run:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 redbook-writing/scripts/validate_run.py evidence-snapshots/2026-07-16-platform-mechanisms --strict
git diff --check
```

Expected: all tests pass, `VALID_COMPLETE: 0 error(s), 0 warning(s)`, and no diff-check output.

- [ ] **Step 2: Confirm the frozen Skill bundle is unchanged.**

Recompute the repository’s Skill bundle hash using the same path-and-bytes algorithm in `tests/test_eval_artifacts.py`; it must remain `da4fdd33f1db880ed3e9d0d46a9e778c51d0abb8d8bf869459cb4b99795f0b90`.

- [ ] **Step 3: Inspect the final diff and commit.**

Run `git status --short`, `git diff --stat`, and `git diff --check`. Commit with:

```bash
git add README.md docs/superpowers/plans/2026-07-17-readme-redesign.md
git commit -m "Improve README for operators and Skill builders"
```

- [ ] **Step 4: Push the authorized repository update.**

Push the current branch, then fast-forward `main` only if the user’s repository request still includes publishing the change:

```bash
git push -u origin codex/build-redbook-writing-skill
git push origin HEAD:main
```

