# Docker Deployment Guide

This guide covers how to build and deploy the ecommerce frontend application using Docker.

## Prerequisites

- Docker 20.10+ installed
- Docker Compose 2.0+ (for multi-service setup)
- At least 2GB of available memory
- Node.js 18+ (for local development)

## Dockerfile Overview

The Dockerfile uses a **multi-stage build** approach for optimal image size and security:

### Build Stage
- Uses `node:18-alpine` as the base image
- Installs dependencies with `npm ci` for reproducible builds
- Builds the React application
- Produces optimized production assets

### Production Stage
- Uses `nginx:alpine` for serving static files
- Includes custom nginx configuration with:
  - Gzip compression
  - Security headers
  - React Router support (SPA routing)
  - API proxy to backend
  - Static asset caching
- Runs as non-root user for security
- Includes health checks
- Uses dumb-init for proper signal handling

## Build Arguments

The Dockerfile accepts the following build arguments:

| Argument | Description | Default |
|----------|-------------|---------|
| `REACT_APP_API_URL` | Backend API URL | - |
| `REACT_APP_ENV` | Environment (development/production) | `production` |

## Quick Start

### 1. Build the Docker Image

```bash
# Basic build
docker build -t ecommerce-frontend:latest .

# Build with environment variables
docker build \
  --build-arg REACT_APP_API_URL=https://api.example.com \
  --build-arg REACT_APP_ENV=production \
  -t ecommerce-frontend:latest .

# Or use Makefile
make docker-build
```

### 2. Run the Container

```bash
# Run with default settings
docker run -d -p 80:80 --name ecommerce-frontend ecommerce-frontend:latest

# Or use Makefile
make docker-run
```

### 3. Verify the Deployment

```bash
# Check container status
docker ps

# View logs
docker logs -f ecommerce-frontend

# Test health endpoint
curl http://localhost/

# Or use Makefile
make docker-logs
```

## Using Docker Compose

Docker Compose orchestrates multiple services (frontend, backend, database, redis).

### 1. Set Environment Variables

Create a `.env` file in the project root:

```bash
# Copy from example
cp .env.example .env

# Edit the values
nano .env
```

### 2. Start All Services

```bash
# Start services in detached mode
docker-compose up -d

# Or use Makefile
make compose-up
```

### 3. View Logs

```bash
# All services
docker-compose logs -f

# Frontend only
docker-compose logs -f frontend

# Or use Makefile
make compose-logs
make logs-frontend
```

### 4. Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Or use Makefile
make compose-down
```

## Production Deployment

### Building for Production

```bash
# Set production environment variables
export REACT_APP_API_URL=https://api.production.com
export REACT_APP_ENV=production

# Build the image
docker build \
  --build-arg REACT_APP_API_URL=${REACT_APP_API_URL} \
  --build-arg REACT_APP_ENV=${REACT_APP_ENV} \
  -t ecommerce-frontend:v1.0.0 \
  -t ecommerce-frontend:latest .
```

### Tagging and Pushing to Registry

```bash
# Tag for your registry
docker tag ecommerce-frontend:latest your-registry.com/ecommerce-frontend:latest

# Login to registry
docker login your-registry.com

# Push the image
docker push your-registry.com/ecommerce-frontend:latest
```

### AWS ECR Example

```bash
# Set AWS variables
export AWS_REGION=us-east-1
export ECR_REGISTRY=123456789.dkr.ecr.us-east-1.amazonaws.com

# Login to ECR
aws ecr get-login-password --region ${AWS_REGION} | \
  docker login --username AWS --password-stdin ${ECR_REGISTRY}

# Build and tag
docker build -t ${ECR_REGISTRY}/ecommerce-frontend:latest .

# Push to ECR
docker push ${ECR_REGISTRY}/ecommerce-frontend:latest

