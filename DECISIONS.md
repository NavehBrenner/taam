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
| D-001 | Beer descriptor vocabulary | Kaggle 13-axis set + hard numerics; `salty` now unmeasured, not fine | OPEN |
| D-002 | How to profile an item | Supervised regressor, LLM as fallback; **Hebrew fork: M0 says C is cheap** | OPEN |
| D-003 | Dimensionality reduction | PCA first, autoencoder only if PCA disappoints | OPEN |
| D-004 | Primary catalog source | catalog.beer (CC BY 4.0 ✅); Untappd dead (DE-002) | OPEN |
| D-005 | Israeli / local coverage | label OCR + brewery pages + manual entry | OPEN |
| D-006 | Preference model form | Bayesian linear regression on reduced axes | OPEN |
| D-007 | Population prior | Hierarchical fit on RateBeer/BeerAdvocate per-user data | OPEN |
| D-008 | Mood representation | Three separate mechanisms, not one | OPEN |
| D-009 | Check-in questions | 1 rating + 3 rotating, ≤30s | OPEN |
| D-010 | Rating scale | 0–10 integer, or forced pairwise | OPEN |
| D-011 | Exploration policy | Thompson sampling | OPEN |
| D-012 | App surface | SQLite + CLI first, Telegram bot second | OPEN |
| D-013 | Hosting, license, privacy | Private repo, no license | OPEN |
| D-014 | Cross-domain shared axes | 8 shared + per-domain tail | OPEN |
| D-015 | Item identity and dedup | normalised key **+ a merge step** | OPEN |
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

**What M0 measured (2026-09-01, NVB-76).** No axis fell below the r = 0.40 drop
bar, so **nothing is dropped from the vocabulary** and option A's 11 measurable
axes all survive. Full table in `docs/06-profiler.md`.

The `salty` sub-question is *not* settled by that, and the result is more
interesting than a pass. Its mean r of 0.532 clears the bar, but its standard
deviation across 20 splits is **0.204** — 7× every other axis. The axis is
near-constant in the data, so its correlation is decided by a few outliers and
swings by split. The honest status is **unmeasured**, not fine. Two ways to
resolve it, no lean yet:

- **A. Keep it and let the model shrink it.** A near-constant axis carries almost
  no variance, so a ridge/Bayesian fit will assign it a near-zero weight anyway.
  Costs one dimension. Rule 5 (never drop context data) points here.
- **B. Score it on stability, not level** — e.g. require sd < 0.05 across splits
  as a second drop bar. This would drop `salty` today, and is the rule we would
  have wanted if the axis had been near-constant *and* below 0.40.

Note the vocabulary is 13 axes in option A but the Kaggle set only ships 11
scoreable ones (`floral` and `mouthfeel` are absent as columns). Those two are
untested by M0, not endorsed by it.

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

**A fifth option, added by M0's result (2026-09-01, NVB-76):**

| Option | For | Against |
|---|---|---|
| **E. Style-average** — the mean descriptor vector of the item's style, no text, no model | Scored r = 0.53–0.84 per axis in M0, within ~0.03 of the full text model. Needs only a style label, so it covers every beer including the Hebrew tail. Three lines of pandas, no training, no LLM, no network. | Cannot distinguish two beers of the same style — which is precisely the discrimination a recommender needs. Its ceiling as a *ranker within a style* is zero, and M0 measured prediction, not ranking. |

Option E is not proposed as a replacement for B; it is proposed as the honest
**floor of the chain in D**, in place of, or ahead of, the manual form. It is
also the thing every future profiler claim has to beat, per rule 1.

**The gap M0 leaves open:** it scored *reconstruction of descriptor labels*, not
*within-style discrimination*. Those are different questions and E is strong on
the first by construction. Whether the +0.03 that text adds is concentrated
exactly where it matters — separating two IPAs — is unmeasured. That is a good
candidate for M1.

