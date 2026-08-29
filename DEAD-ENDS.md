# Dead Ends

A log of approaches that were tried and abandoned, with evidence.

**This file is a feature.** The project is expected to hit walls; an approach
that was properly falsified is a result, and writing it down is what stops it
being re-proposed in six months. Entries are never deleted.

## Template

```
## DE-00N — <short name>
**Date:**
**Related decision:** D-0XX
**What we tried:**
**What we expected:**
**What actually happened:** (numbers, please)
**Why it failed:**
**What we did instead:**
**Would it be worth revisiting if…:**
```

---

## Entries

*None yet — nothing has been built.*

---

## Pre-emptively documented non-starters

These were reasoned about and rejected before any code was written. They are
recorded here so nobody re-derives them, but they were **never actually tested**,
so the reasoning is falsifiable and the door is not locked.

### Collaborative filtering as the primary model
Needs thousands of ratings from the target user. Public rating data is severely
popularity-skewed — a small fraction of items absorbs most ratings — so a model
trained on it tends to become a popularity predictor with a personalization
costume on. Recorded as D-006 option E.

### Fine-tuning a network trained on community ratings using ~10 personal samples
No learning rate exists that both moves the model meaningfully and avoids
destroying it. The intent behind the idea is right; the mechanism is wrong. The
fix is the additive decomposition in D-006, which achieves the same goal
(population knowledge + personal adjustment) with a stable, well-posed estimator.

### An autoencoder to map descriptions to profiles
Autoencoders are unsupervised reconstruction models. The Kaggle set provides
*labelled* target vectors, which makes this straightforwardly supervised
regression — strictly more direct and more accurate. (An autoencoder *is* still
a live option for compressing the profile vectors themselves — that is D-003
option C, and unrelated to this.)

### One shared descriptor vocabulary across all beverages
"Hoppy" has no wine analogue. Forcing a single vocabulary produces mostly-zero
vectors and meaningless axes. Replaced by the shared-core + domain-tail design
in D-014.
