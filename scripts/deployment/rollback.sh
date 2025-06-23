#!/bin/bash

# HealthConnect AI - Rollback Script
# Production-grade rollback functionality for deployments
# Version: 1.0.0
# Last Updated: 2025-06-20

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="healthconnect-ai"
ENVIRONMENT="${ENVIRONMENT:-dev}"
AWS_REGION="${AWS_REGION:-us-east-1}"
BACKUP_BUCKET="${PROJECT_NAME}-${ENVIRONMENT}-backup-storage"

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# List available backups
list_backups() {
    log "Available backups for $ENVIRONMENT environment:"
    
    # List frontend backups
    echo
    echo "Frontend Backups:"
    aws s3 ls "s3://$BACKUP_BUCKET/frontend/" --recursive | awk '{print $1, $2, $4}' | sort -r | head -10
    
    # List backend backups
    echo
    echo "Backend Backups:"
    aws s3 ls "s3://$BACKUP_BUCKET/backend/" --recursive | awk '{print $1, $2, $4}' | sort -r | head -10
    
    # List database backups
    echo
    echo "Database Backups:"
    aws rds describe-db-snapshots \
        --db-instance-identifier "${PROJECT_NAME}-${ENVIRONMENT}-db" \
        --snapshot-type manual \
        --query 'DBSnapshots[*].[SnapshotCreateTime,DBSnapshotIdentifier]' \
        --output table 2>/dev/null || echo "No database backups found"
}

# Create backup before rollback
create_backup() {
    local component="$1"
    local timestamp=$(date +%Y%m%d-%H%M%S)
    
    log "Creating backup before rollback: $component"
    
    case "$component" in
        "frontend")
            # Backup current frontend
            local s3_bucket="${PROJECT_NAME}-${ENVIRONMENT}-frontend-hosting"
            aws s3 sync "s3://$s3_bucket" "s3://$BACKUP_BUCKET/frontend/pre-rollback-$timestamp/" --delete
            ;;
        "backend")
            # Backup current Lambda functions
            local functions=$(aws lambda list-functions --query "Functions[?starts_with(FunctionName, '${PROJECT_NAME}-${ENVIRONMENT}')].FunctionName" --output text)
            for function in $functions; do
                aws lambda get-function --function-name "$function" --query 'Code.Location' --output text | \
                xargs curl -s -o "/tmp/${function}.zip"
                aws s3 cp "/tmp/${function}.zip" "s3://$BACKUP_BUCKET/backend/pre-rollback-$timestamp/${function}.zip"
                rm "/tmp/${function}.zip"
            done
            ;;
        "database")
            # Create database snapshot
            local db_instance="${PROJECT_NAME}-${ENVIRONMENT}-db"
            local snapshot_id="${db_instance}-pre-rollback-$timestamp"
            aws rds create-db-snapshot \
                --db-instance-identifier "$db_instance" \
                --db-snapshot-identifier "$snapshot_id"
            
            # Wait for snapshot to complete
            log "Waiting for database snapshot to complete..."
            aws rds wait db-snapshot-completed --db-snapshot-identifier "$snapshot_id"
            ;;
    esac
    
    success "Backup created for $component"
}

# Rollback frontend
rollback_frontend() {
    local backup_path="$1"
    
    log "Rolling back frontend from: $backup_path"
    
    # Validate backup path
    if ! aws s3 ls "$backup_path" &>/dev/null; then
        error "Backup path not found: $backup_path"
        exit 1
    fi
    
    # Create backup of current state
    create_backup "frontend"
    
    # Restore from backup
    local s3_bucket="${PROJECT_NAME}-${ENVIRONMENT}-frontend-hosting"
    aws s3 sync "$backup_path" "s3://$s3_bucket/" --delete
    
    # Invalidate CloudFront cache if configured
    local cloudfront_distribution_id="${CLOUDFRONT_DISTRIBUTION_ID:-}"
    if [[ -n "$cloudfront_distribution_id" ]]; then
        log "Invalidating CloudFront cache..."
        aws cloudfront create-invalidation \
            --distribution-id "$cloudfront_distribution_id" \
            --paths "/*" > /dev/null
    fi
    
    success "Frontend rollback completed"
}

