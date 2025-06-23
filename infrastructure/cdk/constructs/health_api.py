"""
Health API Construct for HealthConnect AI
Reusable construct for health-related API endpoints
"""

from aws_cdk import (
    aws_apigateway as apigateway,
    aws_lambda as lambda_,
    aws_cognito as cognito,
    aws_iam as iam,
    Duration
)
from constructs import Construct
from typing import Dict, Any, Optional

class HealthApiConstruct(Construct):
    """Reusable construct for health API endpoints"""
    
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        lambda_function: lambda_.Function,
        authorizer: Optional[apigateway.CognitoUserPoolsAuthorizer] = None,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.lambda_function = lambda_function
        self.authorizer = authorizer
        
        # Create API Gateway integration
        self.integration = apigateway.LambdaIntegration(
            self.lambda_function,
            proxy=True,
            integration_responses=[
                apigateway.IntegrationResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": "'*'",
                        "method.response.header.Access-Control-Allow-Headers": "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                        "method.response.header.Access-Control-Allow-Methods": "'GET,POST,PUT,DELETE,OPTIONS'"
                    }
                )
            ]
        )
        
        # Create request validator
        self.request_validator = apigateway.RequestValidator(
            self, "RequestValidator",
            validate_request_body=True,
            validate_request_parameters=True
        )
    
    def add_to_api(self, api: apigateway.RestApi, resource_path: str) -> apigateway.Resource:
        """Add this construct to an API Gateway"""
        
        # Create resource hierarchy
        path_parts = resource_path.strip('/').split('/')
        current_resource = api.root
        
        for part in path_parts:
            existing_resource = None
            for resource in current_resource.get_resources():
                if resource.path_part == part:
                    existing_resource = resource
                    break
            
            if existing_resource:
                current_resource = existing_resource
            else:
                current_resource = current_resource.add_resource(part)
        
        # Add methods to the resource
        method_options = {
            "integration": self.integration,
            "request_validator": self.request_validator,
            "method_responses": [
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Methods": True
                    }
                )
            ]
        }
        
        if self.authorizer:
            method_options.update({
                "authorizer": self.authorizer,
                "authorization_type": apigateway.AuthorizationType.COGNITO
            })
        
        # Add POST method
        current_resource.add_method("POST", **method_options)
        
        # Add GET method
        current_resource.add_method("GET", **method_options)
        
        # Add OPTIONS method for CORS
        current_resource.add_method(
            "OPTIONS",
            apigateway.MockIntegration(
                integration_responses=[
                    apigateway.IntegrationResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": "'*'",
                            "method.response.header.Access-Control-Allow-Headers": "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                            "method.response.header.Access-Control-Allow-Methods": "'GET,POST,PUT,DELETE,OPTIONS'"
                        }
                    )
                ],
                request_templates={
                    "application/json": '{"statusCode": 200}'
                }
            ),
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Methods": True
                    }
                )
            ]
        )
        
        return current_resource
