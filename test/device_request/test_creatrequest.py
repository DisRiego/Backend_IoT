import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from app.main import app
from app.database import SessionLocal
from app.devices_request.models import TypeOpen, Request, DeviceIoT
from app.devices.models import  Notification

client = TestClient(app)

# Fixture para la base de datos
@pytest.fixture
def db_session():
    db = SessionLocal()  # Crear una nueva sesión de base de datos
    yield db
    db.close()

# Test para `create_request`
def test_create_request(db_session):
    # 1. Limpiar cualquier solicitud pendiente para el dispositivo (ID 64)
    device_iot_id = 64  # Dispositivo con ID 64 ya existente en la base de datos
    existing_request = db_session.query(Request).filter(
        Request.device_iot_id == device_iot_id,
        Request.status == 18  # Pendiente
    ).first()

    if existing_request:
        db_session.delete(existing_request)
        db_session.commit()

    # 2. Crear un tipo de apertura
    type_opening = TypeOpen(type_opening="Apertura nueva")
    db_session.add(type_opening)
    db_session.commit()

    # 3. Usar un dispositivo IoT ya creado con ID 64
    device_iot = db_session.query(DeviceIoT).filter(DeviceIoT.id == device_iot_id).first()
    assert device_iot is not None, "El dispositivo IoT con ID 64 no existe en la base de datos"

    # 4. Crear una solicitud de apertura
    request_data = {
        "type_opening_id": 1,  # Tipo de apertura 1
        "lot_id": 1,  # Lote con ID 1
        "user_id": 2,  # Usuario con ID 2
        "device_iot_id": device_iot.id,  # Usar el dispositivo IoT con ID 64
        "open_date": datetime.utcnow().isoformat(),
        "close_date": datetime.utcnow().isoformat(),
        "volume_water": 1000  # Volumen de agua requerido
    }

    # 5. Llamar al servicio create_request
    response = client.post("/devices-request/create-request/", json=request_data)

    # 6. Verificar que la respuesta sea exitosa (status 200)
    assert response.status_code == 200, f"Expected 200, but got {response.status_code}"
    data = response.json()
    assert data["success"] == True, "La solicitud no se creó correctamente"

    # 7. Verificar que la solicitud se haya creado en la base de datos
    created_request = db_session.query(Request).filter(
        Request.device_iot_id == device_iot.id,
        Request.status == 18  # pendiente
    ).first()
    assert created_request is not None, "No se encontró la solicitud en la base de datos"

    # 8. Verificar que el dispositivo IoT está asociado a la solicitud
    assert created_request.device_iot_id == device_iot.id, \
        f"Se esperaba dispositivo con ID {device_iot.id}, pero se obtuvo {created_request.device_iot_id}"

    # 9. Verificar que el volumen de agua fue asignado correctamente
    assert created_request.volume_water == 1000, f"Se esperaba volumen de agua 1000, pero se obtuvo {created_request.volume_water}"

    # 10. Verificar que el tipo de apertura se asignó correctamente
    assert created_request.type_opening_id == 1, f"Se esperaba tipo de apertura 1, pero se obtuvo {created_request.type_opening_id}"

    # 11. Verificar que el lote fue correctamente asignado
    assert created_request.lot_id == 1, f"Se esperaba lote con ID 1, pero se obtuvo {created_request.lot_id}"

    # 12. Verificar que las notificaciones se hayan creado correctamente
    notifications = db_session.query(Notification).filter(Notification.user_id == 2).all()
    assert len(notifications) > 0, "No se enviaron notificaciones al usuario solicitante"

    # 13. Verificar notificación al dueño del lote (si es diferente al usuario)
    owner_notifications = db_session.query(Notification).filter(Notification.user_id != 2).all()
    assert len(owner_notifications) > 0, "No se enviaron notificaciones al dueño del lote"
