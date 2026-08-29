# 04 — Data Model

Sketch, not a migration. Everything here is provisional — see D-015 especially,
which is the one that is painful to change later.

## Entities

```
Domain ──< Item ──< Profile
                └──< CheckIn ──< CheckInAnswer
                                 CheckInContext
Palate (per domain, versioned snapshots)
```

## `item`

| column | type | notes |
|---|---|---|
| `id` | uuid | internal |
| `domain` | text | `beer` / `whisky` / `wine` |
| `name` | text | as displayed |
| `maker` | text | brewery / distillery / winery |
| `identity_key` | text | normalised dedup key — **see D-015** |
| `style` | text | domain taxonomy, free-ish |
| `abv` | real | nullable |
| `ibu` | real | beer only, nullable |
| `srm` | real | beer only, nullable |
| `description` | text | the profiler's main input |
| `ingredients` | text | nullable, often absent |
| `vintage` | int | nullable — matters for wine/whisky, rarely for beer |
| `community_score` | real | normalised 0–1; feeds the `α` term |
| `community_n` | int | how many ratings back that score — **needed**, a 4.5 from 6 raters is not a 4.5 from 6000 |
| `source` | text | which catalog it came from |
| `source_id` | text | id in that source |
| `retrieved_at` | timestamp | |

Open: `style` as free text vs. a controlled vocabulary. Free text is honest about
messy sources; a controlled vocabulary is needed for the style-average baseline
in `10-evaluation.md`. Probably both — raw plus a mapped column.

## `profile`

One row per (item, profiler). Multiple profiles per item are **allowed and
wanted** — that is how cross-source calibration gets measured.

| column | type | notes |
|---|---|---|
| `item_id` | uuid | |
| `axes` | json | `{"bitter": 6.5, "sweet": 2.0, ...}` — named, not positional, so vocabulary changes don't silently corrupt old rows |
| `profiler` | text | `regressor` / `llm` / `manual` / `dataset` |
| `profiler_version` | text | **required** — model id + prompt hash, or code version |
| `confidence` | json | nullable; per-axis spread from an ensemble |
| `created_at` | timestamp | |

Storing axes as a name→value map rather than a fixed array is deliberate: the
vocabulary (D-001) is expected to change, and positional arrays fail silently
when it does.

## `checkin`

| column | type | notes |
|---|---|---|
| `id` | uuid | |
| `item_id` | uuid | |
| `at` | timestamp | when drunk, not when logged |
| `logged_at` | timestamp | so retroactive entries are visible as such |
| `rating` | real | scale per D-010 |
| `notes` | text | free text, optional, possibly mined later |

Repeat check-ins of the same item are kept as separate rows. This is the only
data that will ever measure your own rating noise, and that number sets the
ceiling on model performance — see `10-evaluation.md`.

## `checkin_answer`

| column | notes |
|---|---|
| `checkin_id` | |
| `question_id` | stable id, so the question bank can evolve |
| `question_version` | reworded questions are not the same question |
| `answer` | json |

## `checkin_context`

Free-form tags plus a few structured fields. Written at check-in time
**regardless of whether anything consumes them yet** (R-12).

| column | notes |
|---|---|
| `checkin_id` | |
| `tags` | json array — `["with-food", "burger", "friends", "outdoors"]` |
| `time_of_day` | derived |
| `temperature_c` | nullable; auto-filled if easy |
| `intent` | nullable — `explore` / `safe` / `strong` / `refresh` |

Open: fixed tag vocabulary vs. free tags. Free tags collect more, structure
less. A hybrid (suggested chips + free entry) is the obvious compromise and
nobody has argued against it yet.

## `palate`

Versioned snapshots rather than one mutable row, so the trajectory (R-26) is
free and so a bad model version can be diagnosed after the fact.

| column | notes |
|---|---|
| `id` | |
| `domain` | |
| `fitted_at` | |
| `n_checkins` | the N this was fitted at — needed for every evaluation plot |
| `alpha` | community weight |
| `weights` | json, axis → weight |
| `weight_sd` | json, axis → posterior sd |
| `mood_offsets` | json, mood → offset vector; empty until M6 |
| `model_version` | |

## Things not modelled yet, deliberately

- **Price.** Cheap-and-good is a real objective and this is a real gap. Parked
  because prices are per-shop and volatile.
- **Serving format / freshness / glassware.** Real sources of rating variance.
  Could be context tags if it ever seems worth it.
- **Availability.** Out of scope (see `01-vision-and-scope.md`), but if a source
  ever appears this is where it would attach.
- **Photos.** Will be needed for the shelf-pick path. Storage strategy undecided.
