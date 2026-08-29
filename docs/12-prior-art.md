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

~10M users. **A diary, not a recommender.** Gives you a global community score
and what's trending nearby. It does not build a taste model of you and does not
claim to.

For this project it is: (a) an excellent catalog with genuinely good Israeli
coverage, (b) the source of community scores for the `α` term, (c) not a
competitor, because it isn't trying to do the thing.

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

1. **A persistent, inspectable model of your palate.** Nothing shows you what it
   thinks your taste is. This is the biggest gap and the most interesting part.
2. **Mood / context conditioning.** Absent everywhere.
3. **Cross-domain transfer** (beer palate → whisky recommendations). Absent
   everywhere, and probably the most novel thing here.
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

As a business: crowded, low-margin, and Next Glass already ran the experiment.

As a personal project touching preference elicitation, Bayesian priors,
hierarchical models, active learning, and LLM-as-feature-extractor — with a
dataset you're motivated to grow by drinking beer — it is a good one. The small
dataset is the interesting constraint, not a defect.
