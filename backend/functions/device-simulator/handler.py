import json
import logging
import os
import random
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import boto3
from botocore.exceptions import ClientError
from device_types import DeviceTypeManager
from health_data_generator import HealthDataGenerator
import uuid

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
iot_data = boto3.client('iot-data')
dynamodb = boto3.resource('dynamodb')
eventbridge = boto3.client('events')

# Environment variables
DEVICE_REGISTRY_TABLE = os.environ['DEVICE_REGISTRY_TABLE']
DEVICE_DATA_TABLE = os.environ['DEVICE_DATA_TABLE']
IOT_ENDPOINT = os.environ['IOT_ENDPOINT']
EVENT_BUS_NAME = os.environ['EVENT_BUS_NAME']

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Main Lambda handler for IoT device simulation
    
    Args:
        event: Contains simulation parameters or scheduled event
        context: Lambda context object
        
    Returns:
        Dict containing simulation results
    """
    try:
        # Determine if this is a scheduled run or API call
        if 'source' in event and event['source'] == 'aws.events':
            # Scheduled simulation run
            return handle_scheduled_simulation(event, context)
        else:
            # API-triggered simulation
            return handle_api_simulation(event, context)
            
    except Exception as e:
        logger.error(f"Error in device simulation: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Device simulation failed',
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }

def handle_api_simulation(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle API-triggered device simulation"""
    try:
        # Parse request body
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
        
        # Extract simulation parameters
        device_count = body.get('device_count', 10)
        duration_minutes = body.get('duration_minutes', 60)
        device_types = body.get('device_types', ['heart_rate_monitor', 'blood_pressure_cuff'])
        patient_profiles = body.get('patient_profiles', ['normal', 'hypertensive', 'diabetic'])
        simulation_scenario = body.get('scenario', 'normal_monitoring')
        
        # Validate parameters
        if device_count > 100:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Device count cannot exceed 100',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
            }
        
        # Initialize device and data managers
        device_manager = DeviceTypeManager()
        data_generator = HealthDataGenerator()
        
        # Create virtual devices
        devices = create_virtual_devices(
            device_count, 
            device_types, 
            patient_profiles,
            device_manager
        )
        
        # Start simulation
        simulation_id = str(uuid.uuid4())
        simulation_results = run_device_simulation(
            simulation_id,
            devices,
            duration_minutes,
            simulation_scenario,
            data_generator
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'simulation_id': simulation_id,
                'devices_created': len(devices),
                'simulation_results': simulation_results,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error in API simulation: {str(e)}")
        raise

def handle_scheduled_simulation(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle scheduled device simulation for continuous monitoring"""
    try:
        # Get active devices from registry
        active_devices = get_active_devices()
        
        if not active_devices:
            logger.info("No active devices found for scheduled simulation")
            return {'statusCode': 200, 'message': 'No active devices'}
        
        # Initialize data generator
        data_generator = HealthDataGenerator()
        
        # Generate and publish data for each active device
        published_count = 0
        for device in active_devices:
            try:
                # Generate health data based on device type and patient profile
                health_data = data_generator.generate_realistic_data(
                    device['device_type'],
                    device.get('patient_profile', 'normal'),
                    device.get('current_state', {})
                )
                
                # Publish to IoT Core
                publish_device_data(device['device_id'], health_data)
                
                # Update device state
                update_device_state(device['device_id'], health_data)
                
                published_count += 1
                
            except Exception as e:
                logger.error(f"Error processing device {device['device_id']}: {str(e)}")
                continue
        
        logger.info(f"Published data for {published_count} devices")
        
        return {
            'statusCode': 200,
            'devices_processed': published_count,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in scheduled simulation: {str(e)}")
        raise

def create_virtual_devices(
    count: int, 
    device_types: List[str], 
    patient_profiles: List[str],
    device_manager: DeviceTypeManager
) -> List[Dict[str, Any]]:
    """Create virtual IoT devices with realistic configurations"""
    
    devices = []
    table = dynamodb.Table(DEVICE_REGISTRY_TABLE)
    
    for i in range(count):
        device_type = random.choice(device_types)
        patient_profile = random.choice(patient_profiles)
        
        # Get device specifications
        device_spec = device_manager.get_device_specification(device_type)
        
        device = {
            'device_id': f"sim_{device_type}_{uuid.uuid4().hex[:8]}",
            'device_type': device_type,
            'patient_id': f"patient_{uuid.uuid4().hex[:8]}",
            'patient_profile': patient_profile,
            'device_spec': device_spec,
            'status': 'active',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'last_data_time': None,
            'current_state': device_manager.get_initial_state(device_type, patient_profile),
            'simulation_parameters': {
                'data_frequency': device_spec.get('data_frequency', 30),
                'noise_level': random.uniform(0.05, 0.15),
                'drift_rate': random.uniform(0.001, 0.01)
            }
        }
        
        # Store device in registry
        try:
            table.put_item(Item=device)
            devices.append(device)
            logger.info(f"Created virtual device: {device['device_id']}")
        except ClientError as e:
            logger.error(f"Failed to register device: {str(e)}")
            continue
    
    return devices

def run_device_simulation(
    simulation_id: str,
    devices: List[Dict[str, Any]],
    duration_minutes: int,
    scenario: str,
    data_generator: HealthDataGenerator
) -> Dict[str, Any]:
    """Run device simulation for specified duration"""
    
    start_time = datetime.now(timezone.utc)
    end_time = start_time + timedelta(minutes=duration_minutes)
    
    simulation_results = {
        'simulation_id': simulation_id,
        'start_time': start_time.isoformat(),
        'duration_minutes': duration_minutes,
        'scenario': scenario,
        'devices': len(devices),
        'data_points_generated': 0,
        'alerts_triggered': 0,
        'errors': 0
    }
    
    # For hackathon demo, we'll simulate the full duration in a compressed timeframe
    # In production, this would run over the actual duration
    simulation_steps = min(duration_minutes, 10)  # Limit for Lambda timeout
    
    for step in range(simulation_steps):
        current_time = start_time + timedelta(minutes=step)
        
        for device in devices:
            try:
                # Apply scenario-specific modifications
                scenario_params = get_scenario_parameters(scenario, step, simulation_steps)
                
                # Generate health data
                health_data = data_generator.generate_realistic_data(
                    device['device_type'],
                    device['patient_profile'],
                    device['current_state'],
                    scenario_params
                )
                
                # Add timestamp and device metadata
                health_data['timestamp'] = current_time.isoformat()
                health_data['device_id'] = device['device_id']
                health_data['patient_id'] = device['patient_id']
                
                # Publish to IoT Core
                publish_device_data(device['device_id'], health_data)
                
                # Update device state
                device['current_state'] = data_generator.update_device_state(
                    device['current_state'], 
                    health_data
                )
                
                simulation_results['data_points_generated'] += 1
                
                # Check for alert conditions
                if check_alert_conditions(health_data):
                    trigger_device_alert(device['device_id'], health_data)
                    simulation_results['alerts_triggered'] += 1
                
            except Exception as e:
                logger.error(f"Error in simulation step for device {device['device_id']}: {str(e)}")
                simulation_results['errors'] += 1
                continue
        
        # Small delay between steps to avoid overwhelming downstream systems
        if step < simulation_steps - 1:
            time.sleep(0.1)
    
    simulation_results['end_time'] = datetime.now(timezone.utc).isoformat()
    
    # Store simulation summary
    store_simulation_results(simulation_results)
    
    return simulation_results

def get_scenario_parameters(scenario: str, step: int, total_steps: int) -> Dict[str, Any]:
    """Get scenario-specific parameters for data generation"""
    
    scenarios = {
        'normal_monitoring': {
            'stress_factor': 1.0,
            'anomaly_probability': 0.05
        },
        'emergency_scenario': {
            'stress_factor': 2.0 + (step / total_steps),
            'anomaly_probability': 0.3,
            'emergency_trigger': step > total_steps * 0.7
        },
        'chronic_condition': {
            'stress_factor': 1.2,
            'anomaly_probability': 0.15,
            'condition_progression': step / total_steps
        },
        'post_surgery': {
            'stress_factor': 1.5 - (step / total_steps * 0.5),
            'anomaly_probability': 0.2 - (step / total_steps * 0.15),
            'recovery_factor': step / total_steps
        }
    }
    
    return scenarios.get(scenario, scenarios['normal_monitoring'])

def publish_device_data(device_id: str, health_data: Dict[str, Any]) -> None:
    """Publish device data to AWS IoT Core"""
    try:
        topic = f"healthconnect/devices/{device_id}/data"
        
        # Prepare IoT message
        message = {
            'device_id': device_id,
            'timestamp': health_data['timestamp'],
            'data': health_data,
            'message_id': str(uuid.uuid4())
        }
        
        # Publish to IoT Core
        iot_data.publish(
            topic=topic,
            qos=1,
            payload=json.dumps(message)
        )
        
        # Store in DynamoDB for historical data
        store_device_data(device_id, health_data)
        
        logger.debug(f"Published data for device {device_id} to topic {topic}")
        
    except ClientError as e:
        logger.error(f"Failed to publish device data: {str(e)}")
        raise

def store_device_data(device_id: str, health_data: Dict[str, Any]) -> None:
    """Store device data in DynamoDB"""
    try:
        table = dynamodb.Table(DEVICE_DATA_TABLE)
        
        item = {
            'device_id': device_id,
            'timestamp': health_data['timestamp'],
            'data': health_data,
            'ttl': int(datetime.now().timestamp()) + 2592000  # 30 days TTL
        }
        
        table.put_item(Item=item)
        
    except ClientError as e:
        logger.error(f"Failed to store device data: {str(e)}")

def get_active_devices() -> List[Dict[str, Any]]:
    """Get list of active devices from registry"""
    try:
        table = dynamodb.Table(DEVICE_REGISTRY_TABLE)
        
        response = table.scan(
            FilterExpression='#status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':status': 'active'}
        )
        
        return response.get('Items', [])
        
    except ClientError as e:
        logger.error(f"Failed to get active devices: {str(e)}")
        return []

def update_device_state(device_id: str, health_data: Dict[str, Any]) -> None:
    """Update device state in registry"""
    try:
        table = dynamodb.Table(DEVICE_REGISTRY_TABLE)
        
        table.update_item(
            Key={'device_id': device_id},
            UpdateExpression='SET last_data_time = :timestamp, current_state = :state',
            ExpressionAttributeValues={
                ':timestamp': health_data['timestamp'],
                ':state': health_data
            }
        )
        
    except ClientError as e:
        logger.error(f"Failed to update device state: {str(e)}")

def check_alert_conditions(health_data: Dict[str, Any]) -> bool:
    """Check if health data triggers any alert conditions"""
    
    # Heart rate alerts
    if 'heart_rate' in health_data:
        hr = health_data['heart_rate']
        if hr < 50 or hr > 120:
            return True
    
    # Blood pressure alerts
    if 'blood_pressure' in health_data:
        bp = health_data['blood_pressure']
        systolic = bp.get('systolic', 120)
        diastolic = bp.get('diastolic', 80)
        if systolic > 180 or diastolic > 110 or systolic < 90:
            return True
    
    # Temperature alerts
    if 'temperature' in health_data:
        temp = health_data['temperature']
        if temp > 39.0 or temp < 35.0:
            return True
    
    # Oxygen saturation alerts
    if 'oxygen_saturation' in health_data:
        spo2 = health_data['oxygen_saturation']
        if spo2 < 90:
            return True
    
    return False

def trigger_device_alert(device_id: str, health_data: Dict[str, Any]) -> None:
    """Trigger alert for abnormal device readings"""
    try:
        # Send event to EventBridge
        event_detail = {
            'device_id': device_id,
            'patient_id': health_data.get('patient_id'),
            'alert_type': 'abnormal_reading',
            'health_data': health_data,
            'timestamp': health_data['timestamp']
        }
        
        eventbridge.put_events(
            Entries=[
                {
                    'Source': 'healthconnect.devices',
                    'DetailType': 'Device Alert',
                    'Detail': json.dumps(event_detail),
                    'EventBusName': EVENT_BUS_NAME
                }
            ]
        )
        
        logger.info(f"Alert triggered for device {device_id}")
        
    except Exception as e:
        logger.error(f"Failed to trigger device alert: {str(e)}")

def store_simulation_results(results: Dict[str, Any]) -> None:
    """Store simulation results for analysis"""
    try:
        table = dynamodb.Table(DEVICE_REGISTRY_TABLE)
        
        item = {
            'device_id': f"simulation_{results['simulation_id']}",
            'device_type': 'simulation_summary',
            'simulation_results': results,
            'timestamp': results['start_time'],
            'ttl': int(datetime.now().timestamp()) + 604800  # 7 days TTL
        }
        
        table.put_item(Item=item)
        
    except Exception as e:
        logger.error(f"Failed to store simulation results: {str(e)}")

def cleanup_simulation_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Clean up simulation devices and data"""
    try:
        simulation_id = event.get('simulation_id')
        if not simulation_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'simulation_id required'})
            }
        
        # Get devices for this simulation
        table = dynamodb.Table(DEVICE_REGISTRY_TABLE)
        response = table.scan(
            FilterExpression='contains(device_id, :sim_id)',
            ExpressionAttributeValues={':sim_id': f'sim_'}
        )
        
        devices_cleaned = 0
        for device in response.get('Items', []):
            try:
                # Delete device from registry
                table.delete_item(Key={'device_id': device['device_id']})
                devices_cleaned += 1
            except Exception as e:
                logger.error(f"Failed to delete device {device['device_id']}: {str(e)}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'devices_cleaned': devices_cleaned,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error in cleanup: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Cleanup failed'})
        }