**If we use an LLM at all, non-negotiables** (these are engineering, not
decisions): temperature 0, JSON schema output, k-sample ensemble with per-axis
median, 8–10 fixed anchor exemplars in the prompt, `profiler_version` stored on
every row, and profile-once-never-reprofile.

### Sub-decision: the local descriptions are in Hebrew (new 2026-08-30)

Option B trains on the English Kaggle descriptions. The descriptions we can
actually get for Israeli beers come from the breweries' own sites and are in
**Hebrew** (`docs/05`). Under TF-IDF this is not "unfamiliar vocabulary" — the
two languages share no tokens whatsoever, so the text path contributes exactly
nothing. A new fork, with no lean yet:

| Option | For | Against |
|---|---|---|
| **A. Translate to English first** (LLM, once per beer, cached) | Keeps the whole English-trained pipeline intact. Cheap: one call per beer, ever. Translation is the task LLMs are most reliable at, so it is the least dangerous place to put one. | An LLM enters the pipeline upstream of a number (rule 4 applies). Tasting vocabulary translates unevenly — "מרירות מדוייקת" is "precise bitterness", which is not idiomatic English beer-speak and may land off-distribution anyway. |
| **B. Multilingual sentence encoder** instead of TF-IDF | Handles both languages natively, no translation step, no LLM. | Contradicts M0's deliberate no-model-download stance. Unknown whether a multilingual encoder's Hebrew beer vocabulary is any good — almost certainly weaker than its English. Needs its own validation. |
| **C. Skip text for Hebrew beers; numerics only** | Zero new machinery. **May cost nothing at all** — M0 measures exactly this gap, and if text adds little over ABV/IBU/style then this option is simply correct. | Throws away the one signal we went looking for. Only defensible once M0 has quantified the loss. |
| **D. LLM profiles the Hebrew description directly** (D-002 option A, applied narrowly) | Sidesteps translation and encoding both. LLMs read Hebrew fine. | All of option A's instability, now on the local tail specifically — the beers with the fewest labels to validate against. |

**No lean yet, deliberately: M0 decides this.** If the text path barely beats
numerics-only on English data where it has every advantage, option C wins by
default and this whole sub-decision closes for free. Do not build A or B before
that number exists.

**The number now exists (2026-09-01, NVB-76).** On English data, with every
advantage, the text path is worth about **+0.03 Pearson r** over a style-average
that reads no text at all — reliably positive on 4 of 11 axes, and material
(≥ 0.05) on none. `docs/06-profiler.md` has the table.

That is the price of option C, and it is small. **Lean shifts to C** for the
Hebrew tail: skip the text path there, use style + ABV/IBU, and spend nothing on
translation or a multilingual encoder until something else justifies it. A and B
stay on the table and are cheap to revisit — the argument for them is now
quantified at ~0.03 r, so either one has to buy more than that.

Two caveats that keep this a lean and not a decision:

- The +0.03 is measured on **US-craft beers with clean, populous style labels**.
  Style-average is strong there precisely because each style has many exemplars.
  On the Israeli tail, styles are sparser and the baseline should be weaker, so
  text may be worth more than 0.03 exactly where we cannot measure it.
- It also assumes TF-IDF. A sentence encoder could widen the gap; M0 deliberately
  did not test one (see `docs/06-profiler.md`). If someone wants to reopen this,
  the experiment is "swap the vectoriser, rerun the same harness", which is an
  afternoon.

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
| **catalog.beer** | ~67k beers, ~6.6k brewers — but **10 beers for all of Israel** | name, style, ABV, IBU, description — **description empty for 10/10 Israeli beers** | free key, 1k req/month | **CC BY 4.0, verified 2026-08-30 (NVB-78).** Permanent retention, redistribution and commercial use all permitted; attribution required. Best fit for "give me a beer record" *outside* Israel. |
| **Untappd API** | Very large, incl. good Israeli coverage | name, style, ABV, IBU, community rating | free key, **100 calls/hour**, no tap lists | Rate limit is fine for personal use with permanent caching. |
| ~~**beer.db**~~ | **Zero Israeli rows** | n/a | public domain | ❌ **Falsified — see `DEAD-ENDS.md` DE-001.** Abandoned upstream since 2014; no Israel data anywhere in the org. Row kept so it is not re-proposed. |
| **Kaggle Beer Profile set** | ~3.2k | **labelled descriptor vectors** | free | *Not a catalog.* This is the profiler's training set. Do not confuse the two. |
| **Scraping** | Whatever you point it at | whatever is on the page | ToS violation | Defensible as a one-time backfill of a few hundred local beers. Not as a running pipeline. |

