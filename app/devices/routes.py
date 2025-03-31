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
    - new_status debe ser el ID correspondiente (por ejemplo, 24 para activo, 25 para inactivo)
    """
    device_service = DeviceService(db)
    return device_service.update_device_status(device_id, new_status)

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

@router.delete("/{device_id}", response_model=Dict[str, Any])
def delete_device(device_id: int, db: Session = Depends(get_db)):
    """Eliminar un dispositivo (borrado lógico)"""
    device_service = DeviceService(db)
    return device_service.delete_device(device_id)

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

@router.get("/options/{device_id}", response_model=Dict[str, Any])
def device_options(device_id: int, db: Session = Depends(get_db)):
    """
    Obtener opciones disponibles para un dispositivo específico
    
    Este endpoint devuelve las acciones que se pueden realizar con un dispositivo:
    - Editar: Siempre disponible
    - Inhabilitar/Habilitar: Depende del estado actual
    - Asignar a un lote: Disponible si no tiene lote asignado
    - Ver detalles: Siempre disponible
    - Redirigir al lote: Disponible si tiene lote asignado
    """
     
    try:
        device_service = DeviceService(db)
        device_response = device_service.get_device_by_id(device_id)
        
        # Verificar si hubo error en la respuesta
        if device_response.status_code != 200:
            return device_response
        
        # Extraer datos del dispositivo
        device_data = device_response.body.decode('utf-8')
        import json
        device_info = json.loads(device_data)["data"]
        
        # Preparar opciones disponibles
        options = [
            {
                "label": "Editar",
                "action": "edit",
                "icon": "edit",
                "enabled": True
            },
            {
                "label": "Inhabilitar" if device_info["status"] == 24 else "Habilitar",
                "action": "toggle_status",
                "icon": "power_settings_new",
                "enabled": True,
                "new_status": 25 if device_info["status"] == 24 else 24
            },
            {
                "label": "Ver detalles",
                "action": "view_details",
                "icon": "visibility",
                "enabled": True
            }
        ]
        
        # Opción de asignar a lote solo si no tiene lote
        if not device_info.get("lot_id"):
            options.append({
                "label": "Asignar a un lote",
                "action": "assign_lot",
                "icon": "assignment",
                "enabled": True
            })
        # Opción de reasignar si ya tiene lote y no está inhabilitado
        elif device_info.get("status") != 25:  # Asumiendo 25 como inhabilitado
            options.append({
                "label": "Reasignar a otro lote",
                "action": "reassign_lot",
                "icon": "swap_horiz",
                "enabled": True
            })
        
        # Opción de ir al lote solo si tiene lote asignado
        if device_info.get("lot_id"):
            options.append({
                "label": "Ir al lote",
                "action": "view_lot",
                "icon": "launch",
                "enabled": True,
                "lot_id": device_info["lot_id"]
            })
        
        return {
            "success": True,
            "data": {
                "device_id": device_id,
                "options": options
            }
        }
    except Exception as e:
        return {
            "success": False,
            "data": {
                "title": "Error al obtener opciones",
                "message": f"Error: {str(e)}"
            }
        }
        

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

