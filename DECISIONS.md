# Decision Register

**Every decision in this project is OPEN.** This file exists so that no option is
lost, and so that a future session can pick up an argument mid-thought instead of
re-deriving it.

## Rules

- A decision leaves this register only by getting an **accepted ADR** in
  `docs/adr/`. Currently accepted ADRs: **none**.
- "Current lean" means *what we would do if forced to start today*. It is a
  recommendation, not a commitment, and it is allowed to be wrong.
- Alternatives are never deleted. If an option is falsified, it moves to
  `DEAD-ENDS.md` **with the evidence**, and stays visible here with a link.
- Adding a new option to an existing decision is always welcome and never
  requires justification.

## Index

| ID | Decision | Current lean | Status |
|---|---|---|---|
| D-001 | Beer descriptor vocabulary | Kaggle 13-axis set + hard numerics | OPEN |
| D-002 | How to profile an item | Supervised regressor, LLM as fallback | OPEN |
| D-003 | Dimensionality reduction | PCA first, autoencoder only if PCA disappoints | OPEN |
| D-004 | Primary catalog source | catalog.beer, Untappd second | OPEN |
| D-005 | Israeli / local coverage | Untappd + first-class manual entry | OPEN |
| D-006 | Preference model form | Bayesian linear regression on reduced axes | OPEN |
| D-007 | Population prior | Hierarchical fit on RateBeer/BeerAdvocate per-user data | OPEN |
| D-008 | Mood representation | Three separate mechanisms, not one | OPEN |
| D-009 | Check-in questions | 1 rating + 3 rotating, ≤30s | OPEN |
| D-010 | Rating scale | 0–10 integer, or forced pairwise | OPEN |
| D-011 | Exploration policy | Thompson sampling | OPEN |
| D-012 | App surface | SQLite + CLI first, Telegram bot second | OPEN |
| D-013 | Hosting, license, privacy | Private repo, no license | OPEN |
| D-014 | Cross-domain shared axes | 8 shared + per-domain tail | OPEN |
| D-015 | Item identity and dedup | brewery+name normalised key | OPEN |
| D-016 | Where the LLM runs | Hosted API | OPEN |

---

## D-001 — Beer descriptor vocabulary

*What are the axes of the profile vector?*

| Option | For | Against |
|---|---|---|
| **A. Kaggle 13-axis set** (malty, hoppy, bitter, sweet, sour, salty, astringent, body, spices, fruits, floral, alcohol, mouthfeel) | Comes with ~3.2k labelled beers, so it is trainable *today*. Derived from real review text. | US-craft-centric. Some axes (salty) are nearly constant and useless. |
| **B. BJCP-style sensory vocabulary** | Principled, brewer-legible, standard. | No labelled dataset. We would have to label it ourselves. |
| **C. Learned/latent axes only** — skip named descriptors, embed descriptions directly | Nothing hand-designed to get wrong. Maximum information retained. | Destroys interpretability, which is half the point of the project. |
| **D. Hybrid: hard numerics (ABV, IBU, SRM) + a named descriptor set + a residual embedding** | Keeps measured facts exact, keeps interpretability, keeps headroom. | More moving parts. Two things to validate instead of one. |

**Current lean:** D, with the named set initialised from A so we can train
immediately. Drop any axis that fails validation (see `docs/10-evaluation.md`).

**Open sub-questions:** Do we keep `salty`? Is `mouthfeel` distinct from `body`
in practice, or are they collinear? Should sourness be one axis or two
(lactic vs. acetic)?

---

## D-002 — How to profile an item

*Given a beer, where does its vector come from?*

| Option | For | Against |
|---|---|---|
| **A. LLM, prompted** | Works on any beer with a name. Zero training. Handles obscure Israeli beers a dataset never will. | Unstable across calls/models/phrasings. Scale drift. Silent breakage on model upgrade. Unverifiable. |
| **B. Supervised regressor** — sentence embedding of description ⊕ structured fields → descriptor vector, trained on the Kaggle labels | Deterministic forever. Local. Cheap. Auditable. Directly validated against held-out labels. | Needs a description to exist. Fails on beers unlike its training distribution (i.e. exactly the Israeli ones). |
| **C. Manual entry** | Perfectly accurate for you specifically. | Does not scale past ~50 beers. Boring. |
| **D. Chain: B → A → C** — try the regressor, fall back to a temperature-0 ensembled LLM, fall back to a 30-second manual form | Every beer gets a profile. Each source is recorded, so quality is measurable per-source. | Three code paths. Profiles from different sources may not be on the same scale — **this is the main risk and must be measured.** |

