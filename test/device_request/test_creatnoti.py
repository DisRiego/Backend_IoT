import pytest
from datetime import datetime
from app.devices.models import Notification, User
from app.database import SessionLocal
from app.devices_request.services import DeviceRequestService
from fastapi.testclient import TestClient
from app.main import app

# Suponiendo que tenemos un TestClient para las pruebas de API
client = TestClient(app)

# Setup de base de datos simulado (si usas un DB en memoria, por ejemplo)
@pytest.fixture
def db_session():
    db = SessionLocal()  # Crear una nueva sesión de base de datos
    yield db
    db.close()

# Prueba para la creación de notificación
def test_create_notification(db_session):
    # Datos de prueba
    user_id = 2  # Ya existe en la base de datos
    title = "Notificación de prueba"
    message = "Este es un mensaje de prueba"
    notification_type = "alerta"
    
    # Crear un servicio de solicitud de dispositivo con la sesión db
    service = DeviceRequestService(db_session)
    
    # Llamar al servicio create_notification
    response = service.create_notification(user_id, title, message, notification_type)
    
    # Verificar que la respuesta sea exitosa
    assert response["success"] == True, f"Error al crear la notificación: {response['message']}"
    
    # Verificar que la notificación haya sido agregada a la base de datos
    notification = db_session.query(Notification).filter(Notification.id == response["data"]).first()
    assert notification is not None, "La notificación no se ha creado correctamente"
    
    # Verificar los valores de la notificación en la base de datos
    assert notification.user_id == user_id, f"Esperado user_id {user_id}, pero se obtuvo {notification.user_id}"
    assert notification.title == title, f"Esperado title '{title}', pero se obtuvo {notification.title}"
    assert notification.message == message, f"Esperado message '{message}', pero se obtuvo {notification.message}"
    assert notification.type == notification_type, f"Esperado type '{notification_type}', pero se obtuvo {notification.type}"

    # Si queremos que la prueba también incluya las notificaciones al propietario del lote o a los administradores,
    # podemos agregar validaciones adicionales para esas notificaciones en la misma prueba o hacer pruebas separadas.
    
    # Verificamos que la notificación haya sido guardada correctamente
    notifications = db_session.query(Notification).all()
    assert len(notifications) > 0, "No se han encontrado notificaciones"
