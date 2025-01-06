import sqlite3
import sys
import time
from datetime import datetime, timezone
import logging
import serial

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_stream(stream):
    timestamp = datetime.now(timezone.utc)
    data = {
        'timestamp': timestamp.replace(microsecond=0, second=timestamp.second - timestamp.second % 5),
    }
    for part in stream.split(b'\x09\x06'):
        match list(part):
            case [1, 1, 0, 2, 129, 255, *rest]:
                data['OBIS_List_version'] = int.from_bytes(bytes(rest[2:]))
            case [1, 1, 0, 0, 5, 255, *rest]:
                data['METER_ID'] = int.from_bytes(bytes(rest[2:]))
            case [1, 1, 96, 1, 1, 255, *rest]:
                data['METER_TYPE'] = bytes(rest[2:])
            case [1, 1, 1, 7, 0, 255, *rest]:
                data['ACTIVE_POWER_PLUS'] = int.from_bytes(bytes(rest[-2:]))
            case [1, 1, 2, 7, 0, 255, *rest]:
                data['ACTIVE_POWER_MINUS'] = int.from_bytes(bytes(rest[-2:]))
            case [1, 1, 3, 7, 0, 255, *rest]:
                data['REACTIVE_POWER_PLUS'] = int.from_bytes(bytes(rest[-2:]))
            case [1, 1, 4, 7, 0, 255, *rest]:
                data['REACTIVE_POWER_MINUS'] = int.from_bytes(bytes(rest[-2:]))
            case [1, 1, 31, 7, 0, 255, *rest]:
                data['CURRENT_PHASE_L1'] = int.from_bytes(bytes(rest[-2:]))
            case [1, 1, 51, 7, 0, 255, *rest]:
                data['CURRENT_PHASE_L2'] = int.from_bytes(bytes(rest[-2:]))
            case [1, 1, 71, 7, 0, 255, *rest]:
                data['CURRENT_PHASE_L3'] = int.from_bytes(bytes(rest[-2:]))
            case [1, 1, 32, 7, 0, 255, *rest]:
                data['VOLTAGE_PHASE_L1'] = int.from_bytes(bytes(rest[-2:]))
            case [1, 1, 52, 7, 0, 255, *rest]:
                data['VOLTAGE_PHASE_L2'] = int.from_bytes(bytes(rest[-2:]))
            case [1, 1, 72, 7, 0, 255, *rest]:
                data['VOLTAGE_PHASE_L3'] = int.from_bytes(bytes(rest[-2:]))
            case [0, 1, 1, 0, 0, 255, *rest]:
                data['Clock_and_date'] = bytes(rest)
            case [1, 1, 1, 8, 0, 255, *rest]:
                data['Cumulative_hourly_active_import_kWh'] = int.from_bytes(bytes(rest[2:]))
            case [1, 1, 2, 8, 0, 255, *rest]:
                data['Cumulative_hourly_active_export_kWh'] = int.from_bytes(bytes(rest[2:]))
            case [1, 1, 3, 8, 0, 255, *rest]:
                data['Cumulative_hourly_reactive_import_kVArh'] = int.from_bytes(bytes(rest[2:]))
            case [1, 1, 4, 8, 0, 255, *rest]:
                data['Cumulative_hourly_active_export_kVArh'] = bytes(rest)

    return data

