"""
arduino_reader.py  –  scheduler de estados
────────────────────────────────────────────────────────
• device_status_scheduler()  – mantiene estados   12 / 20 / 11 / 21
• start_background_jobs()    – arranca el hilo en el startup de FastAPI
"""

import os, threading, time, requests
from datetime import datetime
from sqlalchemy import text
from app.database import SessionLocal
from app.devices.models import DeviceIot
from app.devices_request.models import Request

# ─── URL interna del backend ────────────────────────────
PORT = os.getenv("PORT", "8000")   # Render define PORT; local ⇒ 8000
SERVO_CMD_URL = (
    f"http://localhost:{PORT}/devices/devices/servo-command"
)

VALVE_TYPE_ID = 2   # solo para mensajes de control

# ========================================================
def device_status_scheduler():
    print("[scheduler] hilo iniciado")
    while True:
        db = SessionLocal()
        try:
            now = datetime.utcnow()

            # 1) Sin solicitud activa → 12
            for dev in db.query(DeviceIot).all():
                active = db.execute(text("""
                    SELECT 1 FROM request
                     WHERE device_iot_id = :dev
                       AND status = 17
                       AND :now BETWEEN open_date AND close_date
                     LIMIT 1
                """), {"dev": dev.id, "now": now}).first()
                if not active and dev.status != 12:
                    dev.status = 12
                    print(f"[scheduler] {dev.id} → 12 (sin solicitud)")

            # 2) Cierre vencido → 21  + close
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
                if dev and dev.status != 21:
                    dev.status = 21
                    print(f"[scheduler] {dev.id} cierre {cdate} → 21")
                    try:
                        requests.post(SERVO_CMD_URL,
                                      json={"action": "close"},
                                      timeout=2)
                    except requests.RequestException as e:
                        print("[scheduler] POST close:", e)

            # 3) Apertura vigente → 11  + open
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
                if dev and dev.status not in (11, 21, 22):
                    dev.status = 11
                    print(f"[scheduler] {dev.id} apertura {odate} → 11")
                    try:
                        requests.post(SERVO_CMD_URL,
                                      json={"action": "open"},
                                      timeout=2)
                    except requests.RequestException as e:
                        print("[scheduler] POST open:", e)

            # 4) Solicitud futura → 20
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

            for dev_id, odate in rows:
                dev = db.query(DeviceIot).get(dev_id)
                if dev and dev.status not in (11, 21):
                    dev.status = 20
                    print(f"[scheduler] {dev.id} espera {odate} → 20")

            db.commit()

        except Exception as e:
            db.rollback()
            print("[scheduler] Error:", e)
        finally:
            db.close()

        time.sleep(5)

# ========================================================
def start_background_jobs():
    """Lanzar el scheduler desde main.py"""
    threading.Thread(target=device_status_scheduler, daemon=True).start()