**First, the correction that reframes this decision:** *no API returns flavour
descriptors.* Not Untappd, not catalog.beer, not anyone. Descriptors come from
our own profiler trained on the Kaggle labels (§06). A catalog contributes only
name / brewery / style / ABV / IBU / a description string. Untappd was never the
descriptor source, so "we need Untappd for the profiles" is false.

### Sub-decision: how (and whether) to use Untappd at all

| Option | For | Against |
|---|---|---|
| **A. Documented API only**, on demand, nothing held past 24h | Clean. Citable in the README. Sufficient — see the arithmetic below. | Descriptions may be thin for Israeli micro-brews. Shelf-photo bursts strain 100/hr. |
| **B. Private local scrape**, facts only, scripts outside the repo, never published | Gets the local tail in an afternoon. Facts are uncopyrightable (*Feist*); no distribution, no realistic claim. | Contract claim survives copyright (see *hiQ*); API key is clickwrap. Risks the personal Untappd account. **Makes the public repo a demo nobody can run.** Unreproducible data upstream of M0. |
| **C. Scrape and document it in the README** | Honest about provenance. | The worst configuration: legal risk unchanged, **enforcement risk multiplied** — a public repo under a real name is exactly what Untappd finds searching GitHub. |
| **D. Drop Untappd entirely** | Zero terms friction; every row citable. | Loses community scores (the `α` term) and the Israeli long tail. |

**Outcome, 2026-08-30: D — and not on merit.** Untappd closed general API
registration; keys now require contacting them directly, which Naveh declined.
Options A, B and C all require credentials, so **D is the only one still
standing**. See `DEAD-ENDS.md` DE-002.

Recorded honestly because it matters for revisiting: the terms analysis below
was correct and stays correct, it just stopped being the binding constraint.
Access did. The upside is real — with Untappd gone, every remaining source has
clean terms and this decision's hardest problem disappears. The cost is that the
`α` community term has no data source at all.

**The arithmetic that makes A sufficient:** each beer is needed **once, ever** —
fetch, compute the profile vector, keep the vector and the facts, discard the
description. ~2 calls per beer, ~500 distinct beers over years ≈ 1,000 calls
total. Only the 40-bottle shelf photo (~80 calls) comes near the hourly ceiling.

**And the label is a primary source.** ABV is legally required on the bottle;
style, name and brewery are usually printed. That is most of a fact row — free,
authoritative, offline, attached to nobody's terms. Fallback chain:

```
local catalog (beer.db / catalog.beer) → label OCR → Untappd (description only) → type it
```

**Current lean overall:** catalog.beer as the **permanent** catalog; the label as
the primary source for local beers; Untappd demoted to an **on-demand, narrow**
gap-filler for descriptions and community scores; manual entry as the
always-available floor. beer.db is out (DE-001).

⚠️ **This lean moved because of Untappd's API terms** — they require caches to be
purged every 24 hours and forbid using the API to build your own beer database or
to "mine or analyze" the data. That is not a compliance footnote, it is a design
constraint: Untappd cannot back a permanent local store. See
`docs/13-scraping-policy.md`.

### What NVB-78 changed (2026-08-30)

