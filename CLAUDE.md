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
