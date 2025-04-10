import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.devices.models import DeviceIot, PropertyLot
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import random

client = TestClient(app)

@pytest.fixture(scope="function")
def db_session():
    db = next(get_db())
    created_devices = []
    yield db, created_devices
    created_devices.clear()

def ensure_property_lot_relation(db: Session, lot_id: int, property_id: int):
    relation = db.query(PropertyLot).filter_by(lot_id=lot_id, property_id=property_id).first()
    if not relation:
        db.add(PropertyLot(lot_id=lot_id, property_id=property_id))
        db.commit()

def desasignar_dispositivos_existentes(db: Session, lot_id: int, type_id: int):
    dispositivos = db.query(DeviceIot).filter(
        DeviceIot.lot_id == lot_id,
        DeviceIot.devices_id == type_id
    ).all()

    for d in dispositivos:
        d.lot_id = None
        d.status = 16  # Estado desactivado
    db.commit()

def create_test_device(db: Session, created_devices: list, type_id: int = 1, status_id: int = 11) -> int:
    serial_number = random.randint(100000000, 999999999)
    device_data = {
        "serial_number": serial_number,
        "model": "DeviceTestModel",
        "lot_id": None,
        "installation_date": datetime.utcnow().isoformat(),
        "maintenance_interval_id": 1,
        "estimated_maintenance_date": (datetime.utcnow() + timedelta(days=365)).isoformat(),
        "status": status_id,
        "devices_id": type_id,
        "price_device": {"price": 2500},
        "data_devices": {"sensor_data": 100}
    }
    response = client.post("/devices/", json=device_data)
    assert response.status_code == 201, f"Error creando dispositivo: {response.json()}"
    device_id = response.json()["data"]["device"]["id"]
    created_devices.append(device_id)
    return device_id

@pytest.mark.asyncio
async def test_reassign_device_to_new_lot(db_session):
    db, created_devices = db_session
    lot_origen = 1
    lot_destino = 2
    property_id = 7
    device_type_id = 1  # Válvula

    # Asegurar relación predio-lote para ambos lotes
    ensure_property_lot_relation(db, lot_id=lot_origen, property_id=property_id)
    ensure_property_lot_relation(db, lot_id=lot_destino, property_id=property_id)

    # Desasignar válvulas previamente asignadas
    desasignar_dispositivos_existentes(db, lot_id=lot_origen, type_id=device_type_id)
    desasignar_dispositivos_existentes(db, lot_id=lot_destino, type_id=device_type_id)

    # Crear y asignar dispositivo al lote origen
    device_id = create_test_device(db, created_devices, type_id=device_type_id, status_id=11)

    initial_assignment = {
        "device_id": device_id,
        "lot_id": lot_origen,
        "installation_date": datetime.utcnow().isoformat(),
        "maintenance_interval_id": 1,
        "property_id": property_id,
        "estimated_maintenance_date": (datetime.utcnow() + timedelta(days=365)).isoformat()
    }
    response_assign = client.post("/devices/assign", json=initial_assignment)
    assert response_assign.status_code == 200, f"Asignación inicial falló: {response_assign.json()}"

    # Reasignar al lote destino
    reassignment_payload = {
        "device_id": device_id,
        "lot_id": lot_destino,
        "installation_date": datetime.utcnow().isoformat(),
        "maintenance_interval_id": 1,
        "property_id": property_id,
        "estimated_maintenance_date": (datetime.utcnow() + timedelta(days=365)).isoformat()
    }
    response_reassign = client.post("/devices/reassign", json=reassignment_payload)
    assert response_reassign.status_code == 200, f"Reasignación falló: {response_reassign.json()}"

    data = response_reassign.json()["data"]
    assert data["new_lot_id"] == lot_destino
    assert data["previous_lot_id"] == lot_origen
    assert data["installation_date"] is not None
