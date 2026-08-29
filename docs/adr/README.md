# Architecture Decision Records

## Purpose

An ADR is how a decision **leaves** `DECISIONS.md`. Until a decision has an
accepted ADR here, it is open, and all its alternatives remain live.

## Accepted ADRs

- [ADR-0001](0001-public-repo-mit-license.md) — public repo, MIT licensed,
  personal data kept out. *(D-013)*

Everything else remains open. That is deliberate — see `CONTEXT.md`, ground
rule 1.

## When to write one

Write an ADR when *evidence* (not reasoning, not preference) has settled a
question, and reversing it would now cost real work. Until then, update the
"current lean" in `DECISIONS.md` instead.

An ADR does not delete the alternatives. It records which one was chosen, on what
evidence, and — importantly — **what would make us revisit it**.

## Template

```markdown
# ADR-000N: <title>

- **Status:** Proposed | Accepted | Superseded by ADR-000M
- **Date:**
- **Decision register entry:** D-0XX

## Context
What question, and why it now needs answering.

## Evidence
The numbers. An ADR without evidence is a preference, not a decision.

## Decision
What we're doing.

## Alternatives considered
Each one, with why it lost. Never deleted.

## Consequences
What this makes easy. What this makes hard.

## Revisit if
The observation that would reopen this.
```

## Status vocabulary

- **Proposed** — written up, not agreed. Decision stays open.
- **Accepted** — decided. Register entry updated to point here.
- **Superseded** — replaced by a later ADR, which must say why. Never deleted.