**catalog.beer's terms are checked, and they are the best case: CC BY 4.0.**
Permanent retention, redistribution and commercial use are all permitted against
an attribution obligation. The blocking unknown that this decision hung on is
gone, and it landed in our favour.

**But the win is smaller than it looks, because the same spike measured the
data.** For Israel, catalog.beer has 3 of 12 breweries, 10 beers, and an empty
`description` on all 10. Descriptions appear only on `cb_verified` entries, of
which Israel has none. Two effects, pulling in opposite directions:

- **For the non-local catalog** — imports, travel, the M1 profile-space work —
  catalog.beer is now unambiguously the backbone, permanently cacheable and
  citable in public with no asterisk. That is a real and clean result.
- **For local beer it supplies name, brewery, style and ABV: exactly what is
  already printed on the bottle.** It adds identifiers and clean provenance, not
  information. The label-OCR and manual-entry paths therefore carry more of this
  project than the previous lean assumed — they are load-bearing, not a garnish.

**The one that could still swing the decision:** Untappd's `beer_description` for
Israeli beers is *still unmeasured* — it needs an API key, and the cheap way to
check is the scrape §10.1 forbids. Its stakes went up, not down. catalog.beer is
now known to have no local descriptions, so Untappd is the last candidate. If it
is also empty, **no source has prose for a local beer**, D-002 option B (the
trained regressor) cannot run on the local tail at all, and **option D — drop
Untappd entirely — becomes the answer** almost by default. Test spec in
`docs/13-scraping-policy.md` §12.

---

## D-005 — Israeli / local coverage

Checked and worth recording: **Untappd's Israeli coverage is better than
expected.** Tempo, Israel Beer Breweries (IBBL), Biratenu, Sheeta and Beer Bazaar
all have full beer lists, and there is a country-filtered top-rated page.

| Option | For | Against |
|---|---|---|
| **A. Untappd API only** | Already covers most of it. Legitimate. | 100/hr. Hebrew/English name variants will be messy. |
| **B. One-time private scrape of Israeli brewery pages** | Gets a local corpus in an afternoon. Facts aren't copyrightable; no distribution, no realistic claim. | Contract claim is independent of copyright (*hiQ v. LinkedIn*: won CFAA, **lost breach of contract**). Untappd: undocumented-API use → **immediate suspension of key and associated account**, "strictly monitored". Unreproducible data upstream of M0. **Policy either way: no scraper code in this public repo** (`docs/13-scraping-policy.md`). |
| **B2. Label OCR as the local fact source** | ABV is legally required on the bottle; style/name/brewery usually printed. Authoritative, offline, nobody's terms, and it's the shelf-pick path anyway. | Needs the bottle in hand — no bulk seeding. Doesn't give a description. |
| **C. Manual entry as first-class path** — label photo → OCR → LLM fills fields → you correct | Always works. Handles the shop-shelf case that no API covers. | Needs real UX effort, not a hidden admin form. |
| **D. Give up on local, only track imports** | Simplest. | Defeats a large part of the point. |

**Current lean:** A + B2 + C, and NVB-78 **strengthened B2 + C considerably.**
The shop-shelf case is the most common real use, and B2/C both serve it while
producing data that is unambiguously ours.

**Measured 2026-08-30 (NVB-78).** The two free-terms catalogs were tested against
a 12-brewery Israeli sample:

- **beer.db: zero Israeli rows, upstream dead since 2014.** Falsified — DE-001.
- **catalog.beer: 3/12 breweries, 10 beers, 0/10 with a description.** Present:
  Tempo (4), Malka (5), Jem's Beer Factory (1). Negev Brewery has a brewer record
  and no beers. Absent: IBBL, Biratenu, Sheeta, Beer Bazaar, Alexander, Bazelet,
  Herzl, Shapiro.

