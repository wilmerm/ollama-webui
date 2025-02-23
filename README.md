# Ollama WebUI

Ollama WebUI es una interfaz gráfica web minimalista y fácil de usar, construida con FastAPI y Vue.js, que te permite chatear rápida y fácilmente con modelos de IA locales a través de Ollama.

## Características

- Interfaz de usuario intuitiva y amigable
- Integración con FastAPI para una rápida implementación del backend
- Uso de Vue.js para la creación de una interfaz interactiva
- Soporte para múltiples modelos de IA locales

## Instalación

Para instalar y ejecutar el proyecto, sigue estos pasos:

1. Clona el repositorio:
   ```sh
   git clone https://github.com/wilmerm/ollama-webui.git
   cd ollama-webui
   ```

2. Instala las dependencias del backend:
   ```sh
   pip install -r requirements.txt
   ```

3. Instala las dependencias del frontend:
   ```sh
   cd frontend/vue-app
   npm install
   ```

## Uso

Para iniciar el servidor de desarrollo y la aplicación web, ejecuta:

1. Inicia el servidor backend:
   ```sh
   uvicorn main:app --reload
   ```

2. Inicia el servidor frontend:
   ```sh
   cd frontend/vue-app
   npm run dev
   ```

## Contribuciones

¡Las contribuciones son bienvenidas! Por favor, abre un issue o envía un pull request.

## Licencia

Este proyecto está licenciado bajo la Licencia MIT.
