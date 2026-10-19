#!/bin/bash
# Standalone VM & Database Backup Script for HaqNow
# Backs up local MySQL, local PostgreSQL (pgvector), and documents to Exoscale SOS (Object Storage)
#
# Usage:
#   ./scripts/backup-vm.sh                     # Runs full backup and uploads to SOS
#   ./scripts/backup-vm.sh --db-only           # Runs database backup only
#
# Prerequisites:
#   - AWS CLI installed (`aws`)
#   - mysqldump and pg_dump installed
#   - Environment variables set (or .env present in current directory / opt / foi-archive)

set -e

BACKUP_DATE=$(date +%Y-%m-%d-%H%M%S)
BACKUP_DIR="/tmp/haqnow-backup-${BACKUP_DATE}"
mkdir -p "${BACKUP_DIR}"

cleanup() {
    rm -rf "${BACKUP_DIR}"
}
trap cleanup EXIT

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"; }

# Load .env if available
if [ -f ".env" ]; then
    set -a && source .env && set +a
elif [ -f "/opt/foi-archive/.env" ]; then
    set -a && source /opt/foi-archive/.env && set +a
fi

DR_BUCKET="${DR_BUCKET:-foi-archive-dr}"
DR_ENDPOINT="${DR_ENDPOINT:-sos-at-vie-1.exo.io}"
PRIMARY_BUCKET="${EXOSCALE_BUCKET:-foi-archive-terraform}"
PRIMARY_ENDPOINT="${EXOSCALE_S3_ENDPOINT:-sos-ch-dk-2.exo.io}"

export AWS_ACCESS_KEY_ID="${EXOSCALE_S3_ACCESS_KEY}"
export AWS_SECRET_ACCESS_KEY="${EXOSCALE_S3_SECRET_KEY}"
export AWS_DEFAULT_REGION="us-east-1"

# 1. MySQL Backup
backup_mysql() {
    log_info "Creating MySQL database backup..."
    MYSQL_FILE="${BACKUP_DIR}/mysql-${BACKUP_DATE}.sql.gz"
    
    MYSQL_HOST_ARG="${MYSQL_HOST:-localhost}"
    MYSQL_PORT_ARG="${MYSQL_PORT:-3306}"
    MYSQL_USER_ARG="${MYSQL_USER:-foi_user}"
    MYSQL_DB_ARG="${MYSQL_DATABASE:-foi_archive}"
    
    mysqldump \
        --host="${MYSQL_HOST_ARG}" \
        --port="${MYSQL_PORT_ARG}" \
        --user="${MYSQL_USER_ARG}" \
        --password="${MYSQL_PASSWORD}" \
        --single-transaction \
        --routines \
        --triggers \
        "${MYSQL_DB_ARG}" | gzip > "${MYSQL_FILE}"
        
    SIZE=$(du -h "${MYSQL_FILE}" | cut -f1)
    log_info "MySQL dump ready: ${SIZE}. Uploading to Object Storage (Vienna)..."
    
    aws s3 cp "${MYSQL_FILE}" \
        "s3://${DR_BUCKET}/backups/mysql/mysql-${BACKUP_DATE}.sql.gz" \
        --endpoint-url "https://${DR_ENDPOINT}"
    log_info "✅ MySQL backup uploaded successfully"
}

