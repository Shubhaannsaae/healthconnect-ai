#!/bin/bash

# HealthConnect AI - Frontend Deployment Script
# Production-grade frontend deployment with CI/CD integration
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
BUILD_DIR="frontend/dist"
S3_BUCKET="${PROJECT_NAME}-${ENVIRONMENT}-frontend-hosting"
CLOUDFRONT_DISTRIBUTION_ID="${CLOUDFRONT_DISTRIBUTION_ID:-}"
AWS_REGION="${AWS_REGION:-us-east-1}"

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
    
    # Check if we're in the right directory
    if [[ ! -f "frontend/package.json" ]]; then
        error "frontend/package.json not found. Please run this script from the project root."
        exit 1
    fi
    
    # Check required tools
    local required_tools=("node" "npm" "aws")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            error "$tool is not installed or not in PATH"
            exit 1
        fi
    done
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS credentials not configured. Please run 'aws configure'"
        exit 1
    fi
    
    # Check if S3 bucket exists
    if ! aws s3api head-bucket --bucket "$S3_BUCKET" 2>/dev/null; then
        error "S3 bucket $S3_BUCKET does not exist"
        exit 1
    fi
    
    success "Prerequisites check passed"
}

# Install dependencies
install_dependencies() {
    log "Installing frontend dependencies..."
    
    cd frontend
    
    # Clean install for production builds
    if [[ "$ENVIRONMENT" == "production" ]]; then
        rm -rf node_modules package-lock.json
        npm ci --production=false
    else
        npm install
    fi
    
    cd ..
    success "Dependencies installed successfully"
}

# Run tests
run_tests() {
    log "Running frontend tests..."
    
    cd frontend
    
    # Run linting
    if npm run lint --if-present; then
        success "Linting passed"
    else
        error "Linting failed"
        exit 1
    fi
    
    # Run type checking
    if npm run type-check --if-present; then
        success "Type checking passed"
    else
        error "Type checking failed"
        exit 1
    fi
    
    # Run unit tests
    if npm test -- --coverage --watchAll=false; then
        success "Tests passed"
    else
        error "Tests failed"
        exit 1
    fi
    
    cd ..
}

# Build application
build_application() {
    log "Building frontend application..."
    
    cd frontend
    
    # Set environment variables for build
    export NODE_ENV="production"
    export REACT_APP_ENVIRONMENT="$ENVIRONMENT"
    export REACT_APP_API_URL="${API_URL:-https://api-${ENVIRONMENT}.healthconnect-ai.com}"
    export REACT_APP_WS_URL="${WS_URL:-wss://ws-${ENVIRONMENT}.healthconnect-ai.com}"
    
    # Build the application
    npm run build
    
    # Verify build output
    if [[ ! -d "dist" ]] && [[ ! -d "build" ]]; then
        error "Build output directory not found"
        exit 1
    fi
    
    # Use the correct build directory
    if [[ -d "build" ]]; then
        BUILD_DIR="frontend/build"
    fi
    
    cd ..
    success "Application built successfully"
}

# Optimize build
optimize_build() {
    log "Optimizing build for deployment..."
    
    # Compress static assets
    find "$BUILD_DIR" -type f \( -name "*.js" -o -name "*.css" -o -name "*.html" \) -exec gzip -9 -k {} \;
    
    # Generate manifest for cache busting
    cat > "$BUILD_DIR/manifest.json" << EOF
{
    "name": "HealthConnect AI",
    "short_name": "HealthConnect",
    "description": "Advanced AI-powered healthcare platform",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#ffffff",
    "theme_color": "#0ea5e9",
    "icons": [
        {
            "src": "/icons/icon-192x192.png",
            "sizes": "192x192",
            "type": "image/png"
        },
        {
            "src": "/icons/icon-512x512.png",
            "sizes": "512x512",
            "type": "image/png"
        }
    ]
}
EOF
    
    success "Build optimization completed"
}

# Deploy to S3
deploy_to_s3() {
    log "Deploying to S3 bucket: $S3_BUCKET"
    
    # Sync files to S3 with appropriate cache headers
    aws s3 sync "$BUILD_DIR" "s3://$S3_BUCKET" \
        --delete \
        --cache-control "public, max-age=31536000" \
        --exclude "*.html" \
        --exclude "service-worker.js" \
        --exclude "manifest.json"
    
    # Upload HTML files with no-cache headers
    aws s3 sync "$BUILD_DIR" "s3://$S3_BUCKET" \
        --cache-control "no-cache, no-store, must-revalidate" \
        --include "*.html" \
        --include "service-worker.js" \
        --include "manifest.json"
    
    # Set content encoding for compressed files
    aws s3 cp "$BUILD_DIR" "s3://$S3_BUCKET" \
        --recursive \
        --exclude "*" \
        --include "*.gz" \
        --content-encoding gzip \
        --metadata-directive REPLACE
    
    success "Deployment to S3 completed"
}

# Configure S3 bucket for static website hosting
configure_s3_website() {
    log "Configuring S3 bucket for static website hosting..."
    
    # Create website configuration
    cat > /tmp/website-config.json << EOF
{
    "IndexDocument": {
        "Suffix": "index.html"
    },
    "ErrorDocument": {
        "Key": "index.html"
    }
}
EOF
    
    # Apply website configuration
    aws s3api put-bucket-website \
        --bucket "$S3_BUCKET" \
        --website-configuration file:///tmp/website-config.json
    
    # Clean up
    rm /tmp/website-config.json
    
    success "S3 website configuration applied"
}

