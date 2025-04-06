from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.database import Base, engine, get_db
from app.devices.routes import router as devices_router
from app.devices_request.routes import router as devices_request_router
from app.middlewares import setup_middlewares
from app.exceptions import setup_exception_handlers
from app.arduino_reader import read_serial_data
from app.devices.models import User, Notification
from app.websockets import notification_manager
import threading
import json

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

# Agregar este endpoint WebSocket
@app.websocket("/ws/notifications/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, db: Session = Depends(get_db)):
    """Endpoint WebSocket para recibir notificaciones en tiempo real"""
    # Verificar si el usuario existe
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        await websocket.close(code=1008)  # Policy Violation
        return
    
    # Aceptar la conexión
    await notification_manager.connect(websocket, user_id)
    
    try:
        # Escuchar mensajes del cliente
        while True:
            data = await websocket.receive_text()
            # Procesar comandos del cliente (por ejemplo, marcar como leída una notificación)
            try:
                message = json.loads(data)
                if message.get("action") == "mark_as_read" and "notification_id" in message:
                    # Aquí podrías implementar la lógica para marcar como leída
                    notification = db.query(Notification).filter(Notification.id == message["notification_id"]).first()
                    if notification and notification.user_id == user_id:
                        notification.read = True
                        db.commit()
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        notification_manager.disconnect(websocket)
