# Ollama WebUI

Ollama WebUI es una interfaz gráfica web minimalista y fácil de usar, desarrollada con FastAPI y Vue.js, que permite interactuar con modelos de IA locales a través de Ollama.

![image](https://github.com/user-attachments/assets/fbce0ca0-e4a6-4f93-a102-079d05ae3c25)


## Características

- Interfaz intuitiva y amigable
- Backend rápido con FastAPI
- Interfaz interactiva creada con Vue.js
- Soporte para múltiples modelos de IA locales

## Instalación

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

## Configuración (.env)

**⚠️ Importante**: Copia el archivo `.env.example` a `.env` y modifica los valores según tu entorno.

```bash
cp .env.example .env
```

Configura las siguientes variables en tu archivo `.env`:

```ini
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_MODEL=llama3.2:3b

# Configuración de seguridad (IMPORTANTE para producción)
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Variables opcionales:

```ini
DEFAULT_TIMEOUT=30
DEFAULT_TEMPERATURE=0.5

GUNICORN_PORT=8000
GUNICORN_WORKERS=1

VITE_OLLAMA_SERVER_BASE_URL=http://localhost
```

**⚠️ Seguridad**: 
- **Nunca** uses `*` en `ALLOWED_HOSTS` o `CORS_ORIGINS` en producción
- **Nunca** commitees el archivo `.env` al repositorio
- Lee las [Pautas de Seguridad](SECURITY.md) antes del despliegue

## Uso

1. Inicia el servidor backend:
    ```bash
    uvicorn backend.main:app --reload
    ```

2. Inicia el servidor frontend:
    ```bash
    cd frontend/vue-app
    npm run dev
    ```

Para producción con Gunicorn:
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.main:app --bind 0.0.0.0:8000
```

o simplemente ejecuta el archivo **start.sh**:

```bash
./start.sh
```

## Contribuciones

¡Contribuciones son bienvenidas! Abre un issue o envía un pull request.

## Licencia

Este proyecto está licenciado bajo la Licencia MIT.
