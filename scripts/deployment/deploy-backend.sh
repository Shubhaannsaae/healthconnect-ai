#!/bin/bash

# HealthConnect AI - Backend Deployment Script
# Production-grade backend deployment with Lambda and API Gateway
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
LAMBDA_RUNTIME="python3.11"
LAMBDA_TIMEOUT=30
LAMBDA_MEMORY=512

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
    if [[ ! -f "backend/requirements.txt" ]]; then
        error "backend/requirements.txt not found. Please run this script from the project root."
        exit 1
    fi
    
    # Check required tools
    local required_tools=("python3" "pip3" "aws" "zip")
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
    
    # Check Python version
    local python_version=$(python3 --version | awk '{print $2}')
    if [[ "$(printf '%s\n' "3.9" "$python_version" | sort -V | head -n1)" != "3.9" ]]; then
        error "Python 3.9+ required, found $python_version"
        exit 1
    fi
    
    success "Prerequisites check passed"
}

# Install dependencies and create deployment package
create_deployment_package() {
    local function_name="$1"
    local function_dir="backend/functions/$function_name"
    local package_dir="build/$function_name"
    
    log "Creating deployment package for $function_name..."
    
    # Clean and create build directory
    rm -rf "$package_dir"
    mkdir -p "$package_dir"
    
    # Copy function code
    cp -r "$function_dir"/* "$package_dir/"
    
    # Copy shared modules
    if [[ -d "backend/shared" ]]; then
        cp -r backend/shared "$package_dir/"
    fi
    
    # Install dependencies
    if [[ -f "$function_dir/requirements.txt" ]]; then
        pip3 install -r "$function_dir/requirements.txt" -t "$package_dir/"
    fi
    
    # Install common requirements
    pip3 install -r backend/requirements.txt -t "$package_dir/"
    
    # Remove unnecessary files
    find "$package_dir" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "$package_dir" -type f -name "*.pyc" -delete 2>/dev/null || true
    find "$package_dir" -type f -name "*.pyo" -delete 2>/dev/null || true
    find "$package_dir" -type f -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
    
    # Create deployment zip
    cd "$package_dir"
    zip -r "../${function_name}.zip" . -q
    cd - > /dev/null
    
    success "Deployment package created: build/${function_name}.zip"
}

# Deploy Lambda function
deploy_lambda_function() {
    local function_name="$1"
    local handler="$2"
    local description="$3"
    local full_function_name="${PROJECT_NAME}-${ENVIRONMENT}-${function_name}"
    local role_arn="arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/${PROJECT_NAME}-${ENVIRONMENT}-lambda-role"
    local package_file="build/${function_name}.zip"
    
    log "Deploying Lambda function: $full_function_name"
    
    # Check if function exists
    if aws lambda get-function --function-name "$full_function_name" &>/dev/null; then
        # Update existing function
        log "Updating existing function..."
        
        # Update function code
        aws lambda update-function-code \
            --function-name "$full_function_name" \
            --zip-file "fileb://$package_file" \
            --publish > /dev/null
        
        # Update function configuration
        aws lambda update-function-configuration \
            --function-name "$full_function_name" \
            --runtime "$LAMBDA_RUNTIME" \
            --handler "$handler" \
            --timeout "$LAMBDA_TIMEOUT" \
            --memory-size "$LAMBDA_MEMORY" \
            --environment "Variables={
                ENVIRONMENT=$ENVIRONMENT,
                PROJECT_NAME=$PROJECT_NAME,
                AWS_REGION=$AWS_REGION,
                LOG_LEVEL=INFO
            }" > /dev/null
        
    else
        # Create new function
        log "Creating new function..."
        
        aws lambda create-function \
            --function-name "$full_function_name" \
            --runtime "$LAMBDA_RUNTIME" \
            --role "$role_arn" \
            --handler "$handler" \
            --code "ZipFile=fileb://$package_file" \
            --description "$description" \
            --timeout "$LAMBDA_TIMEOUT" \
            --memory-size "$LAMBDA_MEMORY" \
            --environment "Variables={
                ENVIRONMENT=$ENVIRONMENT,
                PROJECT_NAME=$PROJECT_NAME,
                AWS_REGION=$AWS_REGION,
                LOG_LEVEL=INFO
            }" \
            --tags "Project=$PROJECT_NAME,Environment=$ENVIRONMENT" > /dev/null
    fi
    
    # Wait for function to be active
    aws lambda wait function-active --function-name "$full_function_name"
    
    success "Lambda function deployed: $full_function_name"
}

# Configure API Gateway
configure_api_gateway() {
    log "Configuring API Gateway..."
    
    local api_name="${PROJECT_NAME}-${ENVIRONMENT}-api"
    
    # Get API ID
    local api_id=$(aws apigateway get-rest-apis \
        --query "items[?name=='$api_name'].id" \
        --output text)
    
    if [[ -z "$api_id" || "$api_id" == "None" ]]; then
        error "API Gateway $api_name not found"
        exit 1
    fi
    
    # Get root resource ID
    local root_resource_id=$(aws apigateway get-resources \
        --rest-api-id "$api_id" \
        --query 'items[?path==`/`].id' \
        --output text)
    
    # Define API resources and methods
    local -A api_resources=(
        ["health"]="health"
        ["auth"]="auth"
        ["devices"]="devices"
        ["consultations"]="consultations"
        ["alerts"]="alerts"
    )
    
    # Create resources and integrate with Lambda functions
    for resource_path in "${!api_resources[@]}"; do
        local lambda_function="${api_resources[$resource_path]}"
        local full_function_name="${PROJECT_NAME}-${ENVIRONMENT}-${lambda_function}"
        
        # Check if resource exists
        local resource_id=$(aws apigateway get-resources \
            --rest-api-id "$api_id" \
            --query "items[?pathPart=='$resource_path'].id" \
            --output text)
        
        if [[ -z "$resource_id" || "$resource_id" == "None" ]]; then
            # Create resource
            resource_id=$(aws apigateway create-resource \
                --rest-api-id "$api_id" \
                --parent-id "$root_resource_id" \
                --path-part "$resource_path" \
                --query 'id' \
                --output text)
            
            log "Created API resource: /$resource_path"
        fi
        
        # Configure methods (GET, POST, PUT, DELETE)
        local methods=("GET" "POST" "PUT" "DELETE" "OPTIONS")
        
        for method in "${methods[@]}"; do
            # Check if method exists
            if ! aws apigateway get-method \
                --rest-api-id "$api_id" \
                --resource-id "$resource_id" \
                --http-method "$method" &>/dev/null; then
                
                # Create method
                aws apigateway put-method \
                    --rest-api-id "$api_id" \
                    --resource-id "$resource_id" \
                    --http-method "$method" \
                    --authorization-type "AWS_IAM" \
                    --api-key-required > /dev/null
                
                # Create integration
                local lambda_arn="arn:aws:lambda:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):function:$full_function_name"
                
                aws apigateway put-integration \
                    --rest-api-id "$api_id" \
                    --resource-id "$resource_id" \
                    --http-method "$method" \
                    --type "AWS_PROXY" \
                    --integration-http-method "POST" \
                    --uri "arn:aws:apigateway:$AWS_REGION:lambda:path/2015-03-31/functions/$lambda_arn/invocations" > /dev/null
                
                # Add Lambda permission
                aws lambda add-permission \
                    --function-name "$full_function_name" \
                    --statement-id "apigateway-$method-$resource_path" \
                    --action "lambda:InvokeFunction" \
                    --principal "apigateway.amazonaws.com" \
                    --source-arn "arn:aws:execute-api:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):$api_id/*/*" \
                    2>/dev/null || true
                
                log "Configured $method method for /$resource_path"
            fi
        done
    done
    
    success "API Gateway configuration completed"
}

