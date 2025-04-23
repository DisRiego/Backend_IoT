"""
arduino_reader.py  –  Versión 100 % Wi-Fi
—————————————————————————————————————————————————
 •  device_status_scheduler()        (igual que antes)
 •  registrar_volumen_final()        (ahora sin IDs quemados)
—————————————————————————————————————————————————
"""
import threading
import time
import requests
from datetime import datetime
from sqlalchemy import text
from app.database import SessionLocal
from app.devices.models import DeviceIot, ConsumptionMeasurement
from app.devices_request.models import Request

# Ajusta si tu FastAPI no corre en localhost:8004
SERVO_CMD_URL = "http://localhost:8003/devices/devices/servo-command"

# IDs en la tabla DeviceType  (cámbialos si difieren)
VALVE_TYPE_ID  = 2          # válvula
METER_TYPE_ID  = 1          # medidor

# ----------------------------------------------------------------------
# 1.  JOB: Scheduler de estados  (sin cambios de lógica)
# ----------------------------------------------------------------------
def device_status_scheduler():
    print("[scheduler] Hilo iniciado …")
    while True:
        db = SessionLocal()
        try:
            now = datetime.now().replace(tzinfo=None)

            # --- 1) Sin solicitud activa  -> 12
            for dev in db.query(DeviceIot).all():
                active = db.execute(text("""
                    SELECT 1
                      FROM request
                     WHERE device_iot_id = :d
                       AND status = 17
                       AND :now BETWEEN open_date AND close_date
                     LIMIT 1
                """), {"d": dev.id, "now": now}).first()
                if not active and dev.status != 12:
                    dev.status = 12
                    print(f"[scheduler] {dev.id} → 12 (sin solicitud)")

            # --- 2) Cierre vencido  -> 21  + CLOSE
            rows = db.execute(text("""
                SELECT r1.device_iot_id, r1.close_date
                  FROM request r1
                  JOIN (
                        SELECT MAX(id) AS max_id
                          FROM request
                         WHERE status = 17
                         GROUP BY device_iot_id
                       ) r2 ON r1.id = r2.max_id
                 WHERE r1.close_date < :now
            """), {"now": now}).fetchall()

            for dev_id, cdate in rows:
                dev = db.query(DeviceIot).get(dev_id)
                if dev and dev.status != 21:
                    dev.status = 21
                    print(f"[scheduler] {dev.id} cierre {cdate} → 21")
                    try:
                        requests.post(SERVO_CMD_URL, json={"action": "close"})
                    except Exception as e:
                        print("[scheduler] POST close:", e)

            # --- 3) Apertura vigente  -> 11  + OPEN
            rows = db.execute(text("""
                SELECT r1.device_iot_id, r1.open_date
                  FROM request r1
                  JOIN (
                        SELECT MAX(id) AS max_id
                          FROM request
                         WHERE status = 17
                         GROUP BY device_iot_id
                       ) r2 ON r1.id = r2.max_id
                 WHERE :now BETWEEN r1.open_date AND r1.close_date
            """), {"now": now}).fetchall()

            for dev_id, odate in rows:
                dev = db.query(DeviceIot).get(dev_id)
                if dev and dev.status not in (11, 21, 22):
                    dev.status = 11
                    print(f"[scheduler] {dev.id} apertura {odate} → 11")
                    try:
                        requests.post(SERVO_CMD_URL, json={"action": "open"})
                    except Exception as e:
                        print("[scheduler] POST open:", e)

            # --- 4) Solicitud futura  -> 20
            rows = db.execute(text("""
                SELECT r1.device_iot_id, r1.open_date
                  FROM request r1
                  JOIN (
                        SELECT MAX(id) AS max_id
                          FROM request
                         WHERE status = 17
                         GROUP BY device_iot_id
                       ) r2 ON r1.id = r2.max_id
                 WHERE r1.open_date > :now
            """), {"now": now}).fetchall()

            for dev_id, odate in rows:
                dev = db.query(DeviceIot).get(dev_id)
                if dev and dev.status not in (11, 21):
                    dev.status = 20
                    print(f"[scheduler] {dev.id} en espera {odate} → 20")

            db.commit()
        except Exception as e:
            db.rollback()
            print("[scheduler] Error:", e)
        finally:
            db.close()

        time.sleep(5)

# ----------------------------------------------------------------------
# 2.  JOB: Registrar volumen final  (ids dinámicos)
# ----------------------------------------------------------------------
def registrar_volumen_final():
    db = SessionLocal()
    try:
        now = datetime.now()

        # ── 1) Todas las solicitudes aprobadas, ya cerradas,
        #      vinculadas a un dispositivo de tipo "válvula",
        #      sin medición registrada aún.
        rows = db.execute(text("""
            SELECT r.id,
                   r.lot_id,
                   r.open_date,
                   r.close_date
              FROM request r
              JOIN device_iot d ON d.id = r.device_iot_id
             WHERE d.devices_id = :valve_type
               AND r.status     = 17
               AND r.close_date < :now
               AND NOT EXISTS (
                     SELECT 1 FROM consumption_measurements cm
                      WHERE cm.request_id = r.id)
        """), {"valve_type": VALVE_TYPE_ID, "now": now}).fetchall()

        for req_id, lot_id, open_d, close_d in rows:

            # ── 2) Todos los medidores del mismo lote
            meter_ids = db.execute(text("""
                SELECT id
                  FROM device_iot
                 WHERE lot_id = :lot
                   AND devices_id = :meter_type
            """), {"lot": lot_id, "meter_type": METER_TYPE_ID}).fetchall()

            if not meter_ids:
                print(f"[volumen] Lote {lot_id}: sin medidor; omitiendo.")
                continue

            id_tuple = tuple(x[0] for x in meter_ids)   # (id1,id2,…)

            # ── 3) Sumar litros leídos por esos medidores
            total = db.execute(text(f"""
                SELECT COALESCE(SUM(volume_liters),0)
                  FROM device_iot_reading
                 WHERE device_id IN :meters
                   AND timestamp BETWEEN :op AND :cl
            """), {"meters": id_tuple, "op": open_d, "cl": close_d}).scalar()

            db.add(ConsumptionMeasurement(
                request_id   = req_id,
                final_volume = total
            ))
            db.commit()
            print(f"[volumen] Request {req_id} → {total:.2f} L")
    except Exception as e:
        db.rollback()
        print("[volumen] Error:", e)
    finally:
        db.close()

# ----------------------------------------------------------------------
# 3.  Lanzar hilos
# ----------------------------------------------------------------------
if __name__ == "__main__":
    threading.Thread(target=device_status_scheduler, daemon=True).start()

    # Ejecutar registrar_volumen_final() cada hora
    while True:
        registrar_volumen_final()
        time.sleep(3600)
