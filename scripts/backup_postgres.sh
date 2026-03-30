#!/bin/bash
set -e

BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_FILE="$BACKUP_DIR/postgres_backup_$TIMESTAMP.sql"

mkdir -p "$BACKUP_DIR"

export $(grep -v '^#' .env | xargs)

docker compose exec -T postgres pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" > "$BACKUP_FILE"

echo "Backup created: $BACKUP_FILE"