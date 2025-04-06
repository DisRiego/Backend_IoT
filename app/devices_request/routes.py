from fastapi import APIRouter, Body, Depends, Form, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime
from app.database import get_db
from app.devices_request.services import DeviceRequestService

router = APIRouter(prefix="/devices-request", tags=["DevicesRequest"])

@router.get("/type-open/", response_model=Dict)
def get_type_open(db: Session = Depends(get_db)):
    """Obtener todos los tipos de apertura"""
    device_service = DeviceRequestService(db)
    return device_service.get_type_open()

@router.post("/create-request/", response_model=Dict)
async def create_request(
    request: dict = Body(...),  # Acepta el cuerpo completo como un JSON
    db: Session = Depends(get_db)
):
    """Creación de solicitud de apertura de válvula"""
    try:
        type_opening_id = request["type_opening_id"]
        # status = request["status"]
        lot_id = request["lot_id"]
        user_id = request["user_id"]
        device_iot_id = request["device_iot_id"]
        open_date = datetime.strptime(request["open_date"], "%Y-%m-%dT%H:%M:%S")
        close_date = datetime.strptime(request["close_date"], "%Y-%m-%dT%H:%M:%S")
        # request_date = datetime.strptime(request["request_date"], "%Y-%m-%dT%H:%M:%S")
        volume_water = request["volume_water"]
        # Creamos una instancia del servicio para manejar la creación de la solicitud
        device_service = DeviceRequestService(db)

        # Llamamos al método para crear la solicitud
        response = await device_service.create_request(
            type_opening_id=type_opening_id,
            lot_id=lot_id,
            user_id=user_id,
            device_iot_id=device_iot_id,
            open_date=open_date,
            close_date=close_date,
            volume_water=volume_water
        )

        return response
    except HTTPException as e:
        raise e  # Re-lanzamos la excepción si ya se manejó aquí
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear la solicitud: {str(e)}")
    
@router.get("/request/{request_id}", response_model=Dict)
def get_request_by_id(request_id : int, db : Session = Depends(get_db)):
    """Obtener solicitud de apertura por ID"""
    device_service = DeviceRequestService(db)
    return device_service.get_request_by_id(request_id)

@router.get("/request/", response_model=Dict)
def get_request_by_id(db : Session = Depends(get_db)):
    """Obtener solicitudes de apertura"""
    device_service = DeviceRequestService(db)
    return device_service.get_all_requests()

@router.put("/update-request/{request_id}", response_model=Dict)
async def update_request(
    request_id: int,  # ID de la solicitud a actualizar
    request: dict = Body(...),  # Cuerpo de la solicitud con los datos a actualizar
    db: Session = Depends(get_db)
):
    """Actualizar solicitud de apertura de válvula"""
    try:
        # Extraer los campos del JSON recibido
        type_opening_id = request["type_opening_id"]
        user_id = request["user_id"]
        open_date = datetime.strptime(request["open_date"], "%Y-%m-%dT%H:%M:%S")
        close_date = datetime.strptime(request["close_date"], "%Y-%m-%dT%H:%M:%S")
        volume_water = request["volume_water"]

        # Creamos una instancia del servicio para manejar la edición de la solicitud
        device_service = DeviceRequestService(db)

        # Llamamos al método para actualizar la solicitud
        response = await device_service.update_request(
            request_id=request_id,
            type_opening_id=type_opening_id,
            user_id=user_id,
            open_date=open_date,
            close_date=close_date,
            volume_water=volume_water
        )

        return response
    except HTTPException as e:
        raise e  # Re-lanzamos la excepción si ya se manejó aquí
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar la solicitud: {str(e)}")
    
@router.get("/device-detail/{device_id}", response_model=Dict)
def get_device_detail(device_id: int, db: Session = Depends(get_db)):
    """Obtener los detalles de un dispositivo IoT"""
    try:
        # Crear una instancia del servicio DeviceRequestService
        device_service = DeviceRequestService(db)
        
        # Llamamos al método get_device_detail para obtener los detalles del dispositivo
        return device_service.get_device_detail(device_id)
    
    except HTTPException as e:
        raise e  # Re-lanzamos HTTPException si ya fue manejada
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener los detalles del dispositivo: {str(e)}")
    
@router.post("/approve-reject-request/", response_model=Dict)
async def approve_or_reject_request(
    request_id: int,  # ID de la solicitud
    status: int,  # Estado: 16 para aprobado, 18 para rechazado
    justification: Optional[str] = None,  # Justificación solo cuando es rechazado
    db: Session = Depends(get_db)
):
    """Aprobar o rechazar solicitud de apertura de válvula"""
    try:
        # Creamos una instancia del servicio
        device_service = DeviceRequestService(db)

        # Llamamos al método para aprobar o rechazar la solicitud
        response = await device_service.approve_or_reject_request(
            request_id=request_id,
            status=status,
            justification=justification
        )

        return response
    except HTTPException as e:
        raise e  # Re-lanzamos la excepción si ya se manejó aquí
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al aprobar o rechazar la solicitud: {str(e)}")
