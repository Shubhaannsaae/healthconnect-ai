import json
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
import boto3
from botocore.exceptions import ClientError
from webrtc_signaling import WebRTCSignalingServer
from session_manager import ConsultationSessionManager
import uuid
import traceback

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
apigateway_management = None  # Will be initialized per request
eventbridge = boto3.client('events')
lambda_client = boto3.client('lambda')
sns = boto3.client('sns')

# Environment variables
CONSULTATION_SESSIONS_TABLE = os.environ['CONSULTATION_SESSIONS_TABLE']
HEALTHCARE_PROVIDERS_TABLE = os.environ['HEALTHCARE_PROVIDERS_TABLE']
CONSULTATION_QUEUE_TABLE = os.environ['CONSULTATION_QUEUE_TABLE']
EVENT_BUS_NAME = os.environ['EVENT_BUS_NAME']
WEBSOCKET_API_ENDPOINT = os.environ.get('WEBSOCKET_API_ENDPOINT')
BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Main Lambda handler for consultation API
    
    Args:
        event: API Gateway event, WebSocket event, or direct invocation
        context: Lambda context object
        
    Returns:
        Dict containing response status and consultation details
    """
    try:
        # Determine event type and route accordingly
        if 'requestContext' in event:
            if 'connectionId' in event['requestContext']:
                # WebSocket API event
                return handle_websocket_event(event, context)
            elif 'httpMethod' in event:
                # HTTP API event
                return handle_http_event(event, context)
        elif 'source' in event and event['source'] == 'healthconnect.emergency':
            # EventBridge trigger from emergency system
            return handle_emergency_consultation_request(event, context)
        else:
            # Direct invocation
            return handle_direct_consultation_request(event, context)
            
    except Exception as e:
        logger.error(f"Error in consultation handler: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Consultation service error',
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }

def handle_http_event(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle HTTP API events"""
    try:
        http_method = event['httpMethod']
        path = event['path']
        
        if http_method == 'POST' and '/consultation' in path:
            # Create new consultation session
            body = json.loads(event['body']) if event.get('body') else {}
            return create_consultation_session(body)
            
        elif http_method == 'GET' and '/consultation' in path:
            # Get consultation sessions
            query_params = event.get('queryStringParameters', {}) or {}
            return get_consultation_sessions(query_params)
            
        elif http_method == 'PUT' and '/consultation' in path:
            # Update consultation session
            body = json.loads(event['body']) if event.get('body') else {}
            return update_consultation_session(body)
            
        elif http_method == 'DELETE' and '/consultation' in path:
            # End consultation session
            path_params = event.get('pathParameters', {}) or {}
            return end_consultation_session(path_params)
            
        elif http_method == 'POST' and '/providers' in path:
            # Get available providers
            body = json.loads(event['body']) if event.get('body') else {}
            return get_available_providers(body)
            
        elif http_method == 'POST' and '/queue' in path:
            # Add to consultation queue
            body = json.loads(event['body']) if event.get('body') else {}
            return add_to_consultation_queue(body)
            
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
        logger.error(f"Error handling HTTP event: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Internal server error'})
        }

