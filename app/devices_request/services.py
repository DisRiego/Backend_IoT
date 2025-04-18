from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from app.devices.models import DeviceIot, Lot, User , Property , PropertyLot , PropertyUser
from app.devices_request.models import Request, TypeOpen , Vars , RequestRejectionReason , RequestRejection
from app.devices.schemas import NotificationCreate

class DeviceRequestService:
    def __init__(self, db: Session):
        self.db = db



    def get_all_requests(self) -> JSONResponse:
        """
        Obtiene todas las solicitudes, incluyendo:
        - document_number del dueño del lote
        - name del estado (Vars.name) de la solicitud
        - type_opening (TypeOpen.type_opening)
        """
        try:
            rows = (
                self.db.query(
                    Request,
                    Vars.name.label("status_name"),
                    User.document_number.label("owner_document"),
                    TypeOpen.type_opening.label("request_type_name")
                )
                .join(Vars, Request.status == Vars.id)
                .join(PropertyLot, Request.lot_id == PropertyLot.lot_id)
                .join(PropertyUser, PropertyLot.property_id == PropertyUser.property_id)
                .join(User, PropertyUser.user_id == User.id)
                .join(TypeOpen, Request.type_opening_id == TypeOpen.id)
                .all()
            )

            if not rows:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "data": []}
                )

            result: List[Dict[str, Any]] = []
            for req, status_name, owner_document, request_type_name in rows:
                base = jsonable_encoder(req)
                base["status_name"] = status_name
                base["owner_document_number"] = owner_document
                base["request_type_name"] = request_type_name
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
        Obtiene todas las solicitudes hechas por un usuario específico,
        incluyendo:
        - document_number del dueño del lote
        - name del estado (Vars.name) de la solicitud
        - type_opening (TypeOpen.type_opening)
        """
        try:
            rows = (
                self.db.query(
                    Request,
                    Vars.name.label("status_name"),
                    User.document_number.label("owner_document"),
                    TypeOpen.type_opening.label("request_type_name")
                )
                .join(Vars, Request.status == Vars.id)
                .join(PropertyLot, Request.lot_id == PropertyLot.lot_id)
                .join(PropertyUser, PropertyLot.property_id == PropertyUser.property_id)
                .join(User, PropertyUser.user_id == User.id)
                .join(TypeOpen, Request.type_opening_id == TypeOpen.id)
                .filter(Request.user_id == user_id)  # <-- filtramos por quien crea la solicitud
                .order_by(Request.request_date.desc())
                .all()
            )

            if not rows:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "data": []}
                )

            result: List[Dict[str, Any]] = []
            for req, status_name, owner_document, request_type_name in rows:
                base = jsonable_encoder(req)
                base["status_name"] = status_name
                base["owner_document_number"] = owner_document
                base["request_type_name"] = request_type_name
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
                        "title": "Error al obtener solicitudes por usuario",
                        "message": f"Ocurrió un error al intentar obtener las solicitudes: {str(e)}"
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
        open_date,   
        close_date,  
        volume_water: Optional[int] = None 
    ) -> JSONResponse:
        try:
            if isinstance(open_date, str):
                open_date = open_date.rstrip("Z")
                open_date = datetime.strptime(open_date, "%Y-%m-%dT%H:%M:%S")
            if isinstance(close_date, str):
                close_date = close_date.rstrip("Z")
                close_date = datetime.strptime(close_date, "%Y-%m-%dT%H:%M:%S")

            
            if open_date.tzinfo is not None:
                open_date = open_date.replace(tzinfo=None)
            if close_date.tzinfo is not None:
                close_date = close_date.replace(tzinfo=None)


            if self.db.query(Request).filter(
                Request.device_iot_id == device_iot_id,
                Request.status == 18  # pendiente
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

            # Volumen obligatorio para tipo 1
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

            # Crear la solicitud
            new_request = Request(
                type_opening_id = type_opening_id,
                status          = 18,  # pendiente
                lot_id          = lot_id,
                user_id         = user_id,
                device_iot_id   = device_iot_id,
                open_date       = open_date,
                close_date      = close_date,
                volume_water    = volume_water,
                request_date    = datetime.now()  # hora local del servidor
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


    def get_request_by_id(self, request_id: int) -> JSONResponse:
        try:
            row = (
                self.db.query(
                    Request,
                    Lot.name.label("lot_name"),
                    Property.name.label("property_name"),
                    User.document_number.label("owner_document_number"),
                    User.name.label("owner_name"),
                    User.first_last_name.label("owner_first_last_name"),
                    User.second_last_name.label("owner_second_last_name"),
                    TypeOpen.type_opening.label("request_type_name"),
                    Vars.name.label("status_name"),
                    RequestRejectionReason.description.label("rejection_reason_name"),
                    RequestRejection.comment.label("rejection_comment")
                )
                .join(DeviceIot, Request.device_iot_id == DeviceIot.id)
                .join(Lot, Request.lot_id == Lot.id)
                .join(PropertyLot, Lot.id == PropertyLot.lot_id)
                .join(Property, PropertyLot.property_id == Property.id)
                .join(PropertyUser, Property.id == PropertyUser.property_id)
                .join(User, PropertyUser.user_id == User.id)
                .join(TypeOpen, Request.type_opening_id == TypeOpen.id)
                .join(Vars, Request.status == Vars.id)
                .outerjoin(RequestRejection, RequestRejection.request_id == Request.id)
                .outerjoin(RequestRejectionReason, RequestRejection.reason_id == RequestRejectionReason.id)
                .filter(Request.id == request_id)
                .first()
            )

            if not row:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "data": {"title": "Solicitud no encontrada"}}
                )

            (
                req,
                lot_name,
                property_name,
                owner_doc,
                owner_name,
                owner_first_last_name,
                owner_second_last_name,
                request_type,
                status_name,
                rejection_reason_name,
                rejection_comment
            ) = row

            data: Dict[str, Any] = jsonable_encoder(req)

            data.update({
                "lot_name": lot_name,
                "property_name": property_name,
                "owner_document_number": owner_doc,
                "owner_name": owner_name,
                "owner_first_last_name": owner_first_last_name,
                "owner_second_last_name": owner_second_last_name,
                "request_type_name": request_type,
                "status_name": status_name,
                "rejection_reason_name": rejection_reason_name,
                "rejection_comment": rejection_comment
            })

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
                ORDER BY r.request_date DESC
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
        req = self.db.query(Request).get(request_id)
        if not req:
            return JSONResponse(status_code=404, content={"success": False, "data": {"title": "Solicitud no encontrada"}})
        device = self.db.query(DeviceIot).get(req.device_iot_id)
        if not device:
            return JSONResponse(status_code=404, content={"success": False, "data": "Dispositivo no encontrado"})
        req.status = 17   # Aprobado
        device.status = 20 # En espera
        self.db.commit()
        return JSONResponse(status_code=200, content={"success": True, "data": {"title": "Solicitud aprobada"}})

    def reject_request(self, request_id: int, reason_id: int, comment: Optional[str] = None) -> JSONResponse:
        req = self.db.query(Request).get(request_id)
        if not req:
            return JSONResponse(status_code=404, content={"success": False, "data": {"title": "Solicitud no encontrada"}})
        device = self.db.query(DeviceIot).get(req.device_iot_id)
        if not device:
            return JSONResponse(status_code=404, content={"success": False, "data": "Dispositivo no encontrado"})
        reason = self.db.query(RequestRejectionReason).get(reason_id)
        if not reason:
            return JSONResponse(status_code=400, content={"success": False, "data": {"title": "Razón de rechazo no válida"}})

        # Crear entrada en tabla intermedia
        rejection = RequestRejection(
            request_id = request_id,
            reason_id  = reason_id,
            comment    = comment
        )
        self.db.add(rejection)

        req.status   = 19   # Rechazado
        device.status= 12   # No operativo

        self.db.commit()
        return JSONResponse(status_code=200, content={"success": True, "data": {"title": "Solicitud rechazada"}})
    

    def get_all_request_rejection_reasons(self) -> JSONResponse:
        """
        Obtiene todas las razones de rechazo.
        """
        try:
            # Consulta para obtener todas las razones de rechazo
            rows = self.db.query(RequestRejectionReason).all()

            if not rows:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "data": {
                            "title": "Razones de rechazo no encontradas",
                            "message": "No se encontraron razones de rechazo disponibles"
                        }
                    }
                )

            # Serializar las razones de rechazo
            rejection_reasons_data = jsonable_encoder(rows)

            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": rejection_reasons_data
                }
            )

        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "data": {
                        "title": "Error al obtener las razones de rechazo",
                        "message": f"Ocurrió un error al intentar obtener las razones de rechazo: {str(e)}"
                    }
                }
            )