#!/bin/bash
# Disaster Recovery Restore Script for HaqNow
# Restores MySQL, PostgreSQL, and documents from Vienna (at-vie-1) backup
#
# Usage:
#   ./scripts/restore-from-backup.sh                    # Interactive mode
#   ./scripts/restore-from-backup.sh list               # List available backups
#   ./scripts/restore-from-backup.sh restore 2025-01-15 # Restore specific date
#
# Prerequisites:
#   1. AWS CLI installed: pip install awscli
#   2. MySQL client installed: apt install default-mysql-client
#   3. PostgreSQL client installed: apt install postgresql-client
#   4. Environment variables set (from .env)

set -e

# DR Configuration
DR_ENDPOINT="sos-at-vie-1.exo.io"
DR_BUCKET="${DR_BUCKET:-foi-archive-dr}"
PRIMARY_BUCKET="${EXOSCALE_BUCKET:-foi-archive-terraform}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Load environment variables if .env exists
load_env() {
    if [ -f ".env" ]; then
        log_info "Loading environment from .env..."
        export $(grep -v '^#' .env | xargs)
    elif [ -f "../.env" ]; then
        log_info "Loading environment from ../.env..."
        export $(grep -v '^#' ../.env | xargs)
    else
        log_warn ".env file not found. Make sure environment variables are set."
    fi
}

# Configure AWS CLI for Exoscale SOS
configure_s3() {
    export AWS_ACCESS_KEY_ID="${EXOSCALE_S3_ACCESS_KEY}"
    export AWS_SECRET_ACCESS_KEY="${EXOSCALE_S3_SECRET_KEY}"
    export AWS_DEFAULT_REGION="us-east-1"
}

# List available backups
list_backups() {
    log_info "Listing available backups in Vienna (at-vie-1)..."
    configure_s3
    
    echo ""
    echo "=== MySQL Backups ==="
    aws s3 ls "s3://${DR_BUCKET}/backups/mysql/" --endpoint-url "https://${DR_ENDPOINT}" 2>/dev/null | tail -10 || echo "No MySQL backups found"
    
    echo ""
    echo "=== PostgreSQL Backups ==="
    aws s3 ls "s3://${DR_BUCKET}/backups/postgres/" --endpoint-url "https://${DR_ENDPOINT}" 2>/dev/null | tail -10 || echo "No PostgreSQL backups found"
    
    echo ""
    echo "=== Documents Sync Status ==="
    DOC_COUNT=$(aws s3 ls "s3://${DR_BUCKET}/documents/" --endpoint-url "https://${DR_ENDPOINT}" --recursive 2>/dev/null | wc -l || echo "0")
    echo "Total documents in DR bucket: ${DOC_COUNT}"
}

# Download and restore MySQL backup
restore_mysql() {
    local BACKUP_DATE=$1
    local TARGET_HOST=${2:-${MYSQL_HOST}}
    local TARGET_PORT=${3:-${MYSQL_PORT:-21699}}
    local TARGET_USER=${4:-${MYSQL_USER}}
    local TARGET_PASSWORD=${5:-${MYSQL_PASSWORD}}
    local TARGET_DATABASE=${6:-${MYSQL_DATABASE:-defaultdb}}
    
    log_step "Restoring MySQL from backup: ${BACKUP_DATE}"
    
    BACKUP_FILE="mysql-${BACKUP_DATE}.sql.gz"
    LOCAL_FILE="/tmp/${BACKUP_FILE}"
    
    # Download backup
    log_info "Downloading MySQL backup..."
    configure_s3
    aws s3 cp "s3://${DR_BUCKET}/backups/mysql/${BACKUP_FILE}" "${LOCAL_FILE}" \
        --endpoint-url "https://${DR_ENDPOINT}"
    
    # Verify download
    if [ ! -f "${LOCAL_FILE}" ]; then
        log_error "Failed to download backup file"
        return 1
    fi
    
    log_info "Backup downloaded: $(du -h ${LOCAL_FILE} | cut -f1)"
    
    # Confirm before restore
    echo ""
    log_warn "WARNING: This will overwrite the MySQL database!"
    log_warn "Target: ${TARGET_HOST}:${TARGET_PORT}/${TARGET_DATABASE}"
    echo ""
    read -p "Type 'RESTORE' to confirm: " CONFIRM
    
    if [ "${CONFIRM}" != "RESTORE" ]; then
        log_info "Restore cancelled"
        rm -f "${LOCAL_FILE}"
        return 0
    fi
    
    # Restore database
    log_info "Restoring MySQL database..."
    gunzip -c "${LOCAL_FILE}" | mysql \
        --host="${TARGET_HOST}" \
        --port="${TARGET_PORT}" \
        --user="${TARGET_USER}" \
        --password="${TARGET_PASSWORD}" \
        --ssl-mode=REQUIRED \
        "${TARGET_DATABASE}"
    
    log_info "MySQL restore complete!"
    rm -f "${LOCAL_FILE}"
}

