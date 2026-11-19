"""Severity colors for the frontend.

The severity levels themselves live in core/severity.py. This module only
pairs them with the CSS values templates paint with; import the helpers from
core.severity for anything that compares or aggregates severities.
"""

from core.severity import SEVERITY_RANK, severity_bg_color, severity_color

# severity -> (solid color, row tint), in rank order.
SEVERITY_COLORS: dict[str, tuple[str, str]] = {
    severity: (severity_color(severity), severity_bg_color(severity))
    for severity in SEVERITY_RANK
}
