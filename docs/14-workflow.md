# 14 — Working on this repo

How changes get in. Short, because the rules are short.

## Every change starts as a Linear issue

Project: [taam · טעם](https://linear.app/naveh-brenner/project/taam-%D7%98%D7%A2%D7%9D-dbb61e29912b),
team `NVB`.

1. **File the issue first.** If there is no issue, there is no work. This
   includes "small" changes — the register in `DECISIONS.md` and the issue list
   are the two places that remember why something happened.
2. **Branch off the issue.** Linear generates the branch name (`gitBranchName`
   on the issue, e.g. `navegerc/nvb-92-…`); use it verbatim so Linear links the
   branch, the PR, and the issue by itself.
3. **Walk it through, then stop.** See below. The PR does not get opened until
   Naveh has read the finding and responded.
4. **Open a PR.** Every PR body links its issue.
5. **Naveh merges.** Nobody and nothing else does — not an agent, not a bot.

`main` is protected: no direct pushes, PR required. If a push to `main` is
rejected, that is the rule working, not a misconfiguration.

Use `git switch` (and `git switch -c`), not `git checkout`. `checkout` overloads
branch-switching with file-restoring, and the failure mode of the second is
losing uncommitted work.

## The walk-through

**Required before every PR.** `.claude/skills/issue-walkthrough/SKILL.md`; the
output lands in `docs/walkthroughs/NVB-<n>.md` and is committed with the work.

```
work done → qualety check / pytest / mypy pass → walk-through → Naveh responds → PR
```

This project is research, and a PR diff is an honest record of what changed and
a useless record of what we learned. The walk-through carries the second: what
the issue actually asked, what we found *with its baseline and its uncertainty*,
what moved in `DECISIONS.md`, what we tried that failed — including bugs found in
our own instruments, which matter more than bugs in the product because they
corrupt every number they touched.

Two rules make it work rather than become a formality:

- **It comes before the PR, not with it.** A readout that arrives alongside a PR
  is a summary. One that arrives before it is a decision point, and redirecting
  is free at that moment and expensive after review starts.
- **It names its own weakest claim.** Every walk-through ends by pointing at the
  thing most likely to be wrong. A walk-through with nothing to push back on is
  not finished being written.

Plumbing issues get a four-line walk-through saying nothing was found. That is
the correct output; padding one teaches Naveh to skim them.

## Checks

Three, all run in CI on every PR (`.github/workflows/ci.yml`), all runnable at a
desk:

```bash
qualety check    # ruff + qualety's python/* rules
pytest
mypy
```

### qualety

[qualety](https://github.com/NavehBrenner/qualety) enforces the structural rules
a linter cannot: annotations on public callables, no bare/silent `except`, no
mutable defaults, no `sys.path` hacks, public exports referenced from tests. It
also runs Ruff, so it is the only lint entry point — do not add a second one.

Config is `qualety.config.json`. Note that qualety generates its own
`.qualety/ruff.toml` and does **not** read `[tool.ruff]` from `pyproject.toml`;
that section survives only for anyone running `ruff` directly.

It installs from PyPI and is **pinned exactly** in `requirements-dev.txt`
(`qualety==0.1.3`). Pinned rather than floating because a new qualety version
is a new set of enforced rules, and that should arrive in a PR you can read,
not on a Tuesday because CI reinstalled. Bump it deliberately.

**Currently disabled:** `python/no-unnecessary-def`. It counts call sites
statically, and the M0 harness is a standalone script that `tests/` loads via
`importlib.util.spec_from_file_location` — so the rule cannot see the test's
calls and reports tested functions as unused, with a suggestion to delete them.
Filed upstream as
[qualety#100](https://github.com/NavehBrenner/qualety/issues/100); re-enable
when it lands. (Its sibling false positive, registry-dict references, was
[#86](https://github.com/NavehBrenner/qualety/issues/86) and is fixed in
0.1.3.)

qualety has no inline suppression (`# noqa`-style), so one false positive costs
the rule repo-wide. That is why the disable is a whole rule and not one line,
and it is raised in #100.

## The plugin reflex

**When a code change is requested, ask whether the rule behind it can be
executed instead of remembered.**

If Naveh asks for a change, and the same mistake could be made again next week
by a different session, the change is only half the fix. The other half is a
qualety rule. Instructions in `CLAUDE.md` are not enforced; a rule in CI is.

The reflex, in order:

1. Make the requested change.
2. Ask: is this an instance of a class, or a one-off? A one-off stops here.
3. Is the class statically detectable from the AST? If not, it stops here too —
   write it into `CLAUDE.md` and accept that it is advisory.
4. If it is detectable, **file an issue on
   [NavehBrenner/qualety](https://github.com/NavehBrenner/qualety/issues)** —
   upstream, on the repo, not in Linear. That is where qualety's work is
   tracked and where the fix will be written. Quote the taam code that
   motivated it, so the rule has a real example behind it.

This repo has invariants that are good candidates and are not yet rules — for
instance `CLAUDE.md` rule 6, "nothing domain-specific goes in `preference/` or
`recommend/`", which is a substring check over an import/identifier set and is
exactly the kind of architectural fitness function qualety exists for.

The reflex runs the other way too. If qualety flags code that is actually
correct, do **not** contort the code to please it — file the false positive
**upstream on the qualety repo** and disable the rule with a pointer to that
issue, as above.

Both directions land in the same place: **qualety issues go to
`gh issue create -R NavehBrenner/qualety`, never to a Linear issue in this
project.** A Linear issue here is invisible to whoever fixes qualety, and taam's
own Linear board is for taam's work.
