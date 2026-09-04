# Walk-throughs

One file per issue, written before its PR is opened. See
`.claude/skills/issue-walkthrough/SKILL.md` for what goes in one and
`docs/14-workflow.md` for where it sits in the workflow.

These exist because a diff records what changed and not what we learned, and in
this project the second one is the point. If you want to know why a number is
what it is, or what we abandoned to get it, start here rather than in the commit
log.

| Issue | What it asked | Short answer |
|---|---|---|
| [NVB-76](NVB-76.md) | Can we profile a beer from its text and numbers well enough to trust? | Yes, but barely — style-average alone is worth r = 0.53–0.84 and text adds ~+0.03 |
| [NVB-96](NVB-96.md) | Can the profiler tell two beers of the *same style* apart? | Barely — same-style pair accuracy 0.608 on Bitter, 0.566 on Hoppy, ~chance elsewhere |