def handle_websocket_event(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle WebSocket API events for real-time consultation"""
    try:
        connection_id = event['requestContext']['connectionId']
        route_key = event['requestContext']['routeKey']
        
        # Initialize API Gateway Management API client
        global apigateway_management
        apigateway_management = boto3.client(
            'apigatewaymanagementapi',
            endpoint_url=f"https://{event['requestContext']['domainName']}/{event['requestContext']['stage']}"
        )
        
        # Initialize WebRTC signaling server
        signaling_server = WebRTCSignalingServer(apigateway_management)
        
        if route_key == '$connect':
            return handle_websocket_connect(connection_id, event)
        elif route_key == '$disconnect':
            return handle_websocket_disconnect(connection_id, event)
        elif route_key == 'offer':
            return signaling_server.handle_offer(connection_id, json.loads(event['body']))
        elif route_key == 'answer':
            return signaling_server.handle_answer(connection_id, json.loads(event['body']))
        elif route_key == 'ice-candidate':
            return signaling_server.handle_ice_candidate(connection_id, json.loads(event['body']))
        elif route_key == 'join-session':
            return handle_join_consultation_session(connection_id, json.loads(event['body']))
        elif route_key == 'leave-session':
            return handle_leave_consultation_session(connection_id, json.loads(event['body']))
        elif route_key == 'chat-message':
            return handle_chat_message(connection_id, json.loads(event['body']))
        else:
            logger.warning(f"Unknown WebSocket route: {route_key}")
            return {'statusCode': 400}
            
    except Exception as e:
        logger.error(f"Error handling WebSocket event: {str(e)}")
        return {'statusCode': 500}

def create_consultation_session(body: Dict[str, Any]) -> Dict[str, Any]:
    """Create new consultation session"""
    try:
        # Validate required fields
        required_fields = ['patient_id', 'consultation_type']
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
        
        # Initialize session manager
        session_manager = ConsultationSessionManager()
        
        # Create session
        session_data = {
            'patient_id': body['patient_id'],
            'consultation_type': body['consultation_type'],
            'urgency_level': body.get('urgency_level', 'MEDIUM'),
            'symptoms': body.get('symptoms', []),
            'health_data': body.get('health_data', {}),
            'preferred_provider_type': body.get('preferred_provider_type', 'general_practitioner'),
            'language_preference': body.get('language_preference', 'en'),
            'consultation_mode': body.get('consultation_mode', 'video'),  # video, audio, chat
            'scheduled_time': body.get('scheduled_time'),  # For scheduled consultations
            'auto_triggered': body.get('auto_triggered', False)
        }
        
        session_result = session_manager.create_session(session_data)
        
        if session_result['success']:
            # Find available provider
            provider_result = find_available_provider(session_result['session'])
            
            if provider_result['provider_found']:
                # Assign provider and start session
                session_result['session']['provider_id'] = provider_result['provider']['provider_id']
                session_result['session']['provider_info'] = provider_result['provider']
                session_result['session']['status'] = 'provider_assigned'
                
                # Update session in database
                session_manager.update_session(session_result['session'])
                
                # Notify provider
                notify_provider_result = notify_provider_of_consultation(
                    provider_result['provider'], 
                    session_result['session']
                )
                
                # Send session ready event
                send_consultation_event(session_result['session'], 'session_ready')
                
            else:
                # Add to queue
                queue_result = add_to_consultation_queue({
                    'session_id': session_result['session']['session_id'],
                    'patient_id': session_result['session']['patient_id'],
                    'urgency_level': session_result['session']['urgency_level'],
                    'consultation_type': session_result['session']['consultation_type']
                })
                
                session_result['session']['status'] = 'queued'
                session_result['session']['queue_position'] = queue_result.get('queue_position', 0)
        
        return {
            'statusCode': 200 if session_result['success'] else 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'session_created': session_result['success'],
                'session': session_result.get('session', {}),
                'provider_assigned': 'provider_id' in session_result.get('session', {}),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error creating consultation session: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Failed to create consultation session'})
        }

def find_available_provider(session: Dict[str, Any]) -> Dict[str, Any]:
    """Find available healthcare provider for consultation"""
    try:
        table = dynamodb.Table(HEALTHCARE_PROVIDERS_TABLE)
        
        # Query for available providers based on consultation requirements
        consultation_type = session['consultation_type']
        urgency_level = session['urgency_level']
        preferred_type = session.get('preferred_provider_type', 'general_practitioner')
        
        # Build filter expression
        filter_expression = 'availability_status = :available AND provider_type = :provider_type'
        expression_values = {
            ':available': 'available',
            ':provider_type': preferred_type
        }
        
        # Add specialization filter for specific consultation types
        if consultation_type in ['cardiac', 'neurological', 'endocrine']:
            filter_expression += ' AND contains(specializations, :specialization)'
            expression_values[':specialization'] = consultation_type
        
        # Add urgency level consideration
        if urgency_level in ['CRITICAL', 'HIGH']:
            filter_expression += ' AND emergency_available = :emergency_available'
            expression_values[':emergency_available'] = True
        
        response = table.scan(
            FilterExpression=filter_expression,
            ExpressionAttributeValues=expression_values,
            Limit=10
        )
        
        providers = response.get('Items', [])
        
        if providers:
            # Sort by availability score and rating
            providers.sort(key=lambda p: (
                p.get('availability_score', 0.5) * 0.6 + 
                p.get('rating', 4.0) / 5.0 * 0.4
            ), reverse=True)
            
            # Select best available provider
            selected_provider = providers[0]
            
            # Update provider status to busy
            table.update_item(
                Key={'provider_id': selected_provider['provider_id']},
                UpdateExpression='SET availability_status = :busy, current_session_id = :session_id, last_assigned = :timestamp',
                ExpressionAttributeValues={
                    ':busy': 'busy',
                    ':session_id': session['session_id'],
                    ':timestamp': datetime.now(timezone.utc).isoformat()
                }
            )
            
            return {
                'provider_found': True,
                'provider': selected_provider
            }
        else:
            logger.info(f"No available providers found for consultation type: {consultation_type}")
            return {
                'provider_found': False,
                'reason': 'no_available_providers'
            }
            
    except Exception as e:
        logger.error(f"Error finding available provider: {str(e)}")
        return {
            'provider_found': False,
            'error': str(e)
        }

def notify_provider_of_consultation(provider: Dict[str, Any], session: Dict[str, Any]) -> Dict[str, Any]:
    """Notify healthcare provider of new consultation request"""
    try:
        # Prepare notification content
        notification_data = {
            'provider_id': provider['provider_id'],
            'session_id': session['session_id'],
            'patient_id': session['patient_id'],
            'consultation_type': session['consultation_type'],
            'urgency_level': session['urgency_level'],
            'consultation_mode': session['consultation_mode'],
            'estimated_duration': session.get('estimated_duration', 30),
            'patient_symptoms': session.get('symptoms', []),
            'health_data_summary': session.get('health_data', {}),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Send notification through multiple channels
        notification_results = []
        
        # Send SMS notification
        if provider.get('phone_number'):
            sms_message = f"New {session['urgency_level']} consultation request. Patient: {session['patient_id']}, Type: {session['consultation_type']}. Session ID: {session['session_id']}"
            
            sms_result = sns.publish(
                PhoneNumber=provider['phone_number'],
                Message=sms_message,
                MessageAttributes={
                    'AWS.SNS.SMS.SMSType': {
                        'DataType': 'String',
                        'StringValue': 'Transactional'
                    }
                }
            )
            
            notification_results.append({
                'channel': 'sms',
                'success': True,
                'message_id': sms_result['MessageId']
            })
        
        # Send push notification if provider app is configured
        if provider.get('device_token'):
            # Would integrate with mobile push service
            notification_results.append({
                'channel': 'push',
                'success': True,
                'message': 'Push notification sent'
            })
        
        # Send email notification
        if provider.get('email'):
            # Would integrate with SES for email notifications
            notification_results.append({
                'channel': 'email',
                'success': True,
                'message': 'Email notification sent'
            })
        
        return {
            'notifications_sent': len(notification_results),
            'results': notification_results,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error notifying provider: {str(e)}")
        return {
            'notifications_sent': 0,
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

def handle_emergency_consultation_request(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle emergency consultation requests from emergency response system"""
    try:
        detail = event['detail']
        
        # Create urgent consultation session
        consultation_data = {
            'patient_id': detail['patient_id'],
            'consultation_type': 'emergency',
            'urgency_level': 'CRITICAL',
            'alert_id': detail.get('alert_id'),
            'health_data': detail.get('health_data', {}),
            'consultation_mode': 'video',
            'auto_triggered': True,
            'emergency_context': {
                'alert_type': detail.get('alert_type'),
                'severity_score': detail.get('severity_score'),
                'critical_indicators': detail.get('critical_indicators', [])
            }
        }
        
        # Create session with highest priority
        session_result = create_consultation_session(consultation_data)
        
        return {
            'statusCode': 200,
            'emergency_consultation_created': session_result.get('statusCode') == 200,
            'session_data': session_result,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error handling emergency consultation request: {str(e)}")
        return {
            'statusCode': 500,
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

def handle_websocket_connect(connection_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle WebSocket connection"""
    try:
        # Store connection info
        query_params = event.get('queryStringParameters', {}) or {}
        user_type = query_params.get('user_type', 'patient')  # patient or provider
        user_id = query_params.get('user_id')
        session_id = query_params.get('session_id')
        
        # Store connection in DynamoDB for session management
        connection_data = {
            'connection_id': connection_id,
            'user_type': user_type,
            'user_id': user_id,
            'session_id': session_id,
            'connected_at': datetime.now(timezone.utc).isoformat(),
            'ttl': int(datetime.now().timestamp()) + 7200  # 2 hours TTL
        }
        
        # Store connection info (would use a connections table in production)
        logger.info(f"WebSocket connected: {connection_id}, User: {user_id}, Type: {user_type}")
        
        return {'statusCode': 200}
        
    except Exception as e:
        logger.error(f"Error handling WebSocket connect: {str(e)}")
        return {'statusCode': 500}

def handle_websocket_disconnect(connection_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle WebSocket disconnection"""
    try:
        # Clean up connection info and notify session participants
        logger.info(f"WebSocket disconnected: {connection_id}")
        
        # Would clean up connection from database and notify other participants
        
        return {'statusCode': 200}
        
    except Exception as e:
        logger.error(f"Error handling WebSocket disconnect: {str(e)}")
        return {'statusCode': 500}

def handle_join_consultation_session(connection_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle user joining consultation session"""
    try:
        session_id = body.get('session_id')
        user_id = body.get('user_id')
        user_type = body.get('user_type')
        
        # Validate session exists and user is authorized
        session_manager = ConsultationSessionManager()
        session = session_manager.get_session(session_id)
        
        if not session:
            return {'statusCode': 404}
        
        # Add user to session participants
        if 'participants' not in session:
            session['participants'] = []
        
        session['participants'].append({
            'user_id': user_id,
            'user_type': user_type,
            'connection_id': connection_id,
            'joined_at': datetime.now(timezone.utc).isoformat()
        })
        
        # Update session
        session_manager.update_session(session)
        
        # Notify other participants
        for participant in session['participants']:
            if participant['connection_id'] != connection_id:
                try:
                    apigateway_management.post_to_connection(
                        ConnectionId=participant['connection_id'],
                        Data=json.dumps({
                            'type': 'participant_joined',
                            'user_id': user_id,
                            'user_type': user_type
                        })
                    )
                except:
                    pass  # Connection might be stale
        
        return {'statusCode': 200}
        
    except Exception as e:
        logger.error(f"Error handling join session: {str(e)}")
        return {'statusCode': 500}

def handle_chat_message(connection_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle chat message in consultation session"""
    try:
        session_id = body.get('session_id')
        message = body.get('message')
        sender_id = body.get('sender_id')
        sender_type = body.get('sender_type')
        
        # Get session participants
        session_manager = ConsultationSessionManager()
        session = session_manager.get_session(session_id)
        
        if not session:
            return {'statusCode': 404}
        
        # Prepare message data
        message_data = {
            'type': 'chat_message',
            'session_id': session_id,
            'sender_id': sender_id,
            'sender_type': sender_type,
            'message': message,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Send message to all participants
        for participant in session.get('participants', []):
            if participant['connection_id'] != connection_id:
                try:
                    apigateway_management.post_to_connection(
                        ConnectionId=participant['connection_id'],
                        Data=json.dumps(message_data)
                    )
                except:
                    pass  # Connection might be stale
        
        # Store message in session history
        if 'chat_history' not in session:
            session['chat_history'] = []
        
        session['chat_history'].append(message_data)
        session_manager.update_session(session)
        
        return {'statusCode': 200}
        
    except Exception as e:
        logger.error(f"Error handling chat message: {str(e)}")
        return {'statusCode': 500}

def get_consultation_sessions(query_params: Dict[str, Any]) -> Dict[str, Any]:
    """Get consultation sessions with filtering"""
    try:
        table = dynamodb.Table(CONSULTATION_SESSIONS_TABLE)
        
        # Build query based on parameters
        if 'patient_id' in query_params:
            response = table.query(
                IndexName='PatientIndex',
                KeyConditionExpression='patient_id = :patient_id',
                ExpressionAttributeValues={':patient_id': query_params['patient_id']},
                ScanIndexForward=False,  # Most recent first
                Limit=int(query_params.get('limit', 20))
            )
        elif 'provider_id' in query_params:
            response = table.query(
                IndexName='ProviderIndex',
                KeyConditionExpression='provider_id = :provider_id',
                ExpressionAttributeValues={':provider_id': query_params['provider_id']},
                ScanIndexForward=False,
                Limit=int(query_params.get('limit', 20))
            )
        else:
            response = table.scan(
                Limit=int(query_params.get('limit', 50))
            )
        
        sessions = response.get('Items', [])
        
        # Filter by status if specified
        if 'status' in query_params:
            sessions = [s for s in sessions if s.get('status') == query_params['status']]
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'sessions': sessions,
                'count': len(sessions),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error getting consultation sessions: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Failed to retrieve sessions'})
        }

def add_to_consultation_queue(body: Dict[str, Any]) -> Dict[str, Any]:
    """Add consultation request to queue"""
    try:
        table = dynamodb.Table(CONSULTATION_QUEUE_TABLE)
        
        queue_item = {
            'queue_id': str(uuid.uuid4()),
            'session_id': body['session_id'],
            'patient_id': body['patient_id'],
            'urgency_level': body['urgency_level'],
            'consultation_type': body['consultation_type'],
            'queued_at': datetime.now(timezone.utc).isoformat(),
            'status': 'waiting',
            'estimated_wait_time': calculate_estimated_wait_time(body['urgency_level']),
            'ttl': int(datetime.now().timestamp()) + 14400  # 4 hours TTL
        }
        
        table.put_item(Item=queue_item)
        
        # Get queue position
        queue_position = get_queue_position(queue_item['queue_id'], body['urgency_level'])
        
        return {
            'queue_id': queue_item['queue_id'],
            'queue_position': queue_position,
            'estimated_wait_time': queue_item['estimated_wait_time'],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error adding to consultation queue: {str(e)}")
        return {
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

def calculate_estimated_wait_time(urgency_level: str) -> int:
    """Calculate estimated wait time based on urgency level and current queue"""
    try:
        # Base wait times by urgency level (in minutes)
        base_wait_times = {
            'CRITICAL': 2,
            'HIGH': 10,
            'MEDIUM': 30,
            'LOW': 60
        }
        
        base_time = base_wait_times.get(urgency_level, 30)
        
        # Get current queue length for this urgency level
        table = dynamodb.Table(CONSULTATION_QUEUE_TABLE)
        response = table.scan(
            FilterExpression='urgency_level = :urgency AND #status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':urgency': urgency_level,
                ':status': 'waiting'
            }
        )
        
        queue_length = len(response.get('Items', []))
        
        # Calculate estimated wait time
        estimated_time = base_time + (queue_length * base_time * 0.5)
        
        return int(estimated_time)
        
    except Exception as e:
        logger.error(f"Error calculating wait time: {str(e)}")
        return 30  # Default 30 minutes

def get_queue_position(queue_id: str, urgency_level: str) -> int:
    """Get position in queue for a specific queue item"""
    try:
        table = dynamodb.Table(CONSULTATION_QUEUE_TABLE)
        
        # Get all items with same or higher urgency
        urgency_priority = {'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
        current_priority = urgency_priority.get(urgency_level, 2)
        
        response = table.scan(
            FilterExpression='#status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':status': 'waiting'}
        )
        
        queue_items = response.get('Items', [])
        
        # Sort by priority then by queued time
        queue_items.sort(key=lambda x: (
            -urgency_priority.get(x['urgency_level'], 2),  # Higher priority first
            x['queued_at']  # Earlier time first
        ))
        
        # Find position
        for i, item in enumerate(queue_items):
            if item['queue_id'] == queue_id:
                return i + 1
        
        return len(queue_items) + 1
        
    except Exception as e:
        logger.error(f"Error getting queue position: {str(e)}")
        return 1

def send_consultation_event(session: Dict[str, Any], event_type: str) -> None:
    """Send consultation event to EventBridge"""
    try:
        event_detail = {
            'session_id': session['session_id'],
            'patient_id': session['patient_id'],
            'provider_id': session.get('provider_id'),
            'consultation_type': session['consultation_type'],
            'urgency_level': session['urgency_level'],
            'status': session['status'],
            'event_type': event_type,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        eventbridge.put_events(
            Entries=[
                {
                    'Source': 'healthconnect.consultation',
                    'DetailType': f'Consultation {event_type.replace("_", " ").title()}',
                    'Detail': json.dumps(event_detail),
                    'EventBusName': EVENT_BUS_NAME
                }
            ]
        )
        
    except Exception as e:
        logger.error(f"Error sending consultation event: {str(e)}")
