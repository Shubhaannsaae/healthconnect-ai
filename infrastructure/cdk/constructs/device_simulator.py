"""
Device Simulator Construct for HealthConnect AI
Reusable construct for IoT device simulation
"""

from aws_cdk import (
    aws_lambda as lambda_,
    aws_iot as iot,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    Duration
)
from constructs import Construct
from typing import Dict, Any, List

class DeviceSimulatorConstruct(Construct):
    """Reusable construct for IoT device simulation"""
    
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        device_types: List[str],
        simulation_interval: Duration = Duration.minutes(5),
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.device_types = device_types
        self.simulation_interval = simulation_interval
        
        # Create device simulator Lambda function
        self.simulator_function = lambda_.Function(
            self, "SimulatorFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="simulator.handler",
            code=lambda_.Code.from_asset("../backend/functions/device-simulator"),
            timeout=Duration.minutes(5),
            memory_size=1024,
            environment={
                "DEVICE_TYPES": ",".join(self.device_types),
                "IOT_ENDPOINT": self.get_iot_endpoint()
            }
        )
        
        # Grant IoT permissions
        self.simulator_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "iot:Publish",
                    "iot:Connect"
                ],
                resources=[
                    f"arn:aws:iot:*:*:topic/healthconnect/devices/*/data",
                    f"arn:aws:iot:*:*:client/*"
                ]
            )
        )
        
        # Create scheduled event rule
        self.simulation_rule = events.Rule(
            self, "SimulationSchedule",
            description="Scheduled device simulation",
            schedule=events.Schedule.rate(self.simulation_interval)
        )
        
        # Add Lambda target to the rule
        self.simulation_rule.add_target(
            targets.LambdaFunction(
                self.simulator_function,
                event=events.RuleTargetInput.from_object({
                    "action": "simulate_devices",
                    "device_types": self.device_types
                })
            )
        )
        
        # Create IoT things for each device type
        self.create_iot_things()
    
    def create_iot_things(self):
        """Create IoT things for device simulation"""
        
        self.iot_things = {}
        
        for device_type in self.device_types:
            # Create IoT thing
            thing = iot.CfnThing(
                self, f"{device_type}Thing",
                thing_name=f"healthconnect-{device_type}-simulator",
                thing_type_name=f"HealthConnect-{device_type.title()}",
                attribute_payload=iot.CfnThing.AttributePayloadProperty(
                    attributes={
                        "deviceType": device_type,
                        "purpose": "simulation",
                        "environment": "testing"
                    }
                )
            )
            
            self.iot_things[device_type] = thing
    
    def get_iot_endpoint(self) -> str:
        """Get IoT Core endpoint"""
        # This would typically be retrieved from IoT Core
        # For CDK, we construct it based on the standard format
        from aws_cdk import Stack
        stack = Stack.of(self)
        return f"https://a{stack.account}-ats.iot.{stack.region}.amazonaws.com"
