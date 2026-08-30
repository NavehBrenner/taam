# taam · טעם

A personal preference-learning system for drinks.

Profile every beer, log what you drank and what you thought, learn a readable
model of your own palate, and get recommendations that account for mood and
context. Beer first, designed to extend to whisky, wine, and beyond.

> *taam* (טעם) is Hebrew for both **taste** and **reason**. That is the whole
> brief: the system owes you a pick *and* why.

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
LICENSE             MIT.

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
docs/13  Source terms and scraping policy  <- read before writing an adapter
docs/adr Architecture decision records (currently: none accepted)

src/taam/           Code skeleton. Empty by design.
  domains/          Per-domain descriptor vocabularies
  catalog/          Item ingest and normalisation
  profiler/         Item -> profile vector
  preference/       Profile + ratings -> palate model
  recommend/        Palate + candidates + mood -> ranked list
  storage/          Persistence

notebooks/          Exploration. Expect mess here; that's fine.
tests/              Controls for the experiment harnesses.
data/raw            Downloaded datasets. Gitignored.
data/processed      Derived artefacts. Gitignored.
scripts/            One-off ingest and evaluation scripts.
tests/
```

## Quickstart

```bash
pip install -r requirements.txt
ln -sf ../../scripts/pre-commit .git/hooks/pre-commit   # data guard, do this once

# prove the M0 harness works (synthetic data, no download):
python tests/test_m0_harness.py
python scripts/m0_profiler_validation.py --self-test

# then get the data (see data/README.md) and run the real experiment:
python scripts/m0_profiler_validation.py --data data/raw/beer_profile_and_ratings.csv
```

The first thing to run is not the model — it is
[the profiler validation experiment](docs/06-profiler.md#the-validation-experiment),
because it is the highest-risk component and it can be falsified in a day. It is
written and its controls pass; it needs only the Kaggle CSV.

## Data provenance

Every source in this project can be named in public, which is deliberate:

| Used for | Source | Terms |
|---|---|---|
| Profiler training labels | Kaggle Beer Profile and Ratings | dataset licence |
| Population prior | BeerAdvocate / RateBeer dumps (UCSD) | research use, cited |
| Permanent catalog | beer.db | public domain |
| Permanent catalog | catalog.beer | **terms unverified — blocking** |
| Local beers | the bottle label, via OCR, and hand entry | ours |
| Descriptions, community scores | Untappd documented API, on demand | not retained past their cache window; attributed |

No scraped data, and no scraper code. See
[`docs/13-scraping-policy.md`](docs/13-scraping-policy.md) for the reasoning,
including why "the facts aren't copyrighted" is true but not sufficient.

## Contributing / using this

Public and MIT (ADR-0001). If you want to run it on your own palate, the parts
that are yours — your check-ins, your DB — never touch this repo.

**Before adding a data-source adapter, read `docs/13-scraping-policy.md`.** Some
sources' terms are more restrictive than they look, and no scraper code belongs
in this tree.

Install the data guard once after cloning:

```bash
ln -sf ../../scripts/pre-commit .git/hooks/pre-commit
```

## License

MIT — see `LICENSE`.
