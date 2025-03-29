from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.database import get_db
from app.devices.services import DeviceService
from app.devices.schemas import PropertyCreate, PropertyResponse
from datetime import datetime


router = APIRouter(prefix="/devices", tags=["Devices"])

@router.get("/", response_model=dict)
def get_property(db: Session = Depends(get_db)):
    """
    Obtener la información de dispositivos.
    """
    try:
        device_service = DeviceService(db)
        return device_service.get_devices()
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener los dispositivos: {str(e)}")
