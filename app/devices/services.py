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
    DeviceIotReadingUpdateByLot
)

class DeviceService:
    def __init__(self, db: Session):
        self.db = db

    def get_all_devices(self) -> Dict[str, Any]:
        """Obtener todos los dispositivos con información operativa (estado, lote, propiedad y categoría)"""
        try:
            devices = (
                self.db.query(
                    DeviceIot,
                    DeviceType,
                    Device,
                    Lot,
                    Property,
                    PropertyUser,
                    User,
                    Vars,
                    DeviceCategories  # Añadimos DeviceCategories para obtener el nombre de la categoría
                )
                .join(DeviceType, DeviceIot.devices_id == DeviceType.id)
                .join(Device, DeviceIot.devices_id == Device.id)  # Relación con Device
                .join(Lot, DeviceIot.lot_id == Lot.id)
                .join(PropertyLot, Lot.id == PropertyLot.lot_id)
                .join(Property, PropertyLot.property_id == Property.id)
                .join(PropertyUser, Property.id == PropertyUser.property_id)
                .join(User, PropertyUser.user_id == User.id)
                .join(Vars, DeviceIot.status == Vars.id)  # Relación con Vars para obtener el estado del dispositivo
                .join(DeviceCategories, DeviceType.device_category_id == DeviceCategories.id)  # Relación con DeviceCategory
                .all()
            )

            devices_list = []
            for device, device_type, device_details, lot, property_data, property_user, user, state, category in devices:
                device_data = jsonable_encoder(device)

                device_data["device_type_name"] = device_type.name  # Nombre del tipo de dispositivo
                device_data["device_category_name"] = category.name  # Nombre de la categoría del dispositivo
                device_data["owner_document_number"] = user.document_number  # Número de documento del propietario
                device_data["lot_id"] = lot.id  # ID del lote
                device_data["lot_name"] = lot.name  # Nombre del lote
                device_data["property_id"] = property_data.id  # ID del predio
                device_data["real_estate_registration_number"] = property_data.real_estate_registration_number
                device_data["property_state"] = state.name  # Nombre del estado del predio
                device_data["device_status_name"] = state.name  # Nombre del estado del dispositivo

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
            result = (
                self.db.query(
                    DeviceIot,
                    DeviceType,
                    Lot,
                    Property,
                    PropertyUser,
                    User,
                    Vars
                )
                .join(DeviceType, DeviceIot.devices_id == DeviceType.id)
                .join(Lot, DeviceIot.lot_id == Lot.id)
                .join(PropertyLot, Lot.id == PropertyLot.lot_id)
                .join(Property, PropertyLot.property_id == Property.id)
                .join(PropertyUser, Property.id == PropertyUser.property_id)
                .join(User, PropertyUser.user_id == User.id)
                .join(Vars, Property.state == Vars.id)
                .filter(DeviceIot.id == device_id)
                .first()
            )

            if not result:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "data": "Dispositivo no encontrado"}
                )

            device, device_type, lot, property_data, property_user, user, state = result
            device_data = jsonable_encoder(device)
            device_data["device_type_name"] = device_type.name  # Nombre del tipo de dispositivo
            device_data["owner_document_number"] = user.document_number  # Número de documento del propietario
            device_data["lot_id"] = lot.id  # ID del lote
            device_data["lot_name"] = lot.name
            device_data["property_id"] = property_data.id  # ID del predio
            device_data["real_estate_registration_number"] = property_data.real_estate_registration_number
            device_data["property_state"] = state.name

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
            # Se asume que DeviceCreate contiene los campos operativos:
            # serial_number, model, devices_id, y sensor_value para price_device.
            data = device_data.dict()
            new_device = DeviceIot(
                serial_number = data.get("serial_number"),
                model = data.get("model"),
                devices_id = data.get("devices_id"),
                price_device = {"sensor_value": data.get("sensor_value")},
                lot_id = data.get("lot_id"),
                installation_date = data.get("installation_date"),
                maintenance_interval_id = data.get("maintenance_interval_id"),
                estimated_maintenance_date = data.get("estimated_maintenance_date"),
                status = data.get("status")
            )
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
        """Actualizar el estado del dispositivo (habilitar/inhabilitar)"""
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
            device.status = new_status
            self.db.commit()
            self.db.refresh(device)
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
        """Asignar un dispositivo a un lote"""
        try:
            device = self.db.query(DeviceIot).filter(DeviceIot.id == assignment_data.device_id).first()
            if not device:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "data": "Dispositivo no encontrado"}
                )
            if device.status == 25:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "data": {
                            "title": "Operación no válida",
                            "message": "No se puede asignar un dispositivo inhabilitado"
                        }
                    }
                )
            if device.lot_id:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "data": {
                            "title": "Operación no válida",
                            "message": "El dispositivo ya está asignado a un lote. Use reasignar en su lugar."
                        }
                    }
                )
            # Verificar lote
            lot = self.db.query(Lot).filter(Lot.id == assignment_data.lot_id).first()
            if not lot:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "data": "Lote no encontrado"}
                )
            # Verificar que el lote pertenezca al predio especificado utilizando la tabla intermedia PropertyLot
            property_lot = self.db.query(PropertyLot).filter(
                PropertyLot.lot_id == assignment_data.lot_id,
                PropertyLot.property_id == assignment_data.property_id
            ).first()
            if not property_lot:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "data": {
                            "title": "Operación no válida",
                            "message": "El lote no pertenece al predio especificado"
                        }
                    }
                )
            maintenance_interval = self.db.query(MaintenanceInterval).filter(
                MaintenanceInterval.id == assignment_data.maintenance_interval_id
            ).first()
            if not maintenance_interval:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "data": "Intervalo de mantenimiento no encontrado"}
                )
            device.lot_id = assignment_data.lot_id
            device.installation_date = assignment_data.installation_date
            device.maintenance_interval_id = assignment_data.maintenance_interval_id
            device.estimated_maintenance_date = assignment_data.installation_date + timedelta(days=maintenance_interval.days)
            self.db.commit()
            self.db.refresh(device)
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": {
                        "title": "Asignación exitosa",
                        "message": "El dispositivo ha sido asignado al lote correctamente",
                        "device_id": device.id,
                        "lot_id": lot.id,
                        "lot_name": lot.name,
                        "installation_date": device.installation_date.isoformat() if device.installation_date else None,
                        "maintenance_interval": maintenance_interval.name,
                        "estimated_maintenance_date": device.estimated_maintenance_date.isoformat() if device.estimated_maintenance_date else None
                    }
                }
            )
        except Exception as e:
            self.db.rollback()
            return JSONResponse(
                status_code=500,
                content={"success": False, "data": {"title": "Error al asignar lote", "message": str(e)}}
            )

    def reassign_to_lot(self, reassignment_data: DeviceReassignRequest, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Reasignar un dispositivo a otro lote"""
        try:
            device = self.db.query(DeviceIot).filter(DeviceIot.id == reassignment_data.device_id).first()
            if not device:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "data": "Dispositivo no encontrado"}
                )
            if device.status == 25:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "data": {"title": "Operación no válida", "message": "No se puede reasignar un dispositivo inhabilitado"}
                    }
                )
            if not device.lot_id:
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "data": {"title": "Operación no válida", "message": "El dispositivo no está asignado a ningún lote. Use asignar en su lugar."}}
                )
            previous_lot_id = device.lot_id
            lot = self.db.query(Lot).filter(Lot.id == reassignment_data.lot_id).first()
            if not lot:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "data": "Lote no encontrado"}
                )
            # Validar que el lote pertenezca al predio especificado usando la tabla intermedia PropertyLot
            property_lot = self.db.query(PropertyLot).filter(
                PropertyLot.lot_id == reassignment_data.lot_id,
                PropertyLot.property_id == reassignment_data.property_id
            ).first()
            if not property_lot:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "data": {
                            "title": "Operación no válida",
                            "message": "El lote no pertenece al predio especificado"
                        }
                    }
                )
            maintenance_interval = self.db.query(MaintenanceInterval).filter(
                MaintenanceInterval.id == reassignment_data.maintenance_interval_id
            ).first()
            if not maintenance_interval:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "data": "Intervalo de mantenimiento no encontrado"}
                )
            device.lot_id = reassignment_data.lot_id
            device.installation_date = reassignment_data.installation_date
            device.maintenance_interval_id = reassignment_data.maintenance_interval_id
            device.estimated_maintenance_date = reassignment_data.installation_date + timedelta(days=maintenance_interval.days)
            self.db.commit()
            self.db.refresh(device)
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": {
                        "title": "Reasignación exitosa",
                        "message": "El dispositivo ha sido reasignado al lote correctamente",
                        "device_id": device.id,
                        "previous_lot_id": previous_lot_id,
                        "new_lot_id": lot.id,
                        "lot_name": lot.name,
                        "installation_date": device.installation_date.isoformat() if device.installation_date else None,
                        "maintenance_interval": maintenance_interval.name,
                        "estimated_maintenance_date": device.estimated_maintenance_date.isoformat() if device.estimated_maintenance_date else None
                    }
                }
            )
        except Exception as e:
            self.db.rollback()
            return JSONResponse(
                status_code=500,
                content={"success": False, "data": {"title": "Error al reasignar lote", "message": str(e)}}
            )

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
            devices = (
                self.db.query(
                    DeviceIot,
                    Vars.name.label("status_name")
                )
                .outerjoin(Vars, DeviceIot.status == Vars.id)
                .filter(DeviceIot.lot_id == lot_id)
                .all()
            )
            devices_list = []
            for device, status_name in devices:
                device_dict = jsonable_encoder(device)
                device_dict["status_name"] = status_name
                devices_list.append(device_dict)
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": {
                        "lot_id": lot_id,
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
                .join(Lot, DeviceIot.lot_id == Lot.id)
                .join(PropertyLot, Lot.id == PropertyLot.lot_id)
                .join(Property, PropertyLot.property_id == Property.id)
                .join(PropertyUser, Property.id == PropertyUser.property_id)  # Relación con PropertyUser
                .join(User, PropertyUser.user_id == User.id)  # Relación con User para obtener el documento
                .join(Vars, DeviceIot.status == Vars.id)  # Relación con Vars para obtener el estado del dispositivo
                .join(DeviceCategories, DeviceType.device_category_id == DeviceCategories.id)  # Relación con DeviceCategory
                .filter(DeviceType.device_category_id == category_id)
                .all()
            )

            devices_list = []
            for device, device_type, device_details, lot, property_data, property_user, user, state, category in devices:
                device_data = jsonable_encoder(device)

                # Agregar información relacionada
                device_data["device_type_name"] = device_type.name  # Nombre del tipo de dispositivo
                device_data["category_name"] = category.name  # Nombre de la categoría
                device_data["device_status_name"] = state.name  # Nombre del estado del dispositivo
                device_data["lot_id"] = lot.id  # ID del lote
                device_data["lot_name"] = lot.name  # Nombre del lote
                device_data["property_id"] = property_data.id  # ID del predio
                device_data["real_estate_registration_number"] = property_data.real_estate_registration_number
                device_data["owner_document_number"] = user.document_number  # Número de documento del propietario
                device_data["property_state"] = state.name  # Nombre del estado del predio

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