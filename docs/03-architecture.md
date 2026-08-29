# 03 — Architecture

## The core idea

Three layers, and the discipline lives in keeping them apart:

```
┌─────────────────────────────────────────────────────────────┐
│  DOMAIN-SPECIFIC                                            │
│                                                             │
│  catalog/    where items come from       (per domain)       │
│  domains/    what the axes mean          (per domain)       │
│  profiler/   item -> vector              (per domain)       │
└─────────────────────────────────────────────────────────────┘
                            │
                            │  everything below sees only
                            │  (profile: R^d, rating: R, context: tags)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  DOMAIN-AGNOSTIC                                            │
│                                                             │
│  preference/  profiles + ratings + prior -> palate          │
│  recommend/   palate + candidates + mood -> ranked list     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  SURFACE                                                    │
│  CLI / bot / web — thin, swappable, does no thinking        │
└─────────────────────────────────────────────────────────────┘
```

The test that this is working: **nothing under `preference/` or `recommend/` ever
mentions beer.** If it does, the abstraction has leaked and whisky will be
painful. See `11-multi-domain.md`.

## Data flow

```
  ┌──────────┐  ┌──────────┐  ┌─────────┐  ┌────────┐
  │catalog.  │  │ Untappd  │  │ beer.db │  │ manual │   sources (§05)
  │  beer    │  │          │  │         │  │ +photo │
  └────┬─────┘  └────┬─────┘  └────┬────┘  └───┬────┘
       └─────────────┴─────────────┴───────────┘
                     │  normalise + dedup  (D-015)
                     ▼
              ┌─────────────┐
              │   Item      │  cached forever, never re-fetched blindly
              └──────┬──────┘
                     │
                     ▼   PROFILER CHAIN (§06)
        ┌────────────────────────────┐
        │ 1. supervised regressor    │  ← preferred, deterministic
        │ 2. LLM ensemble (t=0)      │  ← fallback for unknown items
        │ 3. manual form             │  ← always available floor
        └────────────┬───────────────┘
                     ▼
              ┌─────────────┐
              │  Profile    │  + source, version, confidence
              └──────┬──────┘
                     │
     ┌───────────────┴────────────────┐
     ▼                                ▼
┌──────────┐                  ┌───────────────┐
│ reduce   │ PCA/AE (§06,D-003)│ population    │ (§07, D-007)
│ to d≈4-6 │                  │ prior         │
└────┬─────┘                  └───────┬───────┘
     │                                │
     └────────────┬───────────────────┘
                  ▼
        ┌───────────────────────┐      ┌──────────────┐
        │ PREFERENCE MODEL (§07)│◄─────│  Check-ins   │ (§09)
        │ α·community + w·prof  │      │ rating,Q&A,  │
        │ + posterior over w    │      │ context      │
        └───────────┬───────────┘      └──────────────┘
                    ▼
          ┌───────────────────┐
          │  palate w_you     │  readable, with error bars
          └─────────┬─────────┘
                    │
                    ▼   RECOMMENDER (§08)
     ┌──────────────────────────────────┐
     │ 1. filter by mood constraints    │
     │ 2. score = (w + δ_mood)·profile  │
     │ 3. objective swap / exploration  │
     └──────────────┬───────────────────┘
                    ▼
               ranked list + one-line explanations
```

## Why this shape and not another

**Why content-based and not collaborative?** One user, tens of ratings. See
D-006 option E for the full argument.

**Why is the community score a separate additive term rather than a feature?**
Because it lets the system work at N=0 with `w=0`, and because the coefficient
`α` is independently interesting (how contrarian are you?). Folding it in as
just another feature loses both properties.

**Why is uncertainty everywhere?** Two reasons, and both are load-bearing. It is
the only honest way to present a prediction from 20 samples, and it *is* the
exploration mechanism — "feeling exploratory" is implemented by changing what we
do with the posterior variance, not by adding a separate system.

**Why is the profiler a chain rather than one method?** Because coverage and
trustworthiness pull in opposite directions. The regressor is trustworthy but
only works on beers resembling its training data; the LLM covers everything but
must be treated as suspect. The chain lets each item get the best available
source, and records which one it got so quality can be tracked per source.

## Key risks, architecturally

| Risk | Where it bites | Mitigation |
|---|---|---|
| Profiler sources are on different scales | Profiles incomparable, model learns nonsense | Calibration set profiled by *all* sources; cross-source correlation reported (§06) |
| Profile is just a laundered style label | Whole content-based premise collapses | M0 kill criterion tests exactly this |
| Rating noise dominates signal | Model can never beat baselines | Repeat check-ins (R-15) measure the noise floor directly |
| Item identity breaks across sources | Duplicate items, split rating history | D-015, decided before the catalog is populated |
| Context never gets logged early enough | Mood conditioning permanently impossible | R-12: log from day one regardless |

## Module sketch

```
src/taam/
  domains/      Descriptor vocabularies. Pure data. beer.py, whisky.py, wine.py.
                Defines shared axes vs. domain tail (D-014).
  catalog/      Source adapters (catalog_beer.py, untappd.py, beerdb.py,
                manual.py), normalisation, dedup, the local cache.
  profiler/     regressor.py, llm.py, manual.py, chain.py, calibration.py
  preference/   model.py (decomposition + Bayesian regression), prior.py
                (population prior), readout.py (palate -> English)
  recommend/    rank.py, mood.py, explore.py, explain.py
  storage/      SQLite schema and access
```

`domains/`, `catalog/` and `profiler/` are allowed to know what beer is.
Nothing else is.
