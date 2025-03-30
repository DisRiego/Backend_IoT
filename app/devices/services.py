from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from app.devices.schemas import DeviceAssignRequest, DeviceReassignRequest
from typing import Dict, Any, List, Optional
from datetime import datetime

# Importar modelos y esquemas
from app.devices.models import Device

from app.devices.schemas import DeviceCreate, DeviceUpdate

class DeviceService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_devices(self) -> Dict[str, Any]:
        """Obtener todos los dispositivos con su información relacionada"""
        try:
            # Consulta con join para obtener información relacionada
            devices = (
                self.db.query(
                    Device,
                    Vars.name.label("status_name"),
                    Lot.name.label("lot_name")
                )
                .outerjoin(Vars, Device.status == Vars.id)
                .outerjoin(Lot, Device.lot_id == Lot.id)
                .all()
            )
            
            # Procesar resultados
            devices_list = []
            for device, status_name, lot_name in devices:
                device_dict = jsonable_encoder(device)
                device_dict["status_name"] = status_name
                device_dict["lot_name"] = lot_name
                devices_list.append(device_dict)
                
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
        """Obtener detalles de un dispositivo específico"""
        try:
            # Consulta con join para obtener información relacionada
            result = (
                self.db.query(
                    Device,
                    Vars.name.label("status_name"),
                    Lot.name.label("lot_name")
                )
                .outerjoin(Vars, Device.status == Vars.id)
                .outerjoin(Lot, Device.lot_id == Lot.id)
                .filter(Device.id == device_id)
                .first()
            )
            
            if not result:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "data": "Dispositivo no encontrado"}
                )
                
            device, status_name, lot_name = result
            device_data = jsonable_encoder(device)
            device_data["status_name"] = status_name
            device_data["lot_name"] = lot_name
            
            # Intentar obtener información del tipo de dispositivo
            if device.devices_id:
                device_type = self.db.query(
                    "devices"
                ).filter_by(id=device.devices_id).first()
                if device_type:
                    device_data["device_type_name"] = device_type.name  # Ajusta esto según tu modelo
            
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
        """Crear un nuevo dispositivo"""
        try:
            # Convertir el esquema Pydantic a un diccionario
            device_dict = device_data.dict()
            
            # Crear el dispositivo
            new_device = Device(**device_dict)
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
        """Actualizar información del dispositivo"""
        try:
            # Buscar el dispositivo
            device = self.db.query(Device).filter(Device.id == device_id).first()
            if not device:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "data": "Dispositivo no encontrado"}
                )
            
            # Actualizar campos
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
        device = self.db.query(Device).filter(Device.id == device_id).first()
        if not device:
            return JSONResponse(
                status_code=404,
                content={"success": False, "data": "Dispositivo no encontrado"}
            )
        
        # Verificar si el nuevo status existe
        status = self.db.query(Vars).filter(Vars.id == new_status).first()
        if not status:
            return JSONResponse(
                status_code=400,
                content={"success": False, "data": "Estado no válido"}
            )
        
        # Verificar que no esté intentando cambiar a un estado igual al actual
        if device.status == new_status:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False, 
                    "data": {
                        "title": "Operación no válida",
                        "message": f"El dispositivo ya se encuentra en el estado '{status.name}'"
                    }
                }
            )
        
        # Actualizar estado
        device.status = new_status
        self.db.commit()
        self.db.refresh(device)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "title": "Estado actualizado",
                    "message": f"El estado del dispositivo ha sido actualizado a '{status.name}' correctamente",
                    "device_id": device.id,
                    "new_status": new_status,
                    "status_name": status.name
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
        # Verificar dispositivo
        device = self.db.query(Device).filter(Device.id == assignment_data.device_id).first()
        if not device:
            return JSONResponse(
                status_code=404,
                content={"success": False, "data": "Dispositivo no encontrado"}
            )
        
        # Verificar que el dispositivo no esté inhabilitado
        if device.status == 25:  # Asumo 25 como el ID para inhabilitado
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
        
        # Verificar que el dispositivo no esté ya asignado
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
        
        # Verificar que el lote pertenezca al predio especificado
        if lot.property_id != assignment_data.property_id:
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
        
        # Verificar intervalo de mantenimiento
        maintenance_interval = self.db.query(MaintenanceInterval).filter(
            MaintenanceInterval.id == assignment_data.maintenance_interval_id
        ).first()
        if not maintenance_interval:
            return JSONResponse(
                status_code=404,
                content={"success": False, "data": "Intervalo de mantenimiento no encontrado"}
            )
        
        # Realizar asignación
        device.lot_id = assignment_data.lot_id
        device.installation_date = assignment_data.installation_date
        device.maintenance_interval_id = assignment_data.maintenance_interval_id
        
        # Calcular fecha estimada de mantenimiento basada en el intervalo
        device.estimated_maintenance_date = assignment_data.installation_date + timedelta(
            days=maintenance_interval.days
        )
        
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
                    "installation_date": device.installation_date.isoformat(),
                    "maintenance_interval": maintenance_interval.name,
                    "estimated_maintenance_date": device.estimated_maintenance_date.isoformat()
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
                    "title": "Error al asignar lote",
                    "message": f"Error: {str(e)}"
                }
            }
        )

