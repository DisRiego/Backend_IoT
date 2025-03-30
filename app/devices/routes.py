from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.devices.services import DeviceService
from app.devices.schemas import (
    DeviceIOTCreate,
    DeviceIOTResponse,
    DeviceTypeWithProperties,
    DeviceCreateResponse  
)
from typing import List


router = APIRouter(prefix="/devices", tags=["Devices"])


@router.get("/types", response_model=List[DeviceTypeWithProperties])
def get_device_types(db: Session = Depends(get_db)):
    """
    Obtener todos los tipos de dispositivos con su estructura de propiedades y categoría.

    Este endpoint se usa en el frontend para construir formularios dinámicos según el tipo.
    """
    service = DeviceService(db)
    return service.get_device_types()


@router.post("/", response_model=DeviceCreateResponse, status_code=201)
def create_device_iot(device_data: DeviceIOTCreate, db: Session = Depends(get_db)):
    """
    Registrar un nuevo dispositivo IoT con datos fijos y propiedades específicas.
    """
    service = DeviceService(db)
    new_device = service.create_device_iot(device_data)

    return {
        "status": "success",
        "message": "Dispositivo creado correctamente",
        "data": new_device
    }


@router.get("/", response_model=List[DeviceIOTResponse])
def get_all_devices(db: Session = Depends(get_db)):
    service = DeviceService(db)
    return service.get_device_iot()


@router.get("/iot", response_model=List[DeviceIOTResponse])
def get_devices_iot(db: Session = Depends(get_db)):
    service = DeviceService(db)
    return service.get_device_iot("IoT")


@router.get("/energia", response_model=List[DeviceIOTResponse])
def get_devices_energia(db: Session = Depends(get_db)):
    service = DeviceService(db)
    return service.get_device_iot("Fuente de energía")


@router.get("/conectividad", response_model=List[DeviceIOTResponse])
def get_devices_conectividad(db: Session = Depends(get_db)):
    service = DeviceService(db)
    return service.get_device_iot("Conectividad")

