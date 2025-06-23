#!/bin/bash

# HealthConnect AI - Infrastructure Deployment Script
# Production-grade infrastructure deployment using Terraform
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
TERRAFORM_DIR="infrastructure/terraform"
STATE_BUCKET="${PROJECT_NAME}-${ENVIRONMENT}-terraform-state"

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

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check required tools
    local required_tools=("terraform" "aws" "jq")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            error "$tool is not installed or not in PATH"
            exit 1
        fi
    done
    
    # Check Terraform version
    local tf_version=$(terraform version -json | jq -r '.terraform_version')
    if [[ "$(printf '%s\n' "1.0.0" "$tf_version" | sort -V | head -n1)" != "1.0.0" ]]; then
        error "Terraform 1.0.0+ required, found $tf_version"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS credentials not configured. Please run 'aws configure'"
        exit 1
    fi
    
    # Check if Terraform directory exists
    if [[ ! -d "$TERRAFORM_DIR" ]]; then
        error "Terraform directory not found: $TERRAFORM_DIR"
        exit 1
    fi
    
    success "Prerequisites check passed"
}

# Initialize Terraform backend
init_terraform_backend() {
    log "Initializing Terraform backend..."
    
    cd "$TERRAFORM_DIR"
    
    # Create backend configuration
    cat > backend.tf << EOF
terraform {
  backend "s3" {
    bucket         = "$STATE_BUCKET"
    key            = "$ENVIRONMENT/terraform.tfstate"
    region         = "$AWS_REGION"
    encrypt        = true
    dynamodb_table = "${PROJECT_NAME}-${ENVIRONMENT}-terraform-locks"
  }
}
EOF
    
    # Initialize Terraform
    terraform init -upgrade
    
    cd - > /dev/null
    success "Terraform backend initialized"
}

# Plan infrastructure changes
plan_infrastructure() {
    log "Planning infrastructure changes..."
    
    cd "$TERRAFORM_DIR"
    
    # Create terraform.tfvars
    cat > terraform.tfvars << EOF
project_name = "$PROJECT_NAME"
environment = "$ENVIRONMENT"
aws_region = "$AWS_REGION"

# VPC Configuration
vpc_cidr = "10.0.0.0/16"
availability_zones = ["${AWS_REGION}a", "${AWS_REGION}b", "${AWS_REGION}c"]

# Database Configuration
db_instance_class = "db.t3.micro"
db_allocated_storage = 20
db_backup_retention_period = 7

# Cache Configuration
redis_node_type = "cache.t3.micro"
redis_num_cache_nodes = 1

# Application Configuration
app_instance_type = "t3.small"
app_min_size = 1
app_max_size = 3
app_desired_capacity = 2

# Monitoring Configuration
enable_monitoring = true
log_retention_days = 30

# Security Configuration
enable_waf = true
enable_shield = false

# Tags
tags = {
  Project = "$PROJECT_NAME"
  Environment = "$ENVIRONMENT"
  ManagedBy = "Terraform"
  Owner = "HealthConnect AI Team"
}
EOF
    
    # Run terraform plan
    terraform plan -var-file=terraform.tfvars -out=tfplan
    
    cd - > /dev/null
    success "Infrastructure plan created"
}

# Apply infrastructure changes
apply_infrastructure() {
    log "Applying infrastructure changes..."
    
    cd "$TERRAFORM_DIR"
    
    # Confirm apply in production
    if [[ "$ENVIRONMENT" == "production" ]]; then
        echo
        warning "You are about to apply changes to PRODUCTION infrastructure!"
        read -p "Are you sure you want to continue? (yes/no): " confirm
        if [[ "$confirm" != "yes" ]]; then
            log "Infrastructure apply cancelled"
            exit 0
        fi
    fi
    
    # Apply changes
    terraform apply tfplan
    
    # Output important values
    terraform output -json > "../outputs/${ENVIRONMENT}-outputs.json"
    
    cd - > /dev/null
    success "Infrastructure changes applied successfully"
}

# Validate infrastructure
validate_infrastructure() {
    log "Validating infrastructure..."
    
    cd "$TERRAFORM_DIR"
    
    # Validate Terraform configuration
    terraform validate
    
    # Format check
    if ! terraform fmt -check; then
        warning "Terraform files are not properly formatted"
        terraform fmt
        log "Terraform files have been formatted"
    fi
    
    cd - > /dev/null
    success "Infrastructure validation completed"
}

# Generate infrastructure documentation
generate_documentation() {
    log "Generating infrastructure documentation..."
    
    cd "$TERRAFORM_DIR"
    
    # Create documentation directory
    mkdir -p "../docs"
    
    # Generate resource graph
    terraform graph > "../docs/infrastructure-graph.dot"
    
    # Generate outputs documentation
    cat > "../docs/infrastructure-outputs.md" << EOF
# Infrastructure Outputs - $ENVIRONMENT

Generated on: $(date)

## Network Resources
EOF
    
    # Add outputs to documentation
    terraform output -json | jq -r 'to_entries[] | "- **\(.key)**: \(.value.value)"' >> "../docs/infrastructure-outputs.md"
    
    cd - > /dev/null
    success "Infrastructure documentation generated"
}

# Destroy infrastructure (for development/testing)
destroy_infrastructure() {
    log "Destroying infrastructure..."
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        error "Cannot destroy production infrastructure using this script"
        exit 1
    fi
    
    cd "$TERRAFORM_DIR"
    
    warning "This will destroy ALL infrastructure in the $ENVIRONMENT environment!"
    read -p "Type 'destroy' to confirm: " confirm
    if [[ "$confirm" != "destroy" ]]; then
        log "Infrastructure destruction cancelled"
        exit 0
    fi
    
    terraform destroy -var-file=terraform.tfvars -auto-approve
    
    cd - > /dev/null
    success "Infrastructure destroyed"
}

# Main deployment function
main() {
    log "Starting infrastructure deployment for HealthConnect AI..."
    log "Environment: $ENVIRONMENT"
    log "AWS Region: $AWS_REGION"
    
    # Create outputs directory
    mkdir -p "infrastructure/outputs"
    
    check_prerequisites
    validate_infrastructure
    init_terraform_backend
    plan_infrastructure
    
    # Show plan summary
    log "Infrastructure plan summary:"
    cd "$TERRAFORM_DIR"
    terraform show -json tfplan | jq -r '.resource_changes[] | "\(.change.actions[0]) \(.address)"' | sort
    cd - > /dev/null
    
    apply_infrastructure
    generate_documentation
    
    success "Infrastructure deployment completed successfully!"
    
    # Display important outputs
    log "Important infrastructure outputs:"
    cd "$TERRAFORM_DIR"
    terraform output
    cd - > /dev/null
}

# Handle command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --environment|-e)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --plan-only)
            PLAN_ONLY="true"
            shift
            ;;
        --destroy)
            destroy_infrastructure
            exit 0
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -e, --environment ENV    Deployment environment (dev/staging/production)"
            echo "  --plan-only             Only run terraform plan, don't apply"
            echo "  --destroy               Destroy infrastructure (non-production only)"
            echo "  -h, --help              Show this help message"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run appropriate function
if [[ "${PLAN_ONLY:-false}" == "true" ]]; then
    check_prerequisites
    validate_infrastructure
    init_terraform_backend
    plan_infrastructure
    log "Plan-only mode completed. Review the plan and run without --plan-only to apply."
else
    main "$@"
fi
