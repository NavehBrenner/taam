# 02 — Requirements

Requirements are written as `R-nn`. Priority: **P0** must exist for the project to
mean anything; **P1** is the intended experience; **P2** is wanted-if-it-survives.

Nothing here constrains *how* — implementation options live in `DECISIONS.md`.

## Functional — items and profiles

| ID | Pri | Requirement |
|---|---|---|
| R-01 | P0 | Every item has a stable identity, a domain, and a set of catalog fields (name, maker, style, ABV, and whatever else the domain offers). |
| R-02 | P0 | Every item can be assigned a **profile**: a fixed-length numeric vector over that domain's descriptor axes. |
| R-03 | P0 | A profile records its `source` (which profiler produced it), `profiler_version`, and timestamp. |
| R-04 | P0 | Profiles are computed once and cached. Re-profiling is an explicit, logged operation, never a side effect. |
| R-05 | P1 | An item with no catalog entry can be added by hand in under 60 seconds, including from a photo of a label. |
| R-06 | P1 | Profile quality is measurable — there is a held-out set with known-good vectors to score any profiler against. |
| R-07 | P2 | Disagreement between profiler runs is surfaced as a per-item confidence, and low-confidence items can be flagged for review. |

## Functional — check-ins

| ID | Pri | Requirement |
|---|---|---|
| R-10 | P0 | A check-in records: item, timestamp, overall rating. |
| R-11 | P0 | A check-in records 2–4 structured follow-up answers. |
| R-12 | P0 | A check-in records **context/mood tags**, whether or not anything consumes them yet. |
| R-13 | P0 | The full check-in takes under 30 seconds on a phone, one-handed, in a noisy bar. |
| R-14 | P1 | Free-text notes are optional and always available. |
| R-15 | P1 | The same item can be checked in multiple times, and repeat ratings are kept separately (they are the only measurement of rating noise we will ever get). |
| R-16 | P2 | Retroactive check-ins ("I had this last week") are supported without lying about the timestamp. |

## Functional — the model

| ID | Pri | Requirement |
|---|---|---|
| R-20 | P0 | The model predicts a rating for any item with a profile. |
| R-21 | P0 | Every prediction carries an uncertainty estimate. |
| R-22 | P0 | The model produces useful output at N=0 check-ins, and improves continuously — no threshold below which it refuses to work. |
| R-23 | P0 | The learned palate is **human-readable**: it can be rendered as a short description a person can agree or disagree with. |
| R-24 | P1 | The model can be evaluated against baselines at any N, on demand, as a single command. |
| R-25 | P1 | Retraining is cheap enough to happen after every check-in. |
| R-26 | P2 | The palate can be shown as a trajectory over time. |

## Functional — recommendations

| ID | Pri | Requirement |
|---|---|---|
| R-30 | P0 | Given a candidate set, return a ranked list with predicted rating and uncertainty. |
| R-31 | P1 | Candidate sets can come from: a typed list, a photo of a menu, a shop's range, or the whole catalog. |
| R-32 | P1 | Recommendations accept a **mood**, which may apply constraints, shift the objective, or change the exploration weight. |
| R-33 | P1 | An "explore" mode optimises for information gain rather than predicted rating. |
| R-34 | P1 | Every recommendation can explain itself in one sentence referencing actual profile axes. |
| R-35 | P2 | Recall queries over past check-ins ("sour, loved it, last spring"). |

## Functional — multi-domain

| ID | Pri | Requirement |
|---|---|---|
| R-40 | P0 | Nothing in the preference model or recommender is beer-specific. |
| R-41 | P1 | Adding a domain requires only: a descriptor vocabulary, a catalog adapter, and a profiler. No core changes. |
| R-42 | P2 | Preference learned in one domain informs another through the shared axes. |

## Non-functional

| ID | Pri | Requirement |
|---|---|---|
| N-01 | P0 | Runs entirely on one machine. No infrastructure. |
| N-02 | P0 | All external data is cached locally and permanently; the system works offline once cached. |
| N-03 | P0 | Respects source rate limits (notably Untappd's 100 calls/hour). |
| N-04 | P1 | Personal drinking data stays private by default; publishing any of it is a deliberate act. |
| N-05 | P1 | Any experiment in the repo is reproducible from a single command with a fixed seed. |
| N-06 | P2 | Model retraining completes in under a second, so it can run inline. |

## Anti-requirements

Things we are explicitly **not** requiring, recorded so they don't creep in:

- No accuracy target. We do not know what is achievable; setting a number before
  M4 would be theatre.
- No latency target for recommendations. It's a personal tool.
- No requirement that the personal model beat the baselines. If it doesn't,
  that's the finding (see `10-evaluation.md`).
