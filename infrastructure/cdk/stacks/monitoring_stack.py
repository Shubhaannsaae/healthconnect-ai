"""
Monitoring Stack for HealthConnect AI
Implements comprehensive monitoring, alerting, and observability
"""

from aws_cdk import (
    Stack,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cw_actions,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subs,
    aws_logs as logs,
    aws_lambda as lambda_,
    aws_apigateway as apigateway,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_events as events,
    aws_events_targets as targets,
    Duration,
    CfnOutput
)
from constructs import Construct
from typing import Dict, Any

class MonitoringStack(Stack):
    """Monitoring and observability infrastructure stack"""
    
    def __init__(
        self, 
        scope: Construct, 
        construct_id: str,
        env_name: str,
        lambda_functions: Dict[str, lambda_.Function],
        api_gateway: apigateway.RestApi,
        dynamodb_tables: Dict[str, dynamodb.Table],
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        self.lambda_functions = lambda_functions
        self.api_gateway = api_gateway
        self.dynamodb_tables = dynamodb_tables
        
        # Create monitoring resources
        self.create_sns_topics()
        self.create_cloudwatch_dashboards()
        self.create_lambda_alarms()
        self.create_api_gateway_alarms()
        self.create_dynamodb_alarms()
        self.create_custom_metrics()
        self.create_log_insights_queries()
        
    def create_sns_topics(self):
        """Create SNS topics for alerts"""
        
        # Critical Alerts Topic
        self.critical_alerts_topic = sns.Topic(
            self, "CriticalAlerts",
            topic_name=f"healthconnect-critical-alerts-{self.env_name}",
            display_name=f"HealthConnect Critical Alerts - {self.env_name.upper()}"
        )
        
        # Add email subscription for critical alerts
        self.critical_alerts_topic.add_subscription(
            sns_subs.EmailSubscription("alerts@healthconnect.ai")
        )
        
        # Warning Alerts Topic
        self.warning_alerts_topic = sns.Topic(
            self, "WarningAlerts",
            topic_name=f"healthconnect-warning-alerts-{self.env_name}",
            display_name=f"HealthConnect Warning Alerts - {self.env_name.upper()}"
        )
        
        # Add email subscription for warning alerts
        self.warning_alerts_topic.add_subscription(
            sns_subs.EmailSubscription("monitoring@healthconnect.ai")
        )
        
        # Emergency Alerts Topic (for patient emergencies)
        self.emergency_alerts_topic = sns.Topic(
            self, "EmergencyAlerts",
            topic_name=f"healthconnect-emergency-alerts-{self.env_name}",
            display_name=f"HealthConnect Emergency Alerts - {self.env_name.upper()}"
        )
        
        # Add multiple subscriptions for emergency alerts
        self.emergency_alerts_topic.add_subscription(
            sns_subs.EmailSubscription("emergency@healthconnect.ai")
        )
        self.emergency_alerts_topic.add_subscription(
            sns_subs.SmsSubscription("+1234567890")  # Replace with actual emergency number
        )
    
    def create_cloudwatch_dashboards(self):
        """Create CloudWatch dashboards for monitoring"""
        
        # Main Application Dashboard
        self.main_dashboard = cloudwatch.Dashboard(
            self, "MainDashboard",
            dashboard_name=f"HealthConnect-Main-{self.env_name}",
            widgets=[
                # API Gateway metrics
                [
                    cloudwatch.GraphWidget(
                        title="API Gateway Requests",
                        left=[
                            cloudwatch.Metric(
                                namespace="AWS/ApiGateway",
                                metric_name="Count",
                                dimensions_map={
                                    "ApiName": self.api_gateway.rest_api_name
                                },
                                statistic="Sum"
                            )
                        ],
                        width=12,
                        height=6
                    )
                ],
                [
                    cloudwatch.GraphWidget(
                        title="API Gateway Latency",
                        left=[
                            cloudwatch.Metric(
                                namespace="AWS/ApiGateway",
                                metric_name="Latency",
                                dimensions_map={
                                    "ApiName": self.api_gateway.rest_api_name
                                },
                                statistic="Average"
                            )
                        ],
                        width=12,
                        height=6
                    )
                ],
                [
                    cloudwatch.GraphWidget(
                        title="API Gateway Errors",
                        left=[
                            cloudwatch.Metric(
                                namespace="AWS/ApiGateway",
                                metric_name="4XXError",
                                dimensions_map={
                                    "ApiName": self.api_gateway.rest_api_name
                                },
                                statistic="Sum"
                            ),
                            cloudwatch.Metric(
                                namespace="AWS/ApiGateway",
                                metric_name="5XXError",
                                dimensions_map={
                                    "ApiName": self.api_gateway.rest_api_name
                                },
                                statistic="Sum"
                            )
                        ],
                        width=12,
                        height=6
                    )
                ]
            ]
        )
        
        # Lambda Functions Dashboard
        lambda_widgets = []
        for func_name, func in self.lambda_functions.items():
            lambda_widgets.extend([
                [
                    cloudwatch.GraphWidget(
                        title=f"{func_name} - Invocations",
                        left=[func.metric_invocations()],
                        width=6,
                        height=6
                    ),
                    cloudwatch.GraphWidget(
                        title=f"{func_name} - Duration",
                        left=[func.metric_duration()],
                        width=6,
                        height=6
                    )
                ],
                [
                    cloudwatch.GraphWidget(
                        title=f"{func_name} - Errors",
                        left=[func.metric_errors()],
                        width=6,
                        height=6
                    ),
                    cloudwatch.GraphWidget(
                        title=f"{func_name} - Throttles",
                        left=[func.metric_throttles()],
                        width=6,
                        height=6
                    )
                ]
            ])
        
        self.lambda_dashboard = cloudwatch.Dashboard(
            self, "LambdaDashboard",
            dashboard_name=f"HealthConnect-Lambda-{self.env_name}",
            widgets=lambda_widgets
        )
        
        # DynamoDB Dashboard
        dynamodb_widgets = []
        for table_name, table in self.dynamodb_tables.items():
            dynamodb_widgets.extend([
                [
                    cloudwatch.GraphWidget(
                        title=f"{table_name} - Read/Write Capacity",
                        left=[
                            table.metric_consumed_read_capacity_units(),
                            table.metric_consumed_write_capacity_units()
                        ],
                        width=12,
                        height=6
                    )
                ],
                [
                    cloudwatch.GraphWidget(
                        title=f"{table_name} - Throttles",
                        left=[
                            table.metric_throttled_requests_for_read(),
                            table.metric_throttled_requests_for_write()
                        ],
                        width=12,
                        height=6
                    )
                ]
            ])
        
        self.dynamodb_dashboard = cloudwatch.Dashboard(
            self, "DynamoDBDashboard",
            dashboard_name=f"HealthConnect-DynamoDB-{self.env_name}",
            widgets=dynamodb_widgets
        )
        
        # Emergency Response Dashboard
        self.emergency_dashboard = cloudwatch.Dashboard(
            self, "EmergencyDashboard",
            dashboard_name=f"HealthConnect-Emergency-{self.env_name}",
            widgets=[
                [
                    cloudwatch.SingleValueWidget(
                        title="Active Emergency Alerts",
                        metrics=[
                            cloudwatch.Metric(
                                namespace="HealthConnect/Emergency",
                                metric_name="ActiveAlerts",
                                statistic="Maximum"
                            )
                        ],
                        width=6,
                        height=6
                    ),
                    cloudwatch.SingleValueWidget(
                        title="Emergency Response Time (avg)",
                        metrics=[
                            cloudwatch.Metric(
                                namespace="HealthConnect/Emergency",
                                metric_name="ResponseTime",
                                statistic="Average"
                            )
                        ],
                        width=6,
                        height=6
                    )
                ],
                [
                    cloudwatch.GraphWidget(
                        title="Emergency Alerts by Urgency",
                        left=[
                            cloudwatch.Metric(
                                namespace="HealthConnect/Emergency",
                                metric_name="AlertsByUrgency",
                                dimensions_map={"UrgencyLevel": "CRITICAL"},
                                statistic="Sum"
                            ),
                            cloudwatch.Metric(
                                namespace="HealthConnect/Emergency",
                                metric_name="AlertsByUrgency",
                                dimensions_map={"UrgencyLevel": "HIGH"},
                                statistic="Sum"
                            ),
                            cloudwatch.Metric(
                                namespace="HealthConnect/Emergency",
                                metric_name="AlertsByUrgency",
                                dimensions_map={"UrgencyLevel": "MEDIUM"},
                                statistic="Sum"
                            )
                        ],
                        width=12,
                        height=6
                    )
                ]
            ]
        )
    
    def create_lambda_alarms(self):
        """Create CloudWatch alarms for Lambda functions"""
        
        for func_name, func in self.lambda_functions.items():
            # Error Rate Alarm
            error_alarm = cloudwatch.Alarm(
                self, f"{func_name}ErrorAlarm",
                alarm_name=f"HealthConnect-{func_name}-Errors-{self.env_name}",
                alarm_description=f"High error rate for {func_name} function",
                metric=func.metric_errors(period=Duration.minutes(5)),
                threshold=5,
                evaluation_periods=2,
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD
            )
            
            error_alarm.add_alarm_action(
                cw_actions.SnsAction(self.critical_alerts_topic)
            )
            
            # Duration Alarm
            duration_alarm = cloudwatch.Alarm(
                self, f"{func_name}DurationAlarm",
                alarm_name=f"HealthConnect-{func_name}-Duration-{self.env_name}",
                alarm_description=f"High duration for {func_name} function",
                metric=func.metric_duration(period=Duration.minutes(5)),
                threshold=30000,  # 30 seconds
                evaluation_periods=3,
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
            )
            
            duration_alarm.add_alarm_action(
                cw_actions.SnsAction(self.warning_alerts_topic)
            )
            
            # Throttle Alarm
            throttle_alarm = cloudwatch.Alarm(
                self, f"{func_name}ThrottleAlarm",
                alarm_name=f"HealthConnect-{func_name}-Throttles-{self.env_name}",
                alarm_description=f"Function throttling for {func_name}",
                metric=func.metric_throttles(period=Duration.minutes(5)),
                threshold=1,
                evaluation_periods=1,
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD
            )
            
            throttle_alarm.add_alarm_action(
                cw_actions.SnsAction(self.critical_alerts_topic)
            )
    
    def create_api_gateway_alarms(self):
        """Create CloudWatch alarms for API Gateway"""
        
        # 4XX Error Rate Alarm
        client_error_alarm = cloudwatch.Alarm(
            self, "APIGateway4XXAlarm",
            alarm_name=f"HealthConnect-API-4XX-{self.env_name}",
            alarm_description="High 4XX error rate in API Gateway",
            metric=cloudwatch.Metric(
                namespace="AWS/ApiGateway",
                metric_name="4XXError",
                dimensions_map={
                    "ApiName": self.api_gateway.rest_api_name
                },
                statistic="Sum",
                period=Duration.minutes(5)
            ),
            threshold=20,
            evaluation_periods=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
        )
        
        client_error_alarm.add_alarm_action(
            cw_actions.SnsAction(self.warning_alerts_topic)
        )
        
        # 5XX Error Rate Alarm
        server_error_alarm = cloudwatch.Alarm(
            self, "APIGateway5XXAlarm",
            alarm_name=f"HealthConnect-API-5XX-{self.env_name}",
            alarm_description="High 5XX error rate in API Gateway",
            metric=cloudwatch.Metric(
                namespace="AWS/ApiGateway",
                metric_name="5XXError",
                dimensions_map={
                    "ApiName": self.api_gateway.rest_api_name
                },
                statistic="Sum",
                period=Duration.minutes(5)
            ),
            threshold=5,
            evaluation_periods=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
        )
        
        server_error_alarm.add_alarm_action(
            cw_actions.SnsAction(self.critical_alerts_topic)
        )
        
        # Latency Alarm
        latency_alarm = cloudwatch.Alarm(
            self, "APIGatewayLatencyAlarm",
            alarm_name=f"HealthConnect-API-Latency-{self.env_name}",
            alarm_description="High latency in API Gateway",
            metric=cloudwatch.Metric(
                namespace="AWS/ApiGateway",
                metric_name="Latency",
                dimensions_map={
                    "ApiName": self.api_gateway.rest_api_name
                },
                statistic="Average",
                period=Duration.minutes(5)
            ),
            threshold=5000,  # 5 seconds
            evaluation_periods=3,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
        )
        
        latency_alarm.add_alarm_action(
            cw_actions.SnsAction(self.warning_alerts_topic)
        )
    
    def create_dynamodb_alarms(self):
        """Create CloudWatch alarms for DynamoDB tables"""
        
        for table_name, table in self.dynamodb_tables.items():
            # Throttle Alarm
            throttle_alarm = cloudwatch.Alarm(
                self, f"{table_name}ThrottleAlarm",
                alarm_name=f"HealthConnect-{table_name}-Throttles-{self.env_name}",
                alarm_description=f"DynamoDB throttling for {table_name} table",
                metric=cloudwatch.MathExpression(
                    expression="throttledReads + throttledWrites",
                    using_metrics={
                        "throttledReads": table.metric_throttled_requests_for_read(),
                        "throttledWrites": table.metric_throttled_requests_for_write()
                    },
                    period=Duration.minutes(5)
                ),
                threshold=1,
                evaluation_periods=1,
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD
            )
            
            throttle_alarm.add_alarm_action(
                cw_actions.SnsAction(self.critical_alerts_topic)
            )
            
            # High Consumed Capacity Alarm
            capacity_alarm = cloudwatch.Alarm(
                self, f"{table_name}CapacityAlarm",
                alarm_name=f"HealthConnect-{table_name}-HighCapacity-{self.env_name}",
                alarm_description=f"High consumed capacity for {table_name} table",
                metric=cloudwatch.MathExpression(
                    expression="readCapacity + writeCapacity",
                    using_metrics={
                        "readCapacity": table.metric_consumed_read_capacity_units(),
                        "writeCapacity": table.metric_consumed_write_capacity_units()
                    },
                    period=Duration.minutes(5)
                ),
                threshold=80,  # 80% of provisioned capacity
                evaluation_periods=3,
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
            )
            
            capacity_alarm.add_alarm_action(
                cw_actions.SnsAction(self.warning_alerts_topic)
            )
    
    def create_custom_metrics(self):
        """Create custom CloudWatch metrics for business logic"""
        
        # Create Lambda function for custom metrics
        custom_metrics_function = lambda_.Function(
            self, "CustomMetricsFunction",
            function_name=f"healthconnect-custom-metrics-{self.env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="index.handler",
            code=lambda_.Code.from_inline("""
import boto3
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger()
logger.setLevel(logging.INFO)

cloudwatch = boto3.client('cloudwatch')
dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    try:
        # Collect custom metrics
        metrics = []
        
        # Emergency alerts metrics
        emergency_table = dynamodb.Table(f"healthconnect-emergency-alerts-{event.get('env_name', 'dev')}")
        
        # Count active emergency alerts
        response = emergency_table.scan(
            FilterExpression='#status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':status': 'active'}
        )
        active_alerts = len(response.get('Items', []))
        
        metrics.append({
            'MetricName': 'ActiveAlerts',
            'Value': active_alerts,
            'Unit': 'Count',
            'Timestamp': datetime.now(timezone.utc)
        })
        
        # Count alerts by urgency level
        for urgency in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            response = emergency_table.scan(
                FilterExpression='urgency_level = :urgency',
                ExpressionAttributeValues={':urgency': urgency}
            )
            count = len(response.get('Items', []))
            
            metrics.append({
                'MetricName': 'AlertsByUrgency',
                'Dimensions': [{'Name': 'UrgencyLevel', 'Value': urgency}],
                'Value': count,
                'Unit': 'Count',
                'Timestamp': datetime.now(timezone.utc)
            })
        
        # Send metrics to CloudWatch
        cloudwatch.put_metric_data(
            Namespace='HealthConnect/Emergency',
            MetricData=metrics
        )
        
        logger.info(f"Published {len(metrics)} custom metrics")
        
        return {
            'statusCode': 200,
            'body': json.dumps({'metrics_published': len(metrics)})
        }
        
    except Exception as e:
        logger.error(f"Error publishing custom metrics: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
            """),
            timeout=Duration.minutes(5),
            environment={
                "env_name": self.env_name
            }
        )
        
        # Grant permissions to access DynamoDB and CloudWatch
        custom_metrics_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:Scan",
                    "dynamodb:Query"
                ],
                resources=[
                    table.table_arn for table in self.dynamodb_tables.values()
                ]
            )
        )
        
        custom_metrics_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "cloudwatch:PutMetricData"
                ],
                resources=["*"]
            )
        )
        
        # Schedule the function to run every 5 minutes
        custom_metrics_rule = events.Rule(
            self, "CustomMetricsSchedule",
            rule_name=f"healthconnect-custom-metrics-{self.env_name}",
            description="Schedule for custom metrics collection",
            schedule=events.Schedule.rate(Duration.minutes(5))
        )
        
        custom_metrics_rule.add_target(
            targets.LambdaFunction(
                custom_metrics_function,
                event=events.RuleTargetInput.from_object({
                    "env_name": self.env_name
                })
            )
        )
    
    def create_log_insights_queries(self):
        """Create CloudWatch Log Insights queries for troubleshooting"""
        
        # Create log group for storing saved queries
        log_insights_queries = [
            {
                "name": "Lambda Errors",
                "query": """
                    fields @timestamp, @message
                    | filter @message like /ERROR/
                    | sort @timestamp desc
                    | limit 100
                """
            },
            {
                "name": "API Gateway 5XX Errors",
                "query": """
                    fields @timestamp, @message, @requestId
                    | filter @message like /5\d{2}/
                    | sort @timestamp desc
                    | limit 50
                """
            },
            {
                "name": "Emergency Alert Processing",
                "query": """
                    fields @timestamp, @message
                    | filter @message like /emergency/ or @message like /CRITICAL/
                    | sort @timestamp desc
                    | limit 100
                """
            },
            {
                "name": "Health Analysis Performance",
                "query": """
                    fields @timestamp, @duration, @billedDuration, @message
                    | filter @type = "REPORT"
                    | stats avg(@duration), max(@duration), min(@duration) by bin(5m)
                """
            },
            {
                "name": "DynamoDB Throttling",
                "query": """
                    fields @timestamp, @message
                    | filter @message like /throttl/
                    | sort @timestamp desc
                    | limit 50
                """
            }
        ]
        
        # Note: Log Insights queries would typically be saved manually
        # or through CLI/SDK as CDK doesn't have native support yet
        
        # Create outputs for the queries
        for i, query in enumerate(log_insights_queries):
            CfnOutput(
                self, f"LogInsightsQuery{i}",
                value=query["query"],
                description=f"Log Insights Query: {query['name']}",
                export_name=f"HealthConnect-LogInsights-{query['name'].replace(' ', '')}-{self.env_name}"
            )
