# 11 — Multi-Domain Extension

Beer first, whisky second, wine third, anything after that nearly free.

## The design

Separate the **domain-specific sensory basis** from the **domain-agnostic
preference machinery**:

| Layer | Per domain? |
|---|---|
| catalog / ingest | yes — different sources entirely |
| descriptor vocabulary | yes — "hoppy" has no wine analogue |
| profiler | yes — different training data |
| **preference model** | **no** |
| **mood / exploration** | **no** |
| **recommender** | **no** |

The core sees only `(profile: R^d, rating: R, context: tags)`. It does not know
what the dimensions mean, and it must not need to.

**The test that this is real:** adding whisky must require zero changes under
`preference/` and `recommend/`. If it doesn't, the abstraction was decorative.

## Shared axes vs. domain tail (D-014)

Do **not** build one shared vocabulary across all beverages. Forcing it produces
mostly-zero vectors and meaningless axes.

```
profile = [ shared core (8) | domain tail ]
```

**Shared core** — the axes that genuinely mean the same thing everywhere:

```
sweetness · bitterness · body/weight · acidity
intensity · alcohol heat · fruitiness · smoke-or-oak
```

**Domain tails:**

| Domain | Tail axes |
|---|---|
| beer | hoppy, malty, floral, astringent, roasty |
| whisky | smoky, medicinal, honey, nutty, winey, spicy |
| wine | tannin, minerality, earthiness, oak |

## The payoff: cross-domain transfer

The preference model fits weights over the shared core **pooled across domains**,
plus a per-domain residual. Which means:

> Your beer ratings warm-start the whisky model with **zero whisky check-ins**.

"Bitter-loving, sweet-averse, high-intensity" plausibly does transfer across
categories in real people. If it does, it is the single most interesting result
this project could produce, and no existing product does it.

**This is an assumption, not a fact.** It should get a cheap early test — see
below — rather than being built on.

## Why whisky is the right second domain

1. **The data is already there.** The classic 86-distillery × 12-flavour
   hand-scored dataset is exactly the right shape: labelled, sensory, small,
   clean. Better ground truth than anything beer has.
2. **It is the hard case, and that's the point.** You will drink far fewer
   whiskies than beers. N will be ~15 forever. That is precisely where the
   population prior and cross-domain transfer have to earn their keep — if the
   architecture survives whisky, it survives anything.
3. Vintage/age and cask type introduce item-identity problems (D-015) that wine
   will also have. Better to hit them at 86 items than at 130,000.

## Wine

Nearly free once beer and whisky both work — the second domain is the expensive
one, the third only proves the abstraction was right.

Data: the WineEnthusiast ~130k review corpus has rich descriptions but no
structured flavour labels, so wine needs either label mining from the text or an
LLM profiler. Vintage matters enormously, which stresses D-015 hard.

## The cheap early test of the whole premise

Before building any of this: take the BeerAdvocate/RateBeer per-aspect sub-ratings
(taste, smell, feel, look) and check whether an individual's weights on the
shared-core-like aspects are **stable across styles**. If a person's preference
structure doesn't even transfer across beer styles, it certainly won't transfer
across beverages, and D-014 should be demoted before any effort goes into it.

Cheap, uses data we already need, and could save M7 entirely.

## Beyond drinks

Nothing in the core is about drinking. Coffee, tea, chocolate, cheese, olive oil,
perfume — same shape: sensory vector, sparse personal ratings, population prior.
Not a goal. Worth knowing the architecture doesn't forbid it.
