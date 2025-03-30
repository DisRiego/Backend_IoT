from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


# ---------- Categoría de dispositivos ----------
class DeviceCategoryBase(BaseModel):
    """
    Categoría general de dispositivos (IoT, Fuente de energía, Conectividad).
    """
    name: str
    description: Optional[str] = None


class DeviceCategoryResponse(DeviceCategoryBase):
    """
    Representación de una categoría de dispositivo para respuestas.
    """
    id: int

    class Config:
        orm_mode = True


# ---------- Plantilla de propiedades de un dispositivo ----------
class DeviceTypeWithProperties(BaseModel):
    """
    Representación mínima de un tipo de dispositivo para el frontend.

    Contiene:
    - id: identificador del tipo de dispositivo
    - name: nombre del tipo de dispositivo (ej. batería, relé, etc.)
    - properties: estructura dinámica de campos para generar formularios
    """
    id: int
    name: str
    properties: Dict[str, Any]

    class Config:
        orm_mode = True


# # ---------- Tipo de dispositivo ----------
# class DeviceTypeBase(BaseModel):
#     """
#     Tipo específico de dispositivo (válvula, batería, relé, etc.).
#     """
#     name: str
#     device_category_id: int


# class DeviceTypeResponse(DeviceTypeBase):
#     """
#     Representación de un tipo de dispositivo con su categoría y plantilla de propiedades.
#     """
#     id: int
#     category: Optional[DeviceCategoryResponse]
#     devices: List[DeviceTemplateResponse]

#     class Config:
#         orm_mode = True


# ---------- Intervalos de mantenimiento (opcional) ----------
class MaintenanceIntervalResponse(BaseModel):
    """
    Intervalo de mantenimiento asociado a un dispositivo IoT.
    """
    id: int
    name: str
    days: int

    class Config:
        orm_mode = True


# ---------- Dispositivo IoT registrado ----------
class DeviceIOTBase(BaseModel):
    """
    Datos fijos y personalizados de un dispositivo IoT registrado.
    """
    serial_number: int
    model: str
    lot_id: int
    user_id: int
    installation_date: Optional[datetime]
    maintenance_interval_id: Optional[int]
    estimated_maintenance_date: Optional[datetime]
    status: Optional[int] = 11
    devices_id: int
    price_device: Dict[str, Any]


class DeviceIOTCreate(DeviceIOTBase):
    """
    Schema para registrar un nuevo dispositivo IoT.
    """
    pass


class DeviceIOTResponse(DeviceIOTBase):
    """
    Representación completa de un dispositivo IoT para respuesta.
    """
    id: int
    device_type: str
    document_number: Optional[int]

    class Config:
        orm_mode = True

class DeviceCreateResponse(BaseModel):
    """
    Respuesta al registrar un nuevo dispositivo IoT.
    """
    status: str
    message: str
    data: DeviceIOTResponse
