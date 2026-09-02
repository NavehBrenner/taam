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

### What M0 actually returned (2026-09-01, NVB-76)

Data: the Kaggle set, 3,197 beers. Method: 20 random 400-beer holdouts, per-axis
Pearson r, mean ± sd. Reproduce with

```bash
python scripts/m0_profiler_validation.py --data data/raw/beer_profile_and_ratings.csv
```

| axis | style-average | numerics-only | text+numerics | lift over baseline | reliable? |
|---|---|---|---|---|---|
| Astringency | 0.661 ± 0.030 | 0.662 ± 0.030 | **0.681 ± 0.027** | +0.020 | 20/20 ✅ |
| Body | 0.787 ± 0.022 | 0.786 ± 0.023 | **0.797 ± 0.022** | +0.010 | 17/20 |
| Alcohol | 0.695 ± 0.031 | 0.748 ± 0.069 | **0.787 ± 0.060** | +0.092 | 18/20 |
| Bitter | 0.765 ± 0.021 | 0.766 ± 0.022 | **0.807 ± 0.020** | +0.042 | 20/20 ✅ |
| Sweet | 0.681 ± 0.031 | 0.687 ± 0.055 | **0.703 ± 0.058** | +0.022 | 17/20 |
| Sour | 0.835 ± 0.020 | 0.834 ± 0.020 | **0.849 ± 0.017** | +0.014 | 18/20 |
| Salty | **0.532 ± 0.204** | 0.531 ± 0.200 | 0.504 ± 0.160 | −0.001 | 11/20 |
| Fruits | 0.790 ± 0.022 | 0.789 ± 0.027 | **0.803 ± 0.028** | +0.013 | 17/20 |
| Hoppy | 0.756 ± 0.022 | 0.757 ± 0.022 | **0.787 ± 0.018** | +0.031 | 20/20 ✅ |
| Spices | 0.747 ± 0.045 | 0.750 ± 0.044 | **0.788 ± 0.034** | +0.041 | 20/20 ✅ |
| Malty | 0.773 ± 0.018 | 0.772 ± 0.019 | **0.787 ± 0.020** | +0.014 | 17/20 |

"Reliable" = the lift over style-average was positive on every one of the 20
splits. On pure noise that is p ≈ 2·10⁻⁶ per axis, so it is a real bar, and the
negative control in `tests/test_m0_harness.py` still fires the kill criterion.

**The kill criterion did not fire.** Four axes beat style-average reliably, and
all three headline axes clear r = 0.7. The project's premise survives.

**But read the size of the lift, not just its sign.** The largest reliable lift
is **+0.042** (Bitter). Not one axis reaches the +0.05 materiality bar. The
honest summary:

> Style-average, which reads no text at all, is worth r ≈ 0.53–0.84 on its own.
> Everything the description and the numerics add on top of it is about +0.03.

#### …and read it on both scales, because r hides the size

`r` is Pearson correlation between prediction and label, **not** R². The identity
`R² = r²` you may be carrying from a statistics class is a property of OLS
evaluated *in-sample*; out of sample the two come apart, because `r` is invariant
to any affine transform of the prediction and R² is not. A model with the right
shape at the wrong scale scores r ≈ 1 and R² < 0, and only R² notices.

On this data they happen to agree to ≈ 0.01, because both predictors are
near-calibrated (regressing truth on prediction gives slopes of 0.91–1.07). That
is a *measured fact about these predictors*, not a property of the metric, which
is why the harness now prints both.

It matters, because r compresses near the top of its range and made the result
look smaller than it is. Same numbers, second scale — the model column is
whichever of numerics-only / text+numerics has the higher mean r:

| axis | Δr | ΔR² | R² base → model | share of *remaining* variance explained | reliable? |
|---|---|---|---|---|---|
| Astringency | +0.020 | +0.027 | 0.433 → 0.460 | 4.7% | 20/20 ✅ |
| Body | +0.010 | +0.016 | 0.617 → 0.633 | 3.8% | 17/20 |
| Alcohol | +0.092 | +0.121 | 0.479 → 0.599 | 22.9% | 18/20 |
| Bitter | +0.042 | +0.066 | 0.584 → 0.649 | **15.8%** | 20/20 ✅ |
| Sweet | +0.022 | +0.022 | 0.460 → 0.482 | 4.1% | 17/20 |
| Sour | +0.014 | +0.022 | 0.692 → 0.714 | 6.6% | 18/20 |
| Salty | −0.001 | +0.001 | 0.304 → 0.305 | −0.6% | 11/20 |
| Fruits | +0.013 | +0.020 | 0.622 → 0.643 | 5.3% | 17/20 |
| Hoppy | +0.031 | +0.048 | 0.568 → 0.616 | **11.0%** | 20/20 ✅ |
| Spices | +0.041 | +0.062 | 0.553 → 0.615 | **13.1%** | 20/20 ✅ |
| Malty | +0.014 | +0.022 | 0.594 → 0.616 | 5.2% | 17/20 |

"+0.042 r on Bitter" and "style-average explains 58% of the holdout variance,
text explains 65%, so the description kills **16% of what the baseline left on
the table**" are the same fact. The second is the more useful one for deciding
whether the profiler earns its keep. Across the four reliable axes the text kills
**5–16%** of residual variance, with bootstrap intervals that stay positive
(Bitter [+9.8, +19.8], Hoppy [+5.3, +17.0], Spices [+1.2, +21.4], Astringency
[+1.3, +8.4]).

