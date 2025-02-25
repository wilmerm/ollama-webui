#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "Running from $DIR"
cd "$DIR"

source .env

PYTHON_VENV=${PYTHON_VENV:-.pyenv}
PORT=${GUNICORN_PORT:-8000}
WORKERS=${GUNICORN_WORKERS:-1}

echo "Activating virtual environment at $PYTHON_VENV"
source ${PYTHON_VENV}/bin/activate

echo "Starting gunicorn with $WORKERS workers on port $PORT"
gunicorn -w $WORKERS -k uvicorn.workers.UvicornWorker backend.main:app --bind 0.0.0.0:$PORT