"""
S3 Stack for HealthConnect AI
Implements S3 buckets for data storage and static assets
"""

from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_kms as kms,
    aws_iam as iam,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    Duration,
    RemovalPolicy,
    CfnOutput
)
from constructs import Construct
from typing import Dict

class S3Stack(Stack):
    """S3 infrastructure stack for data storage"""
    
    def __init__(
        self, 
        scope: Construct, 
        construct_id: str,
        env_name: str,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        self.buckets = {}
        
        # Create KMS key for S3 encryption
        self.create_encryption_key()
        
        # Create S3 buckets
        self.create_data_buckets()
        self.create_static_assets_bucket()
        self.create_backup_bucket()
        self.create_logs_bucket()
        
    def create_encryption_key(self):
        """Create KMS key for S3 bucket encryption"""
        
        self.s3_key = kms.Key(
            self, "S3Key",
            description=f"KMS key for S3 buckets encryption - {self.env_name}",
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
                        principals=[iam.ServicePrincipal("s3.amazonaws.com")],
                        actions=[
                            "kms:Encrypt",
                            "kms:Decrypt",
                            "kms:ReEncrypt*",
                            "kms:GenerateDataKey*",
                            "kms:DescribeKey"
                        ],
                        resources=["*"]
                    )
                ]
            )
        )
        
        # Create alias for the key
        kms.Alias(
            self, "S3KeyAlias",
            alias_name=f"alias/healthconnect-s3-{self.env_name}",
            target_key=self.s3_key
        )
    
    def create_data_buckets(self):
        """Create data storage buckets"""
        
        # Analytics Data Bucket
        self.buckets["analytics"] = s3.Bucket(
            self, "AnalyticsBucket",
            bucket_name=f"healthconnect-analytics-{self.env_name}-{self.account}",
            versioned=True,
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.s3_key,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="AnalyticsDataLifecycle",
                    enabled=True,
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(30)
                        ),
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(90)
                        ),
                        s3.Transition(
                            storage_class=s3.StorageClass.DEEP_ARCHIVE,
                            transition_after=Duration.days(365)
                        )
                    ]
                )
            ],
            removal_policy=self.get_removal_policy(),
            cors=[
                s3.CorsRule(
                    allowed_methods=[s3.HttpMethods.GET, s3.HttpMethods.POST],
                    allowed_origins=["*"],
                    allowed_headers=["*"],
                    max_age=3000
                )
            ]
        )
        
        # Medical Images Bucket
        self.buckets["medical_images"] = s3.Bucket(
            self, "MedicalImagesBucket",
            bucket_name=f"healthconnect-medical-images-{self.env_name}-{self.account}",
            versioned=True,
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.s3_key,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="MedicalImagesLifecycle",
                    enabled=True,
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(90)
                        ),
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(365)
                        )
                    ]
                )
            ],
            removal_policy=self.get_removal_policy()
        )
        
        # Reports Bucket
        self.buckets["reports"] = s3.Bucket(
            self, "ReportsBucket",
            bucket_name=f"healthconnect-reports-{self.env_name}-{self.account}",
            versioned=True,
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.s3_key,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="ReportsLifecycle",
                    enabled=True,
                    expiration=Duration.days(2555),  # 7 years retention for compliance
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(30)
                        ),
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(365)
                        )
                    ]
                )
            ],
            removal_policy=self.get_removal_policy()
        )
        
        # Data Lake Bucket
        self.buckets["data_lake"] = s3.Bucket(
            self, "DataLakeBucket",
            bucket_name=f"healthconnect-data-lake-{self.env_name}-{self.account}",
            versioned=True,
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.s3_key,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DataLakeLifecycle",
                    enabled=True,
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(30)
                        ),
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(90)
                        ),
                        s3.Transition(
                            storage_class=s3.StorageClass.DEEP_ARCHIVE,
                            transition_after=Duration.days(365)
                        )
                    ]
                )
            ],
            removal_policy=self.get_removal_policy()
        )
    
    def create_static_assets_bucket(self):
        """Create bucket for static web assets"""
        
        # Static Assets Bucket
        self.buckets["static_assets"] = s3.Bucket(
            self, "StaticAssetsBucket",
            bucket_name=f"healthconnect-static-assets-{self.env_name}-{self.account}",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=True,
                block_public_policy=True,
                ignore_public_acls=True,
                restrict_public_buckets=False  # Allow CloudFront access
            ),
            removal_policy=self.get_removal_policy(),
            cors=[
                s3.CorsRule(
                    allowed_methods=[s3.HttpMethods.GET],
                    allowed_origins=["*"],
                    allowed_headers=["*"],
                    max_age=3000
                )
            ]
        )
        
        # Create CloudFront Origin Access Identity
        oai = cloudfront.OriginAccessIdentity(
            self, "StaticAssetsOAI",
            comment=f"OAI for HealthConnect static assets - {self.env_name}"
        )
        
        # Grant CloudFront access to the bucket
        self.buckets["static_assets"].grant_read(oai)
        
        # Create CloudFront distribution
        self.static_assets_distribution = cloudfront.Distribution(
            self, "StaticAssetsDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(
                    self.buckets["static_assets"],
                    origin_access_identity=oai
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                compress=True
            ),
            default_root_object="index.html",
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.minutes(30)
                )
            ],
            price_class=cloudfront.PriceClass.PRICE_CLASS_100,
            enabled=True,
            comment=f"HealthConnect static assets CDN - {self.env_name}"
        )
    
    def create_backup_bucket(self):
        """Create backup bucket for disaster recovery"""
        
        self.buckets["backup"] = s3.Bucket(
            self, "BackupBucket",
            bucket_name=f"healthconnect-backup-{self.env_name}-{self.account}",
            versioned=True,
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.s3_key,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="BackupLifecycle",
                    enabled=True,
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(30)
                        ),
                        s3.Transition(
                            storage_class=s3.StorageClass.DEEP_ARCHIVE,
                            transition_after=Duration.days(90)
                        )
                    ]
                )
            ],
            removal_policy=RemovalPolicy.RETAIN if self.env_name == "prod" else RemovalPolicy.DESTROY
        )
        
        # Enable MFA delete for production
        if self.env_name == "prod":
            # Note: MFA delete must be enabled via CLI/Console
            pass
    
    def create_logs_bucket(self):
        """Create bucket for access logs"""
        
        self.buckets["logs"] = s3.Bucket(
            self, "LogsBucket",
            bucket_name=f"healthconnect-logs-{self.env_name}-{self.account}",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="LogsLifecycle",
                    enabled=True,
                    expiration=Duration.days(90),
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(30)
                        )
                    ]
                )
            ],
            removal_policy=self.get_removal_policy()
        )
        
        # Configure access logging for other buckets
        for bucket_name, bucket in self.buckets.items():
            if bucket_name != "logs":
                bucket.add_property_override(
                    "LoggingConfiguration",
                    {
                        "DestinationBucketName": self.buckets["logs"].bucket_name,
                        "LogFilePrefix": f"{bucket_name}/"
                    }
                )
    
    def get_removal_policy(self):
        """Get removal policy based on environment"""
        if self.env_name == "prod":
            return RemovalPolicy.RETAIN
        else:
            return RemovalPolicy.DESTROY
    
    @property
    def account(self) -> str:
        """Get AWS account ID"""
        return Stack.of(self).account
