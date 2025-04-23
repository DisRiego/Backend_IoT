import pytest
from datetime import datetime, timedelta
from app.devices.models import DeviceIot, Vars
from app.devices_request.models import Request, RequestRejectionReason
from app.devices_request.services import DeviceRequestService
from app.database import SessionLocal

# ✅ Fixture de sesión de base de datos
@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


# ✅ Fixture para datos base y solicitud pendiente
@pytest.fixture
def setup_reject_dependencies(db_session):
    for id_, name in [(18, "Pendiente"), (19, "Rechazado"), (12, "No operativo")]:
        if not db_session.query(Vars).filter_by(id=id_).first():
            db_session.add(Vars(id=id_, name=name))
    db_session.commit()

    device = DeviceIot(
        serial_number=123456,
        model="Modelo Test",
        lot_id=1,
        installation_date=datetime.now(),
        estimated_maintenance_date=datetime.now() + timedelta(days=10),
        status=11,
        devices_id=1
    )
    db_session.add(device)
    db_session.commit()
    db_session.refresh(device)

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

    if not db_session.query(RequestRejectionReason).filter_by(id=999).first():
        reason = RequestRejectionReason(id=999, description="Razón válida de prueba")
        db_session.add(reason)
        db_session.commit()

    return {"device": device, "request": request, "reason_id": 999}


# ✅ Test exitoso
def test_reject_request_success(db_session, setup_reject_dependencies):
    service = DeviceRequestService(db_session)
    request = setup_reject_dependencies["request"]
    reason_id = setup_reject_dependencies["reason_id"]

    response = service.reject_request(request.id, reason_id, comment="No procede")
    assert response.status_code == 200
    assert response.body is not None


# ❌ Test solicitud no encontrada
def test_reject_request_not_found(db_session):
    service = DeviceRequestService(db_session)
    response = service.reject_request(request_id=999999, reason_id=999)
    assert response.status_code == 404


# ❌ Test razón inválida
def test_reject_request_invalid_reason(db_session, setup_reject_dependencies):
    service = DeviceRequestService(db_session)
    request = setup_reject_dependencies["request"]
    response = service.reject_request(request.id, reason_id=999999)  # inexistente
    assert response.status_code == 400

