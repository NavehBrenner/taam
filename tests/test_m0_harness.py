"""Controls for the M0 validation harness.

The M0 experiment is allowed to kill the project (ROADMAP.md M0). So before
trusting its verdict, the harness itself has to be shown to work in both
directions. These two tests are that proof.

    python tests/test_m0_harness.py        # or: pytest tests/

Positive control: synthetic data whose descriptions carry a real signal.
                  The harness MUST detect it.
Negative control: the same data with the description/style links broken.
                  The harness MUST fire the kill criterion.

The negative control matters more. A harness that never says "stop" is not a
falsification experiment, it is a rubber stamp — and the first version of this
one had exactly that bug: on pure noise, ridge beat the style-average baseline
on 4 of 11 axes by chance, because both were near zero. That is why the verdict
now requires an absolute r bar and not merely a win over the baseline.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys

import numpy as np
from sklearn.model_selection import train_test_split

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load_m0():
    spec = importlib.util.spec_from_file_location(
        "m0", ROOT / "scripts" / "m0_profiler_validation.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run(df, m0):
    tr, te = train_test_split(df, test_size=200, random_state=0)
    truth = te[m0.CANDIDATE_AXES].to_numpy()
    scores = {name: m0.per_axis_r(truth, np.asarray(fn(tr, te), dtype=float))
              for name, fn in m0.METHODS.items()}
    return scores, m0.report(scores)


def test_positive_control():
    """Real signal in the descriptions -> harness must find it."""
    m0 = _load_m0()
    scores, rc = _run(m0.make_synthetic(seed=1), m0)
    assert rc == 0, "kill criterion fired on data with a known signal"
    for axis in m0.HEADLINE_AXES:
        assert scores["text+numerics"][axis] > scores["style-average"][axis], axis


def test_negative_control():
    """No signal anywhere -> harness must refuse to endorse it."""
    m0 = _load_m0()
    rng = np.random.default_rng(7)
    df = m0.make_synthetic(seed=1)
    df["Description"] = rng.permutation(df["Description"].to_numpy())
    df[m0.STYLE_COL] = rng.permutation(df[m0.STYLE_COL].to_numpy())
    _, rc = _run(df, m0)
    assert rc == 1, "kill criterion did NOT fire on pure noise"


if __name__ == "__main__":
    failures = 0
    for name, fn in [("positive", test_positive_control),
                     ("negative", test_negative_control)]:
        try:
            fn()
            print(f"\n{name} control: PASS")
        except AssertionError as exc:
            failures += 1
            print(f"\n{name} control: FAIL — {exc}")
    sys.exit(1 if failures else 0)
