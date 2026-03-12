#!/bin/bash
# MY JARVIS — PostgreSQL daily backup
# Add to crontab: 0 3 * * * /path/to/backup.sh
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups}"
KEEP_DAYS="${KEEP_DAYS:-7}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="jarvis_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

docker compose exec -T postgres pg_dump \
  -U "${POSTGRES_USER:-jarvis}" \
  -d "${POSTGRES_DB:-jarvis}" \
  --no-owner --clean | gzip > "${BACKUP_DIR}/${FILENAME}"

echo "Backup created: ${BACKUP_DIR}/${FILENAME} ($(du -h "${BACKUP_DIR}/${FILENAME}" | cut -f1))"

# Cleanup old backups
find "$BACKUP_DIR" -name "jarvis_*.sql.gz" -mtime +${KEEP_DAYS} -delete
echo "Cleaned backups older than ${KEEP_DAYS} days"
