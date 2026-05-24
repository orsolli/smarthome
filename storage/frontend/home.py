def root():
    return """
    <html>
        <head>
            <title>Storage Dashboard</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <!-- htmx for dynamic content loading -->
            <script src="https://unpkg.com/htmx.org@1.7.0"></script>
        </head>
        <body>
            <h1>Welcome to the Storage Dashboard</h1>
            <nav>
                <a href="/get_filesystems" hx-get="/get_filesystems" hx-target="#content">View Filesystems</a>
            </nav>
            <div id="content">
                <p>Select an option from the menu to view details.</p>
            </div>
        </body>
    </html>
    """

def get_filesystems(filesystems):
    # Placeholder for fetching filesystem data from the database
    return f"""
    <ul>
        {'\n'.join(f'<li hx-get="/get_usage_history{fs["mounted_on"]}" hx-target="#content">{fs["mounted_on"]}</li>' for fs in filesystems)}
    </ul>"""

def get_usage_history(mounted_on, usage_data):
    # Usage history for a specific mount point using plotly
    plot_data = [{
        'x': [entry['timestamp'] for entry in usage_data],
        'y': [entry['used_bytes'] / (entry['available_bytes'] + entry['used_bytes']) for entry in usage_data],
        'type': 'time-series',
    }]
    return f"""
    <div id="usage-history-plot"></div>
    <script>
        var data = {plot_data};  // Placeholder for usage history data
        var layout = {{
            title: 'Usage History for {mounted_on}',
            xaxis: {{ title: '{(usage_data[-1]['total_bytes']/1024**3):.2f} GB' }},
            yaxis: {{ title: 'Usage' }}
        }};
        Plotly.newPlot('usage-history-plot', data, layout);
    </script>"""
