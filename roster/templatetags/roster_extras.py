"""Presentation helpers for the roster templates."""
from django import template

register = template.Library()

PALETTE = [
    ("#f2b97e", "#8fc8a2"), ("#9fd0b4", "#cfe3a0"), ("#f0c58a", "#e8a06a"),
    ("#8fc9bd", "#a9d8c4"), ("#f4b58a", "#f3d79e"), ("#a7d7bd", "#7fc2a0"),
    ("#e9a06a", "#f2c58a"), ("#9ccabc", "#bfe0a8"), ("#f2c79e", "#9fd2b4"),
    ("#8bc6a6", "#acd8dd"), ("#f0b07a", "#eac98e"), ("#b4e0b0", "#8fc8a2"),
]


@register.filter
def compact(value):
    try:
        n = float(value)
    except (TypeError, ValueError):
        return "-"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M".replace(".0M", "M")
    if n >= 1_000:
        return f"{n / 1_000:.0f}k"
    return str(int(n))


@register.filter
def avatar_grad(name):
    idx = sum(ord(c) for c in (name or "?")) % len(PALETTE)
    a, b = PALETTE[idx]
    return f"linear-gradient(135deg,{a},{b})"


@register.filter
def initials(name):
    parts = (name or "?").split()
    return "".join(p[0] for p in parts[:2]).upper()
