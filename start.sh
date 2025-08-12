#!/bin/bash

set -e

PORT=${APP_PORT:-7000}
WORKERS=${APP_WORKERS:-1}
MODEL=${1:-$DEFAULT_MODEL}
TEMPERATURE=${2:-$DEFAULT_TEMPERATURE}
PORT=${3:-$PORT}
WORKERS=${4:-$WORKERS}

export DEFAULT_MODEL=$MODEL
export DEFAULT_TEMPERATURE=$TEMPERATURE

echo "Starting gunicorn with $WORKERS workers on port $PORT for model $MODEL with temperature $TEMPERATURE"
exec gunicorn -w $WORKERS -k uvicorn.workers.UvicornWorker backend.main:app --bind 0.0.0.0:$PORT --env DEFAULT_MODEL=$MODEL --env DEFAULT_TEMPERATURE=$TEMPERATURE