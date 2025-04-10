import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.devices.models import DeviceIot, DeviceType, PropertyLot
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import random

client = TestClient(app)

@pytest.fixture(scope="function")
def db_session():
    db = next(get_db())
    test_device_ids = []
    yield db, test_device_ids
    for device_id in test_device_ids:
        device = db.query(DeviceIot).filter(DeviceIot.id == device_id).first()
        if device:
            device.status = 16  # Inhabilitado
            device.lot_id = None
            db.commit()

def create_test_device(db: Session, test_device_ids: list, device_type_id: int) -> int:
    serial_number = random.randint(100000000, 999999999)
    device_data = {
        "serial_number": serial_number,
        "model": "ModeloTestValve",
        "lot_id": None,
        "installation_date": datetime.utcnow().isoformat(),
        "maintenance_interval_id": 1,
        "estimated_maintenance_date": (datetime.utcnow() + timedelta(days=180)).isoformat(),
        "status": 11,  # Operativo
        "devices_id": device_type_id,
        "price_device": {"price": 1000},
        "data_devices": {"sensor_data": 55}
    }
    response = client.post("/devices/", json=device_data)
    assert response.status_code == 201
    device_id = response.json()["data"]["device"]["id"]
    test_device_ids.append(device_id)
    return device_id

def get_valve_type_id(db: Session) -> int:
    valve_type = db.query(DeviceType).filter(DeviceType.name.ilike("válvula")).first()
    assert valve_type, "No se encontró el tipo de dispositivo 'Válvula'"
    return valve_type.id

def ensure_property_lot_relation(db: Session, lot_id: int, property_id: int):
    relation = db.query(PropertyLot).filter_by(lot_id=lot_id, property_id=property_id).first()
    if not relation:
        db.add(PropertyLot(lot_id=lot_id, property_id=property_id))
        db.commit()

@pytest.mark.asyncio
async def test_assign_valve_to_lot_dynamically(db_session):
    db, test_device_ids = db_session
    lot_id = 2
    property_id = 7

    ensure_property_lot_relation(db, lot_id, property_id)

    valve_type_id = get_valve_type_id(db)

    # Desasignar válvulas existentes en ese lote si no fueron creadas por esta prueba
    existing_valves = db.query(DeviceIot).filter(
        DeviceIot.lot_id == lot_id,
        DeviceIot.devices_id == valve_type_id,
        DeviceIot.status != 16
    ).all()

    for valve in existing_valves:
        valve.status = 16
        valve.lot_id = None
    db.commit()

    # Crear nuevo dispositivo válvula para asignación
    device_id = create_test_device(db, test_device_ids, valve_type_id)

    payload = {
        "device_id": device_id,
        "lot_id": lot_id,
        "installation_date": datetime.utcnow().isoformat(),
        "maintenance_interval_id": 1,
        "estimated_maintenance_date": (datetime.utcnow() + timedelta(days=180)).isoformat(),
        "property_id": property_id
    }

    response = client.post("/devices/assign", json=payload)
    json_data = response.json()
    assert response.status_code == 200, f"Error: {json_data}"
    assert json_data["success"] is True
    assert json_data["data"]["lot_id"] == lot_id
    assert json_data["data"]["status"] == 12  # No operativo
