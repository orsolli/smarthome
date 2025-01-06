# MIT License
#
# Copyright (c) 2018 Airthings AS
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# https://airthings.com

# ===============================
# Module import dependencies
# ===============================

import asyncio
from bleak import BleakClient
import sqlite3
import sys
import time
import struct
from datetime import datetime, timezone
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===============================
# Class WavePlus
# ===============================

class WavePlus:
    def __init__(self, serial_number):
        self.periph = None
        self.curr_val_char = None
        self.mac_addr = None
        self.sn = serial_number
        self.uuid = "b42e2a68-ade7-11e4-89d3-123b93f75cba"
        self.prev_rawdata = None

    async def discover(self):
        if self.mac_addr is None:
            from bluepy.btle import Scanner, DefaultDelegate
            scanner = Scanner().withDelegate(DefaultDelegate())
            search_count = 0
            while self.mac_addr is None and search_count < 50:
                devices = scanner.scan(0.1)
                search_count += 1
                for dev in devices:
                    manu_data = dev.getValueText(255)
                    sn = self.parse_serial_number(manu_data)
                    if sn == self.sn:
                        self.mac_addr = dev.addr # exits the while loop on next conditional check
                        break # exit for loop
            if self.mac_addr is None:
                logger.error("Could not find device.")
                logger.info("GUIDE: (1) Please verify the serial number.")
                logger.info("       (2) Ensure that the device is advertising.")
                logger.info("       (3) Retry connection.")
                sys.exit(1)

    def parse_serial_number(self, manu_data_hex_str):
        if manu_data_hex_str is None or manu_data_hex_str == "None":
            return "Unknown"
        manu_data = bytearray.fromhex(manu_data_hex_str)
        if ((manu_data[1] << 8) | manu_data[0]) == 0x0334:
            sn = manu_data[2]
            sn |= (manu_data[3] << 8)
            sn |= (manu_data[4] << 16)
            sn |= (manu_data[5] << 24)
            return sn
        return "Unknown"

    async def read(self):
        async with BleakClient(self.mac_addr) as client:
            return await client.read_gatt_char(self.uuid)

    def get_sensor_data(self, compare=False):
        rawdata = asyncio.run(self.read())
        unpackeddata = struct.unpack('<BBBBHHHHHHHH', rawdata)
        sensors = Sensors()
        sensors.set(unpackeddata)
        if compare:
            prev_data = self.prev_rawdata
            self.prev_rawdata = rawdata
            return sensors, rawdata == prev_data
        return sensors


# ===================================
# Class Sensor and sensor definitions
# ===================================

NUMBER_OF_SENSORS               = 7
SENSOR_IDX_HUMIDITY             = 0
SENSOR_IDX_RADON_SHORT_TERM_AVG = 1
SENSOR_IDX_RADON_LONG_TERM_AVG  = 2
SENSOR_IDX_TEMPERATURE          = 3
SENSOR_IDX_REL_ATM_PRESSURE     = 4
SENSOR_IDX_CO2_LVL              = 5
SENSOR_IDX_VOC_LVL              = 6

class Sensors:
    def __init__(self):
        self.sensor_version = None
        self.sensor_data = [None] * NUMBER_OF_SENSORS
        self.sensor_units = ["%rH", "Bq/m3", "Bq/m3", "degC", "hPa", "ppm", "ppb"]

    def set(self, raw_data):
        self.sensor_version = raw_data[0]
        if self.sensor_version == 1:
            self.sensor_data[SENSOR_IDX_HUMIDITY] = raw_data[1] / 2.0
            self.sensor_data[SENSOR_IDX_RADON_SHORT_TERM_AVG] = self.conv2radon(raw_data[4])
            self.sensor_data[SENSOR_IDX_RADON_LONG_TERM_AVG] = self.conv2radon(raw_data[5])
            self.sensor_data[SENSOR_IDX_TEMPERATURE] = raw_data[6] / 100.0
            self.sensor_data[SENSOR_IDX_REL_ATM_PRESSURE] = raw_data[7] / 50.0
            self.sensor_data[SENSOR_IDX_CO2_LVL] = raw_data[8]
            self.sensor_data[SENSOR_IDX_VOC_LVL] = raw_data[9]
        else:
            logger.error("Unknown sensor version.")
            sys.exit(1)

    def conv2radon(self, radon_raw):
        if 0 <= radon_raw <= 16383:
            return radon_raw
        logger.error(f"Radon value out of range. {radon_raw}")
        return "N/A"

