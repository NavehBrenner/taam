"""Controls for the Untappd description check.

Same discipline as `test_m0_harness.py`, for the same reason: this harness is
allowed to retire a data source (D-004 option D — drop Untappd entirely), so its
verdict has to be shown to work in both directions before it is trusted.

    python tests/test_untappd_check.py     # or: pytest tests/

The negative direction is the one that matters. The expected outcome here is
"descriptions are thin" — catalog.beer was measured at 0/10 for Israeli beers —
and a harness that can only confirm what we already expect is worthless. So the
positive control is the important assertion: given genuinely rich descriptions,
the verdict MUST say so and let Untappd keep its slot.

No network and no API key: only the pure verdict/render logic is exercised.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load():
    if "untappd_check" in sys.modules:
        return sys.modules["untappd_check"]
    spec = importlib.util.spec_from_file_location(
        "untappd_check", ROOT / "scripts" / "untappd_description_check.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    # Register before exec: @dataclass resolves annotations via sys.modules, and
    # under `from __future__ import annotations` it fails on an unregistered module.
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _results(mod, outcome: str, chars: int, n: int = 10):
    return [mod.Result("Malka", f"beer {i}", outcome, "x", "Malka", i, chars) for i in range(n)]


def test_positive_control_detects_real_prose():
    """Rich descriptions must be recognised, or the check can only ever condemn."""
    mod = _load()
    call, why = mod.verdict(_results(mod, "FOUND_DESC", 240))
    assert call == "UNTAPPD EARNS ITS SLOT", why


def test_negative_control_empty_descriptions():
    """Found on Untappd but no text: adds nothing over the bottle label."""
    mod = _load()
    call, why = mod.verdict(_results(mod, "FOUND_NO_DESC", 0))
    assert call == "UNTAPPD ADDS NOTHING", why


def test_a_style_tag_is_not_a_description():
    """"Israeli Pale Ale" is 18 chars and teaches the regressor nothing."""
    mod = _load()
    call, why = mod.verdict(_results(mod, "FOUND_DESC", 18))
    assert call == "UNTAPPD ADDS NOTHING", why


def test_half_populated_still_fails():
    """Half a catalog with no text is still a source the profiler cannot rely on."""
    mod = _load()
    mixed = _results(mod, "FOUND_DESC", 400, n=5) + _results(mod, "FOUND_NO_DESC", 0, n=5)
    call, why = mod.verdict(mixed)
    assert call == "UNTAPPD ADDS NOTHING", why


def test_absent_is_distinct_from_empty():
    """Coverage misses are reported as coverage, not silently scored as zero."""
    mod = _load()
    call, why = mod.verdict(_results(mod, "NOT_FOUND", 0))
    assert call == "UNTAPPD ADDS NOTHING"
    assert "exist on Untappd" in why, why


def test_render_never_leaks_description_text():
    """The output is publishable only because it carries lengths, not prose."""
    mod = _load()
    out = mod.render(_results(mod, "FOUND_DESC", 240))
    assert "240" in out
    assert "beer_description" not in out


if __name__ == "__main__":
    test_positive_control_detects_real_prose()
    test_negative_control_empty_descriptions()
    test_a_style_tag_is_not_a_description()
    test_half_populated_still_fails()
    test_absent_is_distinct_from_empty()
    test_render_never_leaks_description_text()
    print("all controls passed")
