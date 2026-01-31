# Docker Deployment Guide for pyWATS

This guide covers deploying pyWATS using Docker for various use cases.

## Table of Contents

- [Quick Start](#quick-start)
- [Available Images](#available-images)
- [Production Deployment](#production-deployment)
- [Development Setup](#development-setup)
- [Configuration](#configuration)
- [Monitoring & Troubleshooting](#monitoring--troubleshooting)
- [Advanced Usage](#advanced-usage)

---

## Quick Start

### 1. Prerequisites

- Docker 20.10+ and Docker Compose 2.0+
- WATS server credentials

### 2. Initial Setup

```bash
# Clone the repository
git clone https://github.com/olreppe/pyWATS.git
cd pyWATS

# Create environment file
cp .env.example .env

# Edit .env and add your WATS credentials
nano .env
```

### 3. Create Required Directories

```bash
mkdir -p watch output archive config
```

### 4. Create Client Configuration

Create `config/client_config.json`:

```json
{
  "wats": {
    "base_url": "https://wats.yourcompany.com",
    "token": "your_base64_token"
  },
  "converters": {
    "enabled": ["csv", "json", "xml"],
    "watch_directory": "/app/watch",
    "output_directory": "/app/output",
    "archive_directory": "/app/archive"
  },
  "logging": {
    "level": "INFO",
    "file": "/app/logs/pywats_client.log"
  }
}
```

### 5. Start the Client

```bash
# Start headless client
docker-compose up -d client

# View logs
docker-compose logs -f client

# Check status
docker-compose ps
```

---

## Available Images

The Dockerfile provides multiple build targets:

### 1. API Only (`api`)

Minimal image with just the pyWATS API library.

```bash
# Build
docker build --target api -t pywats-api .

# Run Python with pyWATS
docker run -it pywats-api python
```

**Use Cases:**
- Python scripts that use pyWATS API
- Custom applications
- Lambda/serverless functions

### 2. Headless Client (`client-headless`)

Client without GUI for servers and embedded systems.

```bash
# Build
docker build --target client-headless -t pywats-client .

# Run with config
docker run -d \
  -v $(pwd)/config:/app/config:ro \
  -v $(pwd)/watch:/app/watch \
  -v $(pwd)/output:/app/output \
  -e WATS_BASE_URL=https://wats.example.com \
  -e WATS_TOKEN=your_token \
  pywats-client
```

**Use Cases:**
- Production test data ingestion
- Automated test report uploads
- Headless test stations
- Raspberry Pi deployments

### 3. Development (`dev`)

Full development environment with all dependencies.

```bash
# Start dev container
docker-compose --profile dev up -d dev

# Attach to container
docker-compose exec dev bash

# Run tests
docker-compose exec dev pytest

# Build docs
docker-compose exec dev sphinx-build docs/api docs/_build/html
```

---

## Production Deployment

### Docker Compose (Recommended)

```bash
# 1. Configure environment
cp .env.example .env
nano .env

# 2. Create config
mkdir -p config watch output archive
nano config/client_config.json

# 3. Start services
docker-compose up -d client

# 4. Verify
docker-compose logs client
docker-compose ps
```

### Kubernetes

Example deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pywats-client
spec:
  replicas: 1
  selector:
    matchLabels:
      app: pywats-client
  template:
    metadata:
      labels:
        app: pywats-client
    spec:
      containers:
      - name: client
        image: pywats-client:latest
        env:
        - name: WATS_BASE_URL
          valueFrom:
            secretKeyRef:
              name: pywats-secrets
              key: base-url
        - name: WATS_TOKEN
          valueFrom:
            secretKeyRef:
              name: pywats-secrets
              key: token
        volumeMounts:
        - name: config
          mountPath: /app/config
          readOnly: true
        - name: watch
          mountPath: /app/watch
        - name: output
          mountPath: /app/output
        - name: logs
          mountPath: /app/logs
        resources:
          requests:
            memory: "256Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "2"
      volumes:
      - name: config
        configMap:
          name: pywats-config
      - name: watch
        persistentVolumeClaim:
          claimName: pywats-watch
      - name: output
        persistentVolumeClaim:
          claimName: pywats-output
      - name: logs
        persistentVolumeClaim:
          claimName: pywats-logs
```

### Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml pywats

# Scale service
docker service scale pywats_client=3

# View logs
docker service logs -f pywats_client
```

---

## Configuration

### Environment Variables

#### Required

- `WATS_BASE_URL` - WATS server URL
- `WATS_TOKEN` - Base64-encoded credentials

#### Optional

- `PYWATS_LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `PYWATS_HEADLESS` - Run in headless mode (default: 1 in Docker)
- `PYWATS_CONFIG_DIR` - Configuration directory (default: /app/config)
- `PYWATS_DATA_DIR` - Data directory (default: /app/data)
- `PYWATS_LOG_DIR` - Log directory (default: /app/logs)

### Volume Mounts

| Mount Point | Purpose | Recommended |
|------------|---------|-------------|
| `/app/config` | Configuration files | Read-only in production |
| `/app/watch` | Incoming test data | Writable |
| `/app/output` | Converted reports | Writable |
| `/app/archive` | Processed files | Writable |
| `/app/logs` | Application logs | Persistent volume |
| `/app/data` | State/queue data | Persistent volume |

### Health Checks

All images include health checks:

```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' pywats-client

# View health check logs
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' pywats-client
```

---

## Monitoring & Troubleshooting

### View Logs

```bash
# Real-time logs
docker-compose logs -f client

# Last 100 lines
docker-compose logs --tail=100 client

# Specific time range
docker-compose logs --since 2024-01-01T00:00:00 client
```

### Check Status

```bash
# Container status
docker-compose ps

# Resource usage
docker stats pywats-client

# Health status
docker inspect --format='{{.State.Health.Status}}' pywats-client
```

### Common Issues

#### Container exits immediately

```bash
# Check logs
docker-compose logs client

# Common causes:
# 1. Missing WATS_BASE_URL or WATS_TOKEN
# 2. Invalid configuration in config/client_config.json
# 3. Permission issues on mounted directories
```

#### Cannot connect to WATS server

```bash
# Test network connectivity
docker-compose exec client ping wats.yourcompany.com

# Test WATS API
docker-compose exec client python -c "
from pywats import pyWATS
api = pyWATS(base_url='https://wats.example.com', token='...')
print(api.test_connection())
"
```

#### Permission denied errors

```bash
# Fix directory permissions (host)
chmod -R 777 watch output archive logs

# Or run with specific user ID
docker-compose run --user $(id -u):$(id -g) client
```

### Debugging

```bash
# Start interactive shell
docker-compose exec client bash

# Or start new container with shell
docker-compose run --rm client bash

# Run Python interactively
docker-compose exec client python
```

---

## Advanced Usage

### Multi-Stage Builds

Build only what you need:

```bash
# API only (smallest)
docker build --target api -t pywats-api:latest .

# Headless client
docker build --target client-headless -t pywats-client:latest .

# Development (largest)
docker build --target dev -t pywats-dev:latest .
```

### Custom Configuration

Override defaults with `docker-compose.override.yml`:

```yaml
version: '3.8'
services:
  client:
    environment:
      PYWATS_LOG_LEVEL: DEBUG
    volumes:
      - /custom/watch:/app/watch
      - /custom/output:/app/output
```

### Resource Limits

Adjust in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '4'      # Max CPUs
      memory: 2G     # Max memory
    reservations:
      cpus: '1'      # Min CPUs
      memory: 512M   # Min memory
```

### Network Configuration

```bash
# Create custom network
docker network create --driver bridge pywats-net

# Run with custom network
docker run -d --network pywats-net pywats-client
```

### CI/CD Integration

GitHub Actions example:

```yaml
name: Build Docker Image

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build image
        run: docker build --target client-headless -t pywats-client:latest .
      
      - name: Test image
        run: |
          docker run --rm pywats-client python -c "import pywats; print('OK')"
      
      - name: Push to registry
        run: |
          echo "${{ secrets.DOCKER_PASSWORD }}" | docker login -u "${{ secrets.DOCKER_USERNAME }}" --password-stdin
          docker push pywats-client:latest
```

---

## Security Considerations

1. **Never commit `.env` files** - Use secrets management
2. **Use read-only config mounts** - Prevent container from modifying config
3. **Run as non-root** - All images use non-root user (uid 1000)
4. **Scan images** - `docker scan pywats-client`
5. **Use HTTPS** - Always use TLS for WATS connections
6. **Rotate credentials** - Update `WATS_TOKEN` regularly
7. **Network isolation** - Use Docker networks to restrict access

---

## Support

- **Documentation:** https://github.com/olreppe/pyWATS/tree/main/docs
- **Issues:** https://github.com/olreppe/pyWATS/issues
- **Email:** support@virinco.com

---

**Last Updated:** January 23, 2026  
**Version:** 0.1.0b34
