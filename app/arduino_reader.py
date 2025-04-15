import serial
import threading
import time
import json
import requests
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from app.devices.services import DeviceService  
from app.database import SessionLocal
from app.devices.schemas import DeviceIotReadingUpdateByLot
from app.devices.models import DeviceIot, ConsumptionMeasurement
from app.devices_request.models import Request

SERVO_CMD_URL = "http://localhost:8004/devices/devices/servo-command"

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

            # Procesamiento para el medidor
            if data["device_type_id"] == 1:  # Medidor
                lot_id = data["lot_id"]
                final_volume = data.get("final_volume", None)
                if final_volume is not None:
                    print(f"[final_volume] Medidor reporta volumen final: {final_volume}")
                    db = SessionLocal()
                    try:
                        # Se busca la solicitud aprobada (estado 17) más reciente para ese lote.
                        # Si el modelo Request tiene un campo que identifique al dispositivo de la válvula (por ejemplo, device_iot_id),
                        # se podría agregar ese filtro para mayor precisión.
                        request = (db.query(Request)
                                   .filter_by(lot_id=lot_id, status=17)
                                   .order_by(Request.id.desc())  # Se ordena de forma descendente para obtener el último request.
                                   .first())
                        if request:
                            reading = DeviceIotReadingUpdateByLot(**data)
                            svc = DeviceService(db)
                            svc.update_device_reading_by_lot(reading)
                            db.commit()
                            print(f"[read] Lectura de medidor guardada en BD para Request {request.id}.")
                        else:
                            print(f"[final_volume] No se encontró solicitud aprobada para la válvula con lot_id={lot_id}")
                    except Exception as db_e:
                        print("[read] Error al insertar en la BD:", db_e)
                    finally:
                        db.close()

            # Procesamiento para la válvula
            elif data["device_type_id"] == 2:  # Válvula
                valve_status = data.get("valve_status", None)
                if valve_status:
                    print(f"[valve_status] Válvula estado: {valve_status}")
                    db = SessionLocal()
                    try:
                        # Se busca la solicitud aprobada (estado 17) más reciente para el lote.
                        # Si fuera necesario, agregar un filtro extra (por ejemplo, device_iot_id) para identificar la válvula.
                        request = (db.query(Request)
                                   .filter_by(lot_id=data["lot_id"], status=17)
                                   .order_by(Request.id.desc())
                                   .first())
                        if request:
                            reading = DeviceIotReadingUpdateByLot(**data)
                            svc = DeviceService(db)
                            svc.update_device_reading_by_lot(reading)
                            db.commit()
                            print(f"[read] Lectura de válvula guardada en BD para Request {request.id}.")
                        else:
                            print(f"[valve_status] No se encontró solicitud aprobada para válvula con lot_id={data['lot_id']}")
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
                    SELECT 1 FROM request r1
                    INNER JOIN (
                        SELECT MAX(id) AS max_id
                        FROM request
                        WHERE device_iot_id = :device_id AND status = 17
                    ) r2 ON r1.id = r2.max_id
                    WHERE r1.open_date <= :now AND r1.close_date >= :now
                """), {"device_id": device.id, "now": now_col}).first()

                if not req and device.status != 12:
                    device.status = 12  # Cambia el estado a 'No operativo'
                    print(f"[scheduler] Dispositivo {device.id} sin solicitud activa → No operativo (12)")

            # 2. Cierre vencido → Estado 21
            cierres = db.execute(text("""
                SELECT r1.device_iot_id, r1.close_date
                FROM request r1
                INNER JOIN (
                    SELECT MAX(id) AS max_id
                    FROM request
                    WHERE status = 17
                    GROUP BY device_iot_id
                ) r2 ON r1.id = r2.max_id
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
                    SELECT MAX(id) AS max_id
                    FROM request
                    WHERE status = 17
                    GROUP BY device_iot_id
                ) r2 ON r1.id = r2.max_id
                WHERE r1.open_date <= :now AND r1.close_date >= :now
            """), {"now": now_col}).fetchall()

            for row in aperturas:
                device = db.query(DeviceIot).filter(DeviceIot.id == row.device_iot_id).first()
                if device and device.status not in [11, 21, 22]:
                    print(f"[scheduler] → APERTURA Dispositivo {device.id} | open_date: {row.open_date}")
                    device.status = 11
                    try:
                        resp = requests.post(SERVO_CMD_URL, json={"action": "open"})
                        print("[scheduler] Comando 'open' seteado:", resp.json())
                    except Exception as e:
                        print("[scheduler] Error al setear comando 'open':", e)

            # 4. Solicitud en espera → Estado 20
            en_espera = db.execute(text("""
                SELECT r1.device_iot_id, r1.open_date
                FROM request r1
                INNER JOIN (
                    SELECT MAX(id) AS max_id
                    FROM request
                    WHERE status = 17
                    GROUP BY device_iot_id
                ) r2 ON r1.id = r2.max_id
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


def registrar_volumen_final(db: Session):
    from datetime import datetime
    now = datetime.now()
    # Se asume que el device_id de la válvula es 9 y el del medidor es 14.
    valve_device_id = 9  
    meter_device_id = 14  

    # Selecciona la solicitud de válvula (request) más reciente para ese dispositivo 
    # que esté aprobada (status 17), que ya haya cerrado (close_date < now) 
    # y que aún no tenga registro en consumption_measurements.
    requests_por_dispositivo = db.execute(text("""
        SELECT r1.id, r1.device_iot_id, r1.open_date, r1.close_date
        FROM request r1
        WHERE r1.device_iot_id = :valve_device_id
          AND r1.status = 17
          AND r1.close_date < :now
          AND r1.id = (
              SELECT MAX(r2.id)
              FROM request r2
              WHERE r2.device_iot_id = :valve_device_id
                AND r2.status = 17
          )
          AND NOT EXISTS (
              SELECT 1 FROM consumption_measurements cm
              WHERE cm.request_id = r1.id
          )
        ORDER BY r1.close_date DESC
    """), {"now": now, "valve_device_id": valve_device_id}).fetchall()

    for req_row in requests_por_dispositivo:
        req_id = req_row[0]
        device_id = req_row[1]
        open_date = req_row[2]
        close_date = req_row[3]

        # Se suma el total medido por el medidor (device_type_id=1) en el intervalo
        # definido por open_date y close_date del request.
        result = db.execute(text("""
            SELECT SUM(volume_liters) as total
            FROM device_iot_reading
            WHERE device_id = :meter_device_id
              AND device_type_id = 1
              AND timestamp BETWEEN :start AND :end
        """), {
            "meter_device_id": meter_device_id,
            "start": open_date,
            "end": close_date
        }).scalar()

        total_medido = result if result is not None else 0

        medicion = ConsumptionMeasurement(
            request_id=req_id,
            final_volume=total_medido
        )

        db.add(medicion)
        db.commit()

        print(f"[scheduler] Medición registrada para request_id={req_id}: {total_medido} litros.")