# Invalidate CloudFront cache
invalidate_cloudfront() {
    if [[ -n "$CLOUDFRONT_DISTRIBUTION_ID" ]]; then
        log "Invalidating CloudFront cache..."
        
        local invalidation_id=$(aws cloudfront create-invalidation \
            --distribution-id "$CLOUDFRONT_DISTRIBUTION_ID" \
            --paths "/*" \
            --query 'Invalidation.Id' \
            --output text)
        
        log "CloudFront invalidation created: $invalidation_id"
        
        # Wait for invalidation to complete (optional)
        if [[ "${WAIT_FOR_INVALIDATION:-false}" == "true" ]]; then
            log "Waiting for CloudFront invalidation to complete..."
            aws cloudfront wait invalidation-completed \
                --distribution-id "$CLOUDFRONT_DISTRIBUTION_ID" \
                --id "$invalidation_id"
            success "CloudFront invalidation completed"
        fi
    else
        warning "CloudFront distribution ID not provided, skipping cache invalidation"
    fi
}

# Run security scan
run_security_scan() {
    log "Running security scan on build..."
    
    cd frontend
    
    # Run npm audit
    if npm audit --audit-level high; then
        success "Security scan passed"
    else
        warning "Security vulnerabilities found. Please review and fix."
        if [[ "$ENVIRONMENT" == "production" ]]; then
            error "Cannot deploy to production with security vulnerabilities"
            exit 1
        fi
    fi
    
    cd ..
}

# Generate deployment report
generate_deployment_report() {
    log "Generating deployment report..."
    
    local report_file="deployment-report-$(date +%Y%m%d-%H%M%S).json"
    local build_size=$(du -sh "$BUILD_DIR" | cut -f1)
    local file_count=$(find "$BUILD_DIR" -type f | wc -l)
    
    cat > "$report_file" << EOF
{
    "deployment": {
        "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
        "environment": "$ENVIRONMENT",
        "project": "$PROJECT_NAME",
        "version": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
        "branch": "$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')",
        "build_size": "$build_size",
        "file_count": $file_count,
        "s3_bucket": "$S3_BUCKET",
        "cloudfront_distribution": "$CLOUDFRONT_DISTRIBUTION_ID",
        "deployed_by": "$(whoami)",
        "status": "success"
    }
}
EOF
    
    success "Deployment report generated: $report_file"
}

# Rollback function
rollback_deployment() {
    log "Rolling back deployment..."
    
    # This would restore the previous version from backup
    # Implementation depends on your backup strategy
    warning "Rollback functionality not implemented yet"
}

# Health check
health_check() {
    log "Performing post-deployment health check..."
    
    local website_url="https://$S3_BUCKET.s3-website-$AWS_REGION.amazonaws.com"
    if [[ -n "$CLOUDFRONT_DISTRIBUTION_ID" ]]; then
        # Get CloudFront domain name
        local cloudfront_domain=$(aws cloudfront get-distribution \
            --id "$CLOUDFRONT_DISTRIBUTION_ID" \
            --query 'Distribution.DomainName' \
            --output text)
        website_url="https://$cloudfront_domain"
    fi
    
    log "Checking website availability: $website_url"
    
    local max_attempts=5
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -s -f "$website_url" > /dev/null; then
            success "Website is accessible"
            return 0
        else
            warning "Attempt $attempt/$max_attempts failed, retrying in 10 seconds..."
            sleep 10
            ((attempt++))
        fi
    done
    
    error "Website health check failed after $max_attempts attempts"
    return 1
}

# Main deployment function
main() {
    log "Starting frontend deployment for HealthConnect AI..."
    log "Environment: $ENVIRONMENT"
    log "S3 Bucket: $S3_BUCKET"
    
    # Trap errors and cleanup
    trap 'error "Deployment failed"; exit 1' ERR
    
    check_prerequisites
    install_dependencies
    
    # Skip tests in development if requested
    if [[ "${SKIP_TESTS:-false}" != "true" ]]; then
        run_tests
    fi
    
    run_security_scan
    build_application
    optimize_build
    configure_s3_website
    deploy_to_s3
    invalidate_cloudfront
    
    # Perform health check
    if health_check; then
        generate_deployment_report
        success "Frontend deployment completed successfully!"
        
        log "Deployment summary:"
        log "- Environment: $ENVIRONMENT"
        log "- S3 Bucket: $S3_BUCKET"
        log "- Build size: $(du -sh "$BUILD_DIR" | cut -f1)"
        log "- Files deployed: $(find "$BUILD_DIR" -type f | wc -l)"
        
        if [[ -n "$CLOUDFRONT_DISTRIBUTION_ID" ]]; then
            local cloudfront_domain=$(aws cloudfront get-distribution \
                --id "$CLOUDFRONT_DISTRIBUTION_ID" \
                --query 'Distribution.DomainName' \
                --output text)
            log "- Website URL: https://$cloudfront_domain"
        else
            log "- Website URL: https://$S3_BUCKET.s3-website-$AWS_REGION.amazonaws.com"
        fi
    else
        error "Deployment completed but health check failed"
        exit 1
    fi
}

# Handle command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --environment|-e)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --skip-tests)
            SKIP_TESTS="true"
            shift
            ;;
        --wait-for-invalidation)
            WAIT_FOR_INVALIDATION="true"
            shift
            ;;
        --rollback)
            rollback_deployment
            exit 0
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -e, --environment ENV    Deployment environment (dev/staging/production)"
            echo "  --skip-tests            Skip running tests"
            echo "  --wait-for-invalidation Wait for CloudFront invalidation to complete"
            echo "  --rollback              Rollback to previous deployment"
            echo "  -h, --help              Show this help message"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run main function
main "$@"
