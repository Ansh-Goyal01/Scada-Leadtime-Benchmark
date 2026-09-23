"""Guards PLOT["method_colors"] against the colour-collision defect.

Plot helpers resolve colours with ``method_colors.get(short_name, None)`` and hand the
result to matplotlib unchanged. A missing key therefore does NOT mean "no colour" -- it
means matplotlib's default property cycle, whose first entries (#1f77b4, #ff7f0e,
#2ca02c) are perceptually indistinguishable from the assigned 3-sigma, Hotelling and
EWMA colours. Five detectors were unassigned and collided that way.
"""

import itertools

import numpy as np
import pytest

from src.config import EXPERIMENT, PLOT

MIN_DELTA_E = 30.0   # CIE76; the shipped palette achieves 38.4


def _lab(hex_color):
    h = hex_color.lstrip("#")
    rgb = np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
    lin = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    m = np.array([[0.4124564, 0.3575761, 0.1804375],
                  [0.2126729, 0.7151522, 0.0721750],
                  [0.0193339, 0.1191920, 0.9503041]])
    t = (m @ lin) / np.array([0.95047, 1.0, 1.08883])
    f = np.where(t > 0.008856, np.cbrt(t), 7.787 * t + 16 / 116)
    return np.array([116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])])


def _delta_e(a, b):
    return float(np.linalg.norm(_lab(a) - _lab(b)))


def _expected_detectors():
    # one_class_svm is run by the D4 pipeline, not methods_to_run, but it is plotted
    # (forest plot) and so needs its own colour too.
    return list(EXPERIMENT["methods_to_run"]) + ["conformal_if", "one_class_svm"]


def test_every_detector_has_a_colour():
    missing = [m for m in _expected_detectors() if m not in PLOT["method_colors"]]
    assert not missing, f"unassigned detectors fall back to matplotlib's cycle: {missing}"


def test_all_plotted_detectors_are_covered():
    assert len(_expected_detectors()) == 12
    assert len(PLOT["method_colors"]) == 12


def test_no_two_detectors_share_a_hex():
    colors = PLOT["method_colors"]
    dupes = [c for c in set(colors.values())
             if sum(1 for v in colors.values() if v == c) > 1]
    assert not dupes, f"colour(s) assigned to more than one detector: {dupes}"


@pytest.mark.parametrize("pair", list(itertools.combinations(
    sorted(PLOT["method_colors"]), 2)))
def test_detector_colours_are_perceptually_distinct(pair):
    a, b = pair
    d = _delta_e(PLOT["method_colors"][a], PLOT["method_colors"][b])
    assert d >= MIN_DELTA_E, f"{a} and {b} are only dE={d:.1f} apart"


def test_palette_does_not_reuse_matplotlib_cycle_defaults():
    """The exact colours a missing key would have produced must not appear, or a
    regression to the fallback would be invisible in the figures."""
    fallback = {"#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"}
    clash = {k: v for k, v in PLOT["method_colors"].items() if v.lower() in fallback}
    assert not clash, f"palette entries collide with the default cycle: {clash}"
