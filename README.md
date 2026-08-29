# Palate

A personal preference-learning system for drinks. Profile every beer, log what
you drank and what you thought, learn a readable model of your own palate, get
recommendations that account for mood and context.

Beer first. Designed to extend to whisky, wine, and beyond.

> **New here? Read [`CONTEXT.md`](CONTEXT.md) first.** It is the map.

---

## Status

**Phase 0 — design only.** Nothing is built. Nothing is decided. This repo is
currently a specification and a decision register.

## The idea in one diagram

```
                 ┌──────────────────────────────────────┐
   catalog       │  Item                                │
   sources  ───► │  name, brewery, style, ABV, IBU, SRM │
   (§05)         │  description, ingredients            │
                 └───────────────┬──────────────────────┘
                                 │
                          PROFILER (§06)
                                 │
                                 ▼
                 ┌──────────────────────────────────────┐
                 │  profile: vector in R^d              │
                 │  [shared axes | domain axes]         │
                 └───────────────┬──────────────────────┘
                                 │
       your check-ins ──►  PREFERENCE MODEL (§07)  ◄── population prior
       (rating + Q&A, §09)       │                     (§07, §05)
                                 ▼
                 ┌──────────────────────────────────────┐
                 │  w_you  (+ uncertainty)              │
                 │  = your palate, readable             │
                 └───────────────┬──────────────────────┘
                                 │
                        + mood/context (§08)
                                 ▼
                        RECOMMENDATIONS
              menu pick · shelf pick · explore · recall
```

Section numbers refer to `docs/`.

## Repository layout

```
CONTEXT.md          Start here. The map.
DECISIONS.md        Open decision register. Nothing is locked.
ROADMAP.md          Build order, milestones, and kill criteria.
DEAD-ENDS.md        What we tried and why it failed. Grows over time.
GLOSSARY.md         Terms of art, so future-you isn't guessing.
CLAUDE.md           Working instructions for an AI session on this repo.

docs/01  Vision and scope
docs/02  Requirements
docs/03  Architecture
docs/04  Data model
docs/05  Data sources
docs/06  The profiler
docs/07  The preference model
docs/08  Mood and context
docs/09  Check-in UX
docs/10  Evaluation
docs/11  Multi-domain extension
docs/12  Prior art
docs/adr Architecture decision records (currently: none accepted)

src/palate/         Code skeleton. Empty by design.
  domains/          Per-domain descriptor vocabularies
  catalog/          Item ingest and normalisation
  profiler/         Item -> profile vector
  preference/       Profile + ratings -> palate model
  recommend/        Palate + candidates + mood -> ranked list
  storage/          Persistence

notebooks/          Exploration. Expect mess here; that's fine.
data/raw            Downloaded datasets. Gitignored.
data/processed      Derived artefacts. Gitignored.
scripts/            One-off ingest and evaluation scripts.
tests/
```

## Quickstart

There is nothing to run yet. When there is, it will go here.

The first thing to build is not the model — it is
[the profiler validation experiment](docs/06-profiler.md#the-validation-experiment),
because it is the highest-risk component and it can be falsified in a day.

## License

Personal project. No license chosen yet — see `DECISIONS.md` D-013.
