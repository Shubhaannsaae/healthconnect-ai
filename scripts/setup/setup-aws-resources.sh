#!/bin/bash

# HealthConnect AI - AWS Resources Setup Script
# Production-grade AWS infrastructure provisioning
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
AWS_REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="healthconnect-ai"
ENVIRONMENT="${ENVIRONMENT:-dev}"
STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}"

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

# Check AWS CLI configuration
check_aws_config() {
    log "Checking AWS CLI configuration..."
    
    if ! command -v aws &> /dev/null; then
        error "AWS CLI not found. Please install AWS CLI first."
        exit 1
    fi
    
    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS CLI not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    local account_id=$(aws sts get-caller-identity --query Account --output text)
    local user_arn=$(aws sts get-caller-identity --query Arn --output text)
    
    success "AWS CLI configured for account: $account_id"
    log "User ARN: $user_arn"
}

# Create S3 buckets
create_s3_buckets() {
    log "Creating S3 buckets..."
    
    local buckets=(
        "${STACK_NAME}-frontend-hosting"
        "${STACK_NAME}-data-storage"
        "${STACK_NAME}-backup-storage"
        "${STACK_NAME}-logs-storage"
        "${STACK_NAME}-terraform-state"
    )
    
    for bucket in "${buckets[@]}"; do
        if aws s3api head-bucket --bucket "$bucket" 2>/dev/null; then
            warning "Bucket $bucket already exists"
        else
            log "Creating bucket: $bucket"
            
            if [[ "$AWS_REGION" == "us-east-1" ]]; then
                aws s3api create-bucket --bucket "$bucket"
            else
                aws s3api create-bucket --bucket "$bucket" --region "$AWS_REGION" \
                    --create-bucket-configuration LocationConstraint="$AWS_REGION"
            fi
            
            # Enable versioning
            aws s3api put-bucket-versioning --bucket "$bucket" \
                --versioning-configuration Status=Enabled
            
            # Enable server-side encryption
            aws s3api put-bucket-encryption --bucket "$bucket" \
                --server-side-encryption-configuration '{
                    "Rules": [{
                        "ApplyServerSideEncryptionByDefault": {
                            "SSEAlgorithm": "AES256"
                        }
                    }]
                }'
            
            # Block public access
            aws s3api put-public-access-block --bucket "$bucket" \
                --public-access-block-configuration \
                BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
            
            success "Created bucket: $bucket"
        fi
    done
}

# Create DynamoDB tables
create_dynamodb_tables() {
    log "Creating DynamoDB tables..."
    
    local tables=(
        "patients:patient_id"
        "health_records:record_id"
        "devices:device_id"
        "consultations:consultation_id"
        "alerts:alert_id"
    )
    
    for table_def in "${tables[@]}"; do
        local table_name="${STACK_NAME}-${table_def%:*}"
        local key_name="${table_def#*:}"
        
        if aws dynamodb describe-table --table-name "$table_name" &>/dev/null; then
            warning "Table $table_name already exists"
        else
            log "Creating table: $table_name"
            
            aws dynamodb create-table \
                --table-name "$table_name" \
                --attribute-definitions AttributeName="$key_name",AttributeType=S \
                --key-schema AttributeName="$key_name",KeyType=HASH \
                --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
                --tags Key=Project,Value="$PROJECT_NAME" Key=Environment,Value="$ENVIRONMENT"
            
            # Wait for table to be active
            aws dynamodb wait table-exists --table-name "$table_name"
            
            # Enable point-in-time recovery
            aws dynamodb put-backup-policy \
                --table-name "$table_name" \
                --backup-policy PointInTimeRecoveryEnabled=true
            
            success "Created table: $table_name"
        fi
    done
}

# Create Cognito User Pool
create_cognito_user_pool() {
    log "Creating Cognito User Pool..."
    
    local pool_name="${STACK_NAME}-user-pool"
    
    # Check if user pool already exists
    local existing_pools=$(aws cognito-idp list-user-pools --max-items 60 --query "UserPools[?Name=='$pool_name'].Id" --output text)
    
    if [[ -n "$existing_pools" ]]; then
        warning "User pool $pool_name already exists"
        return
    fi
    
    # Create user pool
    local pool_id=$(aws cognito-idp create-user-pool \
        --pool-name "$pool_name" \
        --policies '{
            "PasswordPolicy": {
                "MinimumLength": 8,
                "RequireUppercase": true,
                "RequireLowercase": true,
                "RequireNumbers": true,
                "RequireSymbols": true
            }
        }' \
        --auto-verified-attributes email \
        --username-attributes email \
        --schema '[
            {
                "Name": "email",
                "AttributeDataType": "String",
                "Required": true,
                "Mutable": true
            },
            {
                "Name": "given_name",
                "AttributeDataType": "String",
                "Required": true,
                "Mutable": true
            },
            {
                "Name": "family_name",
                "AttributeDataType": "String",
                "Required": true,
                "Mutable": true
            },
            {
                "Name": "custom:user_type",
                "AttributeDataType": "String",
                "Required": false,
                "Mutable": true
            }
        ]' \
        --query 'UserPool.Id' --output text)
    
    # Create user pool client
    local client_id=$(aws cognito-idp create-user-pool-client \
        --user-pool-id "$pool_id" \
        --client-name "${STACK_NAME}-web-client" \
        --generate-secret \
        --explicit-auth-flows ADMIN_NO_SRP_AUTH ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH \
        --query 'UserPoolClient.ClientId' --output text)
    
    success "Created Cognito User Pool: $pool_id"
    success "Created User Pool Client: $client_id"
    
    # Store configuration
    cat > aws-config.json << EOF
{
    "userPoolId": "$pool_id",
    "userPoolClientId": "$client_id",
    "region": "$AWS_REGION"
}
EOF
}