# Download and restore PostgreSQL backup
restore_postgres() {
    local BACKUP_DATE=$1
    local TARGET_HOST=${2:-${POSTGRES_RAG_HOST}}
    local TARGET_PORT=${3:-${POSTGRES_RAG_PORT:-21699}}
    local TARGET_USER=${4:-${POSTGRES_RAG_USER}}
    local TARGET_PASSWORD=${5:-${POSTGRES_RAG_PASSWORD}}
    local TARGET_DATABASE=${6:-${POSTGRES_RAG_DATABASE:-defaultdb}}
    
    log_step "Restoring PostgreSQL from backup: ${BACKUP_DATE}"
    
    BACKUP_FILE="postgres-rag-${BACKUP_DATE}.sql.gz"
    LOCAL_FILE="/tmp/${BACKUP_FILE}"
    
    # Download backup
    log_info "Downloading PostgreSQL backup..."
    configure_s3
    aws s3 cp "s3://${DR_BUCKET}/backups/postgres/${BACKUP_FILE}" "${LOCAL_FILE}" \
        --endpoint-url "https://${DR_ENDPOINT}"
    
    # Verify download
    if [ ! -f "${LOCAL_FILE}" ]; then
        log_error "Failed to download backup file"
        return 1
    fi
    
    log_info "Backup downloaded: $(du -h ${LOCAL_FILE} | cut -f1)"
    
    # Confirm before restore
    echo ""
    log_warn "WARNING: This will overwrite the PostgreSQL RAG database!"
    log_warn "Target: ${TARGET_HOST}:${TARGET_PORT}/${TARGET_DATABASE}"
    echo ""
    read -p "Type 'RESTORE' to confirm: " CONFIRM
    
    if [ "${CONFIRM}" != "RESTORE" ]; then
        log_info "Restore cancelled"
        rm -f "${LOCAL_FILE}"
        return 0
    fi
    
    # Restore database
    log_info "Restoring PostgreSQL database..."
    export PGPASSWORD="${TARGET_PASSWORD}"
    gunzip -c "${LOCAL_FILE}" | psql \
        --host="${TARGET_HOST}" \
        --port="${TARGET_PORT}" \
        --username="${TARGET_USER}" \
        --dbname="${TARGET_DATABASE}"
    unset PGPASSWORD
    
    log_info "PostgreSQL restore complete!"
    rm -f "${LOCAL_FILE}"
}

# Sync documents from DR bucket back to primary
restore_documents() {
    log_step "Restoring documents from Vienna to primary bucket..."
    
    configure_s3
    
    # Confirm before restore
    echo ""
    log_warn "WARNING: This will sync documents from DR bucket to primary!"
    log_warn "Source: s3://${DR_BUCKET}/documents/"
    log_warn "Target: s3://${PRIMARY_BUCKET}/"
    echo ""
    read -p "Type 'RESTORE' to confirm: " CONFIRM
    
    if [ "${CONFIRM}" != "RESTORE" ]; then
        log_info "Restore cancelled"
        return 0
    fi
    
    # Sync from DR to primary
    # Note: You may need to adjust the endpoint based on which region's bucket you're restoring to
    log_info "Syncing documents..."
    aws s3 sync \
        "s3://${DR_BUCKET}/documents/" \
        "s3://${PRIMARY_BUCKET}/" \
        --endpoint-url "https://${DR_ENDPOINT}" \
        --only-show-errors
    
    log_info "Document restore complete!"
}