**Current lean:** D. But note the scale-consistency risk is not hypothetical; see
`docs/06-profiler.md` for the calibration plan that would have to work.

**If we use an LLM at all, non-negotiables** (these are engineering, not
decisions): temperature 0, JSON schema output, k-sample ensemble with per-axis
median, 8–10 fixed anchor exemplars in the prompt, `profiler_version` stored on
every row, and profile-once-never-reprofile.

---

## D-003 — Dimensionality reduction

| Option | For | Against |
|---|---|---|
| **A. None** — use all ~16 axes raw | Nothing lost. Simplest. | Axes are heavily collinear (hoppy↔bitter, malty↔sweet↔body). Makes the small-N problem worse than it needs to be. |
| **B. PCA** | Three lines of code. Interpretable components. Directly shrinks the parameter count in D-006. | Linear only. Components may not be cleanly nameable. |
| **C. Autoencoder** | Captures non-linear structure. | Almost certainly overkill at 3.2k rows and 16 dims. Harder to interpret. Needs its own validation. |
| **D. Supervised reduction** — pick axes by which ones actually predict *Naveh's* ratings | Optimises the thing we care about. | Circular at small N. Cannot be done before there is data. Revisit at N≈50. |

**Current lean:** B now, D later, C only if B leaves >30% variance unexplained in
the first 4 components.

**Note:** this decision is coupled to D-006. Fewer effective dimensions is the
single cheapest way to make the model work at N=10.

---

## D-004 — Primary catalog source

| Option | Coverage | Fields | Cost | Notes |
|---|---|---|---|---|
| **catalog.beer** | ~67k beers, ~6.6k brewers | name, style, ABV, IBU, description | free key | Actively maintained (docs updated Aug 2026). Best fit for "give me a beer record". |
| **Untappd API** | Very large, incl. good Israeli coverage | name, style, ABV, IBU, community rating | free key, **100 calls/hour**, no tap lists | Rate limit is fine for personal use with permanent caching. |
| **beer.db** | Community, Europe-heavy | name, style, ABV | public domain | Zero legal friction. Good for bulk seeding. |
| **Kaggle Beer Profile set** | ~3.2k | **labelled descriptor vectors** | free | *Not a catalog.* This is the profiler's training set. Do not confuse the two. |
| **Scraping** | Whatever you point it at | whatever is on the page | ToS violation | Defensible as a one-time backfill of a few hundred local beers. Not as a running pipeline. |

**Current lean:** catalog.beer as primary lookup, Untappd as secondary and as the
source of community scores (which D-006 needs), beer.db as bulk seed, manual as
the always-available floor.

---

## D-005 — Israeli / local coverage

Checked and worth recording: **Untappd's Israeli coverage is better than
expected.** Tempo, Israel Beer Breweries (IBBL), Biratenu, Sheeta and Beer Bazaar
all have full beer lists, and there is a country-filtered top-rated page.

| Option | For | Against |
|---|---|---|
| **A. Untappd API only** | Already covers most of it. Legitimate. | 100/hr. Hebrew/English name variants will be messy. |
| **B. One-time scrape of Israeli brewery pages** | Gets a local corpus in an afternoon. | ToS. Goes stale. |
| **C. Manual entry as first-class path** — label photo → OCR → LLM fills fields → you correct | Always works. Handles the shop-shelf case that no API covers. | Needs real UX effort, not a hidden admin form. |
| **D. Give up on local, only track imports** | Simplest. | Defeats a large part of the point. |

**Current lean:** A + C. C is underrated and should be built early — the
"standing in a shop holding an unknown bottle" case is the most common real use.

---

## D-006 — Preference model form

