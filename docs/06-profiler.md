# 06 — The Profiler

**Job:** turn everything we know about an item into a fixed-length sensory vector.

This is the highest-risk component in the project. If profiles are noise, nothing
downstream can work, and no amount of clever modelling will rescue it. Hence M0
exists to try to break it before anything else is built.

> **No API provides descriptors.** Not Untappd, not catalog.beer, not anyone.
> That is why this component exists: the labels come from the Kaggle set, the
> model is ours, and a catalog contributes only the description string and the
> hard numerics that go in the top of it.

## Inputs

Never description-only. The structured fields are *measured facts* and inferring
them from prose when they can be looked up is strictly worse.

```
hard numerics   ABV, IBU, SRM            exact, use directly
categorical     style, maker, country    one-hot / embedded
text            description, ingredients  sentence embedding
```

## Option A — supervised regressor  *(current lean as primary)*

```
[ sentence_embedding(description)  ⊕  ABV, IBU, SRM  ⊕  style one-hot ]
                        │
                     small MLP / ridge
                        ▼
              descriptor vector (13–16 axes)
```

Trained on the ~3.2k labelled Kaggle beers.

**For:** deterministic forever, runs locally, free, auditable, and directly
scoreable against held-out labels. It is exactly "a model whose specialty is
profiling from a description", which is the thing we actually want.

**Against:** needs a description to exist; degrades on items unlike its training
distribution — which is precisely the Israeli beers we care most about. This is
the reason the chain has a second link.

**Open:** which sentence encoder; ridge vs. small MLP (try ridge first, 3.2k rows
is not a lot); whether to predict all axes jointly or independently.

## Option B — LLM profiler  *(current lean as fallback)*

Covers anything with a name. The instability concern is real, but it is a
**variance** problem, and variance is cheap to engineer down:

| Technique | What it fixes |
|---|---|
| temperature 0 + JSON schema output | most run-to-run jitter |
| k=5 samples, per-axis **median** | residual noise, as 1/√k — and the spread is a free confidence signal |
| 8–10 fixed anchor exemplars with known vectors in every prompt | **scale drift — the biggest failure mode.** Turns invention into interpolation |
| pinned model id + `profiler_version` on every row | silent re-scaling when a model is upgraded, which is worse than jitter |
| profile once, never re-profile | cross-call inconsistency becomes irrelevant by construction |

The last one deserves emphasis: *the worry "ask twice, get two answers" only
matters if you ask twice.* Write the profile to the DB and never ask again.

**Against:** unverifiable on out-of-distribution items (no labels there, by
definition); costs money; needs network; changes under you.

## Option C — manual
A 60-second form. Perfectly accurate for you, doesn't scale, always available.
The floor of the chain.

## Option D — the chain  *(current lean overall)*

```
regressor (if description exists and item is in-distribution)
   ↓ else
LLM ensemble (t=0, anchored)
   ↓ else
manual form
```

Every profile records which link produced it, so per-source quality can be
tracked separately forever.

### The main risk with the chain

**Scale consistency across sources.** If the regressor's "7 bitter" and the
LLM's "7 bitter" mean different things, the model learns on a warped space and
nobody notices. Mitigation: a **calibration set** of ~100 items profiled by
*every* source, with cross-source per-axis correlation and mean/variance offsets
reported. If offsets are stable, correct them; if they aren't, the chain is not
viable and we fall back to one source (probably B, for coverage).

## The validation experiment

> This is M0 and it is the first thing to build.

1. Hold out 200 beers from the Kaggle set (labels hidden).
2. Profile them with: regressor, LLM ensemble, and a **style-average baseline**
   (just the mean profile of that style).
3. Report per-axis Pearson r for each method.

**Interpretation:**

| Result | Meaning |
|---|---|
| r > 0.7 on bitter / sweet / body | Good. Proceed. |
| some axis at r < 0.4 | Drop that axis from the vocabulary (D-001). |
| **nothing beats style-average** | **Kill criterion.** The "profile" is a laundered style label; the content-based premise is in trouble. Re-open D-001/D-002 and consider that the honest project is style-based. |

That third row is the one to actually watch for. It is the cheapest possible way
to find out the project doesn't work, and finding that out in a day is a win.

## Dimensionality reduction (D-003)

The axes are heavily collinear — hoppy↔bitter, malty↔sweet↔body. Compressing
them is the cheapest available fix for the small-N problem in `07`.

**PCA first**, because it is three lines and interpretable. Expectation (to be
tested): 3–5 components carry 80%+ of the variance, PC1 ≈ light/crisp ↔
dark/rich, PC2 ≈ bitter/hoppy ↔ sweet/malty.

An autoencoder (D-003 option C) is only worth it if PCA leaves a lot on the
table. At 3.2k rows and ~16 dimensions, that would be surprising.

## Clustering, and one warning

Clusters give the "you like X" readout. But **cluster in profile space, then
name clusters by their dominant styles** — do not cluster on style labels.
Style is a marketing-contaminated proxy for flavour. The useful output looks
like *"crisp, low-bitter, light-bodied — mostly lagers and pilsners, plus some
wheat beers"*, which is a truer statement about a palate than "you like lagers"
and is arrived at honestly.