def store_data(data, database):
    with sqlite3.connect(database) as conn:
        logger.debug(f"Connected to database {database}.")
        cursor = conn.cursor()
        # Create table if it does not exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensor_data (
                timestamp TIMESTAMP PRIMARY KEY,
                humidity REAL,
                radon_st_avg INTEGER,
                radon_lt_avg INTEGER,
                temperature REAL,
                pressure REAL,
                co2 INTEGER,
                voc INTEGER
            )
        """)
        # Insert data into table
        cursor.execute("""
            INSERT INTO sensor_data (timestamp, humidity, radon_st_avg, radon_lt_avg, temperature, pressure, co2, voc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (data['timestamp'], data['humidity'], data['radon_st_avg'], data['radon_lt_avg'], data['temperature'], data['pressure'], data['co2'], data['voc']))
        conn.commit()
        logger.debug("Data stored in database.")
    logger.debug("Disconnected from database.")

def main():
    # ===============================
    # Script guards for correct usage
    # ===============================
    help_message = "USAGE: read_waveplus.py SN|MAC_ADDR SAMPLE-PERIOD DATABASE\n" \
        "    where SN is the 10-digit serial number found under the magnetic backplate of your Wave Plus.\n" \
        "    where MAC_ADDR removes the neccesity to scan for the device using SN.\n" \
        "    where SAMPLE-PERIOD is the time in seconds between reading the current values.\n" \
        "    where DATABASE is the path to the SQLite file to store the values.\n" \
        "EXAMPLE: read_waveplus.py 1234567890 300 ./airwave_data.db"
    if len(sys.argv) < 4:
        logger.error("Missing input argument SN|MAC_ADDR or SAMPLE-PERIOD or DATABASE.")
        logger.info(help_message)
        sys.exit(1)

    if sys.argv[2].isdigit() is not True or int(sys.argv[2])<0:
        logger.error("Invalid SAMPLE-PERIOD. Must be a numerical value larger than zero.")
        logger.info(help_message)
        sys.exit(1)

    database = sys.argv[3]
    sample_period = int(sys.argv[2])
    serial_number = None
    mac_addr = None
    if sys.argv[1].isdigit() and len(sys.argv[1]) == 10:
        serial_number = int(sys.argv[1])
    else:
        mac_addr = sys.argv[1]
        if mac_addr is not None:
            if len(mac_addr) != 17:
                logger.error("Invalid MAC_ADDR. Must be a 17-character long string.")
                logger.info(help_message)
                sys.exit(1)
            if mac_addr[2::3] != ":" * 5:
                logger.error("Invalid MAC_ADDR. Must be a 17-character long string with ':' as separators.")
                logger.info(help_message)
                sys.exit(1)

    waveplus = WavePlus(serial_number)
    waveplus.mac_addr = mac_addr
    retry_count = 0
    one_time_message = f"Started writing data to {database} every {sample_period} seconds. Press Ctrl+C to stop."
    while True:
        try:
            if one_time_message is None:
                time.sleep(sample_period)
            logger.debug("Connecting to device.")
            sensors, unchanged = waveplus.get_sensor_data(compare=True)
            logger.debug("Read sensor data.")
            if unchanged and retry_count == 0 and one_time_message is None:
                logger.debug("Sensor data unchanged.")
                continue
            data = {
                'timestamp': datetime.now(timezone.utc),
                'humidity': sensors.sensor_data[SENSOR_IDX_HUMIDITY],
                'radon_st_avg': sensors.sensor_data[SENSOR_IDX_RADON_SHORT_TERM_AVG],
                'radon_lt_avg': sensors.sensor_data[SENSOR_IDX_RADON_LONG_TERM_AVG],
                'temperature': sensors.sensor_data[SENSOR_IDX_TEMPERATURE],
                'pressure': sensors.sensor_data[SENSOR_IDX_REL_ATM_PRESSURE],
                'co2': sensors.sensor_data[SENSOR_IDX_CO2_LVL],
                'voc': sensors.sensor_data[SENSOR_IDX_VOC_LVL]
            }
            store_data(data, database)
            if retry_count > 0:
                logger.info("Connection re-established.")
                retry_count = 0
            if one_time_message:
                logger.info(one_time_message)
                one_time_message = None
        except Exception as e:
            retry_count += 1
            logger.error("Connection failed.", exc_info=not isinstance(e, (TimeoutError, BrokenPipeError)))
            if retry_count <= 10:
                logger.info(f"Retrying connection. Attempt {retry_count} of 10.")
            else:
                logger.critical("Failed too many times.", exc_info=True)
                raise

if __name__ == "__main__":
    main()
