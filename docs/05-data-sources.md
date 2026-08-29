# 05 — Data Sources

Two completely different jobs that are easy to confuse:

- **Catalog** — "what is this beer I'm holding?" Needs coverage.
- **Training data** — "what does a bitterness of 7 look like?" Needs labels.

The Kaggle profile set is training data. catalog.beer and Untappd are catalogs.
Using either for the other's job is a mistake.

## Catalog sources

### catalog.beer
- REST API, ~67,000 beers and ~6,600 brewers.
- ⚠️ **Terms unchecked.** If they permit permanent retention, this becomes the
  backbone and the Untappd retention problem mostly resolves. Check first.
- Per-beer: name, style, ABV, IBU, description.
- Free API key, HTTP basic auth. Docs actively maintained (updated Aug 2026).
- **Best default for item lookup.** Descriptions are what the profiler eats.
- Unknowns: Israeli coverage (untested), description quality distribution,
  whether the key has an undocumented rate limit.

### Untappd API

> ⚠️ **Read `docs/13-scraping-policy.md` first.** Untappd's API terms require
> cache purges every 24 hours and forbid building your own beer database or
> mining/analysing the data. Untappd is an **on-demand enrichment** source here,
> not a store.

- Very large catalog, and **Israeli coverage is genuinely good** — Tempo,
  Israel Beer Breweries (IBBL), Biratenu, Sheeta and Beer Bazaar all have full
  beer lists, plus a country-filtered top-rated listing.
- Per-beer: name, style, ABV, IBU, **community rating** ← the `α` term needs this.
- Free key via app registration. **100 calls/hour.** Venue/tap lists are not
  available on the public tier.
- 100/hr is fine at personal scale (a handful of new beers a week) *provided
  every response is cached permanently*. Design for it, don't fight it.

### beer.db
- Public domain, plain-text CSV, community maintained, Europe-heavy.
- Breweries and beers with ABV and style; thinner on descriptions.
- Zero legal friction; good for bulk seeding a local cache.

### Manual entry
- **Not a fallback — a primary path.** The most common real situation is
  standing in a shop holding a bottle that is in no database.
- Flow: photo of label → OCR → LLM proposes fields → you correct → save.
- Target: under 60 seconds. If it's slower it won't get used and the whole
  local-coverage story collapses.

### Scraping
- Off-the-shelf Untappd scrapers exist; writing one is not hard.
- Against Untappd's ToS. A one-time backfill of a few hundred Israeli beers is
  defensible for a personal project; a continuously running pipeline is not.
- Position: use the official API first, cache aggressively, and treat scraping
  as a deliberate one-off if coverage turns out to be a real blocker.

## Training / prior data

### Kaggle "Beer Profile and Ratings" (~3.2k beers)
- The important one. Contains **labelled flavour descriptor columns** alongside
  style, ABV, IBU and review-derived ratings.
- This trains the profiler (M0) and defines the initial axis vocabulary (D-001).
- Bias to know about: US craft-centric. Israeli lagers are out of distribution,
  which is exactly the population we care about — hence the LLM fallback.

### BeerAdvocate and RateBeer review dumps (UCSD / McAuley)
- BeerAdvocate: ~33k users, ~66k items, ~1.59M reviews (1998–2011).
- RateBeer: ~40k users, ~110k items, ~2.86M reviews (2000–2011).
- **Per-aspect sub-ratings** (taste, look, feel, smell, overall) *and* per-user
  histories — which is what makes the hierarchical population prior (D-007
  option C) possible at all.
- Caveat: data ends in 2011. Palate structure is probably stable; the beer
  catalogue is not. Sanity-check before leaning on it.

### Whisky
- The classic 86-distillery × 12-flavour scored dataset (body, sweetness, smoky,
  medicinal, tobacco, honey, spicy, winey, nutty, malty, fruity, floral).
  Hand-scored, tiny, and *exactly* the right shape. A gift for M7.

### Wine
- WineEnthusiast ~130k reviews with descriptions and scores. Descriptions are
  rich; structured flavour labels are not included, so wine would need either
  label mining or an LLM profiler.

## Caching and rate-limit policy

> Per-source, **subject to that source's terms** — see
> `docs/13-scraping-policy.md`. Untappd specifically does *not* permit the
> permanent cache described below.

1. Every external response is written to a local cache keyed by source + id, and
   **never re-fetched** unless explicitly invalidated.
2. The cache is committed-adjacent (in `data/`, gitignored) and backed up. It is
   slow and rate-limited to rebuild; treat it as precious.
3. Untappd calls are counted and throttled below 100/hour in code, not by hope.
4. Every cached row keeps `retrieved_at` so staleness is visible.

## Open questions

- Does catalog.beer actually cover Israeli beers? **Untested. Test early** — it
  determines whether the manual path is a convenience or the main event.
- Hebrew/English name variants will break dedup (D-015). How badly?
- Is there any legitimate source for local availability? Currently: no.
- Should the local cache be seeded in bulk (beer.db) or lazily on lookup?
