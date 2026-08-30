# 05 — Data Sources

Two completely different jobs that are easy to confuse:

- **Catalog** — "what is this beer I'm holding?" Needs coverage.
- **Training data** — "what does a bitterness of 7 look like?" Needs labels.

The Kaggle profile set is training data. catalog.beer and Untappd are catalogs.
Using either for the other's job is a mistake.

> **No catalog gives descriptors.** No API anywhere returns
> `{bitter: 6.5, malty: 3, body: 7}`. Descriptors are produced by our profiler
> (§06) from the Kaggle labels. A catalog supplies only
> `name / brewery / style / ABV / IBU / description`. This is worth stating
> because it is an easy and consequential thing to get backwards.

## What each source actually provides

The whole picture on one screen, measured rather than assumed. **Read the
Israeli columns as the real ones** — global coverage is not the constraint here.

| Source | Terms | Keep forever? | Israeli coverage | Description for Israeli beer | Verdict |
|---|---|---|---|---|---|
| **Brewery's own site** | prose is theirs ⚠️ | facts yes, vector yes | ~most craft breweries | ✅ **real tasting notes, in Hebrew** | **The local description source.** See below. |
| **catalog.beer** | CC BY 4.0 ✅ | yes | 3/12 breweries, 10 beers | ❌ 0/10 — empty | Backbone *outside* Israel. Locally it repeats the label. |
| **Bottle label** | ours ✅ | yes | 100% of what's in your hand | ❌ no prose on a label | Authoritative for facts. ABV legally required. |
| **Manual entry** | ours ✅ | yes | 100% | whatever you type | The floor. Always works. |
| **Open Food Facts** | ODbL ✅ | yes | mass-market only, **no craft** | ❌ none | **Barcodes.** Useful for identity (D-015), not for profiling. |
| ~~**Untappd**~~ | restrictive ❌ | no | (good, but moot) | (unknown, and now unknowable) | ❌ **API access closed — DE-002.** |
| ~~**beer.db**~~ | public domain ✅ | yes | **zero rows, dead since 2014** | n/a | ❌ Falsified — DE-001. |
| **Kaggle profile set** | per dataset ✅ | yes | *not a catalog* | *not a catalog* | **Training data** — the descriptor labels. |
| **BeerAdvocate / RateBeer (UCSD)** | research use ✅ | yes | *not a catalog* | *not a catalog* | **Prior data** for D-007, and now the only community-score source. |

### The brewery's own site is the local description source

Found 2026-08-30, after Untappd closed. Obvious in hindsight and better than
what it replaces: **the people who made the beer publish tasting notes for it.**

| Brewery | Beers listed | Per-beer tasting notes |
|---|---|---|
| Alexander | 16 | ✅ ~100 chars each |
| Beer Bazaar | 8 | ✅ |
| Malka | 5 | ❌ name, price, size only |

Roughly two thirds of the sampled breweries publish usable prose, and it is
**descriptor-bearing in exactly the way the profiler needs**. Alexander's BLAZER:

> "בירה זהובה עם ראש קצף לבן, מאלטית, חלקה וקרמית, מתחילה עם מתיקות מרומזת
> וממשיכה עם מרירות מדוייקת"
>
> *golden, white foam head, malty, smooth and creamy, opens with hinted
> sweetness and continues with precise bitterness*

That single sentence carries malty, sweet, bitter and body — four axes, from the
manufacturer, for free. Compare Beer Bazaar's *"פירותי ומרענן, גוף קליל, מרירות
עדינה"* (fruity and refreshing, light body, delicate bitterness). This is
**better** than Untappd's user-written entries would have been, because it is
first-party and consistent within a brewery.

**Three caveats, and the first is a genuinely new problem:**

1. **It is in Hebrew, and the profiler trains on English.** M0's text path is
   TF-IDF over the English Kaggle descriptions; a Hebrew string is not merely
   unseen vocabulary, it shares no tokens at all. This is a real fork and it did
   not exist before — see the new sub-decision under D-002.
