#!/usr/bin/env python3
"""M0 — Profiler validation. The falsification experiment.

See ROADMAP.md M0 and docs/06-profiler.md. This is the first thing to run and it
is designed to be able to KILL the project in a day, which is the most valuable
thing it can do.

Question
--------
Can we turn (name, brewery, style, ABV, IBU, description) into a trustworthy
flavour-descriptor vector?

Method
------
Hold out beers from the Kaggle "Beer Profile and Ratings" set (which ships
labelled descriptor columns), predict their descriptors three ways, and score
each against the labels with per-axis Pearson r, averaged over 20 splits:

  1. style-average  — the mean descriptor vector of that beer's style.
                      THE BASELINE THAT MATTERS. Uses no text at all.
  2. numerics-only  — ridge on ABV / IBU / colour + style one-hot.
  3. text+numerics  — ridge on TF-IDF(description) plus the above.

An LLM profiler is deliberately NOT run here: it costs money, needs network, and
is only worth evaluating once we know what the cheap deterministic methods
achieve. Add it as a fourth column later (see --help).

Interpretation
--------------
  r > 0.7 on bitter / sweet / body            good, proceed
  an axis < 0.4                               drop it from the vocabulary (D-001)
  lift not positive on every split            not reliable; style already told us
  nothing beats style-average                 KILL CRITERION — the "profile" is a
                                              laundered style label; re-open
                                              D-001 / D-002

Usage
-----
    python scripts/m0_profiler_validation.py --data data/raw/beer_profile_and_ratings.csv

    # sanity-check the harness itself with synthetic data (no download needed):
    python scripts/m0_profiler_validation.py --self-test

Get the data
------------
    https://www.kaggle.com/datasets/ruthgn/beer-profile-and-ratings-data-set
    -> data/raw/beer_profile_and_ratings.csv   (gitignored)
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable

import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler

SEED = 0

# D-001, initialised from the Kaggle vocabulary. Anything that fails validation
# here should be dropped from the vocabulary rather than carried along.
CANDIDATE_AXES = [
    "Astringency", "Body", "Alcohol", "Bitter", "Sweet", "Sour",
    "Salty", "Fruits", "Hoppy", "Spices", "Malty",
]
# The three we care most about; the success criterion is stated on these.
HEADLINE_AXES = ["Bitter", "Sweet", "Body"]

NUMERIC_COLS = ["ABV", "Min IBU", "Max IBU"]
TEXT_COLS = ["Description"]
STYLE_COL = "Style"


# ----------------------------------------------------------------------------
# data
# ----------------------------------------------------------------------------

def load(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = [c for c in CANDIDATE_AXES if c not in df.columns]
    if missing:
        sys.exit(
            f"Expected descriptor columns not found: {missing}\n"
            f"Columns present: {list(df.columns)}\n"
            "If the dataset schema changed, update CANDIDATE_AXES."
        )
    for c in NUMERIC_COLS + TEXT_COLS + [STYLE_COL]:
        if c not in df.columns:
            df[c] = np.nan
    df[TEXT_COLS] = df[TEXT_COLS].fillna("")
    return df


def description_body(desc: pd.Series) -> pd.Series:
    """The description with the boilerplate `Notes:` prefix removed.

    Every description in the Kaggle set starts with the literal string
    `Notes:`. For 1347 of 3197 beers -- 42% -- that is the ENTIRE field: there
    is no description, only the prefix. A naive empty-string check passes them,
    which is how they went unnoticed in the first M0 run and diluted the
    measured text lift across two beers in five that had nothing to say.
    """
    return (desc.fillna("").str.replace("Notes:", "", regex=False)
            .str.replace("\\t", " ", regex=False).str.strip())


def has_description(df: pd.DataFrame) -> pd.Series:
    """True where the description contains at least one word of actual text.

    The split is clean rather than arbitrary: 1850 beers have >= 1 word, 1347
    have exactly zero. There is no judgement call at the boundary.
    """
    return description_body(df["Description"]).str.split().str.len() > 0


def make_synthetic(n: int = 1200, seed: int = SEED) -> pd.DataFrame:
    """Synthetic data with a KNOWN structure, to prove the harness works.

    Descriptors are built as: style effect + a real text signal + noise.
    A correct harness must therefore show text+numerics beating style-average.
    If the self-test fails, the harness is broken, not the beer.
    """
    rng = np.random.default_rng(seed)
    styles = [f"Style {i}" for i in range(12)]
    words = ["hoppy", "roasted", "citrus", "caramel", "tart", "smooth",
             "crisp", "resinous", "biscuit", "funky"]

    style_effect = {s: rng.normal(0, 1, len(CANDIDATE_AXES)) for s in styles}
    word_effect = {w: rng.normal(0, 1, len(CANDIDATE_AXES)) for w in words}

    rows = []
    for _ in range(n):
        s = rng.choice(styles)
        picked = list(rng.choice(words, size=rng.integers(2, 5), replace=False))
        vec = style_effect[s] + sum(word_effect[w] for w in picked)
        vec = vec + rng.normal(0, 0.8, len(CANDIDATE_AXES))
        abv = float(rng.uniform(3, 12))
        row = {
            "Name": "synthetic", STYLE_COL: s,
            "Description": " ".join(picked) + " beer with a long finish",
            "ABV": abv, "Min IBU": abv * 3 + rng.normal(0, 5),
            "Max IBU": abv * 5 + rng.normal(0, 5),
        }
        row.update(dict(zip(CANDIDATE_AXES, vec, strict=True)))
        rows.append(row)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# the three profilers
# ----------------------------------------------------------------------------

def predict_style_average(tr: pd.DataFrame, te: pd.DataFrame) -> np.ndarray:
    """THE baseline. No text, no model — just 'what does this style taste like'."""
    means = tr.groupby(STYLE_COL)[CANDIDATE_AXES].mean()
    overall = tr[CANDIDATE_AXES].mean()
    return np.vstack([
        means.loc[s].to_numpy() if s in means.index else overall.to_numpy()
        for s in te[STYLE_COL]
    ])


def _numeric_block(tr: pd.DataFrame, te: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    num_tr = tr[NUMERIC_COLS].astype(float)
    num_te = te[NUMERIC_COLS].astype(float)
    med = num_tr.median()
    num_tr, num_te = num_tr.fillna(med), num_te.fillna(med)
    sc = StandardScaler().fit(num_tr)

    oh = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    oh.fit(tr[[STYLE_COL]].astype(str))
    return (
        np.hstack([sc.transform(num_tr), oh.transform(tr[[STYLE_COL]].astype(str))]),
        np.hstack([sc.transform(num_te), oh.transform(te[[STYLE_COL]].astype(str))]),
    )


def _ridge(Xtr: np.ndarray, ytr: np.ndarray, Xte: np.ndarray) -> np.ndarray:
    model = RidgeCV(alphas=np.logspace(-2, 4, 25))
    model.fit(Xtr, ytr)
    return model.predict(Xte)


def predict_numerics_only(tr: pd.DataFrame, te: pd.DataFrame) -> np.ndarray:
    Xtr, Xte = _numeric_block(tr, te)
    return _ridge(Xtr, tr[CANDIDATE_AXES].to_numpy(), Xte)


def predict_text_and_numerics(tr: pd.DataFrame, te: pd.DataFrame) -> np.ndarray:
    """The candidate profiler: TF-IDF over the description + hard numerics.

    TF-IDF rather than sentence embeddings on purpose: no model download, fully
    deterministic, and at ~3k rows it is a fair fight. If this beats the
    baseline, swapping in a sentence encoder is a tuning step, not a rescue.
    """
    Xn_tr, Xn_te = _numeric_block(tr, te)
    vec = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), min_df=2,
                          stop_words="english", sublinear_tf=True)
    Xt_tr = vec.fit_transform(tr["Description"]).toarray()
    Xt_te = vec.transform(te["Description"]).toarray()
    return _ridge(np.hstack([Xn_tr, Xt_tr]), tr[CANDIDATE_AXES].to_numpy(),
                  np.hstack([Xn_te, Xt_te]))


METHODS = {
    "style-average": predict_style_average,
    "numerics-only": predict_numerics_only,
    "text+numerics": predict_text_and_numerics,
}


# ----------------------------------------------------------------------------
# scoring and report
# ----------------------------------------------------------------------------


def per_axis_r(truth: np.ndarray, pred: np.ndarray) -> dict[str, float]:
    """Correlation. Asks whether the ranking is right, ignoring scale."""
    out = {}
    for i, axis in enumerate(CANDIDATE_AXES):
        t, p = truth[:, i], pred[:, i]
        out[axis] = float("nan") if np.std(p) < 1e-12 else pearsonr(t, p)[0]
    return out


def per_axis_r2(truth: np.ndarray, pred: np.ndarray) -> dict[str, float]:
    """Variance explained on the holdout. Asks whether the NUMBERS are right.

    Reported alongside r because the two come apart out of sample: r is
    invariant to any affine transform of the prediction, R^2 is not. A model
    with the right shape at the wrong scale scores r ~ 1 and R^2 < 0, and only
    R^2 notices. (On this data they happen to agree to ~0.01, because both
    predictors are near-calibrated -- but that is a measured fact, not a
    property of the metric, so both get printed.)

    r also compresses near the top of its range, which makes a real gain look
    small: +0.042 r on Bitter is +0.066 R^2, i.e. a sixth of the variance the
    baseline left unexplained. Reporting only r invites underselling.
    """
    out = {}
    for i, axis in enumerate(CANDIDATE_AXES):
        t, p = truth[:, i], pred[:, i]
        ss_tot = float(np.sum((t - t.mean()) ** 2))
        out[axis] = (float("nan") if ss_tot < 1e-12
                     else 1.0 - float(np.sum((t - p) ** 2)) / ss_tot)
    return out


METRICS = {"r": per_axis_r, "r2": per_axis_r2}

Scores = dict[str, dict[str, dict[str, list[float]]]]  # metric -> method -> axis


def run_splits(df: pd.DataFrame, holdout: int, seeds: Iterable[int]) -> Scores:
    """Score every method on every split, on every metric. One split is not a
    measurement."""
    scores: Scores = {m: {n: {} for n in METHODS} for m in METRICS}
    for seed in seeds:
        tr, te = train_test_split(df, test_size=holdout, random_state=seed)
        truth = te[CANDIDATE_AXES].to_numpy()
        for name, fn in METHODS.items():
            pred = np.asarray(fn(tr, te), dtype=float)
            for metric, score in METRICS.items():
                for axis, v in score(truth, pred).items():
                    scores[metric][name].setdefault(axis, []).append(v)
    return scores


def _series(scores: Scores, method: str, axis: str,
            metric: str = "r") -> np.ndarray:
    return np.asarray(scores[metric][method][axis], dtype=float)


def _best_model(scores: Scores, axis: str) -> str:
    """Whichever model method has the higher mean r on this axis.

    Picked once per axis rather than per split: taking the per-split maximum
    would let noise choose the winner and bias every lift upwards.
    """
    return max(("numerics-only", "text+numerics"),
               key=lambda m: np.nanmean(_series(scores, m, axis)))


def report(scores: Scores) -> int:
    width = max(len(a) for a in CANDIDATE_AXES) + 2
    names = list(METHODS)
    n_splits = len(next(iter(scores["r"]["style-average"].values())))

    print(f"\nPer-axis Pearson r against held-out labels "
          f"(mean +/- sd over {n_splits} splits)")
    print("-" * (width + 18 * len(names)))
    print("axis".ljust(width) + "".join(n.rjust(18) for n in names))
    print("-" * (width + 18 * len(names)))
    for axis in CANDIDATE_AXES:
        row = axis.ljust(width)
        for n in names:
            v = _series(scores, n, axis)
            cell = ("     n/a" if np.all(np.isnan(v))
                    else f"{np.nanmean(v):6.3f}+-{np.nanstd(v):.3f}")
            row += cell.rjust(18)
        print(row)
    print("-" * (width + 18 * len(names)))

    # An axis "works" only if it is BOTH usefully predictive in absolute terms
    # AND beats the no-text baseline reliably. Relative improvement on ONE split
    # is not enough: on pure noise ridge beats style-average on some axes by
    # chance, and even on real data a single split moved the verdict by three
    # axes. The reliability bar is a sign test -- the lift must be positive on
    # EVERY split. On noise that is p ~ 2e-6 per axis, so the kill criterion
    # still fires; MARGIN is now a materiality label, not a pass/fail gate.
    USEFUL_R = 0.40
    MARGIN = 0.05

    print("\nLift of the better model over style-average, per split")
    print(f"{'axis'.ljust(width)}{'d r':>8}{'d R2':>8}"
          f"{'R2 base -> model':>20}{'resid killed':>14}{'positive':>11}")
    print("-" * (width + 61))
    lifts, wins, chosen = {}, {}, {}
    for axis in CANDIDATE_AXES:
        m = _best_model(scores, axis)
        d = _series(scores, m, axis) - _series(scores, "style-average", axis)
        b2 = _series(scores, "style-average", axis, "r2")
        m2 = _series(scores, m, axis, "r2")
        chosen[axis], lifts[axis] = m, d
        wins[axis] = int(np.sum(d > 0))
        # share of the variance the baseline left unexplained that the model
        # then explains. Flatters a strong baseline (small denominator), so it
        # is printed next to the neutral dR2 rather than instead of it.
        resid = float(np.nanmean((m2 - b2) / (1.0 - b2)))
        print(f"{axis.ljust(width)}{np.nanmean(d):+8.3f}"
              f"{np.nanmean(m2 - b2):+8.3f}"
              f"{np.nanmean(b2):11.3f} ->{np.nanmean(m2):6.3f}"
              f"{resid * 100:13.1f}%{wins[axis]:8d}/{n_splits}")
    print("-" * (width + 61))
    print("d r compresses near the top of its range; d R2 does not. Read both.")

    def mean_r(axis: str) -> float:
        return float(np.nanmean(_series(scores, chosen[axis], axis)))

    def reliable(axis: str) -> bool:
        return wins[axis] == n_splits and not np.isnan(mean_r(axis))

    working = [a for a in CANDIDATE_AXES if reliable(a) and mean_r(a) >= USEFUL_R]
    material = [a for a in working if float(np.nanmean(lifts[a])) >= MARGIN]
    weak = [a for a in CANDIDATE_AXES
            if not np.isnan(mean_r(a)) and mean_r(a) < USEFUL_R]
    no_lift = [a for a in CANDIDATE_AXES
               if a not in working and a not in weak and not np.isnan(mean_r(a))]
    headline_ok = [a for a in HEADLINE_AXES if mean_r(a) > 0.7]

    print("\nVERDICT")
    print("=" * 62)
    print(f"criterion: an axis works if mean r >= {USEFUL_R} AND its lift over")
    print(f"style-average is positive on all {n_splits} splits\n")

    if not working:
        print("*** KILL CRITERION HIT ***\n")
        if weak and not no_lift:
            print("No axis is usefully predictable from text or numerics at all")
            print(f"(every axis below r={USEFUL_R}). Either the descriptions carry")
            print("no signal, or the labels do not mean what we assumed.")
        else:
            print("No axis beats the style-average baseline reliably.")
            print("The 'profile' is a laundered style label: everything it knows,")
            print("the style already told us.")
        print("\nThe content-based premise is in trouble. Re-open D-001/D-002,")
        print("and consider that the honest project may be style-based.")
        print("Log this in DEAD-ENDS.md WITH THIS TABLE.")
        return 1

    print(f"RELIABLE LIFT on {len(working)}/{len(CANDIDATE_AXES)} axes:")
    print("  " + ", ".join(working))
    print(f"\n  ...of which the lift is also material (>= {MARGIN} r): "
          f"{', '.join(material) if material else 'NONE'}")
    if not material:
        print("  -> small on the r scale. Check the d R2 column before calling it")
        print("     negligible: the same lift can be a tenth of the residual")
        print("     variance, which is not nothing.")
    print(f"\nHeadline axes over r=0.7: "
          f"{', '.join(headline_ok) if headline_ok else 'NONE'} "
          f"(of {', '.join(HEADLINE_AXES)})")
    if not headline_ok:
        print("  -> weaker than hoped. Proceed, but expect a low ceiling in M4.")
    if no_lift:
        print("\nPredictable, but style already told us "
              "(no reliable lift over baseline):\n  " + ", ".join(no_lift))
    if weak:
        print(f"\nBelow r={USEFUL_R} - DROP these from the vocabulary (D-001):")
        print("  " + ", ".join(weak))

    print("\nNext: record this table in docs/06-profiler.md, update D-001 with")
    print(f"the surviving axis list ({len(working) + len(no_lift)} axes), and")
    print("move to M1 (profile-space structure).")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", help="path to beer_profile_and_ratings.csv")
    ap.add_argument("--self-test", action="store_true",
                    help="run on synthetic data with known structure")
    ap.add_argument("--holdout", type=int, default=400)
    ap.add_argument("--seed", type=int, default=SEED, help="first split seed")
    ap.add_argument("--seeds", type=int, default=20,
                    help="number of train/holdout splits to average over")
    ap.add_argument("--text-only", action="store_true",
                    help="drop the 42%% of beers whose description is the bare "
                         "`Notes:` prefix, and measure the text lift on beers "
                         "that actually have text")
    args = ap.parse_args()

    if args.self_test:
        print("SELF-TEST: synthetic data with a known text signal.")
        print("A working harness MUST show text+numerics beating style-average.\n")
        df = make_synthetic(seed=args.seed)
    elif args.data:
        df = load(args.data)
        real = int(has_description(df).sum())
        print(f"Loaded {len(df)} beers from {args.data}")
        print(f"  {real} have a description; {len(df) - real} "
              f"({(len(df) - real) / len(df):.0%}) are the bare `Notes:` prefix")
        if args.text_only:
            df = df[has_description(df)].copy()
            print(f"  --text-only: keeping the {len(df)} with text. The text path "
                  f"is dead weight on the rest,\n  so the full-set lift understates "
                  f"what a description is worth when there is one.")
    else:
        ap.error("pass --data <csv> or --self-test")

    seeds = range(args.seed, args.seed + args.seeds)
    print(f"holdout={args.holdout}  splits={args.seeds}  seeds={seeds.start}..{seeds.stop - 1}")
    scores = run_splits(df, args.holdout, seeds)

    rc = report(scores)
    if args.self_test:
        bit = (_series(scores, "text+numerics", "Bitter")
               - _series(scores, "style-average", "Bitter"))
        ok = bool(np.all(bit > 0))
        print(f"\nself-test {'PASSED' if ok else 'FAILED'} — harness "
              f"{'detects' if ok else 'CANNOT DETECT'} a known text signal.")
        return 0 if ok else 2
    return rc


if __name__ == "__main__":
    sys.exit(main())
