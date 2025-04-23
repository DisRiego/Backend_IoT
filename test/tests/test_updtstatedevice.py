import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.devices.models import Vars, MaintenanceInterval, DeviceIot, Lot
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import random

client = TestClient(app)

# Fixture para la sesión de base de datos (no se borran los dispositivos creados en esta prueba)
@pytest.fixture(scope="function")
def db_session():
    db = next(get_db())
    devices_ids = []
    yield db, devices_ids
    devices_ids.clear()

# Función auxiliar para crear un dispositivo con un estado inicial dado.
# Para esta prueba, crearemos el dispositivo con estado 15 ("No operativo").
def create_test_device_with_status(db: Session, devices_ids: list, status_id: int = 15, lot_id: int = 2) -> int:
    # Asegurarse de que el estado exista. 
    # En nuestra convención, usaremos ID 15 para "No operativo" y ID 11 para "Operativo".
    status = db.query(Vars).filter(Vars.id == status_id).first()
    if not status:
        # Si no existe, lo creamos con el nombre apropiado según el ID
        name = "No operativo" if status_id == 15 else "Operativo"
        status = Vars(id=status_id, name=name)
        db.add(status)
        db.commit()
        db.refresh(status)

    # Asegurarse de que exista un intervalo de mantenimiento (usamos ID 1)
    maintenance_interval = db.query(MaintenanceInterval).filter(MaintenanceInterval.id == 1).first()
    if not maintenance_interval:
        maintenance_interval = MaintenanceInterval(id=1, name="Intervalo estándar", days=365)
        db.add(maintenance_interval)
        db.commit()
        db.refresh(maintenance_interval)

    # Se asume que ya existe un lote con id=2 en la BD.
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

# Función auxiliar para invocar el endpoint update_device_status
def update_device_status(device_id: int, new_status: int):
    # Se envía el nuevo estado en el formulario
    response = client.put(f"/devices/{device_id}/status", data={"new_status": new_status})
    return response

# Prueba para verificar que update_device_status funciona correctamente.
# Se crea un dispositivo con estado 15 ("No operativo") y luego se actualiza a 11 ("Operativo").
@pytest.mark.asyncio
async def test_update_device_status_success(db_session: Session):
    db, devices_ids = db_session

    # Crear dispositivo de prueba con estado 15 ("No operativo")
    created_device_id = create_test_device_with_status(db, devices_ids, status_id=15, lot_id=2)
    
    # Actualizar el estado del dispositivo a 11 ("Operativo")
    response = update_device_status(created_device_id, new_status=11)
    assert response.status_code == 200, f"Error al actualizar estado: {response.json()}"
    data = response.json()["data"]

    # Verificar que el dispositivo actualizado tenga el nuevo estado
    assert data["device_id"] == created_device_id, "El ID del dispositivo no coincide"
    assert data["new_status"] == 11, "El nuevo estado no es el esperado"
    assert data["status_name"] == "Operativo", f"Se esperaba 'Operativo', se obtuvo: {data['status_name']}"
