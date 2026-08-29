# 07 — The Preference Model

**Job:** from a few dozen check-ins, learn a readable palate that predicts ratings
with honest error bars.

## The central difficulty

N is small — 10 at first, maybe 200 eventually, and for whisky it will be ~15
forever. Meanwhile ratings are noisy: mood, food, freshness, glassware and
expectation all move a score. Your own test–retest reliability is probably ±0.5
on a 5-point scale, which puts a hard ceiling on what *any* model here can
achieve (see `10-evaluation.md`).

So the design question is not "which model is most powerful" but **"which model
is well-posed at N=10 and honest about what it doesn't know"**.

## The decomposition

The piece most worth keeping regardless of what else changes:

```
your_rating(item)  ≈  α · community_score(item)  +  w_you · profile(item)  +  b
                      └──── population term ────┘   └─── personal term ───┘
```

| N | behaviour |
|---|---|
| 0 | `w = 0`, `α = 1`. You get community recommendations. Useful immediately. |
| 10 | `w` slightly off zero; predictions mostly community, gently tilted. |
| 50+ | `w` carries real signal; predictions are yours. |

No threshold, no cliff, no fine-tuning instability. And `α` is independently
interesting: a low `α` means your ratings diverge from the crowd — you're a
contrarian, quantified.

**Note `community_n` matters.** A 4.5 from six raters is not a 4.5 from six
thousand. Shrink community scores toward the global mean by rater count, or the
population term will be noisiest exactly where it's least justified.

## Model form options (D-006)

### A. Bayesian linear regression on reduced axes — *current lean*
With d≈4–6 (post-PCA) and a Gaussian prior, fitting from 10 observations is
well-posed. It won't be confident, but it will be **correctly calibrated about
its own uncertainty**, which is the property that actually matters:

> "3.8 ± 0.9" is useful at N=10. A network that says "4.2" with no error bar is
> lying to you.

The posterior over `w` also gives Thompson sampling for free (D-011), which is
the exploration mechanism *and* the "feeling exploratory" mood.

### B. Gaussian process
Handles genuine non-linearity — "bitter is good, but only up to a point", which
is a real phenomenon in palates. More knobs, less directly interpretable. Worth
trying if residual plots show curvature. Cheap at this data size.

### C. Ordinal / ranking model
Closer to how humans actually rate; avoids pretending that 7 vs 8 is a
meaningful metric distance. Pairs naturally with D-010 option C/D. A strong
candidate once there's enough data to distinguish it from A.

### D. Small neural network
Will overfit at any N this project will ever see. Documented so it isn't
re-proposed.

### E. Collaborative filtering
Needs thousands of your ratings; inherits severe popularity bias from public
rating data. Documented so it isn't re-proposed.

## The population prior (D-007)

This is the technically interesting part and the real answer to "can anything
learn from 10 samples".

**The weak version:** a fixed ridge penalty. Works, wastes the opportunity.

**The strong version:** the RateBeer and BeerAdvocate dumps contain *per-user*
rating histories — ~40k and ~33k users respectively. Fit a hierarchical model
across those users and you recover a genuine **distribution over taste vectors**,
not merely an average palate. Your 10 ratings then perform Bayesian inference
against that prior, pulling `w_you` toward the nearest dense region of real
human taste space.

Ten samples is genuinely enough to *locate yourself within a well-estimated
prior*. That is what priors are for, and it is what turns the answer to "can a
model learn from 10 samples?" from *sort of* into *yes*.

**The cheap warm start:** a 60-second pairwise elicitation quiz ("this or that")
at setup. Stated preference is not revealed preference, but it picks your
starting point *within* the population distribution, which is exactly what a
prior is supposed to do. The two compose; they are not alternatives.

**Open worry:** those datasets end in 2011. Palate structure is likely stable;
beer fashion certainly isn't. Sanity-check before leaning hard on it.

## Explicitly rejected mechanism

**Train a network on community ratings, then fine-tune on 10 personal samples.**

The intent is right — combine population knowledge with personal adjustment —
but the mechanism fails. There is no learning rate that both moves the model
meaningfully and avoids destroying it: too low and nothing happens, too high and
it memorises ten points. This is the classic tiny-data fine-tuning failure.

The decomposition above achieves the same goal with a stable, well-posed
estimator. Kept in `DEAD-ENDS.md` so it isn't re-invented.

## The palate readout (R-23)

Not an afterthought — arguably the main deliverable. The weight vector, rendered
as something a human can agree or disagree with:

```
Your palate, from 34 check-ins:

  bitterness   ██████████░░░  strong positive   (±0.2)
  sweetness    ░░░██████████  strong negative   (±0.3)
  body         ██████░░░░░░░  mild positive     (±0.5, still uncertain)
  sourness     ░░░░░░░░░░░░░  no signal yet

  You agree with the crowd about 60% of the way (α = 0.6).
  Least explored: high-sourness, low-bitterness beers.
```

"No signal yet" and the error bars are the point. A readout that projects
confidence it hasn't earned is worse than no readout.
