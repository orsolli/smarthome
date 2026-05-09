"""Severity color utilities for frontend rendering.

Maps severity levels to CSS color values and computes aggregate
severity for parent nodes based on child states.
"""

SEVERITY_COLORS: dict[str, tuple[str, str]] = {
    "CRITICAL": ("#da3633", "rgba(218, 54, 51, 0.3)"),
    "HIGH": ("#f0883e", "rgba(240, 136, 62, 0.25)"),
    "MEDIUM": ("#d29922", "rgba(210, 153, 34, 0.2)"),
    "LOW": ("#3fb950", "rgba(63, 185, 80, 0.15)"),
    "NONE": ("#30363d", "rgba(48, 54, 61, 0.1)"),
}

SEVERITY_ORDER: dict[str, int] = {
    "CRITICAL": 4,
    "HIGH": 3,
    "MEDIUM": 2,
    "LOW": 1,
    "NONE": 0,
}


def aggregate_severity(severities: list[str]) -> str:
    """Compute the highest severity from a list.

    If any child is CRITICAL, parent is CRITICAL.
    If any child is HIGH, parent is at least HIGH.

    Args:
        severities: List of severity strings.

    Returns:
        Highest severity string.
    """
    if not severities:
        return "NONE"
    max_sev = "NONE"
    max_score = 0
    for sev in severities:
        score = SEVERITY_ORDER.get(sev, 0)
        if score > max_score:
            max_score = score
            max_sev = sev
    return max_sev


def severity_color(severity: str) -> str:
    """Get the primary color for a severity level.

    Args:
        severity: Severity string.

    Returns:
        CSS color hex string.
    """
    return SEVERITY_COLORS.get(severity, SEVERITY_COLORS["NONE"])[0]


def severity_bg_color(severity: str) -> str:
    """Get the background (semi-transparent) color for a severity level.

    Args:
        severity: Severity string.

    Returns:
        CSS rgba color string.
    """
    return SEVERITY_COLORS.get(severity, SEVERITY_COLORS["NONE"])[1]


def severity_label(severity: str) -> str:
    """Get a display label for a severity level.

    Args:
        severity: Severity string.

    Returns:
        Human-readable label.
    """
    labels = {
        "CRITICAL": "Critical",
        "HIGH": "High",
        "MEDIUM": "Medium",
        "LOW": "Low",
        "NONE": "Clean",
    }
    return labels.get(severity, "Unknown")
