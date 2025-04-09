from datetime import timedelta, datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

# Importaciones desde app.devices.models (ajusta si es necesario)
from app.devices.models import (
    DeviceIot,
    Device,
    Notification,
    Vars,
    Lot,
    MaintenanceInterval,
    PropertyLot,
    DeviceType,
    Property,
    PropertyUser,
    User,
    DeviceCategories
)

from app.devices.schemas import (
    DeviceCreate,
    DeviceUpdate,
    DeviceAssignRequest,
    DeviceReassignRequest,
    DeviceIotReadingUpdateByLot,
    NotificationCreate
)




class DeviceService:
    def __init__(self, db: Session):
        self.db = db

    # Método auxiliar para crear notificaciones
    def create_notification(self, user_id: int, title: str, message: str, notification_type: str):
        """
        Crea una notificación para un usuario específico directamente en la base de datos.

        Args:
            user_id: ID del usuario
            title: Título de la notificación
            message: Mensaje detallado de la notificación
            notification_type: Tipo de notificación (iot_assignment, iot_status, etc.)

        Returns:
            Diccionario con el resultado de la operación.
        """
        try:
            new_notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                type=notification_type,
                created_at=datetime.utcnow()  # Fecha de creación
            )
            self.db.add(new_notification)
            self.db.commit()
            self.db.refresh(new_notification)
            return {"success": True, "data": new_notification.id, "message": "Notificación creada exitosamente"}
        except Exception as e:
            self.db.rollback()
            print(f"[ERROR] No se pudo crear la notificación: {str(e)}")
            return {"success": False, "data": None, "message": f"Error al crear notificación: {str(e)}"}
        
    def get_all_devices(self) -> Dict[str, Any]:
        """Obtener todos los dispositivos con información operativa (estado, lote, propiedad y categoría)"""
        try:
            from sqlalchemy.orm import aliased
            # Crear alias para la tabla Vars
            device_status_alias = aliased(Vars)
            property_status_alias = aliased(Vars)
            
            devices = (
                self.db.query(
                    DeviceIot,
                    DeviceType,
                    Device,
                    Lot,
                    Property,
                    PropertyUser,
                    User,
                    device_status_alias,    # Estado del dispositivo
                    property_status_alias,  # Estado del predio
                    DeviceCategories        # Categoría del dispositivo
                )
                .join(DeviceType, DeviceIot.devices_id == DeviceType.id)
                .join(Device, DeviceIot.devices_id == Device.id)  # Relación con Device
                .outerjoin(Lot, DeviceIot.lot_id == Lot.id)  # Outer join para dispositivos sin lote
                .outerjoin(PropertyLot, Lot.id == PropertyLot.lot_id)  # Outer join para propiedad
                .outerjoin(Property, PropertyLot.property_id == Property.id)  # Outer join para propiedad
                .outerjoin(PropertyUser, Property.id == PropertyUser.property_id)  # Outer join para propiedad usuario
                .outerjoin(User, PropertyUser.user_id == User.id)  # Outer join para usuario
                .outerjoin(device_status_alias, DeviceIot.status == device_status_alias.id)  # Estado del dispositivo
                .outerjoin(property_status_alias, Property.state == property_status_alias.id)  # Estado del predio
                .outerjoin(DeviceCategories, DeviceType.device_category_id == DeviceCategories.id)  # Categoría
                .all()
            )

            devices_list = []
            for device, device_type, device_details, lot, property_data, property_user, user, device_status, property_status, category in devices:
                device_data = jsonable_encoder(device)

                # Asignamos los valores a la respuesta
                device_data["device_type_name"] = device_type.name  # Nombre del tipo de dispositivo
                device_data["device_category_name"] = category.name if category else "No asignada"  # Categoría del dispositivo
                device_data["owner_document_number"] = user.document_number if user else "No asignado"  # Documento del propietario
                device_data["lot_id"] = lot.id if lot else None  # ID del lote
                device_data["lot_name"] = lot.name if lot else "No asignado"  # Nombre del lote
                device_data["property_id"] = property_data.id if property_data else None  # ID del predio
                device_data["real_estate_registration_number"] = property_data.real_estate_registration_number if property_data else "No disponible"
                device_data["property_state"] = property_status.name if property_status else "No asignado"  # Estado del predio
                device_data["device_status_name"] = device_status.name if device_status else "No asignado"  # Estado del dispositivo

                devices_list.append(device_data)

            return JSONResponse(
                status_code=200,
                content={"success": True, "data": devices_list}
            )

        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "data": {
                        "title": "Error al obtener los dispositivos",
                        "message": f"Error: {str(e)}"
                    }
                }
            )




    def get_device_by_id(self, device_id: int) -> Dict[str, Any]:
        """Obtener detalles de un dispositivo específico con el ID del predio al que pertenece"""
        try:
            from sqlalchemy.orm import aliased
            # Creamos alias para la tabla Vars
            device_status_alias = aliased(Vars)
            property_status_alias = aliased(Vars)
            
            result = (
                self.db.query(
                    DeviceIot,
                    DeviceType,
                    Lot,
                    Property,
                    PropertyUser,
                    User,
                    device_status_alias,    # Estado del dispositivo
                    property_status_alias   # Estado del predio
                )
                .join(DeviceType, DeviceIot.devices_id == DeviceType.id)
                .outerjoin(Lot, DeviceIot.lot_id == Lot.id)  # Outer join para dispositivos sin lote
                .outerjoin(PropertyLot, Lot.id == PropertyLot.lot_id)  # Outer join para la relación con propiedad
                .outerjoin(Property, PropertyLot.property_id == Property.id)  # Outer join para propiedad
                .outerjoin(PropertyUser, Property.id == PropertyUser.property_id)  # Outer join para usuario de la propiedad
                .outerjoin(User, PropertyUser.user_id == User.id)  # Outer join para usuario
                .outerjoin(device_status_alias, DeviceIot.status == device_status_alias.id)  # Estado del dispositivo
                .outerjoin(property_status_alias, Property.state == property_status_alias.id)  # Estado del predio
                .filter(DeviceIot.id == device_id)
                .first()
            )

            if not result:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "data": "Dispositivo no encontrado"}
                )

            device, device_type, lot, property_data, property_user, user, device_status, property_status = result
            device_data = jsonable_encoder(device)

            # Asignamos los valores a la respuesta, diferenciando los estados
            device_data["device_type_name"] = device_type.name if device_type else "No asignado"
            device_data["owner_document_number"] = user.document_number if user else "No asignado"
            device_data["lot_id"] = lot.id if lot else None
            device_data["lot_name"] = lot.name if lot else "No asignado"
            device_data["property_id"] = property_data.id if property_data else None
            device_data["real_estate_registration_number"] = property_data.real_estate_registration_number if property_data else "No disponible"
            device_data["property_state"] = property_status.name if property_status else "No asignado"
            device_data["device_status_name"] = device_status.name if device_status else "No asignado"
            device_data["property_name"] = property_data.name if property_data else "No asignado"

            return JSONResponse(
                status_code=200,
                content={"success": True, "data": device_data}
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "data": {
                        "title": "Error al obtener el dispositivo",
                        "message": f"Error: {str(e)}"
                    }
                }
            )




    def create_device(self, device_data: DeviceCreate) -> Dict[str, Any]:
        """Crear un nuevo dispositivo operativo (en device_iot)"""
        try:
            # Convertir los datos del dispositivo en un diccionario
            data = device_data.dict()

            # Validación: Verificar que no exista ya un dispositivo con el mismo serial_number y devices_id (tipo de dispositivo)
            serial_number = data.get("serial_number")
            devices_id = data.get("devices_id")
            duplicate = self.db.query(DeviceIot).filter(
                DeviceIot.serial_number == serial_number,
                DeviceIot.devices_id == devices_id
            ).first()
            if duplicate:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "data": {
                            "title": "Error de validación",
                            "message": "Ya existe un dispositivo con el mismo número de serie para este tipo de dispositivo"
                        }
                    }
                )

            # Crear el nuevo dispositivo en DeviceIot, utilizando el JSON enviado en 'price_device'
            new_device = DeviceIot(
                serial_number = serial_number,
                model = data.get("model"),
                devices_id = devices_id,
                price_device = data.get("price_device"),  # Aquí almacenamos el JSON que llega desde el frontend
                lot_id = data.get("lot_id"),
                installation_date = data.get("installation_date"),
                maintenance_interval_id = data.get("maintenance_interval_id"),
                estimated_maintenance_date = data.get("estimated_maintenance_date"),
                status = data.get("status")
            )

            # Guardar el nuevo dispositivo en la base de datos
            self.db.add(new_device)
            self.db.commit()
            self.db.refresh(new_device)

            return JSONResponse(
                status_code=201,
                content={
                    "success": True,
                    "data": {
                        "title": "Dispositivo creado",
                        "message": "El dispositivo ha sido creado correctamente",
                        "device": jsonable_encoder(new_device)
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
                        "title": "Error al crear el dispositivo",
                        "message": f"Error: {str(e)}"
                    }
                }
            )


    def update_device(self, device_id: int, device_data: DeviceUpdate) -> Dict[str, Any]:
        """Actualizar información del dispositivo operativo"""
        try:
            device = self.db.query(DeviceIot).filter(DeviceIot.id == device_id).first()
            if not device:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "data": "Dispositivo no encontrado"}
                )
            update_data = device_data.dict(exclude_unset=True)
            for key, value in update_data.items():
                if hasattr(device, key) and value is not None:
                    setattr(device, key, value)
            self.db.commit()
            self.db.refresh(device)
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": {
                        "title": "Actualización exitosa",
                        "message": "La información del dispositivo ha sido actualizada correctamente",
                        "device": jsonable_encoder(device)
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
                        "title": "Error al actualizar dispositivo",
                        "message": f"Error: {str(e)}"
                    }
                }
            )

    def update_device_status(self, device_id: int, new_status: int) -> Dict[str, Any]:
        """Actualizar el estado del dispositivo (habilitar/inhabilitar) y notificar al propietario"""
        try:
            device = self.db.query(DeviceIot).filter(DeviceIot.id == device_id).first()
            if not device:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "data": "Dispositivo no encontrado"}
                )
            
            status_obj = self.db.query(Vars).filter(Vars.id == new_status).first()
            if not status_obj:
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "data": "Estado no válido"}
                )
                
            if device.status == new_status:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "data": {
                            "title": "Operación no válida",
                            "message": f"El dispositivo ya se encuentra en el estado '{status_obj.name}'"
                        }
                    }
                )
                
            old_status = device.status
            device.status = new_status
            self.db.commit()
            self.db.refresh(device)
            
            # Si hay un lote asignado, notificamos al propietario del cambio de estado
            if device.lot_id:
                # Obtenemos el lote
                lot = self.db.query(Lot).filter(Lot.id == device.lot_id).first()
                if lot:
                    # Obtenemos la relación PropertyLot para encontrar la propiedad
                    property_lot = self.db.query(PropertyLot).filter(PropertyLot.lot_id == lot.id).first()
                    if property_lot:
                        # Obtenemos la relación PropertyUser para encontrar al propietario
                        property_user = self.db.query(PropertyUser).filter(
                            PropertyUser.property_id == property_lot.property_id
                        ).first()
                        
                        if property_user:
                            # Creamos la notificación para el propietario
                            self.create_notification(
                                user_id=property_user.user_id,
                                title="Cambio de estado en dispositivo IoT",
                                message=f"El dispositivo con número de serie {device.serial_number} ha cambiado su estado a '{status_obj.name}'.",
                                notification_type="iot_status_change"
                            )
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": {
                        "title": "Estado actualizado",
                        "message": f"El estado del dispositivo ha sido actualizado a '{status_obj.name}' correctamente",
                        "device_id": device.id,
                        "new_status": new_status,
                        "status_name": status_obj.name
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
                        "title": "Error al actualizar estado",
                        "message": f"Error: {str(e)}"
                    }
                }
            )
    def assign_to_lot(self, assignment_data: DeviceAssignRequest, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Asignar un dispositivo a un lote y establecer su estado en 'No Operativo' (ID 12)"""
        try:
            device = self.db.query(DeviceIot).get(assignment_data.device_id)
            if not device:
                return JSONResponse(status_code=404, content={"success": False, "data": "Dispositivo no encontrado"})
            if device.status == 25:
                return JSONResponse(status_code=400, content={"success": False, "data": {"title": "Operación no válida", "message": "No se puede asignar un dispositivo inhabilitado"}})
            if device.lot_id:
                return JSONResponse(status_code=400, content={"success": False, "data": {"title": "Operación no válida", "message": "El dispositivo ya está asignado a un lote. Use reasignar en su lugar."}})

            # Validación de un solo tipo por lote (salvo breaker, fusible, portafusible, dps)
            tipo_obj = self.db.query(DeviceType).get(device.devices_id)
            tipo_nombre = tipo_obj.name.lower() if tipo_obj else ""
            excepciones = {"breaker", "fusible", "portafusible", "dps"}
            existing = (
                self.db.query(DeviceIot)
                  .filter(DeviceIot.lot_id == assignment_data.lot_id)
                  .filter(DeviceIot.devices_id == device.devices_id)
                  .count()
            )
            if tipo_nombre not in excepciones and existing >= 1:
                return JSONResponse(status_code=400, content={"success": False, "data": {"title": "Duplicado", "message": f"Ya existe un dispositivo de tipo '{tipo_obj.name}' asignado al lote {assignment_data.lot_id}"}})
            if tipo_nombre in excepciones and existing >= 2:
                return JSONResponse(status_code=400, content={"success": False, "data": {"title": "Límite alcanzado", "message": f"No puedes asignar más de dos dispositivos de tipo '{tipo_obj.name}' al lote {assignment_data.lot_id}"}})

            # Verificar lote y predio...
            lot = self.db.query(Lot).get(assignment_data.lot_id)
            if not lot:
                return JSONResponse(status_code=404, content={"success": False, "data": "Lote no encontrado"})
            property_lot = self.db.query(PropertyLot).filter_by(
                lot_id=assignment_data.lot_id,
                property_id=assignment_data.property_id
            ).first()
            if not property_lot:
                return JSONResponse(status_code=400, content={"success": False, "data": {"title": "Operación no válida", "message": "El lote no pertenece al predio especificado"}})
            maintenance_interval = self.db.query(MaintenanceInterval).get(assignment_data.maintenance_interval_id)
            if not maintenance_interval:
                return JSONResponse(status_code=404, content={"success": False, "data": "Intervalo de mantenimiento no encontrado"})

            # Asignar valores
            device.lot_id = assignment_data.lot_id
            device.installation_date = assignment_data.installation_date
            device.maintenance_interval_id = assignment_data.maintenance_interval_id
            device.estimated_maintenance_date = assignment_data.estimated_maintenance_date
            device.status = 12  # No Operativo

            self.db.commit()
            self.db.refresh(device)

           
            owner = (
                self.db.query(PropertyUser)
                .filter(PropertyUser.property_id == assignment_data.property_id)
                .first()
            )

            
            if owner:
                self.create_notification(
                    user_id=owner.user_id,
                    title="Dispositivo asignado",
                    message=f"Se ha asignado un nuevo dispositivo al lote '{lot.name}'.",
                    notification_type="device_assigned"
                )

            return JSONResponse(status_code=200, content={
                "success": True,
                "data": {
                    "title": "Asignación exitosa",
                    "message": "El dispositivo ha sido asignado al lote correctamente y se ha establecido en 'No Operativo'",
                    "device_id": device.id,
                    "lot_id": lot.id,
                    "lot_name": lot.name,
                    "installation_date": device.installation_date.isoformat() if device.installation_date else None,
                    "maintenance_interval": maintenance_interval.name,
                    "estimated_maintenance_date": device.estimated_maintenance_date.isoformat() if device.estimated_maintenance_date else None,
                    "status": device.status
                }
            })
        except Exception as e:
            self.db.rollback()
            return JSONResponse(status_code=500, content={"success": False, "data": {"title": "Error al asignar lote", "message": str(e)}})

    def reassign_to_lot(self, reassignment_data: DeviceReassignRequest, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Reasignar un dispositivo a otro lote"""
        try:
            device = self.db.query(DeviceIot).get(reassignment_data.device_id)
            if not device:
                return JSONResponse(status_code=404, content={"success": False, "data": "Dispositivo no encontrado"})
            if device.status == 25:
                return JSONResponse(status_code=400, content={"success": False, "data": {"title": "Operación no válida", "message": "No se puede reasignar un dispositivo inhabilitado"}})
            if not device.lot_id:
                return JSONResponse(status_code=400, content={"success": False, "data": {"title": "Operación no válida", "message": "El dispositivo no está asignado a ningún lote. Use asignar en su lugar."}})

            previous_lot_id = device.lot_id

            # Validación de un solo tipo por lote (salvo breaker, fusible, portafusible, dps)
            tipo_obj = self.db.query(DeviceType).get(device.devices_id)
            tipo_nombre = tipo_obj.name.lower() if tipo_obj else ""
            excepciones = {"breaker", "fusible", "portafusible", "dps"}
            existing = (
                self.db.query(DeviceIot)
                  .filter(DeviceIot.lot_id == reassignment_data.lot_id)
                  .filter(DeviceIot.devices_id == device.devices_id)
                  .count()
            )
            if tipo_nombre not in excepciones and existing >= 1:
                return JSONResponse(status_code=400, content={"success": False, "data": {"title": "Duplicado", "message": f"Ya existe un dispositivo de tipo '{tipo_obj.name}' asignado al lote {reassignment_data.lot_id}"}})
            if tipo_nombre in excepciones and existing >= 2:
                return JSONResponse(status_code=400, content={"success": False, "data": {"title": "Límite alcanzado", "message": f"No puedes asignar más de dos dispositivos de tipo '{tipo_obj.name}' al lote {reassignment_data.lot_id}"}})

            lot = self.db.query(Lot).get(reassignment_data.lot_id)
            if not lot:
                return JSONResponse(status_code=404, content={"success": False, "data": "Lote no encontrado"})
            property_lot = self.db.query(PropertyLot).filter_by(
                lot_id=reassignment_data.lot_id,
                property_id=reassignment_data.property_id
            ).first()
            if not property_lot:
                return JSONResponse(status_code=400, content={"success": False, "data": {"title": "Operación no válida", "message": "El lote no pertenece al predio especificado"}})
            maintenance_interval = self.db.query(MaintenanceInterval).get(reassignment_data.maintenance_interval_id)
            if not maintenance_interval:
                return JSONResponse(status_code=404, content={"success": False, "data": "Intervalo de mantenimiento no encontrado"})

            # Asignar valores
            device.lot_id = reassignment_data.lot_id
            device.installation_date = reassignment_data.installation_date
            device.maintenance_interval_id = reassignment_data.maintenance_interval_id
            device.estimated_maintenance_date = reassignment_data.estimated_maintenance_date

            self.db.commit()
            self.db.refresh(device)

           
            owner = (
                self.db.query(PropertyUser)
                .filter(PropertyUser.property_id == reassignment_data.property_id)
                .first()
            )

            
            if owner:
                self.create_notification(
                    user_id=owner.user_id,
                    title="Dispositivo reasignado",
                    message=f"Se ha reasignado un dispositivo al lote '{lot.name}'.",
                    notification_type="device_reassigned"
                )

            return JSONResponse(status_code=200, content={"success": True, "data": {
                "title": "Reasignación exitosa",
                "message": "El dispositivo ha sido reasignado al lote correctamente",
                "device_id": device.id,
                "previous_lot_id": previous_lot_id,
                "new_lot_id": lot.id,
                "lot_name": lot.name,
                "installation_date": device.installation_date.isoformat() if device.installation_date else None,
                "maintenance_interval": maintenance_interval.name,
                "estimated_maintenance_date": device.estimated_maintenance_date.isoformat() if device.estimated_maintenance_date else None
            }})
        except Exception as e:
            self.db.rollback()
            return JSONResponse(status_code=500, content={"success": False, "data": {"title": "Error al reasignar lote", "message": str(e)}})


    def delete_device(self, device_id: int) -> Dict[str, Any]:
        """Eliminar un dispositivo (borrado lógico mediante cambio de estado)"""
        try:
            device = self.db.query(DeviceIot).filter(DeviceIot.id == device_id).first()
            if not device:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "data": "Dispositivo no encontrado"}
                )
            deleted_status_id = 25  # Ajusta este valor según tu esquema de estados
            device.status = deleted_status_id
            self.db.commit()
            return JSONResponse(
                status_code=200,
                content={"success": True, "data": {"title": "Dispositivo eliminado", "message": "El dispositivo ha sido eliminado correctamente"}}
            )
        except Exception as e:
            self.db.rollback()
            return JSONResponse(
                status_code=500,
                content={"success": False, "data": {"title": "Error al eliminar dispositivo", "message": str(e)}}
            )

    def get_devices_by_lot(self, lot_id: int) -> Dict[str, Any]:
        """Obtener todos los dispositivos asignados a un lote específico"""
        try:
            lot = self.db.query(Lot).filter(Lot.id == lot_id).first()
            if not lot:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "data": "Lote no encontrado"}
                )

            # Traer todos los campos de DeviceIot + nombre de tipo (si existe) + nombre de estado (si existe)
            rows = (    
                self.db.query(
                    DeviceIot,
                    DeviceType.name.label("device_type"),
                    Vars.name.label("status_name")
                )
                .outerjoin(DeviceType, DeviceIot.devices_id == DeviceType.id)
                .outerjoin(Vars, DeviceIot.status == Vars.id)
                .filter(DeviceIot.lot_id == lot_id)
                .all()
            )

            devices_list = []
            for device, device_type, status_name in rows:
                d = jsonable_encoder(device)
                d["device_type"] = device_type or "No asignado"
                d["status_name"] = status_name or "No asignado"
                devices_list.append(d)

            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": {
                        "lot_id": lot.id,
                        "lot_name": lot.name,
                        "devices": devices_list
                    }
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "data": {"title": "Error al obtener dispositivos", "message": str(e)}
                }
            )

    def filter_devices(self, 
                       serial_number: Optional[int] = None,
                       model: Optional[str] = None,
                       lot_id: Optional[int] = None,
                       status: Optional[int] = None,
                       device_type_id: Optional[int] = None,
                       page: int = 1,
                       page_size: int = 10) -> Dict[str, Any]:
        """Filtrar dispositivos según diversos criterios con paginación"""
        try:
            query = self.db.query(
                DeviceIot,
                Vars.name.label("status_name"),
                Lot.name.label("lot_name")
            ).outerjoin(Vars, DeviceIot.status == Vars.id) \
             .outerjoin(Lot, DeviceIot.lot_id == Lot.id)
            if serial_number is not None:
                query = query.filter(DeviceIot.serial_number == serial_number)
            if model is not None:
                query = query.filter(DeviceIot.model.ilike(f"%{model}%"))
            if lot_id is not None:
                query = query.filter(DeviceIot.lot_id == lot_id)
            if status is not None:
                query = query.filter(DeviceIot.status == status)
            if device_type_id is not None:
                query = query.filter(DeviceIot.devices_id == device_type_id)
            total = query.count()
            query = query.offset((page - 1) * page_size).limit(page_size)
            results = query.all()
            devices_list = []
            for device, status_name, lot_name in results:
                device_dict = jsonable_encoder(device)
                device_dict["status_name"] = status_name
                device_dict["lot_name"] = lot_name
                devices_list.append(device_dict)
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": {
                        "total": total,
                        "page": page,
                        "page_size": page_size,
                        "total_pages": (total + page_size - 1) // page_size,
                        "devices": devices_list
                    }
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "data": {"title": "Error al filtrar dispositivos", "message": str(e)}
                }
            )
    
    def create_device_data(self, device_data: DeviceCreate):
        """
        Inserta un nuevo registro en la tabla device_iot usando el valor sensor_value
        dentro de price_device. Se consulta la tabla DeviceType para obtener el id del
        tipo "IoT". Si no se encuentra, se asigna un valor por defecto.
        """
        try:
            device_type = self.db.query(DeviceType).filter(DeviceType.name == "IoT").first()
            if not device_type:
                device_type_id = 1
            else:
                device_type_id = device_type.id
            new_device = DeviceIot(
                devices_id = device_type_id,
                properties = {"sensor_value": device_data.sensor_value}
            )
            self.db.add(new_device)
            self.db.commit()
            self.db.refresh(new_device)
            return new_device
        except Exception as e:
            raise Exception(f"Error al insertar datos: {str(e)}")
        

    def update_device_reading_by_lot(self, reading: DeviceIotReadingUpdateByLot) -> Dict[str, Any]:
        """
        Actualiza la lectura en la tabla device_iot para el dispositivo cuyo id se envíe,
        validando que pertenece al lote indicado.
        Se guarda en el campo data_device solo la información de la lectura,
        excluyendo 'device_id', 'lot_id' y 'device_type_id'.
        """
        try:
            data = reading.dict()
            device_id = data.get("device_id")
            lot_id = data.get("lot_id")
            if device_id is None or lot_id is None:
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "data": "Faltan device_id o lot_id"}
                )
            device = self.db.query(DeviceIot).filter(DeviceIot.id == device_id).first()
            if not device:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "data": "Dispositivo no encontrado"}
                )
            # Validar que el dispositivo pertenezca al lote indicado
            if device.lot_id != lot_id:
                device.lot_id = lot_id

            # Eliminar las claves que no queremos almacenar en data_device
            for key in ["device_id", "lot_id", "device_type_id"]:
                data.pop(key, None)
                
            # Ahora 'data' contiene solo la información de la lectura
            device.data_device = data  # Guardamos las lecturas del Arduino en data_device
            self.db.commit()
            self.db.refresh(device)
            return JSONResponse(
                status_code=200,
                content={"success": True, "data": jsonable_encoder(device)}
            )
        except Exception as e:
            self.db.rollback()
            return JSONResponse(
                status_code=500,
                content={"success": False, "data": {"title": "Error al actualizar lectura", "message": str(e)}}
            )


    def get_devices_by_category(self, category_id: int) -> Dict[str, Any]:
        """Obtener dispositivos por categoría con información del lote, predio, propietario, estado del dispositivo y categoría"""
        try:
            # Consulta para obtener los dispositivos de la categoría con sus relaciones
            devices = (
                self.db.query(DeviceIot, DeviceType, Device, Lot, Property, PropertyUser, User, Vars, DeviceCategories)
                .join(DeviceType, DeviceIot.devices_id == DeviceType.id)
                .join(Device, DeviceIot.devices_id == Device.id)  # Relación con Device para acceder a properties
                .outerjoin(Lot, DeviceIot.lot_id == Lot.id)  # Outer join para incluir dispositivos sin lote asignado
                .outerjoin(PropertyLot, Lot.id == PropertyLot.lot_id)  # Outer join para propiedad
                .outerjoin(Property, PropertyLot.property_id == Property.id)  # Outer join para propiedad
                .outerjoin(PropertyUser, Property.id == PropertyUser.property_id)  # Outer join para propiedad usuario
                .outerjoin(User, PropertyUser.user_id == User.id)  # Outer join para usuario
                .outerjoin(Vars, DeviceIot.status == Vars.id)  # Outer join para estado del dispositivo
                .outerjoin(DeviceCategories, DeviceType.device_category_id == DeviceCategories.id)  # Outer join para categoría
                .filter(DeviceType.device_category_id == category_id)
                .all()
            )

            devices_list = []
            for device, device_type, device_details, lot, property_data, property_user, user, state, category in devices:
                device_data = jsonable_encoder(device)

                # Asignar información a la respuesta
                device_data["device_type_name"] = device_type.name if device_type else "No asignado"  # Nombre del tipo de dispositivo
                device_data["category_name"] = category.name if category else "No asignada"  # Nombre de la categoría
                device_data["device_status_name"] = state.name if state else "No asignado"  # Nombre del estado del dispositivo
                device_data["lot_id"] = lot.id if lot else None  # ID del lote, si no hay lote, lo asignamos como None
                device_data["lot_name"] = lot.name if lot else "No asignado"  # Nombre del lote, si no hay lote, asignamos "No asignado"
                device_data["property_id"] = property_data.id if property_data else None  # ID del predio
                device_data["real_estate_registration_number"] = property_data.real_estate_registration_number if property_data else "No disponible"
                device_data["owner_document_number"] = user.document_number if user else "No asignado"  # Número de documento del propietario
                device_data["property_state"] = state.name if state else "No asignado"  # Nombre del estado del predio

                devices_list.append(device_data)

            return JSONResponse(
                status_code=200,
                content={"success": True, "data": devices_list}
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "data": {
                        "title": "Error al obtener dispositivos por categoría",
                        "message": f"Error: {str(e)}"
                    }
                }
            )

    def get_all_maintenance_intervals(self) -> Dict[str, Any]:
            """Obtener todos los intervalos de mantenimiento"""
            try:
                intervals = self.db.query(MaintenanceInterval).all()
                # Convertir la lista de intervalos a un formato JSON serializable
                intervals_list = jsonable_encoder(intervals)
                return JSONResponse(
                    status_code=200,
                    content={"success": True, "data": intervals_list}
                )
            except Exception as e:
                return JSONResponse(
                    status_code=500,
                    content={
                        "success": False,
                        "data": {
                            "title": "Error al obtener intervalos de mantenimiento",
                            "message": f"Error: {str(e)}"
                        }
                    }
                )


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
        

    def get_maintenance_interval_by_id(self, interval_id: int) -> Dict[str, Any]:
        """Obtener un intervalo de mantenimiento por su id"""
        try:
            interval = self.db.query(MaintenanceInterval).filter(MaintenanceInterval.id == interval_id).first()
            if not interval:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "data": "Intervalo de mantenimiento no encontrado"}
                )
            interval_data = jsonable_encoder(interval)
            return JSONResponse(
                status_code=200,
                content={"success": True, "data": interval_data}
            )
        except Exception as e:
            self.db.rollback()
            return JSONResponse(
                status_code=500,
                content={"success": False, "data": {
                    "title": "Error al obtener el intervalo de mantenimiento",
                    "message": str(e)
                }}
            )