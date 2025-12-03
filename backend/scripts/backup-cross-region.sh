#!/bin/bash
# Cross-Region Backup Script for HaqNow
# Backs up MySQL, PostgreSQL, and S3 documents to Vienna (at-vie-1)
#
# This script is designed to run as a Kubernetes CronJob
# All configuration comes from environment variables

set -e

# Configuration
BACKUP_DATE=$(date +%Y-%m-%d-%H%M%S)
BACKUP_DIR="/tmp/backup-${BACKUP_DATE}"
RETENTION_DAYS=30

# Primary region (Zurich)
PRIMARY_ENDPOINT="sos-ch-dk-2.exo.io"
PRIMARY_BUCKET="${EXOSCALE_BUCKET:-foi-archive-terraform}"

# DR region (Vienna, Austria)
DR_ENDPOINT="sos-at-vie-1.exo.io"
DR_BUCKET="${DR_BUCKET:-foi-archive-dr}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

cleanup() {
    log_info "Cleaning up temporary files..."
    rm -rf "${BACKUP_DIR}"
}

trap cleanup EXIT

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Configure AWS CLI for Exoscale SOS
configure_s3() {
    local endpoint=$1
    export AWS_ACCESS_KEY_ID="${EXOSCALE_S3_ACCESS_KEY}"
    export AWS_SECRET_ACCESS_KEY="${EXOSCALE_S3_SECRET_KEY}"
    export AWS_DEFAULT_REGION="us-east-1"  # Required but not used by Exoscale
}

# ============================================
# MySQL Backup
# ============================================
backup_mysql() {
    log_info "Starting MySQL backup..."
    
    if [ -z "${MYSQL_HOST}" ] || [ -z "${MYSQL_USER}" ] || [ -z "${MYSQL_PASSWORD}" ]; then
        log_error "MySQL credentials not configured"
        return 1
    fi
    
    MYSQL_DUMP_FILE="${BACKUP_DIR}/mysql-${BACKUP_DATE}.sql.gz"
    
    # Use SSL for Exoscale DBaaS
    mysqldump \
        --host="${MYSQL_HOST}" \
        --port="${MYSQL_PORT:-21699}" \
        --user="${MYSQL_USER}" \
        --password="${MYSQL_PASSWORD}" \
        --ssl-mode=REQUIRED \
        --single-transaction \
        --routines \
        --triggers \
        --databases "${MYSQL_DATABASE:-defaultdb}" \
        2>/dev/null | gzip > "${MYSQL_DUMP_FILE}"
    
    MYSQL_SIZE=$(du -h "${MYSQL_DUMP_FILE}" | cut -f1)
    log_info "MySQL backup complete: ${MYSQL_SIZE}"
    
    # Upload to DR bucket
    log_info "Uploading MySQL backup to Vienna..."
    configure_s3 "${DR_ENDPOINT}"
    aws s3 cp "${MYSQL_DUMP_FILE}" \
        "s3://${DR_BUCKET}/backups/mysql/mysql-${BACKUP_DATE}.sql.gz" \
        --endpoint-url "https://${DR_ENDPOINT}"
    
    log_info "MySQL backup uploaded successfully"
}

# ============================================
# PostgreSQL Backup (RAG Database)
# ============================================
backup_postgres() {
    log_info "Starting PostgreSQL RAG backup..."
    
    if [ -z "${POSTGRES_RAG_HOST}" ] || [ -z "${POSTGRES_RAG_USER}" ] || [ -z "${POSTGRES_RAG_PASSWORD}" ]; then
        log_error "PostgreSQL credentials not configured"
        return 1
    fi
    
    PG_DUMP_FILE="${BACKUP_DIR}/postgres-rag-${BACKUP_DATE}.sql.gz"
    
    # Set password via environment variable
    export PGPASSWORD="${POSTGRES_RAG_PASSWORD}"
    
    pg_dump \
        --host="${POSTGRES_RAG_HOST}" \
        --port="${POSTGRES_RAG_PORT:-21699}" \
        --username="${POSTGRES_RAG_USER}" \
        --dbname="${POSTGRES_RAG_DATABASE:-defaultdb}" \
        --format=plain \
        --no-owner \
        --no-acl \
        2>/dev/null | gzip > "${PG_DUMP_FILE}"
    
    unset PGPASSWORD
    
    PG_SIZE=$(du -h "${PG_DUMP_FILE}" | cut -f1)
    log_info "PostgreSQL backup complete: ${PG_SIZE}"
    
    # Upload to DR bucket
    log_info "Uploading PostgreSQL backup to Vienna..."
    configure_s3 "${DR_ENDPOINT}"
    aws s3 cp "${PG_DUMP_FILE}" \
        "s3://${DR_BUCKET}/backups/postgres/postgres-rag-${BACKUP_DATE}.sql.gz" \
        --endpoint-url "https://${DR_ENDPOINT}"
    
    log_info "PostgreSQL backup uploaded successfully"
}

