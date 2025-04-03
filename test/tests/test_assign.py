import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.devices.models import DeviceIot, Vars, MaintenanceInterval, Lot, PropertyLot
from app.devices.schemas import DeviceAssignRequest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import random

client = TestClient(app)

# Fixture para obtener la sesión de la base de datos.
# En esta prueba no eliminamos los dispositivos creados.
@pytest.fixture(scope="function")
def db_session():
    db = next(get_db())
    devices_ids = []
    yield db, devices_ids
    devices_ids.clear()

# Función auxiliar para crear un dispositivo de prueba con estado "Operativo" (ID 11)
def create_test_device(db: Session, devices_ids: list, status_id: int = 11) -> int:
    device_data = {
        "serial_number": random.randint(100000000, 999999999),
        "model": "DeviceTestModel",
        "lot_id": None,  # Se crea sin lote asignado inicialmente
        "installation_date": datetime.utcnow().isoformat(),
        "maintenance_interval_id": 1,  # Se asume que este intervalo existe
        "estimated_maintenance_date": (datetime.utcnow() + timedelta(days=365)).isoformat(),
        "status": status_id,  # Estado "Operativo"
        "devices_id": 1,
        "price_device": {"price": 2500},
        "data_devices": {"sensor_data": 100}
    }
    response = client.post("/devices/", json=device_data)
    assert response.status_code == 201, f"Error creando dispositivo: {response.json()}"
    device_id = response.json()["data"]["device"]["id"]
    devices_ids.append(device_id)
    return device_id

# Función auxiliar para asegurar que exista la relación entre el predio y el lote.
def ensure_property_lot_relation(db: Session, lot_id: int = 2, property_id: int = 7):
    rel = db.query(PropertyLot).filter(
        PropertyLot.lot_id == lot_id,
        PropertyLot.property_id == property_id
    ).first()
    if not rel:
        rel = PropertyLot(property_id=property_id, lot_id=lot_id)
        db.add(rel)
        db.commit()
    return rel

# Prueba para el servicio assign_to_lot
@pytest.mark.asyncio
async def test_assign_device_to_lot(db_session: Session):
    db, devices_ids = db_session

    # 1. Crear un dispositivo de prueba (estado "Operativo" = ID 11)
    device_id = create_test_device(db, devices_ids, status_id=11)
    
    # 2. Asegurarse de que exista la relación entre el predio (property_id=7) y el lote (lot_id=2)
    ensure_property_lot_relation(db, lot_id=2, property_id=7)
    
    # 3. Preparar los datos de asignación usando el esquema DeviceAssignRequest.
    #    NOTA: Ahora se incluye el campo "estimated_maintenance_date" para cumplir con el modelo.
    assignment_payload = {
        "device_id": device_id,
        "lot_id": 2,
        "installation_date": datetime.utcnow().isoformat(),
        "maintenance_interval_id": 1,  # Se asume que existe este intervalo
        "estimated_maintenance_date": (datetime.utcnow() + timedelta(days=365)).isoformat(),
        "property_id": 7  # Debe coincidir con la relación en PropertyLot
    }
    
    # 4. Invocar el endpoint para asignar el dispositivo al lote
    response = client.post("/devices/assign", json=assignment_payload)
    assert response.status_code == 200, f"asignación: {response.json()}"
    json_resp = response.json()
    assert json_resp["success"] is True, f" asignación: {json_resp}"
    
    data = json_resp["data"]
    # 5. Verificar que el dispositivo quedó asignado al lote 2 y que su estado se actualizó a "No Operativo" (ID 12)
    assert data["lot_id"] == 2, "El dispositivo no fue asignado al lote esperado"
    assert data["status"] == 12, "El estado del dispositivo no se actualizó a 'No Operativo'"
    # También se pueden verificar otros campos, como las fechas y el nombre del lote.

