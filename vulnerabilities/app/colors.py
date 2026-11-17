"""Severity colors for the frontend.

The severity levels themselves live in core/severity.py; this module only
exposes them as CSS values. Import from here for rendering, from
core.severity for comparisons.
"""

from core.severity import (
    SEVERITY_RANK,
    aggregate_severity,
    severity_bg_color,
    severity_color,
    severity_from_cvss,
    severity_label,
    severity_rank,
    severity_rgba,
)

# Kept as a literal map so templates can iterate over it directly.
SEVERITY_COLORS: dict[str, tuple[str, str]] = {
    severity: (severity_color(severity), severity_bg_color(severity))
    for severity in SEVERITY_RANK
}

SEVERITY_ORDER: dict[str, int] = SEVERITY_RANK

__all__ = [
    "SEVERITY_COLORS",
    "SEVERITY_ORDER",
    "aggregate_severity",
    "severity_bg_color",
    "severity_color",
    "severity_from_cvss",
    "severity_label",
    "severity_rank",
    "severity_rgba",
]
