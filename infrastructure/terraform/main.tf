terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    # Backend configuration will be provided during terraform init
    # bucket = "healthconnect-terraform-state"
    # key    = "infrastructure/terraform.tfstate"
    # region = "us-east-1"
    # encrypt = true
    # dynamodb_table = "terraform-state-locks"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = var.owner
      CostCenter  = var.cost_center
      Compliance  = "HIPAA"
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
data "aws_availability_zones" "available" {
  state = "available"
}

# Local values
locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.name
  
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
    Owner       = var.owner
    CostCenter  = var.cost_center
    Compliance  = "HIPAA"
  }
  
  name_prefix = "${var.project_name}-${var.environment}"
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"
  
  name_prefix        = local.name_prefix
  vpc_cidr          = var.vpc_cidr
  availability_zones = slice(data.aws_availability_zones.available.names, 0, 3)
  
  tags = local.common_tags
}

# S3 Module
module "s3" {
  source = "./modules/s3"
  
  name_prefix = local.name_prefix
  environment = var.environment
  
  tags = local.common_tags
}

# DynamoDB Module
module "dynamodb" {
  source = "./modules/dynamodb"
  
  name_prefix = local.name_prefix
  environment = var.environment
  
  tags = local.common_tags
}

# IoT Core Module
module "iot_core" {
  source = "./modules/iot-core"
  
  name_prefix = local.name_prefix
  environment = var.environment
  
  device_data_table_name     = module.dynamodb.device_data_table_name
  device_registry_table_name = module.dynamodb.device_registry_table_name
  
  tags = local.common_tags
}

# Lambda Module
module "lambda" {
  source = "./modules/lambda"
  
  name_prefix = local.name_prefix
  environment = var.environment
  
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  
  # DynamoDB table names
  health_records_table     = module.dynamodb.health_records_table_name
  device_data_table        = module.dynamodb.device_data_table_name
  device_registry_table    = module.dynamodb.device_registry_table_name
  emergency_alerts_table   = module.dynamodb.emergency_alerts_table_name
  consultation_sessions_table = module.dynamodb.consultation_sessions_table_name
  analytics_results_table  = module.dynamodb.analytics_results_table_name
  
  # S3 bucket names
  analytics_bucket    = module.s3.analytics_bucket_name
  lambda_code_bucket  = module.s3.lambda_code_bucket_name
  
  # IoT resources
  iot_endpoint = module.iot_core.iot_endpoint
  
  tags = local.common_tags
}

# API Gateway Module
module "api_gateway" {
  source = "./modules/api-gateway"
  
  name_prefix = local.name_prefix
  environment = var.environment
  
  # Lambda function ARNs
  health_analysis_lambda_arn    = module.lambda.health_analysis_function_arn
  device_simulator_lambda_arn   = module.lambda.device_simulator_function_arn
  emergency_response_lambda_arn = module.lambda.emergency_response_function_arn
  consultation_api_lambda_arn   = module.lambda.consultation_api_function_arn
  analytics_engine_lambda_arn   = module.lambda.analytics_engine_function_arn
  
  # WebSocket Lambda function ARNs
  websocket_connect_lambda_arn    = module.lambda.websocket_connect_function_arn
  websocket_disconnect_lambda_arn = module.lambda.websocket_disconnect_function_arn
  websocket_message_lambda_arn    = module.lambda.websocket_message_function_arn
  
  certificate_arn = var.certificate_arn
  domain_name     = var.domain_name
  
  tags = local.common_tags
}

# Cognito Module
module "cognito" {
  source = "./modules/cognito"
  
  name_prefix = local.name_prefix
  environment = var.environment
  
  callback_urls = var.cognito_callback_urls
  logout_urls   = var.cognito_logout_urls
  
  tags = local.common_tags
}

# Monitoring Module
module "monitoring" {
  source = "./modules/monitoring"
  
  name_prefix = local.name_prefix
  environment = var.environment
  
  # Resources to monitor
  lambda_function_names = module.lambda.function_names
  api_gateway_id       = module.api_gateway.rest_api_id
  dynamodb_table_names = module.dynamodb.table_names
  
  # SNS topics for alerts
  alert_email_endpoints = var.alert_email_endpoints
  alert_sms_endpoints   = var.alert_sms_endpoints
  
  tags = local.common_tags
}
