# arduino_reader.py

import os
import threading
import time
import requests
from datetime import datetime, timedelta
from sqlalchemy import text
from app.database import SessionLocal
from app.devices.models import DeviceIot
from app.devices_request.models import Request

PORT          = os.getenv("PORT", "8000")
SERVO_CMD_URL = f"http://localhost:{PORT}/devices/devices/servo-command"

VALVE_TYPE_ID = 2
OFFSET_HOURS  = -5

def device_status_scheduler() -> None:
    print("[scheduler] hilo iniciado")
    while True:
        db = SessionLocal()
        try:
            now = datetime.utcnow() + timedelta(hours=OFFSET_HOURS)

            # 1) Sin solicitud activa → 12 (No operativo)
            for dev in db.query(DeviceIot).filter(DeviceIot.devices_id == VALVE_TYPE_ID):
                active = db.execute(text("""
                    SELECT 1
                      FROM request
                     WHERE device_iot_id = :dev_id
                       AND status = 17
                       AND :now BETWEEN open_date AND close_date
                     LIMIT 1
                """), {"dev_id": dev.id, "now": now}).first()
                if not active and dev.status != 12:
                    dev.status = 12
                    print(f"[scheduler] {dev.id} → 12 (sin solicitud)")

            # 2) Cierre vencido → siempre enviamos "close"
            rows = db.execute(text("""
                SELECT r.device_iot_id, r.close_date, r.open_date
                  FROM request r
                  JOIN (
                      SELECT MAX(id) max_id
                        FROM request
                       WHERE status = 17
                       GROUP BY device_iot_id
                  ) x ON r.id = x.max_id
                 WHERE r.close_date < :now
            """), {"now": now}).fetchall()

            for dev_id, cdate, odate in rows:
                dev = db.query(DeviceIot).get(dev_id)
                if not dev:
                    continue
                if dev.status != 12:
                    dev.status = 21
                    print(f"[scheduler] {dev.id} expiró close_date {cdate} → 21")
                    try:
                        requests.post(SERVO_CMD_URL, json={"action": "close"}, timeout=2)
                        print(f"[scheduler] POST close a servo-command para dev {dev.id}")
                    except requests.RequestException as e:
                        print("[scheduler] POST close:", e)

            # 3) Apertura vigente → 22 + open
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
                if dev and dev.status not in (22, 21):
                    dev.status = 22
                    print(f"[scheduler] {dev.id} apertura {odate} → 22")
                    try:
                        requests.post(SERVO_CMD_URL, json={"action": "open"}, timeout=2)
                    except requests.RequestException as e:
                        print("[scheduler] POST open:", e)

            # 4) Solicitud futura → 20 (En espera)
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
                if dev and dev.status not in (22, 21):
                    dev.status = 20
                    print(f"[scheduler] {dev.id} espera {next_open} → 20")

            db.commit()

        except Exception as e:
            db.rollback()
            print("[scheduler] Error:", e)
        finally:
            db.close()

        time.sleep(5)

def start_background_jobs() -> None:
    threading.Thread(target=device_status_scheduler, daemon=True).start()
