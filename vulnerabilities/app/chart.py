"""Timeline bar chart renderer for vulnerability timeseries.

Generates HTML for a timeline bar chart where each bar represents
a package and segments show vulnerability duration/severity over time.
"""

from datetime import datetime


def _severity_to_color(severity: str, intensity: float = 1.0) -> str:
    """Convert severity to a color, optionally with intensity.

    Args:
        severity: Severity string.
        intensity: Opacity multiplier (0.0-1.0).

    Returns:
        CSS color string.
    """
    colors = {
        "CRITICAL": (218, 54, 51),
        "HIGH": (240, 136, 62),
        "MEDIUM": (210, 153, 34),
        "LOW": (63, 185, 80),
        "NONE": (48, 54, 61),
    }
    r, g, b = colors.get(severity, colors["NONE"])
    alpha = min(1.0, intensity)
    return f"rgba({r}, {g}, {b}, {alpha})"


def _parse_timestamp(ts: str) -> datetime:
    """Parse ISO timestamp string.

    Args:
        ts: ISO format timestamp.

    Returns:
        datetime object.
    """
    try:
        return datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return datetime.min


def timeseries_bar_html(
    package_name: str,
    timeline: list[dict],
    start_time: datetime,
    end_time: datetime,
) -> str:
    """Render a single timeline bar for a package.

    Each segment in the bar represents a time period where the
    package had a particular severity level.

    Args:
        package_name: Package name.
        timeline: List of dicts with keys: timestamp, severity.
        start_time: Chart start time.
        end_time: Chart end time.

    Returns:
        HTML string for the bar.
    """
    if not timeline:
        return f"""<div class="chart-bar">
    <span class="chart-bar-label" title="{package_name}">{package_name}</span>
    <span class="chart-bar-track">
        <span class="chart-bar-segment" style="background:#30363d;flex:1;"></span>
    </span>
</div>"""

    total_seconds = (end_time - start_time).total_seconds()
    if total_seconds <= 0:
        total_seconds = 1

    segments_html = ""
    for event in timeline:
        sev = event.get("severity", "NONE")
        ts = event.get("timestamp", "")
        event_time = _parse_timestamp(ts)

        # Calculate segment position and width
        if event_time <= start_time:
            seg_start = 0.0
        else:
            seg_start = (event_time - start_time).total_seconds() / total_seconds * 100

        # Each event gets 100% width (it marks the state at that time)
        # For a proper timeline, we'd calculate duration between events
        width = 100.0 / max(1, len(timeline))
        color = _severity_to_color(sev)

        segments_html += f'<span class="chart-bar-segment" style="width:{width}%;background:{color};" title="{sev}: {ts}"></span>'

    return f"""<div class="chart-bar">
    <span class="chart-bar-label" title="{package_name}">{package_name}</span>
    <span class="chart-bar-track">
        {segments_html}
    </span>
</div>"""


def timeseries_chart_html(
    data: list[dict],
    start_time: str,
    end_time: str,
) -> str:
    """Render a complete timeline bar chart.

    Args:
        data: List of dicts with keys: package_name, timestamp, severity.
        start_time: Start timestamp (ISO format).
        end_time: End timestamp (ISO format).

    Returns:
        HTML string for the chart.
    """
    start_dt = _parse_timestamp(start_time)
    end_dt = _parse_timestamp(end_time)

    # Group by package
    packages: dict[str, list[dict]] = {}
    for row in data:
        pkg = row.get("package_name", "unknown")
        packages.setdefault(pkg, []).append(row)

    # Sort packages alphabetically
    sorted_packages = sorted(packages.keys())

    bars_html = ""
    for pkg in sorted_packages:
        timeline = sorted(packages[pkg], key=lambda x: _parse_timestamp(x.get("timestamp", "")))
        bars_html += timeseries_bar_html(pkg, timeline, start_dt, end_dt)

    return f"""<h2>Vulnerability Timeline</h2>
<div id="timeline-chart">
    <div style="font-size:0.7rem;color:#8b949e;margin-bottom:8px;">
        {start_time} → {end_time}
    </div>
    {bars_html}
</div>"""
