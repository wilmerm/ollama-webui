# Ollama WebUI

Ollama WebUI is a minimalist, easy-to-use web interface built with **FastAPI** and **Vue.js**, designed to interact with local AI models via [Ollama](https://ollama.com/).

<img width="1234" height="876" alt="image" src="https://github.com/user-attachments/assets/0dd4c163-446e-457f-92da-deb7805cf6d0" />

## Features
- Simple, responsive web interface.
- FastAPI backend + Vue.js frontend.
- Seamless integration with local Ollama models.
- Docker support for quick deployment.

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/wilmerm/ollama-webui.git
cd ollama-webui
````

### 2. Backend setup

```bash
pip install -r requirements.txt
```

### 3. Frontend setup

```bash
cd frontend/vue-app
npm install
npm run build
```

### 4. Start the application

```bash
./start.sh
```

## Running with Docker

```bash
docker compose build
docker compose up -d
```

## Environment Variables (`.env`)

```env
# Required:
DEFAULT_MODEL=llama3.1:latest     # See more models: https://ollama.com/library/
OLLAMA_BASE_URL=http://127.0.0.1:11434

# Optional:
DEFAULT_TIMEOUT=30                # Increase if model is heavy or system resources are limited.
DEFAULT_TEMPERATURE=0.5           # Controls creativity of AI responses.
GUNICORN_WORKERS=1                # Number of Gunicorn workers.
VITE_SERVER_BASE_URL=http://127.0.0.1:7000  # Only set if backend runs on a different URL/port.
```

## Ollama Configuration

To allow the backend inside Docker to connect to Ollama, edit the Ollama systemd service file and add:

```ini
[Service]
Environment="OLLAMA_HOST=0.0.0.0"
```

## Installing Ollama

Download from the official website:
➡️ [https://ollama.com/download](https://ollama.com/download)

Or install via shell:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

## Useful Ollama Commands

**Download a model:**

```bash
ollama pull llama3.1:latest
```

**Run a model:**

```bash
ollama run llama3.1:latest
```

> **Note:** You don’t need to run the model manually when using Ollama WebUI. The app will automatically start the model specified in `.env` if it’s not already running.

---

## Contributing

Contributions are welcome!

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -m 'Add feature'`).
4. Push to your fork (`git push origin feature/your-feature`).
5. Open a Pull Request.

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

## Credits

<table>
    <tr>
        <td align="center">
            <a href="https://github.com/wilmerm">
                <img src="https://github.com/wilmerm.png" width="100px;" alt="Wilmer Martinez"/><br />
                <sub><b>Wilmer Martinez</b></sub>
            </a>
            <br/>Author & Maintainer
        </td>
    </tr>
</table>
