from fastapi import APIRouter, Depends, Form, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi.encoders import jsonable_encoder
from app.devices.schemas import DeviceAssignRequest, DeviceReassignRequest
from app.database import get_db
from app.devices_request.models import Request , DeviceIoT
from app.devices.services import DeviceService
from app.devices.models import User, Notification 
from app.devices.schemas import (
    DeviceCreate, 
    DeviceUpdate, 
    DeviceDetail,
    DeviceAssignRequest,
    DeviceStatusChange,
    DeviceFilter,
    DeviceIotReadingUpdateByLot,
    ServoCommand,
    ValveDevice
)

router = APIRouter(prefix="/devices", tags=["Devices"])

@router.get("/", response_model=Dict[str, Any])
def get_all_devices(db: Session = Depends(get_db)):
    """Obtener todos los dispositivos con información operativa"""
    device_service = DeviceService(db)
    return device_service.get_all_devices()

@router.get("/category/{category_id}", response_model=Dict[str, Any])
def get_devices_by_category(category_id: int, db: Session = Depends(get_db)):
    """Obtener dispositivos por categoría, junto con la información del lote, predio y propietario"""
    device_service = DeviceService(db)
    return device_service.get_devices_by_category(category_id)

@router.get("/device_types_with_readings", response_model=List[dict])
def get_device_types_with_readings(db: Session = Depends(get_db)):
    """Obtener tipos de dispositivos con sus propiedades (en JSON) y lecturas de sensores"""
    device_service = DeviceService(db)
    return device_service.get_device_types()


@router.get("/{device_id}", response_model=Dict[str, Any])
def get_device_by_id(device_id: int, db: Session = Depends(get_db)):
    """Obtener detalles de un dispositivo específico con ID del predio"""
    device_service = DeviceService(db)
    return device_service.get_device_by_id(device_id)


@router.post("/", response_model=Dict[str, Any])
def create_device(device: DeviceCreate, db: Session = Depends(get_db)):
    """Crear un nuevo dispositivo"""
    device_service = DeviceService(db)
    return device_service.create_device(device)

@router.put("/{device_id}", response_model=Dict[str, Any])
def update_device(device_id: int, device: DeviceUpdate, db: Session = Depends(get_db)):
    """Actualizar información de un dispositivo"""
    device_service = DeviceService(db)
    return device_service.update_device(device_id, device)

@router.put("/{device_id}/status", response_model=Dict[str, Any])
def update_device_status(
    device_id: int,
    new_status: int = Form(...),  # ID del estado (activo/inactivo)
    db: Session = Depends(get_db)
):
    """
    Actualizar el estado de un dispositivo (habilitar/inhabilitar)
    - new_status debe ser el ID correspondiente , # Los valores válidos para device_status[11, 12, 13, 14, 15, 16]  
    """
    device_service = DeviceService(db)
    return device_service.update_device_status(device_id, new_status)


@router.get("/maintenance_intervals/{interval_id}", response_model=Dict[str, Any])
def get_maintenance_interval_by_id(interval_id: int, db: Session = Depends(get_db)):
    """Obtener un intervalo de mantenimiento por su id"""
    device_service = DeviceService(db)
    return device_service.get_maintenance_interval_by_id(interval_id)


@router.post("/assign", response_model=Dict[str, Any])
def assign_device_to_lot(
    assignment_data: DeviceAssignRequest,
    db: Session = Depends(get_db),
):
    """Asignar un dispositivo a un lote específico con fecha de instalación e intervalo de mantenimiento"""
    device_service = DeviceService(db)
    return device_service.assign_to_lot(assignment_data)

@router.post("/reassign", response_model=Dict[str, Any])
def reassign_device_to_lot(
    reassignment_data: DeviceReassignRequest,
    db: Session = Depends(get_db),
):
    """Reasignar un dispositivo a otro lote"""
    device_service = DeviceService(db)
    return device_service.reassign_to_lot(reassignment_data, None)


@router.get("/maintenance_intervals/", response_model=Dict[str, Any])
def get_all_maintenance_intervals(db: Session = Depends(get_db)):
    """Obtener todos los intervalos de mantenimiento"""
    device_service = DeviceService(db)
    return device_service.get_all_maintenance_intervals()

@router.get("/lot/{lot_id}", response_model=Dict[str, Any])
def get_devices_by_lot(lot_id: int, db: Session = Depends(get_db)):
    """Obtener todos los dispositivos asignados a un lote específico"""
    device_service = DeviceService(db)
    return device_service.get_devices_by_lot(lot_id)

