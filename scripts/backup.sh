#!/bin/bash
set -e

BACKUP_DIR="/var/backups/telecom"
TIMESTAMP=$(date +%F-%H%M%S)

mkdir -p $BACKUP_DIR

echo "Creating PostgreSQL backup..."
docker exec telecom-system-db-1 pg_dump -U telecom telecom | gzip > $BACKUP_DIR/db-$TIMESTAMP.sql.gz

find $BACKUP_DIR -name "*.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR/db-$TIMESTAMP.sql.gz"
