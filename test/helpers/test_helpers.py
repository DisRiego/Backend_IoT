import random
import uuid
from datetime import datetime, timedelta
from app.devices.models import DeviceIot, Device, DeviceType, DeviceCategories, Lot
from app.devices_request.models import Vars, User
from sqlalchemy.orm import Session

# Helper para crear un dispositivo IoT
def create_device(db: Session, lot_id: int, devices_id: int) -> DeviceIot:
    status = db.query(Vars).filter(Vars.id == 15).first()  # Asumiendo 15 como estado activo
    if not status:
        status = Vars(id=15, name="Activo", type="status")
        db.add(status)
        db.commit()
        db.refresh(status)

    device_iot = DeviceIot(
        serial_number=random.randint(100000000, 999999999),
        model=f"DeviceModel-{uuid.uuid4().hex[:8]}",
        lot_id=lot_id,
        installation_date=datetime.now(),
        maintenance_interval_id=random.randint(1, 5),
        estimated_maintenance_date=datetime.now() + timedelta(days=random.randint(30, 365)),
        status=status.id,
        devices_id=devices_id,
        price_device={"price": random.randint(1000, 5000)},
        data_devices={"sensor_data": random.randint(10, 100)}
    )

    db.add(device_iot)
    db.commit()
    db.refresh(device_iot)
    return device_iot

# Helper para crear un tipo de dispositivo
def create_device_type(db: Session, category_id: int) -> DeviceType:
    device_type = DeviceType(
        name=f"DeviceType-{uuid.uuid4().hex[:8]}",
        device_category_id=category_id
    )

    db.add(device_type)
    db.commit()
    db.refresh(device_type)
    return device_type

# Helper para crear una categoría de dispositivo
def create_device_category(db: Session) -> DeviceCategories:
    device_category = DeviceCategories(
        name=f"Category-{uuid.uuid4().hex[:8]}",
        description="Descripción de la categoría."
    )

    db.add(device_category)
    db.commit()
    db.refresh(device_category)
    return device_category

# Helper para crear un lote
def create_lot(db: Session, property_id: int) -> Lot:
    lot = Lot(
        name=f"Lot-{uuid.uuid4().hex[:8]}",
        longitude=random.uniform(-180, 180),
        latitude=random.uniform(-90, 90),
        extension=random.uniform(1, 100),
        real_estate_registration_number=random.randint(100000, 999999),
        property_id=property_id
    )

    db.add(lot)
    db.commit()
    db.refresh(lot)
    return lot

# Helper para crear un usuario
def create_user(db: Session) -> User:
    user = User(
        name=f"User-{uuid.uuid4().hex[:8]}",
        document_number=str(random.randint(100000000, 999999999))
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# Helper para asignar un dispositivo a un lote
def assign_device_to_lot(db: Session, device_id: int, lot_id: int) -> DeviceIot:
    device = db.query(DeviceIot).filter(DeviceIot.id == device_id).first()
    if not device:
        raise Exception("Dispositivo no encontrado.")
    
    device.lot_id = lot_id
    db.commit()
    db.refresh(device)
    return device

# Helper para actualizar el estado de un dispositivo
def update_device_status(db: Session, device_id: int, new_status: int) -> DeviceIot:
    device = db.query(DeviceIot).filter(DeviceIot.id == device_id).first()
    if not device:
        raise Exception("Dispositivo no encontrado.")
    
    device.status = new_status
    db.commit()
    db.refresh(device)
    return device

# Helper para verificar si un dispositivo existe
def check_device_exists(db: Session, device_id: int) -> bool:
    device = db.query(DeviceIot).filter(DeviceIot.id == device_id).first()
    return device is not None

# Helper para limpiar dispositivos
def clean_up_devices(db: Session, device_ids: list) -> None:
    db.query(DeviceIot).filter(DeviceIot.id.in_(device_ids)).delete(synchronize_session=False)
    db.commit()

# Helper para limpiar lotes
def clean_up_lots(db: Session, lot_ids: list) -> None:
    db.query(Lot).filter(Lot.id.in_(lot_ids)).delete(synchronize_session=False)
    db.commit()

# Helper para limpiar categorías de dispositivos
def clean_up_device_categories(db: Session, category_ids: list) -> None:
    db.query(DeviceCategories).filter(DeviceCategories.id.in_(category_ids)).delete(synchronize_session=False)
    db.commit()

# Helper para limpiar usuarios
def clean_up_users(db: Session, user_ids: list) -> None:
    db.query(User).filter(User.id.in_(user_ids)).delete(synchronize_session=False)
    db.commit()
