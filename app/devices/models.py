from sqlalchemy import Column, Date, Float, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Device(Base):
    __tablename__ = "device_iot"

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
    
    # Relaciones
    # lot = relationship("Lot", back_populates="devices")  # Asegúrate de que la relación inversa esté definida en Lot
    # maintenance_interval = relationship("MaintenanceInterval", back_populates="devices")
    # status_var = relationship("Vars", foreign_keys=[status], back_populates="devices")
    # device_type = relationship("Devices", foreign_keys=[devices_id], back_populates="devices")