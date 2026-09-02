# NVB-76 — M0, profiler validation

*2026-09-01 · [PR #4](https://github.com/NavehBrenner/taam/pull/4) · closes M0*

## The question

**Can we turn what we know about a beer — name, style, ABV, IBU, a paragraph of
description — into a flavour vector we can trust?**

Everything downstream assumes we can. The preference model learns weights over
profile axes; the recommender ranks by distance in profile space; the "what does
my palate look like" readout is a sentence about those axes. If the profiles are
noise, all of that is arithmetic on noise, and the honest move is to stop.

M0 exists to try to make that happen cheaply, on day one, before anything is
built on top.

The sharper form of the question is not "are profiles predictable" — it is
**"are profiles predictable from something other than the style label"**. A
profiler that has secretly learned "IPAs are bitter" is not a profiler. It is a
style lookup table with extra steps, and it can never tell two IPAs apart.

## What we actually did

Three predictors, scored against the 3,197 labelled Kaggle beers on held-out
data with per-axis Pearson r:

1. **style-average** — the mean descriptor vector of that beer's style. Reads no
   text at all. This is the baseline that matters.
2. **numerics-only** — ridge on ABV / IBU + style one-hot.
3. **text+numerics** — ridge on TF-IDF(description) plus the above.

Deliberately not done, and why:

- **No LLM profiler.** It costs money, needs network, and is only worth
  evaluating once the cheap deterministic floor is known. That number now exists,
  so an LLM run has something to beat.
- **No sentence encoder.** TF-IDF is deterministic, needs no model download, and
  at ~3k rows is a fair fight. If text had beaten the baseline decisively,
  swapping in an encoder would be a tuning step, not a rescue.
- **No Kaggle credentials.** Turned out not to be needed at all — see below.

## What we found

3,197 beers, 20 random 400-beer holdouts, mean ± sd:

| axis | style-average | numerics-only | text+numerics | lift | reliable? |
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

"Reliable" = the lift over style-average was positive on **every** one of the 20
splits. On pure noise that is p ≈ 2·10⁻⁶ per axis.

**The kill criterion did not fire.** Four axes beat the baseline reliably, all
three headline axes clear r = 0.7, and nothing falls below the r = 0.40 drop bar,
so no axis leaves the vocabulary. The project's premise survives.

**But the size is the story, not the sign:**

> Style-average, which reads no text at all, is worth r = 0.53–0.84 on its own.
> Everything the description and the numerics add on top of it is about **+0.03**.
> The largest reliable lift is +0.042 (Bitter). Not one axis reaches the +0.05
> materiality bar.

Numerics alone add essentially nothing over style — ABV and IBU are largely
determined by style, and only Alcohol moves, unsurprisingly. The lift that does
exist is coming from the description text.

### The same result on the R² scale, which reads very differently

`r` is Pearson correlation, not R². (`R² = r²` holds for OLS *in-sample*; out of
sample the two come apart, because r is invariant to affine transforms of the
prediction and R² is not.) Here they agree to ≈ 0.01 — both predictors are
near-calibrated, slopes 0.91–1.07 — so squaring is safe on this table. That was
worth checking, because r compresses near the top of its range and made the
result look smaller than it is:

| axis | Δr | ΔR² | R² base → model | share of *remaining* variance explained |
|---|---|---|---|---|
| Astringency ✅ | +0.020 | +0.027 | 0.433 → 0.460 | 4.7% [+1.3, +8.4] |
| Bitter ✅ | +0.042 | +0.066 | 0.584 → 0.649 | **15.8%** [+9.8, +19.8] |
| Hoppy ✅ | +0.031 | +0.048 | 0.568 → 0.616 | **11.0%** [+5.3, +17.0] |
| Spices ✅ | +0.041 | +0.062 | 0.553 → 0.615 | **13.1%** [+1.2, +21.4] |
| Alcohol | +0.092 | +0.121 | 0.479 → 0.599 | 22.9% [−48.7, +41.8] |

"+0.042 r on Bitter" and "style-average explains 58% of holdout variance, text
explains 65%, so the description kills **16% of what the baseline left on the
table**" are the same fact. The second is the more useful one for deciding
whether the profiler earns its keep. Across the four reliable axes, text kills
**5–16%** of residual variance with intervals clear of zero.

Two limits, so this does not oversell in the other direction: the
share-of-remaining framing divides by `1 − R²_base`, so it flatters a strong
baseline (ΔR² is the neutral column); and Alcohol's 22.9% is noise wearing a
large number — 18/20 splits, interval [−48.7, +41.8].

## What surprised us

**Style is a much better proxy for flavour than the docs assumed.** `06-profiler`
warns that style is "a marketing-contaminated proxy for flavour" — true for the
*readout*, but as a *predictor* on this data it is strong, and it sets a bar the
content model barely clears. We went in expecting to measure how much text adds;
we ended up measuring how little anything adds over knowing the style.

The likely reason is mechanical rather than deep: this is US-craft data with
clean, populous style labels. Each style has many exemplars, so its mean is
well-estimated. That is a property of the dataset, not of beer.

**`Salty` failed in an unexpected direction.** D-001 predicted it would be
"nearly constant and useless" and would fall below the drop bar. It did not — its
mean r is 0.532, comfortably over 0.40. But its standard deviation across splits
is **0.204**, seven times every other axis. Because it is near-constant, a
handful of outliers decide the correlation, and it swings wildly by split. The
axis is not measured-and-fine. It is **unmeasured**, and the drop bar was the
wrong instrument to catch it.

**The dataset needed no Kaggle credentials.** The download endpoint serves this
one anonymously. `curl -I` returns 404 only because there is no HEAD handler; a
GET works. `data/README.md` had said an API token was required, which blocked
this issue for two days for no reason.

## What this moved

- **D-001** — nothing dropped from the vocabulary. `salty` recorded as
  *unmeasured, not fine*, with two logged ways to resolve it (keep it and let the
  model shrink it, per rule 5; or add a *stability* drop bar alongside the level
  bar). No lean between them. Also noted: the Kaggle set ships 11 scoreable axes,
  not 13 — `floral` and `mouthfeel` have no columns and are untested by M0, not
  endorsed by it.
- **D-002 sub-decision (Hebrew)** — this fork was explicitly waiting on M0, and
  M0 has now priced it. Option C, "skip text for Hebrew beers, numerics only",
  costs **~0.03 r**. The lean moves there: do not build translation or a
  multilingual encoder to buy 0.03. A and B stay on the table with a number
  attached, which is what they were missing.
- **D-002 gains option E** — *style-average as a profiler*. Not a replacement for
  the supervised regressor; the honest **floor of the chain**, ahead of the manual
  form, and the thing every future profiler claim has to beat under rule 1. Its
  weakness is recorded too: it cannot rank two beers of the same style at all.
- **ROADMAP M1** gains a new item — **within-style discrimination**. See below.
- Nothing moved to `DEAD-ENDS.md`. Nothing closed.

## What we tried that failed

**The harness was reading its verdict off a single holdout, and it was wrong.**

The first real run reported `WORKS on 3/11 axes: Alcohol, Sweet, Spices`. That
verdict is wrong. Over 20 splits, Alcohol and Sweet are not reliable at all, and
it had missed Bitter, Hoppy and Astringency entirely. **Three of the four names
changed.** The reliable set is Astringency, Bitter, Hoppy, Spices.

The cause: a fixed 0.05 margin on one 200-beer holdout sits inside the
split-to-split noise, which is sd ≈ 0.02–0.06 per axis. The margin was standing
in for statistical significance without measuring it.

This is the **second** time this harness's verdict logic has been wrong. The
first — ridge beating a near-zero baseline on noise — was caught by the negative
control and fixed with an absolute r bar. This one the controls could not catch,
because both controls ran on a single split too: the bug was in the experimental
design, not in the code.

The fix replaces the proxy with the real thing: 20 splits, and the lift must be
positive on **every** one. That is a sign test at p ≈ 2·10⁻⁶ per axis on noise,
so the harness can still say stop, and the negative control confirms it does.
`MARGIN = 0.05` survives as a *materiality label* rather than a pass/fail gate,
which is why the report now says "reliable but not material" out loud instead of
silently promoting a +0.02 lift to a finding. `--seeds 1` reproduces the old
behaviour if you want to watch it fail.

`run_splits()` is now shared between the script and the control tests, so the
thing being validated and the thing doing the validating cannot drift apart
again.

Worth naming plainly: **a bug in the instrument is worse than a bug in the
product**, because it silently corrupts every number the instrument has ever
produced. Both of this harness's bugs inflated confidence rather than destroying
it, which is the direction that does damage.

## Still open

- **Within-style discrimination — the question M0 could not answer.** M0 scored
  *reconstruction of descriptor labels*, which is exactly the task style-average
  wins by construction. It never asked whether the profiler can separate two
  IPAs, which is the only thing a recommender actually needs. The +0.03 might be
  concentrated precisely there, in which case it matters far more than its size
  suggests — or it might be spread evenly, in which case option E is the honest
  answer and the regressor is decoration. **This is now an M1 item and it decides
  D-002.**
- **Does the baseline hold up on the Israeli tail?** Style-average is strong here
  because US-craft styles are populous. Israeli styles will be sparser, so the
  baseline should weaken and text may be worth more than 0.03 — exactly where we
  have no labels to measure it. Uncomfortable, and unresolved.
- **`salty`** — keep it and shrink it, or add a stability bar? Cheap either way,
  no rush.
- **Would a sentence encoder widen the gap?** The experiment is "swap the
  vectoriser, rerun the same harness". An afternoon, and it now has a clear
  number to beat.

## Where to push back

**My weakest claim was that +0.03 is small — and it has already partly broken.**

I first reported this as "the profiler is not the star of the show". Naveh asked
whether `r` was the R² from statistics class; checking that produced the ΔR²
column above, and it undercuts the framing. +0.042 r on Bitter is +0.066 R², a
sixth of the variance the baseline left unexplained. Not nothing. The claim was
not false, but it was stated on a scale that compresses near the top of its
range, which is a way of being misleading while being correct.

Recorded because it is the instructive part: the number was right, the *scale*
was the editorial choice, and reporting one scale rather than two is how a result
gets undersold. The harness now prints both.

**What is still genuinely unmeasured**: whether the lift is concentrated where
the recommender lives — inside a style, between two beers whose style vectors are
identical. Style-average scores zero on that task by construction, so a modest
average lift over it could be an enormous relative lift on the only comparison
that counts. M1 has to answer this before D-002 can move further.

The second-weakest: **20 random splits of one dataset are not 20 independent
measurements.** Train sets overlap heavily, so the sign test is somewhat
anti-conservative. It is far more honest than one split, and the effect sizes are
not near the boundary, but "positive on 20/20" should be read as *stable across
resampling*, not as a clean p-value.

**Decisions that are yours:**

1. **Does M1 get reordered to put within-style discrimination first?** My
   recommendation: yes. PCA and clustering are interesting; this one decides
   whether D-002's whole chain is worth building.
2. **`salty`: keep or add a stability bar?** My recommendation: keep it for now
   (rule 5), and add the stability bar as a reporting column rather than a gate,
   so the next near-constant axis is visible without being silently dropped.
3. Nothing here is blocked on you except the merge of
   [PR #4](https://github.com/NavehBrenner/taam/pull/4).
