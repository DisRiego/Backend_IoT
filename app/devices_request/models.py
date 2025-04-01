from sqlalchemy import TIMESTAMP, Column, Date, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Vars(Base):
    __tablename__ = 'vars'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)

    # role = relationship('Role', back_populates='vars')

class TypeOpen(Base):
    __tablename__ = 'type_opening'
    
    id = Column(Integer, primary_key=True, index=True)
    type_opening = Column(String)

    # __table_args__ = {'extend_existing': True}
    # role = relationship('Request', back_populates='type_opening')

class Request(Base):
    __tablename__ = 'request'

    id = Column(Integer, primary_key=True, index=True)
    type_opening_id = Column(Integer)
    status = Column(Integer)
    lot_id = Column(Integer)
    user_id = Column(Integer)
    device_iot_id = Column(Integer)
    open_date = Column(DateTime)
    close_date = Column(DateTime)
    request_date = Column(DateTime)
    volume_water = Column(Integer)

    # Relaciones
    # type_opening = relationship("TypeOpening", back_populates="requests")
    # status_type = relationship("Status", back_populates="requests")
    # lot = relationship("Lot", back_populates="requests")
    # user = relationship("User", back_populates="requests")
    # device = relationship("DeviceIoT", back_populates="requests")

    def __repr__(self):
        return f"<Request(id={self.id}, open_date={self.open_date}, volume_water={self.volume_water})>"
    

class DeviceIoT(Base):
    __tablename__ = "devices_iot"

    id = Column(Integer, primary_key=True, index=True)
    serial_number = Column(Integer, nullable=False)
    model = Column(String(45), nullable=True)
    lot_id = Column(Integer, nullable=False)  # Relación con la tabla Lot
    installation_date = Column(DateTime, nullable=False)
    maintenance_interval_id = Column(Integer, nullable=True)  # Relación con la tabla MaintenanceInterval
    estimated_maintenance_date = Column(DateTime, nullable=True)
    status = Column(Integer, nullable=False)  # Suponiendo que el estado es un valor numérico
    devices_id = Column(Integer, nullable=True)  # Relación con la tabla Devices
    price_device = Column(JSON, nullable=True)  # Guardamos el precio en formato JSON
    user_id = Column(Integer, nullable=False)  # Relación con la tabla Users

    # Relaciones
    # lot = relationship("Lot", back_populates="devices")  # Relación con Lot
    # maintenance_interval = relationship("MaintenanceInterval", back_populates="devices")  # Relación con MaintenanceInterval
    # devices = relationship("Device", back_populates="device_iots")  # Relación con Devices
    # user = relationship("User", back_populates="devices")  # Relación con Users

    def __repr__(self):
        return f"<DeviceIoT(id={self.id}, serial_number={self.serial_number}, model={self.model})>"
