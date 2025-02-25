#!/bin/bash

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "Running from $DIR"
cd "$DIR"

if [ -f .env ]; then
    source .env
else
    echo ".env file not found. Exiting."
    exit 1
fi

PYTHON_VENV=${PYTHON_VENV:-.pyenv}
PORT=${APP_PORT:-8000}
WORKERS=${APP_WORKERS:-1}

MODEL=${1:-$DEFAULT_MODEL}
TEMPERATURE=${2:-$DEFAULT_TEMPERATURE}
PORT=${3:-$PORT}
WORKERS=${4:-$WORKERS}

if [ ! -d "$PYTHON_VENV" ]; then
    echo "Python virtual environment not found at $PYTHON_VENV. Exiting."
    exit 1
fi

echo "Activating virtual environment at $PYTHON_VENV"
source ${PYTHON_VENV}/bin/activate

export DEFAULT_MODEL=$MODEL
export DEFAULT_TEMPERATURE=$TEMPERATURE

echo "Starting gunicorn with $WORKERS workers on port $PORT for model $MODEL with temperature $TEMPERATURE"
exec gunicorn -w $WORKERS -k uvicorn.workers.UvicornWorker backend.main:app --bind 0.0.0.0:$PORT --env DEFAULT_MODEL=$MODEL --env DEFAULT_TEMPERATURE=$TEMPERATURE