Two limits on that framing, so it does not oversell in the other direction:

- **Share-of-remaining-variance flatters a strong baseline.** It divides by
  `1 − R²_base`, so the better the baseline, the bigger the same absolute gain
  looks. ΔR² is the neutral column; both are printed.
- **Alcohol's 22.9% is noise wearing a large number** — its interval is
  [−48.7, +41.8] and it is positive on only 18/20 splits. Only the four ✅ axes
  have intervals clear of zero.

The verdict bars stay stated in `r` (the 0.40 drop bar, the sign test) because
that is what D-001 is written in; R² and ΔR² are reported alongside so the size
of a lift cannot be misread again.

#### 42% of the beers have no description, and it halved the measured lift

Every description in the Kaggle set begins with the literal string `Notes:`. For
**1,347 of 3,197 beers — 42% — that is the entire field.** There is no
description, only the prefix. An empty-string check passes them, which is how
they went unnoticed: the text path was dead weight on two beers in five, and the
lift above is that dilution averaged in.

Rerun on the 1,850 beers that have at least one word of description
(`--text-only`; the split is clean, 1,850 have ≥ 1 word and 1,347 have exactly
zero, so there is no judgement call at the boundary):

| axis | Δr | ΔR² | R² base → model | resid killed | reliable? |
|---|---|---|---|---|---|
| Astringency | +0.030 | +0.054 | 0.389 → 0.443 | 8.5% | 20/20 ✅ |
| Body | +0.019 | +0.030 | 0.625 → 0.656 | 7.8% | 19/20 |
| **Alcohol** | **+0.167** | **+0.252** | 0.443 → 0.695 | **44.7%** | 20/20 ✅ |
| **Bitter** | **+0.072** | **+0.113** | 0.538 → 0.651 | **24.5%** | 20/20 ✅ |
| Sweet | +0.069 | +0.100 | 0.430 → 0.530 | 17.2% | 19/20 |
| Sour | +0.021 | +0.036 | 0.709 → 0.745 | 11.2% | 20/20 ✅ |
| Salty | +0.002 | +0.024 | 0.240 → 0.264 | 2.0% | 12/20 |
| Fruits | +0.032 | +0.053 | 0.619 → 0.671 | 13.5% | 20/20 ✅ |
| **Hoppy** | **+0.066** | **+0.103** | 0.516 → 0.619 | **21.3%** | 20/20 ✅ |
| **Spices** | **+0.054** | **+0.081** | 0.528 → 0.610 | **17.3%** | 20/20 ✅ |
| Malty | +0.016 | +0.026 | 0.613 → 0.639 | 6.7% | 19/20 |

**The result roughly doubles.** Reliable lift goes from 4 axes to **7**, and the
materiality bar — which nothing cleared on the full set — is now cleared by
**four axes**: Alcohol, Bitter, Hoppy, Spices. Bitter's description kills a
quarter of the variance style-average leaves behind; Alcohol's kills nearly half.

Two things to keep straight about this comparison:

- **The baseline weakens too.** The subset is 1,850 beers rather than 3,197, so
  style means are estimated from fewer exemplars — Bitter's base R² falls
  0.584 → 0.538. Part of the wider gap is a noisier baseline, not only a stronger
  model. The direction is not in doubt, the exact magnitude is.
- **This is the honest number for our actual use case.** A beer we want to
  profile either has a description or it does not. On the ones that do, this
  table is what the text is worth; on the ones that do not, the text path
  contributes nothing by construction and the chain falls through to its next
  link. Averaging the two together answers a question nobody asks.

`Salty` collapses further here (base R² 0.240) and remains unreliable at 12/20 —
consistent with it being near-constant rather than hard.

Three things follow, none of which close a decision:

1. **Style is not a poor proxy for flavour — it is a very good one**, at least on
   US-craft data with clean style labels. The warning in "Clustering" below still
   stands for the *readout*, but as a *predictor* the style label is strong.
2. **Numerics alone add essentially nothing over style** (ABV/IBU are largely
   determined by style; only Alcohol, unsurprisingly, moves). The lift is coming
   from the description text, which is the good news for the premise and the bad
   news for D-002's Hebrew fork.
3. **`Salty` is the unstable one**, but not in the way D-001 predicted. Its mean
   r of 0.532 clears the 0.40 bar, so it is not dropped — yet its sd of **0.204**
   is 7× any other axis. It is near-constant in the data (D-001 option A already
   flagged this), so a handful of outliers dominate the correlation and the
   number swings wildly by split. Treat r = 0.53 on Salty as not measured rather
   than as measured-and-fine.

#### The single-split trap, and what it cost

The first run of this experiment used one 200-beer holdout, as originally
specified above. It reported *"WORKS on 3/11 axes: Alcohol, Sweet, Spices"*.
That verdict is **wrong**: over 20 splits, Alcohol and Sweet are not reliable at
all, and it missed Bitter, Hoppy and Astringency entirely. Three of the four
names changed.

A 0.05 margin on one 400-beer holdout sits inside the split-to-split noise
(sd ≈ 0.02–0.06 per axis). The harness now averages over 20 splits and requires
the lift to be positive on every one; `--seeds 1` reproduces the old behaviour if
you ever want to see it fail. This is the second time a control caught a bug in
this harness's verdict logic — see the header of `tests/test_m0_harness.py`.

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