| Option | Works at N=10? | Interpretable? | Gives uncertainty? | Notes |
|---|---|---|---|---|
| **A. Bayesian linear regression on reduced axes** | Yes, if d≈4–6 | Yes — weights *are* the palate | Yes, natively | The obvious starting point. |
| **B. Gaussian process** | Yes | Partially | Yes | Handles non-linear taste (e.g. "bitter is good, but only up to a point"). More knobs. |
| **C. Ordinal / ranking model** | Yes | Yes | Yes | Matches how humans actually rate. Avoids pretending 7 vs 8 is meaningful. |
| **D. Small MLP** | **No** | No | No | Included for completeness. Will overfit. Do not start here. |
| **E. Matrix factorisation / collaborative filtering** | No | No | Sort of | Needs thousands of your ratings. Popularity-biased. Documented here so nobody re-proposes it. |

**Current lean:** A, with C as a strong candidate once there is enough data to
tell them apart, and B if residual plots show curvature.

**The decomposition** (somewhat separable from the model form, and the part worth
keeping whatever else changes):

```
your_rating(item) ≈ α · community_score(item)  +  w_you · profile(item)  +  b
                    └── free, no learning ──┘    └── the personal part ──┘
```

At N=0 this reduces to community recommendations. `w_you` lifts off zero
smoothly as data arrives. No cliff, no fine-tuning instability. `α` is itself
interesting — low `α` means you are a contrarian.

