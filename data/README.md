# data/

Everything under `raw/` and `processed/` is **gitignored**. Nothing here is
committed — see ADR-0001 and `scripts/pre-commit`.

## What to download

### `raw/beer_profile_and_ratings.csv` — needed for M0 and M1
Kaggle: <https://www.kaggle.com/datasets/ruthgn/beer-profile-and-ratings-data-set>

~3.2k beers with **labelled flavour descriptor columns** plus style, ABV, IBU
and a description. This is the profiler's training set — not a catalog.

No Kaggle account or API token needed — the download endpoint serves this one
anonymously (verified 2026-09-01). `curl -I` returns 404 because the endpoint has
no HEAD handler; a GET works.

```bash
curl -L -o /tmp/beer.zip \
  "https://www.kaggle.com/api/v1/datasets/download/ruthgn/beer-profile-and-ratings-data-set"
unzip -o /tmp/beer.zip -d data/raw/
```

Gives `beer_profile_and_ratings.csv` (3,197 beers) plus two fuzzy-match lists and
an `.xlsx` of descriptor definitions. Everything under `data/` is gitignored.

### `raw/beeradvocate.json` / `raw/ratebeer.json` — needed for the population prior
<https://cseweb.ucsd.edu/~jmcauley/datasets.html>

Per-user review histories with per-aspect sub-ratings. Research use; cite the
papers listed on that page. Large (~400MB each) — only needed for D-007.

### `raw/whisky.csv` — needed for M7
The 86-distillery × 12-flavour scored set:
<https://www.kaggle.com/datasets/koki25ando/scotch-whisky-dataset>

## Provenance rule

Before adding any source here, record its terms in the register at
`docs/13-scraping-policy.md` §11. No scraped data.
