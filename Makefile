.PHONY: help build up down logs clean restart db-shell api-shell test

# Default target
help:
	@echo "Available commands:"
	@echo "  build     - Build Docker images"
	@echo "  up        - Start services"
	@echo "  down      - Stop services"
	@echo "  restart   - Restart services"
	@echo "  logs      - Show logs"
	@echo "  clean     - Clean up containers and images"
	@echo "  db-shell  - Access database shell"
	@echo "  api-shell - Access API container shell"
	@echo "  test      - Run tests"

# Build Docker images
build:
	docker compose build --no-cache

# Start services
up:
	docker compose up -d

# Stop services
down:
	docker compose down

# Restart services
restart: down up

# Show logs
logs:
	docker compose logs -f

# Show API logs only
logs-api:
	docker compose logs -f api

# Show DB logs only
logs-db:
	docker compose logs -f db

# Clean up everything
clean:
	docker compose down -v --rmi all --remove-orphans
	docker system prune -f

# Access database shell
db-shell:
	docker compose exec db psql -U $DB_USER -d $DB_NAME

# Access API container shell
api-shell:
	docker compose exec api bash

# Check services health
health:
	@echo "Checking API health..."
	@curl -f http://localhost:8000/health || echo "API not responding"
	@echo "Checking database..."
	@docker compose exec db pg_isready -U $DB_USER -d $DB_NAME

# Run tests (if you have them)
test:
	docker compose exec api python -m pytest tests/ -v

# Development commands
dev-setup:
	cp .env.example .env
	@echo "Please edit .env file with your configuration"

# Production deployment
prod-deploy:
	@echo "Deploying to production..."
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Backup database
backup:
	docker compose exec db pg_dump -U $DB_USER $DB_NAME > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore database from backup
restore:
	@read -p "Enter backup file path: " backup_file; \
	docker compose exec -T db psql -U $DB_USER -d $DB_NAME < $backup_file