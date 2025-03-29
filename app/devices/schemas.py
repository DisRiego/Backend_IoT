from pydantic import BaseModel, Field , model_validator , validator
import re
from typing import Optional , List
from datetime import datetime

# Modelo base para la solicitud de usuario
class DeviceBase(BaseModel):
    id: int