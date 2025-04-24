import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.devices_request.models import Request, TypeOpen, Vars
from app.devices.models import User
from sqlalchemy.orm import Session
from datetime import datetime

# Instancia del cliente de pruebas
client = TestClient(app)

# Fixture para la sesión de base de datos
@pytest.fixture(scope="function")
def db_session():
    db = next(get_db())
    # Limpiar la base de datos y crear datos de prueba
    yield db
    db.rollback()  # Hacer rollback al final de la prueba

# Función para crear una solicitud de prueba
def create_test_request(db: Session, user_id: int, device_iot_id: int, type_opening_id: int):
    # Obtener el tipo de apertura y estado desde la base de datos, sin crear nuevos
    type_open = db.query(TypeOpen).filter_by(id=type_opening_id).first()

    # Cambiado: Filtrar solo por el nombre del estado sin usar el campo "type"
    status = db.query(Vars).filter_by(name="Pendiente").first()

    # Crear la solicitud de prueba
    request = Request(
        type_opening_id=type_open.id,
        status=status.id,
        lot_id=1,
        user_id=user_id,
        device_iot_id=device_iot_id,
        open_date=datetime.utcnow(),
        close_date=datetime.utcnow(),
        request_date=datetime.utcnow(),
        volume_water=100
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    
    return request

def test_get_requests_by_user(db_session):
    # Usamos el user_id = 2 y su documento de usuario es 1010115909
    user_id = 2  # ID del usuario con número de documento 1010115909
    device_iot_id = 1  # Suponemos que hay un dispositivo IoT con ID 1
    request = create_test_request(db_session, user_id, device_iot_id, 1)
    
    # Llamar al endpoint para obtener todas las solicitudes del usuario
    response = client.get(f"/devices-request/user/{user_id}")

    # Verificamos que la respuesta sea exitosa
    assert response.status_code == 200, f"Error al obtener las solicitudes: {response.json()}"

    data = response.json()["data"]
    
    # Comprobamos que los datos contengan las claves correctas
    assert len(data) > 0, "No se encontraron solicitudes"
    assert "status_name" in data[0], "No se encontró el nombre del estado en la solicitud"
    assert "owner_document_number" in data[0], "No se encontró el número de documento del propietario"
    assert "request_type_name" in data[0], "No se encontró el tipo de apertura de la solicitud"

    # Verificar que los valores coincidan con los datos de prueba
    assert data[0]["status_name"] == "Pendiente", f"Esperado 'Pendiente', pero se obtuvo {data[0]['status_name']}"
    assert str(data[0]["owner_document_number"]) == "1010115909", f"Esperado '1010115909', pero se obtuvo {data[0]['owner_document_number']}"
    assert data[0]["request_type_name"] == "Apertura programada con limite de agua", f"Esperado 'Apertura programada con limite de agua', pero se obtuvo {data[0]['request_type_name']}"

# Prueba para cuando no hay solicitudes del usuario
def test_get_requests_by_user_no_data(db_session):
    # Llamar al endpoint para obtener todas las solicitudes del usuario (sin datos de prueba)
    response = client.get("/devices-request/user/999")  # Suponemos que no hay usuario con ID 999

    # Verificamos que la respuesta sea exitosa y que no haya datos
    assert response.status_code == 404, f"Error esperado 404, pero se obtuvo {response.status_code}"
    assert response.json()["data"] == [], "Se esperaban datos vacíos"