def reassign_to_lot(self, reassignment_data: DeviceReassignRequest, user_id: Optional[int] = None) -> Dict[str, Any]:
    """Reasignar un dispositivo a otro lote"""
    try:
        # Verificar dispositivo
        device = self.db.query(Device).filter(Device.id == reassignment_data.device_id).first()
        if not device:
            return JSONResponse(
                status_code=404,
                content={"success": False, "data": "Dispositivo no encontrado"}
            )
        
        # Verificar que el dispositivo no esté inhabilitado
        if device.status == 25:  # Asumo 25 como el ID para inhabilitado
            return JSONResponse(
                status_code=400,
                content={
                    "success": False, 
                    "data": {
                        "title": "Operación no válida",
                        "message": "No se puede reasignar un dispositivo inhabilitado"
                    }
                }
            )
        
        # Verificar que el dispositivo esté ya asignado
        if not device.lot_id:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False, 
                    "data": {
                        "title": "Operación no válida",
                        "message": "El dispositivo no está asignado a ningún lote. Use asignar en su lugar."
                    }
                }
            )
        
        # Guardar el lote anterior para la respuesta
        previous_lot_id = device.lot_id
        
        # Verificar nuevo lote
        lot = self.db.query(Lot).filter(Lot.id == reassignment_data.lot_id).first()
        if not lot:
            return JSONResponse(
                status_code=404,
                content={"success": False, "data": "Lote no encontrado"}
            )
        
        # Verificar que el lote pertenezca al predio especificado
        if lot.property_id != reassignment_data.property_id:
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
        
        # Verificar intervalo de mantenimiento
        maintenance_interval = self.db.query(MaintenanceInterval).filter(
            MaintenanceInterval.id == reassignment_data.maintenance_interval_id
        ).first()
        if not maintenance_interval:
            return JSONResponse(
                status_code=404,
                content={"success": False, "data": "Intervalo de mantenimiento no encontrado"}
            )
        
        # Realizar reasignación
        device.lot_id = reassignment_data.lot_id
        device.installation_date = reassignment_data.installation_date
        device.maintenance_interval_id = reassignment_data.maintenance_interval_id
        
        # Calcular fecha estimada de mantenimiento basada en el intervalo
        device.estimated_maintenance_date = reassignment_data.installation_date + timedelta(
            days=maintenance_interval.days
        )
        
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
                    "installation_date": device.installation_date.isoformat(),
                    "maintenance_interval": maintenance_interval.name,
                    "estimated_maintenance_date": device.estimated_maintenance_date.isoformat()
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
                    "title": "Error al reasignar lote",
                    "message": f"Error: {str(e)}"
                }
            }
        )
    
    def delete_device(self, device_id: int) -> Dict[str, Any]:
        """Eliminar un dispositivo (borrado lógico mediante cambio de estado)"""
        try:
            device = self.db.query(Device).filter(Device.id == device_id).first()
            if not device:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "data": "Dispositivo no encontrado"}
                )
            
            # Cambiar estado a "eliminado" (ajusta el ID según tu esquema)
            deleted_status_id = 25  # Asume que el ID para "eliminado" es 25 - ajusta según tu base de datos
            device.status = deleted_status_id
            
            self.db.commit()
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": {
                        "title": "Dispositivo eliminado",
                        "message": "El dispositivo ha sido eliminado correctamente"
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
                        "title": "Error al eliminar dispositivo",
                        "message": f"Error: {str(e)}"
                    }
                }
            )
    
    def get_devices_by_lot(self, lot_id: int) -> Dict[str, Any]:
        """Obtener todos los dispositivos asignados a un lote específico"""
        try:
            # Verificar que el lote existe
            lot = self.db.query(Lot).filter(Lot.id == lot_id).first()
            if not lot:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "data": "Lote no encontrado"}
                )
            
            # Consultar dispositivos del lote
            devices = (
                self.db.query(
                    Device,
                    Vars.name.label("status_name")
                )
                .outerjoin(Vars, Device.status == Vars.id)
                .filter(Device.lot_id == lot_id)
                .all()
            )
            
            # Procesar resultados
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
                    "data": {
                        "title": "Error al obtener dispositivos",
                        "message": f"Error: {str(e)}"
                    }
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
            # Construir consulta base
            query = self.db.query(
                Device,
                Vars.name.label("status_name"),
                Lot.name.label("lot_name")
            ).outerjoin(Vars, Device.status == Vars.id) \
             .outerjoin(Lot, Device.lot_id == Lot.id)
            
            # Aplicar filtros
            if serial_number is not None:
                query = query.filter(Device.serial_number == serial_number)
            
            if model is not None:
                query = query.filter(Device.model.ilike(f"%{model}%"))
            
            if lot_id is not None:
                query = query.filter(Device.lot_id == lot_id)
            
            if status is not None:
                query = query.filter(Device.status == status)
            
            if device_type_id is not None:
                query = query.filter(Device.devices_id == device_type_id)
            
            # Contar total de resultados
            total = query.count()
            
            # Aplicar paginación
            query = query.offset((page - 1) * page_size).limit(page_size)
            
            # Ejecutar consulta
            results = query.all()
            
            # Procesar resultados
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
                    "data": {
                        "title": "Error al filtrar dispositivos",
                        "message": f"Error: {str(e)}"
                    }
                }
            )