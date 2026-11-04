"""Inline-SVG sparkline helper for profile trend charts (no JS, CSP-safe)."""
from __future__ import annotations


def sparkline(values, width=520, height=120, pad=8):
    pts = [v for v in values if v is not None]
    if len(pts) < 2:
        return None
    lo, hi = min(pts), max(pts)
    span = (hi - lo) or 1
    n = len(pts)
    coords = []
    for i, v in enumerate(pts):
        x = pad + (width - 2 * pad) * i / (n - 1)
        y = pad + (height - 2 * pad) * (1 - (v - lo) / span)
        coords.append((round(x, 1), round(y, 1)))
    line = " ".join(f"{x},{y}" for x, y in coords)
    area = f"{pad},{height - pad} {line} {width - pad},{height - pad}"
    return {"line": line, "area": area, "width": width, "height": height}
