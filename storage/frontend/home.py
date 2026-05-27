"""Dashboard frontend with HTMX, Pico CSS, and Plotly."""

def _safe_id(name):
    """Sanitize a string for use as a DOM ID."""
    return "".join(c if c.isalnum() or c == '_' else '_' for c in name)
# JavaScript version of the same function
_safeId_func = """
    function _safeId(name) {
        return name.replace(/[^a-zA-Z0-9]/g, '_');
    }
"""

def root():
    return """
    <!DOCTYPE html>
    <html lang="en" data-theme="dark">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Storage Dashboard</title>
        <!-- Pico CSS -->
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">
        <!-- HTMX -->
        <script src="https://unpkg.com/htmx.org@1.9.12"></script>
        <!-- Plotly -->
        <script src="https://cdn.plot.ly/plotly-2.35.0.min.js"></script>
        <style>
            :root {
                --card-bg: var(--pico-card-background-color, #fff);
                --card-border: var(--pico-card-border-color, #e0e0e0);
                --bar-bg: #e9ecef;
                --bar-fill: var(--pico-primary, #0d6efd);
                --bar-fill-warn: #fd7e14;
                --bar-fill-crit: #d63031;
            }
            body { max-width: 1400px; margin: 0 auto; padding: 2rem 1rem; }
            .fs-card {
                border: 1px solid var(--card-border);
                border-radius: 8px;
                padding: 1rem;
                margin-bottom: 1rem;
                background: var(--card-bg);
                transition: box-shadow 0.2s;
            }
            .fs-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
            .fs-card.pinned { border-left: 4px solid var(--pico-primary); }
            .fs-card.hidden { display: none; }
            .usage-bar {
                height: 8px;
                background: var(--bar-bg);
                border-radius: 4px;
                overflow: hidden;
                margin: 0.5rem 0;
            }
            .usage-bar-fill {
                height: 100%;
                border-radius: 4px;
                transition: width 0.3s ease;
            }
            .chart-container { width: 100%; margin-top: 0.75rem; min-height: 200px; }
            .card-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 0.5rem;
            }
            .card-header h3 { margin: 0; font-size: var(--pico-font-size, 1rem); }
            .card-actions button {
                font-size: 0.75rem;
                padding: 0.15rem 0.5rem;
                margin-left: 0.25rem;
            }
            .stats {
                display: flex;
                gap: 1rem;
                font-size: 0.85rem;
                color: var(--pico-muted-color, #666);
                flex-wrap: wrap;
            }
            .stats span { white-space: nowrap; }
            #dashboard-grid { display: flex; flex-direction: column; gap: 0.5rem; }
            .view-toggle {
                display: inline-flex;
                border: 1px solid var(--pico-card-border-color);
                border-radius: 4px;
                overflow: hidden;
            }
            .view-toggle button {
                border: none;
                padding: 0.25rem 0.75rem;
                cursor: pointer;
                background: transparent;
                font-size: 0.8rem;
            }
            .view-toggle button.active {
                background: var(--pico-primary);
                color: white;
            }
            .empty-state {
                text-align: center;
                padding: 3rem;
                color: var(--pico-muted-color);
            }
            /* Hint styling for filesystems that might be interesting */
            .fs-card.hint {
                border-left: 4px solid var(--bar-fill-warn);
                opacity: 0.85;
            }
            .fs-card.hint::after {
                content: '⚠ High usage detected';
                font-size: 0.7rem;
                color: var(--bar-fill-warn);
                margin-left: 0.5rem;
            }
        </style>
    </head>
    <body>
        <header>
            <h1>Storage Dashboard</h1>
            <p class="text-muted">
                <button onclick="refreshAll()" class="secondary">↻ Refresh All</button>
                <button onclick="toggleHidden()" class="secondary">Show Hidden</button>
            </p>
        </header>

        <div id="dashboard-grid"
             hx-get="/get_filesystems"
             hx-trigger="load"
             hx-swap="innerHTML"
             hx-on::after-request="onFilesystemsLoaded()">
            <div class="empty-state">Loading filesystems...</div>
        </div>

        <script>
        // ── localStorage preferences ──
        const PREFS_KEY = 'storage_dashboard_prefs';

        function getPrefs() {
            try {
                return JSON.parse(localStorage.getItem(PREFS_KEY)) || { hidden: [], pinned: [] };
            } catch { return { hidden: [], pinned: [] }; }
        }

        function savePrefs(prefs) {
            localStorage.setItem(PREFS_KEY, JSON.stringify(prefs));
        }

        function toggleHiddenFs(mountedOn) {
            const prefs = getPrefs();
            const idx = prefs.hidden.indexOf(mountedOn);
            if (idx === -1) prefs.hidden.push(mountedOn);
            else prefs.hidden.splice(idx, 1);
            savePrefs(prefs);
            applyVisibility();
        }

        function togglePinnedFs(mountedOn) {
            const prefs = getPrefs();
            const idx = prefs.pinned.indexOf(mountedOn);
            if (idx === -1) prefs.pinned.push(mountedOn);
            else prefs.pinned.splice(idx, 1);
            savePrefs(prefs);
            applyVisibility();
        }

        function applyVisibility() {
            const prefs = getPrefs();
            document.querySelectorAll('.fs-card').forEach(card => {
                const fs = card.dataset.mountedOn;
                if (prefs.hidden.includes(fs)) {
                    card.classList.add('hidden');
                } else {
                    card.classList.remove('hidden');
                }
                if (prefs.pinned.includes(fs)) {
                    card.classList.add('pinned');
                } else {
                    card.classList.remove('pinned');
                }
            });
        }

        let showHidden = false;
        function toggleHidden() {
            showHidden = !showHidden;
            const prefs = getPrefs();
            document.querySelectorAll('.fs-card').forEach(card => {
                const fs = card.dataset.mountedOn;
                if (showHidden || !prefs.hidden.includes(fs)) {
                    card.classList.remove('hidden');
                } else {
                    card.classList.add('hidden');
                }
            });
        }

        // ── Chart rendering ──
        const chartDefaults = {
            margin: { t: 10, b: 40, l: 50, r: 20 },
            font: { size: 10 },
            hovermode: 'x unified',
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
        };

        function renderLineChart(containerId, data, mountedOn) {
            if (!data || data.length === 0) return;
            const usagePct = data.map(d =>
                d.total_bytes > 0
                    ? (d.used_bytes / d.total_bytes) * 100
                    : 0
            );
            const availablePct = data.map(d =>
                d.total_bytes > 0
                    ? (d.available_bytes / d.total_bytes) * 100
                    : 0
            );
            const traces = [
                {
                    x: data.map(d => d.timestamp),
                    y: usagePct,
                    name: 'Used %',
                    line: { color: '#d63031' },
                    fill: 'tozeroy',
                    fillcolor: 'rgba(214,48,49,0.1)',
                    type: 'scatter',
                },
                {
                    x: data.map(d => d.timestamp),
                    y: availablePct,
                    name: 'Available %',
                    line: { color: '#00b894' },
                    fill: 'tozeroy',
                    fillcolor: 'rgba(0,184,148,0.1)',
                    type: 'scatter',
                }
            ];
            const layout = {
                ...chartDefaults,
                title: { text: mountedOn, font: { size: 12 } },
                xaxis: { title: 'Time', tickformat: '%H:%M\\n%b %d' },
                yaxis: { title: 'Usage %', range: [0, 105] },
                showlegend: true,
                legend: { orientation: 'h', y: -0.15 },
            };
            Plotly.newPlot(containerId, traces, layout, { responsive: true, displayModeBar: false });
        }

        function renderCandlestickChart(containerId, data, mountedOn) {
            if (!data || data.length === 0) return;
            const traces = [{
                x: data.map(d => d.timestamp),
                open: data.map(d => d.open_bytes),
                high: data.map(d => d.high_bytes),
                low: data.map(d => d.low_bytes),
                close: data.map(d => d.close_bytes),
                type: 'candlestick',
                increasing: { line: { color: '#00b894' } },
                decreasing: { line: { color: '#d63031' } },
            }];
            const layout = {
                ...chartDefaults,
                title: { text: mountedOn, font: { size: 12 } },
                xaxis: { title: 'Time', tickformat: '%b %d, %Y' },
                yaxis: { title: 'Bytes Used' },
                showlegend: false,
            };
            Plotly.newPlot(containerId, traces, layout, { responsive: true, displayModeBar: false });
        }

        function renderChart(containerId, data, mountedOn, resolution) {
            const container = document.getElementById(containerId);
            if (!container) return;
            Plotly.purge(containerId);
            if (resolution === 'high') {
                renderLineChart(containerId, data, mountedOn);
            } else {
                renderCandlestickChart(containerId, data, mountedOn);
            }
        }

        // ── Card rendering ──
        function setResolution(mountedOn, resolution, btn) {
            const card = document.querySelector(`.fs-card[data-mounted-on="${mountedOn}"]`);
            if (!card) return;
            card.dataset.resolution = resolution;
            // Update button states
            const toggle = btn.parentElement;
            toggle.querySelectorAll('button').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            // Re-render chart
            const chartId = `chart-${_safeId(mountedOn)}`;
            const range = resolution === 'high' ? '1w' : '1y';
            fetch(`/get_usage_history/${encodeURIComponent(mountedOn)}?range=${range}`)
                .then(r => r.json())
                .then(data => renderChart(chartId, data, mountedOn, resolution))
                .catch(() => {
                    document.getElementById(chartId).innerHTML = '<p class="text-muted">Error loading data</p>';
                });
        }
        """ + _safeId_func + """

        function formatBytes(bytes) {
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
        }

        function usageColor(pct) {
            if (pct >= 90) return 'var(--bar-fill-crit)';
            if (pct >= 70) return 'var(--bar-fill-warn)';
            return 'var(--bar-fill)';
        }

        function onFilesystemsLoaded() {
            renderCards();
        }

        function renderCards() {
            const prefs = getPrefs();
            const cards = document.querySelectorAll('.fs-card');
            cards.forEach(card => {
                const mountedOn = card.dataset.mountedOn;
                const chartContainerId = `chart-${_safeId(mountedOn)}`;
                const chartDiv = document.getElementById(chartContainerId);
                if (!chartDiv || prefs.hidden.includes(card.dataset.mountedOn)) return;
                const resolution = card.dataset.resolution || 'low';
                const range = resolution === 'high' ? '1w' : '1y';

                fetch(`/get_usage_history/${encodeURIComponent(mountedOn)}?range=${range}`)
                    .then(r => r.json())
                    .then(data => {
                        if (Array.isArray(data) && data.length > 0) {
                            renderChart(chartContainerId, data, mountedOn, resolution);
                            // Update stats with latest data
                            let latest, pct;
                            if (resolution === 'high') {
                                // Line chart data: raw measurements
                                latest = data[data.length - 1];
                                pct = (latest.used_bytes / latest.total_bytes) * 100;
                            } else {
                                // Candlestick data: daily aggregates
                                latest = data[data.length - 1];
                                pct = (latest.close_bytes / latest.total_bytes) * 100;
                            }
                            const statsDiv = card.querySelector('.stats');
                            if (statsDiv) {
                                statsDiv.innerHTML = `
                                    <span>Used: ${formatBytes(latest.used_bytes ?? latest.close_bytes)}</span>
                                    <span>Free: ${formatBytes(latest.available_bytes ?? (latest.total_bytes - latest.close_bytes))}</span>
                                    <span>Total: ${formatBytes(latest.total_bytes)}</span>
                                `;
                                // Update usage bar
                                const barFill = card.querySelector('.usage-bar-fill');
                                if (barFill) {
                                    barFill.style.width = `${pct}%`;
                                    if (pct >= 90) barFill.style.background = 'var(--bar-fill-crit)';
                                    else if (pct >= 70) barFill.style.background = 'var(--bar-fill-warn)';
                                    else barFill.style.background = 'var(--bar-fill)';
                                }
                                // Add hint if usage is high
                                if (pct >= 85) {
                                    card.classList.add('hint');
                                } else {
                                    card.classList.remove('hint');
                                }
                            }
                        } else {
                            chartDiv.innerHTML = '<p class="text-muted">No data available</p>';
                        }
                    })
                    .catch(() => {
                        chartDiv.innerHTML = '<p class="text-muted">Error loading data</p>';
                    });
            });
            applyVisibility();
        }

        function refreshAll() {
            location.reload();
        }
        </script>
    </body>
    </html>
    """


def get_filesystems(filesystems):
    """Render the filesystem list as cards (HTML template for HTMX swap)."""
    if not filesystems or len(filesystems) == 0:
        return '<div class="empty-state">No filesystems found.</div>'

    cards = []
    for fs in filesystems:
        mounted_on = fs['mounted_on']
        safe_id = _safe_id(mounted_on)
        cards.append(f"""
        <div class="fs-card" data-mounted-on="{mounted_on}" data-resolution="low">
            <div class="card-header">
                <h3>{mounted_on}</h3>
                <div class="card-actions">
                    <button class="secondary" onclick="togglePinnedFs('{mounted_on}')">📌 Pin</button>
                    <button class="secondary" onclick="toggleHiddenFs('{mounted_on}')">👁 Hide</button>
                    <div class="view-toggle">
                        <button class="active" onclick="setResolution('{mounted_on}', 'low', this)">1Y</button>
                        <button onclick="setResolution('{mounted_on}', 'high', this)">1W</button>
                    </div>
                </div>
            </div>
            <div class="stats">
                <span class="loading">Loading data...</span>
            </div>
            <div id="chart-{safe_id}" class="chart-container"></div>
        </div>
        """)

    return '\n'.join(cards)
