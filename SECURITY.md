# Security Guidelines

## Overview

This document outlines security best practices and configurations for the Ollama WebUI application.

## Environment Configuration

### Required Environment Variables

Create a `.env` file in the root directory with the following secure configurations:

```ini
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434

# Model Configuration
DEFAULT_MODEL=llama3.2:3b
DEFAULT_TEMPERATURE=0.5
DEFAULT_TIMEOUT=30

# Application Security
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Server Configuration
GUNICORN_PORT=8000
GUNICORN_WORKERS=1

# Frontend Configuration
VITE_OLLAMA_SERVER_BASE_URL=http://localhost
```

### Security Best Practices

1. **Never commit .env files to version control**
2. **Use specific hostnames instead of wildcards (*)**
3. **Set DEBUG=False in production**
4. **Limit CORS origins to trusted domains only**
5. **Use HTTPS in production**
6. **Regularly update dependencies**

### Production Considerations

- Use environment-specific configuration files
- Implement proper authentication if exposing to public networks
- Use reverse proxy (nginx) with proper security headers
- Enable rate limiting to prevent abuse
- Monitor and log security events
- Use HTTPS with proper SSL certificates

## Common Security Issues to Avoid

1. **CORS Misconfiguration**: Never use `allow_origins=["*"]` in production
2. **Debug Mode**: Ensure DEBUG is False in production
3. **Error Disclosure**: Avoid exposing detailed system information in error messages
4. **Input Validation**: Always validate and sanitize user inputs
5. **Dependency Vulnerabilities**: Regularly update dependencies

## Reporting Security Issues

If you discover a security vulnerability, please report it privately by:
1. Creating a private GitHub security advisory
2. Contacting the maintainers directly

Do not create public issues for security vulnerabilities.