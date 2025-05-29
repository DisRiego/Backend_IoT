# ---------- 1. Imagen base ----------
FROM python:3.11-slim

# ---------- 2. Instalar tzdata para zonas horarias ----------
RUN apt-get update \
 && apt-get install -y --no-install-recommends tzdata \
 && rm -rf /var/lib/apt/lists/*

# Ajusta la zona por defecto en build (opcional)
ENV TZ=America/Bogota
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
 && echo $TZ > /etc/timezone

# ---------- 3. Directorio de trabajo ----------
WORKDIR /app

# ---------- 4. Copiar código ----------
COPY . /app/

# ---------- 5. Instalar dependencias ----------
RUN pip install --no-cache-dir -r requirements.txt

# ---------- 6. Exponer puerto (opcional) ----------
EXPOSE 10000

# ---------- 7. Comando de arranque ----------
ENV PYTHONUNBUFFERED=1 \
    PORT=8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
