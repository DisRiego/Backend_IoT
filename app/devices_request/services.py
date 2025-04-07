from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from app.devices_request.models import Request, TypeOpen

class DeviceRequestService:
    def __init__(self, db: Session):
        self.db = db

    def get_type_open(self):
        try:
            devices = self.db.query(TypeOpen).all()
            if not devices:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "data": {
                            "title": "IOT solicitudes de apertura",
                            "message": "No se encontraron tipos de apertura."
                        }
                    }
                )
            devices_data = jsonable_encoder(devices)
            return JSONResponse(
                status_code=200,
                content={"success": True, "data": devices_data}
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "data": {
                        "title": "Error al obtener tipos de apertura",
                        "message": f"Ocurrió un error al intentar obtener los tipos de apertura: {str(e)}"
                    }
                }
            )

    async def create_request(
        self,
        type_opening_id: int,
        lot_id: int,
        user_id: int,
        device_iot_id: int,
        open_date: datetime,
        close_date: datetime,
        volume_water: Optional[int] = None 
    ):
        try:
            if self.db.query(Request).filter(Request.device_iot_id == device_iot_id, Request.status == 1).first():
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "data": {
                            "title": "Solicitud de apertura ya existe",
                            "message": "Ya existe una solicitud de apertura para este lote"
                        }
                    }
                )
            if type_opening_id == 1 and not volume_water:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "data": {
                            "title": "Solicitud de apertura",
                            "message": "El volumen de agua es obligatorio cuando tipo de apertura es del tipo con limite de agua"
                        }
                    }
                )
            new_request = Request(
                type_opening_id=type_opening_id,
                status=18,  # pendiente
                lot_id=lot_id,
                user_id=user_id,
                device_iot_id=device_iot_id,
                open_date=open_date,
                close_date=close_date,
                volume_water=volume_water,
                request_date=datetime.today().date()
            )
            self.db.add(new_request)
            self.db.commit()
            self.db.refresh(new_request)
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": {
                        "title": "Solicitud de apertura",
                        "message": "Solicitud creada exitosamente"
                    }
                }
            )
        except Exception as e:
            self.db.rollback()
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "data": {
                        "title": "Solicitud de apertura",
                        "message": f"Error al crear la solicitud: {str(e)}"
                    }
                }
            )

    def get_request_by_id(self, request_id):
        try:
            request_data = self.db.query(Request).filter(Request.device_iot_id == request_id).first()
            devices_data = jsonable_encoder(request_data)
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": devices_data
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "data": {
                        "title": "Error al obtener la solicitud",
                        "message": f"Ocurrió un error al intentar obtener el detalle de la solicitud: {str(e)}"
                    }
                }
            )

    async def update_request(
        self,
        request_id: int,
        type_opening_id: int,
        user_id: int,
        open_date: datetime,
        close_date: datetime,
        volume_water: Optional[int] = None
    ):
        try:
            existing_request = self.db.query(Request).filter(Request.id == request_id).first()
            if not existing_request:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "data": {
                            "title": "Solicitud no encontrada",
                            "message": "La solicitud de apertura no existe"
                        }
                    }
                )
            if type_opening_id == 1 and not volume_water:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "data": {
                            "title": "Campo obligatorio",
                            "message": "El volumen de agua es obligatorio cuando el tipo de apertura es 1"
                        }
                    }
                )
            existing_request.type_opening_id = type_opening_id
            existing_request.user_id = user_id
            existing_request.open_date = open_date
            existing_request.close_date = close_date
            existing_request.volume_water = volume_water
            self.db.commit()
            self.db.refresh(existing_request)
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": {
                        "title": "Solicitud de apertura actualizada",
                        "message": "La solicitud ha sido actualizada exitosamente"
                    }
                }
            )
        except Exception as e:
            self.db.rollback()
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "data": {
                        "title": "Error al actualizar la solicitud",
                        "message": f"Error al actualizar la solicitud: {str(e)}"
                    }
                }
            )

    def get_device_detail(self, device_id: int):
        try:
            query = text("""
                SELECT
                    di.id,
                    di.serial_number,
                    di.model,
                    di.lot_id,
                    di.installation_date,
                    di.maintenance_interval_id,
                    di.estimated_maintenance_date,
                    di.status,
                    di.devices_id,
                    di.price_device,
                    d.properties AS device_model,
                    l.name AS lot_name,
                    mi.name AS maintenance_interval,
                    u.name AS user_name
                FROM device_iot di
                LEFT JOIN lot l ON di.lot_id = l.id
                LEFT JOIN maintenance_intervals mi ON di.maintenance_interval_id = mi.id
                LEFT JOIN devices d ON di.devices_id = d.id
                LEFT JOIN request r ON di.id = r.device_iot_id
                LEFT JOIN users u ON r.user_id = u.id
                WHERE di.id = :device_id
            """)
            result = self.db.execute(query, {"device_id": device_id}).fetchone()
            if not result:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "data": {
                            "title": "Dispositivo IoT no encontrado",
                            "message": f"No se encontró el dispositivo IoT con ID {device_id}"
                        }
                    }
                )
            device_data = {
                "id": result.id,
                "serial_number": result.serial_number,
                "model": result.model,
                "lot_id": result.lot_id,
                "installation_date": result.installation_date,
                "maintenance_interval_id": result.maintenance_interval_id,
                "estimated_maintenance_date": result.estimated_maintenance_date,
                "status": result.status,
                "devices_id": result.devices_id,
                "device_data": result.price_device,
                "device_model": result.device_model,
                "lot_name": result.lot_name,
                "maintenance_interval": result.maintenance_interval,
                "user_name": result.user_name
            }
            # Convertir el diccionario a un formato serializable (por ejemplo, formateando datetime)
            device_data_serialized = jsonable_encoder(device_data)
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": device_data_serialized
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "data": {
                        "title": "Error al obtener el dispositivo IoT",
                        "message": f"Error al obtener los detalles del dispositivo IoT: {str(e)}"
                    }
                }
            )

    def get_all_requests(self):
        try:
            requests = self.db.query(Request).all()
            if not requests:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "data": []
                    }
                )
            requests_data = jsonable_encoder(requests)
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": requests_data
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "data": {
                        "title": "Error al obtener solicitudes",
                        "message": f"Ocurrió un error al intentar obtener las solicitudes: {str(e)}"
                    }
                }
            )

    def approve_or_reject_request(self, request_id: int, status: int, justification: Optional[str] = None):
        try:
            request_obj = self.db.query(Request).filter(Request.id == request_id).first()
            if not request_obj:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "data": {
                            "title": "Solicitud no encontrada",
                            "message": "No se encontró la solicitud de apertura"
                        }
                    }
                )
            if status == 19 and not justification:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "data": {
                            "title": "Justificación requerida",
                            "message": "Debe proporcionar una justificación para rechazar la solicitud"
                        }
                    }
                )
            request_obj.status = status
            if status == 19:
                request_obj.justification = justification
            self.db.commit()
            self.db.refresh(request_obj)
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": {
                        "title": "Estado actualizado",
                        "message": "La solicitud ha sido actualizada correctamente"
                    }
                }
            )
        except Exception as e:
            self.db.rollback()
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "data": {
                        "title": "Error al actualizar el estado",
                        "message": f"Error al intentar actualizar la solicitud: {str(e)}"
                    }
                }
            )
