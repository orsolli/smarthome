from datetime import datetime, timezone, timedelta
from enum import Enum
from functools import lru_cache
from flask import Flask, render_template_string, request, jsonify
import sqlite3
import plotly.graph_objs as go
import plotly.io as pio
import os

app = Flask(__name__)

class SensorData(Enum):
    humidity = 'sensor_data.humidity'
    radon_st_avg = 'sensor_data.radon_st_avg'
    radon_lt_avg = 'sensor_data.radon_lt_avg'
    temperature = 'sensor_data.temperature'
    pressure = 'sensor_data.pressure'
    co2 = 'sensor_data.co2'
    voc = 'sensor_data.voc'
    ACTIVE_POWER_PLUS = 'kamstrup_10sec.ACTIVE_POWER_PLUS'
    ACTIVE_POWER_MINUS = 'kamstrup_10sec.ACTIVE_POWER_MINUS'
    REACTIVE_POWER_PLUS = 'kamstrup_10sec.REACTIVE_POWER_PLUS'
    REACTIVE_POWER_MINUS = 'kamstrup_10sec.REACTIVE_POWER_MINUS'
    CURRENT_PHASE_L1 = 'kamstrup_10sec.CURRENT_PHASE_L1'
    CURRENT_PHASE_L2 = 'kamstrup_10sec.CURRENT_PHASE_L2'
    CURRENT_PHASE_L3 = 'kamstrup_10sec.CURRENT_PHASE_L3'
    VOLTAGE_PHASE_L1 = 'kamstrup_10sec.VOLTAGE_PHASE_L1'
    VOLTAGE_PHASE_L2 = 'kamstrup_10sec.VOLTAGE_PHASE_L2'
    VOLTAGE_PHASE_L3 = 'kamstrup_10sec.VOLTAGE_PHASE_L3'
    Cumulative_hourly_active_import_kWh = 'kamstrup_10sec.Cumulative_hourly_active_import_kWh'
    Cumulative_hourly_active_export_kWh = 'kamstrup_10sec.Cumulative_hourly_active_export_kWh'
    Cumulative_hourly_reactive_import_kVArh = 'kamstrup_10sec.Cumulative_hourly_reactive_import_kVArh'
    Cumulative_hourly_active_export_kVArh = 'kamstrup_10sec.Cumulative_hourly_active_export_kVArh'

def fetch_timeseries_data(sensor: SensorData, start_time=None, end_time=None):
    # Partition the start and end times into 5-minute intervals
    if not end_time:
        end_time = datetime.now(timezone.utc)
    if not start_time:
        start_time = end_time - timedelta(hours=6)
    start_time = start_time.replace(minute=start_time.minute - start_time.minute % 5, second=0, microsecond=0)
    next_time = start_time + timedelta(minutes=5)
    result = []
    while next_time < end_time:
        if next_time > datetime.now(timezone.utc):
            next_time = datetime.now(timezone.utc)
        data = fetch_timeseries_data_cached(sensor, start_time, next_time)
        result.extend(data)
        start_time = next_time
        next_time = next_time + timedelta(minutes=5)
    return result

@lru_cache(maxsize=65535)
def fetch_timeseries_data_cached(sensor: SensorData, start_time=None, end_time=None):
    assert SensorData(sensor.value) == sensor
    table, column = sensor.value.split('.')
    query = f"""
        SELECT
            timestamp,
            {column}
        FROM {table}
        WHERE 1=1
    """
    params = []
    if start_time:
        query += " AND timestamp >= ?"
        params.append(start_time)
    if end_time:
        query += " AND timestamp <= ?"
        params.append(end_time)
    query += " ORDER BY timestamp ASC"

    try:
        with sqlite3.connect(f"file:{os.environ.get('DATABASE_PATH')}?mode=ro", uri=True) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            data = cursor.fetchall()
        return data
    except Exception as e:
        print(f"Error fetching data for {sensor.name}: {str(e)}")
        return [[None, None]]

def plot_data(sensors: list[SensorData], title: str, start_time=None, end_time=None):
    fig = go.Figure()
    for sensor in sensors:
        data = fetch_timeseries_data(sensor, start_time, end_time)
        if len(data) < 1:
            continue
        timestamps, values = zip(*data)
        fig.add_trace(go.Scatter(x=timestamps, y=values, mode='lines', name=sensor.name))
    fig.update_layout(
        title=title,
        xaxis_title='Timestamp',
        yaxis_title='Value',
        template='plotly_dark'
    )
    return pio.to_html(fig, full_html=False)

@app.route('/')
def plot():

    end_time = request.args.get('end_time')
    end_time = datetime.fromisoformat(end_time) if end_time else None
    plot1_html = plot_data([
        SensorData.humidity,
        SensorData.temperature,
    ], title='Temperature and humidity', end_time=end_time)

    plot2_html = plot_data([
        SensorData.radon_st_avg,
        SensorData.radon_lt_avg,
        SensorData.voc
        #SensorData.pressure,
        #SensorData.co2,
    ], title='Radon, VOC', end_time=end_time)

    plot3_html = plot_data([
        SensorData.ACTIVE_POWER_PLUS,
        SensorData.ACTIVE_POWER_MINUS,
        SensorData.REACTIVE_POWER_PLUS,
        SensorData.REACTIVE_POWER_MINUS,
        SensorData.CURRENT_PHASE_L1,
        SensorData.CURRENT_PHASE_L2,
        SensorData.CURRENT_PHASE_L3,
        SensorData.VOLTAGE_PHASE_L1,
        SensorData.VOLTAGE_PHASE_L2,
        SensorData.VOLTAGE_PHASE_L3,
        #SensorData.Cumulative_hourly_active_import_kWh,
        #SensorData.Cumulative_hourly_active_export_kWh,
        #SensorData.Cumulative_hourly_reactive_import_kVArh,
        #SensorData.Cumulative_hourly_active_export_kVArh
    ], title='HAN', end_time=end_time)

    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Interactive Timeseries Plot</title>
        </head>
        <body style="background: rgb(17, 17, 17);">
            {{ plot1_html|safe }}
            {{ plot2_html|safe }}
            {{ plot3_html|safe }}
        </body>
        </html>
    ''',
        plot1_html=plot1_html,
        plot2_html=plot2_html,
        plot3_html=plot3_html,
    )

@app.route('/data')
def data():
    sensor_name = request.args.get('sensor')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')

    if not sensor_name or sensor_name != SensorData[sensor_name].name:
        return jsonify({"error": "Invalid sensor name"}), 400

    sensor = SensorData[sensor_name]
    data = fetch_timeseries_data(
        sensor,
        datetime.fromisoformat(start_time) if start_time else None,
        datetime.fromisoformat(end_time) if end_time else None
    )
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)

def start_server():
    from gunicorn.app.wsgiapp import run
    run(app)
