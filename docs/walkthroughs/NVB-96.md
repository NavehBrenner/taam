# NVB-96 — within-style discrimination

*2026-09-02 · closes the question M0 left open · M1 item 4*

## The question

M0 asked whether a beer's descriptors can be predicted from its text and
numbers, and the answer was yes — but style-average, which reads nothing at all,
got r = 0.53–0.84 on its own, and the text added about +0.03.

That comparison flatters the baseline, because most of the variance in the labels
is *between* styles. The recommender does not do that task. It picks between six
beers on a menu, four IPAs on a shelf — things that are already similar. So:

**Can the profiler tell two beers of the same style apart?**

Style-average scores exactly zero on this by construction: every IPA gets the
identical vector. It is the one comparison where the baseline cannot compete, and
it decides whether D-002 option E (style-average as the floor of the chain) is the
honest answer or a strawman we set up to knock down.

## What we actually did

Same harness, same splits, same three methods, two additions:

1. **`--within-style`** — centre every axis on the *train* style mean, in train
   and holdout alike, and score against that residual. Style-average then
   predicts a constant, so its R² is ~0 and any lift is within-style signal that
   cannot have been laundered from the style label.
2. **Same-style pairwise ranking accuracy**, reported in both modes — of two
   holdout beers of the same style, how often is the predicted order right?
   0.5 is chance; style-average scores exactly 0.5 because every same-style pair
   is a tie. This is the metric the downstream job actually runs.

Run on the 1,850 beers that have a description (`--text-only`), 20 × 400-beer
holdouts, per the issue.

Deliberately not done: no encoder swap (that is NVB-97, and mixing the two would
confound them), no within-style Spearman on top of pairwise accuracy — for a
ranking question they say the same thing and one metric is enough.

## What we found

**The M0 lift is mostly between styles, not within them.**

| axis | within-style variance | r on residual (text) | R² | pair acc. numerics | pair acc. **text** |
|---|---|---|---|---|---|
| Astringency | 49% | 0.081 ± 0.057 | 0.003 | 0.523 | 0.545 |
| Body | 34% | 0.129 ± 0.068 | 0.014 | 0.549 | 0.556 |
| **Alcohol** | 48% | 0.451 ± 0.119 | 0.183 | 0.656 | 0.659 |
| **Bitter** | 41% | 0.299 ± 0.132 | 0.034 | **0.489** | **0.608** |
| Sweet | 50% | 0.223 ± 0.084 | 0.045 | 0.576 | 0.588 |
| Sour | 24% | 0.103 ± 0.069 | 0.007 | 0.520 | 0.551 |
| Salty | 47% | 0.034 ± 0.045 | −0.005 | 0.507 | 0.509 |
| Fruits | 33% | 0.147 ± 0.075 | 0.018 | 0.551 | 0.565 |
| Hoppy | 41% | 0.151 ± 0.122 | 0.026 | 0.523 | 0.566 |
| Spices | 39% | 0.177 ± 0.112 | 0.032 | 0.558 | 0.566 |
| Malty | 35% | 0.112 ± 0.076 | 0.011 | 0.536 | 0.557 |

Baseline in every row: style-average, which is r = n/a (it predicts a constant),
R² ≈ 0, and pair accuracy exactly 0.500 ± 0.000.

Three readings, in order of how much they matter:

1. **Only `Alcohol` clears the r = 0.40 bar within style — and the text is not
   what gets it there.** Numerics-only already reaches r = 0.395 and 0.656 pair
   accuracy, because ABV is a measured number and alcohol warmth is what it
   measures. The description adds +0.003 pair accuracy on top. This axis is not
   evidence for the profiler; it is evidence for reading the label.

2. **`Bitter` is the one axis where the description is the only source of
   signal.** Numerics-only ranks same-style pairs at **0.489 — worse than a
   coin.** Add the text and it goes to **0.608**. `Hoppy` repeats it weaker
   (0.523 → 0.566). So the text is doing genuine within-style work, on exactly
   the axes beer descriptions talk about, and close to nothing anywhere else.

3. **Read the size.** 0.608 means: shown two beers of the same style, the
   profiler puts the bitterer one first three times in five. That is a real
   signal and a poor ranker. The eight remaining axes sit between 0.509 and
   0.588 — closer to the coin than to anything useful.

## What surprised us

**`Min IBU` and `Max IBU` are not this beer's IBU. They are the style's.** Zero
of 111 styles have any variation in either column — they are BJCP style ranges
copied onto every row. Which means "numerics-only", inside a style, is an
**ABV-only model**, and the finding that it cannot rank bitterness is not a
finding about numerics at all. It is a finding about a dataset in which no
per-beer bitterness number exists.

This also retro-explains an M0 result: "numerics add essentially nothing over
style" was half-guaranteed, because two of the three numerics *are* the style.

