from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.database import Base, engine, get_db
from app.devices.routes import router as devices_router
from app.devices_request.routes import router as devices_request_router
from app.middlewares import setup_middlewares
from app.exceptions import setup_exception_handlers
from app.arduino_reader import read_serial_data
from app.devices.models import Notification
from app.arduino_reader import read_serial_data, poll_servo_commands, device_status_scheduler
import serial
import threading
import json

SERIAL_PORT = "COM4"   
BAUD_RATE = 9600

# **Configurar FastAPI**
app = FastAPI(
    title="Distrito de Riego API Gateway - IoT",
    description="API Gateway para IoT en el sistema de riego",
    version="1.0.0"
)

# **Configurar Middlewares**
setup_middlewares(app)

# **Configurar Manejadores de Excepciones**
setup_exception_handlers(app)

# **Registrar Rutas**
app.include_router(devices_router)
app.include_router(devices_request_router)

Base.metadata.create_all(bind=engine)

@app.on_event("startup")
async def startup_event():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Conectado al puerto serial: {SERIAL_PORT} @ {BAUD_RATE}bps")

        threading.Thread(target=read_serial_data, args=(ser,), daemon=True).start()
        threading.Thread(target=poll_servo_commands, args=(ser,), daemon=True).start()
        threading.Thread(target=device_status_scheduler, daemon=True).start()

    except Exception as e:
        print(f"Error al abrir el puerto serial: {e}")


# **Endpoint de Salud**
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "message": "API funcionando correctamente"}


