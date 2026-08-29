# 08 — Mood and Context

## The observation that makes this tractable

The example moods look like one feature. They are not:

| "I want…" | What it actually is | Mechanism |
|---|---|---|
| something light, it's noon | a **constraint** on the item | 1. Filter |
| I'm eating a burger | a **shift in what's good** | 2. Offset |
| I'm with friends, relaxed | a shift, probably weak | 2. Offset |
| something strong, I want to get drunk | a **different objective** | 3. Objective swap |
| feeling exploratory | not a taste statement at all | 3. Exploration weight |

Treating these as one thing is why mood features are usually bad. Split them and
each becomes simple.

## Mechanism 1 — filters

Mood maps to hard/soft constraints over the candidate set.

```
"light, noon"    →  abv ≤ 5.5, body ≤ 5
"session"        →  abv ≤ 4.5
"nightcap"       →  abv ≥ 7, intensity ≥ 6
```

Deterministic, needs **zero training data**, and honestly delivers most of the
practical value. Build this first.

Open: hard filters (exclude) vs. soft (penalise)? Soft is more forgiving when
the candidate set is small — a bar with 6 taps may have nothing under 5.5% ABV,
and returning nothing is worse than returning the closest thing with a caveat.

## Mechanism 2 — a context offset on the palate

```
rating ≈ (w + δ_m) · profile
```

`δ_m` is a small per-mood adjustment vector with a **strong prior pulling it
toward zero**. Same hierarchical trick as the main model, applied to a second
axis:

| check-ins in that context | behaviour |
|---|---|
| 0–3 | `δ ≈ 0`; falls back to base palate. Nothing breaks. |
| ~15 | `δ` starts to move. |
| 30+ | genuine statements like *"with food you shift toward more body and more bitterness"* |

Graceful degradation is the entire point — a mood you've used twice must not
produce a wild recommendation.

**Kill criterion:** if per-mood offsets remain statistically indistinguishable
from zero at 30 check-ins per context, then mood really is just filters and
objectives. That's a fine answer, and much cheaper.

## Mechanism 3 — objective swap and exploration

Some moods don't change taste, they change *what is being optimised*:

```
"get drunk"    →  maximise abv, subject to predicted_rating ≥ acceptable
"exploratory"  →  maximise posterior variance in a region you probably like
"safe"         →  pure exploitation, minimise variance
"cheap"        →  maximise rating per shekel   (needs price — see 04, parked)
```

The exploration ones cost nothing extra: the Bayesian model already produces the
posterior, so this is just choosing what to do with it. One slider,
exploit ↔ explore.

Make the objective function pluggable and this whole category is a few lines.

## The non-negotiable

> **Log context at check-in time from day one, before any of it is modelled.**

It is one tap. Un-collected context cannot be recovered, ever. This is the
highest-value, lowest-cost decision in the project, and it is the one most
likely to be skipped because none of it is used yet.

See R-12 and the `checkin_context` table in `04-data-model.md`.

## The stopgap worth taking seriously (D-008 option C)

Before there is enough data for mechanism 2: hand the top ~20 candidates plus a
free-text mood to an LLM and let it re-rank.

It is unverifiable and inconsistent — and it handles moods nobody anticipated,
costs an afternoon to build, and gives something to use while data accumulates.
Do not dismiss it on purity grounds; just don't confuse it with the model, and
don't let its output feed back into training data.

## UI

Never a form. Preset chips, each a named bundle of *(filter, δ_m, exploration
weight, objective)*:

```
[ light & crisp ]  [ with food ]  [ exploring ]  [ going hard ]
[ cold day ]  [ hot day ]  [ nightcap ]  [ safe bet ]
```

Adding a mood = adding a row. Free-text stays available for the long tail and
feeds the stopgap above.

## Open questions

- Fixed tag vocabulary or free tags? (Hybrid is the obvious compromise.)
- Should time of day / weather be auto-filled rather than asked? Cheaper, but
  auto-filled data is easy to trust more than it deserves.
- Do moods compose? "with food" + "exploring" — sum the offsets, or is that
  nonsense? Untested.
- Is "who I'm with" a context, or a confound that just adds noise?
