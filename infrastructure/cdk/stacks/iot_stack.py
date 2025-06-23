"""
IoT Stack for HealthConnect AI
Implements AWS IoT Core infrastructure for medical device connectivity
"""

from aws_cdk import (
    Stack,
    aws_iot as iot,
    aws_iam as iam,
    aws_dynamodb as dynamodb,
    aws_lambda as lambda_,
    aws_events as events,
    aws_events_targets as targets,
    aws_logs as logs,
    aws_kinesis as kinesis,
    aws_kinesisfirehose as firehose,
    aws_s3 as s3,
    CfnOutput
)
from constructs import Construct
from typing import Dict, Any

class IoTStack(Stack):
    """IoT Core infrastructure stack for medical devices"""
    
    def __init__(
        self, 
        scope: Construct, 
        construct_id: str,
        env_name: str,
        dynamodb_tables: Dict[str, dynamodb.Table],
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        self.dynamodb_tables = dynamodb_tables
        
        # Create IoT resources
        self.iot_resources = {}
        self.create_iot_thing_types()
        self.create_iot_policies()
        self.create_iot_rules()
        self.create_device_registry()
        self.create_data_streams()
        
    def create_iot_thing_types(self):
        """Create IoT Thing Types for different medical devices"""
        
        # Heart Rate Monitor Thing Type
        self.heart_rate_monitor_type = iot.CfnThingType(
            self, "HeartRateMonitorType",
            thing_type_name=f"HealthConnect-HeartRateMonitor-{self.env_name}",
            thing_type_description="Heart rate monitoring devices",
            thing_type_properties=iot.CfnThingType.ThingTypePropertiesProperty(
                thing_type_description="Continuous heart rate monitoring device",
                searchable_attributes=[
                    "manufacturer",
                    "model",
                    "firmware_version",
                    "patient_id",
                    "location"
                ]
            )
        )
        
        # Blood Pressure Monitor Thing Type
        self.blood_pressure_monitor_type = iot.CfnThingType(
            self, "BloodPressureMonitorType",
            thing_type_name=f"HealthConnect-BloodPressureMonitor-{self.env_name}",
            thing_type_description="Blood pressure monitoring devices",
            thing_type_properties=iot.CfnThingType.ThingTypePropertiesProperty(
                thing_type_description="Automated blood pressure monitoring device",
                searchable_attributes=[
                    "manufacturer",
                    "model",
                    "calibration_date",
                    "patient_id",
                    "location"
                ]
            )
        )
        
        # Glucose Monitor Thing Type
        self.glucose_monitor_type = iot.CfnThingType(
            self, "GlucoseMonitorType",
            thing_type_name=f"HealthConnect-GlucoseMonitor-{self.env_name}",
            thing_type_description="Continuous glucose monitoring devices",
            thing_type_properties=iot.CfnThingType.ThingTypePropertiesProperty(
                thing_type_description="Continuous glucose monitoring device",
                searchable_attributes=[
                    "manufacturer",
                    "model",
                    "sensor_expiry",
                    "patient_id",
                    "location"
                ]
            )
        )
        
        # Temperature Sensor Thing Type
        self.temperature_sensor_type = iot.CfnThingType(
            self, "TemperatureSensorType",
            thing_type_name=f"HealthConnect-TemperatureSensor-{self.env_name}",
            thing_type_description="Temperature monitoring devices",
            thing_type_properties=iot.CfnThingType.ThingTypePropertiesProperty(
                thing_type_description="Continuous temperature monitoring device",
                searchable_attributes=[
                    "manufacturer",
                    "model",
                    "accuracy_class",
                    "patient_id",
                    "location"
                ]
            )
        )
        
        # Pulse Oximeter Thing Type
        self.pulse_oximeter_type = iot.CfnThingType(
            self, "PulseOximeterType",
            thing_type_name=f"HealthConnect-PulseOximeter-{self.env_name}",
            thing_type_description="Pulse oximetry devices",
            thing_type_properties=iot.CfnThingType.ThingTypePropertiesProperty(
                thing_type_description="Pulse oximetry monitoring device",
                searchable_attributes=[
                    "manufacturer",
                    "model",
                    "sensor_type",
                    "patient_id",
                    "location"
                ]
            )
        )
        
        # Activity Tracker Thing Type
        self.activity_tracker_type = iot.CfnThingType(
            self, "ActivityTrackerType",
            thing_type_name=f"HealthConnect-ActivityTracker-{self.env_name}",
            thing_type_description="Activity and fitness tracking devices",
            thing_type_properties=iot.CfnThingType.ThingTypePropertiesProperty(
                thing_type_description="Medical-grade activity tracking device",
                searchable_attributes=[
                    "manufacturer",
                    "model",
                    "wear_location",
                    "patient_id",
                    "location"
                ]
            )
        )
        
        # ECG Monitor Thing Type
        self.ecg_monitor_type = iot.CfnThingType(
            self, "ECGMonitorType",
            thing_type_name=f"HealthConnect-ECGMonitor-{self.env_name}",
            thing_type_description="Electrocardiogram monitoring devices",
            thing_type_properties=iot.CfnThingType.ThingTypePropertiesProperty(
                thing_type_description="Portable ECG monitoring device",
                searchable_attributes=[
                    "manufacturer",
                    "model",
                    "lead_configuration",
                    "patient_id",
                    "location"
                ]
            )
        )
        
        # Respiratory Monitor Thing Type
        self.respiratory_monitor_type = iot.CfnThingType(
            self, "RespiratoryMonitorType",
            thing_type_name=f"HealthConnect-RespiratoryMonitor-{self.env_name}",
            thing_type_description="Respiratory monitoring devices",
            thing_type_properties=iot.CfnThingType.ThingTypePropertiesProperty(
                thing_type_description="Respiratory rate monitoring device",
                searchable_attributes=[
                    "manufacturer",
                    "model",
                    "sensor_type",
                    "patient_id",
                    "location"
                ]
            )
        )
    
    def create_iot_policies(self):
        """Create IoT policies for device access control"""
        
        # Device Data Publishing Policy
        device_publish_policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "iot:Connect"
                    ],
                    "Resource": f"arn:aws:iot:{self.region}:{self.account}:client/${{iot:Connection.Thing.ThingName}}"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "iot:Publish"
                    ],
                    "Resource": [
                        f"arn:aws:iot:{self.region}:{self.account}:topic/healthconnect/devices/${{iot:Connection.Thing.ThingName}}/data",
                        f"arn:aws:iot:{self.region}:{self.account}:topic/healthconnect/devices/${{iot:Connection.Thing.ThingName}}/status",
                        f"arn:aws:iot:{self.region}:{self.account}:topic/healthconnect/devices/${{iot:Connection.Thing.ThingName}}/alerts"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "iot:Subscribe"
                    ],
                    "Resource": [
                        f"arn:aws:iot:{self.region}:{self.account}:topicfilter/healthconnect/devices/${{iot:Connection.Thing.ThingName}}/commands",
                        f"arn:aws:iot:{self.region}:{self.account}:topicfilter/healthconnect/devices/${{iot:Connection.Thing.ThingName}}/config"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "iot:Receive"
                    ],
                    "Resource": [
                        f"arn:aws:iot:{self.region}:{self.account}:topic/healthconnect/devices/${{iot:Connection.Thing.ThingName}}/commands",
                        f"arn:aws:iot:{self.region}:{self.account}:topic/healthconnect/devices/${{iot:Connection.Thing.ThingName}}/config"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "iot:UpdateThingShadow",
                        "iot:GetThingShadow"
                    ],
                    "Resource": f"arn:aws:iot:{self.region}:{self.account}:thing/${{iot:Connection.Thing.ThingName}}"
                }
            ]
        }
        
        self.device_policy = iot.CfnPolicy(
            self, "DevicePolicy",
            policy_name=f"HealthConnect-DevicePolicy-{self.env_name}",
            policy_document=device_publish_policy_document
        )
        
        # Emergency Device Policy (for critical alerts)
        emergency_policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "iot:Connect"
                    ],
                    "Resource": f"arn:aws:iot:{self.region}:{self.account}:client/${{iot:Connection.Thing.ThingName}}"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "iot:Publish"
                    ],
                    "Resource": [
                        f"arn:aws:iot:{self.region}:{self.account}:topic/healthconnect/emergency/${{iot:Connection.Thing.ThingName}}",
                        f"arn:aws:iot:{self.region}:{self.account}:topic/healthconnect/devices/${{iot:Connection.Thing.ThingName}}/data",
                        f"arn:aws:iot:{self.region}:{self.account}:topic/healthconnect/devices/${{iot:Connection.Thing.ThingName}}/status"
                    ]
                }
            ]
        }
        
        self.emergency_device_policy = iot.CfnPolicy(
            self, "EmergencyDevicePolicy",
            policy_name=f"HealthConnect-EmergencyDevicePolicy-{self.env_name}",
            policy_document=emergency_policy_document
        )
    
    def create_iot_rules(self):
        """Create IoT rules for data processing and routing"""
        
        # Create IAM role for IoT rules
        iot_rules_role = iam.Role(
            self, "IoTRulesRole",
            role_name=f"HealthConnect-IoTRules-Role-{self.env_name}",
            assumed_by=iam.ServicePrincipal("iot.amazonaws.com"),
            inline_policies={
                "IoTRulesPolicy": iam.PolicyDocument(
                    statements=[
                        # DynamoDB permissions
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "dynamodb:PutItem",
                                "dynamodb:UpdateItem"
                            ],
                            resources=[
                                self.dynamodb_tables["device_data"].table_arn,
                                self.dynamodb_tables["device_registry"].table_arn
                            ]
                        ),
                        # Kinesis permissions
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "kinesis:PutRecord",
                                "kinesis:PutRecords"
                            ],
                            resources=[f"arn:aws:kinesis:{self.region}:{self.account}:stream/healthconnect-*"]
                        ),
                        # Lambda permissions
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["lambda:InvokeFunction"],
                            resources=[f"arn:aws:lambda:{self.region}:{self.account}:function:healthconnect-*"]
                        ),
                        # SNS permissions
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["sns:Publish"],
                            resources=[f"arn:aws:sns:{self.region}:{self.account}:healthconnect-*"]
                        )
                    ]
                )
            }
        )
        
        # Device Data Processing Rule
        device_data_rule = iot.CfnTopicRule(
            self, "DeviceDataRule",
            rule_name=f"HealthConnect_DeviceData_{self.env_name}",
            topic_rule_payload=iot.CfnTopicRule.TopicRulePayloadProperty(
                description="Process and store device health data",
                sql=f"SELECT *, timestamp() as received_timestamp, topic() as topic FROM 'healthconnect/devices/+/data'",
                rule_disabled=False,
                actions=[
                    # Store in DynamoDB
                    iot.CfnTopicRule.ActionProperty(
                        dynamo_d_bv2=iot.CfnTopicRule.DynamoDBv2ActionProperty(
                            role_arn=iot_rules_role.role_arn,
                            put_item=iot.CfnTopicRule.PutItemInputProperty(
                                table_name=self.dynamodb_tables["device_data"].table_name
                            )
                        )
                    ),
                    # Send to Kinesis for real-time processing
                    iot.CfnTopicRule.ActionProperty(
                        kinesis=iot.CfnTopicRule.KinesisActionProperty(
                            role_arn=iot_rules_role.role_arn,
                            stream_name=f"healthconnect-device-data-{self.env_name}",
                            partition_key="${device_id}"
                        )
                    )
                ]
            )
        )
        
        # Emergency Alert Rule
        emergency_alert_rule = iot.CfnTopicRule(
            self, "EmergencyAlertRule",
            rule_name=f"HealthConnect_EmergencyAlert_{self.env_name}",
            topic_rule_payload=iot.CfnTopicRule.TopicRulePayloadProperty(
                description="Process emergency alerts from devices",
                sql=f"SELECT *, timestamp() as received_timestamp FROM 'healthconnect/emergency/+' WHERE urgency_level = 'CRITICAL' OR urgency_level = 'HIGH'",
                rule_disabled=False,
                actions=[
                    # Trigger emergency response Lambda
                    iot.CfnTopicRule.ActionProperty(
                        lambda_=iot.CfnTopicRule.LambdaActionProperty(
                            function_arn=f"arn:aws:lambda:{self.region}:{self.account}:function:healthconnect-emergency-response-{self.env_name}"
                        )
                    ),
                    # Send to SNS for immediate notification
                    iot.CfnTopicRule.ActionProperty(
                        sns=iot.CfnTopicRule.SnsActionProperty(
                            role_arn=iot_rules_role.role_arn,
                            target_arn=f"arn:aws:sns:{self.region}:{self.account}:healthconnect-emergency-{self.env_name}",
                            message_format="RAW"
                        )
                    )
                ]
            )
        )
        
        # Device Status Update Rule
        device_status_rule = iot.CfnTopicRule(
            self, "DeviceStatusRule",
            rule_name=f"HealthConnect_DeviceStatus_{self.env_name}",
            topic_rule_payload=iot.CfnTopicRule.TopicRulePayloadProperty(
                description="Update device status and registry information",
                sql=f"SELECT *, timestamp() as last_seen FROM 'healthconnect/devices/+/status'",
                rule_disabled=False,
                actions=[
                    # Update device registry
                    iot.CfnTopicRule.ActionProperty(
                        dynamo_d_bv2=iot.CfnTopicRule.DynamoDBv2ActionProperty(
                            role_arn=iot_rules_role.role_arn,
                            put_item=iot.CfnTopicRule.PutItemInputProperty(
                                table_name=self.dynamodb_tables["device_registry"].table_name
                            )
                        )
                    )
                ]
            )
        )
        
        # Anomaly Detection Rule
        anomaly_detection_rule = iot.CfnTopicRule(
            self, "AnomalyDetectionRule",
            rule_name=f"HealthConnect_AnomalyDetection_{self.env_name}",
            topic_rule_payload=iot.CfnTopicRule.TopicRulePayloadProperty(
                description="Detect anomalies in health data",
                sql=f"""SELECT * FROM 'healthconnect/devices/+/data' 
                        WHERE (heart_rate < 40 OR heart_rate > 150) 
                        OR (systolic_pressure > 200 OR systolic_pressure < 80)
                        OR (oxygen_saturation < 88)
                        OR (temperature > 40.0 OR temperature < 35.0)""",
                rule_disabled=False,
                actions=[
                    # Trigger health analysis Lambda
                    iot.CfnTopicRule.ActionProperty(
                        lambda_=iot.CfnTopicRule.LambdaActionProperty(
                            function_arn=f"arn:aws:lambda:{self.region}:{self.account}:function:healthconnect-health-analysis-{self.env_name}"
                        )
                    )
                ]
            )
        )
        
        # Store IoT rules in resources
        self.iot_resources.update({
            "device_data_rule": device_data_rule,
            "emergency_alert_rule": emergency_alert_rule,
            "device_status_rule": device_status_rule,
            "anomaly_detection_rule": anomaly_detection_rule,
            "iot_rules_role": iot_rules_role
        })
    
    def create_device_registry(self):
        """Create device registry and fleet indexing"""
        
        # Enable fleet indexing for device search and monitoring
        fleet_indexing = iot.CfnFleetMetric(
            self, "DeviceFleetMetric",
            metric_name=f"HealthConnect-ActiveDevices-{self.env_name}",
            description="Track active health monitoring devices",
            query_string="thingTypeName:HealthConnect-* AND connectivity.connected:true",
            aggregation_type=iot.CfnFleetMetric.AggregationTypeProperty(
                name="Statistics",
                values=["count"]
            ),
            period=300,  # 5 minutes
            aggregation_field="registry.version",
            query_version="2016-03-23"
        )
        
        # Create device groups for different types
        device_groups = [
            "HeartRateMonitors",
            "BloodPressureMonitors", 
            "GlucoseMonitors",
            "TemperatureSensors",
            "PulseOximeters",
            "ActivityTrackers",
            "ECGMonitors",
            "RespiratoryMonitors"
        ]
        
        for group_name in device_groups:
            device_group = iot.CfnThingGroup(
                self, f"{group_name}Group",
                thing_group_name=f"HealthConnect-{group_name}-{self.env_name}",
                thing_group_properties=iot.CfnThingGroup.ThingGroupPropertiesProperty(
                    thing_group_description=f"Group for {group_name} devices",
                    attribute_payload=iot.CfnThingGroup.AttributePayloadProperty(
                        attributes={
                            "DeviceCategory": group_name,
                            "Environment": self.env_name,
                            "Project": "HealthConnect-AI"
                        }
                    )
                )
            )
        
        # Store fleet indexing in resources
        self.iot_resources["fleet_indexing"] = fleet_indexing
    
    def create_data_streams(self):
        """Create Kinesis streams for real-time data processing"""
        
        # Device Data Stream
        device_data_stream = kinesis.Stream(
            self, "DeviceDataStream",
            stream_name=f"healthconnect-device-data-{self.env_name}",
            shard_count=2 if self.env_name == "prod" else 1,
            retention_period=kinesis.StreamMode.PROVISIONED
        )
        
        # Emergency Alerts Stream
        emergency_stream = kinesis.Stream(
            self, "EmergencyStream", 
            stream_name=f"healthconnect-emergency-{self.env_name}",
            shard_count=1,
            retention_period=kinesis.StreamMode.PROVISIONED
        )
        
        # Create Kinesis Firehose for data archival
        # S3 bucket for archived data
        archive_bucket = s3.Bucket(
            self, "DeviceDataArchive",
            bucket_name=f"healthconnect-device-archive-{self.env_name}-{self.account}",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="ArchiveRule",
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
            ]
        )
        
        # Firehose delivery role
        firehose_role = iam.Role(
            self, "FirehoseDeliveryRole",
            role_name=f"HealthConnect-Firehose-Role-{self.env_name}",
            assumed_by=iam.ServicePrincipal("firehose.amazonaws.com"),
            inline_policies={
                "FirehoseDeliveryPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "s3:AbortMultipartUpload",
                                "s3:GetBucketLocation",
                                "s3:GetObject",
                                "s3:ListBucket",
                                "s3:ListBucketMultipartUploads",
                                "s3:PutObject"
                            ],
                            resources=[
                                archive_bucket.bucket_arn,
                                f"{archive_bucket.bucket_arn}/*"
                            ]
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "kinesis:DescribeStream",
                                "kinesis:GetShardIterator",
                                "kinesis:GetRecords"
                            ],
                            resources=[
                                device_data_stream.stream_arn
                            ]
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "logs:PutLogEvents"
                            ],
                            resources=["*"]
                        )
                    ]
                )
            }
        )
        
        # Firehose delivery stream
        firehose_stream = firehose.CfnDeliveryStream(
            self, "DeviceDataFirehose",
            delivery_stream_name=f"healthconnect-device-data-firehose-{self.env_name}",
            delivery_stream_type="KinesisStreamAsSource",
            kinesis_stream_source_configuration=firehose.CfnDeliveryStream.KinesisStreamSourceConfigurationProperty(
                kinesis_stream_arn=device_data_stream.stream_arn,
                role_arn=firehose_role.role_arn
            ),
            extended_s3_destination_configuration=firehose.CfnDeliveryStream.ExtendedS3DestinationConfigurationProperty(
                bucket_arn=archive_bucket.bucket_arn,
                role_arn=firehose_role.role_arn,
                prefix="year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/",
                error_output_prefix="errors/",
                buffering_hints=firehose.CfnDeliveryStream.BufferingHintsProperty(
                    size_in_m_bs=5,
                    interval_in_seconds=300
                ),
                compression_format="GZIP",
                data_format_conversion_configuration=firehose.CfnDeliveryStream.DataFormatConversionConfigurationProperty(
                    enabled=True,
                    output_format_configuration=firehose.CfnDeliveryStream.OutputFormatConfigurationProperty(
                        serializer=firehose.CfnDeliveryStream.SerializerProperty(
                            parquet_ser_de=firehose.CfnDeliveryStream.ParquetSerDeProperty()
                        )
                    )
                ),
                cloud_watch_logging_options=firehose.CfnDeliveryStream.CloudWatchLoggingOptionsProperty(
                    enabled=True,
                    log_group_name=f"/aws/kinesisfirehose/healthconnect-{self.env_name}"
                )
            )
        )
        
        # Store streams in resources
        self.iot_resources.update({
            "device_data_stream": device_data_stream,
            "emergency_stream": emergency_stream,
            "archive_bucket": archive_bucket,
            "firehose_stream": firehose_stream
        })
        
        # Get IoT endpoint
        self.iot_resources["endpoint"] = f"https://{self.get_iot_endpoint()}"
    
    def get_iot_endpoint(self) -> str:
        """Get IoT Core endpoint for the region"""
        # This would typically be retrieved from IoT Core
        # For CDK, we construct it based on the standard format
        return f"a{self.account}-ats.iot.{self.region}.amazonaws.com"
    
    @property
    def account(self) -> str:
        """Get AWS account ID"""
        return Stack.of(self).account
    
    @property
    def region(self) -> str:
        """Get AWS region"""
        return Stack.of(self).region