# Rollback backend
rollback_backend() {
    local backup_path="$1"
    
    log "Rolling back backend from: $backup_path"
    
    # Validate backup path
    if ! aws s3 ls "$backup_path" &>/dev/null; then
        error "Backup path not found: $backup_path"
        exit 1
    fi
    
    # Create backup of current state
    create_backup "backend"
    
    # Get list of Lambda functions to restore
    local functions=$(aws lambda list-functions --query "Functions[?starts_with(FunctionName, '${PROJECT_NAME}-${ENVIRONMENT}')].FunctionName" --output text)
    
    for function in $functions; do
        local backup_file="$backup_path/${function}.zip"
        
        # Check if backup exists for this function
        if aws s3 ls "$backup_file" &>/dev/null; then
            log "Restoring function: $function"
            
            # Download backup
            aws s3 cp "$backup_file" "/tmp/${function}.zip"
            
            # Update function code
            aws lambda update-function-code \
                --function-name "$function" \
                --zip-file "fileb:///tmp/${function}.zip" > /dev/null
            
            # Clean up
            rm "/tmp/${function}.zip"
            
            success "Restored function: $function"
        else
            warning "No backup found for function: $function"
        fi
    done
    
    success "Backend rollback completed"
}

# Rollback database
rollback_database() {
    local snapshot_id="$1"
    
    log "Rolling back database from snapshot: $snapshot_id"
    
    # Validate snapshot exists
    if ! aws rds describe-db-snapshots --db-snapshot-identifier "$snapshot_id" &>/dev/null; then
        error "Database snapshot not found: $snapshot_id"
        exit 1
    fi
    
    # Create backup of current state
    create_backup "database"
    
    local db_instance="${PROJECT_NAME}-${ENVIRONMENT}-db"
    local temp_instance="${db_instance}-temp-$(date +%s)"
    
    warning "Database rollback requires downtime!"
    read -p "Continue with database rollback? (yes/no): " confirm
    if [[ "$confirm" != "yes" ]]; then
        log "Database rollback cancelled"
        exit 0
    fi
    
    # Restore snapshot to temporary instance
    log "Restoring snapshot to temporary instance..."
    aws rds restore-db-instance-from-db-snapshot \
        --db-instance-identifier "$temp_instance" \
        --db-snapshot-identifier "$snapshot_id"
    
    # Wait for temporary instance to be available
    log "Waiting for temporary instance to be available..."
    aws rds wait db-instance-available --db-instance-identifier "$temp_instance"
    
    # Stop current instance
    log "Stopping current database instance..."
    aws rds stop-db-instance --db-instance-identifier "$db_instance"
    aws rds wait db-instance-stopped --db-instance-identifier "$db_instance"
    
    # Rename instances
    log "Swapping database instances..."
    local backup_instance="${db_instance}-backup-$(date +%s)"
    
    # Rename current to backup
    aws rds modify-db-instance \
        --db-instance-identifier "$db_instance" \
        --new-db-instance-identifier "$backup_instance" \
        --apply-immediately
    
    # Rename temp to current
    aws rds modify-db-instance \
        --db-instance-identifier "$temp_instance" \
        --new-db-instance-identifier "$db_instance" \
        --apply-immediately
    
    # Wait for rename to complete
    aws rds wait db-instance-available --db-instance-identifier "$db_instance"
    
    success "Database rollback completed"
    log "Previous database instance renamed to: $backup_instance"
}

# Rollback infrastructure
rollback_infrastructure() {
    local terraform_state_backup="$1"
    
    log "Rolling back infrastructure from state: $terraform_state_backup"
    
    warning "Infrastructure rollback is complex and may cause downtime!"
    read -p "Continue with infrastructure rollback? (yes/no): " confirm
    if [[ "$confirm" != "yes" ]]; then
        log "Infrastructure rollback cancelled"
        exit 0
    fi
    
    cd "infrastructure/terraform"
    
    # Backup current state
    local current_state_backup="terraform-state-backup-$(date +%Y%m%d-%H%M%S).tfstate"
    aws s3 cp "s3://${PROJECT_NAME}-${ENVIRONMENT}-terraform-state/${ENVIRONMENT}/terraform.tfstate" \
        "s3://$BACKUP_BUCKET/infrastructure/$current_state_backup"
    
    # Restore previous state
    aws s3 cp "$terraform_state_backup" \
        "s3://${PROJECT_NAME}-${ENVIRONMENT}-terraform-state/${ENVIRONMENT}/terraform.tfstate"
    
    # Refresh and plan
    terraform init
    terraform refresh
    terraform plan
    
    cd - > /dev/null
    
    warning "Infrastructure state restored. Review the plan and apply if needed."
    success "Infrastructure rollback preparation completed"
}