So **no free-terms catalog covers Israeli beer**, and the one with good terms
tells us nothing the bottle does not. Option D ("give up on local, only track
imports") remains on the table and is now the honest alternative to investing in
OCR — but taking it would concede most of the point of the project, and the
label genuinely does carry ABV, style, name and brewery for free. B2 + C stay
the lean; they are just no longer optional.

**Update 2026-08-30 — option A is gone, and something better replaced it.**
Untappd closed general API registration (DE-002), so "Untappd API only" is no
longer available at any price. The question of whether its descriptions were any
good is now permanently unanswerable and also moot, because the search for a
replacement found a better source than Untappd would have been:

**E. The brewery's own website.** Alexander publishes 16 beers with ~100-character
Hebrew tasting notes; Beer Bazaar 8; Malka none. Roughly two thirds of sampled
breweries publish usable prose, and it is *first-party* — written by the people
who made the beer, consistent within a brewery, and descriptor-bearing in exactly
the way the profiler wants ("malty, smooth and creamy, hinted sweetness, precise
bitterness" is four axes in one sentence). Strictly better than the user-written
Untappd entries we were hoping for.

Its costs are real but bounded: the text is Hebrew (a new fork — see D-002's
sub-decision), the prose is copyrightable so only the vector is kept, and there
is no API, so collection is by hand through the manual-entry flow. ~10 breweries
× ~10 beers is one evening, once.

**Current lean:** B2 + C + E, with catalog.beer for imports. Option D (give up on
local) is still on the table and still the honest alternative, but it is now
clearly the worse deal: the local data turned out to be *available*, just not
through an API.

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

**CLOSED by [ADR-0001](docs/adr/0001-public-repo-mit-license.md)** — public
repo, MIT, personal data kept out via `.env` + external DB + gitignored `data/`.
The alternatives considered are preserved in the ADR.

Still open underneath it: where the DB actually lives and how it is backed up;
whether an engine/UI split is ever worth making (revisit only if a product
appears).

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

**Evidence from NVB-78 (2026-08-30) — the problem is worse than "Hebrew vs
English", and it is already present inside a single source.**

- **Nothing in catalog.beer is in Hebrew script.** Every Israeli entry is
  transliterated, so the cross-script join never arises. The damage comes from
  *transliteration being unstable*: `Goldstar` / `Gold Star`, `Sheeta` / `Shita`,
  `Jem's` / `JEMS`. A normaliser must fold spaces, apostrophes and case before
  comparing, and that still will not catch everything.
- **catalog.beer already contains duplicates of the same beer.** `Goldstar` and
  `Gold Star Dark Lager` are two separate rows with distinct UUIDs for one
  product — same brewery, same 4.9% ABV, same (wrong) style. So dedup is not
  only a cross-source problem: **a single source needs deduping against itself**,
  which rules out any design that treats "one source, one authoritative row" as
  a simplifying assumption.
- **Style strings are not trustworthy as identity or as features.** Both Goldstar
  rows are classified "South German-Style Dunkel Weizen / Dunkel Weissbier".
  Goldstar is a dark lager. If style feeds the profiler (D-001/D-002) or the
  style-average baseline (the bar in `docs/10-evaluation.md`), source-provided
  style needs verification, not trust.
- **Junk rows are publicly visible**, e.g. `[Postman API Test]` entries with
  77–91% ABV and 8,877 IBU. Identity work must sit behind a plausibility filter
  on ABV/IBU, or test data will land in the catalog with real-looking keys.

**Implication for the lean:** a pure deterministic `normalise(brewery)+
normalise(name)` key is not sufficient on its own. It needs a merge step —
probably a similarity pass over (brewery, ABV, style-class) proposing candidate
duplicates for one-tap confirmation at check-in time. That is cheap to add now
and painful later, which is exactly what this decision warned about.

---

## D-016 — Where the LLM runs

Open: hosted API (best quality, costs money, changes under you, needs network in
a bar) vs. a local small model (free, stable, private, weaker) vs. no LLM at all
if D-002 option B validates well enough. Coupled to D-002 and D-005.
