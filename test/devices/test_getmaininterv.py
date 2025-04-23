import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.devices.models import MaintenanceInterval, Device, DeviceType
from sqlalchemy.orm import Session

client = TestClient(app)

# Fixture para obtener una sesión de base de datos sin limpiar registros, 
# ya que para estos endpoints queremos ver lo que existe en la BD.
@pytest.fixture(scope="function")
def db_session():
    db = next(get_db())
    yield db
    # No se borran los registros; se deja la BD intacta.

def test_get_all_maintenance_intervals(db_session: Session):
    """
    Prueba para verificar que el servicio get_all_maintenance_intervals
    devuelve una lista de intervalos de mantenimiento.
    """
    response = client.get("/devices/maintenance_intervals/")
    assert response.status_code == 200, f"Error: {response.json()}"
    data = response.json()
    assert data["success"] is True, "La respuesta debe indicar éxito"
    assert isinstance(data["data"], list), "Los intervalos deben venir en una lista"
    # Se puede comprobar que la lista tenga al menos un elemento (si se espera que la BD tenga datos)
    if data["data"]:
        # Verificamos que cada elemento tiene al menos los campos id, name y days
        for interval in data["data"]:
            assert "id" in interval, "Falta el campo 'id' en el intervalo"
            assert "name" in interval, "Falta el campo 'name' en el intervalo"
            assert "days" in interval, "Falta el campo 'days' en el intervalo"

def test_get_device_types(db_session: Session):
    """
    Prueba para verificar que el servicio get_device_types devuelve la lista de tipos de dispositivos.
    Este endpoint devuelve una lista de diccionarios con id, name y properties de cada dispositivo.
    """
    # Llamamos directamente al servicio mediante la función que se encarga de obtener los tipos
    from app.devices.services import DeviceService
    device_service = DeviceService(db_session)
    
    result = device_service.get_device_types()
    # Se espera que se retorne una lista
    assert isinstance(result, list), "El resultado debe ser una lista"
    # Si hay elementos en la lista, verificamos que cada uno contenga los campos requeridos
    if result:
        for d in result:
            assert "id" in d, "Falta el campo 'id' en el tipo de dispositivo"
            assert "name" in d, "Falta el campo 'name' en el tipo de dispositivo"
            assert "properties" in d, "Falta el campo 'properties' en el tipo de dispositivo"
