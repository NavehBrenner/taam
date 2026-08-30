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
forbid "mining or analyzing" the data — which describes this project. The catalog
backbone therefore has to be catalog.beer + beer.db + manual entry, with Untappd
demoted to on-demand enrichment. **catalog.beer's own terms are unchecked and
should be read before anything is built on it.** Details in
`docs/13-scraping-policy.md`.

## Status

**Phase 0 → M0.** One decision made (ADR-0001: public repo, MIT). The M0
falsification harness is written and its controls pass; it needs only the Kaggle
CSV to produce a real verdict. Everything else in this repo is still a plan.

Run `python tests/test_m0_harness.py` first — it proves the harness can both
detect a signal and refuse to endorse noise. The verdict is only worth trusting
because that second control exists.

## Tracking

Linear project: **taam** (team: Naveh Brenner) —
https://linear.app/naveh-brenner/project/palate-dbb61e29912b

Issues are milestone-shaped and each carries its kill criteria. The repo docs are
the source of truth for design; Linear is the source of truth for *what is
being worked on*.

Start with **NVB-76 (M0, profiler validation)** and **NVB-80 (start logging
beers)**. The first can kill the project in a day; the second cannot be started
retroactively.
