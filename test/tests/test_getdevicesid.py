import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.devices.models import Vars, MaintenanceInterval, DeviceIot, Lot, Property, PropertyUser, User
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import random

client = TestClient(app)

# Fixture para la sesión de base de datos sin eliminar el dispositivo creado
@pytest.fixture(scope="function")
def db_session():
    db = next(get_db())
    devices_ids = []
    yield db, devices_ids
    devices_ids.clear()

def create_test_device(db: Session, devices_ids: list, lot_id: int = 2) -> int:
    # Asegurarse de que el estado "Operativo" esté en Vars (supongamos que el id 11 corresponde a "Operativo")
    status = db.query(Vars).filter(Vars.id == 11).first()
    if not status:
        status = Vars(id=11, name="Operativo", type="status")
        db.add(status)
        db.commit()
        db.refresh(status)

    # Asegurarse de que el intervalo de mantenimiento exista (id 1)
    maintenance_interval = db.query(MaintenanceInterval).filter(MaintenanceInterval.id == 1).first()
    if not maintenance_interval:
        maintenance_interval = MaintenanceInterval(id=1, name="Intervalo estándar", days=365)
        db.add(maintenance_interval)
        db.commit()
        db.refresh(maintenance_interval)

    # Se asume que ya existe un lote con id=2.
    device_data = {
        "serial_number": random.randint(100000000, 999999999),
        "model": "DeviceTestModel",
        "lot_id": lot_id,
        "installation_date": datetime.utcnow().isoformat(),
        "maintenance_interval_id": maintenance_interval.id,
        "estimated_maintenance_date": (datetime.utcnow() + timedelta(days=365)).isoformat(),
        "status": status.id,  # Usamos el registro operativo (id 11)
        "devices_id": 1,
        "price_device": {"price": 2500},
        "data_devices": {"sensor_data": 75}
    }
    
    response = client.post("/devices/", json=device_data)
    assert response.status_code == 201, f"Error creando dispositivo: {response.json()}"
    created_device_id = response.json()["data"]["device"]["id"]
    devices_ids.append(created_device_id)
    return created_device_id

@pytest.mark.asyncio
async def test_get_device_by_id(db_session: Session):
    db, devices_ids = db_session

    # Crear un dispositivo de prueba asociado al lote con id 2
    created_device_id = create_test_device(db, devices_ids, lot_id=2)

    # Invocar el servicio para obtener el dispositivo por su id
    response = client.get(f"/devices/{created_device_id}")
    assert response.status_code == 200, f"Error en get_device_by_id: {response.json()}"
    data = response.json()["data"]

    # Verificar que el ID y el modelo coinciden
    assert data["id"] == created_device_id, "El ID del dispositivo no coincide"
    assert data["model"] == "DeviceTestModel", "El modelo del dispositivo no coincide"
    # Verificar que se incluye la información del lote
    assert "lot_id" in data, "Falta el campo lot_id en la respuesta"
    # Verificar que el estado del dispositivo se retorne como "Operativo"
    assert data["device_status_name"] == "Operativo", f"El estado del dispositivo no es el esperado: {data['device_status_name']}"
