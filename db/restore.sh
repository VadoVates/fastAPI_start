#!/bin/sh

echo ">>> Restoring from dump..."
pg_restore --clean --no-owner -U "$POSTGRES_USER" -d "$POSTGRES_DB" "$(dirname "$0")/data.dump"