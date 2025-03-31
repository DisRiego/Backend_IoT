import os
import firebase_admin
from firebase_admin import credentials, storage
from dotenv import load_dotenv


load_dotenv()


FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS")
FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET")

if not FIREBASE_CREDENTIALS:
    raise ValueError("❌ ERROR: FIREBASE_CREDENTIALS no está definido en .env")

if not os.path.exists(FIREBASE_CREDENTIALS):
    raise ValueError(f"❌ ERROR: El archivo de credenciales en {FIREBASE_CREDENTIALS} no existe.")

if not FIREBASE_STORAGE_BUCKET:
    raise ValueError("❌ ERROR: FIREBASE_STORAGE_BUCKET no está definido en .env")


cred = credentials.Certificate(FIREBASE_CREDENTIALS)
firebase_admin.initialize_app(cred, {"storageBucket": FIREBASE_STORAGE_BUCKET})
bucket = storage.bucket()

print("✅ Firebase inicializado correctamente.")