# Deploy API Gateway stage
deploy_api_stage() {
    log "Deploying API Gateway stage..."
    
    local api_name="${PROJECT_NAME}-${ENVIRONMENT}-api"
    local stage_name="$ENVIRONMENT"
    
    # Get API ID
    local api_id=$(aws apigateway get-rest-apis \
        --query "items[?name=='$api_name'].id" \
        --output text)
    
    # Create deployment
    local deployment_id=$(aws apigateway create-deployment \
        --rest-api-id "$api_id" \
        --stage-name "$stage_name" \
        --stage-description "Deployment for $ENVIRONMENT environment" \
        --description "Automated deployment $(date)" \
        --query 'id' \
        --output text)
    
    # Configure stage settings
    aws apigateway update-stage \
        --rest-api-id "$api_id" \
        --stage-name "$stage_name" \
        --patch-ops '[
            {
                "op": "replace",
                "path": "/throttle/rateLimit",
                "value": "1000"
            },
            {
                "op": "replace",
                "path": "/throttle/burstLimit",
                "value": "2000"
            },
            {
                "op": "replace",
                "path": "/logging/loglevel",
                "value": "INFO"
            },
            {
                "op": "replace",
                "path": "/logging/dataTrace",
                "value": "true"
            }
        ]' > /dev/null
    
    local api_url="https://$api_id.execute-api.$AWS_REGION.amazonaws.com/$stage_name"
    
    success "API deployed to: $api_url"
    echo "$api_url" > "build/api-url.txt"
}

