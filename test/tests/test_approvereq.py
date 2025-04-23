import pytest
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.devices_request.services import DeviceRequestService
from app.devices_request.models import Request, Vars
from app.devices.models import DeviceIot
import json 

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

def test_approve_request_success(db_session):
    # Crear dispositivo
    device = DeviceIot(
        serial_number=999123,
        model="Modelo X",
        lot_id=1,
        installation_date=datetime.now(),
        estimated_maintenance_date=datetime.now() + timedelta(days=30),
        status=11,
        devices_id=1,
        price_device=None
    )
    db_session.add(device)
    db_session.commit()
    db_session.refresh(device)

    # Asegurar Vars con estado 18 (Pendiente) y 17 (Aprobado) existen
    for status_id, name in [(18, "Pendiente"), (17, "Aprobado")]:
        if not db_session.query(Vars).filter_by(id=status_id).first():
            db_session.add(Vars(id=status_id, name=name))
    if not db_session.query(Vars).filter_by(id=20).first():
        db_session.add(Vars(id=20, name="En espera"))
    db_session.commit()

    # Crear solicitud pendiente asociada al dispositivo
    request = Request(
        type_opening_id=1,
        status=18,
        lot_id=device.lot_id,
        user_id=1,
        device_iot_id=device.id,
        open_date=datetime.now(),
        close_date=datetime.now() + timedelta(hours=1),
        request_date=datetime.now(),
        volume_water=100
    )
    db_session.add(request)
    db_session.commit()
    db_session.refresh(request)

    # Aprobar solicitud
    service = DeviceRequestService(db_session)
    response = service.approve_request(request.id)
    body = json.loads(response.body)
    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["title"] == "Solicitud aprobada"

    # Verificar que los estados se actualizaron
    updated_request = db_session.query(Request).get(request.id)
    updated_device = db_session.query(DeviceIot).get(device.id)
    assert updated_request.status == 17  # Aprobado
    assert updated_device.status == 20   # En espera
