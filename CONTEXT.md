# CONTEXT — read this first

> If you are a new Claude session, a new collaborator, or Naveh-in-six-months:
> read this file top to bottom before touching anything else. It is the only
> file that is allowed to be a summary. Everything else is detail.

## What this project is

**taam** (Hebrew טעם — both *taste* and *reason*) is a personal, single-user
preference-learning system for drinks. The name is the thesis: the system should
give you a taste and a reason for it.

The loop:

1. Every drinkable item gets a **profile** — a fixed-length vector of sensory
   attributes (bitterness, sweetness, body, hoppiness, …) derived from whatever
   we know about it.
2. Naveh logs what he drank: an overall rating plus 2–4 short follow-up answers.
3. A small model learns the mapping `profile -> his rating`. That learned weight
   vector *is* his palate, and it is meant to be readable, not a black box.
4. The system recommends: from a menu, from a shop shelf, from memory, and
   conditioned on **mood/context** ("light, at noon, with a burger").

It starts with **beer**. It is designed from day one to extend to **whisky**,
then **wine**, then anything else. See `docs/11-multi-domain.md`.

## What this project is NOT

- Not a business. Not a startup. Not a product with users. It is a personal
  project for fun and for the ML.
- Not a social check-in app. Untappd already exists and is good at that. If a
  feature is really "a diary with friends", it is out of scope.
- Not a catalog. We do not want to own beer data; we want to borrow it.

## The one-paragraph technical thesis

Naive collaborative filtering fails here: one user, tens of ratings, and public
rating data is so popularity-skewed that a model trained on it becomes a
bestseller list wearing a personalization costume. The bet instead is
**content-based Bayesian regression over a low-dimensional sensory space, with a
population-derived prior**. Rating is decomposed into a community term plus a
personal deviation term, so the system is useful at N=0 and degrades gracefully
rather than falling off a cliff. Uncertainty is first-class, because it powers
both honest recommendations and the active-learning loop that decides what to
suggest next.

## Ground rules for this repo

1. **Nothing is locked.** Every significant choice lives in `DECISIONS.md` with
   its alternatives intact and a status of `OPEN`. Docs may say "current
   recommendation". No doc may say "we decided" unless the decision has an
   accepted ADR in `docs/adr/`. As of this writing there are **zero** accepted
   ADRs.
2. **Dead ends are expected and are output.** This project will hit walls. When
   an approach fails, it gets an entry in `DEAD-ENDS.md` with the evidence.
   A documented dead end is a result, not a wasted week.
3. **Every modelling claim gets a baseline.** See `docs/10-evaluation.md`. The
   project's honesty depends on this and nothing else.
4. **Log context from day one, even before it is modelled.** Data you did not
   collect is gone forever. See `docs/08-mood-and-context.md`.

## Where to go next

| You want to… | Read |
|---|---|
| Understand the whole design | `docs/03-architecture.md` |
| Know what is undecided | `DECISIONS.md` |
| Know what to build first | `ROADMAP.md` |
| Know what already failed | `DEAD-ENDS.md` |
| Understand the data problem | `docs/05-data-sources.md` |
| Understand the ML | `docs/07-preference-model.md` |
| Know why we didn't just use Untappd | `docs/12-prior-art.md` |
| Add a data source (read first) | `docs/13-scraping-policy.md` |
| Actually change something | `docs/14-workflow.md` |

## Known live problem

**Untappd's API terms conflict with the architecture.** They require caches to be
purged every 24 hours, forbid using the API to build your own beer database, and
forbid "mining or analyzing" the data — which describes this project. Untappd is
therefore demoted to on-demand enrichment, never a store. Details in
`docs/13-scraping-policy.md`.

**catalog.beer's terms are now checked (NVB-78, 2026-08-30): CC BY 4.0** —
permanent retention, redistribution and commercial use permitted, attribution
required. It is the permanent backbone. But the same spike measured its data and
found the local shelf nearly bare: **3 of 12 Israeli breweries, 10 beers, and an
empty description on all 10.** beer.db is dead (DE-001: zero Israeli rows,
abandoned since 2014).

So the terms problem is solved and a coverage problem replaced it. For Israeli
beer, no catalog supplies anything the bottle label does not — which makes the
label-OCR and manual-entry paths load-bearing rather than a convenience.

**Untappd is out entirely (2026-08-30, DE-002)** — they closed general API
registration and now require contacting them for a key. So the terms problem
solved itself by the source disappearing, and **every remaining source has clean
terms.** The cost: the `α` community term has no data source, so v1 has none and
M4 measures what that costs.

**What replaced it is better:** the breweries publish tasting notes for their own
beers. Alexander lists 16 with ~100-character Hebrew descriptions carrying malty
/ sweet / bitter / body in a single sentence. First-party, no API, no terms
conflict — collected by hand through the manual-entry flow. New problem, new
fork: those descriptions are in Hebrew and the profiler trains on English. See
D-002's sub-decision.

**Also corrected 2026-08-30: Untappd's app does build a taste profile and does
recommend from it.** `docs/12` previously claimed it didn't; that was wrong. The
remaining gap is narrower and sharper — nobody *shows you the model*. That is
still the half of this project worth doing.

**Within-style discrimination is measured (2026-09-02, NVB-96).** The M0 lift
turns out to be mostly *between* styles: on the residual after the style mean is
removed, only `Alcohol` clears r = 0.40 and ABV alone already carries it. The
description is the only source of within-style signal on `Bitter` and `Hoppy`,
and it ranks same-style pairs at 0.608 and 0.566 against a 0.5 coin. So the
profiler is a real but weak discriminator inside a style, and **D-002 option E —
style-average as the floor of the chain — is the honest answer rather than a
strawman.** Nothing closed; see `docs/06-profiler.md`.

**The highest-value things left to run are the two questions M0 and NVB-96 both
left open:** NVB-97 (does a sentence encoder read the description better than
TF-IDF?) and NVB-84 (how much of the within-style residual is label noise, i.e.
unlearnable by anyone?). The second is the missing denominator for every number
above.

## Status

**M0 is run and M2 logging is live.** One decision made (ADR-0001: public repo,
MIT). The falsification harness passed its controls, the kill criterion did not
fire, and the follow-up within-style question (NVB-96) is answered too. M1's PCA
and clustering items are the next unstarted work.

**Check-ins can be logged as of 2026-08-30 (NVB-80)** —
`python scripts/checkin.py`, storing to a gitignored `data/taam.db`. This is the
one thing that cannot be backfilled, so it ships before the model, before the
catalog clients, and before any UI. Everything else in this repo is still a plan.

Run `python tests/test_m0_harness.py` first — it proves the harness can both
detect a signal and refuse to endorse noise. The verdict is only worth trusting
because that second control exists.

## Tracking

Linear project: **taam** (team: Naveh Brenner) —
https://linear.app/naveh-brenner/project/palate-dbb61e29912b

Issues are milestone-shaped and each carries its kill criteria. The repo docs are
the source of truth for design; Linear is the source of truth for *what is
being worked on*.

**NVB-80 (start logging beers) is done — so start logging.** NVB-76 (M0) and
NVB-96 (within-style) are both run; nothing is blocked on a download any more.
