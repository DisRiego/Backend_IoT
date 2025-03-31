# app/arduino_reader.py

import serial
import threading
import time
from app.devices.services import DeviceService  
from app.database import SessionLocal
from app.devices.schemas import DeviceCreate

# Ajusta el puerto según corresponda, por ejemplo "COM4" o '/dev/ttyACM0'
SERIAL_PORT = "COM4"  # Cambia esto al puerto correcto
BAUD_RATE = 9600

def read_serial_data():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Conectado al puerto serial: {SERIAL_PORT}")
    except Exception as e:
        print(f"Error al abrir el puerto serial: {e}")
        return

    while True:
        try:
            line = ser.readline().decode('utf-8').strip()
            if line:
                print("Dato recibido:", line)
                try:
                    sensor_value = int(line)
                except ValueError:
                    sensor_value = 0  # Maneja el error según tu lógica

                db = SessionLocal()
                try:
                    service = DeviceService(db)
                    device_payload = DeviceCreate(sensor_value=sensor_value)
                    service.create_device_data(device_payload)
                    db.commit()
                except Exception as db_e:
                    print(f"Error al insertar en la BD: {db_e}")
                finally:
                    db.close()
        except Exception as e:
            print("Error en la lectura del puerto serial:", e)
        
        time.sleep(0.5)
