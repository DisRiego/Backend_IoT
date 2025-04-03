import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.devices.models import (
    DeviceIot,
    Vars,
    MaintenanceInterval,
    Lot,
    PropertyLot
)
from app.devices.schemas import DeviceReassignRequest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import random

client = TestClient(app)

# Fixture para obtener la sesión de base de datos;
# en esta prueba no eliminamos los dispositivos creados.
@pytest.fixture(scope="function")
def db_session():
    db = next(get_db())
    devices_ids = []
    yield db, devices_ids
    devices_ids.clear()

# Función auxiliar para crear un dispositivo de prueba que se crea asignado inicialmente al lote 2
# y con estado "Operativo" (ID 11).
def create_test_device_assigned_to_lot(db: Session, devices_ids: list, lot_id: int = 2, status_id: int = 11) -> int:
    device_data = {
        "serial_number": random.randint(100000000, 999999999),
        "model": "DeviceTestModel",
        "lot_id": lot_id,  # Se crea asignado al lote original (id 2)
        "installation_date": datetime.utcnow().isoformat(),
        "maintenance_interval_id": 1,  # Se asume que este intervalo existe
        "estimated_maintenance_date": (datetime.utcnow() + timedelta(days=365)).isoformat(),
        "status": status_id,  # Estado "Operativo"
        "devices_id": 1,
        "price_device": {"price": 2500},
        "data_devices": {"sensor_data": 100}
    }
    response = client.post("/devices/", json=device_data)
    assert response.status_code == 201, f"Error creando dispositivo: {response.json()}"
    device_id = response.json()["data"]["device"]["id"]
    devices_ids.append(device_id)
    return device_id

# Función auxiliar para asegurar que la relación entre un lote y un predio existe.
# En este caso, se espera que exista una relación entre el nuevo lote (id_new) y el predio (property_id).
def ensure_property_lot_relation(db: Session, lot_id: int, property_id: int):
    from app.devices.models import PropertyLot  # Importación local para evitar conflictos
    rel = db.query(PropertyLot).filter(
        PropertyLot.lot_id == lot_id,
        PropertyLot.property_id == property_id
    ).first()
    if not rel:
        rel = PropertyLot(property_id=property_id, lot_id=lot_id)
        db.add(rel)
        db.commit()
    return rel

# Prueba para el servicio reassign_to_lot
# Se asume que:
#   - Existe un dispositivo creado asignado inicialmente al lote 2.
#   - Existe una relación entre el predio (property_id=7) y el lote original (id=2).
#   - Existe (o se ha creado previamente en el entorno de test) un nuevo lote con id 3
#     que esté relacionado con el mismo predio (property_id=7).
@pytest.mark.asyncio
async def test_reassign_device_to_lot(db_session: Session):
    db, devices_ids = db_session

    # 1. Crear un dispositivo de prueba asignado inicialmente al lote 2, estado "Operativo" (ID 11)
    original_device_id = create_test_device_assigned_to_lot(db, devices_ids, lot_id=2, status_id=11)

    # 2. Asegurar que existe la relación entre el predio (property_id=7) y el lote original (id 2)
    ensure_property_lot_relation(db, lot_id=2, property_id=7)

    # 3. Verificar (o asumir) que ya existe un nuevo lote con id 3 y que está relacionado con el predio 7.
    #    En un entorno real, se debería crear este nuevo lote o disponerlo en la BD de test.
    new_lot_id = 3
    rel_new = ensure_property_lot_relation(db, lot_id=new_lot_id, property_id=7)
    assert rel_new is not None, "La relación entre el nuevo lote (id 3) y el predio (id 7) no existe"

    # 4. Preparar los datos de reasignación
    new_installation_date = datetime.utcnow()
    new_estimated_maintenance_date = new_installation_date + timedelta(days=180)
    reassignment_payload = {
        "device_id": original_device_id,
        "lot_id": new_lot_id,  # Nuevo lote al que se reasigna
        "installation_date": new_installation_date.isoformat(),
        "maintenance_interval_id": 1,  # Se asume que este intervalo existe
        "estimated_maintenance_date": new_estimated_maintenance_date.isoformat(),
        "property_id": 7  # Predio existente
    }

    # 5. Invocar el endpoint para reasignar el dispositivo al nuevo lote
    response = client.post("/devices/reassign", json=reassignment_payload)
    assert response.status_code == 200, f"Error en reasignación: {response.json()}"
    json_resp = response.json()
    assert json_resp["success"] is True, f"Reasignación no exitosa: {json_resp}"
    
    data = json_resp["data"]
    # 6. Verificar que el dispositivo pasó a estar asignado al nuevo lote (id 3)
    #    y que se devuelve el lote anterior (id 2).
    assert data["new_lot_id"] == new_lot_id, "El nuevo lote asignado no es el esperado"
    assert data["previous_lot_id"] == 2, "El lote anterior no es el esperado"
    # 7. Verificar que la fecha de instalación se actualizó correctamente.
    assert data["installation_date"] == new_installation_date.isoformat(), "La fecha de instalación no se actualizó correctamente"
    # (Otras comprobaciones sobre intervalos y nombres pueden agregarse según la lógica del servicio.)
