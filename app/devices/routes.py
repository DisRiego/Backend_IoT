from fastapi import APIRouter, Depends, Form, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.devices.schemas import DeviceAssignRequest, DeviceReassignRequest
from app.database import get_db
from app.devices.services import DeviceService
from app.devices.schemas import (
    DeviceCreate, 
    DeviceUpdate, 
    DeviceDetail,
    DeviceAssignRequest,
    DeviceStatusChange,
    DeviceFilter,
    DeviceIotReadingUpdateByLot
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
def update_sensor_data_by_lot(data: dict, db: Session = Depends(get_db)):
    """
    Recibe el JSON del Arduino y actualiza el registro operativo en device_iot.
    Se espera un JSON con, al menos:
      - device_id: ID del dispositivo operativo
      - lot_id: ID del lote
      - (otros campos que se guardarán en price_device)
    """
    device_service = DeviceService(db)
    return device_service.update_device_reading_by_lot(data)

