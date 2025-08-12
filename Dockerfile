# ----------------------
# Stage 1: Build Frontend
# ----------------------
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/vue-app/package*.json ./

ARG VITE_OLLAMA_SERVER_BASE_URL
RUN echo "VITE_OLLAMA_SERVER_BASE_URL=${VITE_OLLAMA_SERVER_BASE_URL}" > .env

RUN npm ci
COPY frontend/vue-app/ ./
RUN npm run build

# ----------------------
# Stage 2: Backend
# ----------------------
FROM python:3.12-slim AS backend

# Instalar dependencias del sistema necesarias para python y gunicorn
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar requirements e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar backend
COPY backend/ ./backend/

# Copiar frontend compilado al backend
COPY --from=frontend-builder /app/frontend/dist ./frontend/vue-app/dist/

# Copiar start.sh y dar permisos
COPY start.sh .
RUN chmod +x start.sh

# Variables de entorno por defecto
ENV PYTHONUNBUFFERED=1 \
    APP_PORT=7000 \
    APP_WORKERS=1

EXPOSE 7000

CMD ["./start.sh"]
