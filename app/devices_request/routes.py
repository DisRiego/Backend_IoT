from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime
from app.database import get_db
from app.devices_request.services import DeviceRequestService
from app.devices_request.schemas import RequestCreate , ApproveRequest, RejectRequest

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

@router.get("/{request_id}", response_model=Dict)
def get_request_by_id(request_id: int, db: Session = Depends(get_db)):
    """
    Obtiene una solicitud por su ID.
    """
    service = DeviceRequestService(db)
    return service.get_request_by_id(request_id)

@router.get("/", response_model=Dict)
def get_all_requests(db: Session = Depends(get_db)):
    """
    Obtiene todas las solicitudes de apertura/cierre de válvulas.
    """
    service = DeviceRequestService(db)
    return service.get_all_requests()

@router.get("/user/{user_id}", response_model=Dict)
def get_requests_by_user(user_id: int, db: Session = Depends(get_db)):
    """
    Obtiene todas las solicitudes de un usuario.
    """
    service = DeviceRequestService(db)
    result = service.get_requests_by_user(user_id)
    return result


@router.get("/request-rejection-reasons/")
def get_rejection_reasons(db: Session = Depends(get_db)):
    service = DeviceRequestService(db)
    return service.get_all_request_rejection_reasons()


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


@router.post("/reject", response_model=Dict)
def reject_request(
    body: RejectRequest,
    db: Session = Depends(get_db)
):
    service = DeviceRequestService(db)
    return service.reject_request(
        request_id=body.request_id,
        reason_id=body.reason_id,
        comment=body.comment
    )
@router.post("/approve", response_model=Dict)
def approve_request(
    body: ApproveRequest,
    db: Session = Depends(get_db)
):
    service = DeviceRequestService(db)
    return service.approve_request(body.request_id)