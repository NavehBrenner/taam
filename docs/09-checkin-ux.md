# 09 — Check-in UX

## What exists (NVB-80, 2026-08-30)

`scripts/checkin.py` — a terminal prompt implementing the flow below, minus
steps 1's scan/OCR paths. Item pick is recent-list → text search → manual add;
rating is 0–10 (D-010 option B); the three bootstrap questions are fixed
(D-009 option B) and stored with `question_id` + `question_version`; context
tags are pre-filled from the last check-in and Enter accepts them.

Deliberately not built: a phone app, offline sync, prediction display, OCR.
Data collected now cannot be backfilled; a UI can be written at any time.

## The binding constraint

**Under 30 seconds, one-handed, in a noisy bar, possibly after two beers.**

Every design question here resolves against that constraint. A check-in flow that
is 90 seconds long is a check-in flow that gets abandoned in week three, and
then there is no project.

## The flow

```
1. identify the item     scan / search / recent / manual   ~10s
2. overall rating        one tap                            ~2s
3. 2–4 follow-ups        taps, no typing                   ~10s
4. context chips         taps, pre-suggested                 ~3s
5. optional free text    skippable, usually skipped
```

Step 4 must be pre-populated from time of day and last-used tags so that the
common case is *confirming*, not entering.

## Rating (D-010)

0–10 integer as the current lean. 1–5 stars is too coarse — everything lands
between 3.5 and 4.5 and the model gets nothing to work with.

The upgrade worth considering: occasional **pairwise calibration** — "better than
the last IPA you had?" Absolute ratings drift over months; pairwise doesn't.
Interleaving one comparison every few check-ins would anchor the scale for very
little cost.

## The follow-up questions

Purpose: give the model information the overall rating cannot carry. A single
scalar from 20 samples is very little; three cheap extra dimensions per check-in
roughly triples the signal per beer drunk.

### Candidate question bank

Each maps to something the model can use.

**Diagnostic (which axis drove the rating?)**
- "What stood out?" → chips: *bitter · sweet · sour · malty · fruity · roasty ·
  boozy · watery · nothing much*
- "Too much of anything?" → same chips. **Negative signal is scarcer and more
  informative than positive.**
- "Would you have another right now?" → yes / no / one was enough
  *(this may be a better target variable than the rating itself — worth testing)*

**Calibration**
- "Better or worse than the last one of this style?" → better / same / worse

**Context-linked**
- "Would this have been better in a different situation?" → chips: *with food ·
  colder day · summer · alone · not now*

**Exploration value**
- "Surprised you?" → yes / no. Directly measures whether the model's prediction
  was wrong, which is the cheapest possible model-error signal.

### Selection strategy (D-009)

- **Now (bootstrap):** three fixed questions — *what stood out*, *too much of
  anything*, *another right now*. Consistent and comparable.
- **Later:** choose questions by **information gain** — ask about the axes the
  model is currently least certain about. This is the correct active-learning
  framing and it makes each question earn its place. Requires the model to exist.
- **Always:** keep free text as an optional field. It costs nothing to collect
  and may be mined later.

Questions carry a `question_id` **and** `question_version` (see
`04-data-model.md`) so the bank can evolve without silently merging a reworded
question with its predecessor.

## Item identification

In rough order of speed:

1. **Recent / nearby** — you often drink what you drank before.
2. **Search** — text, against the local cache first, then the APIs.
3. **Label photo** — OCR → candidates → pick. The shop-shelf case.
4. **Manual** — the floor. Must exist. Must be fast.

## Repeat check-ins

Explicitly encouraged (R-15). The same beer rated twice, weeks apart, is the
**only** measurement of your own rating noise this project will ever get — and
that number sets the ceiling on model performance. Prompt for it occasionally.

## Open questions

- Is "would you have another right now?" a better target than the 0–10 rating?
  It is more behavioural and less scale-drifty. Genuinely might be. Testable
  once there is data — collect both.
- Should the check-in show the model's prediction *before* you rate? It closes
  a nice feedback loop and makes the app feel alive — but it will anchor the
  rating and contaminate the data. **Current lean: show it after, never before.**
- Is offline logging needed? (Bars have bad signal.) Probably yes: queue locally
  and sync.
