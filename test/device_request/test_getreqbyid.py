import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from app.main import app
from app.database import SessionLocal
from app.devices_request.models import TypeOpen, Request, DeviceIoT

client = TestClient(app)

# Fixture para la base de datos
@pytest.fixture
def db_session():
    db = SessionLocal()  # Crear una nueva sesión de base de datos
    yield db
    db.close()

# Test para `get_request_by_id`
def test_get_request_by_id(db_session):
    # 1. Usar un dispositivo IoT ya creado con ID 64 (dispositivo existente)
    device_iot_id = 64  # Usando el dispositivo con ID 64 ya existente en la base de datos
    device_iot = db_session.query(DeviceIoT).filter(DeviceIoT.id == device_iot_id).first()
    assert device_iot is not None, "El dispositivo IoT con ID 64 no existe en la base de datos"

    # 2. Verificar si ya existe una solicitud pendiente para este dispositivo
    existing_request = db_session.query(Request).filter(
        Request.device_iot_id == device_iot_id,
        Request.status == 18  # Pendiente
    ).first()

    if existing_request:
        # Si ya existe una solicitud pendiente, no se debe crear una nueva
        print(f"Ya existe una solicitud pendiente para el dispositivo {device_iot_id}")
        return

    # 3. Crear un tipo de apertura
    type_opening = TypeOpen(type_opening="Apertura nueva")
    db_session.add(type_opening)
    db_session.commit()

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

    # 5. Llamar al servicio create_request para crear la solicitud
    response = client.post("/devices-request/create-request/", json=request_data)

    assert response.status_code == 200, f"Expected 200, but got {response.status_code}"
    data = response.json()
    assert data["success"] == True, "La solicitud no se creó correctamente"

    # 6. Obtener el ID de la solicitud recién creada
    created_request = db_session.query(Request).filter(
        Request.device_iot_id == device_iot.id,
        Request.status == 18  # Pendiente
    ).first()

    assert created_request is not None, "No se encontró la solicitud en la base de datos"

    # 7. Llamar al servicio `get_request_by_id` para obtener los detalles de la solicitud
    response = client.get(f"/devices-request/{created_request.id}")

    assert response.status_code == 200, f"Expected 200, but got {response.status_code}"
    data = response.json()
    assert data["success"] == True, "La solicitud no se recuperó correctamente"

    # 8. Verificar que los datos de la solicitud sean correctos
    assert data["data"]["lot_name"] == "Lote 1", f"Se esperaba 'Lote 1', pero se obtuvo {data['data']['lot_name']}"
    assert data["data"]["property_name"] == "Propiedad 7", f"Se esperaba 'Propiedad 7', pero se obtuvo {data['data']['property_name']}"
    assert data["data"]["owner_document_number"] == "123456", f"Se esperaba '123456', pero se obtuvo {data['data']['owner_document_number']}"
    assert data["data"]["owner_name"] == "Usuario 2", f"Se esperaba 'Usuario 2', pero se obtuvo {data['data']['owner_name']}"
    assert data["data"]["request_type_name"] == "Apertura nueva", f"Se esperaba 'Apertura nueva', pero se obtuvo {data['data']['request_type_name']}"
    assert data["data"]["status_name"] == "Pendiente", f"Se esperaba 'Pendiente', pero se obtuvo {data['data']['status_name']}"
    assert data["data"]["rejection_reason_name"] is None, "Se esperaba None para la razón de rechazo"
    assert data["data"]["rejection_comment"] is None, "Se esperaba None para el comentario de rechazo"
