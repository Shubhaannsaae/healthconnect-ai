#!/bin/bash

# HealthConnect AI - Environment Configuration Script
# Production-grade environment setup and configuration
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
CONFIG_DIR="./config"
ENV_FILE=".env"

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

# Create directory structure
create_directories() {
    log "Creating directory structure..."
    
    local directories=(
        "$CONFIG_DIR"
        "$CONFIG_DIR/environments"
        "logs"
        "data/uploads"
        "data/backups"
        "data/temp"
        "certificates"
        "scripts/logs"
    )
    
    for dir in "${directories[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            success "Created directory: $dir"
        else
            log "Directory already exists: $dir"
        fi
    done
}

# Generate environment configuration
generate_env_config() {
    log "Generating environment configuration..."
    
    # Read AWS configuration if it exists
    local user_pool_id=""
    local user_pool_client_id=""
    local aws_region="us-east-1"
    
    if [[ -f "aws-config.json" ]]; then
        user_pool_id=$(jq -r '.userPoolId // ""' aws-config.json)
        user_pool_client_id=$(jq -r '.userPoolClientId // ""' aws-config.json)
        aws_region=$(jq -r '.region // "us-east-1"' aws-config.json)
    fi
    
    # Generate random secrets
    local jwt_secret=$(openssl rand -hex 32)
    local encryption_key=$(openssl rand -hex 32)
    local api_key=$(openssl rand -hex 16)
    
    # Create .env file
    cat > "$ENV_FILE" << EOF
# HealthConnect AI Environment Configuration
# Generated on $(date)
# Environment: $ENVIRONMENT

# Application Configuration
NODE_ENV=$ENVIRONMENT
APP_NAME=$PROJECT_NAME
APP_VERSION=1.0.0
APP_PORT=3000
API_PORT=8000

# AWS Configuration
AWS_REGION=$aws_region
AWS_COGNITO_USER_POOL_ID=$user_pool_id
AWS_COGNITO_CLIENT_ID=$user_pool_client_id
AWS_S3_BUCKET_PREFIX=${PROJECT_NAME}-${ENVIRONMENT}

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=${PROJECT_NAME}_${ENVIRONMENT}
DB_USER=${PROJECT_NAME}_user
DB_PASSWORD=$(openssl rand -base64 32)

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=$(openssl rand -base64 32)

# Security Configuration
JWT_SECRET=$jwt_secret
ENCRYPTION_KEY=$encryption_key
API_KEY=$api_key
SESSION_SECRET=$(openssl rand -base64 32)

# CORS Configuration
CORS_ORIGIN=http://localhost:3000
CORS_CREDENTIALS=true

# Logging Configuration
LOG_LEVEL=info
LOG_FILE=logs/app.log
LOG_MAX_SIZE=10m
LOG_MAX_FILES=5

# Health Monitoring
HEALTH_CHECK_INTERVAL=30000
METRICS_ENABLED=true
MONITORING_ENDPOINT=/health

# Email Configuration (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_SECURE=false
SMTP_USER=
SMTP_PASSWORD=
EMAIL_FROM=noreply@healthconnect-ai.com

# WebSocket Configuration
WS_PORT=8080
WS_PATH=/ws

# File Upload Configuration
UPLOAD_MAX_SIZE=10485760
UPLOAD_ALLOWED_TYPES=image/jpeg,image/png,application/pdf
UPLOAD_DESTINATION=data/uploads

# Rate Limiting
RATE_LIMIT_WINDOW=900000
RATE_LIMIT_MAX_REQUESTS=100

# Feature Flags
FEATURE_DEVICE_SIMULATION=true
FEATURE_AI_INSIGHTS=true
FEATURE_VIDEO_CALLS=true
FEATURE_EMERGENCY_ALERTS=true

# Third-party Integrations
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=

# Development Configuration
DEV_MOCK_DATA=true
DEV_BYPASS_AUTH=false
DEV_VERBOSE_LOGGING=true
EOF
    
    success "Generated environment configuration: $ENV_FILE"
}

