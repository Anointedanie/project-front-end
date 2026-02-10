# Complete Docker Deployment Guide

This guide provides a complete overview of deploying the ecommerce frontend application using Docker.

## Quick Reference

```bash
# Local Development
make dev                    # Start dev server
make docker-build          # Build Docker image
make docker-run            # Run container
make compose-up            # Start all services

# Production
./build-docker.sh --version v1.0.0 --push
docker-compose -f docker-compose.prod.yml up -d

# Cleanup
make docker-stop
make compose-down
```

## File Structure

```
.
├── Dockerfile                  # Multi-stage production build
├── docker-compose.yml         # Development multi-service setup
├── docker-compose.prod.yml    # Production configuration
├── nginx.conf                 # Basic nginx config
├── nginx.prod.conf           # Production nginx with SSL
├── .dockerignore             # Files to exclude from build
├── build-docker.sh           # Production build script
├── .env.docker               # Environment template
├── .github/workflows/        # CI/CD automation
└── DOCKER.md                 # Detailed documentation
```

## Configuration Files Explained

### 1. Dockerfile
**Purpose**: Defines how to build the Docker image

**Features**:
- Multi-stage build (Node build + Nginx serve)
- Build arguments for environment variables
- Non-root user for security
- Health checks
- Optimized layer caching
- Signal handling with dumb-init

**Usage**:
```bash
docker build \
  --build-arg REACT_APP_API_URL=https://api.example.com \
  -t ecommerce-frontend:latest .
```

### 2. nginx.conf
**Purpose**: Basic nginx configuration for development

**Features**:
- React Router support (SPA routing)
- API proxy to backend
- Gzip compression
- Basic security headers
- Static asset caching

**When to use**: Local development and testing

### 3. nginx.prod.conf
**Purpose**: Production-ready nginx configuration

**Features**:
- All features from nginx.conf
- SSL/TLS configuration (commented)
- Enhanced security headers
- CSP headers
- Rate limiting support
- Health check endpoint
- Error pages
- Monitoring endpoint

**When to use**: Production deployments

**To use in production**, update Dockerfile:
```dockerfile
COPY nginx.prod.conf /etc/nginx/conf.d/default.conf
```

### 4. docker-compose.yml
**Purpose**: Multi-service development environment

**Includes**:
- Frontend (React)
- Backend (Django)
- Database (PostgreSQL)
- Cache (Redis)

**Usage**:
```bash
docker-compose up -d
docker-compose logs -f frontend
```

### 5. docker-compose.prod.yml
**Purpose**: Production deployment configuration

**Features**:
- Resource limits (CPU/Memory)
- Production logging
- Health checks
- Restart policies
- Network isolation

**Usage**:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 6. build-docker.sh
**Purpose**: Production build automation script

**Features**:
- Version tagging
- Git metadata
- Build arguments
- Registry push
- Multiple tags (version, branch, latest)
- Colored output

**Usage**:
```bash
# Basic build
./build-docker.sh

# Production build with version
./build-docker.sh --version v1.0.0 --push

# Custom registry
./build-docker.sh --registry myregistry.com --version v1.0.0

# With custom API URL
./build-docker.sh --api-url https://api.prod.com --env production
```

### 7. .dockerignore
**Purpose**: Exclude files from Docker build context

**Excludes**:
- node_modules
- Build artifacts
- Git files
- IDE configurations
- Documentation
- Environment files

**Why it matters**: Reduces build context size and speeds up builds

## Deployment Scenarios

### Scenario 1: Local Development

```bash
# Clone repository
git clone <repository-url>
cd ecommerce-frontend

# Setup environment
cp .env.example .env
nano .env

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f frontend

# Access application
open http://localhost
```

### Scenario 2: Production Single Server

```bash
# Set environment variables
export REACT_APP_API_URL=https://api.production.com
export REACT_APP_ENV=production

# Build image
./build-docker.sh --version v1.0.0 --no-cache

# Run with production compose
docker-compose -f docker-compose.prod.yml up -d

# Verify health
curl http://localhost/health
```

### Scenario 3: Docker Registry Deployment

```bash
# Build and push to private registry
REGISTRY=myregistry.com ./build-docker.sh \
  --version v1.0.0 \
  --api-url https://api.production.com \
  --push

# On production server
docker pull myregistry.com/ecommerce-frontend:v1.0.0
docker run -d -p 80:80 myregistry.com/ecommerce-frontend:v1.0.0
```

### Scenario 4: AWS ECR Deployment

```bash
# Set AWS variables
export AWS_REGION=us-east-1
export ECR_REGISTRY=123456789.dkr.ecr.us-east-1.amazonaws.com

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $ECR_REGISTRY

# Build and push
REGISTRY=$ECR_REGISTRY ./build-docker.sh \
  --version v1.0.0 \
  --api-url https://api.production.com \
  --push

# Deploy (on EC2/ECS)
docker pull $ECR_REGISTRY/ecommerce-frontend:v1.0.0
docker run -d -p 80:80 $ECR_REGISTRY/ecommerce-frontend:v1.0.0
```

### Scenario 5: CI/CD with GitHub Actions

The `.github/workflows/docker-build.yml` file automates:
- Building on push to main
- Tagging with version numbers
- Pushing to GitHub Container Registry
- Vulnerability scanning with Trivy
- Multi-platform builds (amd64, arm64)

**Setup**:
1. Add secrets to GitHub repository:
   - `REACT_APP_API_URL`
2. Push code to trigger build
3. Images available at `ghcr.io/<org>/ecommerce-frontend`

## Environment Variables

### Build-time Variables (ARG in Dockerfile)

