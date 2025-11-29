# Docker Setup - Quick Reference

## ✅ All Services Running Successfully

### Service Status
| Service | Status | Port | Health Check |
|---------|--------|------|--------------|
| postgres | ✅ Running | 127.0.0.1:5432 | Healthy |
| mongo | ✅ Running | 127.0.0.1:27017 | Healthy |
| redis | ✅ Running | 127.0.0.1:6379 | Healthy |
| api | ✅ Running | 127.0.0.1:8000 | - |
| nlp | ✅ Running | - | - |
| web | ✅ Running | 127.0.0.1:3000 | - |

## Quick Commands

### Start Services
```bash
cd infra
docker-compose up -d
```

### Stop Services
```bash
cd infra
docker-compose down
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f nlp
docker-compose logs -f web
```

### Check Status
```bash
docker-compose ps
```

### Rebuild After Code Changes
```bash
docker-compose up -d --build
```

### Restart a Specific Service
```bash
docker-compose restart api
```

## Access Points

- **Web Frontend**: http://localhost:3000
- **API Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **MongoDB**: localhost:27017
- **Redis**: localhost:6379

## Environment Configuration

The services use two sets of connection strings:

### For Host Machine (in .env)
```env
POSTGRES_URL=postgresql://clarity:clarity@localhost:5432/clarity
MONGO_URL=mongodb://clarity:clarity@localhost:27017/?authSource=admin
REDIS_URL=redis://localhost:6379/0
```

### For Docker Containers (overridden in docker-compose.yml)
```yaml
POSTGRES_URL: postgresql://clarity:clarity@postgres:5432/clarity
MONGO_URL: mongodb://clarity:clarity@mongo:27017/?authSource=admin
REDIS_URL: redis://redis:6379/0
```

This allows you to:
- Run services in Docker and access databases from your host
- Have containers communicate with each other using service names

## Troubleshooting

### Service Won't Start
```bash
# Check logs
docker-compose logs <service-name>

# Rebuild specific service
docker-compose up -d --build <service-name>
```

### Clear Everything and Start Fresh
```bash
docker-compose down -v  # -v removes volumes (WARNING: deletes data!)
docker-compose up -d --build
```

### Permission Issues
```bash
# If you get permission errors with volumes
sudo chown -R $USER:$USER apps/
```

### Check Container Health
```bash
docker ps
docker inspect <container-id> | grep -A 10 Health
```

## Key Improvements Made

1. **Security**
   - Non-root users in containers
   - Localhost-only port bindings
   - Environment variables for credentials

2. **Reliability**
   - Health checks for all databases
   - Smart dependency waiting
   - Proper service networking

3. **Development Experience**
   - Hot-reload with volume mounts
   - Optimized Docker layer caching
   - Clear logging and error messages

4. **Performance**
   - Multi-stage builds for production
   - Efficient dependency installation
   - Minimal image sizes

## Notes

- The NLP service runs an RQ worker that processes background jobs
- The API service auto-reloads on code changes
- The web service uses Next.js with Turbopack for fast development
- All ports are bound to 127.0.0.1 for security (not accessible externally)
