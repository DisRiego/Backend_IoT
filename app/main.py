from fastapi import FastAPI
from app.database import Base, engine
from app.devices.routes import router as devices_router
from app.devices_request.routes import router as devices_request_router
from app.middlewares import setup_middlewares
from app.exceptions import setup_exception_handlers
from app.arduino_reader import read_serial_data 
import threading

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
    # Inicia el hilo en segundo plano para leer el puerto serial
    threading.Thread(target=read_serial_data, daemon=True).start()
    print("Hilo de lectura del Arduino iniciado.")
    
# **Endpoint de Salud**
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "message": "API funcionando correctamente"}