**Explicitly rejected mechanism (but kept here so it isn't re-invented):**
train a net on the Kaggle ratings and *fine-tune on 10 personal samples*. There
is no learning rate that both moves the model and doesn't destroy it. The fix is
decomposition, not fine-tuning.

---

## D-007 — Population prior

*Where does the "reasonable human palate" prior come from?*

| Option | For | Against |
|---|---|---|
| **A. No prior** — plain ridge with a fixed penalty | Trivial. | Wastes the single biggest advantage available. |
| **B. Prior from aggregate community scores only** | Easy. | Only gives a mean, not a distribution over palates. |
| **C. Hierarchical fit over per-user histories** in the RateBeer (40k users / 2.9M reviews) and BeerAdvocate (33k users / 1.6M reviews) dumps | Yields a real *distribution over taste vectors*. 10 ratings is genuinely enough to locate yourself inside a well-estimated prior. This is the technical heart of the project. | Real work. Datasets end in 2011, so the beers are dated even if the palates aren't. Requires joining reviews to profiles. |
| **D. Prior from a preference-elicitation quiz** — pairwise "this or that" at signup | Gives a usable profile in 60 seconds with zero drinking. Proven approach (PINtPOINT does exactly this). | Stated preference ≠ revealed preference. |

**Current lean:** C as the ambition, D as the cheap warm start, and they compose
— the quiz picks your starting point *within* the population distribution.

**Open worry:** the 2011 cutoff. Palate axes are probably stable; beer fashion is
not. Needs a sanity check before leaning on it.

---

## D-008 — Mood representation

The key observation: the example moods are **not the same kind of object**, and
conflating them is why this feature is usually bad.

| Mood | What it actually is | Mechanism |
|---|---|---|
| "something light, at noon" | a constraint | **1. Filter** over candidates |
| "with a burger", "with friends" | a shift in what's good | **2. Offset** `δ_m` on the taste vector |
| "something strong, to get drunk" | a different objective | **3. Objective swap** |
| "feeling exploratory" | not a taste statement at all | **3. Exploration weight** |

| Option | For | Against |
|---|---|---|
| **A. All three mechanisms** | Each is simple and correct for its case. Mechanism 1 works with zero data. | Three things to build. |
| **B. Offsets only** | Uniform. | Needs a lot of per-mood data before it does anything. |
| **C. LLM re-ranks the top 20 given a free-text mood** | Handles moods you never anticipated. Very cheap to build. | Unverifiable. Inconsistent. But possibly a great *v1* while data accumulates. |
| **D. Hard-coded rules only** | Predictable. | Never learns anything. |

**Current lean:** A, but built in order 1 → 3 → 2, because 2 is the only one that
needs data. C is a legitimate stopgap and should not be dismissed.

**Non-negotiable regardless of choice:** log context at check-in time from day
one, before any of it is modelled. It is one tap. Un-collected context cannot be
recovered later.

---

## D-009 — Check-in questions

Constraint: the whole check-in must be **under 30 seconds** or it will not
survive contact with an actual bar.

| Option | For | Against |
|---|---|---|
| **A. Rating only** | Fastest. | Throws away the signal that makes small-N work. |
| **B. Rating + 3 fixed questions** | Consistent, comparable across all entries. | Repetitive; the answers will start to autopilot. |
| **C. Rating + 3 questions chosen by information gain** — ask about the axes the model is currently least certain about | Every question earns its place. Genuinely the right answer in an active-learning framing. | Inconsistent data across entries. Harder to analyse. Needs the model to already exist. |
| **D. Rating + free text, parsed later by an LLM** | Zero friction, most natural. | Parsing is another unverifiable step. |

**Current lean:** B to bootstrap, C once the model exists. D as an optional
extra field that costs nothing to collect and might be mined later.

**Candidate question bank** — see `docs/09-checkin-ux.md`.

---

## D-010 — Rating scale

| Option | For | Against |
|---|---|---|
| **A. 1–5 stars** | Familiar. | Too coarse. Everything lands on 3.5–4.5. |
| **B. 0–10 integer** | Enough resolution without false precision. | Still absolute, still drifts over time. |
| **C. Forced pairwise comparison** ("better than the last IPA?") | Far more reliable than absolute ratings. Immune to scale drift. | Awkward UX. Needs a comparison partner. |
| **D. Both: absolute rating + occasional pairwise calibration** | Best of both; pairwise anchors the absolute scale over time. | More to build. |

**Current lean:** B, with D as the upgrade. **Worth knowing:** your own
test–retest reliability on absolute ratings is probably ±0.5 on a 5-point scale.
That noise floor caps how good *any* model here can get — see
`docs/10-evaluation.md`.

---

## D-011 — Exploration policy

| Option | Notes |
|---|---|
| **A. Thompson sampling** | Falls straight out of the Bayesian posterior. One line. Naturally balances. **Current lean.** |
| **B. UCB** | More tunable, more explainable ("this is a risky pick"). |
| **C. ε-greedy** | Trivial, wasteful. |
| **D. Pure exploitation + a manual "surprise me" button** | Honest and simple; puts the user in control instead of the algorithm. |

The exploration weight is also the mechanism behind the "feeling exploratory"
mood (D-008), so this is more load-bearing than it looks.

---

## D-012 — App surface

| Option | For | Against |
|---|---|---|
| **A. SQLite + Python CLI** | Fastest to build. All the ML is right there. | Useless in a bar. |
| **B. Telegram bot** | Actually usable one-handed while holding a beer. No app store. Photos work. | Awkward for browsing. |
| **C. Local web app (FastAPI + a page)** | Flexible, nice for the palate visualisations. | Needs to be reachable from a phone. |
| **D. Native / PWA mobile app** | The real answer for the shop-shelf case. | Most work by far. |

**Current lean:** A for all model development, B as the first real interface,
C for the "look at my palate" visualisations. D only if the project survives.

---

## D-013 — Hosting, license, privacy

Open: private vs. public repo; whether the drinking log is something to publish;
license (none / MIT / CC0 for any derived data); where the DB lives and whether
it is backed up. Nothing decided. Note the log is personal alcohol-consumption
data — worth a deliberate choice rather than a default.

---

## D-014 — Cross-domain shared axes

*Which axes are shared across beer / whisky / wine, and which are domain-local?*

Proposed shared set (8): sweetness, bitterness, body/weight, acidity, intensity,
alcohol heat, fruitiness, smoke-or-oak.

Proposed domain tails: beer → hoppy, malty, floral, astringent;
whisky → smoky, medicinal, honey, nutty, winey, spicy;
wine → tannin, minerality, earthiness.

The payoff if this works: beer ratings warm-start the whisky model with zero
whisky ratings. See `docs/11-multi-domain.md`. **Untested assumption:** that
cross-domain preference transfer is real for an individual. Worth an early
cheap test.

---

## D-015 — Item identity and dedup

Open: how to key an item across sources. `normalise(brewery) + normalise(name)`
is the obvious start and will break on Hebrew/English variants, brewery renames,
seasonal editions, and vintage years (which matter enormously for wine and
whisky and not at all for most beer). Needs a real think before the catalog is
populated, because retrofitting identity is painful.

---

## D-016 — Where the LLM runs

Open: hosted API (best quality, costs money, changes under you, needs network in
a bar) vs. a local small model (free, stable, private, weaker) vs. no LLM at all
if D-002 option B validates well enough. Coupled to D-002 and D-005.
