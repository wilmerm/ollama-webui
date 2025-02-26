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

Configura las siguientes variables en tu archivo `.env`:

```ini
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_MODEL=llama3.2:3b
```

Variables opcionales:

```ini
DEBUG=True
ALLOWED_HOSTS=*

DEFAULT_TIMEOUT=30
DEFAULT_TEMPERATURE=0.5

GUNICORN_PORT=8000
GUNICORN_WORKERS=1
```

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