# Generate environment-specific configurations
generate_environment_configs() {
    log "Generating environment-specific configurations..."
    
    # Development configuration
    cat > "$CONFIG_DIR/environments/development.json" << EOF
{
  "environment": "development",
  "debug": true,
  "database": {
    "logging": true,
    "synchronize": true,
    "dropSchema": false
  },
  "cache": {
    "ttl": 300,
    "max": 100
  },
  "security": {
    "rateLimiting": {
      "enabled": false
    },
    "helmet": {
      "enabled": false
    }
  },
  "monitoring": {
    "enabled": true,
    "detailedMetrics": true
  }
}
EOF
    
    # Production configuration
    cat > "$CONFIG_DIR/environments/production.json" << EOF
{
  "environment": "production",
  "debug": false,
  "database": {
    "logging": false,
    "synchronize": false,
    "dropSchema": false
  },
  "cache": {
    "ttl": 3600,
    "max": 1000
  },
  "security": {
    "rateLimiting": {
      "enabled": true,
      "windowMs": 900000,
      "max": 100
    },
    "helmet": {
      "enabled": true,
      "contentSecurityPolicy": true,
      "hsts": true
    }
  },
  "monitoring": {
    "enabled": true,
    "detailedMetrics": false
  }
}
EOF
    
    # Testing configuration
    cat > "$CONFIG_DIR/environments/test.json" << EOF
{
  "environment": "test",
  "debug": false,
  "database": {
    "logging": false,
    "synchronize": true,
    "dropSchema": true
  },
  "cache": {
    "ttl": 60,
    "max": 50
  },
  "security": {
    "rateLimiting": {
      "enabled": false
    },
    "helmet": {
      "enabled": false
    }
  },
  "monitoring": {
    "enabled": false,
    "detailedMetrics": false
  }
}
EOF
    
    success "Generated environment-specific configurations"
}

# Generate SSL certificates for development
generate_ssl_certificates() {
    log "Generating SSL certificates for development..."
    
    if [[ "$ENVIRONMENT" == "development" ]]; then
        local cert_dir="certificates"
        
        # Generate private key
        openssl genrsa -out "$cert_dir/private-key.pem" 2048
        
        # Generate certificate signing request
        openssl req -new -key "$cert_dir/private-key.pem" -out "$cert_dir/csr.pem" -subj "/C=US/ST=CA/L=San Francisco/O=HealthConnect AI/CN=localhost"
        
        # Generate self-signed certificate
        openssl x509 -req -days 365 -in "$cert_dir/csr.pem" -signkey "$cert_dir/private-key.pem" -out "$cert_dir/certificate.pem"
        
        # Clean up CSR
        rm "$cert_dir/csr.pem"
        
        success "Generated SSL certificates for development"
    else
        log "Skipping SSL certificate generation for $ENVIRONMENT environment"
    fi
}

# Create logging configuration
create_logging_config() {
    log "Creating logging configuration..."
    
    cat > "$CONFIG_DIR/logging.json" << EOF
{
  "level": "info",
  "format": "combined",
  "datePattern": "YYYY-MM-DD",
  "zippedArchive": true,
  "maxSize": "20m",
  "maxFiles": "14d",
  "transports": [
    {
      "type": "console",
      "level": "debug",
      "colorize": true
    },
    {
      "type": "file",
      "level": "info",
      "filename": "logs/app.log",
      "handleExceptions": true,
      "maxsize": 5242880,
      "maxFiles": 5
    },
    {
      "type": "file",
      "level": "error",
      "filename": "logs/error.log",
      "handleExceptions": true,
      "maxsize": 5242880,
      "maxFiles": 5
    }
  ]
}
EOF
    
    success "Created logging configuration"
}

