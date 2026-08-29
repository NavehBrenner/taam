# 01 — Vision and Scope

## The problem, honestly stated

Naveh drinks beer. He would like to (a) remember which ones he liked, (b) choose
well from an unfamiliar menu or shelf, and (c) find out what his taste actually
*is*, in terms more useful than "I like IPAs".

Existing tools solve (a) very well and essentially ignore (b) and (c). See
`12-prior-art.md`.

This is a personal project. Success is measured in *understanding gained* and
*enjoyment had*, not in users or revenue. That framing licenses some choices that
would be wrong for a product — over-investing in interpretability,
under-investing in UI, preferring an honest negative result to a plausible demo.

## Vision

> A system that knows my palate well enough to be *useful when I'm standing in
> front of a fridge in a shop in Beer Sheva*, that can explain itself, and that
> learns something true about me from a few dozen beers rather than a few
> thousand.

## Primary use cases, in order of how often they'll actually happen

1. **Shelf pick.** Standing in a shop, 40 unfamiliar bottles, which one?
2. **Menu pick.** A bar list of 8 taps. Rank them for me.
3. **Logging.** I drank this, here's what I thought. Must take <30 seconds.
4. **Recall.** "What was that sour one I loved last spring?"
5. **Self-knowledge.** Show me my palate. Show me how it has moved.
6. **Mood pick.** Same as 1–2, but conditioned on the situation.
7. **Exploration.** Push me somewhere I haven't been but will probably like.

## Non-goals

| Not doing | Why |
|---|---|
| Social / friends / feed | Untappd does this well. Nothing to add. |
| Multi-user | The whole design is N-of-1. Multi-user would change the ML fundamentally. |
| Owning a beer catalog | We borrow data. Maintaining a catalog is a full-time job. |
| Venue / tap-list availability | Genuinely valuable, genuinely out of reach (Untappd gates it behind their business tier). Revisit if a source appears. |
| Brewing / recipes | Different project. |
| Price optimisation | Maybe later. Cheap and good is a real objective. Parked. |

## Explicit scope boundaries

**In scope from day one:** beer; a single user; profiles; ratings; context
logging; the preference model; evaluation.

**In scope by design but not yet built:** whisky; wine; mood conditioning;
photo-to-candidates.

**Out of scope until something changes:** everything in the non-goals table.

## What "done" would look like

There is no done. But there are checkpoints worth naming:

- **Checkpoint 1:** the profiler validates (M0). We can turn an unknown beer into
  a trustworthy vector.
- **Checkpoint 2:** the crossover N is found (M4). We know whether a personal
  model beats style preference, and after how many beers.
- **Checkpoint 3:** the palate readout is something Naveh reads and says "yes,
  that's me" — or "no, and that's interesting".
- **Checkpoint 4:** whisky works without touching the core (M7).

Any one of these failing is a legitimate and interesting outcome.
