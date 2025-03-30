from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.devices.models import Device, DeviceType, DeviceCategory, DeviceIOT, User
from app.devices.schemas import DeviceIOTCreate
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional


class DeviceService:
    """
    Servicio para la gestión de dispositivos:
    tipos, plantillas, dispositivos registrados.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_device_types(self) -> List[dict]:
        """
        Obtener tipos de dispositivos con sus propiedades
        """
        try:
            Devices = (
                self.db.query(Device)
                .join(DeviceType)
                .all()
            )
            # Para cada tipo, solo retornar lo que se necesita
            result = []
            for d in Devices:
                result.append({
                    "id": d.id,  # <-- ID de la tabla `devices`
                    "name": d.device_type.name,  # nombre del tipo (válvula, batería, etc.)
                    "properties": d.properties  # plantilla para construir formulario
                })
            
            return result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al obtener los tipos de dispositivos: {str(e)}")

    def create_device_iot(self, device_data: DeviceIOTCreate) -> DeviceIOT:
        """
        Registrar un nuevo dispositivo IoT.
        """
        #valdiacion de permisos para crear dispositivo
        # if !user.permission == 'create':
        #     raise HTTPException(status_code=403, detail="No tienes permisos para crear un dispositivo")    
        
        try:
            existing = self.db.query(DeviceIOT).filter_by(serial_number=device_data.serial_number).first()
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail="Ya existe un dispositivo con ese número de serie."
                )
            new_device = DeviceIOT(**device_data.dict())
            self.db.add(new_device)
            self.db.commit()
            self.db.refresh(new_device)
            return new_device
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al registrar el dispositivo: {str(e)}")

    def get_device_iot(self, category_name: Optional[str] = None) -> List[dict]:
        """
        Obtener dispositivos IoT registrados, con opción de filtrar por categoría.

        Si no se proporciona `category_name`, se devuelven todos los dispositivos.
        """
        try:
            query = (
                self.db.query(DeviceIOT)
                .join(Device)
                .join(DeviceType)
                .join(DeviceCategory)
                .join(User)
            )

            if category_name:
                query = query.filter(DeviceCategory.name.ilike(category_name))

            devices = query.all()

            result = []
            for d in devices:
                result.append({
                    "id": d.id,
                    "serial_number": d.serial_number,
                    "device_type": d.device_template.device_type.name,
                    "model": d.model,
                    "lot_id": d.lot_id,
                    "user_id": d.user_id,
                    "installation_date": d.installation_date,
                    "maintenance_interval_id": d.maintenance_interval_id,
                    "estimated_maintenance_date": d.estimated_maintenance_date,
                    "status": d.status,
                    "devices_id": d.devices_id,
                    "price_device": d.price_device,
                    "document_number": d.user.document_number if d.user else None
                })

            return result

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al obtener dispositivos: {str(e)}")