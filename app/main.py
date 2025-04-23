# main.py
from fastapi import FastAPI
from sqlalchemy.orm import Session
from app.database import Base, engine
from app.devices.routes import router as devices_router
from app.devices_request.routes import router as devices_request_router
from app.middlewares import setup_middlewares
from app.exceptions import setup_exception_handlers

# ─── Jobs que sí siguen activos ──────────────────────────
from app.arduino_reader import device_status_scheduler, registrar_volumen_final

import threading
import time

# ─── Instancia FastAPI ───────────────────────────────────
app = FastAPI(
    title="Distrito de Riego API Gateway - IoT",
    description="API Gateway para IoT en el sistema de riego",
    version="1.0.0",
)

# ─── Middlewares y manejadores de excepciones ────────────
setup_middlewares(app)
setup_exception_handlers(app)

# ─── Rutas -----------------------------------------------------------------
app.include_router(devices_router)
app.include_router(devices_request_router)

# ─── Crear tablas (si no existen) ────────────────────────
Base.metadata.create_all(bind=engine)

# ─── Lanzar hilos en el arranque ─────────────────────────
# main.py  – arranque
@app.on_event("startup")
def startup_event():
    threading.Thread(target=device_status_scheduler, daemon=True).start()
    #  ⟶  NO vuelvas a arrancar registrar_volumen_final()


# ─── Endpoint de salud ───────────────────────────────────
@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "API funcionando correctamente"}
