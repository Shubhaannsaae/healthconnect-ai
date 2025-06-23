# VPC Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = module.vpc.vpc_cidr_block
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = module.vpc.private_subnet_ids
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = module.vpc.public_subnet_ids
}

# API Gateway Outputs
output "api_gateway_url" {
  description = "URL of the API Gateway"
  value       = module.api_gateway.api_gateway_url
}

output "websocket_api_url" {
  description = "URL of the WebSocket API"
  value       = module.api_gateway.websocket_api_url
}

output "api_gateway_id" {
  description = "ID of the API Gateway"
  value       = module.api_gateway.rest_api_id
}

# Lambda Outputs
output "lambda_function_arns" {
  description = "ARNs of all Lambda functions"
  value       = module.lambda.function_arns
}

output "lambda_function_names" {
  description = "Names of all Lambda functions"
  value       = module.lambda.function_names
}

# DynamoDB Outputs
output "dynamodb_table_names" {
  description = "Names of all DynamoDB tables"
  value       = module.dynamodb.table_names
}

output "dynamodb_table_arns" {
  description = "ARNs of all DynamoDB tables"
  value       = module.dynamodb.table_arns
}

# S3 Outputs
output "s3_bucket_names" {
  description = "Names of all S3 buckets"
  value       = module.s3.bucket_names
}

output "analytics_bucket_name" {
  description = "Name of the analytics S3 bucket"
  value       = module.s3.analytics_bucket_name
}

# Cognito Outputs
output "cognito_user_pool_id" {
  description = "ID of the Cognito User Pool"
  value       = module.cognito.user_pool_id
}

output "cognito_user_pool_client_id" {
  description = "ID of the Cognito User Pool Client"
  value       = module.cognito.user_pool_client_id
}

output "cognito_identity_pool_id" {
  description = "ID of the Cognito Identity Pool"
  value       = module.cognito.identity_pool_id
}

# IoT Outputs
output "iot_endpoint" {
  description = "IoT Core endpoint"
  value       = module.iot_core.iot_endpoint
}

output "iot_device_data_stream_name" {
  description = "Name of the IoT device data Kinesis stream"
  value       = module.iot_core.device_data_stream_name
}

# Monitoring Outputs
output "cloudwatch_dashboard_urls" {
  description = "URLs of CloudWatch dashboards"
  value       = module.monitoring.dashboard_urls
}

output "sns_topic_arns" {
  description = "ARNs of SNS topics for alerts"
  value       = module.monitoring.sns_topic_arns
}

# Security Outputs
output "kms_key_ids" {
  description = "IDs of KMS keys used for encryption"
  value = {
    dynamodb = module.dynamodb.kms_key_id
    s3       = module.s3.kms_key_id
  }
}

# Environment Information
output "environment_info" {
  description = "Environment information"
  value = {
    project_name = var.project_name
    environment  = var.environment
    region       = var.aws_region
    account_id   = local.account_id
  }
}
