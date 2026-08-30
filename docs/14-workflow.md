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
3. **Open a PR.** Every PR body links its issue.
4. **Naveh merges.** Nobody and nothing else does — not an agent, not a bot.

`main` is protected: no direct pushes, PR required. If a push to `main` is
rejected, that is the rule working, not a misconfiguration.

Use `git switch` (and `git switch -c`), not `git checkout`. `checkout` overloads
branch-switching with file-restoring, and the failure mode of the second is
losing uncommitted work.

## Checks

Three, all run in CI on every PR (`.github/workflows/ci.yml`), all runnable at a
desk:

```bash
./scripts/qualety.sh    # code quality: ruff + qualety's python/* rules
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

qualety is not published to npm or PyPI yet, so `scripts/qualety.sh` builds a
**pinned commit** from source into `.tools/` on first run and caches it. To move
the pin, change `PIN` in that script and let CI rebuild.

**Currently disabled:** `python/no-unnecessary-def`, because it treats a
function referenced from a registry dict (`METHODS = {"style-average":
predict_style_average, …}` in the M0 harness) as never called, and tells you to
delete it. Those functions are the experiment's baseline and candidates.
Filed upstream as
[qualety#86](https://github.com/NavehBrenner/qualety/issues/86) (NVB-93);
re-enable when it lands.

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
4. If it is detectable, file a `code-invariants` issue for the rule. Reference
   the taam change that motivated it, so the rule has a real example behind it.

This repo has invariants that are good candidates and are not yet rules — for
instance `CLAUDE.md` rule 6, "nothing domain-specific goes in `preference/` or
`recommend/`", which is a substring check over an import/identifier set and is
exactly the kind of architectural fitness function qualety exists for.

The reflex runs the other way too. If qualety flags code that is actually
correct, do **not** contort the code to please it — file the false positive
against qualety and disable the rule with a pointer, as above.
