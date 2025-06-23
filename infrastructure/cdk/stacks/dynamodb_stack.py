"""
DynamoDB Stack for HealthConnect AI
Implements all DynamoDB tables with proper configurations
"""

from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_kms as kms,
    aws_iam as iam,
    RemovalPolicy,
    CfnOutput
)
from constructs import Construct
from typing import Dict

class DynamoDBStack(Stack):
    """DynamoDB infrastructure stack"""
    
    def __init__(
        self, 
        scope: Construct, 
        construct_id: str,
        env_name: str,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        self.tables = {}
        
        # Create KMS key for DynamoDB encryption
        self.create_encryption_key()
        
        # Create all DynamoDB tables
        self.create_health_records_table()
        self.create_device_tables()
        self.create_consultation_tables()
        self.create_emergency_tables()
        self.create_analytics_tables()
        self.create_websocket_tables()
        
    def create_encryption_key(self):
        """Create KMS key for DynamoDB table encryption"""
        
        self.dynamodb_key = kms.Key(
            self, "DynamoDBKey",
            description=f"KMS key for DynamoDB tables encryption - {self.env_name}",
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
                        principals=[iam.ServicePrincipal("dynamodb.amazonaws.com")],
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
            self, "DynamoDBKeyAlias",
            alias_name=f"alias/healthconnect-dynamodb-{self.env_name}",
            target_key=self.dynamodb_key
        )
    
    def create_health_records_table(self):
        """Create health records table"""
        
        self.tables["health_records"] = dynamodb.Table(
            self, "HealthRecordsTable",
            table_name=f"healthconnect-health-records-{self.env_name}",
            partition_key=dynamodb.Attribute(
                name="patient_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.dynamodb_key,
            point_in_time_recovery=True,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
            removal_policy=self.get_removal_policy(),
            time_to_live_attribute="ttl"
        )
        
        # Add GSI for querying by data type
        self.tables["health_records"].add_global_secondary_index(
            index_name="DataTypeIndex",
            partition_key=dynamodb.Attribute(
                name="data_type",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Add GSI for querying by provider
        self.tables["health_records"].add_global_secondary_index(
            index_name="ProviderIndex",
            partition_key=dynamodb.Attribute(
                name="provider_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Analysis Results Table
        self.tables["analysis_results"] = dynamodb.Table(
            self, "AnalysisResultsTable",
            table_name=f"healthconnect-analysis-results-{self.env_name}",
            partition_key=dynamodb.Attribute(
                name="analysis_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.dynamodb_key,
            point_in_time_recovery=True,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
            removal_policy=self.get_removal_policy(),
            time_to_live_attribute="ttl"
        )
        
        # Add GSI for querying by patient
        self.tables["analysis_results"].add_global_secondary_index(
            index_name="PatientIndex",
            partition_key=dynamodb.Attribute(
                name="patient_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Add GSI for querying by urgency level
        self.tables["analysis_results"].add_global_secondary_index(
            index_name="UrgencyIndex",
            partition_key=dynamodb.Attribute(
                name="urgency_level",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
    
    def create_device_tables(self):
        """Create device-related tables"""
        
        # Device Registry Table
        self.tables["device_registry"] = dynamodb.Table(
            self, "DeviceRegistryTable",
            table_name=f"healthconnect-device-registry-{self.env_name}",
            partition_key=dynamodb.Attribute(
                name="device_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.dynamodb_key,
            point_in_time_recovery=True,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
            removal_policy=self.get_removal_policy()
        )
        
        # Add GSI for querying by patient
        self.tables["device_registry"].add_global_secondary_index(
            index_name="PatientIndex",
            partition_key=dynamodb.Attribute(
                name="patient_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="device_type",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Add GSI for querying by device type
        self.tables["device_registry"].add_global_secondary_index(
            index_name="DeviceTypeIndex",
            partition_key=dynamodb.Attribute(
                name="device_type",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="status",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Device Data Table
        self.tables["device_data"] = dynamodb.Table(
            self, "DeviceDataTable",
            table_name=f"healthconnect-device-data-{self.env_name}",
            partition_key=dynamodb.Attribute(
                name="device_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.dynamodb_key,
            point_in_time_recovery=True,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
            removal_policy=self.get_removal_policy(),
            time_to_live_attribute="ttl"
        )
        
        # Add GSI for querying by patient
        self.tables["device_data"].add_global_secondary_index(
            index_name="PatientIndex",
            partition_key=dynamodb.Attribute(
                name="patient_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
    
    def create_consultation_tables(self):
        """Create consultation-related tables"""
        
        # Consultation Sessions Table
        self.tables["consultation_sessions"] = dynamodb.Table(
            self, "ConsultationSessionsTable",
            table_name=f"healthconnect-consultation-sessions-{self.env_name}",
            partition_key=dynamodb.Attribute(
                name="session_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.dynamodb_key,
            point_in_time_recovery=True,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
            removal_policy=self.get_removal_policy(),
            time_to_live_attribute="ttl"
        )
        
        # Add GSI for querying by patient
        self.tables["consultation_sessions"].add_global_secondary_index(
            index_name="PatientIndex",
            partition_key=dynamodb.Attribute(
                name="patient_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Add GSI for querying by provider
        self.tables["consultation_sessions"].add_global_secondary_index(
            index_name="ProviderIndex",
            partition_key=dynamodb.Attribute(
                name="provider_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Add GSI for querying by status
        self.tables["consultation_sessions"].add_global_secondary_index(
            index_name="StatusIndex",
            partition_key=dynamodb.Attribute(
                name="status",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Healthcare Providers Table
        self.tables["healthcare_providers"] = dynamodb.Table(
            self, "HealthcareProvidersTable",
            table_name=f"healthconnect-healthcare-providers-{self.env_name}",
            partition_key=dynamodb.Attribute(
                name="provider_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.dynamodb_key,
            point_in_time_recovery=True,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
            removal_policy=self.get_removal_policy()
        )
        
        # Add GSI for querying by specialty
        self.tables["healthcare_providers"].add_global_secondary_index(
            index_name="SpecialtyIndex",
            partition_key=dynamodb.Attribute(
                name="specialty",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="availability_status",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Consultation Queue Table
        self.tables["consultation_queue"] = dynamodb.Table(
            self, "ConsultationQueueTable",
            table_name=f"healthconnect-consultation-queue-{self.env_name}",
            partition_key=dynamodb.Attribute(
                name="queue_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.dynamodb_key,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
            removal_policy=self.get_removal_policy(),
            time_to_live_attribute="ttl"
        )
        
        # Add GSI for querying by urgency
        self.tables["consultation_queue"].add_global_secondary_index(
            index_name="UrgencyIndex",
            partition_key=dynamodb.Attribute(
                name="urgency_level",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="queued_at",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
    
    def create_emergency_tables(self):
        """Create emergency-related tables"""
        
        # Emergency Alerts Table
        self.tables["emergency_alerts"] = dynamodb.Table(
            self, "EmergencyAlertsTable",
            table_name=f"healthconnect-emergency-alerts-{self.env_name}",
            partition_key=dynamodb.Attribute(
                name="alert_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.dynamodb_key,
            point_in_time_recovery=True,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
            removal_policy=self.get_removal_policy(),
            time_to_live_attribute="ttl"
        )
        
        # Add GSI for querying by patient
        self.tables["emergency_alerts"].add_global_secondary_index(
            index_name="PatientIndex",
            partition_key=dynamodb.Attribute(
                name="patient_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Add GSI for querying by status
        self.tables["emergency_alerts"].add_global_secondary_index(
            index_name="StatusIndex",
            partition_key=dynamodb.Attribute(
                name="status",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Add GSI for querying by urgency level
        self.tables["emergency_alerts"].add_global_secondary_index(
            index_name="UrgencyIndex",
            partition_key=dynamodb.Attribute(
                name="urgency_level",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Emergency Contacts Table
        self.tables["emergency_contacts"] = dynamodb.Table(
            self, "EmergencyContactsTable",
            table_name=f"healthconnect-emergency-contacts-{self.env_name}",
            partition_key=dynamodb.Attribute(
                name="patient_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="contact_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.dynamodb_key,
            point_in_time_recovery=True,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
            removal_policy=self.get_removal_policy(),
            time_to_live_attribute="ttl"
        )
    
    def create_analytics_tables(self):
        """Create analytics-related tables"""
        
        # Analytics Results Table
        self.tables["analytics_results"] = dynamodb.Table(
            self, "AnalyticsResultsTable",
            table_name=f"healthconnect-analytics-results-{self.env_name}",
            partition_key=dynamodb.Attribute(
                name="analytics_run_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.dynamodb_key,
            point_in_time_recovery=True,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
            removal_policy=self.get_removal_policy(),
            time_to_live_attribute="ttl"
        )
        
        # Add GSI for querying by analytics type
        self.tables["analytics_results"].add_global_secondary_index(
            index_name="TypeIndex",
            partition_key=dynamodb.Attribute(
                name="analytics_type",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Population Metrics Table
        self.tables["population_metrics"] = dynamodb.Table(
            self, "PopulationMetricsTable",
            table_name=f"healthconnect-population-metrics-{self.env_name}",
            partition_key=dynamodb.Attribute(
                name="metric_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.dynamodb_key,
            point_in_time_recovery=True,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
            removal_policy=self.get_removal_policy(),
            time_to_live_attribute="ttl"
        )
    
    # Add GSI for querying by metric type
    self.tables["population_metrics"].add_global_secondary_index(
        index_name="MetricTypeIndex",
        partition_key=dynamodb.Attribute(
            name="metric_type",
            type=dynamodb.AttributeType.STRING
        ),
        sort_key=dynamodb.Attribute(
            name="timestamp",
            type=dynamodb.AttributeType.STRING
        ),
        projection_type=dynamodb.ProjectionType.ALL
    )
    
    # Predictive Models Table
    self.tables["predictive_models"] = dynamodb.Table(
        self, "PredictiveModelsTable",
        table_name=f"healthconnect-predictive-models-{self.env_name}",
        partition_key=dynamodb.Attribute(
            name="model_id",
            type=dynamodb.AttributeType.STRING
        ),
        billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
        encryption_key=self.dynamodb_key,
        point_in_time_recovery=True,
        stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
        removal_policy=self.get_removal_policy()
    )
    
    # Add GSI for querying by model type
    self.tables["predictive_models"].add_global_secondary_index(
        index_name="ModelTypeIndex",
        partition_key=dynamodb.Attribute(
            name="model_type",
            type=dynamodb.AttributeType.STRING
        ),
        sort_key=dynamodb.Attribute(
            name="created_at",
            type=dynamodb.AttributeType.STRING
        ),
        projection_type=dynamodb.ProjectionType.ALL
    )

def create_websocket_tables(self):
    """Create WebSocket-related tables"""
    
    # WebSocket Connections Table
    self.tables["websocket_connections"] = dynamodb.Table(
        self, "WebSocketConnectionsTable",
        table_name=f"healthconnect-websocket-connections-{self.env_name}",
        partition_key=dynamodb.Attribute(
            name="connection_id",
            type=dynamodb.AttributeType.STRING
        ),
        billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
        encryption_key=self.dynamodb_key,
        stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
        removal_policy=self.get_removal_policy(),
        time_to_live_attribute="ttl"
    )
    
    # Add GSI for querying by session
    self.tables["websocket_connections"].add_global_secondary_index(
        index_name="SessionIndex",
        partition_key=dynamodb.Attribute(
            name="session_id",
            type=dynamodb.AttributeType.STRING
        ),
        projection_type=dynamodb.ProjectionType.ALL
    )
    
    # WebSocket Messages Table
    self.tables["websocket_messages"] = dynamodb.Table(
        self, "WebSocketMessagesTable",
        table_name=f"healthconnect-websocket-messages-{self.env_name}",
        partition_key=dynamodb.Attribute(
            name="message_id",
            type=dynamodb.AttributeType.STRING
        ),
        billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
        encryption_key=self.dynamodb_key,
        removal_policy=self.get_removal_policy(),
        time_to_live_attribute="ttl"
    )
    
    # Add GSI for querying by session
    self.tables["websocket_messages"].add_global_secondary_index(
        index_name="SessionIndex",
        partition_key=dynamodb.Attribute(
            name="session_id",
            type=dynamodb.AttributeType.STRING
        ),
        sort_key=dynamodb.Attribute(
            name="timestamp",
            type=dynamodb.AttributeType.STRING
        ),
        projection_type=dynamodb.ProjectionType.ALL
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

@property
def region(self) -> str:
    """Get AWS region"""
    return Stack.of(self).region
