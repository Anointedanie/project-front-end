# Docker Build Troubleshooting Guide

## Common Docker Build Issues and Solutions

### Issue 1: npm ci --only=production error ✅ FIXED

**Error:**
```
npm error Invalid: lock file's typescript@5.9.3 does not satisfy typescript@4.9.5
npm error code EUSAGE
```

**Cause:** 
- `--only=production` is deprecated npm syntax
- Build stage needs ALL dependencies (including dev dependencies like react-scripts)

**Solution:**
Use `npm ci` without flags in the build stage:
```dockerfile
# Build stage - needs ALL dependencies
RUN npm ci

# NOT: npm ci --only=production
# NOT: npm ci --omit=dev
```

---

### Issue 2: "Cannot find module 'react-scripts'"

**Cause:** Missing dev dependencies needed for build

**Solution:**
```dockerfile
# Install ALL dependencies in build stage
RUN npm ci
```

---

### Issue 3: Docker build is slow

**Solution:** Use .dockerignore file (already included):
```
node_modules
build
.git
```

---

### Issue 4: "EACCES: permission denied"

**Cause:** File permissions in Docker

**Solution:**
```dockerfile
# Add this if needed
RUN chown -R node:node /app
USER node
```

---

### Issue 5: Build works locally but fails in Docker

**Cause:** Different Node versions or missing files

**Solution:**
```bash
# Check Node version
node --version  # Should match Dockerfile (18)

# Ensure package-lock.json exists
ls package-lock.json

# Clean local build
rm -rf node_modules build
npm install
npm run build

# Then try Docker build again
docker build -t ecommerce-frontend .
```

---

## Correct Dockerfile (Final Version)

```dockerfile
# Build stage
FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install ALL dependencies (including dev dependencies for build)
RUN npm ci

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built app from build stage
COPY --from=build /app/build /usr/share/nginx/html

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
```

---

## Step-by-Step Docker Build

### 1. Build the Image
```bash
docker build -t ecommerce-frontend:latest .
```

Expected output:
```
[+] Building 45.2s (14/14) FINISHED
 => [build 1/6] FROM node:18-alpine
 => [build 2/6] WORKDIR /app
 => [build 3/6] COPY package*.json ./
 => [build 4/6] RUN npm ci
 => [build 5/6] COPY . .
 => [build 6/6] RUN npm run build
 => [stage-1 1/3] FROM nginx:alpine
 => [stage-1 2/3] COPY nginx.conf /etc/nginx/conf.d/default.conf
 => [stage-1 3/3] COPY --from=build /app/build /usr/share/nginx/html
 => exporting to image
```

### 2. Verify Image is Created
```bash
docker images | grep ecommerce-frontend
```

Should show:
```
ecommerce-frontend   latest   abc123def456   2 minutes ago   50MB
```

### 3. Run the Container
```bash
docker run -d \
  -p 80:80 \
  --name ecommerce-frontend \
  -e REACT_APP_API_URL=http://your-backend:8000/api \
  ecommerce-frontend:latest
```

### 4. Check Container is Running
```bash
docker ps
```

### 5. View Logs
```bash
docker logs ecommerce-frontend
```

### 6. Test the App
```bash
curl http://localhost
# Should return HTML
```

Or open in browser: `http://localhost`

---

## Docker Build Best Practices

### 1. Clean Build (if issues persist)
```bash
# Remove old images
docker rmi ecommerce-frontend:latest

# Remove build cache
docker builder prune -a

# Rebuild from scratch
docker build --no-cache -t ecommerce-frontend:latest .
```

### 2. Multi-stage Build Benefits
- Smaller final image (~50MB vs ~500MB)
- Faster deployment
- More secure (no build tools in production)

### 3. Check Build Context
```bash
# See what files are being sent to Docker
docker build --progress=plain -t ecommerce-frontend .
```

### 4. Optimize Build Time
```bash
# Use BuildKit for parallel builds
DOCKER_BUILDKIT=1 docker build -t ecommerce-frontend .
```

---

## Docker Compose Build

If using docker-compose:

```bash
# Build
docker-compose build frontend

# Or build and start
docker-compose up -d --build
```

---

## Common Environment Variables

```bash
# Development
docker run -d -p 80:80 \
  -e REACT_APP_API_URL=http://localhost:8000/api \
  -e REACT_APP_ENV=development \
  ecommerce-frontend

# Production
docker run -d -p 80:80 \
  -e REACT_APP_API_URL=https://api.yourdomain.com/api \
  -e REACT_APP_ENV=production \
  ecommerce-frontend
```

---

## Debugging Inside Container

```bash
# Get a shell inside running container
docker exec -it ecommerce-frontend sh

# Check nginx config
docker exec ecommerce-frontend cat /etc/nginx/conf.d/default.conf

# Check files are present
docker exec ecommerce-frontend ls -la /usr/share/nginx/html

# Check nginx logs
docker exec ecommerce-frontend cat /var/log/nginx/access.log
docker exec ecommerce-frontend cat /var/log/nginx/error.log
```

---

## Quick Commands Reference

```bash
# Build
docker build -t ecommerce-frontend .

# Run
docker run -d -p 80:80 --name ecommerce-frontend ecommerce-frontend

# Stop
docker stop ecommerce-frontend

# Remove container
docker rm ecommerce-frontend

# Remove image
docker rmi ecommerce-frontend

# View logs
docker logs -f ecommerce-frontend

# Restart
docker restart ecommerce-frontend

# Check stats
docker stats ecommerce-frontend
```

---

## Still Having Issues?

1. **Check Node version in Dockerfile matches your local version**
2. **Ensure package-lock.json is committed to git**
3. **Delete node_modules and build folders before Docker build**
4. **Try building without Docker first:** `npm run build`
5. **Check Docker daemon is running:** `docker info`

---

## Success Checklist

- [ ] Dockerfile uses `npm ci` (not `npm ci --only=production`)
- [ ] package-lock.json exists and is up to date
- [ ] .dockerignore excludes node_modules and build
- [ ] Docker build completes without errors
- [ ] Image size is reasonable (~50MB for nginx+app)
- [ ] Container starts successfully
- [ ] App accessible at http://localhost
- [ ] Environment variables work correctly

---

**Your Dockerfile is now fixed and ready to use!** 🎉