2. **Prose is the copyrightable part** (`docs/13` §3). Same rule as everywhere
   else: run it through the profiler, keep the vector, discard the text. Do not
   mirror brewery copy into the repo.
3. **No API, and `docs/13` §10.1 forbids scraper code here.** The realistic path
   is the manual-entry flow (D-005 option C) with paste-a-description as a field
   — ~10 breweries × ~10 beers is an evening of work, once, by hand. It is also
   exactly the case where a one-time collection is defensible: a manufacturer's
   public product page, no API key, no clickwrap, no contract.

Reading the table across, the shape of the problem is stark: for an Israeli
beer, **every source with usable terms provides exactly what is printed on the
bottle, and nothing more.** The two things a catalog could uniquely add — a
prose description for the profiler, and a community score for the `α` term —
are available only from Untappd, whose terms forbid keeping either.

**Updated 2026-08-30, after Untappd closed its API (DE-002).** The paragraph
above still describes the *catalogs* correctly, but the conclusion changed: the
description gap is filled not by a catalog at all, but by the breweries
themselves. The two remaining questions are:

1. **Do descriptions even matter?** Unmeasured, and cheap to settle. **M0
   already answers this**: it scores a numerics-only ridge (ABV / IBU / colour /
   style one-hot) against a TF-IDF-text + numerics ridge. If text adds little
   over the numerics, the entire description problem — Hebrew, copyright,
   manual collection, all of it — evaporates, and the label alone is enough.
   **This is the single highest-value thing left to run, and it needs only a
   free Kaggle download.**
2. **Does the `α` community term earn its place?** No longer a design choice:
   with Untappd gone there is **no per-beer community score available at all**,
   so v1 simply has none. M4's second baseline measures what that costs, for
   free. If it matters, the UCSD dumps are the replacement.

## The lookup chain

```
catalog.beer                                free, permanent, citable — but see above
  ↓ miss (the normal case for Israeli beer)
label OCR → facts off the bottle            ours, authoritative, offline
  ↓ no description
brewery's own page, once per beer           first-party tasting notes, in Hebrew
  ↓ brewery publishes none
type it, ~30s                               always available
```

Each beer traverses this **once**: fetch, profile, keep the vector and the facts.
See `docs/13-scraping-policy.md` §7 for why that makes 100 calls/hour ample.

**Note the chain is now much shorter in practice than it looks.** beer.db is
gone, and for a local beer catalog.beer contributes identifiers rather than
information — so the realistic path for most Israeli check-ins starts at the
label.

## Catalog sources

### catalog.beer

> **Terms verified 2026-08-30 (NVB-78).** Content is **CC BY 4.0** — permanent
> retention, redistribution and commercial use are all permitted, attribution
> required. The licence explicitly excludes brewery names, brands and
> trademarks, which stay with their owners. There is no cache-purge clause, no
> no-database clause, and no anti-analysis clause. **This is the backbone.**

- REST API, ~67,000 beers and ~6,600 brewers. Base `https://api.catalog.beer`,
  HTTP basic auth with the key as username. 1,000 requests/month free, then
  $1/1,000. Docs actively maintained (updated Aug 2026).
- Per-beer schema: `name`, `style`, `style_id`, `class`, `beverage_type`,
  `description`, `abv`, `ibu`, `cb_verified`, `brewer_verified`, `brewer`.
- **Attribution:** credit Catalog.beer, link the CC BY 4.0 licence, and state
  that changes were made. This has to appear wherever catalog-derived rows are
  published — README and any exported dataset.

**Measured, not assumed (NVB-78, 2026-08-30).** Twelve Israeli breweries were
queried through the public search:

| Result | Breweries |
|---|---|
| Brewer present, ≥1 beer | Tempo (4 beers), Malka (5), Jem's Beer Factory (1) |
| Brewer record but **zero beers** | Negev Brewery |
| Absent entirely | IBBL, Biratenu, Sheeta, Beer Bazaar, Alexander, Bazelet, Herzl, Shapiro |

