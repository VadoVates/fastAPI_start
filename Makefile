.PHONY: help build up down logs clean restart db-shell api-shell test

# Default target
help:
	@echo ""
	@echo "  Użycie: make <komenda>"
	@echo ""
	@echo "  build        — Buduj obrazy Dockera od zera"
	@echo "  rebuild      — Zrób build od nowa i odpal kontenery"
	@echo "  up           — Odpal kontenery w tle"
	@echo "  down         — Zatrzymaj wszystko"
	@echo "  restart      — Zrób porządek: stop, start"
	@echo "  logs         — Lej logi wszystkich kontenerów"
	@echo "  logs-api     — Lej tylko logi API"
	@echo "  logs-db      — Lej tylko logi bazy"
	@echo "  clean        — Wypierdol wszystko (kontenery, obrazy, volumy, osierocone)"
	@echo "  db-shell     — Wbij się do bazy"
	@echo "  api-shell    — Wbij się do kontenera API"
	@echo "  health       — Sprawdź, czy API i baza żyją"
	@echo "  backup       — Zrób backup bazy (plik SQL)"
	@echo "  restore      — Przywróć bazę z dumpa (.dump)"
	@echo "  test         — Odpal testy z pytesta (jeśli są)"
	@echo "  dev-setup    — Sklonuj i przygotuj środowisko .env"
	@echo "  prod-deploy  — Odpal produkcję z monitoringiem"
	@echo "  prod-up      — Alias do prod-deploy"
	@echo "  prod-down    — Zatrzymaj produkcję"
	@echo "  config       — Pokaż finalny config docker-compose"
	@echo "  prod-config  — Pokaż finalny config dla produkcji"
	@echo ""

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

# Production deployment (merges docker-compose.yml + docker-compose.prod.yml)
prod-deploy:
	@echo "Deploying to production with monitoring..."
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Alternative way to deploy prod (same result)
prod-up:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Stop production deployment
prod-down:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# Show merged configuration (useful for debugging)
config:
	docker compose config

# Show merged production configuration
prod-config:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml config

# Backup database
backup:
	docker compose exec db pg_dump -U $DB_USER $DB_NAME > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore database from backup
restore:
	@bash -c 'source .env && \
	read -p "Enter path to .dump file: " backup_file; \
	docker compose exec -T db pg_restore --clean --no-owner -U $$DB_USER -d $$DB_NAME < $$backup_file'

# Rebuild everything from scratch
rebuild: down clean build up