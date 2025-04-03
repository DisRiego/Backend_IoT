import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.devices.models import MaintenanceInterval
from sqlalchemy.orm import Session

client = TestClient(app)

# Fixture para la sesión de base de datos. En esta prueba no eliminamos los datos creados.
@pytest.fixture(scope="function")
def db_session():
    db = next(get_db())
    yield db
    # No se limpia nada para conservar los datos en la prueba.

def ensure_maintenance_interval(db: Session, interval_id: int = 1) -> MaintenanceInterval:
    """
    Asegura que exista un intervalo de mantenimiento con el ID indicado.
    Si no existe, lo crea.
    """
    interval = db.query(MaintenanceInterval).filter(MaintenanceInterval.id == interval_id).first()
    if not interval:
        interval = MaintenanceInterval(id=interval_id, name="Intervalo estándar", days=365)
        db.add(interval)
        db.commit()
        db.refresh(interval)
    return interval

def test_get_maintenance_interval_by_id(db_session: Session):
    db = db_session

    # Aseguramos que exista el intervalo de mantenimiento con ID 1.
    expected_interval = ensure_maintenance_interval(db, interval_id=1)
    
    # Llamamos al endpoint para obtener el intervalo de mantenimiento.
    # Se asume que el endpoint para obtener un intervalo por ID es de la forma:
    # GET /devices/maintenance_intervals/{interval_id}
    response = client.get("/devices/maintenance_intervals/1")
    
    # Verificamos que la respuesta sea exitosa.
    assert response.status_code == 200, f"Error: {response.json()}"
    
    # Convertimos la respuesta a JSON.
    data = response.json()["data"]
    
    # Comprobamos que los datos del intervalo coinciden con lo que se espera.
    assert data["id"] == expected_interval.id, "El ID del intervalo no es el esperado"
    assert data["name"] == expected_interval.name, "El nombre del intervalo no coincide"
    assert data["days"] == expected_interval.days, "Los días del intervalo no coinciden"