**10 beers for the entire Israeli scene**, and two of those ten are duplicates
of each other. Beware fuzzy search: `Sheeta`, `Alexander` and `Beer Bazaar` all
return non-empty result sets made **entirely of unrelated US and European
breweries**. A naive hit-rate count that trusts "did the search return rows?"
reports 6/12 instead of the true 3/12.

**The finding that matters most: `description` is empty for 10/10 of the Israeli
beers.** The field exists in the schema and is well populated — but only on
entries carrying the `cb_verified` ("Verified by Catalog.beer") curation flag,
which no Israeli entry has. Sampled verified US entries (Russian River *Tempo
Change*, Pabst *Olympia*, Flying Fish *Jersey Juice*) all have real prose.

So for local beers catalog.beer supplies name, brewery, style and ABV —
**exactly the fields already printed on the bottle**, and nothing the profiler
can eat. Its value here is clean terms and clean identifiers, not information.

- Data quality is uneven and must be filtered on ingest: public search returns
  `[Postman API Test]` rows with 77–91% ABV and 8,877 IBU. Any bulk import needs
  a plausibility filter on ABV/IBU before rows reach the catalog.
- IBU is absent on every Israeli entry sampled.

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

### beer.db — dead, see `DEAD-ENDS.md` DE-001
- Public domain, plain-text fixtures, community maintained, Europe-heavy.
- **Abandoned upstream and useless here.** The `openbeer/world` repo has no
  Israel directory and zero Israel matches anywhere in its tree; its last commit
  is from 2014. Of the 27 org repos, most were last pushed 2014–2018.
- Retained in this list only so it is not re-proposed. Do not build an adapter.

### The bottle label itself
- **A primary source, and the best one for local beers.** ABV is legally
  required on the label; style, name and brewery are usually printed. That is
  most of a fact row — free, authoritative, works with no signal in a shop
  basement, and attached to nobody's terms.
- Feeds the same OCR path as the shelf-pick use case, so it costs nothing extra.
- What it does *not* give is a prose description, which is the one thing the
  regressor wants. Hence the narrow remaining slot for Untappd.

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

**Answered by NVB-78 (2026-08-30):**

- ~~Does catalog.beer actually cover Israeli beers?~~ Barely: 3 of 12 breweries,
  10 beers, no descriptions. **The manual/label path is the main event, not a
  convenience.**
- ~~Should the local cache be seeded in bulk (beer.db) or lazily on lookup?~~
  Neither source can bulk-seed anything Israeli. Lazily, on lookup.
- ~~Hebrew/English name variants will break dedup (D-015). How badly?~~ Worse
  than the Hebrew/English axis suggests — see D-015. Nothing in catalog.beer is
  in Hebrew script at all; the damage comes from unstable *transliteration* and
  from duplicate rows within a single source.

**Still open:**

- ~~**Is Untappd's `beer_description` populated for Israeli micro-brews?**~~
  **Closed unanswered, 2026-08-30 — and it no longer matters.** Untappd shut
  public API registration (DE-002), so the question is unanswerable *and* moot:
  the description gap is filled by the breweries' own pages instead. The harness
  (`scripts/untappd_description_check.py`) and its controls are kept because
  they cost nothing to keep and would settle it in a minute if a key ever
  appears — but nothing should be planned around it.
- **How much does the description actually contribute, versus ABV / IBU / style
  alone?** The question that now governs how much effort the local description
  problem deserves. **M0 measures it** — see the two ridge variants in
  `scripts/m0_profiler_validation.py`. Blocked only on a free Kaggle download.
- **How do we feed Hebrew descriptions to an English-trained profiler?** New as
  of 2026-08-30. See the sub-decision added to D-002. Now the single highest-value
  unknown left in the source strategy: catalog.beer has been shown to supply no
  descriptions locally, so if Untappd has none either, **no source does**, the
  regressor has no text to eat for local beers, and D-002 option B cannot run on
  them at all. See D-004 and the register in `docs/13-scraping-policy.md` §11.
- Is there any legitimate source for local availability? Currently: no.
