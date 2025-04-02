import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.devices.models import Vars, MaintenanceInterval, DeviceIot, Lot
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import random

client = TestClient(app)

# Fixture de base de datos sin borrar el dispositivo (para poder verificar su persistencia)
@pytest.fixture(scope="function")
def db_session():
    db = next(get_db())
    devices_ids = []
    yield db, devices_ids
    devices_ids.clear()

def create_test_device(db: Session, devices_ids: list, lot_id: int = 2) -> int:
    # Asegurar que el estado "Operativo" existe (ID 11 se considera "Operativo")
    status = db.query(Vars).filter(Vars.id == 11).first()
    if not status:
        status = Vars(id=11, name="Operativo")
        db.add(status)
        db.commit()
        db.refresh(status)

    # Asegurar que existe un intervalo de mantenimiento (usamos ID 1)
    maintenance_interval = db.query(MaintenanceInterval).filter(MaintenanceInterval.id == 1).first()
    if not maintenance_interval:
        maintenance_interval = MaintenanceInterval(id=1, name="Intervalo estándar", days=365)
        db.add(maintenance_interval)
        db.commit()
        db.refresh(maintenance_interval)

    # Se asume que ya existe un lote con id 2.
    device_data = {
        "serial_number": random.randint(100000000, 999999999),
        "model": "DeviceTestModel",
        "lot_id": lot_id,
        "installation_date": datetime.utcnow().isoformat(),
        "maintenance_interval_id": maintenance_interval.id,
        "estimated_maintenance_date": (datetime.utcnow() + timedelta(days=365)).isoformat(),
        "status": status.id,
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
async def test_get_all_devices(db_session: Session):
    db, devices_ids = db_session

    # Crear un dispositivo de prueba con lote id 2
    created_device_id = create_test_device(db, devices_ids, lot_id=2)

    # Ahora, llamar al endpoint para obtener todos los dispositivos
    response = client.get("/devices/")
    assert response.status_code == 200, f"Error en get_all_devices: {response.json()}"
    data = response.json()
    assert data["success"] is True, "El servicio no devolvió éxito"
    assert "data" in data, "La respuesta no contiene la clave 'data'"

    # Comprobar que el dispositivo recién creado está en la lista
    devices = data["data"]
    device_found = any(device["id"] == created_device_id for device in devices)
    assert device_found is True, "El dispositivo creado se encuentra en la lista de dispositivos"
