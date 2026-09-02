---
name: issue-walkthrough
description: >
  Produce the research readout for a finished taam issue, before its PR is
  opened: what was asked, what was found, what moved, what failed. Run it after
  `qualety check` / `pytest` / `mypy` pass and BEFORE `gh pr create` — this is a
  required step in taam's workflow (`docs/14-workflow.md`), not an optional
  extra. Also invoke on request: "walk me through it", "what did we find",
  "/issue-walkthrough".
---

# Issue walk-through

taam is a research project wearing a software project's clothes. The PR diff is
an honest record of *what changed* and a terrible record of *what we learned* —
and the second one is the whole point. A file list cannot tell you that the
baseline turned out to be stronger than the model, or that our own measuring
instrument was broken twice.

So: before every PR, hand Naveh the finding, not the diff. Then **stop**, and let
him redirect while redirecting is still free.

## When this runs

```
work done → qualety check / pytest / mypy pass → THIS SKILL → he responds → PR
```

Not after the PR. A walk-through that arrives with the PR is a summary; one that
arrives before it is a decision point.

## What you produce

Two things, same content:

1. **The readout, in the conversation.** This is the deliverable he actually
   reads.
2. **`docs/walkthroughs/NVB-<n>.md`**, committed in the same PR. The terminal
   scrolls away; in a month the reasoning behind a number needs to be findable
   next to the code that produced it. Same argument as `DECISIONS.md`.

The file gets a one-line pointer added to `docs/walkthroughs/README.md`.

## The shape

Eight sections. Skip any that is genuinely empty — say "nothing here" in one
line rather than padding it. Target one screen; two if the numbers earn it.

### 1. The question

What this issue was actually asking, in plain language, as a question — not as a
task title. Why it mattered, and what the answer would change. Someone who has
not read the issue should be able to start here.

> M0 asked: can we turn a beer's name, style, ABV, IBU and description into a
> flavour vector we can trust? If not, everything downstream is arithmetic on
> noise and the project is over.

### 2. What we actually did

The approach in three or four lines. Include what you deliberately did **not**
do and why — the skipped work is usually the more interesting half, and it is
invisible in a diff. Ponytail simplifications, deferred options, roads not taken.

### 3. What we found

**The section everything else exists to support.** The standing rules in
`CLAUDE.md` are not advisory here:

- **Every number carries its baseline.** Global mean, community score, and
  especially style-average of past ratings. A result reported without its
  baseline is not reported.
- **Every number carries its uncertainty.** A point estimate from one split or
  N=20 samples is a rumour. Give the spread, the split count, the interval.
- **State the size, not just the direction.** "Beats the baseline" is nearly
  content-free if the margin is +0.02. Say which it is.
- Tables where the numbers matter, prose where the meaning does.

If the answer is negative or null, that is a *result* — lead with it. Naveh has
said outright he would rather have an honest negative with a clean experiment
than a demo that cannot be defended.

### 4. What surprised us

Anything you did not expect going in. A baseline that was much stronger than
assumed, a correlation that vanished, a dataset that was smaller or cleaner or
weirder than the docs claimed, an assumption in the register that turned out to
be false. If nothing surprised you, say so — that is information too.

### 5. What this moved

The architectural and register delta, explicitly:

- Which `DECISIONS.md` entries had their lean shift, and to what
- Any **new option** discovered (D-nnn option E, etc.) — new options are always
  welcome and must be recorded
- Anything that moved to `DEAD-ENDS.md`, **with the numbers that killed it**
- What changed in the code's structure, not its contents
- Milestones opened or closed in `ROADMAP.md`

And say clearly what did **not** close. The prime directive of this repo is *do
not lock decisions*; a walk-through that reads like a series of settlements is
misreporting.

### 6. What we tried that failed

Dead ends, wrong turns, and bugs in our own instruments. Be specific and
unflattering. Include:

- approaches abandoned, and whether they were **falsified by evidence** or merely
  **argued against** (only the first belongs in `DEAD-ENDS.md`)
- bugs found in the harness, the metric, or the verdict logic — these matter more
  than bugs in the product, because they corrupt every number they touched
- anything that worked but you would not do again

If a previously reported result changed because of a bug found here, say the old
number, the new one, and what the difference was caused by.

### 7. Still open

What this issue did not answer, including questions it *created*. Which ones are
now the cheapest to attack, and which are blocking a milestone.

### 8. Where to push back

**Name your weakest claim.** Not a formality — pick the single thing in the
readout most likely to be wrong, or the interpretation you are least confident
generalises, and say why. If a result rests on an assumption Naveh has not
agreed to, surface it here rather than letting it ride into the next milestone.

Then: the specific decisions that are his to make, stated as questions with your
recommendation attached. If a blocker needs him, follow the exact-CTA format in
his global instructions — the click path, the command, where the output lands.

## How to write it

- Plain language over jargon. He knows the domain; write for someone who has not
  had this issue in their head for an hour.
- Lead with the answer, then support it. Never build up to a conclusion.
- Numbers in tables, meaning in sentences.
- No marketing. "The kill criterion did not fire, but the largest reliable lift
  is +0.042" is the right register. "Great results!" is not.
- Do not recite the diff. No file lists, no "added a function that…". If a code
  detail matters it is because it changed a *finding*.
- Own the mistakes plainly and move on. No self-flagellation, no burying.

## When there is nothing to report

Some issues are plumbing — a CI fix, a rename, a dependency bump. Do not
manufacture insight. Write four lines: what it was, why it was needed, what it
unblocks, nothing found. A short honest walk-through is the correct output, and
padding one trains him to skim them.

## Then stop

Present the readout and **wait**. Do not open the PR in the same turn. He may
want a different framing, an extra experiment, a decision recorded differently,
or the work pointed somewhere else — all of which are cheap now and expensive
after review starts.

Once he responds: fold in his changes, commit the walk-through file with them,
then open the PR.
