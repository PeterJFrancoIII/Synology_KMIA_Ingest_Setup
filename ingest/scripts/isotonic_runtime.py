"""Isotonic calibration knot interpolation (no sklearn at runtime)."""

from __future__ import annotations

from typing import Sequence


def apply_isotonic_points(raw_p: float, points: Sequence[Sequence[float]]) -> float:
    if not points:
        return raw_p
    pts = [(float(x), float(y)) for x, y in points]
    pts.sort(key=lambda t: t[0])
    p = float(raw_p)
    if p <= pts[0][0]:
        return pts[0][1]
    if p >= pts[-1][0]:
        return pts[-1][1]
    for i in range(1, len(pts)):
        x0, y0 = pts[i - 1]
        x1, y1 = pts[i]
        if x0 <= p <= x1:
            if x1 == x0:
                return y1
            t = (p - x0) / (x1 - x0)
            return y0 + t * (y1 - y0)
    return p