**Bitter's numerics-only pair accuracy is below chance (0.489).** With no
within-style information in the features, ridge fits noise and the sign is a coin
flip; that it landed slightly below 0.5 is not meaningful in itself, but it is a
clean demonstration that the feature set is empty for this question.

**r and R² come apart badly on the residual.** M0 measured them agreeing to
≈0.01 on the raw labels. Here Bitter scores r = 0.299 but R² = 0.034, where a
per-split optimal rescale would give ≈0.107. The residual predictions are
mis-scaled, not merely small. Pair accuracy is immune to this, which is another
argument for leading with it.

## What this moved

- **D-002 option E is confirmed as the floor, not a strawman** — on 9 of 11 axes.
  What the profiler buys over the style label, on a beer that has a description,
  is bitterness and hoppiness ranking inside a style at three correct calls in
  five, an alcohol number ABV already gave us, and little else.
- **D-002's Hebrew sub-decision is priced, not settled.** The result cuts both
  ways: the lift is not concentrated within style (which favours option C, skip
  text for Hebrew), but the part that *is* within-style is carried entirely by
  the description on Bitter and Hoppy (which is what C would throw away). Still
  no lean — deliberately.
- **ROADMAP M1 item 4 closes.** Items 1–3 (PCA, component naming, clustering) are
  untouched and still open.
- **Nothing moved to `DEAD-ENDS.md`.** Nothing was falsified. Option E gained
  evidence; option B was measured, not killed.
- Code: the harness gained `--within-style`, a third metric, and a third control
  in `tests/test_m0_harness.py` asserting that centring removes the style and
  leaves the text signal.
- Also fixed on the way past: `CONTEXT.md` still said M0 was unrun and blocked on
  a Kaggle download. It has been run since 2026-09-01.

## What we tried that failed

Nothing was abandoned, but one thing in the harness was wrong enough to be worth
naming: the first version of the within-style verdict inherited M0's
`DROP these from the vocabulary (D-001)` line, and so cheerfully advised dropping
ten of eleven axes because they score below r = 0.40 **on the residual**. That is
the wrong instrument for this question — D-001's bar is stated on raw labels,
where those axes are predicted well. Caught before the numbers were recorded;
the message now branches on the mode.

Same family of bug as the two the harness has already produced (single-split
verdict, `Notes:`-only descriptions). All three were the verdict logic, not the
model — which is the third time the *reporting* was wrong rather than the
experiment.

## Still open

- **How much of the residual is unlearnable?** The Kaggle descriptor labels are
  aggregates, so an unknown share of the within-style spread is label noise.
  Nothing here separates "the profiler cannot see it" from "there is nothing to
  see". **NVB-84** (rating noise ceiling) is the same question one level up and
  would supply the missing denominator. This is now the cheapest high-value run.
- **Would a real IBU change the answer?** See below — it is the weakest point in
  this readout.
- **NVB-97** (sentence encoder) is unaffected by this and still worth running: it
  bounds how much better any text representation can do.
- **NVB-98** (non-linear head), filed off the back of this issue. Every profiler
  number this project has reported came from one model class, `RidgeCV`, and that
  was never tested — only assumed. Filed separately from NVB-97 on purpose:
  representation and head move one at a time, or neither result is readable.
- **The LLM profiler (D-002 option A) has still never been run**, on either
  question.

## Where to push back

**My weakest claim: "the numerics cannot rank bitterness within a style."** True
of *this dataset*, and possibly not true of the system we are building. The
Kaggle IBU columns are style ranges, but a real catalog entry — or a bottle label,
or a brewery page — often carries a *measured* IBU that varies within style. If
we get that number, within-style bitterness ranking probably improves
substantially, and the profiler's contribution here is a lower bound rather than
an estimate. I have not checked whether catalog.beer or the Israeli brewery pages
actually publish per-beer IBU; that is a half-hour check and it would change how
this table should be read.

Second-weakest: US-craft data with populous style labels makes style-average
unusually strong, so the within-style residual is unusually small. On the Israeli
tail, where a "style" may have three exemplars, the split between within and
between should be different — and we cannot measure it there.

Decisions that are yours:

1. **Does M1 continue to PCA and clustering now, or does NVB-84 (noise ceiling)
   jump the queue?** My recommendation: **NVB-84 first.** Every number in this
   readout is missing its denominator, and PCA on the labelled vectors will still
   be there afterwards.
2. **Is the per-beer IBU check worth doing before either?** My recommendation:
   yes, and it is small — it decides whether the profiler's within-style ceiling
   is 0.61 or something meaningfully higher.
3. **Should option E be promoted from "floor of the chain" to "the default
   profiler, with B as an enhancement on beers with a description"?** I am not
   recommending it — it would read as locking a decision on one dataset — but the
   evidence now points that way and it deserves a deliberate answer rather than
   drift.
