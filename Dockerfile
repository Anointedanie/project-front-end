# Build stage
FROM node:18-alpine AS build

# Set working directory
WORKDIR /app

# Add build arguments for environment variables
ARG REACT_APP_API_URL
ARG REACT_APP_ENV=production

# Set environment variables
ENV NODE_ENV=production
ENV REACT_APP_API_URL=${REACT_APP_API_URL}
ENV REACT_APP_ENV=${REACT_APP_ENV}

# Copy package files for better layer caching
COPY package.json package-lock.json* ./

# Install dependencies with clean install for reproducible builds
# Use npm ci if package-lock.json exists, otherwise npm install
RUN if [ -f package-lock.json ]; then npm ci --only=production=false; else npm install; fi

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Remove development dependencies to reduce size
RUN npm prune --production

# Production stage
FROM nginx:alpine

# Install dumb-init for proper signal handling
RUN apk add --no-cache dumb-init

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built application from build stage
COPY --from=build /app/build /usr/share/nginx/html

# Add non-root user for security
RUN addgroup -g 101 -S nginx && \
    adduser -S -D -H -u 101 -h /var/cache/nginx -s /sbin/nologin -G nginx -g nginx nginx || true

# Set proper permissions
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

# Switch to non-root user
USER nginx

# Expose port 80
EXPOSE 80

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# Use dumb-init to handle signals properly
ENTRYPOINT ["/usr/bin/dumb-init", "--"]

# Start nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