| Variable | Description | Default |
|----------|-------------|---------|
| `REACT_APP_API_URL` | Backend API URL | - |
| `REACT_APP_ENV` | Environment name | `production` |

**Set during build**:
```bash
docker build --build-arg REACT_APP_API_URL=https://api.com -t app .
```

### Runtime Variables (ENV in compose)

Set in `.env` file or docker-compose:
```env
REACT_APP_API_URL=http://backend:8000/api
REACT_APP_ENV=production
```

**Note**: React apps embed env vars at build time, so runtime changes require rebuild.

## Production Checklist

Before deploying to production:

- [ ] Update `REACT_APP_API_URL` to production API
- [ ] Set `REACT_APP_ENV=production`
- [ ] Use `nginx.prod.conf` instead of `nginx.conf`
- [ ] Configure SSL certificates (if using HTTPS)
- [ ] Set resource limits in docker-compose
- [ ] Configure log rotation
- [ ] Set up monitoring and alerts
- [ ] Enable health checks
- [ ] Configure backup strategy
- [ ] Set proper CORS headers
- [ ] Review and set CSP headers
- [ ] Use specific version tags (not `latest`)
- [ ] Test rollback procedure
- [ ] Configure firewall rules
- [ ] Set up CDN (optional)
- [ ] Review security headers

## SSL/TLS Setup

### 1. Obtain SSL Certificate

**Option A: Let's Encrypt (Free)**
```bash
# Install certbot
sudo apt-get install certbot

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com
```

**Option B: Self-signed (Development)**
```bash
make ssl-generate
```

### 2. Update Dockerfile

```dockerfile
# Copy SSL certificates
COPY ssl/certificate.crt /etc/ssl/certs/
COPY ssl/private.key /etc/ssl/private/

# Copy production nginx config
COPY nginx.prod.conf /etc/nginx/conf.d/default.conf
```

### 3. Update nginx.prod.conf

Uncomment SSL sections:
```nginx
listen 443 ssl http2;
ssl_certificate /etc/ssl/certs/certificate.crt;
ssl_certificate_key /etc/ssl/private/private.key;
```

### 4. Update docker-compose

```yaml
ports:
  - "80:80"
  - "443:443"
volumes:
  - ./ssl:/etc/ssl:ro
```

## Monitoring and Logging

### View Logs

```bash
# All containers
docker-compose logs -f

# Specific service
docker-compose logs -f frontend

# Last 100 lines
docker-compose logs --tail 100 frontend

# Since 30 minutes ago
docker-compose logs --since 30m frontend
```

### Health Checks

```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' ecommerce-frontend

# Test health endpoint
curl http://localhost/health

# Use Makefile
make health
```

### Resource Monitoring

```bash
# Real-time stats
docker stats ecommerce-frontend

# Container details
docker inspect ecommerce-frontend

# Nginx status (if enabled)
curl http://localhost/nginx_status
```

## Troubleshooting

### Build Issues

```bash
# Clear cache and rebuild
docker build --no-cache -t ecommerce-frontend:latest .

# Check build logs
docker build -t ecommerce-frontend:latest . 2>&1 | tee build.log

# Verify build args
docker history ecommerce-frontend:latest
```

### Runtime Issues

```bash
# Check logs
docker logs -f ecommerce-frontend

# Test nginx config
docker exec ecommerce-frontend nginx -t

# Get shell access
docker exec -it ecommerce-frontend /bin/sh

# Check file permissions
docker exec ecommerce-frontend ls -la /usr/share/nginx/html
```

### Network Issues

```bash
# Test backend connectivity
docker exec ecommerce-frontend wget -O- http://backend:8000/api/health/

# Inspect network
docker network inspect ecommerce-network

# Test DNS resolution
docker exec ecommerce-frontend nslookup backend
```

### Performance Issues

```bash
# Check resource usage
docker stats ecommerce-frontend

# Analyze image layers
docker history ecommerce-frontend:latest

# Check image size
docker images ecommerce-frontend
```

## Maintenance

### Updates

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose build --no-cache
docker-compose up -d

# Or use Makefile
make compose-build
make compose-restart
```

### Backup

```bash
# Backup configuration
tar -czf backup-config.tar.gz .env nginx.conf docker-compose.yml

# Backup volumes (if any)
docker run --rm -v ecommerce-data:/data -v $(pwd):/backup \
  alpine tar -czf /backup/volumes-backup.tar.gz /data
```

### Cleanup

```bash
# Stop and remove containers
docker-compose down

# Remove volumes
docker-compose down -v

# Clean up system
docker system prune -af
docker volume prune -f

# Or use Makefile
make clean-all
```

## Best Practices

1. **Always use specific version tags** in production
2. **Never commit secrets** to version control
3. **Use multi-stage builds** to minimize image size
4. **Run as non-root user** for security
5. **Implement health checks** for reliability
6. **Set resource limits** to prevent resource exhaustion
7. **Use .dockerignore** to speed up builds
8. **Enable logging** with rotation
9. **Monitor container metrics** and logs
10. **Regular security updates** of base images
11. **Test locally** before deploying to production
12. **Document all environment variables**
13. **Use CI/CD** for consistent deployments
14. **Implement proper error handling**
15. **Regular backups** of critical data

## Support

For issues or questions:
- Check [DOCKER.md](./DOCKER.md) for detailed documentation
- Review [DOCKER_TROUBLESHOOTING.md](./DOCKER_TROUBLESHOOTING.md) if it exists
- Check container logs: `docker-compose logs -f`
- Verify configuration: `docker-compose config`
- Test locally first before deploying to production

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [React Deployment Guide](https://create-react-app.dev/docs/deployment/)
- [Docker Security Best Practices](https://docs.docker.com/develop/security-best-practices/)
