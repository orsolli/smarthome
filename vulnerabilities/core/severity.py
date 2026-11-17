"""Canonical severity levels for the whole scanner.

Severity is defined once, here. Everything that compares, aggregates or
paints a severity reads from this module: the rank used to bubble a
child's severity up to its parent, the opacity used for timeline
segments, the tint used behind tree rows, and the CSS colors.

Levels run NONE -> LOW -> MEDIUM -> HIGH -> CRITICAL. NONE is a real
severity here: a node that was matched across scans and had no
vulnerability gets an explicit NONE entry so its bar ends cleanly.
"""

SEVERITY_RANK: dict[str, int] = {
    "NONE": 0,
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 4,
}

SEVERITY_RGB: dict[str, tuple[int, int, int]] = {
    "CRITICAL": (218, 54, 51),
    "HIGH": (240, 136, 62),
    "MEDIUM": (210, 153, 34),
    "LOW": (63, 185, 80),
    "NONE": (48, 54, 61),
}

# Opacity of a timeline segment: the longer a package stays unpatched,
# the darker the bar. Applied per segment, not per severity alone.
SEVERITY_INTENSITY: dict[str, float] = {
    "CRITICAL": 1.0,
    "HIGH": 0.8,
    "MEDIUM": 0.6,
    "LOW": 0.4,
    "NONE": 1.0,
}

# Soft background tint for tree rows, independent of segment opacity.
SEVERITY_BG_ALPHA: dict[str, float] = {
    "CRITICAL": 0.3,
    "HIGH": 0.25,
    "MEDIUM": 0.2,
    "LOW": 0.15,
    "NONE": 0.1,
}

SEVERITY_LABELS: dict[str, str] = {
    "CRITICAL": "Critical",
    "HIGH": "High",
    "MEDIUM": "Medium",
    "LOW": "Low",
    "NONE": "Clean",
}


def severity_rank(severity: str) -> int:
    """Rank of a severity; unknown values rank as NONE."""
    return SEVERITY_RANK.get(severity, 0)


def severity_from_cvss(cvss_score: float) -> str:
    """Map a CVSS v3 base score to a severity label."""
    if cvss_score >= 9.0:
        return "CRITICAL"
    if cvss_score >= 7.0:
        return "HIGH"
    if cvss_score >= 4.0:
        return "MEDIUM"
    return "LOW"


def aggregate_severity(severities: list[str]) -> str:
    """Highest severity in a list: a parent is as red as its worst child."""
    worst = "NONE"
    for severity in severities:
        if severity_rank(severity) > severity_rank(worst):
            worst = severity
    return worst


def severity_rgba(severity: str, intensity: float = 1.0) -> str:
    """CSS color for a timeline segment, with the segment's opacity."""
    r, g, b = SEVERITY_RGB.get(severity, SEVERITY_RGB["NONE"])
    return f"rgba({r}, {g}, {b}, {min(1.0, max(0.0, intensity))})"


def severity_color(severity: str) -> str:
    """Solid hex color for a severity."""
    r, g, b = SEVERITY_RGB.get(severity, SEVERITY_RGB["NONE"])
    return f"#{r:02x}{g:02x}{b:02x}"


def severity_bg_color(severity: str) -> str:
    """Semi-transparent background tint for a tree row."""
    alpha = SEVERITY_BG_ALPHA.get(severity, SEVERITY_BG_ALPHA["NONE"])
    r, g, b = SEVERITY_RGB.get(severity, SEVERITY_RGB["NONE"])
    return f"rgba({r}, {g}, {b}, {alpha})"


def severity_label(severity: str) -> str:
    """Display label for a severity."""
    return SEVERITY_LABELS.get(severity, "Unknown")
