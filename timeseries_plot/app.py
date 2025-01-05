from datetime import datetime
from enum import Enum
from flask import Flask, render_template_string, request, jsonify
import sqlite3
import plotly.graph_objs as go
import plotly.io as pio
import os
import sys

app = Flask(__name__)

class SensorData(Enum):
    humidity = 'humidity'
    radon_st_avg = 'radon_st_avg'
    radon_lt_avg = 'radon_lt_avg'
    temperature = 'temperature'
    pressure = 'pressure'
    co2 = 'co2'
    voc = 'voc'

OLD_TIME = datetime.fromisoformat('1970-01-01T00:00:00')
def naive_cache(fetch_timeseries_data):
    def wrapper(sensor: SensorData, start_time=None, end_time=None, cache = {
        'humidity':[{'start_time': OLD_TIME, 'end_time': OLD_TIME, 'data': []}],
        'radon_st_avg':[{'start_time': OLD_TIME, 'end_time': OLD_TIME, 'data': []}],
        'radon_lt_avg':[{'start_time': OLD_TIME, 'end_time': OLD_TIME, 'data': []}],
        'temperature':[{'start_time': OLD_TIME, 'end_time': OLD_TIME, 'data': []}],
        'pressure':[{'start_time': OLD_TIME, 'end_time': OLD_TIME, 'data': []}],
        'co2':[{'start_time': OLD_TIME, 'end_time': OLD_TIME, 'data': []}],
        'voc':[{'start_time': OLD_TIME, 'end_time': OLD_TIME, 'data': []}],
    }):
        try:
            index = -1
            prev_end_time = cache[sensor.value][index]['end_time']
            cutoff_time = max(start_time, prev_end_time)
            if cutoff_time < end_time:
                cache[sensor.value].append({
                    'start_time': cutoff_time,
                    'end_time': end_time,
                    'data': fetch_timeseries_data(sensor, cutoff_time, end_time)
                })
            
            result = cache[sensor.value][index]['data']
            index -= 1
            while cutoff_time > start_time:
                result = cache[sensor.value][index]['data'] + result
                cutoff_time = cache[sensor.value][index]['start_time']
                index -= 1
            cache[sensor.value] = cache[sensor.value][index:]
            return [x for x in result if datetime.fromisoformat(x[0]) >= start_time and datetime.fromisoformat(x[0]) <= end_time]
        except Exception as e:
            print(e, file=sys.stderr)
            result = fetch_timeseries_data(sensor, start_time, end_time)
            cache[sensor.value].append({
                'start_time': start_time,
                'end_time': end_time,
                'data': result
            })
            return result

    return wrapper


@naive_cache
def fetch_timeseries_data(sensor: SensorData, start_time=None, end_time=None):
    assert SensorData(sensor.name) == sensor
    query = f"""
        SELECT
            timestamp,
            {sensor.name}
        FROM sensor_data
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

    with sqlite3.connect(f"file:{os.environ.get('DATABASE_PATH')}?mode=ro", uri=True) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        data = cursor.fetchall()
    return data


@app.route('/')
def plot():
    fig1 = go.Figure()

    for sensor in [
        SensorData.humidity,
        SensorData.temperature,
    ]:
        data = fetch_timeseries_data(sensor)
        timestamps, values = zip(*data)
        fig1.add_trace(go.Scatter(x=timestamps, y=values, mode='lines', name=sensor.name))

    fig1.update_layout(
        title='Temperature and humidity',
        xaxis_title='Timestamp',
        yaxis_title='Value',
        template='plotly_dark'
    )

    plot1_html = pio.to_html(fig1, full_html=False)

    fig2 = go.Figure()

    for sensor in [
        SensorData.radon_st_avg,
        SensorData.radon_lt_avg,
        SensorData.voc
        #SensorData.pressure,
        #SensorData.co2,
    ]:
        data = fetch_timeseries_data(sensor)
        timestamps, values = zip(*data)
        fig2.add_trace(go.Scatter(x=timestamps, y=values, mode='lines', name=sensor.name))

    fig2.update_layout(
        title='Radon, VOC',
        xaxis_title='Timestamp',
        yaxis_title='Value',
        template='plotly_dark'
    )
    plot2_html = pio.to_html(fig2, full_html=False)

    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Interactive Timeseries Plot</title>
        </head>
        <body style="background: rgb(17, 17, 17);">
            {{ plot1_html|safe }}
            {{ plot2_html|safe }}
        </body>
        </html>
    ''', plot1_html=plot1_html, plot2_html=plot2_html)

@app.route('/data')
def data():
    sensor_name = request.args.get('sensor')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')

    if not sensor_name or sensor_name not in SensorData.__members__:
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
