import os
import uuid
from app.devices.models import Devices
from fastapi import HTTPException, UploadFile, File, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import date
from app.firebase_config import bucket


class PropertyLotService:
    def __init__(self, db: Session):
        self.db = db

    def get_devices(self):
        """Obtener todos los dispositivos, incluyendo todos los datos"""
        try:
            devices = (
                self.db.query(Devices).all()
            )

            if not devices:
                return JSONResponse(status_code=404, content={"success": False, "data": []})

            return JSONResponse(
                status_code=200,
                content={"success": True, "data": devices}
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "data": {
                        "title": "Dispositivos",
                        "message": f"Error al obtener los dispositivos, contacta al administrador: {str(e)}"
                    }
                }
            )