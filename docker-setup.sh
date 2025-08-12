#!/bin/bash
# Docker Installation Script for Ollama WebUI
# This script sets up and runs Ollama WebUI using Docker

set -e

echo "🐳 Ollama WebUI - Docker Setup"
echo "================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed."
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is available
if ! docker compose version &> /dev/null; then
    echo "❌ Error: Docker Compose is not available."
    echo "Please ensure Docker Compose is installed."
    exit 1
fi

echo "✅ Docker and Docker Compose are available."

# Check if Ollama is running
echo ""
echo "🔍 Checking Ollama service..."
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "✅ Ollama is running on localhost:11434"
else
    echo "⚠️  Warning: Ollama doesn't seem to be running on localhost:11434"
    echo "   Make sure Ollama is installed and running:"
    echo "   - Install: https://ollama.ai/"
    echo "   - Start: ollama serve"
    echo ""
    read -p "Do you want to continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 1
    fi
fi

# Setup environment file
echo ""
echo "🔧 Setting up environment configuration..."
if [ ! -f .env ]; then
    if [ -f .env.docker ]; then
        cp .env.docker .env
        echo "✅ Created .env from .env.docker"
    else
        echo "⚠️  .env.docker not found, using .env.example"
        cp .env.example .env
    fi
else
    echo "✅ .env file already exists"
fi

# Ask for model preference
echo ""
echo "🤖 Model Configuration"
read -p "Enter the model you want to use (default: llama3.2:3b): " model
if [ ! -z "$model" ]; then
    # Update the model in .env file
    if grep -q "DEFAULT_MODEL=" .env; then
        sed -i.bak "s/DEFAULT_MODEL=.*/DEFAULT_MODEL=$model/" .env
        echo "✅ Updated DEFAULT_MODEL to $model"
    fi
fi

# Build and start services
echo ""
echo "🏗️  Building and starting Docker containers..."
echo "This may take a few minutes on first run..."

docker compose build
docker compose up -d

# Wait a bit for services to start
sleep 5

# Check service status
echo ""
echo "🏥 Checking service health..."
if docker compose ps | grep -q "healthy\|running"; then
    echo "✅ Services are starting up!"
else
    echo "⚠️  Some services may have issues. Check logs with: docker compose logs"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📍 Access your application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo ""
echo "📚 Useful commands:"
echo "   View logs: docker compose logs -f"
echo "   Stop: docker compose down"
echo "   Restart: docker compose restart"
echo "   Update: docker compose pull && docker compose up -d"
echo ""
echo "🔧 If you need to modify settings, edit the .env file and restart:"
echo "   docker compose restart"