# ============================================
# S3 Documents Sync
# ============================================
sync_documents() {
    log_info "Starting S3 documents sync to Vienna..."
    
    configure_s3 "${DR_ENDPOINT}"
    
    # For Exoscale SOS cross-region sync, we need to:
    # 1. Download from primary region
    # 2. Upload to DR region
    # This is because aws s3 sync doesn't support different endpoints for source/dest
    
    SYNC_DIR="/tmp/s3-sync-$$"
    mkdir -p "${SYNC_DIR}"
    
    # Download from primary bucket (using primary endpoint)
    log_info "Downloading documents from primary bucket..."
    aws s3 sync \
        "s3://${PRIMARY_BUCKET}/" \
        "${SYNC_DIR}/" \
        --endpoint-url "https://${PRIMARY_ENDPOINT}" \
        --only-show-errors
    
    # Upload to DR bucket (using DR endpoint)
    log_info "Uploading documents to DR bucket..."
    aws s3 sync \
        "${SYNC_DIR}/" \
        "s3://${DR_BUCKET}/documents/" \
        --endpoint-url "https://${DR_ENDPOINT}" \
        --only-show-errors
    
    # Cleanup sync directory
    rm -rf "${SYNC_DIR}"
    
    log_info "S3 documents sync complete"
}

# ============================================
# Cleanup Old Backups
# ============================================
cleanup_old_backups() {
    log_info "Cleaning up backups older than ${RETENTION_DAYS} days..."
    
    configure_s3 "${DR_ENDPOINT}"
    
    # Calculate cutoff date
    CUTOFF_DATE=$(date -d "-${RETENTION_DAYS} days" +%Y-%m-%d 2>/dev/null || date -v-${RETENTION_DAYS}d +%Y-%m-%d)
    
    # List and delete old MySQL backups
    aws s3 ls "s3://${DR_BUCKET}/backups/mysql/" --endpoint-url "https://${DR_ENDPOINT}" 2>/dev/null | while read -r line; do
        FILE_DATE=$(echo "$line" | awk '{print $4}' | grep -oP '\d{4}-\d{2}-\d{2}' | head -1)
        FILE_NAME=$(echo "$line" | awk '{print $4}')
        if [ -n "${FILE_DATE}" ] && [[ "${FILE_DATE}" < "${CUTOFF_DATE}" ]]; then
            log_info "Deleting old backup: ${FILE_NAME}"
            aws s3 rm "s3://${DR_BUCKET}/backups/mysql/${FILE_NAME}" --endpoint-url "https://${DR_ENDPOINT}"
        fi
    done
    
    # List and delete old PostgreSQL backups
    aws s3 ls "s3://${DR_BUCKET}/backups/postgres/" --endpoint-url "https://${DR_ENDPOINT}" 2>/dev/null | while read -r line; do
        FILE_DATE=$(echo "$line" | awk '{print $4}' | grep -oP '\d{4}-\d{2}-\d{2}' | head -1)
        FILE_NAME=$(echo "$line" | awk '{print $4}')
        if [ -n "${FILE_DATE}" ] && [[ "${FILE_DATE}" < "${CUTOFF_DATE}" ]]; then
            log_info "Deleting old backup: ${FILE_NAME}"
            aws s3 rm "s3://${DR_BUCKET}/backups/postgres/${FILE_NAME}" --endpoint-url "https://${DR_ENDPOINT}"
        fi
    done
    
    log_info "Cleanup complete"
}

# ============================================
# Main Execution
# ============================================
main() {
    log_info "=========================================="
    log_info "HaqNow Cross-Region Backup Starting"
    log_info "Date: ${BACKUP_DATE}"
    log_info "DR Region: Vienna (at-vie-1)"
    log_info "=========================================="
    
    BACKUP_SUCCESS=true
    
    # Backup MySQL
    if ! backup_mysql; then
        log_error "MySQL backup failed"
        BACKUP_SUCCESS=false
    fi
    
    # Backup PostgreSQL
    if ! backup_postgres; then
        log_error "PostgreSQL backup failed"
        BACKUP_SUCCESS=false
    fi
    
    # Sync documents
    if ! sync_documents; then
        log_error "S3 sync failed"
        BACKUP_SUCCESS=false
    fi
    
    # Cleanup old backups
    cleanup_old_backups || log_warn "Cleanup had issues (non-fatal)"
    
    log_info "=========================================="
    if [ "${BACKUP_SUCCESS}" = true ]; then
        log_info "Backup completed successfully!"
    else
        log_error "Backup completed with errors"
        exit 1
    fi
    log_info "=========================================="
}

main "$@"

