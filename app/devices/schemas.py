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
    status: Optional[int] = 15
    devices_id: Optional[int] = None
    price_device: Optional[Dict[str, Any]] = None

class DeviceCreate(DeviceBase):
    """Esquema para crear un dispositivo"""
    # Campos obligatorios pueden definirse aquí
    serial_number: int
    model: str
    devices_id: int  # Tipo de dispositivo

class DeviceUpdate(DeviceBase):
    """Esquema para actualizar un dispositivo"""
    # Se mantienen todos los campos opcionales para permitir actualizaciones parciales
    pass

class DeviceInDB(DeviceBase):
    """Esquema para representar un dispositivo almacenado en la base de datos"""
    id: int

    class Config:
        orm_mode = True

class DeviceResponse(BaseModel):
    """Esquema para la respuesta de dispositivos"""
    device_id: int
    serial_number: Optional[int] = None
    model: Optional[str] = None
    device_type_name: Optional[str] = None  # Nombre del tipo de dispositivo
    owner_document_number: Optional[str] = None  # Número de documento del propietario
    lot_id: Optional[int] = None
    lot_name: Optional[str] = None
    property_id: Optional[int] = None  # ID del predio
    real_estate_registration_number: Optional[int] = None
    property_state: Optional[str] = None  # Estado del predio

    class Config:
        orm_mode = True


class DeviceDetail(DeviceResponse):
    """Esquema para detalles completos de un dispositivo, incluyendo información relacionada"""
    lot_name: Optional[str] = None
    status_name: Optional[str] = None
    maintenance_interval_name: Optional[str] = None
    device_type_name: Optional[str] = None

class DeviceAssignRequest(BaseModel):
    """Esquema para asignar un dispositivo a un lote"""
    device_id: int
    lot_id: int
    installation_date: datetime
    maintenance_interval_id: int
    property_id: int  # ID del predio

class DeviceReassignRequest(DeviceAssignRequest):
    """Esquema para reasignar un dispositivo a otro lote"""
    pass

class DeviceStatusChange(BaseModel):
    """Esquema para cambiar el estado de un dispositivo"""
    device_id: int
    new_status: int  # ID del nuevo estado (ej: activo = 24, inactivo = 25)

class SimpleResponse(BaseModel):
    """Esquema para respuestas simples"""
    success: bool
    message: str
    data: Optional[Any] = None

class PaginatedDeviceResponse(BaseModel):
    """Esquema para respuestas paginadas de dispositivos"""
    total: int
    page: int
    page_size: int
    data: List[DeviceResponse]

class DeviceFilter(BaseModel):
    """Esquema para filtrar dispositivos"""
    serial_number: Optional[int] = None
    model: Optional[str] = None
    lot_id: Optional[int] = None
    status: Optional[int] = None
    devices_id: Optional[int] = None  # Tipo de dispositivo
    installed_before: Optional[datetime] = None
    installed_after: Optional[datetime] = None
    

        
class DeviceIotReadingUpdateByLot(BaseModel):
    device_id: int
    lot_id: int
    device_type_id: int
    sensor_value: Optional[int] = None  

    class Config:
        orm_mode = True
        extra = "allow"  
 

class DeviceCategoryResponse(BaseModel):
    """Esquema para la respuesta de dispositivos por categoría"""
    device_id: int
    serial_number: Optional[int] = None
    model: Optional[str] = None
    lot_id: Optional[int] = None
    lot_name: Optional[str] = None
    property_id: Optional[int] = None
    real_estate_registration_number: Optional[int] = None
    owner_document_number: Optional[str] = None  # Número de documento del propietario
    device_type_name: Optional[str] = None
    category_name: Optional[str] = None  # Nombre de la categoría

    class Config:
        orm_mode = True

