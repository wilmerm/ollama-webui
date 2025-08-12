# Ollama WebUI

Ollama WebUI es una interfaz gráfica web minimalista y fácil de usar, desarrollada con FastAPI y Vue.js, que permite interactuar con modelos de IA locales a través de Ollama.

![image](https://github.com/user-attachments/assets/fbce0ca0-e4a6-4f93-a102-079d05ae3c25)


## Características

- Interfaz intuitiva y amigable
- Backend rápido con FastAPI
- Interfaz interactiva creada con Vue.js
- Soporte para múltiples modelos de IA locales
- 🐳 **Soporte completo para Docker**

## Métodos de Instalación

### 🐳 Opción 1: Docker (Recomendado)

La forma más fácil de ejecutar Ollama WebUI es utilizando Docker. Esta opción no requiere instalación manual de dependencias.

#### Requisitos Previos
- Docker y Docker Compose instalados
- Ollama ejecutándose en tu sistema (puerto 11434)

#### Inicio Rápido con Docker

**Opción A: Script de instalación automática (Recomendado)**

```bash
# Clona el repositorio
git clone https://github.com/wilmerm/ollama-webui.git
cd ollama-webui

# Ejecuta el script de setup
./docker-setup.sh
```

**Opción B: Instalación manual**

1. **Clona el repositorio:**
   ```bash
   git clone https://github.com/wilmerm/ollama-webui.git
   cd ollama-webui
   ```

2. **Configura las variables de entorno:**
   ```bash
   cp .env.docker .env
   ```

3. **Ejecuta con Docker Compose:**
   ```bash
   docker compose up -d
   ```

4. **Accede a la aplicación:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

#### Configuración Docker

La configuración predeterminada funciona con Ollama ejecutándose en el sistema host. Asegúrate de que:

- Ollama esté ejecutándose: `ollama serve`
- El modelo esté disponible: `ollama pull llama3.2:3b`

**Variables de entorno importantes para Docker:**

```env
# Conexión a Ollama en el host
OLLAMA_BASE_URL=http://host.docker.internal:11434

# Configuración del modelo
DEFAULT_MODEL=llama3.2:3b

# Puertos de la aplicación
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

#### Comandos Docker Útiles

```bash
# Iniciar en segundo plano
docker compose up -d

# Ver logs
docker compose logs -f

# Reconstruir contenedores
docker compose build

# Detener contenedores
docker compose down

# Para producción (con optimizaciones adicionales)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

#### Desarrollo con Docker

Para desarrollo, puedes montar volúmenes para cambios en tiempo real:

```yaml
# Descomenta estas líneas en docker-compose.yml para desarrollo
volumes:
  - ./backend:/app/backend:ro
  - ./frontend/vue-app/src:/app/src:ro
```

### 📦 Opción 2: Instalación Manual

#### Requisitos
- Python 3.8+
- Node.js 16+
- Ollama instalado y ejecutándose

#### Pasos de Instalación

1. Clona el repositorio:
    ```bash
    git clone https://github.com/wilmerm/ollama-webui.git
    cd ollama-webui
    ```

2. Instala las dependencias del backend:
    ```bash
    pip install -r requirements.txt
    ```

3. Instala las dependencias del frontend:
    ```bash
    cd frontend/vue-app
    npm install
    ```

## Configuración de Variables de Entorno

### Para Docker

Si usas Docker, copia el archivo de ejemplo específico para Docker:

```bash
cp .env.docker .env
```

### Para Instalación Manual

**⚠️ Importante**: Copia el archivo `.env.example` a `.env` y modifica los valores según tu entorno.

```bash
cp .env.example .env
```

### Variables de Entorno Disponibles

**Configuración básica:**

```ini
# URL de Ollama (para Docker usa host.docker.internal)
OLLAMA_BASE_URL=http://localhost:11434

# Modelo por defecto
DEFAULT_MODEL=llama3.2:3b
DEFAULT_TEMPERATURE=0.5
DEFAULT_TIMEOUT=60

# Seguridad (IMPORTANTE para producción)
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173  # Para desarrollo manual
# CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000  # Para Docker
```

**Variables opcionales:**

```ini
# Configuración del servidor
GUNICORN_PORT=8000
GUNICORN_WORKERS=4

# Frontend (solo para Docker)
VITE_OLLAMA_SERVER_BASE_URL=http://localhost:8000

# Para desarrollo manual
PYTHON_VENV=.pyenv
```

**⚠️ Seguridad**: 
- **Nunca** uses `*` en `ALLOWED_HOSTS` o `CORS_ORIGINS` en producción
- **Nunca** commitees el archivo `.env` al repositorio
- Lee las [Pautas de Seguridad](SECURITY.md) antes del despliegue

## Uso

### Con Docker

```bash
# Iniciar (primera vez)
docker compose up -d

# Ver logs
docker compose logs -f

# Detener
docker compose down
```

Accede a:
- **Frontend**: http://localhost:3000
- **API Backend**: http://localhost:8000

### Instalación Manual

1. Inicia el servidor backend:
    ```bash
    uvicorn backend.main:app --reload
    ```

2. Inicia el servidor frontend (en otra terminal):
    ```bash
    cd frontend/vue-app
    npm run dev
    ```

Accede a:
- **Frontend**: http://localhost:5173
- **API Backend**: http://localhost:8000

### Producción (Instalación Manual)

Para producción con Gunicorn:
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.main:app --bind 0.0.0.0:8000
```

O simplemente ejecuta el script de inicio:
```bash
./start.sh
```

## Arquitectura de los Contenedores

### Backend (FastAPI)
- **Base**: `python:3.12-slim`
- **Puerto**: 8000
- **Características**: 
  - Optimizado para producción con Gunicorn
  - Usuario no-root por seguridad
  - Health checks incluidos
  - Variables de entorno configurables

### Frontend (Vue.js + Nginx)
- **Build**: `node:20-alpine` (para construcción)
- **Runtime**: `nginx:alpine` (para servir archivos)
- **Puerto**: 80 (mapeado a 3000 en host)
- **Características**:
  - Build multistage para imágenes ligeras
  - Configuración Nginx optimizada
  - Proxy automático de API al backend
  - Compresión gzip habilitada
  - Headers de seguridad

### Networking
- Red interna: `ollama-network`
- Frontend se comunica con backend via proxy interno
- Backend accede a Ollama en el host via `host.docker.internal`

## Personalización Docker

### Variables de Entorno Docker

```env
# Configuración de Ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434
DEFAULT_MODEL=llama3.2:3b

# Seguridad
ALLOWED_HOSTS=localhost,127.0.0.1,frontend
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Performance
GUNICORN_WORKERS=4
```

### Docker Compose para Producción

```bash
# Usar configuración optimizada para producción
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

La configuración de producción incluye:
- Límites de recursos (CPU/memoria)
- Modo read-only para mayor seguridad
- Usuarios no-root
- Reinicio automático
- Optimizaciones de seguridad adicionales

## Solución de Problemas

### Docker

1. **Error de conexión a Ollama:**
   ```bash
   # Verifica que Ollama esté ejecutándose
   ollama serve
   
   # Verifica la conectividad desde el contenedor
   docker compose exec backend curl -f http://host.docker.internal:11434/api/tags
   ```

2. **Frontend no puede acceder al backend:**
   - Verifica que ambos contenedores estén en la misma red
   - Revisa la configuración del proxy en `nginx.conf`

3. **Problemas de permisos:**
   ```bash
   # Reconstruir con permisos correctos
   docker compose build --no-cache
   ```

### General

- Asegúrate de que Ollama esté ejecutándose: `ollama serve`
- Verifica que el modelo esté disponible: `ollama pull llama3.2:3b`  
- Revisa los logs para errores: `docker compose logs -f` (Docker) o revisa la consola (manual)
- Verifica las variables de entorno en el archivo `.env`

## Contribuciones

¡Contribuciones son bienvenidas! Abre un issue o envía un pull request.

## Licencia

Este proyecto está licenciado bajo la Licencia MIT.
