from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class DeviceCategory(Base):
    """
    Categoría general de dispositivos (por ejemplo: IoT, Fuente de energía, Conectividad).
    """
    __tablename__ = "device_categories"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)

    types = relationship("DeviceType", back_populates="category")


class DeviceType(Base):
    """
    Tipo específico de dispositivo (ej: Válvula, Relé, Batería), asociado a una categoría.
    """
    __tablename__ = "device_type"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    device_category_id = Column(Integer, ForeignKey("device_categories.id"))

    category = relationship("DeviceCategory", back_populates="types")
    devices = relationship("Device", back_populates="device_type")


class Device(Base):
    """
    Estructura base de propiedades dinámicas para cada tipo de dispositivo.
    Estas propiedades se usan para construir formularios en el frontend.

    No representa un dispositivo real, sino la plantilla del tipo.
    """
    __tablename__ = "devices"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    devices_type_id = Column(Integer, ForeignKey("device_type.id"), nullable=False)
    properties = Column(JSONB, nullable=True)

    device_type = relationship("DeviceType", back_populates="devices")
    instances = relationship("DeviceIOT", back_populates="device_template")


class MaintenanceInterval(Base):
    """
    Define intervalos de mantenimiento (en días) para dispositivos IoT.
    """
    __tablename__ = "maintenance_intervals"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(30), nullable=False)
    days = Column(Integer, nullable=False)

    devices_iot = relationship("DeviceIOT", back_populates="maintenance_interval")


class DeviceIOT(Base):
    """
    Representa un dispositivo IoT registrado en el sistema.

    Contiene información fija (número de serie, modelo, fechas, estado) y propiedades
    variables almacenadas en formato JSONB (price_device), definidas por su tipo.
    """
    __tablename__ = "device_iot"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    serial_number = Column(Integer, nullable=False)
    model = Column(String(45), nullable=False)
    lot_id = Column(Integer, nullable=False)
    installation_date = Column(DateTime)
    maintenance_interval_id = Column(Integer, ForeignKey("maintenance_intervals.id"))
    estimated_maintenance_date = Column(DateTime)
    status = Column(Integer, default=11)
    devices_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    price_device = Column(JSONB)
    user_id = Column(Integer, ForeignKey("users.id"))

    device_template = relationship("Device", back_populates="instances")
    maintenance_interval = relationship("MaintenanceInterval", back_populates="devices_iot")
    user = relationship("User", back_populates="devices")


class User(Base):
    """
    Usuario del sistema. Se utiliza para asociar dispositivos con una persona.
    """
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    document_number = Column(String, nullable=False)

    devices = relationship("DeviceIOT", back_populates="user")