# 12 — Prior Art

Researched Aug 2026. The short version: **the diary is solved, the decision
engine is not, and the exact idea was tried once at scale and got absorbed.**

## The cautionary tale: Next Glass

Next Glass (2014) was almost exactly this project. Scan a label, get a
personalised 0–100 score predicting whether *you* would like it, built on
lab-analysed chemical profiles plus your rating history.

It was well funded. It worked. It merged with Untappd in 2016, the personalisation
disappeared as a consumer feature, and the company pivoted into B2B brewery and
menu software — later acquiring BeerAdvocate (which became independent again in
2026).

**The lesson:** this idea has been validated *and* the market pulled it toward
selling software to bars rather than to drinkers. Which is fine — this is not a
business (see `01-vision-and-scope.md`). But it explains why the gap is still
open, and it means "why doesn't this exist?" has an answer that isn't "it's
impossible".

## Untappd

> ⚠️ **Corrected 2026-08-30.** This section previously read "a diary, not a
> recommender… it does not build a taste model of you and does not claim to."
> **That was wrong**, and it was the load-bearing claim under this project's
> novelty story, so it is corrected here rather than quietly edited.

~10M users, and it **does** build a taste model and recommend from it. Untappd's
own published description of the feature: *"As users build a taste profile from
their history of check-ins and beers they've rated, Untappd will recommend new
beers for the user to try in their current location."* The App Store listing
sells the same thing — "check in and rate drinks to build personal drink
profile", "track taste preferences across multiple drink categories",
"suggestions for new drinks".

It has also expanded well past beer: spirits, cocktails, non-alcoholic and
THC-infused drinks are all in the app now. **So "multi-domain" is not a
differentiator either.** D-014's shared-axis design is still interesting, but as
engineering, not as a gap in the market.

**What is genuinely still absent, and how confident we are:**

| | Confidence | Why |
|---|---|---|
| **The model is never shown to you** | high | Every published description of the feature is of a silent recommender. Nothing surfaces *"you like bitter, you dislike heavy body"*. The year-end Recappd shows top styles and breweries — descriptive statistics of what you drank, not a model of why. |
| **No mood/context conditioning** | high | Nothing anywhere does this. |
| **No honest uncertainty** | high | Recommendations are presented flat; nothing says "I don't know you well enough yet". |
| **Cross-domain *transfer*** | medium | They now cover multiple drink categories, but almost certainly track them separately. Predicting whisky from a beer-derived palate is still, as far as we can tell, unattempted. |
| **Israeli availability** | medium | Recommendations are location-based off venue menus, which are thin here. Unverified. |

**The honest reading:** Untappd occupies more of this space than this document
used to admit. The remaining gap is not "nobody predicts what you'll like" —
they do. It is "**nobody shows you the model**", which is narrower, and happens
to be the half of taam that CLAUDE.md calls the actual point.

**And as of 2026-08-30 Untappd is not available to us as a source at all** — see
`DEAD-ENDS.md` DE-002. General API access is closed; keys now require contacting
them directly. So (a) and (b) below are both gone:

- ~~(a) an excellent catalog with good Israeli coverage~~ — inaccessible.
- ~~(b) the source of community scores for the `α` term~~ — inaccessible. The
  `α` term now has no data source at all, which makes "does `α` earn its place?"
  a question M4 must answer rather than a design choice.
- (c) **not a competitor in the part that matters** — it recommends, but it
  never explains. That is now the whole of the distinction, and it should be
  stated that narrowly.

## The current small fry

| Product | What it does | Relevance |
|---|---|---|
| **PINtPOINT** (UK) | Closest in spirit. Swipe-based preference elicitation builds a style profile in <60s, then scores against *actual nearby tap lists*. Positions itself as "Untappd is the diary, we're the decision engine". | Their elicitation approach is D-007 option D. Their critique of collaborative filtering matches ours independently. |
| **Picky Pint** | Photo of a beer menu → scores the options | The menu-pick use case, shallow |
| **Drinkist "Smart Pick"** | Reads a menu when you can't decide | Same |
| **Brewzy** | AI beer journal, label scanner, LLM chatbot | Essentially no users. Shows the LLM-wrapper approach is easy and not obviously valuable. |
| **Vivino** (wine) | Personal match score that people actually trust | **The proof the pattern works.** The closest thing to a demonstration that this is achievable. |

## What nobody does

Ranked by how confident we are the gap is real:

1. **A persistent, inspectable model of your palate.** Several products predict
   what you'll like — Untappd among them. **None show you the model.** This is
   the whole gap now, and it is still the most interesting part.
2. **Mood / context conditioning.** Absent everywhere.
3. **Cross-domain transfer** (beer palate → whisky recommendations). Untappd now
   *covers* several drink categories, so breadth is no longer novel; predicting
   one domain from another still appears to be.
4. **Honest uncertainty.** Every product presents a confident score. None say
   "I don't know you well enough yet".
5. **Israeli availability.** Every serious app is US- or UK-catalogued.

## Prior art in the research literature

- Multi-aspect review modelling on the BeerAdvocate/RateBeer corpora (McAuley et
  al.) — the source of both our datasets and the per-aspect structure.
- Cold-start work on text-based collaborative filtering — relevant to D-007.
- The 86-distillery whisky clustering studies — a well-trodden path, which is
  good: it means the whisky data is clean and the expected results are known.

## Honest assessment

Revised 2026-08-30, after finding that Untappd recommends and that its API is
closed to us.

**As a business: don't.** Crowded, low-margin, Next Glass already ran the
experiment and got absorbed, and the incumbent has ~10M users and does a version
of the core feature.

**As a product with a novelty claim: the claim is much narrower than this
document used to imply.** "Predicts what you'll like" is taken. What is left is
"*and shows you why, in terms of a palate you can read*", plus mood conditioning
and cross-domain transfer. That is a real gap, but it is one feature, not a
category.

**As a personal ML project: unaffected, and this is the honest answer to "is it
still worth doing".** The stated purpose (CLAUDE.md) is fun and the ML —
preference elicitation, Bayesian priors with a population prior, hierarchical
models, active learning, uncertainty, LLM-as-feature-extractor — over a dataset
you grow by drinking beer. None of that depends on nobody else having built a
recommender. Untappd having one does not make Bayesian regression at N=30 less
interesting to implement, and it cannot tell you what *your* palate looks like,
because it never shows you.

**What the competitive finding should actually change:** stop treating "nobody
does this" as a reason the project exists, because it is no longer true. The
reasons that survive are (1) you want to build it, (2) the interpretability
angle is genuinely unoccupied, and (3) M4's crossover-N result is a real
question about your own data that no product will ever answer for you. Those are
sufficient. The novelty framing was never load-bearing — it just needs to stop
being repeated.
