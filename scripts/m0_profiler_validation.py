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
each against the labels with per-axis Pearson r:

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
        row.update(dict(zip(CANDIDATE_AXES, vec)))
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


def _numeric_block(tr, te):
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


def _ridge(Xtr, ytr, Xte):
    model = RidgeCV(alphas=np.logspace(-2, 4, 25))
    model.fit(Xtr, ytr)
    return model.predict(Xte)


def predict_numerics_only(tr, te):
    Xtr, Xte = _numeric_block(tr, te)
    return _ridge(Xtr, tr[CANDIDATE_AXES].to_numpy(), Xte)


def predict_text_and_numerics(tr, te):
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
    out = {}
    for i, axis in enumerate(CANDIDATE_AXES):
        t, p = truth[:, i], pred[:, i]
        out[axis] = float("nan") if np.std(p) < 1e-12 else pearsonr(t, p)[0]
    return out


def report(scores: dict[str, dict[str, float]]) -> int:
    width = max(len(a) for a in CANDIDATE_AXES) + 2
    names = list(METHODS)

    print("\nPer-axis Pearson r against held-out labels")
    print("-" * (width + 16 * len(names)))
    print("axis".ljust(width) + "".join(n.rjust(16) for n in names))
    print("-" * (width + 16 * len(names)))
    for axis in CANDIDATE_AXES:
        row = axis.ljust(width)
        best = max((scores[n][axis] for n in names if not np.isnan(scores[n][axis])),
                   default=float("nan"))
        for n in names:
            v = scores[n][axis]
            cell = "   n/a" if np.isnan(v) else f"{v:6.3f}"
            if not np.isnan(v) and abs(v - best) < 1e-9:
                cell += " *"
            row += cell.rjust(16)
        print(row)
    print("-" * (width + 16 * len(names)))
    print("* = best method for that axis\n")

    base = scores["style-average"]
    best_model = {a: max(scores["numerics-only"][a], scores["text+numerics"][a])
                  for a in CANDIDATE_AXES}

    # An axis "works" only if it is BOTH usefully predictive in absolute terms
    # AND better than the no-text baseline. Relative improvement alone is not
    # enough: on pure noise, ridge beats style-average on some axes by chance,
    # and both are near zero. USEFUL_R is the absolute bar.
    USEFUL_R = 0.40
    MARGIN = 0.05

    def ok(a):
        return (not np.isnan(best_model[a])
                and best_model[a] >= USEFUL_R
                and best_model[a] > base[a] + MARGIN)

    working = [a for a in CANDIDATE_AXES if ok(a)]
    weak = [a for a in CANDIDATE_AXES
            if not np.isnan(best_model[a]) and best_model[a] < USEFUL_R]
    no_lift = [a for a in CANDIDATE_AXES
               if not np.isnan(best_model[a])
               and best_model[a] >= USEFUL_R
               and best_model[a] <= base[a] + MARGIN]
    headline_ok = [a for a in HEADLINE_AXES if best_model.get(a, 0) > 0.7]

    print("VERDICT")
    print("=" * 62)
    print(f"criterion: an axis works if r >= {USEFUL_R} AND beats "
          f"style-average by > {MARGIN}\n")

    if not working:
        print("*** KILL CRITERION HIT ***\n")
        if weak and not no_lift:
            print("No axis is usefully predictable from text or numerics at all")
            print(f"(every axis below r={USEFUL_R}). Either the descriptions carry")
            print("no signal, or the labels do not mean what we assumed.")
        else:
            print("No axis beats the style-average baseline by a useful margin.")
            print("The 'profile' is a laundered style label: everything it knows,")
            print("the style already told us.")
        print("\nThe content-based premise is in trouble. Re-open D-001/D-002,")
        print("and consider that the honest project may be style-based.")
        print("Log this in DEAD-ENDS.md WITH THIS TABLE.")
        return 1

    print(f"WORKS on {len(working)}/{len(CANDIDATE_AXES)} axes:")
    print("  " + ", ".join(working))
    print(f"\nHeadline axes over r=0.7: "
          f"{', '.join(headline_ok) if headline_ok else 'NONE'} "
          f"(of {', '.join(HEADLINE_AXES)})")
    if not headline_ok:
        print("  -> weaker than hoped. Proceed, but expect a low ceiling in M4.")
    if no_lift:
        print(f"\nPredictable, but style already told us "
              f"(no lift over baseline):\n  " + ", ".join(no_lift))
    if weak:
        print(f"\nBelow r={USEFUL_R} — DROP these from the vocabulary (D-001):")
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
    ap.add_argument("--holdout", type=int, default=200)
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()

    if args.self_test:
        print("SELF-TEST: synthetic data with a known text signal.")
        print("A working harness MUST show text+numerics beating style-average.\n")
        df = make_synthetic(seed=args.seed)
    elif args.data:
        df = load(args.data)
        print(f"Loaded {len(df)} beers from {args.data}")
    else:
        ap.error("pass --data <csv> or --self-test")

    tr, te = train_test_split(df, test_size=args.holdout, random_state=args.seed)
    print(f"train={len(tr)}  holdout={len(te)}  seed={args.seed}")

    truth = te[CANDIDATE_AXES].to_numpy()
    scores = {}
    for name, fn in METHODS.items():
        scores[name] = per_axis_r(truth, np.asarray(fn(tr, te), dtype=float))

    rc = report(scores)
    if args.self_test:
        ok = scores["text+numerics"]["Bitter"] > scores["style-average"]["Bitter"]
        print(f"\nself-test {'PASSED' if ok else 'FAILED'} — harness "
              f"{'detects' if ok else 'CANNOT DETECT'} a known text signal.")
        return 0 if ok else 2
    return rc


if __name__ == "__main__":
    sys.exit(main())
