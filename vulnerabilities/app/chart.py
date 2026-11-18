"""Timeline bar renderer for the dependency tree.

Each tree node gets one compact bar spanning the scan window of its target.
A segment is the stretch between two scans, painted with the highest severity
found anywhere in that node's subtree during that stretch.
"""

from datetime import datetime

from core.severity import SEVERITY_INTENSITY, severity_rgba


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
        color = severity_rgba(sev, SEVERITY_INTENSITY.get(sev, 1.0))
        title = f"{sev} from {seg_start.isoformat()} to {seg_end.isoformat()}"
        if version:
            title += f" ({version})"
        html += (
            f'<span class="chart-bar-segment" '
            f'style="width:{width:.2f}%;background:{color};" '
            f'title="{title}"></span>'
        )
    return html


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

