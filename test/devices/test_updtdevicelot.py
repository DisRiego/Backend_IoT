import json
import pytest
from datetime import datetime, timedelta
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy import text  # ✅ Import necesario para ejecutar texto SQL en db_session
from app.devices.services import DeviceService
from app.devices.models import Device, DeviceIot, DeviceType, Lot, Vars, ConsumptionMeasurement
from app.devices_request.models import Request
from app.devices.schemas import DeviceIotReadingUpdateByLot
from app.database import SessionLocal
import random

# ✅ Fixture para db_session
@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

# ✅ Fixture auxiliar para crear dispositivos base
@pytest.fixture
def create_base_device(db_session):
    def _create():
        device_type = db_session.query(DeviceType).first()
        if not device_type:
            device_type = DeviceType(name="TipoPrueba")
            db_session.add(device_type)
            db_session.commit()
            db_session.refresh(device_type)

        vars_ok = db_session.query(Vars).filter_by(id=11).first()
        if not vars_ok:
            vars_ok = Vars(id=11, name="Operativo")
            db_session.add(vars_ok)
            db_session.commit()

        lot = db_session.query(Lot).filter_by(id=2).first()
        if not lot:
            lot = Lot(
                id=2,
                name="Lote Test",
                longitude=1.0,
                latitude=2.0,
                extension=5.0,
                real_estate_registration_number=1234,
                planting_date=datetime.now().date(),
                estimated_harvest_date=(datetime.now() + timedelta(days=90)).date(),
                state=16
            )
            db_session.add(lot)
            db_session.commit()
            db_session.refresh(lot)

        device_config = Device(devices_type_id=device_type.id, properties={})
        db_session.add(device_config)
        db_session.commit()
        db_session.refresh(device_config)

        device_iot = DeviceIot(
            serial_number=random.randint(10000000, 99999999),
            model="ModeloPrueba",
            lot_id=lot.id,
            devices_id=device_config.id,
            status=11,
            installation_date=datetime.now(),
            estimated_maintenance_date=datetime.now() + timedelta(days=30),
            data_devices={}
        )
        db_session.add(device_iot)
        db_session.commit()
        db_session.refresh(device_iot)

        return device_iot
    return _create

# ✅ Pruebas

@pytest.mark.parametrize("payload, expected_status, expected_fragment", [
    ({"lot_id": 1}, 400, "Faltan device_id o lot_id"),
    ({"device_id": 999999}, 400, "Faltan device_id o lot_id"),
    ({"device_id": 999999, "lot_id": 1}, 404, "Dispositivo no encontrado")
])
def test_update_missing_and_not_found(db_session, payload, expected_status, expected_fragment):
    service = DeviceService(db_session)
    try:
        reading = DeviceIotReadingUpdateByLot(**payload)
    except Exception:
        class Dummy:
            def dict(self):
                return payload
        reading = Dummy()
    response = service.update_device_reading_by_lot(reading)
    body = json.loads(response.body)
    assert response.status_code == expected_status
    assert expected_fragment in str(body["data"])


def test_update_simple_data_devices(db_session, create_base_device):
    device = create_base_device()
    service = DeviceService(db_session)

    payload = {
        "device_id": device.id,
        "lot_id": device.lot_id,
        "device_type_id": 1,
        "sensor_value": 42,
        "humidity": 55
    }

    reading = DeviceIotReadingUpdateByLot(**payload)
    response = service.update_device_reading_by_lot(reading)
    body = json.loads(response.body)

    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["data_devices"] == {"sensor_value": 42, "humidity": 55}
