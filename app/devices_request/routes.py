from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime
from app.database import get_db
from app.devices_request.services import DeviceRequestService
from app.devices_request.schemas import RequestCreate

router = APIRouter(prefix="/devices-request", tags=["DevicesRequest"])

@router.get("/type-open/", response_model=Dict)
def get_type_open(db: Session = Depends(get_db)):
    device_service = DeviceRequestService(db)
    return device_service.get_type_open()

@router.post("/create-request/", response_model=dict)
async def create_request(
    request_data: RequestCreate,  # Ahora usamos el esquema RequestCreate
    db: Session = Depends(get_db)
):
    try:
        # Extraer los datos del modelo
        type_opening_id = request_data.type_opening_id
        lot_id = request_data.lot_id
        user_id = request_data.user_id
        device_iot_id = request_data.device_iot_id
        open_date = request_data.open_date
        close_date = request_data.close_date
        volume_water = request_data.volume_water

        device_service = DeviceRequestService(db)
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
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear la solicitud: {str(e)}")

@router.get("/request/{request_id}", response_model=Dict)
def get_request_by_id(request_id: int, db: Session = Depends(get_db)):
    device_service = DeviceRequestService(db)
    return device_service.get_request_by_id(request_id)

@router.get("/request/", response_model=Dict)
def get_all_requests(db: Session = Depends(get_db)):
    device_service = DeviceRequestService(db)
    return device_service.get_all_requests()

@router.put("/update-request/{request_id}", response_model=Dict)
async def update_request(
    request_id: int,
    request: dict = Body(...),
    db: Session = Depends(get_db)
):
    try:
        type_opening_id = request["type_opening_id"]
        user_id = request["user_id"]
        open_date = datetime.strptime(request["open_date"], "%Y-%m-%dT%H:%M:%S")
        close_date = datetime.strptime(request["close_date"], "%Y-%m-%dT%H:%M:%S")
        volume_water = request["volume_water"]
        device_service = DeviceRequestService(db)
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
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar la solicitud: {str(e)}")

@router.get("/device-detail/{device_id}", response_model=Dict)
def get_device_detail(device_id: int, db: Session = Depends(get_db)):
    try:
        device_service = DeviceRequestService(db)
        return device_service.get_device_detail(device_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener los detalles del dispositivo: {str(e)}")

@router.post("/approve-reject-request/", response_model=dict)
def approve_or_reject_request(
    request_id: int,
    status: int,
    justification: Optional[str] = None,
    db: Session = Depends(get_db)
):
    try:
        device_service = DeviceRequestService(db)
        response = device_service.approve_or_reject_request(
            request_id=request_id,
            status=status,
            justification=justification
        )
        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al aprobar o rechazar la solicitud: {str(e)}")

