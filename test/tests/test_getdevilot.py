import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.devices.models import DeviceIot, Vars, DeviceType, Lot
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random

# Instancia del cliente de pruebas
client = TestClient(app)

# Fixture para la sesión de base de datos: no se eliminan los dispositivos creados.
@pytest.fixture(scope="function")
def db_session():
    db = next(get_db())
    devices_ids = []
    yield db, devices_ids
    devices_ids.clear()  # Limpiamos la lista de dispositivos al final de la prueba

def create_test_device(db: Session, devices_ids: list, lot_id: int = 1) -> int:
    """Función para crear un dispositivo de prueba y devolver su ID"""
    # Verificar o crear el estado "Activo" (ID 15)
    status = db.query(Vars).filter(Vars.id == 15).first()
    if not status:
        status = Vars(id=15, name="Activo", type="status")
        db.add(status)
        db.commit()
        db.refresh(status)

    # Crear el dispositivo con datos de prueba
    device_data = {
        "serial_number": random.randint(100000000, 999999999),
        "model": "DeviceTestModel",
        "lot_id": lot_id,  # Usamos el lote existente con id 1
        "installation_date": datetime.utcnow().isoformat(),
        "maintenance_interval_id": 1,  # Usar el ID de intervalo estándar
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

def test_get_devices_by_lot(db_session):
    db, devices_ids = db_session

    # Usar el lote con id=1 y crear un dispositivo asignado a ese lote
    lot_id = 1  # Usamos el lote existente con id 1

    # Crear dispositivos asignados al lote con id=1
    created_device_id_1 = create_test_device(db, devices_ids, lot_id)
    created_device_id_2 = create_test_device(db, devices_ids, lot_id)

    # Llamar al servicio para obtener los dispositivos por lote
    response = client.get(f"/devices/lot/{lot_id}")

    # Comprobamos que la respuesta sea exitosa
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "data" in response.json()  # Verificamos que contenga "data"

    data = response.json()["data"]
    # Verificamos que el lote esté correcto
    assert data["lot_id"] == lot_id
    assert data["lot_name"] == "Lote uno del ocho"  # Cambié el nombre del lote aquí

    # Verificamos que los dispositivos creados estén en la respuesta
    devices = data["devices"]
    device_found_1 = any(device["id"] == created_device_id_1 for device in devices)
    device_found_2 = any(device["id"] == created_device_id_2 for device in devices)
    assert device_found_1, f"El dispositivo con ID {created_device_id_1} no fue encontrado en la respuesta"
    assert device_found_2, f"El dispositivo con ID {created_device_id_2} no fue encontrado en la respuesta"
