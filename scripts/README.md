# Scripts

`qualety.sh` is the code-quality entry point, not an experiment — it builds a
pinned qualety from source into `.tools/` and runs it. See `docs/14-workflow.md`.

```bash
./scripts/qualety.sh              # check the repo
./scripts/qualety.sh check --diff # only what changed vs the merge base
```

Everything else here is one-off ingest and experiment scripts. Each should be
runnable standalone with a fixed seed and should print its numbers (N-05).

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
- `m1_profile_structure.py` — PCA / clustering of the labelled profile vectors.
- `fetch_catalog.py` — cached pulls from catalog.beer / Untappd / beer.db.
- `m4_evaluate.py` — model vs. B0/B1/B2 across N. Produces the crossover plot.
