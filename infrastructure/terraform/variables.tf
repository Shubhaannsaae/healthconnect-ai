# Project Configuration
variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "healthconnect-ai"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "owner" {
  description = "Owner of the resources"
  type        = string
  default     = "HealthConnect-Team"
}

variable "cost_center" {
  description = "Cost center for billing"
  type        = string
  default     = "Healthcare-Innovation"
}

# AWS Configuration
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Network Configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

# SSL Certificate
variable "certificate_arn" {
  description = "ARN of the SSL certificate for HTTPS"
  type        = string
  default     = ""
}

variable "domain_name" {
  description = "Domain name for the API"
  type        = string
  default     = ""
}

# Cognito Configuration
variable "cognito_callback_urls" {
  description = "Callback URLs for Cognito"
  type        = list(string)
  default     = ["http://localhost:3000/callback"]
}

variable "cognito_logout_urls" {
  description = "Logout URLs for Cognito"
  type        = list(string)
  default     = ["http://localhost:3000/logout"]
}

# Monitoring Configuration
variable "alert_email_endpoints" {
  description = "Email endpoints for alerts"
  type        = list(string)
  default     = ["alerts@healthconnect.ai"]
}

variable "alert_sms_endpoints" {
  description = "SMS endpoints for alerts"
  type        = list(string)
  default     = []
}

# Database Configuration
variable "database_username" {
  description = "Database administrator username"
  type        = string
  default     = "healthconnect_admin"
  sensitive   = true
}

variable "database_password" {
  description = "Database administrator password"
  type        = string
  sensitive   = true
}

# Feature Flags
variable "enable_bedrock" {
  description = "Enable AWS Bedrock for AI features"
  type        = bool
  default     = true
}

variable "enable_monitoring" {
  description = "Enable comprehensive monitoring"
  type        = bool
  default     = true
}

variable "enable_backup" {
  description = "Enable automated backups"
  type        = bool
  default     = true
}

# Capacity Configuration
variable "lambda_reserved_concurrency" {
  description = "Reserved concurrency for Lambda functions"
  type = object({
    health_analysis    = number
    device_simulator   = number
    emergency_response = number
    consultation_api   = number
    analytics_engine   = number
  })
  default = {
    health_analysis    = 10
    device_simulator   = 5
    emergency_response = 10
    consultation_api   = 10
    analytics_engine   = 5
  }
}

# Security Configuration
variable "enable_waf" {
  description = "Enable AWS WAF for API Gateway"
  type        = bool
  default     = false
}

variable "allowed_ip_ranges" {
  description = "Allowed IP ranges for API access"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}
