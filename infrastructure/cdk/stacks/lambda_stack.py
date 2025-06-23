"""
Lambda Stack for HealthConnect AI
Implements all Lambda functions with proper configurations
"""

from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_logs as logs,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_events as events,
    aws_events_targets as targets,
    aws_sns as sns,
    Duration,
    CfnOutput
)
from constructs import Construct
from typing import Dict, Any

class LambdaStack(Stack):
    """Lambda functions infrastructure stack"""
    
    def __init__(
        self, 
        scope: Construct, 
        construct_id: str,
        env_name: str,
        dynamodb_tables: Dict[str, dynamodb.Table],
        s3_buckets: Dict[str, s3.Bucket],
        iot_resources: Dict[str, Any],
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        self.dynamodb_tables = dynamodb_tables
        self.s3_buckets = s3_buckets
        self.iot_resources = iot_resources
        
        # Create Lambda layers
        self.create_lambda_layers()
        
        # Create Lambda functions
        self.functions = {}
        self.create_lambda_functions()
        
        # Create event rules and triggers
        self.create_event_triggers()
    
    def create_lambda_layers(self):
        """Create Lambda layers for shared code"""
        
        # Common utilities layer
        self.common_utils_layer = lambda_.LayerVersion(
            self, "CommonUtilsLayer",
            layer_version_name=f"healthconnect-common-utils-{self.env_name}",
            description="Common utilities for HealthConnect AI",
            code=lambda_.Code.from_asset("../backend/layers/common-utils"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_11],
            removal_policy=self.get_removal_policy()
        )
        
        # Medical models layer
        self.medical_models_layer = lambda_.LayerVersion(
            self, "MedicalModelsLayer",
            layer_version_name=f"healthconnect-medical-models-{self.env_name}",
            description="Medical models and algorithms for HealthConnect AI",
            code=lambda_.Code.from_asset("../backend/layers/medical-models"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_11],
            removal_policy=self.get_removal_policy()
        )
    
    def create_lambda_functions(self):
        """Create all Lambda functions"""
        
        # Common environment variables
        common_env = {
            "STAGE": self.env_name,
            "REGION": self.region,
            "LOG_LEVEL": "INFO" if self.env_name == "prod" else "DEBUG"
        }
        
        # Health Analysis Function
        self.functions["health_analysis"] = self.create_health_analysis_function(common_env)
        
        # Device Simulator Function
        self.functions["device_simulator"] = self.create_device_simulator_function(common_env)
        
        # Emergency Response Function
        self.functions["emergency_response"] = self.create_emergency_response_function(common_env)
        
        # Consultation API Function
        self.functions["consultation_api"] = self.create_consultation_api_function(common_env)
        
        # Analytics Engine Function
        self.functions["analytics_engine"] = self.create_analytics_engine_function(common_env)
        
        # WebSocket Functions
        self.functions["websocket_connect"] = self.create_websocket_connect_function(common_env)
        self.functions["websocket_disconnect"] = self.create_websocket_disconnect_function(common_env)
        self.functions["websocket_message"] = self.create_websocket_message_function(common_env)
    
    def create_health_analysis_function(self, common_env: Dict[str, str]) -> lambda_.Function:
        """Create health analysis Lambda function"""
        
        # Create execution role
        execution_role = iam.Role(
            self, "HealthAnalysisExecutionRole",
            role_name=f"healthconnect-health-analysis-role-{self.env_name}",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole")
            ],
            inline_policies={
                "HealthAnalysisPolicy": iam.PolicyDocument(
                    statements=[
                        # Bedrock permissions
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "bedrock:InvokeModel",
                                "bedrock:InvokeModelWithResponseStream"
                            ],
                            resources=[
                                f"arn:aws:bedrock:{self.region}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0",
                                f"arn:aws:bedrock:{self.region}::foundation-model/anthropic.claude-3-haiku-20240307-v1:0"
                            ]
                        ),
                        # Comprehend Medical permissions
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "comprehendmedical:DetectEntitiesV2",
                                "comprehendmedical:DetectPHI",
                                "comprehendmedical:InferICD10CM",
                                "comprehendmedical:InferRxNorm"
                            ],
                            resources=["*"]
                        ),
                        # DynamoDB permissions
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "dynamodb:PutItem",
                                "dynamodb:GetItem",
                                "dynamodb:UpdateItem",
                                "dynamodb:Query",
                                "dynamodb:Scan"
                            ],
                            resources=[
                                self.dynamodb_tables["health_records"].table_arn,
                                self.dynamodb_tables["analysis_results"].table_arn,
                                f"{self.dynamodb_tables['health_records'].table_arn}/index/*",
                                f"{self.dynamodb_tables['analysis_results'].table_arn}/index/*"
                            ]
                        ),
                        # SNS permissions for emergency alerts
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["sns:Publish"],
                            resources=[f"arn:aws:sns:{self.region}:{self.account}:healthconnect-emergency-*"]
                        ),
                        # EventBridge permissions
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["events:PutEvents"],
                            resources=[f"arn:aws:events:{self.region}:{self.account}:event-bus/healthconnect-*"]
                        )
                    ]
                )
            }
        )
        
        # Function environment
        function_env = {
            **common_env,
            "HEALTH_RECORDS_TABLE": self.dynamodb_tables["health_records"].table_name,
            "ANALYSIS_RESULTS_TABLE": self.dynamodb_tables["analysis_results"].table_name,
            "EMERGENCY_TOPIC_ARN": f"arn:aws:sns:{self.region}:{self.account}:healthconnect-emergency-{self.env_name}",
            "EVENT_BUS_NAME": f"healthconnect-events-{self.env_name}",
            "BEDROCK_MODEL_ID": "anthropic.claude-3-sonnet-20240229-v1:0"
        }
        
        # Create function
        function = lambda_.Function(
            self, "HealthAnalysisFunction",
            function_name=f"healthconnect-health-analysis-{self.env_name}",
            description="AI-powered health data analysis using AWS Bedrock",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("../backend/functions/health-analysis"),
            layers=[self.common_utils_layer, self.medical_models_layer],
            environment=function_env,
            role=execution_role,
            timeout=Duration.minutes(5),
            memory_size=1024,
            reserved_concurrent_executions=10,
            log_retention=logs.RetentionDays.ONE_MONTH,
            tracing=lambda_.Tracing.ACTIVE,
            architecture=lambda_.Architecture.X86_64,
            dead_letter_queue_enabled=True
        )
        
        return function
    
    def create_device_simulator_function(self, common_env: Dict[str, str]) -> lambda_.Function:
        """Create device simulator Lambda function"""
        
        # Create execution role
        execution_role = iam.Role(
            self, "DeviceSimulatorExecutionRole",
            role_name=f"healthconnect-device-simulator-role-{self.env_name}",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ],
            inline_policies={
                "DeviceSimulatorPolicy": iam.PolicyDocument(
                    statements=[
                        # IoT Core permissions
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "iot:Publish",
                                "iot:Connect"
                            ],
                            resources=[
                                f"arn:aws:iot:{self.region}:{self.account}:topic/healthconnect/devices/*/data",
                                f"arn:aws:iot:{self.region}:{self.account}:client/*"
                            ]
                        ),
                        # DynamoDB permissions
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "dynamodb:PutItem",
                                "dynamodb:GetItem",
                                "dynamodb:UpdateItem",
                                "dynamodb:DeleteItem",
                                "dynamodb:Query",
                                "dynamodb:Scan"
                            ],
                            resources=[
                                self.dynamodb_tables["device_registry"].table_arn,
                                self.dynamodb_tables["device_data"].table_arn
                            ]
                        ),
                        # EventBridge permissions
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["events:PutEvents"],
                            resources=[f"arn:aws:events:{self.region}:{self.account}:event-bus/healthconnect-*"]
                        )
                    ]
                )
            }
        )
        
        # Function environment
        function_env = {
            **common_env,
            "DEVICE_REGISTRY_TABLE": self.dynamodb_tables["device_registry"].table_name,
            "DEVICE_DATA_TABLE": self.dynamodb_tables["device_data"].table_name,
            "IOT_ENDPOINT": self.iot_resources["endpoint"],
            "EVENT_BUS_NAME": f"healthconnect-events-{self.env_name}"
        }
        
        # Create function
        function = lambda_.Function(
            self, "DeviceSimulatorFunction",
            function_name=f"healthconnect-device-simulator-{self.env_name}",
            description="IoT device simulator for HealthConnect AI",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("../backend/functions/device-simulator"),
            layers=[self.common_utils_layer],
            environment=function_env,
            role=execution_role,
            timeout=Duration.minutes(5),
            memory_size=1024,
            reserved_concurrent_executions=5,
            log_retention=logs.RetentionDays.ONE_MONTH,
            tracing=lambda_.Tracing.ACTIVE
        )
        
        return function
    
    def create_emergency_response_function(self, common_env: Dict[str, str]) -> lambda_.Function:
        """Create emergency response Lambda function"""
        
        # Create execution role
        execution_role = iam.Role(
            self, "EmergencyResponseExecutionRole",
            role_name=f"healthconnect-emergency-response-role-{self.env_name}",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ],
            inline_policies={
                "EmergencyResponsePolicy": iam.PolicyDocument(
                    statements=[
                        # DynamoDB permissions
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "dynamodb:PutItem",
                                "dynamodb:GetItem",
                                "dynamodb:UpdateItem",
                                "dynamodb:DeleteItem",
                                "dynamodb:Query",
                                "dynamodb:Scan"
                            ],
                            resources=[
                                self.dynamodb_tables["emergency_alerts"].table_arn,
                                self.dynamodb_tables["emergency_contacts"].table_arn,
                                f"{self.dynamodb_tables['emergency_alerts'].table_arn}/index/*",
                                f"{self.dynamodb_tables['emergency_contacts'].table_arn}/index/*"
                            ]
                        ),
                        # SNS permissions
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "sns:Publish",
                                "sns:Subscribe",
                                "sns:Unsubscribe"
                            ],
                            resources=[f"arn:aws:sns:{self.region}:{self.account}:*"]
                        ),
                        # SES permissions
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "ses:SendEmail",
                                "ses:SendRawEmail"
                            ],
                            resources=[f"arn:aws:ses:{self.region}:{self.account}:identity/*"]
                        ),
                        # Pinpoint permissions
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "mobiletargeting:SendMessages",
                                "mobiletargeting:GetEndpoint",
                                "mobiletargeting:UpdateEndpoint"
                            ],
                            resources=[f"arn:aws:mobiletargeting:{self.region}:{self.account}:apps/*"]
                        ),
                        # EventBridge permissions
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["events:PutEvents"],
                            resources=[f"arn:aws:events:{self.region}:{self.account}:event-bus/healthconnect-*"]
                        ),
                        # Lambda invoke permissions
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["lambda:InvokeFunction"],
                            resources=[f"arn:aws:lambda:{self.region}:{self.account}:function:healthconnect-*"]
                        ),
                        # SSM parameters for external service credentials
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "ssm:GetParameter",
                                "ssm:GetParameters"
                            ],
                            resources=[f"arn:aws:ssm:{self.region}:{self.account}:parameter/healthconnect/{self.env_name}/*"]
                        )
                    ]
                )
            }
        )
        
        # Function environment
        function_env = {
            **common_env,
            "EMERGENCY_ALERTS_TABLE": self.dynamodb_tables["emergency_alerts"].table_name,
            "EMERGENCY_CONTACTS_TABLE": self.dynamodb_tables["emergency_contacts"].table_name,
            "EMERGENCY_TOPIC_ARN": f"arn:aws:sns:{self.region}:{self.account}:healthconnect-emergency-{self.env_name}",
            "EVENT_BUS_NAME": f"healthconnect-events-{self.env_name}",
            "CONSULTATION_FUNCTION_ARN": f"arn:aws:lambda:{self.region}:{self.account}:function:healthconnect-consultation-{self.env_name}"
        }
        
        # Create function
        function = lambda_.Function(
            self, "EmergencyResponseFunction",
            function_name=f"healthconnect-emergency-response-{self.env_name}",
            description="Emergency response system for HealthConnect AI",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("../backend/functions/emergency-response"),
            layers=[self.common_utils_layer],
            environment=function_env,
            role=execution_role,
            timeout=Duration.minutes(5),
            memory_size=1024,
            reserved_concurrent_executions=10,
            log_retention=logs.RetentionDays.ONE_MONTH,
            tracing=lambda_.Tracing.ACTIVE,
            dead_letter_queue_enabled=True
        )
        
        return function
    
    def create_consultation_api_function(self, common_env: Dict[str, str]) -> lambda_.Function:
        """Create consultation API Lambda function"""
        
        # Create execution role
        execution_role = iam.Role(
            self, "ConsultationApiExecutionRole",
            role_name=f"healthconnect-consultation-api-role-{self.env_name}",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ],
            inline_policies={
                "ConsultationApiPolicy": iam.PolicyDocument(
                    statements=[
                        # Bedrock permissions for AI assistance
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "bedrock:InvokeModel",
                                "bedrock:InvokeModelWithResponseStream"
                            ],
                            resources=[
                                f"arn:aws:bedrock:{self.region}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
                            ]
                        ),
                        # DynamoDB permissions
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "dynamodb:PutItem",
                                "dynamodb:GetItem",
                                "dynamodb:UpdateItem",
                                "dynamodb:DeleteItem",
                                "dynamodb:Query",
                                "dynamodb:Scan"
                            ],
                            resources=[
                                self.dynamodb_tables["consultation_sessions"].table_arn,
                                self.dynamodb_tables["healthcare_providers"].table_arn,
                                self.dynamodb_tables["consultation_queue"].table_arn,
                                f"{self.dynamodb_tables['consultation_sessions'].table_arn}/index/*",
                                f"{self.dynamodb_tables['healthcare_providers'].table_arn}/index/*"
                            ]
                        ),
                        # SNS permissions
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["sns:Publish"],
                            resources=[f"arn:aws:sns:{self.region}:{self.account}:*"]
                        ),
                        # EventBridge permissions
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["events:PutEvents"],
                            resources=[f"arn:aws:events:{self.region}:{self.account}:event-bus/healthconnect-*"]
                        ),
                        # Lambda invoke permissions
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["lambda:InvokeFunction"],
                            resources=[f"arn:aws:lambda:{self.region}:{self.account}:function:healthconnect-*"]
                        ),
                        # API Gateway Management permissions for WebSocket
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["execute-api:ManageConnections"],
                            resources=[f"arn:aws:execute-api:{self.region}:{self.account}:*/*/*/*"]
                        )
                    ]
                )
            }
        )
        
        # Function environment
        function_env = {
            **common_env,
            "CONSULTATION_SESSIONS_TABLE": self.dynamodb_tables["consultation_sessions"].table_name,
            "HEALTHCARE_PROVIDERS_TABLE": self.dynamodb_tables["healthcare_providers"].table_name,
            "CONSULTATION_QUEUE_TABLE": self.dynamodb_tables["consultation_queue"].table_name,
            "EVENT_BUS_NAME": f"healthconnect-events-{self.env_name}",
            "BEDROCK_MODEL_ID": "anthropic.claude-3-sonnet-20240229-v1:0"
        }
        
        # Create function
        function = lambda_.Function(
            self, "ConsultationApiFunction",
            function_name=f"healthconnect-consultation-api-{self.env_name}",
            description="Consultation API with WebRTC signaling for HealthConnect AI",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("../backend/functions/consultation-api"),
            layers=[self.common_utils_layer, self.medical_models_layer],
            environment=function_env,
            role=execution_role,
            timeout=Duration.minutes(5),
            memory_size=1024,
            reserved_concurrent_executions=10,
            log_retention=logs.RetentionDays.ONE_MONTH,
            tracing=lambda_.Tracing.ACTIVE
        )
        
        return function
    
    def create_analytics_engine_function(self, common_env: Dict[str, str]) -> lambda_.Function:
        """Create analytics engine Lambda function"""
        
        # Create execution role
        execution_role = iam.Role(
            self, "AnalyticsEngineExecutionRole",
            role_name=f"healthconnect-analytics-engine-role-{self.env_name}",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ],
            inline_policies={
                "AnalyticsEnginePolicy": iam.PolicyDocument(
                    statements=[
                        # Bedrock permissions for AI insights
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "bedrock:InvokeModel",
                                "bedrock:InvokeModelWithResponseStream"
                            ],
                            resources=[
                                f"arn:aws:bedrock:{self.region}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
                            ]
                        ),
                        # DynamoDB permissions
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "dynamodb:PutItem",
                                "dynamodb:GetItem",
                                "dynamodb:UpdateItem",
                                "dynamodb:Query",
                                "dynamodb:Scan",
                                "dynamodb:BatchGetItem",
                                "dynamodb:BatchWriteItem"
                            ],
                            resources=[
                                self.dynamodb_tables["analytics_results"].table_arn,
                                self.dynamodb_tables["population_metrics"].table_arn,
                                self.dynamodb_tables["predictive_models"].table_arn,
                                f"{self.dynamodb_tables['analytics_results'].table_arn}/index/*"
                            ]
                        ),
                        # S3 permissions for analytics data
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "s3:GetObject",
                                "s3:PutObject",
                                "s3:DeleteObject",
                                "s3:ListBucket"
                            ],
                            resources=[
                                self.s3_buckets["analytics"].bucket_arn,
                                f"{self.s3_buckets['analytics'].bucket_arn}/*"
                            ]
                        ),
                        # Athena permissions for data querying
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "athena:StartQueryExecution",
                                "athena:GetQueryExecution",
                                "athena:GetQueryResults",
                                "athena:StopQueryExecution"
                            ],
                            resources=["*"]
                        ),
                        # Glue permissions for data catalog
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "glue:GetDatabase",
                                "glue:GetTable",
                                "glue:GetPartitions"
                            ],
                            resources=["*"]
                        ),
                        # QuickSight permissions for dashboards
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "quicksight:CreateDashboard",
                                "quicksight:UpdateDashboard",
                                "quicksight:DescribeDashboard",
                                "quicksight:ListDashboards",
                                "quicksight:CreateDataSet",
                                "quicksight:UpdateDataSet"
                            ],
                            resources=["*"]
                        ),
                        # EventBridge permissions
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["events:PutEvents"],
                            resources=[f"arn:aws:events:{self.region}:{self.account}:event-bus/healthconnect-*"]
                        )
                    ]
                )
            }
        )
        
        # Function environment
        function_env = {
            **common_env,
            "ANALYTICS_RESULTS_TABLE": self.dynamodb_tables["analytics_results"].table_name,
            "POPULATION_METRICS_TABLE": self.dynamodb_tables["population_metrics"].table_name,
            "PREDICTIVE_MODELS_TABLE": self.dynamodb_tables["predictive_models"].table_name,
            "ANALYTICS_BUCKET": self.s3_buckets["analytics"].bucket_name,
            "ATHENA_DATABASE": f"healthconnect_analytics_{self.env_name}",
            "ATHENA_WORKGROUP": f"healthconnect-{self.env_name}",
            "EVENT_BUS_NAME": f"healthconnect-events-{self.env_name}",
            "QUICKSIGHT_ACCOUNT_ID": self.account
        }
        
        # Create function
        function = lambda_.Function(
            self, "AnalyticsEngineFunction",
            function_name=f"healthconnect-analytics-engine-{self.env_name}",
            description="Analytics engine for population health and predictive modeling",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("../backend/functions/analytics-engine"),
            layers=[self.common_utils_layer, self.medical_models_layer],
            environment=function_env,
            role=execution_role,
            timeout=Duration.minutes(15),
            memory_size=3008,
            reserved_concurrent_executions=5,
            log_retention=logs.RetentionDays.ONE_MONTH,
            tracing=lambda_.Tracing.ACTIVE
        )
        
        return function
    
    def create_websocket_connect_function(self, common_env: Dict[str, str]) -> lambda_.Function:
        """Create WebSocket connect Lambda function"""
        
        # Create execution role
        execution_role = iam.Role(
            self, "WebSocketConnectExecutionRole",
            role_name=f"healthconnect-websocket-connect-role-{self.env_name}",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ],
            inline_policies={
                "WebSocketConnectPolicy": iam.PolicyDocument(
                    statements=[
                        # DynamoDB permissions
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "dynamodb:PutItem",
                                "dynamodb:GetItem",
                                "dynamodb:UpdateItem"
                            ],
                            resources=[
                                self.dynamodb_tables["websocket_connections"].table_arn
                            ]
                        )
                    ]
                )
            }
        )
        
        # Function environment
        function_env = {
            **common_env,
            "WEBSOCKET_CONNECTIONS_TABLE": self.dynamodb_tables["websocket_connections"].table_name
        }
        
        # Create function
        function = lambda_.Function(
            self, "WebSocketConnectFunction",
            function_name=f"healthconnect-websocket-connect-{self.env_name}",
            description="Handle WebSocket connection events",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("../backend/functions/websocket-api/connect"),
            layers=[self.common_utils_layer],
            environment=function_env,
            role=execution_role,
            timeout=Duration.seconds(30),
            memory_size=256,
            log_retention=logs.RetentionDays.ONE_WEEK,
            tracing=lambda_.Tracing.ACTIVE
        )
        
        return function
    
    def create_websocket_disconnect_function(self, common_env: Dict[str, str]) -> lambda_.Function:
        """Create WebSocket disconnect Lambda function"""
        
        # Create execution role
        execution_role = iam.Role(
            self, "WebSocketDisconnectExecutionRole",
            role_name=f"healthconnect-websocket-disconnect-role-{self.env_name}",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ],
            inline_policies={
                "WebSocketDisconnectPolicy": iam.PolicyDocument(
                    statements=[
                        # DynamoDB permissions
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "dynamodb:GetItem",
                                "dynamodb:DeleteItem"
                            ],
                            resources=[
                                self.dynamodb_tables["websocket_connections"].table_arn
                            ]
                        ),
                        # EventBridge permissions
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["events:PutEvents"],
                            resources=[f"arn:aws:events:{self.region}:{self.account}:event-bus/healthconnect-*"]
                        )
                    ]
                )
            }
        )
        
        # Function environment
        function_env = {
            **common_env,
            "WEBSOCKET_CONNECTIONS_TABLE": self.dynamodb_tables["websocket_connections"].table_name,
            "EVENT_BUS_NAME": f"healthconnect-events-{self.env_name}"
        }
        
        # Create function
        function = lambda_.Function(
            self, "WebSocketDisconnectFunction",
            function_name=f"healthconnect-websocket-disconnect-{self.env_name}",
            description="Handle WebSocket disconnection events",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("../backend/functions/websocket-api/disconnect"),
            layers=[self.common_utils_layer],
            environment=function_env,
            role=execution_role,
            timeout=Duration.seconds(30),
            memory_size=256,
            log_retention=logs.RetentionDays.ONE_WEEK,
            tracing=lambda_.Tracing.ACTIVE
        )
        
        return function
    
    def create_websocket_message_function(self, common_env: Dict[str, str]) -> lambda_.Function:
        """Create WebSocket message Lambda function"""
        
        # Create execution role
        execution_role = iam.Role(
            self, "WebSocketMessageExecutionRole",
            role_name=f"healthconnect-websocket-message-role-{self.env_name}",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ],
            inline_policies={
                "WebSocketMessagePolicy": iam.PolicyDocument(
                    statements=[
                        # DynamoDB permissions
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "dynamodb:GetItem",
                                "dynamodb:UpdateItem",
                                "dynamodb:PutItem",
                                "dynamodb:Scan",
                                "dynamodb:Query",
                                "dynamodb:DeleteItem"
                            ],
                            resources=[
                                self.dynamodb_tables["websocket_connections"].table_arn,
                                self.dynamodb_tables["websocket_messages"].table_arn
                            ]
                        ),
                        # API Gateway Management permissions
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["execute-api:ManageConnections"],
                            resources=[f"arn:aws:execute-api:{self.region}:{self.account}:*/*/*/*"]
                        )
                    ]
                )
            }
        )
        
        # Function environment
        function_env = {
            **common_env,
            "WEBSOCKET_CONNECTIONS_TABLE": self.dynamodb_tables["websocket_connections"].table_name,
            "WEBSOCKET_MESSAGES_TABLE": self.dynamodb_tables["websocket_messages"].table_name
        }
        
        # Create function
        function = lambda_.Function(
            self, "WebSocketMessageFunction",
            function_name=f"healthconnect-websocket-message-{self.env_name}",
            description="Handle WebSocket message routing and delivery",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("../backend/functions/websocket-api/message"),
            layers=[self.common_utils_layer],
            environment=function_env,
            role=execution_role,
            timeout=Duration.seconds(30),
            memory_size=512,
            log_retention=logs.RetentionDays.ONE_WEEK,
            tracing=lambda_.Tracing.ACTIVE
        )
        
        return function
    
    def create_event_triggers(self):
        """Create EventBridge rules and scheduled triggers"""
        
        # Create EventBridge bus
        event_bus = events.EventBus(
            self, "HealthConnectEventBus",
            event_bus_name=f"healthconnect-events-{self.env_name}"
        )
        
        # Scheduled device simulation
        device_simulation_rule = events.Rule(
            self, "DeviceSimulationSchedule",
            rule_name=f"healthconnect-device-simulation-{self.env_name}",
            description="Scheduled device simulation for continuous monitoring",
            schedule=events.Schedule.rate(Duration.minutes(5)),
            enabled=True
        )
        
        device_simulation_rule.add_target(
            targets.LambdaFunction(
                self.functions["device_simulator"],
                event=events.RuleTargetInput.from_object({
                    "source": "aws.events",
                    "action": "scheduled_simulation"
                })
            )
        )
        
        # Scheduled analytics processing
        analytics_schedule_rule = events.Rule(
            self, "AnalyticsSchedule",
            rule_name=f"healthconnect-analytics-schedule-{self.env_name}",
            description="Scheduled analytics processing",
            schedule=events.Schedule.rate(Duration.hours(6)),
            enabled=True
        )
        
        analytics_schedule_rule.add_target(
            targets.LambdaFunction(
                self.functions["analytics_engine"],
                event=events.RuleTargetInput.from_object({
                    "source": "aws.events",
                    "analytics_type": "comprehensive"
                })
            )
        )
        
        # Emergency alert processing rule
        emergency_rule = events.Rule(
            self, "EmergencyAlertRule",
            rule_name=f"healthconnect-emergency-alerts-{self.env_name}",
            description="Process emergency alerts from health analysis",
            event_bus=event_bus,
            event_pattern=events.EventPattern(
                source=["healthconnect.analysis"],
                detail_type=["Health Analysis Complete"],
                detail={
                    "urgency_level": ["CRITICAL", "HIGH"]
                }
            )
        )
        
        emergency_rule.add_target(
            targets.LambdaFunction(self.functions["emergency_response"])
        )
    
    def get_removal_policy(self):
        """Get removal policy based on environment"""
        if self.env_name == "prod":
            return None  # Retain resources in production
        else:
            from aws_cdk import RemovalPolicy
            return RemovalPolicy.DESTROY
    
    @property
    def account(self) -> str:
        """Get AWS account ID"""
        return Stack.of(self).account
    
    @property
    def region(self) -> str:
        """Get AWS region"""
        return Stack.of(self).region
