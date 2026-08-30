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
