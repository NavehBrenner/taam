# Scripts

One-off ingest and experiment scripts. Each should be runnable standalone with a
fixed seed and should print its numbers (N-05).

Planned, in roadmap order:

- `m0_profiler_validation.py` — the falsification experiment (see docs/06 and
  ROADMAP M0). **Build this first.** It can kill the project in a day, which is
  the most valuable thing any script here can do.
- `m1_profile_structure.py` — PCA / clustering of the labelled profile vectors.
- `fetch_catalog.py` — cached pulls from catalog.beer / Untappd / beer.db.
- `m4_evaluate.py` — model vs. B0/B1/B2 across N. Produces the crossover plot.
