import pytest
from app.devices_request.services import DeviceRequestService
from app.database import SessionLocal
from app.devices.models import PropertyUser, PropertyLot, User

# Fixture para configurar la base de datos de prueba
@pytest.fixture
def db_session():
    # Crear una sesión de base de datos temporal para la prueba
    db = SessionLocal()
    try:
        yield db  # Esto proporciona la base de datos a las pruebas
    finally:
        db.rollback()  # Deshacer cualquier cambio después de la prueba
        db.close()

# Prueba para el servicio _get_lot_owner_id
def test_get_lot_owner_id(db_session):
    # Usamos el user_id = 2, lote_id = 1
    user_id = 2
    lot_id = 1
    
    # Simulamos la relación de propiedades y usuarios en la base de datos
    property_user = PropertyUser(user_id=user_id, property_id=7)
    property_lot = PropertyLot(property_id=7, lot_id=lot_id)
    
    db_session.add(property_user)
    db_session.add(property_lot)
    db_session.commit()

    # Llamamos al servicio _get_lot_owner_id
    service = DeviceRequestService(db_session)
    owner_id = service._get_lot_owner_id(lot_id)

    # Verificamos que el id del dueño sea el correcto
    assert owner_id == user_id, f"Esperado dueño con id {user_id}, pero se obtuvo {owner_id}"