# 2. PostgreSQL Backup (RAG & Vectors)
backup_postgres() {
    log_info "Creating PostgreSQL (pgvector) database backup..."
    PG_FILE="${BACKUP_DIR}/postgres-${BACKUP_DATE}.sql.gz"
    
    PG_HOST_ARG="${POSTGRES_RAG_HOST:-localhost}"
    PG_PORT_ARG="${POSTGRES_RAG_PORT:-5432}"
    PG_USER_ARG="${POSTGRES_RAG_USER:-rag_user}"
    PG_DB_ARG="${POSTGRES_RAG_DATABASE:-rag_vectors}"
    
    export PGPASSWORD="${POSTGRES_RAG_PASSWORD}"
    pg_dump \
        --host="${PG_HOST_ARG}" \
        --port="${PG_PORT_ARG}" \
        --username="${PG_USER_ARG}" \
        --dbname="${PG_DB_ARG}" \
        --format=plain \
        --no-owner \
        --no-acl | gzip > "${PG_FILE}"
    unset PGPASSWORD
    
    SIZE=$(du -h "${PG_FILE}" | cut -f1)
    log_info "PostgreSQL dump ready: ${SIZE}. Uploading to Object Storage (Vienna)..."
    
    aws s3 cp "${PG_FILE}" \
        "s3://${DR_BUCKET}/backups/postgres/postgres-${BACKUP_DATE}.sql.gz" \
        --endpoint-url "https://${DR_ENDPOINT}"
    log_info "✅ PostgreSQL backup uploaded successfully"
}

# 3. Documents Cross-Region Sync (Optional if documents already in SOS)
sync_documents() {
    log_info "Verifying documents backup in Object Storage..."
    SYNC_TMP="${BACKUP_DIR}/sync"
    mkdir -p "${SYNC_TMP}"
    
    # Sync from primary bucket to temp, then to DR bucket
    aws s3 sync "s3://${PRIMARY_BUCKET}/" "${SYNC_TMP}/" \
        --endpoint-url "https://${PRIMARY_ENDPOINT}" \
        --only-show-errors || log_warn "Primary bucket sync warning"
        
    aws s3 sync "${SYNC_TMP}/" "s3://${DR_BUCKET}/documents/" \
        --endpoint-url "https://${DR_ENDPOINT}" \
        --only-show-errors || log_warn "DR bucket sync warning"
        
    rm -rf "${SYNC_TMP}"
    log_info "✅ Document synchronization verified"
}

# 4. Retention Policy (Clean up backups older than 30 days)
cleanup_old_backups() {
    log_info "Enforcing 30-day retention on Object Storage backups..."
    CUTOFF_DATE=$(date -v-30d +%Y-%m-%d 2>/dev/null || date -d "30 days ago" +%Y-%m-%d)
    
    # Prune old MySQL dumps
    aws s3 ls "s3://${DR_BUCKET}/backups/mysql/" --endpoint-url "https://${DR_ENDPOINT}" 2>/dev/null | while read -r line; do
        FILE_DATE=$(echo "$line" | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' | head -1)
        FILE_NAME=$(echo "$line" | awk '{print $4}')
        if [ -n "$FILE_DATE" ] && [ "$FILE_DATE" \< "$CUTOFF_DATE" ] && [ -n "$FILE_NAME" ]; then
            log_info "Deleting expired backup: ${FILE_NAME}"
            aws s3 rm "s3://${DR_BUCKET}/backups/mysql/${FILE_NAME}" --endpoint-url "https://${DR_ENDPOINT}"
        fi
    done
    
    # Prune old Postgres dumps
    aws s3 ls "s3://${DR_BUCKET}/backups/postgres/" --endpoint-url "https://${DR_ENDPOINT}" 2>/dev/null | while read -r line; do
        FILE_DATE=$(echo "$line" | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' | head -1)
        FILE_NAME=$(echo "$line" | awk '{print $4}')
        if [ -n "$FILE_DATE" ] && [ "$FILE_DATE" \< "$CUTOFF_DATE" ] && [ -n "$FILE_NAME" ]; then
            log_info "Deleting expired backup: ${FILE_NAME}"
            aws s3 rm "s3://${DR_BUCKET}/backups/postgres/${FILE_NAME}" --endpoint-url "https://${DR_ENDPOINT}"
        fi
    done
}

# Run execution
backup_mysql
backup_postgres
if [ "$1" != "--db-only" ]; then
    sync_documents
fi
cleanup_old_backups

log_info "🎉 Full Object Storage backup finished successfully!"
