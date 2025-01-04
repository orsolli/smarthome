from enum import Enum
from flask import Flask, render_template_string
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


def fetch_timeseries_data(sensor: SensorData):
    assert SensorData(sensor.name) == sensor
    with sqlite3.connect(f"file:{os.environ.get('DATABASE_PATH')}?mode=ro", uri=True) as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT
                timestamp,
                {sensor.name}
            FROM sensor_data
            ORDER BY timestamp DESC
            LIMIT 1000
        """)
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

if __name__ == "__main__":
    app.run(debug=True)