# Or use Makefile
make aws-push
```

## Image Optimization

The Dockerfile is optimized for:

1. **Layer Caching**: Package files are copied before source code
2. **Size Reduction**: Multi-stage build discards build dependencies
3. **Security**: Runs as non-root user, minimal base image
4. **Performance**: nginx with gzip compression and caching headers

### Image Size

- Build stage: ~500MB (temporary)
- Final image: ~25-30MB (nginx + static files)

## Security Features

### Non-Root User
The container runs as the `nginx` user (UID 101) instead of root.

### Security Headers
nginx is configured with:
- `X-Frame-Options: SAMEORIGIN`
- `X-Content-Type-Options: nosniff`
- `X-XSS-Protection: 1; mode=block`

### Health Checks
Built-in health check monitors container health:
```bash
# Check health status
docker inspect --format='{{.State.Health.Status}}' ecommerce-frontend
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs ecommerce-frontend

# Check nginx configuration
docker exec ecommerce-frontend nginx -t

# Verify file permissions
docker exec ecommerce-frontend ls -la /usr/share/nginx/html
```

### Build Failures

```bash
# Clear Docker cache and rebuild
docker build --no-cache -t ecommerce-frontend:latest .

# Or use Makefile
make docker-build-no-cache
```

### Memory Issues

```bash
# Check container resource usage
docker stats ecommerce-frontend

# Increase Docker memory limit in Docker Desktop settings
# Minimum recommended: 2GB
```

### Network Issues

```bash
# Test connectivity between containers
docker network inspect ecommerce-network

# Check if backend is reachable
docker exec ecommerce-frontend wget -O- http://backend:8000/api/health/
```

### Permission Errors

If you encounter permission errors:

```bash
# Rebuild with root user (not recommended for production)
docker run -u root -p 80:80 ecommerce-frontend:latest
```

## Development vs Production

### Development
```bash
# Use docker-compose with hot reload
docker-compose -f docker-compose.dev.yml up

# Or run locally
npm start
```

### Production
```bash
# Use optimized production build
docker-compose up -d
```

## Environment Variables

### Build-time Variables (ARG)
- Set with `--build-arg` during build
- Baked into the image at build time
- Cannot be changed after build

### Runtime Variables (ENV)
- Set with `-e` or `--env-file` during run
- Can be changed when container starts
- Not applicable for React apps (vars are embedded at build time)

**Note**: React apps embed environment variables at build time, so you must rebuild the image to change them.

## Maintenance

### Cleaning Up

```bash
# Stop and remove container
docker stop ecommerce-frontend
docker rm ecommerce-frontend

# Remove image
docker rmi ecommerce-frontend:latest

# Clean up everything
docker system prune -af
docker volume prune -f

# Or use Makefile
make docker-clean
make clean-all
```

### Updating the Application

```bash
# Pull latest code
git pull

# Rebuild image
docker-compose build --no-cache

# Restart services
docker-compose up -d

# Or use Makefile
make compose-build
make compose-restart
```

## Monitoring

### Container Logs

```bash
# Follow logs
docker logs -f ecommerce-frontend

# Last 100 lines
docker logs --tail 100 ecommerce-frontend

# Since specific time
docker logs --since 30m ecommerce-frontend
```

### Resource Usage

```bash
# Real-time stats
docker stats ecommerce-frontend

# Detailed inspect
docker inspect ecommerce-frontend
```

### Health Status

```bash
# Check health
docker inspect --format='{{json .State.Health}}' ecommerce-frontend | jq
```

## Best Practices

1. **Version Tags**: Always tag images with version numbers
2. **Environment Variables**: Use `.env` files, never commit secrets
3. **Multi-Stage Builds**: Keep using them for optimal size
4. **Health Checks**: Monitor container health
5. **Non-Root User**: Never run as root in production
6. **Resource Limits**: Set memory and CPU limits in production
7. **Logging**: Use centralized logging solutions
8. **Backups**: Regular backups of volumes and databases

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [nginx Configuration Guide](https://nginx.org/en/docs/)
- [React Production Build Guide](https://create-react-app.dev/docs/production-build/)
