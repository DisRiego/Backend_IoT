import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.devices.models import DeviceIot, Vars, DeviceType, Lot, Property, PropertyUser, User, DeviceCategories
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random

# Instancia del cliente de pruebas
client = TestClient(app)

# Fixture para la sesión de base de datos
@pytest.fixture(scope="function")
def db_session():
    db = next(get_db())
    devices_ids = []
    yield db, devices_ids
    devices_ids.clear()  # Limpiamos la lista de dispositivos al final de la prueba

def create_test_device(db: Session, devices_ids: list, category_id: int = 1) -> int:
    """Función para crear un dispositivo de prueba y devolver su ID"""
    # Verificar o crear el estado "No Operativo" (ID 12)
    status = db.query(Vars).filter(Vars.id == 12).first()  # ID 12 corresponde a "No Operativo"
    if not status:
        status = Vars(id=12, name="No Operativo", type="status")
        db.add(status)
        db.commit()
        db.refresh(status)

    # Crear el dispositivo con datos de prueba
    device_data = {
        "serial_number": random.randint(100000000, 999999999),
        "model": "DeviceTestModel",
        "lot_id": 1,  # Usamos un lote existente con id=1
        "installation_date": datetime.utcnow().isoformat(),
        "maintenance_interval_id": 1,  # Usar el ID de intervalo estándar
        "estimated_maintenance_date": (datetime.utcnow() + timedelta(days=365)).isoformat(),
        "status": status.id,  # Asignamos el estado "No Operativo" (ID 12)
        "devices_id": 1,  # Se asume que este es un tipo de dispositivo válido
        "price_device": {"price": 2500},
        "data_devices": {"sensor_data": 75}
    }

    response = client.post("/devices/", json=device_data)
    assert response.status_code == 201, f"Error creando dispositivo: {response.json()}"
    created_device_id = response.json()["data"]["device"]["id"]
    devices_ids.append(created_device_id)
    return created_device_id

def test_get_devices_by_category(db_session):
    db, devices_ids = db_session

    # Usar una categoría existente con id=1 y crear un dispositivo asignado a esa categoría
    category_id = 1  # Usamos la categoría existente con id=1

    # Crear dispositivos asignados a la categoría con id=1
    created_device_id_1 = create_test_device(db, devices_ids, category_id)
    created_device_id_2 = create_test_device(db, devices_ids, category_id)

    # Llamar al servicio para obtener los dispositivos por categoría
    response = client.get(f"/devices/category/{category_id}")

    # Comprobamos que la respuesta sea exitosa
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "data" in response.json()  # Verificamos que contenga "data"

    data = response.json()["data"]
    # Verificamos que los dispositivos creados estén en la respuesta
    devices = data
    device_found_1 = any(device["id"] == created_device_id_1 for device in devices)
    device_found_2 = any(device["id"] == created_device_id_2 for device in devices)
    assert device_found_1, f"El dispositivo con ID {created_device_id_1} no fue encontrado en la respuesta"     
    assert device_found_2, f"El dispositivo con ID {created_device_id_2} no fue encontrado en la respuesta"     

    # Verificamos que la categoría esté correctamente asignada
    assert data[0]["category_name"] == "IoT"     
    
    # Verificar que el estado sea "No Operativo" (correspondiente al estado con ID 12)
    assert data[0]["device_status_name"] == "No Operativo"  