# Run tests
run_tests() {
    log "Running backend tests..."
    
    cd backend
    
    # Create virtual environment for testing
    python3 -m venv test_env
    source test_env/bin/activate
    
    # Install test dependencies
    pip install -r requirements.txt
    pip install pytest pytest-cov pytest-mock
    
    # Run tests
    if pytest tests/ --cov=functions --cov-report=html --cov-report=term; then
        success "Tests passed"
    else
        error "Tests failed"
        deactivate
        cd ..
        exit 1
    fi
    
    deactivate
    cd ..
}

# Security scan
run_security_scan() {
    log "Running security scan..."
    
    cd backend
    
    # Check for known vulnerabilities
    pip3 install safety
    if safety check -r requirements.txt; then
        success "Security scan passed"
    else
        warning "Security vulnerabilities found. Please review."
        if [[ "$ENVIRONMENT" == "production" ]]; then
            error "Cannot deploy to production with security vulnerabilities"
            exit 1
        fi
    fi
    
    cd ..
}

# Health check
health_check() {
    log "Performing post-deployment health check..."
    
    local api_url=$(cat "build/api-url.txt" 2>/dev/null || echo "")
    
    if [[ -z "$api_url" ]]; then
        error "API URL not found"
        return 1
    fi
    
    # Test health endpoint
    local health_url="$api_url/health"
    
    log "Checking API health: $health_url"
    
    local max_attempts=5
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -s -f "$health_url" > /dev/null; then
            success "API health check passed"
            return 0
        else
            warning "Attempt $attempt/$max_attempts failed, retrying in 10 seconds..."
            sleep 10
            ((attempt++))
        fi
    done
    
    error "API health check failed after $max_attempts attempts"
    return 1
}

# Main deployment function
main() {
    log "Starting backend deployment for HealthConnect AI..."
    log "Environment: $ENVIRONMENT"
    
    # Trap errors and cleanup
    trap 'error "Deployment failed"; exit 1' ERR
    
    check_prerequisites
    
    # Create build directory
    mkdir -p build
    
    # Skip tests in development if requested
    if [[ "${SKIP_TESTS:-false}" != "true" ]]; then
        run_tests
    fi
    
    run_security_scan
    
    # Define Lambda functions to deploy
    local -A lambda_functions=(
        ["health"]="lambda_function.lambda_handler"
        ["auth"]="lambda_function.lambda_handler"
        ["devices"]="lambda_function.lambda_handler"
        ["consultations"]="lambda_function.lambda_handler"
        ["alerts"]="lambda_function.lambda_handler"
    )
    
    # Deploy each Lambda function
    for function_name in "${!lambda_functions[@]}"; do
        local handler="${lambda_functions[$function_name]}"
        create_deployment_package "$function_name"
        deploy_lambda_function "$function_name" "$handler" "HealthConnect AI $function_name service"
    done
    
    configure_api_gateway
    deploy_api_stage
    
    # Perform health check
    if health_check; then
        success "Backend deployment completed successfully!"
        
        local api_url=$(cat "build/api-url.txt")
        log "Deployment summary:"
        log "- Environment: $ENVIRONMENT"
        log "- API URL: $api_url"
        log "- Functions deployed: ${#lambda_functions[@]}"
        log "- Runtime: $LAMBDA_RUNTIME"
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
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -e, --environment ENV    Deployment environment (dev/staging/production)"
            echo "  --skip-tests            Skip running tests"
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