# Full disaster recovery
full_restore() {
    local BACKUP_DATE=$1
    
    log_step "Starting FULL disaster recovery..."
    echo ""
    log_warn "=========================================="
    log_warn "     FULL DISASTER RECOVERY MODE"
    log_warn "=========================================="
    log_warn "This will restore:"
    log_warn "  - MySQL database"
    log_warn "  - PostgreSQL RAG database"
    log_warn "  - All documents from S3"
    log_warn ""
    log_warn "Backup date: ${BACKUP_DATE}"
    log_warn "=========================================="
    echo ""
    read -p "Type 'FULL RESTORE' to confirm: " CONFIRM
    
    if [ "${CONFIRM}" != "FULL RESTORE" ]; then
        log_info "Full restore cancelled"
        return 0
    fi
    
    restore_mysql "${BACKUP_DATE}"
    restore_postgres "${BACKUP_DATE}"
    restore_documents
    
    log_info "=========================================="
    log_info "Full disaster recovery complete!"
    log_info "=========================================="
    log_info ""
    log_info "Next steps:"
    log_info "1. Verify database connectivity"
    log_info "2. Check document access"
    log_info "3. Run application health checks"
    log_info "4. Update DNS if needed"
}

# Interactive mode
interactive_mode() {
    echo ""
    echo "=========================================="
    echo "  HaqNow Disaster Recovery Console"
    echo "=========================================="
    echo ""
    echo "Available commands:"
    echo "  1) List available backups"
    echo "  2) Restore MySQL only"
    echo "  3) Restore PostgreSQL only"
    echo "  4) Restore documents only"
    echo "  5) Full restore (all databases + documents)"
    echo "  6) Exit"
    echo ""
    read -p "Select option [1-6]: " OPTION
    
    case ${OPTION} in
        1)
            list_backups
            ;;
        2)
            list_backups
            echo ""
            read -p "Enter backup date (YYYY-MM-DD-HHMMSS): " BACKUP_DATE
            restore_mysql "${BACKUP_DATE}"
            ;;
        3)
            list_backups
            echo ""
            read -p "Enter backup date (YYYY-MM-DD-HHMMSS): " BACKUP_DATE
            restore_postgres "${BACKUP_DATE}"
            ;;
        4)
            restore_documents
            ;;
        5)
            list_backups
            echo ""
            read -p "Enter backup date (YYYY-MM-DD-HHMMSS): " BACKUP_DATE
            full_restore "${BACKUP_DATE}"
            ;;
        6)
            log_info "Exiting..."
            exit 0
            ;;
        *)
            log_error "Invalid option"
            exit 1
            ;;
    esac
}

# Main
main() {
    load_env
    
    case ${1:-""} in
        "list")
            list_backups
            ;;
        "restore")
            if [ -z "$2" ]; then
                log_error "Usage: $0 restore <backup-date>"
                log_info "Run '$0 list' to see available backups"
                exit 1
            fi
            full_restore "$2"
            ;;
        "mysql")
            if [ -z "$2" ]; then
                log_error "Usage: $0 mysql <backup-date>"
                exit 1
            fi
            restore_mysql "$2"
            ;;
        "postgres")
            if [ -z "$2" ]; then
                log_error "Usage: $0 postgres <backup-date>"
                exit 1
            fi
            restore_postgres "$2"
            ;;
        "documents")
            restore_documents
            ;;
        "")
            interactive_mode
            ;;
        *)
            echo "Usage: $0 [list|restore|mysql|postgres|documents] [backup-date]"
            echo ""
            echo "Commands:"
            echo "  list              - List available backups"
            echo "  restore <date>    - Full restore from backup date"
            echo "  mysql <date>      - Restore MySQL only"
            echo "  postgres <date>   - Restore PostgreSQL only"
            echo "  documents         - Sync documents from DR bucket"
            echo ""
            echo "Run without arguments for interactive mode."
            exit 1
            ;;
    esac
}

main "$@"









