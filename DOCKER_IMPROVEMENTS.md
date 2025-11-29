# Docker Configuration Improvements

This document outlines the improvements made to the Docker and Docker Compose configurations.

## Changes Made

### 1. Docker Compose (`infra/docker-compose.yml`)

#### Security Improvements
- ✅ **Environment Variables**: Moved hardcoded credentials to environment variables with defaults
  - `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
  - `MONGO_USER`, `MONGO_PASSWORD`
- ✅ **Port Binding**: Changed from `0.0.0.0` to `127.0.0.1` to prevent external access
  - `127.0.0.1:5432:5432` (postgres)
  - `127.0.0.1:27017:27017` (mongo)
  - `127.0.0.1:6379:6379` (redis)
  - `127.0.0.1:8000:8000` (api)
  - `127.0.0.1:3000:3000` (web)

#### Reliability Improvements
- ✅ **Health Checks**: Added health checks for all database services
  - MongoDB: `mongosh --eval "db.adminCommand('ping')"`
  - Redis: `redis-cli ping`
  - Postgres: Already had health check, added timeout
- ✅ **Smart Dependencies**: Updated `depends_on` to wait for health checks
  ```yaml
  depends_on:
    postgres:
      condition: service_healthy
  ```

#### Development Experience
- ✅ **Volume Mounts**: Added volume mounts for hot-reloading
  - API: `../apps/api:/app`
  - NLP: `../apps/nlp_service:/app`
  - Web: `../apps/web:/app` (with node_modules exclusion)
- ✅ **Command Simplification**: Removed unnecessary `bash -lc` wrappers

### 2. API Dockerfile (`apps/api/Dockerfile`)

- ✅ **Python Version**: Updated from `3.11` to `3.12` to match project settings
- ✅ **Security**: Added non-root user (`appuser` with UID 1000)
- ✅ **Layer Caching**: Copy dependency files before application code
- ✅ **Build Optimization**: Use `--no-cache-dir` for pip install
- ✅ **Dependency Lock**: Use `--frozen` flag with uv sync

### 3. NLP Service Dockerfile (`apps/nlp_service/Dockerfile`)

- ✅ **Python Version**: Updated from `3.11` to `3.12`
- ✅ **Security**: Added non-root user (`appuser` with UID 1000)
- ✅ **Layer Caching**: Copy dependency files before application code
- ✅ **Build Optimization**: Use `--no-cache-dir` for pip install
- ✅ **Dependency Lock**: Use `--frozen` flag with uv sync

### 4. Web Dockerfile (`apps/web/Dockerfile`)

- ✅ **Layer Caching**: Copy package files before application code
- ✅ **Dependency Lock**: Use `--frozen-lockfile` with pnpm
- ✅ **Workspace Support**: Added `pnpm-workspace.yaml` to COPY

### 5. Web Production Dockerfile (`apps/web/Dockerfile.prod`)

- ✅ **Multi-stage Build**: Separate stages for deps, builder, and runner
- ✅ **Security**: Non-root user (`nextjs` with UID 1001)
- ✅ **Optimization**: Only copy necessary files to final image
- ✅ **Production Ready**: Uses `pnpm start` instead of `pnpm dev`

### 6. Additional Files

- ✅ **`.dockerignore`**: Created to exclude unnecessary files from Docker context
- ✅ **`.env.example`**: Updated with database credential variables

## How to Use

### Development

```bash
# Make sure you have a .env file (copy from .env.example)
cp .env.example .env

# Start all services
cd infra
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after changes
docker-compose up -d --build
```

### Production (Web)

```bash
# Build production image
docker build -f apps/web/Dockerfile.prod -t clarity-web:prod apps/web

# Run production container
docker run -p 3000:3000 --env-file .env clarity-web:prod
```

## Security Checklist for Production

Before deploying to production, ensure:

- [ ] Change all default passwords in `.env`
- [ ] Use secrets management (e.g., Docker Secrets, HashiCorp Vault)
- [ ] Use a reverse proxy (e.g., Nginx, Traefik) with SSL/TLS
- [ ] Set `APP_ENV=production` in `.env`
- [ ] Review and restrict network access
- [ ] Enable Docker security scanning
- [ ] Set up monitoring and logging
- [ ] Configure resource limits (CPU, memory)
- [ ] Use production Dockerfile for web service
- [ ] Enable HTTPS only
- [ ] Set proper CORS policies

## Performance Tips

1. **Build Cache**: Use BuildKit for better caching
   ```bash
   DOCKER_BUILDKIT=1 docker-compose build
   ```

2. **Prune Regularly**: Clean up unused Docker resources
   ```bash
   docker system prune -a
   ```

3. **Resource Limits**: Add resource limits in docker-compose.yml
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '1'
         memory: 512M
   ```

## Troubleshooting

### Health Check Failing

If a service fails health checks:
```bash
# Check service logs
docker-compose logs <service-name>

# Inspect health status
docker inspect <container-id> | grep -A 10 Health
```

### Volume Mount Issues

If hot-reload isn't working:
```bash
# Ensure volumes are properly mounted
docker-compose ps
docker inspect <container-id> | grep -A 20 Mounts
```

### Permission Issues

If you get permission errors with non-root user:
```bash
# Fix ownership on host
sudo chown -R 1000:1000 apps/api
```

## Next Steps

Consider implementing:
- Docker Compose override files for different environments
- Container orchestration (Kubernetes, Docker Swarm)
- CI/CD pipeline integration
- Automated security scanning
- Database backup strategies
- Log aggregation (ELK stack, Grafana Loki)
- Monitoring (Prometheus, Grafana)