# Create API Gateway
create_api_gateway() {
    log "Creating API Gateway..."
    
    local api_name="${STACK_NAME}-api"
    
    # Check if API already exists
    local existing_apis=$(aws apigateway get-rest-apis --query "items[?name=='$api_name'].id" --output text)
    
    if [[ -n "$existing_apis" ]]; then
        warning "API Gateway $api_name already exists"
        return
    fi
    
    # Create REST API
    local api_id=$(aws apigateway create-rest-api \
        --name "$api_name" \
        --description "HealthConnect AI REST API" \
        --endpoint-configuration types=REGIONAL \
        --query 'id' --output text)
    
    success "Created API Gateway: $api_id"
    
    # Get root resource ID
    local root_resource_id=$(aws apigateway get-resources \
        --rest-api-id "$api_id" \
        --query 'items[?path==`/`].id' --output text)
    
    # Create resources and methods would go here
    # This is a simplified version - full implementation would include all endpoints
    
    log "API Gateway URL: https://$api_id.execute-api.$AWS_REGION.amazonaws.com/prod"
}

# Create Lambda execution role
create_lambda_role() {
    log "Creating Lambda execution role..."
    
    local role_name="${STACK_NAME}-lambda-role"
    
    # Check if role already exists
    if aws iam get-role --role-name "$role_name" &>/dev/null; then
        warning "Role $role_name already exists"
        return
    fi
    
    # Create trust policy
    cat > lambda-trust-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF
    
    # Create role
    aws iam create-role \
        --role-name "$role_name" \
        --assume-role-policy-document file://lambda-trust-policy.json \
        --tags Key=Project,Value="$PROJECT_NAME" Key=Environment,Value="$ENVIRONMENT"
    
    # Attach policies
    aws iam attach-role-policy \
        --role-name "$role_name" \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    
    aws iam attach-role-policy \
        --role-name "$role_name" \
        --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess
    
    aws iam attach-role-policy \
        --role-name "$role_name" \
        --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
    
    # Clean up
    rm lambda-trust-policy.json
    
    success "Created Lambda execution role: $role_name"
}

# Create CloudWatch Log Groups
create_log_groups() {
    log "Creating CloudWatch Log Groups..."
    
    local log_groups=(
        "/aws/lambda/${STACK_NAME}-api"
        "/aws/lambda/${STACK_NAME}-auth"
        "/aws/lambda/${STACK_NAME}-health"
        "/aws/lambda/${STACK_NAME}-devices"
        "/aws/apigateway/${STACK_NAME}-api"
    )
    
    for log_group in "${log_groups[@]}"; do
        if aws logs describe-log-groups --log-group-name-prefix "$log_group" --query 'logGroups[0].logGroupName' --output text | grep -q "$log_group"; then
            warning "Log group $log_group already exists"
        else
            aws logs create-log-group --log-group-name "$log_group"
            aws logs put-retention-policy --log-group-name "$log_group" --retention-in-days 30
            success "Created log group: $log_group"
        fi
    done
}

# Create VPC and networking (optional)
create_vpc() {
    log "Creating VPC and networking resources..."
    
    local vpc_name="${STACK_NAME}-vpc"
    
    # This is a simplified VPC creation
    # In production, you might want to use CloudFormation or Terraform for complex networking
    
    local vpc_id=$(aws ec2 create-vpc \
        --cidr-block 10.0.0.0/16 \
        --tag-specifications "ResourceType=vpc,Tags=[{Key=Name,Value=$vpc_name},{Key=Project,Value=$PROJECT_NAME}]" \
        --query 'Vpc.VpcId' --output text)
    
    success "Created VPC: $vpc_id"
    
    # Enable DNS hostnames
    aws ec2 modify-vpc-attribute --vpc-id "$vpc_id" --enable-dns-hostnames
    
    # Create Internet Gateway
    local igw_id=$(aws ec2 create-internet-gateway \
        --tag-specifications "ResourceType=internet-gateway,Tags=[{Key=Name,Value=${vpc_name}-igw}]" \
        --query 'InternetGateway.InternetGatewayId' --output text)
    
    aws ec2 attach-internet-gateway --vpc-id "$vpc_id" --internet-gateway-id "$igw_id"
    
    success "Created and attached Internet Gateway: $igw_id"
}

# Main setup function
main() {
    log "Starting AWS resources setup for HealthConnect AI..."
    
    check_aws_config
    create_s3_buckets
    create_dynamodb_tables
    create_cognito_user_pool
    create_api_gateway
    create_lambda_role
    create_log_groups
    
    # Uncomment if VPC is needed
    # create_vpc
    
    success "AWS resources setup completed successfully!"
    
    log "Configuration files created:"
    log "- aws-config.json (Cognito configuration)"
    
    log "Next steps:"
    log "1. Update your environment variables with the created resource IDs"
    log "2. Deploy your Lambda functions"
    log "3. Configure API Gateway endpoints"
    log "4. Set up monitoring and alerting"
}

# Run main function
main "$@"
