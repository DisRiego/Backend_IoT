# ---------- 1. Imagen base ----------
    FROM python:3.11-slim

    # ---------- 2. Directorio de trabajo ----------
    WORKDIR /app
    
    # ---------- 3. Copiar código ----------
    COPY . /app/
    
    # ---------- 4. Instalar dependencias ----------
    RUN pip install --no-cache-dir -r requirements.txt
    
    # ---------- 5. Exponer puerto (opcional) ----------
    # No es estrictamente necesario con Render, pero  $PORT suele ser 10000.
    EXPOSE 10000
    
    # ---------- 6. Comando de arranque ----------
    # Render define PORT; si no existe (ejecución local) usa 8000.
    ENV PYTHONUNBUFFERED=1 \
        PORT=8000
    
    CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
    