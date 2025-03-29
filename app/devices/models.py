from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from pydantic import BaseModel


class Devices(Base):
    """Modelo de Usuario"""
    __tablename__ = "devices"

    __table_args__ = {'extend_existing': True}  
