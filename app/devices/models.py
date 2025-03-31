from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Float, Date
from sqlalchemy.orm import relationship
from app.database import Base

# =======================================================
# Modelos para la configuración y operación de dispositivos
# =======================================================

class DeviceCategories(Base):
    """
    Categorías de dispositivos (por ejemplo, IoT, Fuente de energía, Conectividad)
    """
    __tablename__ = "device_categories"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    # Relación: Una categoría puede tener varios tipos de dispositivos.
    device_types = relationship("DeviceType", back_populates="device_category")


class DeviceType(Base):
    """
    Tipos de dispositivos (por ejemplo, Válvula, Medidor, Controlador, etc.)
    Se relaciona con una categoría definida en DeviceCategories.
    """
    __tablename__ = "device_type"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(30), nullable=False)
    device_category_id = Column(Integer, ForeignKey("device_categories.id"))
    # Relaciones
    device_category = relationship("DeviceCategories", back_populates="device_types")
    devices = relationship("Device", back_populates="device_type")


class Device(Base):
    """
    Configuración general del dispositivo.
    Se definen propiedades fijas y se relaciona con DeviceType.
    Además, se establece una relación uno a uno con DeviceIot (parte operativa).
    """
    __tablename__ = "devices"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    devices_type_id = Column(Integer, ForeignKey("device_type.id"))
    properties = Column(JSON)
    # Relaciones
    device_type = relationship("DeviceType", back_populates="devices")
    device_iot = relationship("DeviceIot", back_populates="device", uselist=False)


class DeviceIot(Base):
    """
    Información operativa de dispositivos IoT.
    Aquí se almacenan datos dinámicos (por ejemplo, la lectura del sensor en price_device)
    y otros datos operativos.
    """
    __tablename__ = "device_iot"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    serial_number = Column(Integer, nullable=True)
    model = Column(String(45), nullable=True)
    lot_id = Column(Integer, ForeignKey("lot.id"), nullable=True)
    installation_date = Column(DateTime, nullable=True)
    maintenance_interval_id = Column(Integer, ForeignKey("maintenance_intervals.id"), nullable=True)
    estimated_maintenance_date = Column(DateTime, nullable=True)
    status = Column(Integer, ForeignKey("vars.id"), nullable=True)
    devices_id = Column(Integer, ForeignKey("devices.id"), nullable=True)
    price_device = Column(JSON, nullable=True)
    
    # Relaciones con otros modelos
    lot = relationship("Lot")
    maintenance_interval = relationship("MaintenanceInterval")
    status_var = relationship("Vars", foreign_keys=[status])
    # Relación inversa con Device (configuración general)
    device = relationship("Device", back_populates="device_iot")


# =======================================================
# Modelos de otros microservicios
# =======================================================

class Lot(Base):
    """
    Modelo para la tabla lot, que almacena la información de un lote.
    """
    __tablename__ = 'lot'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    longitude = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    extension = Column(Float, nullable=False)
    real_estate_registration_number = Column(Integer, nullable=False)
    public_deed = Column(String, nullable=True)
    freedom_tradition_certificate = Column(String, nullable=True)
    
    payment_interval = Column(Integer, ForeignKey("payment_interval.id"), nullable=True)
    type_crop_id = Column(Integer, ForeignKey('type_crop.id'), nullable=True)
    planting_date = Column(Date, nullable=True)
    estimated_harvest_date = Column(Date, nullable=True)
    state = Column("State", Integer, ForeignKey("vars.id"), default=18, nullable=False)

    # Si tienes definido TypeCrop, la relación se puede agregar
    # type_crop = relationship("TypeCrop", back_populates="lots")

    def __repr__(self):
        return f"<Lot(id={self.id}, name={self.name}, state={self.state})>"


class Vars(Base):
    """
    Modelo para la tabla vars, que se utiliza para estados u otros valores.
    """
    __tablename__ = 'vars'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    # Si tienes una relación con Role, agrégala según tu modelo.
    # role = relationship('Role', back_populates='vars')


class MaintenanceInterval(Base):
    """
    Modelo para la tabla maintenance_intervals, que almacena intervalos de mantenimiento.
    """
    __tablename__ = 'maintenance_intervals'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(30))
    days = Column(Integer)


class Property(Base):
    """
    Modelo para la tabla property, que almacena la información de una propiedad (predio).
    """
    __tablename__ = 'property'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    longitude = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    extension = Column(Float, nullable=False)
    real_estate_registration_number = Column(Integer, nullable=False)
    public_deed = Column(String, nullable=True)
    freedom_tradition_certificate = Column(String, nullable=True)
    state = Column("State", Integer, ForeignKey("vars.id"), default=16, nullable=False)

    def __repr__(self):
        return f"<Property(id={self.id}, name={self.name}, state={self.state})>"

class PropertyLot(Base):
    __tablename__ = 'property_lot'

    property_id = Column(Integer, ForeignKey('property.id'), primary_key=True)
    lot_id = Column(Integer, ForeignKey('lot.id'), primary_key=True)
