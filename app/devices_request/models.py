from sqlalchemy import TIMESTAMP, Column, Date, Integer, String, DateTime, JSON, ForeignKey , Text
from sqlalchemy.orm import relationship
from app.database import Base

class Vars(Base):
    __tablename__ = 'vars'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)

class TypeOpen(Base):
    __tablename__ = 'type_opening'
    
    id = Column(Integer, primary_key=True, index=True)
    type_opening = Column(String)

class Request(Base):
    __tablename__ = 'request'

    id             = Column(Integer, primary_key=True, index=True)
    type_opening_id= Column(Integer)
    status         = Column(Integer)
    lot_id         = Column(Integer)
    user_id        = Column(Integer)
    device_iot_id  = Column(Integer)
    open_date      = Column(DateTime)
    close_date     = Column(DateTime)
    request_date   = Column(DateTime)
    volume_water   = Column(Integer)

    # relación a las entradas de rechazo (0 o 1)
    rejections     = relationship("RequestRejection", back_populates="request")


class DeviceIoT(Base):
    __tablename__ = "device_iot"  # Se usa la tabla correcta
    id = Column(Integer, primary_key=True, index=True)
    serial_number = Column(Integer, nullable=False)
    model = Column(String(45), nullable=True)
    lot_id = Column(Integer, nullable=False)  # Relación con la tabla Lot (asumida existente)
    installation_date = Column(DateTime, nullable=False)
    maintenance_interval_id = Column(Integer, nullable=True)  # Relación con la tabla MaintenanceInterval (asumida)
    estimated_maintenance_date = Column(DateTime, nullable=True)
    status = Column(Integer, nullable=False)  # Estado como valor numérico
    devices_id = Column(Integer, nullable=True)  # Relación con la tabla Devices (asumida)
    price_device = Column(JSON, nullable=True)  # Precio en formato JSON

    def __repr__(self):
        return f"<DeviceIoT(id={self.id}, serial_number={self.serial_number}, model={self.model})>"



class RequestRejectionReason(Base):
    __tablename__ = 'request_rejection_reason'

    id          = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)

    rejections  = relationship("RequestRejection", back_populates="reason")


class RequestRejection(Base):
    __tablename__ = 'request_rejection'

    id         = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey('request.id'), nullable=False)
    reason_id  = Column(Integer, ForeignKey('request_rejection_reason.id'), nullable=False)
    comment    = Column(Text, nullable=True)

    request    = relationship("Request", back_populates="rejections")
    reason     = relationship("RequestRejectionReason", back_populates="rejections")