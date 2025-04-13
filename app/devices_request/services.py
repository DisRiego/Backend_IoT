from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from app.devices.models import DeviceIot, Lot, User , Property , PropertyLot , PropertyUser
from app.devices_request.models import Request, TypeOpen , Vars
from app.devices.schemas import NotificationCreate

class DeviceRequestService:
    def __init__(self, db: Session):
        self.db = db



    def get_all_requests(self) -> JSONResponse:
        """
        Obtiene todas las solicitudes, incluyendo:
         - document_number del dueño del lote
         - name del estado (Vars.name) de la solicitud
        """
        try:
            # Query con joins
            rows = (
                self.db.query(Request, Vars.name.label("status_name"), User.document_number.label("owner_document"))
                .join(Vars, Request.status == Vars.id)                         # Estado de la solicitud
                .join(PropertyLot, Request.lot_id == PropertyLot.lot_id)      # Relación lote ↔ propiedad
                .join(PropertyUser, PropertyLot.property_id == PropertyUser.property_id)  # Relación propiedad ↔ usuario
                .join(User, PropertyUser.user_id == User.id)                  # Usuario dueño
                .all()
            )

            if not rows:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "data": []}
                )

            # Construir la lista de diccionarios
            result: List[Dict[str, Any]] = []
            for req, status_name, owner_document in rows:
                # Serializar el objeto Request
                base = jsonable_encoder(req)
                # Añadir campos extra
                base["status_name"] = status_name
                base["owner_document_number"] = owner_document
                result.append(base)

            return JSONResponse(
                status_code=200,
                content={"success": True, "data": result}
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

    def get_requests_by_user(self, user_id: int) -> JSONResponse:
        """
        Obtiene todas las solicitudes hechas por un usuario específico.
        """
        try:
            rows: List[Request] = (
                self.db
                .query(Request)
                .filter(Request.user_id == user_id)
                .order_by(Request.request_date.desc())
                .all()
            )
            data = jsonable_encoder(rows)
            return JSONResponse(
                status_code=200,
                content={"success": True, "data": data}
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "data": {
                        "title": "Error al obtener solicitudes por usuario",
                        "message": str(e)
                    }
                }
            )
    # Método auxiliar para crear notificaciones
    def create_notification(self, user_id: int, title: str, message: str, notification_type: str):
        """
        Crea una notificación para un usuario específico.
        
        Args:
            user_id: ID del usuario
            title: Título de la notificación
            message: Mensaje detallado de la notificación
            notification_type: Tipo de notificación (iot_request, iot_approval, etc.)
            
        Returns:
            Resultado de la creación de la notificación
        """
        try:
            notification_data = NotificationCreate(
                user_id=user_id,
                title=title,
                message=message,
                type=notification_type
            )
            return self.user_service.create_notification(notification_data)
        except Exception as e:
            print(f"[ERROR] No se pudo crear la notificación: {str(e)}")
            return {"success": False, "data": None, "message": f"Error al crear notificación: {str(e)}"}


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
            # 🧽 Limpiar fechas: quitar la 'Z' si vienen como string
            if isinstance(open_date, str):
                open_date = open_date.rstrip("Z")
                open_date = datetime.strptime(open_date, "%Y-%m-%dT%H:%M:%S")
            if isinstance(close_date, str):
                close_date = close_date.rstrip("Z")
                close_date = datetime.strptime(close_date, "%Y-%m-%dT%H:%M:%S")

            # Validar duplicados en estado pendiente
            if self.db.query(Request).filter(
                Request.device_iot_id == device_iot_id,
                Request.status == 18
            ).first():
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "data": {
                            "title": "Solicitud pendiente existente",
                            "message": "Ya existe una solicitud pendiente para este dispositivo"
                        }
                    }
                )

            if type_opening_id == 1 and not volume_water:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "data": {
                            "title": "Volumen obligatorio",
                            "message": "El volumen de agua es obligatorio para este tipo de apertura"
                        }
                    }
                )

            new_request = Request(
                type_opening_id=type_opening_id,
                status=18,
                lot_id=lot_id,
                user_id=user_id,
                device_iot_id=device_iot_id,
                open_date=open_date,
                close_date=close_date,
                volume_water=volume_water,
                request_date=datetime.now()
            )
            self.db.add(new_request)
            self.db.commit()
            self.db.refresh(new_request)

            type_opening = self.db.query(TypeOpen).filter(TypeOpen.id == type_opening_id).first()
            type_opening_name = type_opening.type_opening if type_opening else "Desconocido"

            lot = self.db.query(Lot).filter(Lot.id == lot_id).first()
            lot_name = lot.name if lot else f"Lote {lot_id}"

            try:
                self.create_notification(
                    user_id=user_id,
                    title="Solicitud de apertura creada",
                    message=f"Su solicitud de apertura para el lote {lot_name} ha sido registrada. Tipo: {type_opening_name}, fecha de apertura: {open_date.strftime('%d/%m/%Y %H:%M')}",
                    notification_type="iot_request_created"
                )

                admins = self.db.execute(text("""
                    SELECT u.id FROM users u
                    JOIN user_role ur ON u.id = ur.user_id
                    WHERE ur.role_id = 2
                """)).fetchall()

                for admin in admins:
                    self.create_notification(
                        user_id=admin.id,
                        title="Nueva solicitud de apertura",
                        message=f"Se ha recibido una nueva solicitud de apertura para el lote {lot_name}. Tipo: {type_opening_name}.",
                        notification_type="iot_request_admin"
                    )
            except Exception as notif_error:
                print(f"[ERROR] Error al enviar notificaciones: {notif_error}")

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
                        "title": "Error en creación",
                        "message": f"Ocurrió un error al crear la solicitud: {str(e)}"
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
            # Consulta del dispositivo con el nombre del estado
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
                    ds.name AS status_name,
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
                LEFT JOIN vars ds ON ds.id = di.status AND ds.type = 'device_status'
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

            # Última solicitud asociada al dispositivo
            latest_request = self.db.execute(text("""
                SELECT
                    r.id,
                    r.status,
                    v.name AS status_name,
                    r.open_date,
                    r.close_date,
                    r.volume_water,
                    r.request_date,
                    r.user_id,
                    r.lot_id,
                    r.type_opening_id
                FROM request r
                LEFT JOIN vars v ON v.id = r.status AND v.type = 'request_status'
                WHERE r.device_iot_id = :device_id
                ORDER BY r.open_date DESC
                LIMIT 1
            """), {"device_id": device_id}).fetchone()

            device_data = {
                "id": result.id,
                "serial_number": result.serial_number,
                "model": result.model,
                "lot_id": result.lot_id,
                "installation_date": result.installation_date,
                "maintenance_interval_id": result.maintenance_interval_id,
                "estimated_maintenance_date": result.estimated_maintenance_date,
                "status": {
                    "id": result.status,
                    "name": result.status_name
                },
                "devices_id": result.devices_id,
                "device_data": result.price_device,
                "device_model": result.device_model,
                "lot_name": result.lot_name,
                "maintenance_interval": result.maintenance_interval,
                "user_name": result.user_name,
                "latest_request": {
                    "id": latest_request.id,
                    "status": {
                        "id": latest_request.status,
                        "name": latest_request.status_name
                    },
                    "open_date": latest_request.open_date,
                    "close_date": latest_request.close_date,
                    "volume_water": latest_request.volume_water,
                    "request_date": latest_request.request_date,
                    "user_id": latest_request.user_id,
                    "lot_id": latest_request.lot_id,
                    "type_opening_id": latest_request.type_opening_id
                } if latest_request else None
            }

            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": jsonable_encoder(device_data)
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


    def approve_request(self, request_id: int) -> JSONResponse:
        try:
            request_obj = self.db.query(Request).filter(Request.id == request_id).first()
            if not request_obj:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "data": {"title": "Solicitud no encontrada"}}
                )

            device = self.db.query(DeviceIot).filter(DeviceIot.id == request_obj.device_iot_id).first()
            if not device:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "data": "Dispositivo no encontrado"}
                )

            request_obj.status = 17  # Aprobado

            if request_obj.open_date and request_obj.close_date:
                device.status = 20  # En espera
            else:
                device.status = 20

            self.db.commit()
            self.db.refresh(request_obj)

            return JSONResponse(
                status_code=200,
                content={"success": True, "data": {"title": "Solicitud aprobada"}}
            )
        except Exception as e:
            self.db.rollback()
            return JSONResponse(
                status_code=500,
                content={"success": False, "data": {"title": "Error al aprobar", "message": str(e)}}
            )

    def reject_request(self, request_id: int, justification: Optional[str] = None) -> JSONResponse:
        try:
            request_obj = self.db.query(Request).filter(Request.id == request_id).first()
            if not request_obj:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "data": {"title": "Solicitud no encontrada"}}
                )

            device = self.db.query(DeviceIot).filter(DeviceIot.id == request_obj.device_iot_id).first()
            if not device:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "data": "Dispositivo no encontrado"}
                )

            request_obj.status = 19  # Rechazado
            device.status = 12       # No operativo
            if justification:
                request_obj.justification = justification

            self.db.commit()
            self.db.refresh(request_obj)

            return JSONResponse(
                status_code=200,
                content={"success": True, "data": {"title": "Solicitud rechazada"}}
            )
        except Exception as e:
            self.db.rollback()
            return JSONResponse(
                status_code=500,
                content={"success": False, "data": {"title": "Error al rechazar", "message": str(e)}}
            )