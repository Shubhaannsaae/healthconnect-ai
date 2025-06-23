"""
API Gateway Stack for HealthConnect AI
Implements REST API, WebSocket API, and API Gateway configurations
"""

from aws_cdk import (
    Stack,
    aws_apigateway as apigateway,
    aws_apigatewayv2 as apigatewayv2,
    aws_lambda as lambda_,
    aws_cognito as cognito,
    aws_iam as iam,
    aws_logs as logs,
    aws_certificatemanager as acm,
    aws_route53 as route53,
    Duration,
    CfnOutput
)
from constructs import Construct
from typing import Dict, Any

class ApiGatewayStack(Stack):
    """API Gateway infrastructure stack"""
    
    def __init__(
        self, 
        scope: Construct, 
        construct_id: str,
        env_name: str,
        lambda_functions: Dict[str, lambda_.Function],
        cognito_user_pool: cognito.UserPool,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        self.lambda_functions = lambda_functions
        self.cognito_user_pool = cognito_user_pool
        
        # Create API Gateway resources
        self.create_rest_api()
        self.create_websocket_api()
        self.create_api_documentation()
        self.create_usage_plans()
        self.create_custom_domain()
        
    def create_rest_api(self):
        """Create REST API Gateway"""
        
        # Create CloudWatch log group for API Gateway
        self.api_log_group = logs.LogGroup(
            self, "ApiGatewayLogGroup",
            log_group_name=f"/aws/apigateway/healthconnect-{self.env_name}",
            retention=logs.RetentionDays.ONE_MONTH
        )
        
        # Create REST API
        self.api = apigateway.RestApi(
            self, "HealthConnectRestApi",
            rest_api_name=f"healthconnect-api-{self.env_name}",
            description=f"HealthConnect AI REST API - {self.env_name.upper()}",
            endpoint_configuration=apigateway.EndpointConfiguration(
                types=[apigateway.EndpointType.REGIONAL]
            ),
            deploy_options=apigateway.StageOptions(
                stage_name=self.env_name,
                logging_level=apigateway.MethodLoggingLevel.INFO,
                data_trace_enabled=True,
                metrics_enabled=True,
                access_log_destination=apigateway.LogGroupLogDestination(self.api_log_group),
                access_log_format=apigateway.AccessLogFormat.json_with_standard_fields(
                    caller=True,
                    http_method=True,
                    ip=True,
                    protocol=True,
                    request_time=True,
                    resource_path=True,
                    response_length=True,
                    status=True,
                    user=True
                ),
                throttling_rate_limit=1000,
                throttling_burst_limit=2000
            ),
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=[
                    "Content-Type",
                    "X-Amz-Date",
                    "Authorization",
                    "X-Api-Key",
                    "X-Amz-Security-Token",
                    "X-Amz-User-Agent"
                ]
            )
        )
        
        # Create Cognito authorizer
        self.cognito_authorizer = apigateway.CognitoUserPoolsAuthorizer(
            self, "CognitoAuthorizer",
            cognito_user_pools=[self.cognito_user_pool],
            authorizer_name=f"healthconnect-cognito-auth-{self.env_name}",
            identity_source="method.request.header.Authorization"
        )
        
        # Create API key for external integrations
        self.api_key = apigateway.ApiKey(
            self, "HealthConnectApiKey",
            api_key_name=f"healthconnect-api-key-{self.env_name}",
            description=f"API Key for HealthConnect AI - {self.env_name}"
        )
        
        # Create resource hierarchy
        self.create_api_resources()
        
    def create_api_resources(self):
        """Create API resource hierarchy and methods"""
        
        # Health Analysis API
        health_resource = self.api.root.add_resource("health")
        
        # Health analysis endpoint
        analysis_resource = health_resource.add_resource("analysis")
        analysis_integration = apigateway.LambdaIntegration(
            self.lambda_functions["health_analysis"],
            proxy=True,
            integration_responses=[
                apigateway.IntegrationResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": "'*'"
                    }
                )
            ]
        )
        
        analysis_resource.add_method(
            "POST",
            analysis_integration,
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO,
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True
                    }
                )
            ],
            request_validator=apigateway.RequestValidator(
                self, "HealthAnalysisValidator",
                rest_api=self.api,
                validate_request_body=True,
                validate_request_parameters=True
            )
        )
        
        # Device API
        device_resource = self.api.root.add_resource("devices")
        
        # Device simulation endpoint
        simulate_resource = device_resource.add_resource("simulate")
        simulate_integration = apigateway.LambdaIntegration(
            self.lambda_functions["device_simulator"],
            proxy=True
        )
        
        simulate_resource.add_method(
            "POST",
            simulate_integration,
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        # Device status endpoint
        status_resource = device_resource.add_resource("status")
        status_resource.add_method(
            "GET",
            simulate_integration,
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        # Emergency API
        emergency_resource = self.api.root.add_resource("emergency")
        
        # Emergency alert endpoint
        alert_resource = emergency_resource.add_resource("alert")
        alert_integration = apigateway.LambdaIntegration(
            self.lambda_functions["emergency_response"],
            proxy=True
        )
        
        alert_resource.add_method(
            "POST",
            alert_integration,
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        # Emergency alerts list
        alerts_resource = emergency_resource.add_resource("alerts")
        alerts_resource.add_method(
            "GET",
            alert_integration,
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        # Consultation API
        consultation_resource = self.api.root.add_resource("consultation")
        
        # Consultation session endpoint
        session_resource = consultation_resource.add_resource("session")
        consultation_integration = apigateway.LambdaIntegration(
            self.lambda_functions["consultation_api"],
            proxy=True
        )
        
        session_resource.add_method(
            "POST",
            consultation_integration,
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        session_resource.add_method(
            "GET",
            consultation_integration,
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        # Analytics API
        analytics_resource = self.api.root.add_resource("analytics")
        
        # Population health analytics
        population_resource = analytics_resource.add_resource("population")
        analytics_integration = apigateway.LambdaIntegration(
            self.lambda_functions["analytics_engine"],
            proxy=True
        )
        
        population_resource.add_method(
            "POST",
            analytics_integration,
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        # Predictive analytics
        predictive_resource = analytics_resource.add_resource("predictive")
        predictive_resource.add_method(
            "POST",
            analytics_integration,
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        # Health check endpoint (no auth required)
        health_check_resource = self.api.root.add_resource("health-check")
        health_check_integration = apigateway.MockIntegration(
            integration_responses=[
                apigateway.IntegrationResponse(
                    status_code="200",
                    response_templates={
                        "application/json": '{"status": "healthy", "timestamp": "$context.requestTime"}'
                    }
                )
            ],
            request_templates={
                "application/json": '{"statusCode": 200}'
            }
        )
        
        health_check_resource.add_method(
            "GET",
            health_check_integration,
            method_responses=[
                apigateway.MethodResponse(status_code="200")
            ]
        )
    
    def create_websocket_api(self):
        """Create WebSocket API for real-time communication"""
        
        # Create WebSocket API
        self.websocket_api = apigatewayv2.WebSocketApi(
            self, "HealthConnectWebSocketApi",
            api_name=f"healthconnect-websocket-{self.env_name}",
            description=f"HealthConnect AI WebSocket API - {self.env_name.upper()}",
            route_selection_expression="$request.body.action"
        )
        
        # Create WebSocket stage
        self.websocket_stage = apigatewayv2.WebSocketStage(
            self, "WebSocketStage",
            web_socket_api=self.websocket_api,
            stage_name=self.env_name,
            auto_deploy=True,
            throttle=apigatewayv2.ThrottleSettings(
                rate_limit=1000,
                burst_limit=2000
            )
        )
        
        # Create WebSocket routes
        self.create_websocket_routes()
    
    def create_websocket_routes(self):
        """Create WebSocket routes and integrations"""
        
        # Connect route
        connect_integration = apigatewayv2.WebSocketLambdaIntegration(
            "ConnectIntegration",
            self.lambda_functions["websocket_connect"]
        )
        
        apigatewayv2.WebSocketRoute(
            self, "ConnectRoute",
            web_socket_api=self.websocket_api,
            route_key="$connect",
            integration=connect_integration
        )
        
        # Disconnect route
        disconnect_integration = apigatewayv2.WebSocketLambdaIntegration(
            "DisconnectIntegration",
            self.lambda_functions["websocket_disconnect"]
        )
        
        apigatewayv2.WebSocketRoute(
            self, "DisconnectRoute",
            web_socket_api=self.websocket_api,
            route_key="$disconnect",
            integration=disconnect_integration
        )
        
        # Default route for messages
        message_integration = apigatewayv2.WebSocketLambdaIntegration(
            "MessageIntegration",
            self.lambda_functions["websocket_message"]
        )
        
        apigatewayv2.WebSocketRoute(
            self, "DefaultRoute",
            web_socket_api=self.websocket_api,
            route_key="$default",
            integration=message_integration
        )
        
        # Custom routes for specific message types
        custom_routes = [
            "sendMessage",
            "joinRoom",
            "leaveRoom",
            "healthData",
            "emergencyAlert"
        ]
        
        for route in custom_routes:
            apigatewayv2.WebSocketRoute(
                self, f"{route}Route",
                web_socket_api=self.websocket_api,
                route_key=route,
                integration=message_integration
            )
    
    def create_api_documentation(self):
        """Create API documentation"""
        
        # Create API documentation
        self.api_docs = apigateway.CfnDocumentationVersion(
            self, "ApiDocumentation",
            rest_api_id=self.api.rest_api_id,
            documentation_version=f"v1-{self.env_name}",
            description=f"HealthConnect AI API Documentation - {self.env_name.upper()}"
        )
    
    def create_usage_plans(self):
        """Create API usage plans and rate limiting"""
        
        # Create usage plan for different tiers
        self.usage_plan_basic = apigateway.UsagePlan(
            self, "BasicUsagePlan",
            name=f"healthconnect-basic-{self.env_name}",
            description="Basic usage plan for HealthConnect AI",
            throttle=apigateway.ThrottleSettings(
                rate_limit=100,
                burst_limit=200
            ),
            quota=apigateway.QuotaSettings(
                limit=10000,
                period=apigateway.Period.DAY
            ),
            api_stages=[
                apigateway.UsagePlanPerApiStage(
                    api=self.api,
                    stage=self.api.deployment_stage
                )
            ]
        )
        
        self.usage_plan_premium = apigateway.UsagePlan(
            self, "PremiumUsagePlan",
            name=f"healthconnect-premium-{self.env_name}",
            description="Premium usage plan for HealthConnect AI",
            throttle=apigateway.ThrottleSettings(
                rate_limit=1000,
                burst_limit=2000
            ),
            quota=apigateway.QuotaSettings(
                limit=100000,
                period=apigateway.Period.DAY
            ),
            api_stages=[
                apigateway.UsagePlanPerApiStage(
                    api=self.api,
                    stage=self.api.deployment_stage
                )
            ]
        )
        
        # Associate API key with usage plans
        self.usage_plan_basic.add_api_key(self.api_key)
        self.usage_plan_premium.add_api_key(self.api_key)
    
    def create_custom_domain(self):
        """Create custom domain for API (if certificate is available)"""
        
        # This would be configured with actual domain and certificate
        # For production deployment
        domain_name = f"api-{self.env_name}.healthconnect.ai"
        
        # Note: Certificate must be created separately in ACM
        # self.domain = apigateway.DomainName(
        #     self, "CustomDomain",
        #     domain_name=domain_name,
        #     certificate=acm.Certificate.from_certificate_arn(
        #         self, "Certificate",
        #         certificate_arn="arn:aws:acm:region:account:certificate/certificate-id"
        #     ),
        #     endpoint_type=apigateway.EndpointType.REGIONAL
        # )
        
        # Create outputs
        CfnOutput(
            self, "RestApiUrl",
            value=self.api.url,
            description="REST API Gateway URL",
            export_name=f"HealthConnect-RestApi-Url-{self.env_name}"
        )
        
        CfnOutput(
            self, "WebSocketApiUrl",
            value=self.websocket_stage.url,
            description="WebSocket API Gateway URL",
            export_name=f"HealthConnect-WebSocketApi-Url-{self.env_name}"
        )
        
        CfnOutput(
            self, "ApiKeyId",
            value=self.api_key.key_id,
            description="API Gateway API Key ID",
            export_name=f"HealthConnect-ApiKey-Id-{self.env_name}"
        )
