# ADR-0001: Public repository, MIT licensed, personal data kept out

- **Status:** Accepted
- **Date:** 2026-08-29
- **Decision register entry:** D-013

## Context

The repo needed a visibility and licensing choice before first push. The
question underneath it was whether open-sourcing forecloses any future
commercial option, and whether personal drinking data makes public risky.

## Evidence

Not experimental evidence — this is a values-and-market judgement, recorded as an
ADR because it is now acted upon and reversing it (un-publishing) is costly.

The market evidence from `docs/12-prior-art.md`: Next Glass shipped a working
personalisation engine and was still pulled toward B2B. The constraint in this
category is catalog coverage and distribution, not the algorithm. Neither of
those lives in a repository, so publishing the algorithm forecloses little.

## Decision

Public repository, MIT licensed.

Personal data never enters the repo: check-ins live in an external DB reached
through `.env` configuration, and `data/` is gitignored.

## Alternatives considered

- **Private.** Protects nothing that is actually scarce; costs the portfolio
  value and the small-but-real chance of being useful to someone else.
- **Public, engine only, UI closed.** A reasonable commercial hedge, but
  architecting a split before there is any UI is speculative. Revisit if a
  product ever appears.
- **Public with a non-commercial licence.** Deters contribution, protects an
  asset that isn't scarce.

## Consequences

**Easier:** portfolio value; other people can use it; no split-brain between a
public and private tree.

**Harder — and these need active care:**

1. **Untappd's terms.** Any scraping code is a visible ToS violation in a public
   repo in a way it is not in a private one. See `docs/13-scraping-policy.md`.
   Scrapers do not go in this repo.
2. **Accidental data commits.** A one-off export written to the repo root would
   be published permanently. A pre-commit guard is needed before logging starts.

## Revisit if

- A real product emerges and the engine/UI split becomes worth making.
- Any source's terms make redistribution of derived data a problem.
