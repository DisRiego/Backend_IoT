from fastapi import FastAPI
from app.database import Base, engine
from app.devices.routes import router as devices_router
from app.devices_request.routes import router as devices_request_router
from app.middlewares import setup_middlewares
from app.exceptions import setup_exception_handlers
from app.arduino_reader import start_background_jobs

from app.arduino_reader import (
    device_status_scheduler
)

import threading, time

app = FastAPI(
    title="Distrito de Riego API Gateway - IoT",
    description="API Gateway para IoT en el sistema de riego",
    version="1.0.0",
)

setup_middlewares(app)
setup_exception_handlers(app)

app.include_router(devices_router)
app.include_router(devices_request_router)

Base.metadata.create_all(bind=engine)

# ── Lanzar los dos hilos en el startup ─────────────────────
@app.on_event("startup")
def startup_event():
    start_background_jobs()

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "API funcionando correctamente"}
