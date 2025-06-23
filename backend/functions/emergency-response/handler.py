import json
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
import boto3
from botocore.exceptions import ClientError
from alert_system import EmergencyAlertSystem
from notification_service import NotificationService
import uuid
import traceback

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
eventbridge = boto3.client('events')
lambda_client = boto3.client('lambda')
ses = boto3.client('ses')

# Environment variables
EMERGENCY_ALERTS_TABLE = os.environ['EMERGENCY_ALERTS_TABLE']
EMERGENCY_CONTACTS_TABLE = os.environ['EMERGENCY_CONTACTS_TABLE']
EMERGENCY_TOPIC_ARN = os.environ['EMERGENCY_TOPIC_ARN']
EVENT_BUS_NAME = os.environ['EVENT_BUS_NAME']
CONSULTATION_FUNCTION_ARN = os.environ['CONSULTATION_FUNCTION_ARN']
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Main Lambda handler for emergency response system
    
    Args:
        event: Emergency event data or API Gateway event
        context: Lambda context object
        
    Returns:
        Dict containing response status and emergency response details
    """
    try:
        # Determine event source
        if 'Records' in event:
            # SNS trigger
            return handle_sns_emergency_alert(event, context)
        elif 'source' in event and event['source'] == 'healthconnect.analysis':
            # EventBridge trigger from health analysis
            return handle_health_analysis_alert(event, context)
        elif 'source' in event and event['source'] == 'healthconnect.devices':
            # EventBridge trigger from device alerts
            return handle_device_alert(event, context)
        elif 'httpMethod' in event:
            # API Gateway trigger
            return handle_api_request(event, context)
        else:
            # Direct invocation
            return handle_direct_emergency(event, context)
            
    except Exception as e:
        logger.error(f"Error in emergency response handler: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Emergency response system error',
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }

def handle_sns_emergency_alert(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle emergency alerts from SNS"""
    try:
        processed_alerts = 0
        
        for record in event['Records']:
            if record['EventSource'] == 'aws:sns':
                message = json.loads(record['Sns']['Message'])
                
                # Process emergency alert
                alert_response = process_emergency_alert(message)
                
                if alert_response['success']:
                    processed_alerts += 1
                    logger.info(f"Processed emergency alert: {alert_response['alert_id']}")
                else:
                    logger.error(f"Failed to process emergency alert: {alert_response.get('error')}")
        
        return {
            'statusCode': 200,
            'processed_alerts': processed_alerts,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error handling SNS emergency alert: {str(e)}")
        raise

def handle_health_analysis_alert(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle emergency alerts from health analysis"""
    try:
        detail = event['detail']
        patient_id = detail['patient_id']
        analysis_id = detail['analysis_id']
        urgency_level = detail['urgency_level']
        
        if urgency_level in ['CRITICAL', 'HIGH']:
            # Create emergency alert
            emergency_data = {
                'patient_id': patient_id,
                'analysis_id': analysis_id,
                'urgency_level': urgency_level,
                'alert_type': 'health_analysis',
                'source': 'ai_analysis',
                'timestamp': detail['timestamp']
            }
            
            alert_response = process_emergency_alert(emergency_data)
            
            return {
                'statusCode': 200,
                'alert_processed': alert_response['success'],
                'alert_id': alert_response.get('alert_id'),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        else:
            logger.info(f"Non-emergency health analysis for patient {patient_id}")
            return {
                'statusCode': 200,
                'message': 'Non-emergency alert - no action taken'
            }
            
    except Exception as e:
        logger.error(f"Error handling health analysis alert: {str(e)}")
        raise

def handle_device_alert(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle emergency alerts from IoT devices"""
    try:
        detail = event['detail']
        device_id = detail['device_id']
        patient_id = detail.get('patient_id')
        health_data = detail['health_data']
        
        # Assess emergency severity based on device readings
        severity_assessment = assess_device_emergency_severity(health_data)
        
        if severity_assessment['is_emergency']:
            emergency_data = {
                'patient_id': patient_id,
                'device_id': device_id,
                'urgency_level': severity_assessment['urgency_level'],
                'alert_type': 'device_reading',
                'source': 'iot_device',
                'health_data': health_data,
                'severity_score': severity_assessment['severity_score'],
                'timestamp': detail['timestamp']
            }
            
            alert_response = process_emergency_alert(emergency_data)
            
            return {
                'statusCode': 200,
                'alert_processed': alert_response['success'],
                'alert_id': alert_response.get('alert_id'),
                'severity_score': severity_assessment['severity_score'],
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        else:
            logger.info(f"Non-emergency device reading from {device_id}")
            return {
                'statusCode': 200,
                'message': 'Non-emergency device alert - monitoring continues'
            }
            
    except Exception as e:
        logger.error(f"Error handling device alert: {str(e)}")
        raise

def handle_api_request(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle API Gateway requests"""
    try:
        http_method = event['httpMethod']
        path = event['path']
        
        if http_method == 'POST' and '/emergency' in path:
            # Manual emergency trigger
            body = json.loads(event['body']) if event.get('body') else {}
            return handle_manual_emergency(body)
            
        elif http_method == 'GET' and '/alerts' in path:
            # Get emergency alerts
            query_params = event.get('queryStringParameters', {}) or {}
            return get_emergency_alerts(query_params)
            
        elif http_method == 'PUT' and '/alerts' in path:
            # Update alert status
            body = json.loads(event['body']) if event.get('body') else {}
            return update_alert_status(body)
            
        elif http_method == 'POST' and '/test' in path:
            # Test emergency system
            return test_emergency_system()
            
        else:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Endpoint not found'})
            }
            
    except Exception as e:
        logger.error(f"Error handling API request: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Internal server error'})
        }

def handle_direct_emergency(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle direct emergency invocation"""
    try:
        alert_response = process_emergency_alert(event)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'alert_processed': alert_response['success'],
                'alert_id': alert_response.get('alert_id'),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error handling direct emergency: {str(e)}")
        raise

def process_emergency_alert(emergency_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process emergency alert and coordinate response"""
    try:
        # Generate unique alert ID
        alert_id = str(uuid.uuid4())
        
        # Initialize emergency systems
        alert_system = EmergencyAlertSystem()
        notification_service = NotificationService()
        
        # Create emergency alert record
        alert_record = {
            'alert_id': alert_id,
            'patient_id': emergency_data.get('patient_id'),
            'device_id': emergency_data.get('device_id'),
            'analysis_id': emergency_data.get('analysis_id'),
            'alert_type': emergency_data.get('alert_type', 'unknown'),
            'urgency_level': emergency_data.get('urgency_level', 'HIGH'),
            'source': emergency_data.get('source', 'system'),
            'health_data': emergency_data.get('health_data', {}),
            'severity_score': emergency_data.get('severity_score', 0.8),
            'status': 'ACTIVE',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'response_actions': [],
            'notifications_sent': [],
            'escalation_level': 1,
            'ttl': int(datetime.now().timestamp()) + 2592000  # 30 days TTL
        }
        
        # Store alert in DynamoDB
        table = dynamodb.Table(EMERGENCY_ALERTS_TABLE)
        table.put_item(Item=alert_record)
        
        # Determine response protocol based on urgency
        response_protocol = alert_system.determine_response_protocol(
            alert_record['urgency_level'],
            alert_record['alert_type'],
            alert_record.get('health_data', {})
        )
        
        # Execute immediate response actions
        immediate_actions = execute_immediate_response(alert_record, response_protocol)
        
        # Send notifications
        notification_results = send_emergency_notifications(alert_record, response_protocol)
        
        # Trigger emergency consultation if needed
        consultation_result = None
        if response_protocol.get('require_immediate_consultation', False):
            consultation_result = trigger_emergency_consultation(alert_record)
        
        # Update alert record with response actions
        alert_record['response_actions'] = immediate_actions
        alert_record['notifications_sent'] = notification_results
        alert_record['consultation_triggered'] = consultation_result is not None
        alert_record['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        # Update record in DynamoDB
        table.put_item(Item=alert_record)
        
        # Send completion event
        send_emergency_response_event(alert_record)
        
        # Schedule follow-up actions
        schedule_follow_up_actions(alert_record, response_protocol)
        
        logger.info(f"Emergency alert processed successfully: {alert_id}")
        
        return {
            'success': True,
            'alert_id': alert_id,
            'response_protocol': response_protocol,
            'immediate_actions': immediate_actions,
            'notifications_sent': len(notification_results),
            'consultation_triggered': consultation_result is not None
        }
        
    except Exception as e:
        logger.error(f"Error processing emergency alert: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

def assess_device_emergency_severity(health_data: Dict[str, Any]) -> Dict[str, Any]:
    """Assess emergency severity from device readings"""
    
    severity_score = 0.0
    critical_indicators = []
    
    # Heart rate assessment
    if 'heart_rate' in health_data:
        hr = health_data['heart_rate']
        if hr < 40 or hr > 150:
            severity_score += 0.4
            critical_indicators.append(f"Critical heart rate: {hr} bpm")
        elif hr < 50 or hr > 120:
            severity_score += 0.2
            critical_indicators.append(f"Abnormal heart rate: {hr} bpm")
    
    # Blood pressure assessment
    if 'blood_pressure' in health_data:
        bp = health_data['blood_pressure']
        systolic = bp.get('systolic', 120)
        diastolic = bp.get('diastolic', 80)
        
        if systolic > 200 or diastolic > 120:
            severity_score += 0.5
            critical_indicators.append(f"Hypertensive crisis: {systolic}/{diastolic} mmHg")
        elif systolic < 80 or diastolic < 50:
            severity_score += 0.4
            critical_indicators.append(f"Hypotensive crisis: {systolic}/{diastolic} mmHg")
        elif systolic > 180 or diastolic > 110:
            severity_score += 0.3
            critical_indicators.append(f"Severe hypertension: {systolic}/{diastolic} mmHg")
    
    # Temperature assessment
    if 'core_temperature' in health_data:
        temp = health_data['core_temperature']
        if temp > 40.0 or temp < 34.0:
            severity_score += 0.4
            critical_indicators.append(f"Critical temperature: {temp}°C")
        elif temp > 39.0 or temp < 35.0:
            severity_score += 0.2
            critical_indicators.append(f"Abnormal temperature: {temp}°C")
    
    # Oxygen saturation assessment
    if 'oxygen_saturation' in health_data:
        spo2 = health_data['oxygen_saturation']
        if spo2 < 85:
            severity_score += 0.5
            critical_indicators.append(f"Critical hypoxemia: {spo2}%")
        elif spo2 < 90:
            severity_score += 0.3
            critical_indicators.append(f"Severe hypoxemia: {spo2}%")
        elif spo2 < 95:
            severity_score += 0.1
            critical_indicators.append(f"Mild hypoxemia: {spo2}%")
    
    # Glucose assessment
    if 'glucose_level' in health_data:
        glucose = health_data['glucose_level']
        if glucose > 400 or glucose < 50:
            severity_score += 0.4
            critical_indicators.append(f"Critical glucose: {glucose} mg/dL")
        elif glucose > 300 or glucose < 70:
            severity_score += 0.2
            critical_indicators.append(f"Abnormal glucose: {glucose} mg/dL")
    
    # Respiratory rate assessment
    if 'respiratory_rate' in health_data:
        rr = health_data['respiratory_rate']
        if rr > 30 or rr < 8:
            severity_score += 0.3
            critical_indicators.append(f"Critical respiratory rate: {rr} breaths/min")
        elif rr > 25 or rr < 10:
            severity_score += 0.1
            critical_indicators.append(f"Abnormal respiratory rate: {rr} breaths/min")
    
    # Determine urgency level
    if severity_score >= 0.8:
        urgency_level = 'CRITICAL'
    elif severity_score >= 0.5:
        urgency_level = 'HIGH'
    elif severity_score >= 0.3:
        urgency_level = 'MEDIUM'
    else:
        urgency_level = 'LOW'
    
    is_emergency = severity_score >= 0.5
    
    return {
        'is_emergency': is_emergency,
        'severity_score': round(severity_score, 2),
        'urgency_level': urgency_level,
        'critical_indicators': critical_indicators,
        'assessment_timestamp': datetime.now(timezone.utc).isoformat()
    }

def execute_immediate_response(alert_record: Dict[str, Any], response_protocol: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Execute immediate response actions"""
    
    actions_taken = []
    
    try:
        # Auto-escalate to emergency services if critical
        if alert_record['urgency_level'] == 'CRITICAL':
            if response_protocol.get('auto_call_ems', False):
                ems_result = initiate_ems_call(alert_record)
                actions_taken.append({
                    'action': 'ems_call_initiated',
                    'result': ems_result,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
        
        # Notify emergency contacts
        if response_protocol.get('notify_emergency_contacts', True):
            contact_results = notify_emergency_contacts(alert_record)
            actions_taken.append({
                'action': 'emergency_contacts_notified',
                'contacts_reached': len(contact_results),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        
        # Alert healthcare providers
        if response_protocol.get('alert_healthcare_providers', True):
            provider_results = alert_healthcare_providers(alert_record)
            actions_taken.append({
                'action': 'healthcare_providers_alerted',
                'providers_notified': len(provider_results),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        
        # Trigger device data collection
        if response_protocol.get('increase_monitoring', True):
            monitoring_result = increase_device_monitoring(alert_record)
            actions_taken.append({
                'action': 'monitoring_increased',
                'result': monitoring_result,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        
        logger.info(f"Executed {len(actions_taken)} immediate response actions")
        
    except Exception as e:
        logger.error(f"Error executing immediate response: {str(e)}")
        actions_taken.append({
            'action': 'error_in_immediate_response',
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    
    return actions_taken

def send_emergency_notifications(alert_record: Dict[str, Any], response_protocol: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Send emergency notifications through multiple channels"""
    
    notification_service = NotificationService()
    notifications_sent = []
    
    try:
        patient_id = alert_record['patient_id']
        
        # Get emergency contacts
        emergency_contacts = get_emergency_contacts(patient_id)
        
        # Prepare notification content
        notification_content = prepare_notification_content(alert_record)
        
        # Send SMS notifications
        if response_protocol.get('send_sms', True):
            for contact in emergency_contacts:
                if contact.get('phone_number'):
                    sms_result = notification_service.send_sms(
                        contact['phone_number'],
                        notification_content['sms_message']
                    )
                    notifications_sent.append({
                        'type': 'sms',
                        'recipient': contact['name'],
                        'phone': contact['phone_number'],
                        'success': sms_result['success'],
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    })
        
        # Send email notifications
        if response_protocol.get('send_email', True):
            for contact in emergency_contacts:
                if contact.get('email'):
                    email_result = notification_service.send_email(
                        contact['email'],
                        notification_content['email_subject'],
                        notification_content['email_body']
                    )
                    notifications_sent.append({
                        'type': 'email',
                        'recipient': contact['name'],
                        'email': contact['email'],
                        'success': email_result['success'],
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    })
        
        # Send push notifications
        if response_protocol.get('send_push', True):
            push_result = notification_service.send_push_notification(
                patient_id,
                notification_content['push_title'],
                notification_content['push_message']
            )
            notifications_sent.append({
                'type': 'push',
                'recipient': 'patient_app',
                'success': push_result['success'],
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        
        logger.info(f"Sent {len(notifications_sent)} emergency notifications")
        
    except Exception as e:
        logger.error(f"Error sending emergency notifications: {str(e)}")
        notifications_sent.append({
            'type': 'error',
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    
    return notifications_sent

def trigger_emergency_consultation(alert_record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Trigger emergency consultation with healthcare provider"""
    
    try:
        consultation_request = {
            'patient_id': alert_record['patient_id'],
            'alert_id': alert_record['alert_id'],
            'urgency_level': alert_record['urgency_level'],
            'consultation_type': 'emergency',
            'health_data': alert_record.get('health_data', {}),
            'priority': 'IMMEDIATE',
            'auto_triggered': True,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Invoke consultation function
        response = lambda_client.invoke(
            FunctionName=CONSULTATION_FUNCTION_ARN,
            InvocationType='Event',  # Asynchronous
            Payload=json.dumps(consultation_request)
        )
        
        logger.info(f"Emergency consultation triggered for alert {alert_record['alert_id']}")
        
        return {
            'consultation_triggered': True,
            'function_response': response['StatusCode'],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error triggering emergency consultation: {str(e)}")
        return {
            'consultation_triggered': False,
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

def get_emergency_contacts(patient_id: str) -> List[Dict[str, Any]]:
    """Get emergency contacts for a patient"""
    
    try:
        table = dynamodb.Table(EMERGENCY_CONTACTS_TABLE)
        
        response = table.query(
            KeyConditionExpression='patient_id = :patient_id',
            ExpressionAttributeValues={':patient_id': patient_id}
        )
        
        return response.get('Items', [])
        
    except ClientError as e:
        logger.error(f"Error getting emergency contacts: {str(e)}")
        return []

def prepare_notification_content(alert_record: Dict[str, Any]) -> Dict[str, str]:
    """Prepare notification content for different channels"""
    
    patient_id = alert_record['patient_id']
    urgency_level = alert_record['urgency_level']
    alert_type = alert_record['alert_type']
    timestamp = alert_record['created_at']
    
    # SMS message (short)
    sms_message = f"EMERGENCY ALERT: {urgency_level} health alert for patient {patient_id}. Alert type: {alert_type}. Time: {timestamp}. Please respond immediately."
    
    # Email subject
    email_subject = f"URGENT: {urgency_level} Health Emergency Alert - Patient {patient_id}"
    
    # Email body (detailed)
    email_body = f"""
EMERGENCY HEALTH ALERT

Patient ID: {patient_id}
Alert Level: {urgency_level}
Alert Type: {alert_type}
Timestamp: {timestamp}

Health Data:
{json.dumps(alert_record.get('health_data', {}), indent=2)}

This is an automated emergency alert from HealthConnect AI. 
Please take immediate action and contact emergency services if necessary.

Alert ID: {alert_record['alert_id']}
"""
    
    # Push notification
    push_title = f"{urgency_level} Health Alert"
    push_message = f"Emergency detected: {alert_type}. Please check your health status immediately."
    
    return {
        'sms_message': sms_message,
        'email_subject': email_subject,
        'email_body': email_body,
        'push_title': push_title,
        'push_message': push_message
    }

def initiate_ems_call(alert_record: Dict[str, Any]) -> Dict[str, Any]:
    """Initiate emergency medical services call (simulation for hackathon)"""
    
    # In production, this would integrate with actual EMS systems
    # For hackathon, we simulate the call
    
    try:
        ems_data = {
            'patient_id': alert_record['patient_id'],
            'alert_id': alert_record['alert_id'],
            'location': 'Patient registered address',  # Would get from patient profile
            'medical_condition': alert_record.get('health_data', {}),
            'urgency_level': alert_record['urgency_level'],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Log EMS call for demonstration
        logger.info(f"EMS CALL INITIATED: {json.dumps(ems_data, indent=2)}")
        
        return {
            'ems_call_initiated': True,
            'call_id': str(uuid.uuid4()),
            'estimated_arrival': '8-12 minutes',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error initiating EMS call: {str(e)}")
        return {
            'ems_call_initiated': False,
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

def notify_emergency_contacts(alert_record: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Notify emergency contacts"""
    
    try:
        patient_id = alert_record['patient_id']
        emergency_contacts = get_emergency_contacts(patient_id)
        
        contact_results = []
        notification_service = NotificationService()
        
        for contact in emergency_contacts:
            if contact.get('phone_number'):
                # Send SMS to emergency contact
                message = f"EMERGENCY: {alert_record['urgency_level']} health alert for {patient_id}. Please respond immediately."
                
                sms_result = notification_service.send_sms(
                    contact['phone_number'],
                    message
                )
                
                contact_results.append({
                    'contact_name': contact.get('name', 'Unknown'),
                    'contact_phone': contact['phone_number'],
                    'notification_sent': sms_result['success'],
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
        
        return contact_results
        
    except Exception as e:
        logger.error(f"Error notifying emergency contacts: {str(e)}")
        return []

def alert_healthcare_providers(alert_record: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Alert healthcare providers"""
    
    try:
        # In production, this would query healthcare provider database
        # For hackathon, we simulate provider notifications
        
        providers = [
            {'name': 'Dr. Smith', 'phone': '+1234567890', 'specialty': 'Emergency Medicine'},
            {'name': 'Nurse Johnson', 'phone': '+1234567891', 'specialty': 'Critical Care'}
        ]
        
        provider_results = []
        notification_service = NotificationService()
        
        for provider in providers:
            message = f"PATIENT EMERGENCY: {alert_record['urgency_level']} alert for patient {alert_record['patient_id']}. Alert ID: {alert_record['alert_id']}"
            
            sms_result = notification_service.send_sms(
                provider['phone'],
                message
            )
            
            provider_results.append({
                'provider_name': provider['name'],
                'specialty': provider['specialty'],
                'notification_sent': sms_result['success'],
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        
        return provider_results
        
    except Exception as e:
        logger.error(f"Error alerting healthcare providers: {str(e)}")
        return []

def increase_device_monitoring(alert_record: Dict[str, Any]) -> Dict[str, Any]:
    """Increase device monitoring frequency during emergency"""
    
    try:
        # Send event to increase monitoring frequency
        event_detail = {
            'patient_id': alert_record['patient_id'],
            'alert_id': alert_record['alert_id'],
            'monitoring_mode': 'emergency',
            'frequency_multiplier': 3,  # 3x normal frequency
            'duration_minutes': 60,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        eventbridge.put_events(
            Entries=[
                {
                    'Source': 'healthconnect.emergency',
                    'DetailType': 'Increase Device Monitoring',
                    'Detail': json.dumps(event_detail),
                    'EventBusName': EVENT_BUS_NAME
                }
            ]
        )
        
        return {
            'monitoring_increased': True,
            'frequency_multiplier': 3,
            'duration_minutes': 60,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error increasing device monitoring: {str(e)}")
        return {
            'monitoring_increased': False,
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

def send_emergency_response_event(alert_record: Dict[str, Any]) -> None:
    """Send emergency response completion event"""
    
    try:
        event_detail = {
            'alert_id': alert_record['alert_id'],
            'patient_id': alert_record['patient_id'],
            'urgency_level': alert_record['urgency_level'],
            'status': alert_record['status'],
            'response_actions_count': len(alert_record.get('response_actions', [])),
            'notifications_sent_count': len(alert_record.get('notifications_sent', [])),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        eventbridge.put_events(
            Entries=[
                {
                    'Source': 'healthconnect.emergency',
                    'DetailType': 'Emergency Response Complete',
                    'Detail': json.dumps(event_detail),
                    'EventBusName': EVENT_BUS_NAME
                }
            ]
        )
        
    except Exception as e:
        logger.error(f"Error sending emergency response event: {str(e)}")

def schedule_follow_up_actions(alert_record: Dict[str, Any], response_protocol: Dict[str, Any]) -> None:
    """Schedule follow-up actions for emergency alert"""
    
    try:
        # Schedule 5-minute follow-up
        follow_up_time = datetime.now(timezone.utc) + timedelta(minutes=5)
        
        follow_up_event = {
            'alert_id': alert_record['alert_id'],
            'patient_id': alert_record['patient_id'],
            'follow_up_type': 'status_check',
            'scheduled_time': follow_up_time.isoformat()
        }
        
        # In production, this would use EventBridge scheduled rules
        # For hackathon, we log the scheduled action
        logger.info(f"Follow-up scheduled for {follow_up_time}: {json.dumps(follow_up_event)}")
        
    except Exception as e:
        logger.error(f"Error scheduling follow-up actions: {str(e)}")

def handle_manual_emergency(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle manually triggered emergency"""
    
    try:
        required_fields = ['patient_id', 'emergency_type']
        for field in required_fields:
            if field not in body:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': f'Missing required field: {field}'})
                }
        
        emergency_data = {
            'patient_id': body['patient_id'],
            'alert_type': 'manual_trigger',
            'emergency_type': body['emergency_type'],
            'urgency_level': body.get('urgency_level', 'HIGH'),
            'source': 'manual',
            'description': body.get('description', ''),
            'location': body.get('location', ''),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        alert_response = process_emergency_alert(emergency_data)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'alert_processed': alert_response['success'],
                'alert_id': alert_response.get('alert_id'),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error handling manual emergency: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Failed to process manual emergency'})
        }

def get_emergency_alerts(query_params: Dict[str, Any]) -> Dict[str, Any]:
    """Get emergency alerts with filtering"""
    
    try:
        table = dynamodb.Table(EMERGENCY_ALERTS_TABLE)
        
        # Build query based on parameters
        if 'patient_id' in query_params:
            # Query by patient ID
            response = table.query(
                IndexName='PatientIndex',  # Assuming GSI exists
                KeyConditionExpression='patient_id = :patient_id',
                ExpressionAttributeValues={':patient_id': query_params['patient_id']},
                ScanIndexForward=False,  # Most recent first
                Limit=int(query_params.get('limit', 50))
            )
        else:
            # Scan all alerts
            response = table.scan(
                Limit=int(query_params.get('limit', 50))
            )
        
        alerts = response.get('Items', [])
        
        # Filter by status if specified
        if 'status' in query_params:
            alerts = [alert for alert in alerts if alert.get('status') == query_params['status']]
        
        # Filter by urgency level if specified
        if 'urgency_level' in query_params:
            alerts = [alert for alert in alerts if alert.get('urgency_level') == query_params['urgency_level']]
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'alerts': alerts,
                'count': len(alerts),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error getting emergency alerts: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Failed to retrieve alerts'})
        }

def update_alert_status(body: Dict[str, Any]) -> Dict[str, Any]:
    """Update emergency alert status"""
    
    try:
        alert_id = body.get('alert_id')
        new_status = body.get('status')
        
        if not alert_id or not new_status:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'alert_id and status are required'})
            }
        
        table = dynamodb.Table(EMERGENCY_ALERTS_TABLE)
        
        response = table.update_item(
            Key={'alert_id': alert_id},
            UpdateExpression='SET #status = :status, updated_at = :updated_at',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': new_status,
                ':updated_at': datetime.now(timezone.utc).isoformat()
            },
            ReturnValues='ALL_NEW'
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'updated': True,
                'alert': response['Attributes'],
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error updating alert status: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Failed to update alert status'})
        }

def test_emergency_system() -> Dict[str, Any]:
    """Test emergency system functionality"""
    
    try:
        test_alert = {
            'patient_id': 'test_patient_123',
            'alert_type': 'system_test',
            'urgency_level': 'MEDIUM',
            'source': 'test',
            'health_data': {
                'heart_rate': 95,
                'blood_pressure': {'systolic': 140, 'diastolic': 90},
                'temperature': 37.2
            },
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Process test alert
        alert_response = process_emergency_alert(test_alert)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'test_completed': True,
                'alert_processed': alert_response['success'],
                'alert_id': alert_response.get('alert_id'),
                'system_status': 'operational',
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error testing emergency system: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'test_completed': False,
                'error': str(e),
                'system_status': 'error'
            })
        }
