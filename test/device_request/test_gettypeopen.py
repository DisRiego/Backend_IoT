import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.devices_request.models import TypeOpen

client = TestClient(app)

# Fixture para la base de datos
@pytest.fixture
def db_session():
    db = SessionLocal()  # Crear una nueva sesión de base de datos
    yield db
    db.close()

# Test para `get_type_open`
def test_get_type_open(db_session):
    # Asegurarse de que haya datos en la tabla de tipo de apertura
    types_of_opening = db_session.query(TypeOpen).all()
    
    # Si no hay datos, insertar un tipo de apertura para que la prueba funcione
    if not types_of_opening:
        type_opening = TypeOpen(type_opening="Apertura nueva")
        db_session.add(type_opening)
        db_session.commit()
        types_of_opening = [type_opening]
    
    # Llamar al servicio get_type_open
    response = client.get("/devices-request/type-open/")

    # Verificar que la respuesta sea exitosa (status_code 200)
    assert response.status_code == 200
    data = response.json()

    # Verificar que la respuesta contiene los tipos de apertura
    assert "success" in data, "Falta el campo 'success' en la respuesta"
    assert data["success"] is True, "El campo 'success' debe ser True"
    assert "data" in data, "Falta el campo 'data' en la respuesta"
    
    # Verificar que la respuesta contiene al menos un tipo de apertura
    assert len(data["data"]) > 0, "La respuesta no contiene tipos de apertura"

    # Verificar que los tipos de apertura de la base de datos están en la respuesta
    for type_opening in types_of_opening:
        # Acceder a 'type_opening' directamente desde el diccionario
        assert any(type_opening.type_opening == type_opening_data['type_opening'] for type_opening_data in data["data"]), \
            f"No se encontró el tipo de apertura '{type_opening.type_opening}' en los resultados"
