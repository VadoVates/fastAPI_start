#!/bin/bash

TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_DIR="/home/marek/backend/fastapi/db/backup"
CONTAINER_NAME="postgres_db"
DB_NAME="measures"
DB_USER="esp32"

# Tworzymy katalog na backupy, jeśli nie istnieje
mkdir -p "$BACKUP_DIR"

# Wykonujemy dump
docker exec "$CONTAINER_NAME" pg_dump -U "$DB_USER" -F c -f /tmp/backup_$TIMESTAMP.dump "$DB_NAME"
# Kopiujemy backup na hosta
docker cp "$CONTAINER_NAME":/tmp/backup_$TIMESTAMP.dump "$BACKUP_DIR"
# Usuwamy stary dump z kontenera
docker exec "$CONTAINER_NAME" rm /tmp/backup_$TIMESTAMP.dump
# Usuwamy stare backupy (np. starsze niż 7 dni)
find "$BACKUP_DIR" -type f -name "*.dump" -mtime +7 -delete
