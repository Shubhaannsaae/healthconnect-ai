"""
Bedrock Stack for HealthConnect AI
Implements AWS Bedrock infrastructure for AI/ML capabilities
"""

from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_logs as logs,
    aws_s3 as s3,
    aws_kms as kms,
    CfnOutput
)
from constructs import Construct
from typing import Dict, Any

class BedrockStack(Stack):
    """AWS Bedrock infrastructure stack for AI/ML services"""
    
    def __init__(
        self, 
        scope: Construct, 
        construct_id: str,
        env_name: str,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Create Bedrock resources
        self.create_bedrock_access_policies()
        self.create_model_invocation_logging()
        self.create_knowledge_base_resources()
        self.create_guardrails()
        
    def create_bedrock_access_policies(self):
        """Create IAM policies for Bedrock model access"""
        
        # Bedrock model access policy for health analysis
        self.health_analysis_bedrock_policy = iam.ManagedPolicy(
            self, "HealthAnalysisBedrockPolicy",
            managed_policy_name=f"HealthConnect-Bedrock-HealthAnalysis-{self.env_name}",
            description="Bedrock access policy for health analysis functions",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "bedrock:InvokeModel",
                        "bedrock:InvokeModelWithResponseStream"
                    ],
                    resources=[
                        f"arn:aws:bedrock:{self.region}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0",
                        f"arn:aws:bedrock:{self.region}::foundation-model/anthropic.claude-3-haiku-20240307-v1:0",
                        f"arn:aws:bedrock:{self.region}::foundation-model/anthropic.claude-3-opus-20240229-v1:0"
                    ],
                    conditions={
                        "StringEquals": {
                            "aws:RequestedRegion": self.region
                        }
                    }
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "bedrock:GetFoundationModel",
                        "bedrock:ListFoundationModels"
                    ],
                    resources=["*"]
                )
            ]
        )
        
        # Bedrock model access policy for consultation AI
        self.consultation_bedrock_policy = iam.ManagedPolicy(
            self, "ConsultationBedrockPolicy",
            managed_policy_name=f"HealthConnect-Bedrock-Consultation-{self.env_name}",
            description="Bedrock access policy for consultation AI functions",
            statements=[
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
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "bedrock:GetFoundationModel",
                        "bedrock:ListFoundationModels"
                    ],
                    resources=["*"]
                )
            ]
        )
        
        # Bedrock model access policy for analytics
        self.analytics_bedrock_policy = iam.ManagedPolicy(
            self, "AnalyticsBedrockPolicy",
            managed_policy_name=f"HealthConnect-Bedrock-Analytics-{self.env_name}",
            description="Bedrock access policy for analytics functions",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "bedrock:InvokeModel",
                        "bedrock:InvokeModelWithResponseStream"
                    ],
                    resources=[
                        f"arn:aws:bedrock:{self.region}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0",
                        f"arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-text-express-v1"
                    ]
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "bedrock:GetFoundationModel",
                        "bedrock:ListFoundationModels"
                    ],
                    resources=["*"]
                )
            ]
        )
    
    def create_model_invocation_logging(self):
        """Create CloudWatch logging for Bedrock model invocations"""
        
        # Create KMS key for log encryption
        self.bedrock_logs_key = kms.Key(
            self, "BedrockLogsKey",
            description=f"KMS key for Bedrock logs encryption - {self.env_name}",
            enable_key_rotation=True,
            policy=iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        principals=[iam.AccountRootPrincipal()],
                        actions=["kms:*"],
                        resources=["*"]
                    ),
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        principals=[iam.ServicePrincipal(f"logs.{self.region}.amazonaws.com")],
                        actions=[
                            "kms:Encrypt",
                            "kms:Decrypt",
                            "kms:ReEncrypt*",
                            "kms:GenerateDataKey*",
                            "kms:DescribeKey"
                        ],
                        resources=["*"],
                        conditions={
                            "ArnEquals": {
                                "kms:EncryptionContext:aws:logs:arn": f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/bedrock/healthconnect-*"
                            }
                        }
                    )
                ]
            )
        )
        
        # Create alias for the key
        kms.Alias(
            self, "BedrockLogsKeyAlias",
            alias_name=f"alias/healthconnect-bedrock-logs-{self.env_name}",
            target_key=self.bedrock_logs_key
        )
        
        # Health Analysis Model Invocation Logs
        self.health_analysis_log_group = logs.LogGroup(
            self, "HealthAnalysisBedrockLogs",
            log_group_name=f"/aws/bedrock/healthconnect-health-analysis-{self.env_name}",
            retention=logs.RetentionDays.ONE_MONTH,
            encryption_key=self.bedrock_logs_key,
            removal_policy=self.get_removal_policy()
        )
        
        # Consultation AI Model Invocation Logs
        self.consultation_log_group = logs.LogGroup(
            self, "ConsultationBedrockLogs",
            log_group_name=f"/aws/bedrock/healthconnect-consultation-{self.env_name}",
            retention=logs.RetentionDays.ONE_MONTH,
            encryption_key=self.bedrock_logs_key,
            removal_policy=self.get_removal_policy()
        )
        
        # Analytics Model Invocation Logs
        self.analytics_log_group = logs.LogGroup(
            self, "AnalyticsBedrockLogs",
            log_group_name=f"/aws/bedrock/healthconnect-analytics-{self.env_name}",
            retention=logs.RetentionDays.ONE_MONTH,
            encryption_key=self.bedrock_logs_key,
            removal_policy=self.get_removal_policy()
        )
        
        # Model Invocation Logging Configuration
        # Note: This would typically be configured through the Bedrock console or CLI
        # as CDK doesn't yet have native support for Bedrock logging configuration
        
        # Create IAM role for Bedrock logging
        self.bedrock_logging_role = iam.Role(
            self, "BedrockLoggingRole",
            role_name=f"HealthConnect-Bedrock-Logging-{self.env_name}",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            inline_policies={
                "BedrockLoggingPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "logs:CreateLogStream",
                                "logs:PutLogEvents"
                            ],
                            resources=[
                                self.health_analysis_log_group.log_group_arn,
                                self.consultation_log_group.log_group_arn,
                                self.analytics_log_group.log_group_arn
                            ]
                        )
                    ]
                )
            }
        )
    
    def create_knowledge_base_resources(self):
        """Create resources for Bedrock Knowledge Base (if needed)"""
        
        # S3 bucket for knowledge base documents
        self.knowledge_base_bucket = s3.Bucket(
            self, "KnowledgeBaseBucket",
            bucket_name=f"healthconnect-knowledge-base-{self.env_name}-{self.account}",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="KnowledgeBaseLifecycle",
                    enabled=True,
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(30)
                        )
                    ]
                )
            ]
        )
        
        # IAM role for Knowledge Base
        self.knowledge_base_role = iam.Role(
            self, "KnowledgeBaseRole",
            role_name=f"HealthConnect-KnowledgeBase-{self.env_name}",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            inline_policies={
                "KnowledgeBasePolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "s3:GetObject",
                                "s3:ListBucket"
                            ],
                            resources=[
                                self.knowledge_base_bucket.bucket_arn,
                                f"{self.knowledge_base_bucket.bucket_arn}/*"
                            ]
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "bedrock:InvokeModel"
                            ],
                            resources=[
                                f"arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-text-v1"
                            ]
                        )
                    ]
                )
            }
        )
        
        # Note: Bedrock Knowledge Base creation would typically be done through
        # the console or CLI as CDK support is limited
    
    def create_guardrails(self):
        """Create Bedrock guardrails for responsible AI"""
        
        # Create IAM policy for guardrails
        self.guardrails_policy = iam.ManagedPolicy(
            self, "BedrockGuardrailsPolicy",
            managed_policy_name=f"HealthConnect-Bedrock-Guardrails-{self.env_name}",
            description="Policy for Bedrock guardrails in healthcare context",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "bedrock:ApplyGuardrail",
                        "bedrock:GetGuardrail",
                        "bedrock:ListGuardrails"
                    ],
                    resources=[
                        f"arn:aws:bedrock:{self.region}:{self.account}:guardrail/*"
                    ]
                )
            ]
        )
        
        # Note: Guardrail creation would typically be done through the console or CLI
        # Healthcare-specific guardrails would include:
        # - Content filtering for medical advice disclaimers
        # - PII detection and redaction
        # - Bias detection for healthcare decisions
        # - Toxicity filtering
        # - Custom word filters for inappropriate medical content
    
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
