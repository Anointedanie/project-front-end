.PHONY: help install dev build docker-build docker-run docker-stop docker-clean deploy-local deploy-k3s deploy-eks

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

install: ## Install dependencies
	npm install

dev: ## Start development server
	npm start

build: ## Build production bundle
	npm run build

test: ## Run tests
	npm test

lint: ## Run linter
	npm run lint

# Docker Commands
docker-build: ## Build Docker image
	docker build \
		--build-arg REACT_APP_API_URL=${REACT_APP_API_URL:-http://localhost:8000/api} \
		--build-arg REACT_APP_ENV=${REACT_APP_ENV:-production} \
		-t ecommerce-frontend:latest .

docker-build-no-cache: ## Build Docker image without cache
	docker build --no-cache \
		--build-arg REACT_APP_API_URL=${REACT_APP_API_URL:-http://localhost:8000/api} \
		--build-arg REACT_APP_ENV=${REACT_APP_ENV:-production} \
		-t ecommerce-frontend:latest .

docker-run: ## Run Docker container
	docker run -d -p 80:80 --name ecommerce-frontend ecommerce-frontend:latest

docker-stop: ## Stop Docker container
	docker stop ecommerce-frontend
	docker rm ecommerce-frontend

docker-clean: ## Remove Docker image
	docker rmi ecommerce-frontend:latest

docker-logs: ## View Docker container logs
	docker logs -f ecommerce-frontend

# Docker Compose Commands
compose-up: ## Start all services with docker-compose
	docker-compose up -d

compose-down: ## Stop all services
	docker-compose down

compose-logs: ## View docker-compose logs
	docker-compose logs -f

compose-build: ## Build docker-compose services
	docker-compose build

compose-restart: ## Restart all services
	docker-compose restart

# Deployment Commands
deploy-local: build ## Deploy locally with Docker
	@echo "Building and deploying locally..."
	docker-compose up -d --build
	@echo "Application deployed at http://localhost"

deploy-k3s: build ## Deploy to K3s cluster
	@echo "Deploying to K3s..."
	kubectl apply -f k8s/deployment.yaml
	kubectl apply -f k8s/service.yaml
	@echo "Deployment complete. Check status with: kubectl get pods"

deploy-eks: build ## Deploy to AWS EKS
	@echo "Deploying to AWS EKS..."
	# Build and push to ECR
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(ECR_REGISTRY)
	docker build -t $(ECR_REGISTRY)/ecommerce-frontend:$(VERSION) .
	docker push $(ECR_REGISTRY)/ecommerce-frontend:$(VERSION)
	# Update K8s manifests
	kubectl apply -f k8s/production/
	@echo "Deployment to EKS complete"

# Monitoring Commands
logs-frontend: ## View frontend logs
	docker-compose logs -f frontend

logs-backend: ## View backend logs
	docker-compose logs -f backend

logs-db: ## View database logs
	docker-compose logs -f db

monitor: ## Open monitoring dashboard
	@echo "Opening monitoring dashboard..."
	@echo "Application logs: http://localhost/logs"
	@echo "Metrics: http://localhost/metrics"

# Database Commands
db-migrate: ## Run database migrations (requires backend)
	docker-compose exec backend python manage.py migrate

db-shell: ## Open database shell
	docker-compose exec db psql -U ecommerce_user -d ecommerce

db-backup: ## Backup database
	@echo "Creating database backup..."
	docker-compose exec db pg_dump -U ecommerce_user ecommerce > backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Backup created successfully"

db-restore: ## Restore database from backup (requires BACKUP_FILE variable)
	@echo "Restoring database from $(BACKUP_FILE)..."
	docker-compose exec -T db psql -U ecommerce_user ecommerce < $(BACKUP_FILE)
	@echo "Database restored successfully"

# SSL Commands
ssl-generate: ## Generate self-signed SSL certificate for local testing
	@echo "Generating self-signed SSL certificate..."
	openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
		-keyout ssl/private.key \
		-out ssl/certificate.crt \
		-subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
	@echo "SSL certificate generated in ssl/ directory"

# Cleanup Commands
clean: ## Clean build artifacts
	rm -rf build
	rm -rf node_modules

clean-all: clean docker-clean ## Clean everything including Docker images
	docker-compose down -v
	docker system prune -af

# Environment Setup
setup-dev: ## Setup development environment
	@echo "Setting up development environment..."
	cp .env.example .env
	npm install
	@echo "Development environment ready. Update .env with your configuration."

setup-prod: ## Setup production environment
	@echo "Setting up production environment..."
	cp .env.docker .env
	@echo "Update .env with production values before deploying"

# Health Check
health: ## Check application health
	@echo "Checking application health..."
	@curl -f http://localhost/ > /dev/null 2>&1 && echo "✓ Frontend is healthy" || echo "✗ Frontend is down"
	@curl -f http://localhost:8000/api/health/ > /dev/null 2>&1 && echo "✓ Backend is healthy" || echo "✗ Backend is down"

# Version Management
version: ## Display current version
	@echo "Version: $$(grep -m1 version package.json | awk -F: '{ print $$2 }' | sed 's/[", ]//g')"

bump-version: ## Bump version (patch)
	npm version patch

# Quick Commands
quick-start: install dev ## Quick start for new developers

quick-deploy: build deploy-local ## Quick local deployment

# AWS Commands
aws-login: ## Login to AWS ECR
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(ECR_REGISTRY)

aws-push: docker-build aws-login ## Build and push to AWS ECR
	docker tag ecommerce-frontend:latest $(ECR_REGISTRY)/ecommerce-frontend:latest
	docker push $(ECR_REGISTRY)/ecommerce-frontend:latest

# Kubernetes Commands
k8s-status: ## Check K8s deployment status
	kubectl get pods -l app=ecommerce-frontend
	kubectl get services -l app=ecommerce-frontend

k8s-logs: ## View K8s pod logs
	kubectl logs -f deployment/ecommerce-frontend

k8s-shell: ## Get shell in K8s pod
	kubectl exec -it deployment/ecommerce-frontend -- /bin/sh

k8s-restart: ## Restart K8s deployment
	kubectl rollout restart deployment/ecommerce-frontend

# Documentation
docs: ## Generate documentation
	@echo "Generating documentation..."
	npm run docs

# Default target
.DEFAULT_GOAL := help
