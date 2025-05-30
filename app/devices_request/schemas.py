from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class DeviceBase(BaseModel):
    """Esquema base para los dispositivos"""
    serial_number: Optional[int] = None
    model: Optional[str] = None
    lot_id: Optional[int] = None
    installation_date: Optional[datetime] = None
    maintenance_interval_id: Optional[int] = None
    estimated_maintenance_date: Optional[datetime] = None
    status: Optional[int] = None
    devices_id: Optional[int] = None
    price_device: Optional[Dict[str, Any]] = None

class RequestCreate(BaseModel):
    type_opening_id: int = Field(..., title="ID del tipo de apertura")
    lot_id: int           = Field(..., title="ID del lote")
    user_id: int          = Field(..., title="ID del usuario")
    device_iot_id: int    = Field(..., title="ID del dispositivo IoT")
    open_date: datetime   = Field(..., title="Fecha de apertura")
    close_date: datetime  = Field(..., title="Fecha de cierre")
    volume_water: Optional[int] = Field(..., title="Volumen de agua en litros")

    class Config:
        from_attributes = True

class ApproveRequest(BaseModel):
    request_id: int = Field(..., title="ID de la solicitud a aprobar")

class RejectRequest(BaseModel):
    request_id: int      = Field(..., title="ID de la solicitud a rechazar")
    justification: int   = Field(..., title="ID de la razón de rechazo (justification)")



class RejectRequest(BaseModel):
    request_id: int      = Field(..., title="ID de la solicitud a rechazar")
    reason_id: int       = Field(..., title="ID de la razón de rechazo")
    comment: Optional[str] = Field(None, title="Comentario adicional")

