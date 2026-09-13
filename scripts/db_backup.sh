#!/bin/bash

set -euo pipefail

BACKUP_DIR="/var/backups/db"
TIMESTAMP=$(date '+%Y%m%d')
BACKUP_FILE="${BACKUP_DIR}/db_backup_${TIMESTAMP}.sql.gz"

DB_CONTAINER="devops_trainee_assignment-db-1"
DB_NAME="traineedb"
DB_USER="trainee"

mkdir -p "$BACKUP_DIR"

echo "Starting PostgreSQL backup..."
echo "Database: $DB_NAME"
echo "Output: $BACKUP_FILE"

docker exec "$DB_CONTAINER" \
    pg_dump -U "$DB_USER" -d "$DB_NAME" \
    | gzip > "$BACKUP_FILE"

chmod 600 "$BACKUP_FILE"

echo "Backup completed successfully."
ls -lh "$BACKUP_FILE"
