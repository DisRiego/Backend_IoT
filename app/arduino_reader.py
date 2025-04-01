import serial
import threading
import time
import json
from app.devices.services import DeviceService  
from app.database import SessionLocal
from app.devices.schemas import DeviceIotReadingUpdateByLot

SERIAL_PORT = "COM4" 
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
                    # Parsear el JSON enviado por Arduino
                    data = json.loads(line)
                except Exception as parse_e:
                    print("Error al parsear JSON:", parse_e)
                    data = {}

                # Se espera que el JSON tenga device_type_id y sensor_value
                try:
                    sensor_data = DeviceIotReadingUpdateByLot(**data)
                except Exception as val_e:
                    print(f"Error de validación: {val_e}")
                    sensor_data = None

                if sensor_data:
                    db = SessionLocal()
                    try:
                        service = DeviceService(db)
                        service.update_device_reading_by_lot(sensor_data)
                        db.commit()
                    except Exception as db_e:
                        print(f"Error al insertar en la BD: {db_e}")
                    finally:
                        db.close()
        except Exception as e:
            print("Error en la lectura del puerto serial:", e)
        
        time.sleep(0.5)
        
if __name__ == '__main__':
    read_serial_data()
