# Dead Ends

A log of approaches that were tried and abandoned, with evidence.

**This file is a feature.** The project is expected to hit walls; an approach
that was properly falsified is a result, and writing it down is what stops it
being re-proposed in six months. Entries are never deleted.

## Template

```
## DE-00N — <short name>
**Date:**
**Related decision:** D-0XX
**What we tried:**
**What we expected:**
**What actually happened:** (numbers, please)
**Why it failed:**
**What we did instead:**
**Would it be worth revisiting if…:**
```

---

## Entries

## DE-002 — Untappd as a data source, in any role
**Date:** 2026-08-30
**Related decision:** D-004 (the whole "how do we use Untappd" sub-decision),
D-005 option A, D-007 (the `α` community term)
**What we tried:** Untappd as an on-demand gap-filler for prose descriptions and
as the sole source of community scores for the `α` term — D-004 option A, which
was the standing lean.
**What we expected:** a narrow but real slot: ~2 calls per beer, ~1,000 calls
over the project's life, descriptions and a community score for beers the free
catalogs miss.
**What actually happened:** **General API access is closed.** Untappd has blocked
public API registration following abuse; obtaining a key now requires contacting
them directly and being granted access case by case (observed by Naveh on their
site, 2026-08-30 — the notice sits behind a login, so it is not linkable here).
The `/api/register` URL redirects to a login wall.

**Why it failed:** Not on terms, and not on data quality — on **access**. This is
worth separating, because the terms analysis in `docs/13` §2–§6 was correct and
remains correct; it simply stopped mattering. A source you cannot obtain
credentials for is not a source.

Applying for a key was considered and declined: Naveh is not interested in
pitching a personal project to Untappd for access, which is a legitimate call —
the resulting dependency would be a single revocable permission sitting upstream
of the catalog, which `docs/13` §10.5 already warns against ("could it be deleted
tomorrow and the project still work?").

**What we did instead:** D-004 **option D — drop Untappd entirely.** Note this
option was not chosen on its merits; it is the only one left standing. Two
consequences, and the second is the significant one:

1. **The entire terms problem disappears.** No 24h purge, no anti-mining clause,
   no "don't build your own database". `docs/13` becomes mostly historical —
   every remaining source has clean terms. This is a genuine simplification.
2. **The `α` community term has no data source.** Untappd was the only one. So
   "does `α` earn its place?" stops being a design question and becomes a
   constraint: v1 has no community term. **M4 was always going to measure this
   for free** (its second baseline is community-score-alone), so the answer
   arrives on its own — but until then the model is `w·profile + b`, and
   D-006/D-007 should be read with that in mind.

**Would it be worth revisiting if…:** Untappd reopens public registration, or
someone hands over a key. Neither is worth planning around. If a community score
is ever genuinely needed, the UCSD BeerAdvocate/RateBeer dumps already in
`docs/05` carry per-beer community ratings for a large catalog — with clean
research-use terms — and are a better fit for the `α` prior anyway, since D-007
wants per-user histories that Untappd's API never exposed.

---

## DE-001 — beer.db as a catalog source
**Date:** 2026-08-30
**Related decision:** D-004 (it was the "public domain, zero legal friction"
option), D-005
**What we tried:** Evaluated beer.db / the `openbeer` GitHub organisation as the
bulk-seed source for the permanent local catalog, per the D-004 lean
"catalog.beer and beer.db as the permanent local catalog".
**What we expected:** Europe-heavy but broad public-domain coverage, good for
seeding a local cache for free with no terms to read.
**What actually happened:**
- The `openbeer/world` repository tree contains **0 matches** for Israel — no
  `il-israel` directory, nothing under `asia/`, no match anywhere in the
  recursive tree listing.
- None of the 27 repositories in the organisation covers Israel. The org is
  organised as one repo per country/region; Israel was never added.
- The project is abandoned. `openbeer/world` was last pushed **2014-10-25**.
  Across the org, the newest data push is 2018 (`at-austria`); the great
  majority are 2014–2015. Only the website repo has been touched since.

**Why it failed:** Two independent reasons, either of which alone is fatal.
Coverage is zero for the only region this project needs, and the upstream is
eleven years dead, so the coverage will never improve.

**What we did instead:** catalog.beer (CC BY 4.0, verified — see
`docs/13-scraping-policy.md` §11) is the entire permanent catalog. It is thin
locally too (3/12 Israeli breweries, 10 beers), which pushes real weight onto
the label-OCR and manual-entry paths in D-005.

**Would it be worth revisiting if…:** the upstream revives, or someone
contributes Israeli data to it. Neither is worth waiting for. If a public-domain
bulk seed is ever wanted again, the live candidate is **Open Brewery DB** — but
note it catalogues *breweries*, not beers, so it cannot supply item rows and
would not have helped here either.

---

---

## Pre-emptively documented non-starters

These were reasoned about and rejected before any code was written. They are
recorded here so nobody re-derives them, but they were **never actually tested**,
so the reasoning is falsifiable and the door is not locked.

### Collaborative filtering as the primary model
Needs thousands of ratings from the target user. Public rating data is severely
popularity-skewed — a small fraction of items absorbs most ratings — so a model
trained on it tends to become a popularity predictor with a personalization
costume on. Recorded as D-006 option E.

### Fine-tuning a network trained on community ratings using ~10 personal samples
No learning rate exists that both moves the model meaningfully and avoids
destroying it. The intent behind the idea is right; the mechanism is wrong. The
fix is the additive decomposition in D-006, which achieves the same goal
(population knowledge + personal adjustment) with a stable, well-posed estimator.

### An autoencoder to map descriptions to profiles
Autoencoders are unsupervised reconstruction models. The Kaggle set provides
*labelled* target vectors, which makes this straightforwardly supervised
regression — strictly more direct and more accurate. (An autoencoder *is* still
a live option for compressing the profile vectors themselves — that is D-003
option C, and unrelated to this.)

### One shared descriptor vocabulary across all beverages
"Hoppy" has no wine analogue. Forcing a single vocabulary produces mostly-zero
vectors and meaningless axes. Replaced by the shared-core + domain-tail design
in D-014.