def store_data(data, database):
    table = 'kamstrup_1hour' if data['timestamp'].second % 10 == 5 else 'kamstrup_10sec'
    with sqlite3.connect(database) as conn:
        logger.debug(f"Connected to database {database}.")
        cursor = conn.cursor()
        # Create table if it does not exist
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table} (
                timestamp TIMESTAMP PRIMARY KEY,
                ACTIVE_POWER_PLUS INTEGER,
                ACTIVE_POWER_MINUS INTEGER,
                REACTIVE_POWER_PLUS INTEGER,
                REACTIVE_POWER_MINUS INTEGER,
                CURRENT_PHASE_L1 INTEGER,
                CURRENT_PHASE_L2 INTEGER,
                CURRENT_PHASE_L3 INTEGER,
                VOLTAGE_PHASE_L1 INTEGER,
                VOLTAGE_PHASE_L2 INTEGER,
                VOLTAGE_PHASE_L3 INTEGER,
                Cumulative_hourly_active_import_kWh INTEGER,
                Cumulative_hourly_active_export_kWh INTEGER,
                Cumulative_hourly_reactive_import_kVArh INTEGER,
                Cumulative_hourly_active_export_kVArh VARCHAR(255)
            )
        """)
        # Insert data into table
        cursor.execute(f"""
            INSERT INTO {table} (
                timestamp,
                ACTIVE_POWER_PLUS,
                ACTIVE_POWER_MINUS,
                REACTIVE_POWER_PLUS,
                REACTIVE_POWER_MINUS,
                CURRENT_PHASE_L1,
                CURRENT_PHASE_L2,
                CURRENT_PHASE_L3,
                VOLTAGE_PHASE_L1,
                VOLTAGE_PHASE_L2,
                VOLTAGE_PHASE_L3,
                Cumulative_hourly_active_import_kWh,
                Cumulative_hourly_active_export_kWh,
                Cumulative_hourly_reactive_import_kVArh,
                Cumulative_hourly_active_export_kVArh
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('timestamp'),
            data.get('ACTIVE_POWER_PLUS'),
            data.get('ACTIVE_POWER_MINUS'),
            data.get('REACTIVE_POWER_PLUS'),
            data.get('REACTIVE_POWER_MINUS'),
            data.get('CURRENT_PHASE_L1'),
            data.get('CURRENT_PHASE_L2'),
            data.get('CURRENT_PHASE_L3'),
            data.get('VOLTAGE_PHASE_L1'),
            data.get('VOLTAGE_PHASE_L2'),
            data.get('VOLTAGE_PHASE_L3'),
            data.get('Cumulative_hourly_active_import_kWh'),
            data.get('Cumulative_hourly_active_export_kWh'),
            data.get('Cumulative_hourly_reactive_import_kVArh'),
            data.get('Cumulative_hourly_active_export_kVArh')
        ))
        conn.commit()
        logger.debug("Data stored in database.")
    logger.debug("Disconnected from database.")

def main():
    database = sys.argv[1]
    attempts = 100
    retry_count = 0
    one_time_message = f"Started writing data to {database}. Press Ctrl+C to stop."
    serial_port = serial.Serial(port='/dev/ttyUSB0', baudrate=2400, timeout=5, parity='N')
    while True:
        try:
            time.sleep(5 - datetime.now().second % 5)
            if serial_port is None:
                logger.debug("Connecting to device.")
                serial_port = serial.Serial(port='/dev/ttyUSB0', baudrate=2400, timeout=5, parity='N')
            data = parse_stream(serial_port.read_until(b'Kamstrup_V0001'))
            logger.debug("Read sensor data.")
            if len(data) == 0:
                logger.warning("No data read from sensor.")
                continue
            store_data(data, database)
            if retry_count > 0:
                logger.info("Connection re-established.")
                retry_count = 0
            if one_time_message:
                logger.info(one_time_message)
                one_time_message = None
        except Exception as e:
            retry_count += 1
            logger.error("Connection failed.", exc_info=not isinstance(e, (TimeoutError, serial.serialutil.SerialException)))
            if retry_count > attempts / 2:
                try:
                    if serial_port is not None:
                        logger.warning("Closing connection.")
                        serial_port.close()
                    serial_port = None
                except Exception as e:
                    logger.error("Failed to close connection.", exc_info=True)
            if retry_count <= attempts:
                logger.info(f"Retrying connection. Attempt {retry_count} of {attempts}.")
            else:
                logger.info(f"last known data: {data}")
                logger.critical("Failed too many times.", exc_info=True)
                raise

if __name__ == "__main__":
    main()
