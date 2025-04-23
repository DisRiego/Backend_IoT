import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.devices.models import Vars, MaintenanceInterval, DeviceIot, Lot
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import random

# Instancia del cliente de pruebas
client = TestClient(app)

# Fixture para la sesión de base de datos: no se eliminan los dispositivos creados.
@pytest.fixture(scope="function")
def db_session():
    db = next(get_db())
    devices_ids = []
    yield db, devices_ids
    devices_ids.clear()

def create_test_device(db: Session, devices_ids: list, lot_id: int = 2) -> int:
    # Verificar o crear el estado "Activo" (ID 15)
    status = db.query(Vars).filter(Vars.id == 15).first()
    if not status:
        status = Vars(id=15, name="Activo", type="status")
        db.add(status)
        db.commit()
        db.refresh(status)

    # Verificar o crear el intervalo de mantenimiento (ID 1)
    maintenance_interval = db.query(MaintenanceInterval).filter(MaintenanceInterval.id == 1).first()
    if not maintenance_interval:
        maintenance_interval = MaintenanceInterval(id=1, name="Intervalo estándar", days=365)
        db.add(maintenance_interval)
        db.commit()
        db.refresh(maintenance_interval)

    # Se asume que el lote con id `lot_id` ya existe.
    device_data = {
        "serial_number": random.randint(100000000, 999999999),
        "model": "DeviceTestModel",
        "lot_id": lot_id,
        "installation_date": datetime.utcnow().isoformat(),
        "maintenance_interval_id": maintenance_interval.id,
        "estimated_maintenance_date": (datetime.utcnow() + timedelta(days=365)).isoformat(),
        "status": status.id,
        "devices_id": 1,  # Se asume que este es un tipo de dispositivo válido
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

    # Crear un dispositivo de prueba
    created_device_id = create_test_device(db, devices_ids, lot_id=2)

    # Llamar al endpoint para obtener todos los dispositivos
    response = client.get("/devices/")
    assert response.status_code == 200, f"Error en GET /devices/: {response.json()}"
    data = response.json()
    assert data["success"] is True, "La respuesta indica fallo en la obtención de dispositivos"
    assert "data" in data, "La respuesta no contiene la clave 'data'"

    devices = data["data"]
    # Verificar que el dispositivo creado se encuentra en la lista
    device_found = any(device["id"] == created_device_id for device in devices)
    assert device_found, f"El dispositivo con ID {created_device_id} no fue encontrado en la respuesta. Dispositivos retornados: {devices}"
