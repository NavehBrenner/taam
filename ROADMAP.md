# Roadmap

Ordered by **risk retired per hour spent**, not by what's satisfying to build.

The project is expected to hit dead ends. Each milestone therefore has explicit
**kill criteria** — the observation that would tell us this path is wrong. Hitting
one is a success: it means we learned something cheaply. Record it in
`DEAD-ENDS.md` and pick a different option from `DECISIONS.md`.

---

## M0 — Profiler validation (the falsification experiment)

**Do this first.** It is the highest-risk component and it can be settled in a day.
Everything downstream is worthless if item profiles are garbage.

> **Status: harness written and verified** —
> `scripts/m0_profiler_validation.py`, controls in `tests/test_m0_harness.py`.
> Needs only `data/raw/beer_profile_and_ratings.csv` (see `data/README.md`).
> It runs a style-average baseline, a numerics-only ridge, and a
> TF-IDF-text + numerics ridge, then prints per-axis Pearson r and a verdict.
>
> TF-IDF rather than sentence embeddings deliberately: no model download, fully
> deterministic, and a fair fight at ~3k rows. If it beats the baseline,
> swapping in a sentence encoder is a tuning step, not a rescue.

1. Download the Kaggle Beer Profile set (~3.2k beers, labelled descriptor vectors).
2. Hold out 200 beers.
3. Profile them **three ways**, from name + brewery + style + description only:
   - a trained regressor (sentence embedding ⊕ structured fields → descriptors)
   - a temperature-0 LLM with anchor exemplars, k=5, per-axis median
   - style-average baseline (the profile of the average beer of that style)
4. Report per-axis Pearson r for each method against the labels.

**Success:** at least one method gets r > 0.7 on bitterness, sweetness, body.
**Kill criteria:** no method beats the style-average baseline on any axis. If the
style average is as good as everything else, then "profile" is just a laundered
style label — and the whole content-based premise is in trouble. Go read D-001
and D-002 again, and consider that the honest project might be style-based.

**Also produced here:** the per-axis correlation table decides which axes survive
into the vector at all. Drop anything under r ≈ 0.4.

---

## M1 — Profile space structure

1. PCA the labelled profile vectors. How many components for 80% variance?
2. Try to name the components. Look at the extremes of each.
3. k-means in profile space; check which styles dominate each cluster.

**Success:** ≤5 components explain ≥80%, and at least PC1 and PC2 are nameable.
This directly sets the parameter count for M3.
**Kill criteria:** variance is spread flat across 12+ components. Then the taste
space is genuinely high-dimensional, small-N learning gets much harder, and
D-003/D-006 need rethinking (probably toward a stronger prior, D-007 option C).

---

## M2 — Catalog and logging (the boring, essential part)

1. Schema per `docs/04-data-model.md`. SQLite.
2. catalog.beer client + Untappd client, both cached permanently to local disk.
3. Manual-entry path (D-005 option C) — this is not optional garnish.
4. Check-in flow: rating + questions + **context/mood tags**.
5. **Start logging beers immediately, before any model exists.**

The single most valuable thing in the whole roadmap is *starting to collect data
early*, including context you cannot yet use. There is no way to backfill it.

**Kill criteria:** none. This has to happen regardless of which modelling path wins.

---

## M3 — Preference model v1

1. Implement the decomposition: `α·community + w·profile + b`.
2. Bayesian linear regression on the reduced axes from M1.
3. Report posterior mean and uncertainty for every prediction.
4. Palate readout: the weight vector, in words.

**Kill criteria:** see M4. v1 is not allowed to be called working until M4 runs.

---

## M4 — Evaluation (the moment of truth)

Held-out error at N = 10, 20, 30, 50, against three baselines:

- global mean rating
- community score alone (`α`=1, `w`=0)
- style-average of your own past ratings ← **the one that usually wins**

**The number this project exists to find:** the N at which the personal model
overtakes the best baseline. Estimate: somewhere between 25 and 60 for beer.

**Kill criteria:** at N=60 the model still hasn't beaten the style-average
baseline. That is a real, publishable-to-yourself result: it would mean your
palate is well described by style preference alone, and the honest product is a
much simpler thing. Write it up in `DEAD-ENDS.md` and be pleased.

---

## M5 — Recommendation surfaces

1. Menu pick: "here are 6 options, rank them for me."
2. Shelf pick: photo → OCR → candidates → rank.
3. Explore: Thompson sampling over the catalog.
4. Recall: "what did I like that was like this?"

## M6 — Mood conditioning

Build in order: filters (mechanism 1) → objective/exploration swaps
(mechanism 3) → learned offsets (mechanism 2, only once there are ≥15 check-ins
in a given context).

**Kill criteria for mechanism 2:** per-mood offsets stay statistically
indistinguishable from zero at N=30 per context. Then mood is genuinely just
filters and objectives, which is a fine answer and much cheaper.

## M7 — Whisky

The real test of the architecture. If adding whisky requires touching anything in
`preference/` or `recommend/`, the abstraction was wrong.

**The interesting experiment:** does the beer-derived shared-axis weight vector
predict whisky ratings better than chance, before any whisky is logged?

## M8 — Wine, and anything else

Should be nearly free by then. If it isn't, M7 didn't actually succeed.

---

## Deliberately not on the roadmap

- Social features, friends, feeds. Untappd exists.
- Anything multi-user. This is an N-of-1 system by design.
- A mobile app before M4. Building UI before knowing the model works is the
  classic way to spend three months and learn nothing.
