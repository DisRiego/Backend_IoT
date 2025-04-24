import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.devices_request.models import DeviceIoT, Request
from app.devices.models import User, Lot
from datetime import datetime

client = TestClient(app)

# Fixture para la base de datos
@pytest.fixture
def db_session():
    db = SessionLocal()  # Crear una nueva sesión de base de datos
    yield db
    db.close()

# Test para obtener los detalles de un dispositivo IoT
def test_get_device_detail(db_session):
    # 1. Usar un dispositivo IoT ya creado con ID 64
    device_iot_id = 64
    device_iot = db_session.query(DeviceIoT).filter(DeviceIoT.id == device_iot_id).first()
    assert device_iot is not None, "El dispositivo IoT con ID 64 no existe en la base de datos"

    # 2. Verificar que el lote con ID 1 existe
    lot = db_session.query(Lot).filter(Lot.id == 1).first()
    assert lot is not None, "El lote con ID 1 no existe en la base de datos"

    # 3. Verificar que el usuario con ID 2 existe
    user = db_session.query(User).filter(User.id == 2).first()
    assert user is not None, "El usuario con ID 2 no existe en la base de datos"

    # 4. Verificar que hay una solicitud asociada al dispositivo (opcional)
    latest_request = db_session.query(Request).filter(Request.device_iot_id == device_iot_id).order_by(Request.request_date.desc()).first()

    # 5. Llamar al servicio get_device_detail para obtener los detalles del dispositivo
    response = client.get(f"/devices-request/device-detail/{device_iot_id}")

    # 6. Verificar que la respuesta sea exitosa
    assert response.status_code == 200, f"Expected 200, but got {response.status_code}"
    data = response.json()

    # 7. Verificar que los datos del dispositivo IoT estén correctos
    assert data["success"] == True, "La solicitud no se completó correctamente"
    assert data["data"]["id"] == device_iot.id, f"Se esperaba ID {device_iot.id}, pero se obtuvo {data['data']['id']}"
    assert data["data"]["serial_number"] == device_iot.serial_number, f"Se esperaba serial_number {device_iot.serial_number}, pero se obtuvo {data['data']['serial_number']}"

    # 8. Verificar que la última solicitud asociada al dispositivo esté correcta (si existe)
    if latest_request:
        assert data["data"]["latest_request"]["id"] == latest_request.id, f"Se esperaba ID de solicitud {latest_request.id}, pero se obtuvo {data['data']['latest_request']['id']}"
    else:
        assert data["data"]["latest_request"] is None, "Se esperaba que no hubiera solicitud asociada"
