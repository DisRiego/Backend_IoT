import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.devices.models import Vars, MaintenanceInterval
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.devices.models import DeviceIot
from fastapi import HTTPException


# Instancia del cliente de pruebas
client = TestClient(app)

# db_session para el manejo de la sesión de base de datos
@pytest.fixture(scope="function")
def db_session():
    db = next(get_db())  # Usamos la función get_db proporcionada en database.py
    # Almacenar el id de los dispositivos creados en esta prueba
    devices_ids = []
    yield db, devices_ids
    # Limpiar los dispositivos creados durante la prueba, sin afectar los preexistentes
    for device_id in devices_ids:
        device = db.query(DeviceIot).filter(DeviceIot.id == device_id).first()
        if device:
            db.delete(device)
    db.commit()


# Test para la creación de un dispositivo válido
@pytest.mark.asyncio
async def test_create_device_for_user_and_lot(db_session: Session):
    lot_id = 2  # Lote específico de la prueba
    db, devices_ids = db_session

    # Crear dispositivo válido para la prueba
    status = db.query(Vars).filter(Vars.id == 15).first()  # Suponiendo que 15 es el estado activo
    if not status:
        status = Vars(id=15, name="Activo", type="status")
        db.add(status)
        db.commit()
        db.refresh(status)

    maintenance_interval = db.query(MaintenanceInterval).filter(MaintenanceInterval.id == 1).first()
    if not maintenance_interval:
        maintenance_interval = MaintenanceInterval(id=1, name="Intervalo estándar", days=365)
        db.add(maintenance_interval)
        db.commit()
        db.refresh(maintenance_interval)

    device_data = {
        "serial_number": 123456789,  # Serial específico para prueba
        "model": "DeviceTestModel",
        "lot_id": lot_id,
        "installation_date": datetime.utcnow().isoformat(),  # Convertir a formato de cadena
        "maintenance_interval_id": maintenance_interval.id,
        "estimated_maintenance_date": (datetime.utcnow() + timedelta(days=365)).isoformat(),  # Convertir a formato de cadena
        "status": status.id,
        "devices_id": 1,  # Asignamos un tipo de dispositivo básico
        "price_device": {"price": 2500},
        "data_devices": {"sensor_data": 75}
    }

    # Intentar crearlo y verificar que se lanza un error 201
    response = client.post("/devices/", json=device_data)
    
    assert response.status_code == 201
    assert response.json()["success"] is True
    assert response.json()["data"]["title"] == "Dispositivo creado"
    assert response.json()["data"]["message"] == "El dispositivo ha sido creado correctamente"

    # Almacenar el id del dispositivo creado
    created_device_id = response.json()["data"]["device"]["id"]
    devices_ids.append(created_device_id)


@pytest.mark.asyncio
async def test_create_device_without_serial_number(db_session: Session):
    lot_id = 2  # Lote específico de la prueba
    db, devices_ids = db_session

    # Crear dispositivo sin número de serie
    status = db.query(Vars).filter(Vars.id == 15).first()  # Suponiendo que 15 es el estado activo
    if not status:
        status = Vars(id=15, name="Activo", type="status")
        db.add(status)
        db.commit()
        db.refresh(status)

    maintenance_interval = db.query(MaintenanceInterval).filter(MaintenanceInterval.id == 1).first()
    if not maintenance_interval:
        maintenance_interval = MaintenanceInterval(id=1, name="Intervalo estándar", days=365)
        db.add(maintenance_interval)
        db.commit()
        db.refresh(maintenance_interval)

    # Crear el dispositivo sin serial_number
    device_data = {
        "model": "DeviceTestModel",
        "lot_id": lot_id,
        "installation_date": datetime.utcnow().isoformat(),  # Convertir a formato de cadena
        "maintenance_interval_id": maintenance_interval.id,
        "estimated_maintenance_date": (datetime.utcnow() + timedelta(days=365)).isoformat(),  # Convertir a formato de cadena
        "status": status.id,
        "devices_id": 1,  # Asignamos un tipo de dispositivo básico
        "price_device": {"price": 2500},
        "data_devices": {"sensor_data": 75}
    }

    # Intentar crear el dispositivo y verificar que lanza un error 422
    response = client.post("/devices/", json=device_data)


    assert response.status_code == 422
