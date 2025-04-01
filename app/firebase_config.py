import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, storage

load_dotenv()

FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS")
FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET")

if not FIREBASE_CREDENTIALS:
    raise ValueError("❌ ERROR: FIREBASE_CREDENTIALS no está definido en .env")

if not os.path.exists(FIREBASE_CREDENTIALS):
    raise ValueError(f"❌ ERROR: El archivo de credenciales en {FIREBASE_CREDENTIALS} no existe.")

if not FIREBASE_STORAGE_BUCKET:
    raise ValueError("❌ ERROR: FIREBASE_STORAGE_BUCKET no está definido en .env")

# Inicializa solo si aún no se ha hecho
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_CREDENTIALS)
    firebase_admin.initialize_app(cred, {
        "projectId": "testeo-36565",  # Asegura que es el mismo que está en el JSON
        "storageBucket": FIREBASE_STORAGE_BUCKET  # Bucket que viene del .env
    })

# Bucket explícito (esto es correcto, solo que aquí va el mismo nombre que .env)
bucket = storage.bucket()
