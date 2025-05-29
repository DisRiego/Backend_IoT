# arduino_reader.py

import os
import threading
import time
import requests
from datetime import datetime, timedelta
from sqlalchemy import text
from app.database import SessionLocal
from app.devices.models import DeviceIot

PORT          = os.getenv("PORT", "8003")
SERVO_CMD_URL = f"http://localhost:{PORT}/devices/devices/servo-command"
VALVE_TYPE_ID = 2


def device_status_scheduler() -> None:
    print("[scheduler] hilo iniciado")
    while True:
        db = SessionLocal()
        try:
            now = datetime.now()

            # 1) CIERRE EXPIRADO → cerrar + status 12 (No Operativo)
            rows = db.execute(text("""
                SELECT r.device_iot_id, r.close_date
                  FROM request r
                  JOIN (
                      SELECT MAX(id) max_id
                        FROM request
                       WHERE status = 17
                       GROUP BY device_iot_id
                  ) x ON r.id = x.max_id
                 WHERE r.close_date < :now
            """), {"now": now}).fetchall()

            for dev_id, cdate in rows:
                dev = db.query(DeviceIot).get(dev_id)
                if not dev:
                    continue
                if dev.status != 12:
                    # Cambiamos directamente a No Operativo
                    dev.status = 12
                    print(f"[scheduler] {dev.id} expiró close_date {cdate} → 12 (No Operativo)")
                    try:
                        requests.post(SERVO_CMD_URL, json={"action": "close"}, timeout=2)
                        print(f"[scheduler] POST close al ESP32 para dev {dev.id}")
                    except requests.RequestException as e:
                        print("[scheduler] POST close error:", e)

            # 2) APERTURA VIGENTE → solo desde 20 a 22 (abierta)
            rows = db.execute(text("""
                SELECT r.device_iot_id, r.open_date
                  FROM request r
                  JOIN (
                      SELECT MAX(id) max_id
                        FROM request
                       WHERE status = 17
                       GROUP BY device_iot_id
                  ) x ON r.id = x.max_id
                 WHERE :now BETWEEN r.open_date AND r.close_date
            """), {"now": now}).fetchall()

            for dev_id, odate in rows:
                dev = db.query(DeviceIot).get(dev_id)
                if dev and dev.status == 20:
                    dev.status = 22
                    print(f"[scheduler] {dev.id} apertura {odate} → 22 (Abierta)")
                    try:
                        requests.post(SERVO_CMD_URL, json={"action": "open"}, timeout=2)
                        print(f"[scheduler] POST open al ESP32 para dev {dev.id}")
                    except requests.RequestException as e:
                        print("[scheduler] POST open error:", e)

            # 3) SOLICITUD FUTURA → status 20 (En espera)
            rows = db.execute(text("""
                SELECT r.device_iot_id, r.open_date
                  FROM request r
                  JOIN (
                      SELECT MAX(id) max_id
                        FROM request
                       WHERE status = 17
                       GROUP BY device_iot_id
                  ) x ON r.id = x.max_id
                 WHERE r.open_date > :now
            """), {"now": now}).fetchall()

            for dev_id, next_open in rows:
                dev = db.query(DeviceIot).get(dev_id)
                if dev and dev.status not in (21, 22):
                    dev.status = 20
                    print(f"[scheduler] {dev.id} próxima apertura {next_open} → 20 (En espera)")

            # 4) SIN NINGUNA SOLICITUD → status 12 (No Operativo)
            for dev in db.query(DeviceIot).filter(DeviceIot.devices_id == VALVE_TYPE_ID):
                # si no hay ninguna solicitud aprobada
                any_req = db.execute(text("""
                    SELECT 1 FROM request
                     WHERE device_iot_id = :dev_id
                       AND status = 17
                   LIMIT 1
                """), {"dev_id": dev.id}).first()
                if not any_req and dev.status != 12:
                    dev.status = 12
                    print(f"[scheduler] {dev.id} → 12 (No Operativo, sin solicitudes)")

            db.commit()

        except Exception as e:
            db.rollback()
            print("[scheduler] Error:", e)
        finally:
            db.close()

        time.sleep(5)

def start_background_jobs() -> None:
    threading.Thread(target=device_status_scheduler, daemon=True).start()