# Health check after rollback
health_check() {
    local component="$1"
    
    log "Performing health check after $component rollback..."
    
    case "$component" in
        "frontend")
            local website_url="https://${PROJECT_NAME}-${ENVIRONMENT}-frontend-hosting.s3-website-${AWS_REGION}.amazonaws.com"
            if curl -s -f "$website_url" > /dev/null; then
                success "Frontend health check passed"
            else
                error "Frontend health check failed"
                return 1
            fi
            ;;
        "backend")
            local api_id=$(aws apigateway get-rest-apis --query "items[?name=='${PROJECT_NAME}-${ENVIRONMENT}-api'].id" --output text)
            local api_url="https://$api_id.execute-api.$AWS_REGION.amazonaws.com/$ENVIRONMENT/health"
            if curl -s -f "$api_url" > /dev/null; then
                success "Backend health check passed"
            else
                error "Backend health check failed"
                return 1
            fi
            ;;
        "database")
            local db_endpoint=$(aws rds describe-db-instances \
                --db-instance-identifier "${PROJECT_NAME}-${ENVIRONMENT}-db" \
                --query 'DBInstances[0].Endpoint.Address' \
                --output text)
            if [[ -n "$db_endpoint" ]]; then
                success "Database health check passed"
            else
                error "Database health check failed"
                return 1
            fi
            ;;
    esac
}

# Main rollback function
main() {
    local component="$1"
    local backup_identifier="$2"
    
    log "Starting rollback for HealthConnect AI..."
    log "Component: $component"
    log "Environment: $ENVIRONMENT"
    
    # Confirm rollback
    warning "You are about to rollback $component in $ENVIRONMENT environment!"
    read -p "Are you sure you want to continue? (yes/no): " confirm
    if [[ "$confirm" != "yes" ]]; then
        log "Rollback cancelled"
        exit 0
    fi
    
    case "$component" in
        "frontend")
            rollback_frontend "s3://$BACKUP_BUCKET/frontend/$backup_identifier/"
            health_check "frontend"
            ;;
        "backend")
            rollback_backend "s3://$BACKUP_BUCKET/backend/$backup_identifier/"
            health_check "backend"
            ;;
        "database")
            rollback_database "$backup_identifier"
            health_check "database"
            ;;
        "infrastructure")
            rollback_infrastructure "s3://$BACKUP_BUCKET/infrastructure/$backup_identifier"
            ;;
        *)
            error "Unknown component: $component"
            exit 1
            ;;
    esac
    
    success "Rollback completed successfully!"
}

# Handle command line arguments
case "${1:-}" in
    "list")
        list_backups
        ;;
    "frontend"|"backend"|"database"|"infrastructure")
        if [[ $# -lt 2 ]]; then
            error "Backup identifier required for rollback"
            echo "Usage: $0 $1 <backup_identifier>"
            exit 1
        fi
        main "$1" "$2"
        ;;
    "--help"|"-h"|"")
        echo "Usage: $0 <command> [options]"
        echo
        echo "Commands:"
        echo "  list                           List available backups"
        echo "  frontend <backup_identifier>   Rollback frontend"
        echo "  backend <backup_identifier>    Rollback backend"
        echo "  database <snapshot_id>         Rollback database"
        echo "  infrastructure <state_backup>  Rollback infrastructure"
        echo
        echo "Environment Variables:"
        echo "  ENVIRONMENT                    Deployment environment (default: dev)"
        echo "  AWS_REGION                     AWS region (default: us-east-1)"
        echo "  CLOUDFRONT_DISTRIBUTION_ID     CloudFront distribution ID (optional)"
        exit 0
        ;;
    *)
        error "Unknown command: $1"
        echo "Use '$0 --help' for usage information"
        exit 1
        ;;
esac
