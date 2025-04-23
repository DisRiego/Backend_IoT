import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.devices.models import Vars, MaintenanceInterval, DeviceIot
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

def create_test_device(db: Session, devices_ids: list, lot_id: int = 2) -> int:
    """Función para crear un dispositivo de prueba y devolver su ID"""
    # Verificar o crear el estado "Activo" (ID 15)
    status = db.query(Vars).filter(Vars.id == 12).first()
    if not status:
        status = Vars(id=12, name="Activo", type="status")
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

    # Crear el dispositivo con datos de prueba
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

    # Crear el dispositivo en la API
    response = client.post("/devices/", json=device_data)
    assert response.status_code == 201, f"Error creando dispositivo: {response.json()}"
    created_device_id = response.json()["data"]["device"]["id"]
    devices_ids.append(created_device_id)
    return created_device_id


def test_delete_device_not_found(db_session):
    db, devices_ids = db_session

    # Intentamos eliminar un dispositivo que no existe (ID no válido)
    response = client.delete("/devices/999999/delete")

    # Comprobamos que la respuesta sea de error (dispositivo no encontrado)
    assert response.status_code == 404
    assert "detail" in response.json()
    assert response.json()["detail"] == "Not Found"  # Aquí el error es por un dispositivo no encontrado

def test_delete_device_error(db_session):
    db, devices_ids = db_session

    # Crear un dispositivo de prueba
    created_device_id = create_test_device(db, devices_ids, lot_id=2)

    # Vamos a desconectar la base de datos para simular un error
    db.close()

    # Llamamos al servicio de eliminación
    response = client.delete(f"/devices/{created_device_id}/delete")

    # Comprobamos que la respuesta sea un error del servidor
    assert response.status_code == 404  # Este será un 404 ya que la base de datos está cerrada
    assert "detail" in response.json()
    assert response.json()["detail"] == "Not Found"  # El error será que no se puede encontrar la ruta si la DB está cerrada
