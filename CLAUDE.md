# Working instructions for an AI session on this repo

## Orientation

Read `CONTEXT.md` first, then `DECISIONS.md`. Do not read the whole `docs/` tree
before doing anything — read the one or two files relevant to the task.

## The prime directive of this repo

**Do not lock decisions.** This project is in an exploratory phase and the owner
has explicitly asked that alternatives be preserved. Concretely:

- Do not delete an option from `DECISIONS.md` because you think it's inferior.
  Argue for a lean; keep the alternatives.
- Do not write "we decided X" in a doc. Write "current lean: X, because …".
- If an approach is genuinely falsified **by evidence you produced**, move it to
  `DEAD-ENDS.md` with the numbers, and leave a pointer in `DECISIONS.md`.
  Reasoning alone is not falsification.
- If you introduce a new option, add it to the register. New options are always
  welcome.

## Standing engineering rules

1. **Every model claim needs a baseline.** Global mean, community score, and
   style-average of past ratings. Especially the third — it is deceptively strong
   and beating it is the actual bar. A result reported without baselines should
   be treated as not reported.
2. **Report uncertainty.** A point prediction from N=20 samples is misleading.
3. **Profiles are computed once and cached forever.** Store `profiler_version`,
   `source`, and `retrieved_at` on every row. Never silently re-profile.
4. **If an LLM produces a number that enters the model,** it must be temperature
   0, schema-constrained, anchored with fixed exemplars, ensembled over k≥3, and
   validated against held-out labels before it is trusted.
5. **Never drop context data** because it isn't modelled yet.
6. **Nothing domain-specific goes in `preference/` or `recommend/`.** If a change
   there mentions beer, the abstraction is leaking. See `docs/11-multi-domain.md`.

## Workflow — non-negotiable

Full detail in `docs/14-workflow.md`. The short version:

1. **No work without a Linear issue.** If one is not filed, file it (project
   `taam · טעם`, team `NVB`) before writing code.
2. **Branch off the issue** using Linear's own `gitBranchName`, so the issue,
   branch and PR link themselves.
3. **Walk it through before the PR, and stop.** Once the three checks pass, run
   the `issue-walkthrough` skill (`.claude/skills/issue-walkthrough/SKILL.md`):
   what the issue asked, what we found with baselines and uncertainty, what
   moved in the register, what failed. Present it and **wait for Naveh's
   response**. Do not open the PR in the same turn. This is research; the
   finding is the deliverable and a diff does not carry it.
4. **Open a PR. Never merge it.** `main` is protected and Naveh is the only
   merger. Do not push to `main`.
5. Use `git switch`, not `git checkout`.
6. **The plugin reflex.** When Naveh asks for a code change, ask whether the
   rule behind it can be enforced by a qualety rule instead of remembered by
   the next session. Instructions here are advisory; CI is not.
7. **Anything about qualety is filed upstream**, with
   `gh issue create -R NavehBrenner/qualety` — a new rule, a false positive, a
   bug. Never a Linear issue in this project: that board is for taam's work,
   and a Linear issue is invisible to whoever fixes qualety.
8. If qualety flags correct code, file the false positive upstream and disable
   the rule with a pointer to that issue. Do not contort the code to please it.
9. The three checks are `qualety check`, `pytest`, `mypy`. Run them before
   opening a PR — CI runs exactly the same three.

## Style

- Small, readable, well-named Python. Notebooks for exploration, modules for
  anything that gets reused.
- Prefer scipy/sklearn/numpy over deep learning frameworks. At this data scale,
  a deep learning dependency is a smell.
- Plots over tables where a plot is clearer; both where the numbers matter.

## When you finish a piece of work

Update, in this order: the relevant `docs/` file, `DECISIONS.md` (if a lean
moved), `DEAD-ENDS.md` (if something died), and `ROADMAP.md` (if a milestone
closed). A code change that leaves the docs stale is incomplete.

## What the owner cares about

Naveh is doing this for fun and for the ML. He would rather have an honest
negative result with a clean experiment behind it than a demo that looks good
and can't be defended. Interpretability is not a nice-to-have here — "what does
my palate actually look like" is half the point of the project.
