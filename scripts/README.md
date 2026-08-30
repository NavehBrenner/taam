# Scripts

One-off ingest and experiment scripts. Each should be runnable standalone with
a fixed seed and should print its numbers (N-05).

Written:

- `checkin.py` — **the one to run daily.** Logs a beer: item, 0–10 rating, the
  three bootstrap questions (D-009 option B) and context tags, into
  `data/taam.db`. Every prompt takes digits or Enter; nothing needs typing.

  ```bash
  python scripts/checkin.py                          # log one
  python scripts/checkin.py --list                   # what's been logged
  python scripts/checkin.py --at 2026-08-29T21:00    # backfill last night
  ```

  It is a terminal prompt on purpose (NVB-80). docs/09 wants a phone eventually,
  but the store is the part that has to be right and the front end is
  replaceable — and not logging while a UI gets built is unrecoverable.

Planned, in roadmap order:

- `m0_profiler_validation.py` — **WRITTEN, ready to run.** The falsification
  experiment (docs/06, ROADMAP M0). Compares a style-average baseline, a
  numerics-only ridge, and TF-IDF-text + numerics ridge against the labelled
  Kaggle descriptors, and prints a verdict including the kill criterion.

  ```bash
  # sanity-check the harness itself, no download needed:
  python scripts/m0_profiler_validation.py --self-test

  # the real thing, once data/raw/beer_profile_and_ratings.csv exists:
  python scripts/m0_profiler_validation.py --data data/raw/beer_profile_and_ratings.csv
  ```

  Both controls for the harness live in `tests/test_m0_harness.py` and must
  pass before its verdict is trusted.
- `untappd_description_check.py` — **WRITTEN, needs an API key.** Settles the
  last open question in the source strategy (NVB-78): does Untappd have prose
  for Israeli beers, when catalog.beer was measured to have none? If it does not,
  no source does, and the trained regressor (D-002 option B) cannot run on local
  beer at all.

  ```bash
  # the verdict logic's controls, no network and no key needed:
  python scripts/untappd_description_check.py --self-test

  # the real thing (~40 calls, well inside the 100/hour limit):
  export UNTAPPD_CLIENT_ID=... UNTAPPD_CLIENT_SECRET=...
  python scripts/untappd_description_check.py --out docs/data/untappd-il-check.md
  ```

  Records description **lengths only, never the text** — Untappd's terms require
  a 24h purge and the prose is the copyrightable part (docs/13 §3). That is what
  makes its output publishable in a public repo. Documented API only; it must
  never grow a scraping path (§10.1).
- `m1_profile_structure.py` — PCA / clustering of the labelled profile vectors.
- `fetch_catalog.py` — cached pulls from catalog.beer / Untappd. (Not beer.db —
  that source is dead, see DEAD-ENDS DE-001.)
- `m4_evaluate.py` — model vs. B0/B1/B2 across N. Produces the crossover plot.