@router.get("/filter/", response_model=Dict[str, Any])
def filter_devices(
    serial_number: Optional[int] = None,
    model: Optional[str] = None,
    lot_id: Optional[int] = None,
    status: Optional[int] = None,
    device_type_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Filtrar dispositivos según múltiples criterios con paginación
    
    - serial_number: Número de serie del dispositivo
    - model: Modelo del dispositivo (búsqueda parcial)
    - lot_id: ID del lote al que está asignado
    - status: Estado del dispositivo (activo, inactivo, etc.)
    - device_type_id: Tipo de dispositivo
    - page: Número de página a mostrar
    - page_size: Cantidad de elementos por página
    """
    device_service = DeviceService(db)
    return device_service.filter_devices(
        serial_number=serial_number,
        model=model,
        lot_id=lot_id,
        status=status,
        device_type_id=device_type_id,
        page=page,
        page_size=page_size
    )

        

@router.post("/sensor_update_by_lot", response_model=Dict[str, Any])
def update_sensor_data_by_lot(
    reading: DeviceIotReadingUpdateByLot,
    db: Session = Depends(get_db)
):
    device_service = DeviceService(db)
    return device_service.update_device_reading_by_lot(reading)

@router.get("/notifications/user/{user_id}", response_model=Dict[str, Any])
def get_user_notifications(
    user_id: int, 
    limit: int = Query(50, ge=1, le=100), 
    unread_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """Obtener notificaciones de un usuario"""
    try:
        # Verificar si el usuario existe
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Consultar las notificaciones
        query = db.query(Notification).filter(Notification.user_id == user_id)
        
        if unread_only:
            query = query.filter(Notification.read == False)
            
        notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()

        return {
            "success": True,
            "data": jsonable_encoder(notifications)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener las notificaciones: {str(e)}")

@router.put("/notifications/{notification_id}/read", response_model=Dict[str, Any])
def mark_notification_as_read(notification_id: int, db: Session = Depends(get_db)):
    """Marcar una notificación específica como leída"""
    try:
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if not notification:
            raise HTTPException(status_code=404, detail="Notificación no encontrada")

        notification.read = True
        db.commit()
        db.refresh(notification)

        return {
            "success": True,
            "data": {
                "title": "Notificaciones",
                "message": "Notificación marcada como leída correctamente"
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al marcar la notificación como leída: {str(e)}")

@router.put("/notifications/user/{user_id}/read-all", response_model=Dict[str, Any])
def mark_all_notifications_as_read(user_id: int, db: Session = Depends(get_db)):
    """Marcar todas las notificaciones de un usuario como leídas"""
    try:
        # Verificar si el usuario existe
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Marcar todas las notificaciones no leídas como leídas
        result = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.read == False
        ).update({"read": True})
        
        db.commit()

        return {
            "success": True,
            "data": {
                "title": "Notificaciones",
                "message": f"Se han marcado {result} notificaciones como leídas"
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al marcar las notificaciones como leídas: {str(e)}")


_servo_action: Dict[str, str] = {"action": None}

@router.post("/devices/servo-command", response_model=Dict[str, str])
def set_servo_command(command: ServoCommand):
    """
    Establece el comando del servo. action debe ser "open" o "close".
    """
    global _servo_action
    if command.action not in ("open", "close"):
        return {"error": "action debe ser 'open' o 'close'"}
    _servo_action["action"] = command.action
    return {"action": command.action}

@router.get("/devices/servo-command", response_model=Dict[str,str])
def get_servo_command():
    """
    Devuelve el comando pendiente para el servo y luego lo limpia.
    """
    global _servo_action
    cmd = _servo_action.get("action")
    # Una vez leído, lo borramos para no reenviarlo
    _servo_action["action"] = None
    return {"action": cmd or ""}

@router.post("/devices/open-valve", response_model=Dict[str, str])
def open_valve(payload: ValveDevice, db: Session = Depends(get_db)):
    device_id = payload.device_id
    now = datetime.now()  # hora local
    print(f"[open-valve] now={now.isoformat()} comprobando solicitud")

    active_request = (
        db.query(Request)
          .filter(
              Request.device_iot_id == device_id,
              Request.status == 17,
              Request.open_date <= now,
              Request.close_date >= now
          )
          .first()
    )
    if not active_request:
        raise HTTPException(status_code=403, detail="No hay una solicitud activa en este momento.")

    device = db.query(DeviceIoT).get(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado.")

    device.status = 22  # Abierto
    db.commit()
    db.refresh(device)
    print(f"[open-valve] dispositivo {device_id} status → 22 (Abierto)")

    global _servo_action
    _servo_action["action"] = "open"

    return {"action": "open"}


@router.post("/devices/close-valve", response_model=Dict[str, str])
def close_valve(payload: ValveDevice, db: Session = Depends(get_db)):
    device_id = payload.device_id
    now = datetime.now()  # hora local
    print(f"[close-valve] now={now.isoformat()} comprobando solicitud")

    active_request = (
        db.query(Request)
          .filter(
              Request.device_iot_id == device_id,
              Request.status == 17,
              Request.open_date <= now,
              Request.close_date >= now
          )
          .first()
    )
    if not active_request:
        raise HTTPException(status_code=403, detail="No hay una solicitud activa en este momento.")

    device = db.query(DeviceIoT).get(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado.")

    device.status = 21  # Cerrado
    db.commit()
    db.refresh(device)
    print(f"[close-valve] dispositivo {device_id} status → 21 (Cerrado)")

    global _servo_action
    _servo_action["action"] = "close"

    return {"action": "close"}