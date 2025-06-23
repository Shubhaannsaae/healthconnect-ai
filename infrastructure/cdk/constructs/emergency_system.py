"""
Emergency System Construct for HealthConnect AI
Reusable construct for emergency response capabilities
"""

from aws_cdk import (
    aws_lambda as lambda_,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subs,
    aws_dynamodb as dynamodb,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    Duration
)
from constructs import Construct
from typing import Dict, Any, List

class EmergencySystemConstruct(Construct):
    """Reusable construct for emergency response system"""
    
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        emergency_contacts: List[str],
        escalation_levels: int = 3,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.emergency_contacts = emergency_contacts
        self.escalation_levels = escalation_levels
        
        # Create emergency response components
        self.create_emergency_topics()
        self.create_emergency_function()
        self.create_escalation_rules()
    
    def create_emergency_topics(self):
        """Create SNS topics for emergency notifications"""
        
        # Critical emergency topic
        self.critical_topic = sns.Topic(
            self, "CriticalEmergencyTopic",
            display_name="Critical Emergency Alerts"
        )
        
        # High priority emergency topic
        self.high_priority_topic = sns.Topic(
            self, "HighPriorityEmergencyTopic",
            display_name="High Priority Emergency Alerts"
        )
        
        # Add subscriptions for emergency contacts
        for contact in self.emergency_contacts:
            if "@" in contact:
                # Email subscription
                self.critical_topic.add_subscription(
                    sns_subs.EmailSubscription(contact)
                )
                self.high_priority_topic.add_subscription(
                    sns_subs.EmailSubscription(contact)
                )
            elif contact.startswith("+"):
                # SMS subscription
                self.critical_topic.add_subscription(
                    sns_subs.SmsSubscription(contact)
                )
    
    def create_emergency_function(self):
        """Create Lambda function for emergency processing"""
        
        self.emergency_function = lambda_.Function(
            self, "EmergencyFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="emergency.handler",
            code=lambda_.Code.from_asset("../backend/functions/emergency-response"),
            timeout=Duration.minutes(5),
            memory_size=1024,
            environment={
                "CRITICAL_TOPIC_ARN": self.critical_topic.topic_arn,
                "HIGH_PRIORITY_TOPIC_ARN": self.high_priority_topic.topic_arn,
                "ESCALATION_LEVELS": str(self.escalation_levels)
            }
        )
        
        # Grant SNS publish permissions
        self.critical_topic.grant_publish(self.emergency_function)
        self.high_priority_topic.grant_publish(self.emergency_function)
        
        # Grant additional permissions for emergency response
        self.emergency_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ses:SendEmail",
                    "ses:SendRawEmail",
                    "mobiletargeting:SendMessages"
                ],
                resources=["*"]
            )
        )
    
    def create_escalation_rules(self):
        """Create escalation rules for emergency alerts"""
        
        # Create escalation rule for unresolved emergencies
        escalation_rule = events.Rule(
            self, "EmergencyEscalationRule",
            description="Escalate unresolved emergency alerts",
            schedule=events.Schedule.rate(Duration.minutes(15))
        )
        
        # Add Lambda target for escalation processing
        escalation_rule.add_target(
            targets.LambdaFunction(
                self.emergency_function,
                event=events.RuleTargetInput.from_object({
                    "action": "check_escalations",
                    "escalation_levels": self.escalation_levels
                })
            )
        )
    
    def add_emergency_trigger(self, source_function: lambda_.Function):
        """Add emergency trigger from another Lambda function"""
        
        # Create event rule for emergency triggers
        emergency_trigger_rule = events.Rule(
            self, f"EmergencyTriggerFrom{source_function.function_name}",
            description=f"Emergency trigger from {source_function.function_name}",
            event_pattern=events.EventPattern(
                source=["healthconnect.analysis"],
                detail_type=["Health Analysis Complete"],
                detail={
                    "urgency_level": ["CRITICAL", "HIGH"]
                }
            )
        )
        
        # Add target to emergency function
        emergency_trigger_rule.add_target(
            targets.LambdaFunction(self.emergency_function)
        )
        
        return emergency_trigger_rule
