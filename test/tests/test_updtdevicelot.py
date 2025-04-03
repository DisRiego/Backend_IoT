import json
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.devices.models import DeviceIot, Vars, MaintenanceInterval
from app.devices.schemas import DeviceIotReadingUpdateByLot
from app.devices.services import DeviceService
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import random

client = TestClient(app)

# Fixture para obtener la sesión de la BD; en esta prueba no eliminamos los dispositivos creados.
@pytest.fixture(scope="function")
def db_session():
    db = next(get_db())
    devices_ids = []
    yield db, devices_ids
    devices_ids.clear()

# Función auxiliar para crear un dispositivo de prueba.
def create_test_device(db: Session, devices_ids: list, status_id: int = 11) -> int:
    device_data = {
        "serial_number": random.randint(100000000, 999999999),
        "model": "DeviceTestModel",
        "lot_id": 2,  # Se asume que ya existe un lote con id 2.
        "installation_date": datetime.utcnow().isoformat(),
        "maintenance_interval_id": 1,  # Se asume que existe este intervalo.
        "estimated_maintenance_date": (datetime.utcnow() + timedelta(days=365)).isoformat(),
        "status": status_id,  # Estado "Operativo" (ID 11)
        "devices_id": 1,
        "price_device": {"price": 2500},
        "data_devices": {}  # Inicialmente vacío.
    }
    response = client.post("/devices/", json=device_data)
    assert response.status_code == 201, f"Error creando dispositivo: {response.json()}"
    device_id = response.json()["data"]["device"]["id"]
    devices_ids.append(device_id)
    return device_id

# Prueba para el servicio update_device_reading_by_lot
@pytest.mark.asyncio
def test_update_device_reading_by_lot_model(db_session: Session):
    db, devices_ids = db_session

    # 1. Crear un dispositivo de prueba.
    device_id = create_test_device(db, devices_ids, status_id=11)

    # 2. Construir la instancia del modelo DeviceIotReadingUpdateByLot con los datos de lectura.
    #    Usamos model_validate en lugar de parse_obj si estás en Pydantic v2.
    reading_model = DeviceIotReadingUpdateByLot.model_validate({
        "device_id": device_id,
        "lot_id": 2,               # Se asume que el dispositivo está en el lote 2.
        "device_type_id": 1,       # Este campo se eliminará en el servicio.
        "sensor_value": 88,
        "temperature": 30
    })

    # 3. Instanciar el servicio y llamar al método update_device_reading_by_lot.
    service = DeviceService(db)
    response = service.update_device_reading_by_lot(reading_model)

    # 4. Convertir la respuesta a un diccionario.
    response_body = response.body.decode("utf-8")
    resp_json = json.loads(response_body)

    # 5. Verificar que la actualización fue exitosa.
    assert response.status_code == 200, f"Error al actualizar lectura: {resp_json}"
    assert resp_json["success"] is True, f"Actualización de lectura no exitosa: {resp_json}"

    # 6. Verificar que en el dispositivo actualizado se encuentren los valores esperados en data_device.
    updated_device = resp_json["data"]
    data_device = updated_device.get("data_device", {})
    assert data_device.get("sensor_value") == 88, "El valor de sensor_value no se actualizó correctamente"
    assert data_device.get("temperature") == 30, "El valor de temperature no se actualizó correctamente"
    
    print("Dispositivo actualizado:", updated_device)
