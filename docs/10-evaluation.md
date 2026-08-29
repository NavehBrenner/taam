# 10 — Evaluation

The most important document in the repo. Everything else is a plan; this is what
tells us whether the plan worked.

> **Rule:** a modelling claim without a baseline is not a claim. Most hobby
> recommender projects skip this step and quietly lose to a one-line heuristic.

## The baselines

Every model result is reported against all three.

| Baseline | What it is | Why it matters |
|---|---|---|
| **B0 — global mean** | predict your average rating for everything | The floor. Losing to this means something is broken. |
| **B1 — community score** | predict the public rating | The `α`=1, `w`=0 corner of our own model. Beating it is what "personalised" means. |
| **B2 — your style average** | predict the mean of your past ratings for that style | **The real bar.** Deceptively strong. This is the one that usually wins, and the one nobody tests against. |

If the model cannot beat **B2**, then your palate is adequately described by
"which styles you like" and the entire content-based, profile-vector premise is
unnecessary. That is a legitimate finding, and an interesting one.

## The headline number: crossover N

Plot held-out error against N (number of check-ins used for fitting), for the
model and all three baselines.

```
error
  │
  │  ╲___                     B0
  │      ╲______              B1
  │  ╲          ╲_____        B2
  │   ╲___                    model
  │       ╲____
  │            ╲______
  └────┬────┬────┬────┬────→  N
      10   20   30   50
                 ↑
            crossover N
```

**Crossover N** — where the personal model overtakes the best baseline — is the
number this project exists to find. Prior estimate: **25–60 for beer**, and
considerably later for whisky (fewer, noisier samples).

Report it with a confidence interval. At these sample sizes a single crossing is
mostly noise; use repeated random splits.

## Protocol

- **Temporal splits, not random.** Your palate drifts and your rating scale
  drifts. Random splits leak the future into the past and will flatter the model.
- Report **MAE** (interpretable in rating units) as primary, and **Spearman ρ**
  on ranked candidate sets, because ranking is what recommendations actually do.
- Report **calibration**: do the ±1σ bands contain the truth ~68% of the time?
  A model that is honestly uncertain is doing its job even when it's inaccurate.
- Fixed seeds; one command reproduces every number (N-05).

## The noise ceiling

Before judging any model, measure **how consistently you rate the same beer**.
Repeat check-ins (R-15) give this directly.

If your test–retest MAE is 0.8 rating points, then a model achieving 0.9 is
close to the maximum achievable and calling it "not very good" is a
misunderstanding. **Establish this number early** — it reframes every result that
follows, and without it there is no way to tell a bad model from a hard problem.

## Profiler evaluation (separate, and prior)

Per `06-profiler.md`, on 200 held-out labelled beers:

- per-axis Pearson r vs. the labels, for each profiler in the chain
- vs. the **style-average profile** baseline (the same trap as B2, one level down)
- cross-source agreement on the calibration set — are the profilers even on the
  same scale?

Axes below r ≈ 0.4 get dropped from the vocabulary. This should happen before
any preference modelling, or the model is learning on sand.

## Qualitative evaluation

Not everything worth knowing is a number. Two checks worth running:

1. **The palate readout test.** Show Naveh the rendered palate. Does he agree?
   Disagreement is not automatically a model failure — it might be a genuine
   discovery about revealed vs. believed preference — but it is always
   informative.
2. **The blind menu test.** Take a real menu, have the model rank it, order its
   top pick and its bottom pick without looking, and see. Small N, high
   information, and much more fun than a validation curve.

## Sanity checks to run early

- Is `community_score` alone already predicting your ratings well? If `α` comes
  out near 1 with `w` near 0 at N=50, you just have mainstream taste, and that is
  worth knowing before building more.
- Are the profile axes actually varying across the beers you drink, or do you
  drink a narrow slice where every profile looks the same? A model cannot learn
  a weight for an axis that never moves. **This is a live risk** and it argues
  for exploration early (D-011).
- Is any single axis carrying all the predictive weight? If bitterness alone
  explains everything, most of the vector is decoration.

## What a negative result looks like

Worth naming in advance, so it isn't quietly avoided:

> "At N=60, the personal model does not beat the style-average baseline. My
> palate is well described by style preference. The profile vector adds nothing
> beyond what style already encodes."

That is a clean, honest, well-earned result. It goes in `DEAD-ENDS.md`, and it
would be a better outcome than a demo that looks good and can't be defended.
