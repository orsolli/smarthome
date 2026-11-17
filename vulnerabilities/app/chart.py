"""Timeline bar chart renderer for vulnerability timeseries.

Generates HTML for a timeline bar chart where each bar represents
a package and segments show vulnerability duration/severity over time.
"""

from datetime import datetime

from core.severity import SEVERITY_INTENSITY, severity_rgba


def _severity_to_color(severity: str, intensity: float = 1.0) -> str:
    """Convert severity to a color, optionally with intensity.

    Args:
        severity: Severity string.
        intensity: Opacity multiplier (0.0-1.0).

    Returns:
        CSS color string.
    """
    return severity_rgba(severity, intensity)


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


def _build_segments(
    timeline: list[dict],
    start_time: datetime,
    end_time: datetime,
) -> list[tuple[str, float, datetime, datetime, str]]:
    """Turn scan events into (severity, width_percent, start, end, version) segments.

    The severity recorded at a scan persists until the next scan changes
    it, so a bar always covers the whole [start_time, end_time] window.
    Zero-width segments (two scans at the same timestamp) are skipped.

    Args:
        timeline: List of dicts with keys: timestamp, severity, version.
        start_time: Chart start time.
        end_time: Chart end time.

    Returns:
        List of (severity, width_percent, segment_start, segment_end, version).
    """
    total_seconds = (end_time - start_time).total_seconds()
    if total_seconds <= 0:
        total_seconds = 1

    timeline = sorted(timeline, key=lambda x: _parse_timestamp(x.get("timestamp", "")))

    segments: list[tuple[str, float, datetime, datetime, str]] = []
    prev_time = start_time
    prev_sev = "NONE"
    prev_version = ""
    for event in timeline:
        sev = event.get("severity", "NONE")
        version = event.get("version", "")
        event_time = _parse_timestamp(event.get("timestamp", ""))
        event_time = max(start_time, min(event_time, end_time))

        if event_time > prev_time:
            width = (event_time - prev_time).total_seconds() / total_seconds * 100
            segments.append((prev_sev, width, prev_time, event_time, prev_version))

        prev_time = event_time
        prev_sev = sev
        prev_version = version

    if prev_time < end_time:
        width = (end_time - prev_time).total_seconds() / total_seconds * 100
        segments.append((prev_sev, width, prev_time, end_time, prev_version))

    return segments


def _segments_html(
    segments: list[tuple[str, float, datetime, datetime, str]]
) -> str:
    """Render timeline segments as span elements."""
    html = ""
    for sev, width, seg_start, seg_end, version in segments:
        color = _severity_to_color(sev, SEVERITY_INTENSITY.get(sev, 1.0))
        title = f"{sev} from {seg_start.isoformat()} to {seg_end.isoformat()}"
        if version:
            title += f" ({version})"
        html += (
            f'<span class="chart-bar-segment" '
            f'style="width:{width:.2f}%;background:{color};" '
            f'title="{title}"></span>'
        )
    return html


def timeseries_bar_html(
    package_name: str,
    timeline: list[dict],
    start_time: datetime,
    end_time: datetime,
) -> str:
    """Render a single labelled timeline bar for a package.

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

    return f"""<div class="chart-bar">
    <span class="chart-bar-label" title="{package_name}">{package_name}</span>
    <span class="chart-bar-track">
        {_segments_html(_build_segments(timeline, start_time, end_time))}
    </span>
</div>"""


def mini_bar_html(
    timeline: list[dict],
    start_time: datetime,
    end_time: datetime,
) -> str:
    """Render a compact, label-free timeline track for a tree node.

    Args:
        timeline: List of dicts with keys: timestamp, severity.
        start_time: Chart start time (shared window for all nodes).
        end_time: Chart end time.

    Returns:
        HTML string containing only the bar track.
    """
    if not timeline:
        return (
            '<span class="chart-bar-track">'
            '<span class="chart-bar-segment" style="background:#30363d;flex:1;"></span>'
            "</span>"
        )

    return f'<span class="chart-bar-track">{_segments_html(_build_segments(timeline, start_time, end_time))}</span>'


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
