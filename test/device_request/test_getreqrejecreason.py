import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.devices_request.models import RequestRejectionReason
from sqlalchemy.orm import Session

# Instancia del cliente de pruebas
client = TestClient(app)

# Fixture para la sesión de base de datos
@pytest.fixture(scope="function")
def db_session():
    db = next(get_db())
    yield db
    db.rollback()  # Hacer rollback al final de la prueba

# Prueba para obtener todas las razones de rechazo
def test_get_all_request_rejection_reasons(db_session):
    # Llamar al servicio get_all_request_rejection_reasons para obtener todas las razones de rechazo
    response = client.get("/devices-request/request-rejection-reasons/")

    # Verificar que la respuesta sea exitosa
    assert response.status_code == 200, f"Error al obtener las razones de rechazo: {response.json()}"

    data = response.json()["data"]

    # Comprobamos que los datos contengan las claves correctas
    assert len(data) > 0, "No se encontraron razones de rechazo"
    assert "id" in data[0], "No se encontró el ID en la razón de rechazo"
    assert "description" in data[0], "No se encontró la descripción en la razón de rechazo"

    # Verificar que las razones existentes en la base de datos estén presentes
    expected_reasons = [
        "Nivel de agua insuficiente",
        "Conflicto de apertura con otro lote",
        "Mantenimiento Programada",
        "Condiciones ambientales adversas",
        "Razón válida de prueba"
    ]

    for reason in expected_reasons:
        assert any(reason in reason_data["description"] for reason_data in data), f"Razón {reason} no encontrada"