# Create database configuration
create_database_config() {
    log "Creating database configuration..."
    
    cat > "$CONFIG_DIR/database.json" << EOF
{
  "development": {
    "type": "postgres",
    "host": "localhost",
    "port": 5432,
    "username": "${PROJECT_NAME}_user",
    "database": "${PROJECT_NAME}_development",
    "synchronize": true,
    "logging": true,
    "entities": ["src/entities/**/*.ts"],
    "migrations": ["src/migrations/**/*.ts"],
    "subscribers": ["src/subscribers/**/*.ts"]
  },
  "test": {
    "type": "postgres",
    "host": "localhost",
    "port": 5432,
    "username": "${PROJECT_NAME}_test_user",
    "database": "${PROJECT_NAME}_test",
    "synchronize": true,
    "logging": false,
    "dropSchema": true,
    "entities": ["src/entities/**/*.ts"],
    "migrations": ["src/migrations/**/*.ts"],
    "subscribers": ["src/subscribers/**/*.ts"]
  },
  "production": {
    "type": "postgres",
    "host": "\${DB_HOST}",
    "port": "\${DB_PORT}",
    "username": "\${DB_USER}",
    "password": "\${DB_PASSWORD}",
    "database": "\${DB_NAME}",
    "synchronize": false,
    "logging": false,
    "entities": ["dist/entities/**/*.js"],
    "migrations": ["dist/migrations/**/*.js"],
    "subscribers": ["dist/subscribers/**/*.js"]
  }
}
EOF
    
    success "Created database configuration"
}

# Set up Git hooks
setup_git_hooks() {
    log "Setting up Git hooks..."
    
    if [[ -d ".git" ]]; then
        # Pre-commit hook
        cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Pre-commit hook for HealthConnect AI

echo "Running pre-commit checks..."

# Check for secrets in staged files
if git diff --cached --name-only | xargs grep -l "password\|secret\|key" 2>/dev/null; then
    echo "Warning: Potential secrets found in staged files"
    echo "Please review and remove any sensitive information"
    exit 1
fi

# Run linting
if command -v npm &> /dev/null; then
    npm run lint
fi

# Run tests
if command -v npm &> /dev/null; then
    npm test
fi

echo "Pre-commit checks passed"
EOF
        
        chmod +x .git/hooks/pre-commit
        
        success "Set up Git hooks"
    else
        warning "Not a Git repository. Skipping Git hooks setup."
    fi
}

# Validate configuration
validate_configuration() {
    log "Validating configuration..."
    
    local errors=0
    
    # Check required files
    local required_files=(
        "$ENV_FILE"
        "$CONFIG_DIR/environments/development.json"
        "$CONFIG_DIR/environments/production.json"
        "$CONFIG_DIR/logging.json"
        "$CONFIG_DIR/database.json"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            error "Required file not found: $file"
            ((errors++))
        fi
    done
    
    # Validate JSON files
    for json_file in "$CONFIG_DIR"/**/*.json; do
        if [[ -f "$json_file" ]]; then
            if ! jq empty "$json_file" 2>/dev/null; then
                error "Invalid JSON in file: $json_file"
                ((errors++))
            fi
        fi
    done
    
    if [[ $errors -eq 0 ]]; then
        success "Configuration validation passed"
    else
        error "Configuration validation failed with $errors errors"
        exit 1
    fi
}

# Main configuration function
main() {
    log "Starting environment configuration for HealthConnect AI..."
    
    create_directories
    generate_env_config
    generate_environment_configs
    generate_ssl_certificates
    create_logging_config
    create_database_config
    setup_git_hooks
    validate_configuration
    
    success "Environment configuration completed successfully!"
    
    log "Configuration summary:"
    log "- Environment: $ENVIRONMENT"
    log "- Configuration directory: $CONFIG_DIR"
    log "- Environment file: $ENV_FILE"
    log "- SSL certificates: certificates/ (development only)"
    
    warning "Important security notes:"
    warning "1. Update default passwords in $ENV_FILE"
    warning "2. Configure SMTP settings for email notifications"
    warning "3. Set up proper SSL certificates for production"
    warning "4. Review and update CORS settings"
    warning "5. Configure monitoring and alerting"
    
    log "Next steps:"
    log "1. Review and update $ENV_FILE with your specific values"
    log "2. Set up your database and Redis instances"
    log "3. Configure third-party service credentials"
    log "4. Run the database migration scripts"
}

# Run main function
main "$@"
