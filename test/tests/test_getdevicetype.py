import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.devices.models import Device, DeviceType
from app.devices.services import DeviceService

client = TestClient(app)

@pytest.fixture(scope="function")
def db_session():
    db = next(get_db())
    yield db
    # No se realizan eliminaciones para este test; se asume que la base de datos tiene datos preexistentes.

def test_get_device_types(db_session):
    """
    Prueba para el servicio get_device_types, que debe devolver una lista de dispositivos
    con su ID, nombre del tipo y propiedades.
    """
    # Instanciar el servicio con la sesión de base de datos
    service = DeviceService(db_session)
    
    # Llamar al servicio que obtiene los tipos de dispositivos
    result = service.get_device_types()
    
    # Verificar que se obtiene una lista
    assert isinstance(result, list), "El resultado debe ser una lista"
    
    # Si la lista no está vacía, verificamos que cada elemento tiene las claves esperadas.
    if result:
        for item in result:
            assert "id" in item, "Cada elemento debe tener la clave 'id'"
            assert "name" in item, "Cada elemento debe tener la clave 'name'"
            assert "properties" in item, "Cada elemento debe tener la clave 'properties'"
