# data/

Everything under `raw/` and `processed/` is **gitignored**. Nothing here is
committed — see ADR-0001 and `scripts/pre-commit`.

## `taam.db` — your check-ins

Created on first run of `python scripts/checkin.py`. Never committed (`*.db` is
gitignored and the pre-commit hook refuses it). Override the location with
`$TAAM_DB`. This is the only irreplaceable file in the project: everything else
here can be re-downloaded.

## What to download

### `raw/beer_profile_and_ratings.csv` — needed for M0 and M1
Kaggle: <https://www.kaggle.com/datasets/ruthgn/beer-profile-and-ratings-data-set>

~3.2k beers with **labelled flavour descriptor columns** plus style, ABV, IBU
and a description. This is the profiler's training set — not a catalog.

```bash
# with the kaggle CLI configured (~/.kaggle/kaggle.json)
kaggle datasets download -d ruthgn/beer-profile-and-ratings-data-set -p data/raw --unzip
```

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
