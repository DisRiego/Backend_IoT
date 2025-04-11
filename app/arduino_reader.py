import serial
import threading
import time
import json
import requests
from datetime import datetime
from sqlalchemy import text
from app.devices.services import DeviceService  
from app.database import SessionLocal
from app.devices.schemas import DeviceIotReadingUpdateByLot
from app.devices.models import DeviceIot

SERVO_CMD_URL = "http://localhost:8003/devices/devices/servo-command"

def read_serial_data(ser):
    print("Hilo de lectura del Arduino iniciado.")
    while True:
        try:
            line = ser.readline().decode('utf-8').strip()
            if not line:
                time.sleep(0.5)
                continue

            print("[read] Dato recibido:", line)
            if "\"status\":\"ready\"" in line or line == "Loop tick":
                continue

            try:
                data = json.loads(line)
            except Exception as parse_e:
                print("[read] Error al parsear JSON:", parse_e)
                continue

            try:
                reading = DeviceIotReadingUpdateByLot(**data)
            except Exception as val_e:
                print("[read] Error de validación:", val_e)
                continue

            db = SessionLocal()
            try:
                svc = DeviceService(db)
                svc.update_device_reading_by_lot(reading)
                db.commit()
                print("[read] Lectura guardada en BD.")
            except Exception as db_e:
                print("[read] Error al insertar en la BD:", db_e)
            finally:
                db.close()
        except Exception as e:
            print("[read] Error en la lectura del puerto serial:", e)
        time.sleep(0.5)


def poll_servo_commands(ser):
    print("Hilo de polling de comandos iniciado.")
    while True:
        try:
            resp = requests.get(SERVO_CMD_URL, timeout=5)
            if resp.status_code == 200:
                cmd = resp.json()
                action = cmd.get("action")
                print(f"[poll] Comando recibido del backend: '{action}'")

                if action in ("open", "close"):
                    angle = 180 if action == "open" else 0
                    msg = json.dumps({"angle": angle})
                    print(f"[poll] Enviando al Arduino: {msg}")
                    ser.write((msg + "\n").encode('utf-8'))
                    ser.flush()
                    print("[poll] Mensaje enviado al Arduino.")
                else:
                    print("[poll] No es 'open' ni 'close', no se envía nada.")
            else:
                print(f"[poll] No hay comando válido (HTTP {resp.status_code})")
        except Exception as e:
            print("[poll] Error al obtener comando de servo:", e)

        time.sleep(2)


def device_status_scheduler():
    print("Hilo de scheduler de estado de dispositivos iniciado.")
    while True:
        db = SessionLocal()
        try:
            now_col = datetime.now().replace(tzinfo=None)
            print("[scheduler] Hora Colombia:", now_col.strftime("%Y-%m-%d %H:%M:%S"))

            # 1. Dispositivos sin solicitud activa → No operativo
            all_devices = db.query(DeviceIot).all()
            for device in all_devices:
                req = db.execute(text("""
                    SELECT 1 FROM request
                    WHERE device_iot_id = :device_id
                    AND status = 17
                    AND open_date <= :now AND close_date >= :now
                """), {"device_id": device.id, "now": now_col}).first()

                if not req and device.status != 12:
                    device.status = 12
                    print(f"[scheduler] Dispositivo {device.id} sin solicitud activa → No operativo (12)")

            # 2. Cierre vencido → Estado 21
            cierres = db.execute(text("""
                SELECT r1.device_iot_id, r1.close_date
                FROM request r1
                INNER JOIN (
                    SELECT device_iot_id, MAX(open_date) AS latest_open
                    FROM request
                    WHERE status = 17
                    GROUP BY device_iot_id
                ) r2 ON r1.device_iot_id = r2.device_iot_id AND r1.open_date = r2.latest_open
                WHERE r1.close_date < :now
            """), {"now": now_col}).fetchall()

            for row in cierres:
                device = db.query(DeviceIot).filter(DeviceIot.id == row.device_iot_id).first()
                if device and device.status != 21:
                    print(f"[scheduler] → CIERRE Dispositivo {device.id} | close_date: {row.close_date}")
                    device.status = 21
                    try:
                        resp = requests.post(SERVO_CMD_URL, json={"action": "close"})
                        print("[scheduler] Comando 'close' seteado:", resp.json())
                    except Exception as e:
                        print("[scheduler] Error al setear comando 'close':", e)

            # 3. Apertura en curso → Estado 11
            aperturas = db.execute(text("""
                SELECT r1.device_iot_id, r1.open_date
                FROM request r1
                INNER JOIN (
                    SELECT device_iot_id, MAX(open_date) AS latest_open
                    FROM request
                    WHERE status = 17
                    GROUP BY device_iot_id
                ) r2 ON r1.device_iot_id = r2.device_iot_id AND r1.open_date = r2.latest_open
                WHERE r1.open_date <= :now AND r1.close_date >= :now
            """), {"now": now_col}).fetchall()

            for row in aperturas:
                device = db.query(DeviceIot).filter(DeviceIot.id == row.device_iot_id).first()
                if device and device.status != 11:
                    print(f"[scheduler] → APERTURA Dispositivo {device.id} | open_date: {row.open_date}")
                    device.status = 11
                    try:
                        resp = requests.post(SERVO_CMD_URL, json={"action": "open"})
                        print("[scheduler] Comando 'open' seteado:", resp.json())
                    except Exception as e:
                        print("[scheduler] Error al setear comando 'open':", e)

            # 4. Solicitud aprobada pero fuera de rango → Estado 20 (en espera)
            en_espera = db.execute(text("""
                SELECT r1.device_iot_id, r1.open_date
                FROM request r1
                INNER JOIN (
                    SELECT device_iot_id, MAX(open_date) AS latest_open
                    FROM request
                    WHERE status = 17
                    GROUP BY device_iot_id
                ) r2 ON r1.device_iot_id = r2.device_iot_id AND r1.open_date = r2.latest_open
                WHERE r1.open_date > :now
            """), {"now": now_col}).fetchall()

            for row in en_espera:
                device = db.query(DeviceIot).filter(DeviceIot.id == row.device_iot_id).first()
                if device and device.status not in [11, 21]:
                    print(f"[scheduler] → ESPERA Dispositivo {device.id} | open_date: {row.open_date}")
                    device.status = 20

            db.commit()
        except Exception as e:
            db.rollback()
            print("[scheduler] Error general en scheduler:", e)
        finally:
            db.close()
        time.sleep(5)
