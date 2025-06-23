#!/usr/bin/env python3
"""
HealthConnect AI CDK Application
Production-grade infrastructure deployment using AWS CDK
"""

import os
import aws_cdk as cdk
from aws_cdk import (
    Environment,
    Tags
)

from stacks.api_gateway_stack import ApiGatewayStack
from stacks.lambda_stack import LambdaStack
from stacks.iot_stack import IoTStack
from stacks.bedrock_stack import BedrockStack
from stacks.dynamodb_stack import DynamoDBStack
from stacks.s3_stack import S3Stack
from stacks.cognito_stack import CognitoStack
from stacks.monitoring_stack import MonitoringStack

class HealthConnectApp:
    """Main CDK application for HealthConnect AI"""
    
    def __init__(self):
        self.app = cdk.App()
        
        # Get environment configuration
        self.env_name = self.app.node.try_get_context("env") or "dev"
        self.account = os.environ.get("CDK_DEFAULT_ACCOUNT")
        self.region = os.environ.get("CDK_DEFAULT_REGION", "us-east-1")
        
        # Define environment
        self.env = Environment(
            account=self.account,
            region=self.region
        )
        
        # Common stack properties
        self.stack_props = {
            "env": self.env,
            "description": f"HealthConnect AI Infrastructure - {self.env_name.upper()}",
            "tags": {
                "Project": "HealthConnect-AI",
                "Environment": self.env_name,
                "Owner": "HealthConnect-Team",
                "CostCenter": "Healthcare-Innovation",
                "Compliance": "HIPAA"
            }
        }
        
        # Deploy stacks
        self.deploy_infrastructure()
    
    def deploy_infrastructure(self):
        """Deploy all infrastructure stacks in correct order"""
        
        # Core data and storage stacks
        dynamodb_stack = DynamoDBStack(
            self.app, 
            f"HealthConnect-DynamoDB-{self.env_name}",
            env_name=self.env_name,
            **self.stack_props
        )
        
        s3_stack = S3Stack(
            self.app,
            f"HealthConnect-S3-{self.env_name}",
            env_name=self.env_name,
            **self.stack_props
        )
        
        # Authentication and authorization
        cognito_stack = CognitoStack(
            self.app,
            f"HealthConnect-Cognito-{self.env_name}",
            env_name=self.env_name,
            **self.stack_props
        )
        
        # AI/ML services
        bedrock_stack = BedrockStack(
            self.app,
            f"HealthConnect-Bedrock-{self.env_name}",
            env_name=self.env_name,
            **self.stack_props
        )
        
        # IoT infrastructure
        iot_stack = IoTStack(
            self.app,
            f"HealthConnect-IoT-{self.env_name}",
            env_name=self.env_name,
            dynamodb_tables=dynamodb_stack.tables,
            **self.stack_props
        )
        
        # Lambda functions
        lambda_stack = LambdaStack(
            self.app,
            f"HealthConnect-Lambda-{self.env_name}",
            env_name=self.env_name,
            dynamodb_tables=dynamodb_stack.tables,
            s3_buckets=s3_stack.buckets,
            iot_resources=iot_stack.iot_resources,
            **self.stack_props
        )
        
        # API Gateway
        api_gateway_stack = ApiGatewayStack(
            self.app,
            f"HealthConnect-API-{self.env_name}",
            env_name=self.env_name,
            lambda_functions=lambda_stack.functions,
            cognito_user_pool=cognito_stack.user_pool,
            **self.stack_props
        )
        
        # Monitoring and observability
        monitoring_stack = MonitoringStack(
            self.app,
            f"HealthConnect-Monitoring-{self.env_name}",
            env_name=self.env_name,
            lambda_functions=lambda_stack.functions,
            api_gateway=api_gateway_stack.api,
            dynamodb_tables=dynamodb_stack.tables,
            **self.stack_props
        )
        
        # Set up dependencies
        lambda_stack.add_dependency(dynamodb_stack)
        lambda_stack.add_dependency(s3_stack)
        lambda_stack.add_dependency(iot_stack)
        lambda_stack.add_dependency(bedrock_stack)
        
        api_gateway_stack.add_dependency(lambda_stack)
        api_gateway_stack.add_dependency(cognito_stack)
        
        monitoring_stack.add_dependency(lambda_stack)
        monitoring_stack.add_dependency(api_gateway_stack)
        
        # Add global tags
        for key, value in self.stack_props["tags"].items():
            Tags.of(self.app).add(key, value)

def main():
    """Main entry point"""
    app = HealthConnectApp()
    app.app.synth()

if __name__ == "__main__":
    main()
