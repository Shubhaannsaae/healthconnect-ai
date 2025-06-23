import json
import logging
import os
from typing import Dict, Any, List
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
apigateway_management = None  # Will be initialized per request

# Environment variables
CONNECTIONS_TABLE = os.environ['WEBSOCKET_CONNECTIONS_TABLE']
MESSAGES_TABLE = os.environ.get('WEBSOCKET_MESSAGES_TABLE')

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Handle WebSocket message events
    
    Args:
        event: WebSocket message event from API Gateway
        context: Lambda context object
        
    Returns:
        Dict containing status code
    """
    try:
        # Initialize API Gateway Management API client
        global apigateway_management
        domain_name = event['requestContext']['domainName']
        stage = event['requestContext']['stage']
        apigateway_management = boto3.client(
            'apigatewaymanagementapi',
            endpoint_url=f'https://{domain_name}/{stage}'
        )
        
        connection_id = event['requestContext']['connectionId']
        route_key = event['requestContext']['routeKey']
        
        # Parse message body
        try:
            message_body = json.loads(event.get('body', '{}'))
        except json.JSONDecodeError:
            return send_error_response(connection_id, 'Invalid JSON format')
        
        # Update last activity for connection
        update_connection_activity(connection_id)
        
        # Route message based on route key
        if route_key == 'sendMessage':
            return handle_send_message(connection_id, message_body)
        elif route_key == 'joinRoom':
            return handle_join_room(connection_id, message_body)
        elif route_key == 'leaveRoom':
            return handle_leave_room(connection_id, message_body)
        elif route_key == 'broadcast':
            return handle_broadcast_message(connection_id, message_body)
        elif route_key == 'healthData':
            return handle_health_data_message(connection_id, message_body)
        elif route_key == 'emergencyAlert':
            return handle_emergency_alert_message(connection_id, message_body)
        else:
            return send_error_response(connection_id, f'Unknown route: {route_key}')
        
    except Exception as e:
        logger.error(f"Error handling WebSocket message: {str(e)}")
        return {'statusCode': 500}

def handle_send_message(connection_id: str, message_body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle direct message sending"""
    try:
        target_user_id = message_body.get('target_user_id')
        message_content = message_body.get('message')
        message_type = message_body.get('type', 'text')
        
        if not target_user_id or not message_content:
            return send_error_response(connection_id, 'Missing target_user_id or message')
        
        # Get sender info
        sender_info = get_connection_info(connection_id)
        if not sender_info:
            return send_error_response(connection_id, 'Sender not found')
        
        # Find target user connections
        target_connections = get_user_connections(target_user_id)
        
        if not target_connections:
            return send_error_response(connection_id, 'Target user not connected')
        
        # Prepare message
        message_data = {
            'type': 'direct_message',
            'message_type': message_type,
            'from_user_id': sender_info.get('user_id'),
            'from_user_type': sender_info.get('user_type'),
            'message': message_content,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Send to all target user connections
        sent_count = 0
        for target_connection in target_connections:
            if send_message_to_connection(target_connection['connection_id'], message_data):
                sent_count += 1
        
        # Store message if table is configured
        if MESSAGES_TABLE:
            store_message(sender_info.get('user_id'), target_user_id, message_data)
        
        # Send confirmation to sender
        confirmation = {
            'type': 'message_sent',
            'target_user_id': target_user_id,
            'delivered_to_connections': sent_count,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        send_message_to_connection(connection_id, confirmation)
        
        return {'statusCode': 200}
        
    except Exception as e:
        logger.error(f"Error in handle_send_message: {str(e)}")
        return send_error_response(connection_id, 'Failed to send message')

def handle_join_room(connection_id: str, message_body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle joining a room/session"""
    try:
        room_id = message_body.get('room_id')
        room_type = message_body.get('room_type', 'general')
        
        if not room_id:
            return send_error_response(connection_id, 'Missing room_id')
        
        # Get connection info
        connection_info = get_connection_info(connection_id)
        if not connection_info:
            return send_error_response(connection_id, 'Connection not found')
        
        # Update connection with room info
        table = dynamodb.Table(CONNECTIONS_TABLE)
        table.update_item(
            Key={'connection_id': connection_id},
            UpdateExpression='SET room_id = :room_id, room_type = :room_type, last_activity = :timestamp',
            ExpressionAttributeValues={
                ':room_id': room_id,
                ':room_type': room_type,
                ':timestamp': datetime.now(timezone.utc).isoformat()
            }
        )
        
        # Notify other room members
        room_connections = get_room_connections(room_id, exclude_connection=connection_id)
        join_notification = {
            'type': 'user_joined_room',
            'room_id': room_id,
            'user_id': connection_info.get('user_id'),
            'user_type': connection_info.get('user_type'),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        for room_connection in room_connections:
            send_message_to_connection(room_connection['connection_id'], join_notification)
        
        # Send confirmation to joiner
        confirmation = {
            'type': 'room_joined',
            'room_id': room_id,
            'room_type': room_type,
            'room_members': len(room_connections) + 1,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        send_message_to_connection(connection_id, confirmation)
        
        return {'statusCode': 200}
        
    except Exception as e:
        logger.error(f"Error in handle_join_room: {str(e)}")
        return send_error_response(connection_id, 'Failed to join room')

def handle_broadcast_message(connection_id: str, message_body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle broadcasting message to room or all users"""
    try:
        message_content = message_body.get('message')
        broadcast_type = message_body.get('broadcast_type', 'room')  # room, all, user_type
        target_room = message_body.get('room_id')
        target_user_type = message_body.get('target_user_type')
        
        if not message_content:
            return send_error_response(connection_id, 'Missing message content')
        
        # Get sender info
        sender_info = get_connection_info(connection_id)
        if not sender_info:
            return send_error_response(connection_id, 'Sender not found')
        
        # Prepare broadcast message
        broadcast_data = {
            'type': 'broadcast_message',
            'from_user_id': sender_info.get('user_id'),
            'from_user_type': sender_info.get('user_type'),
            'message': message_content,
            'broadcast_type': broadcast_type,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Get target connections based on broadcast type
        target_connections = []
        
        if broadcast_type == 'room' and target_room:
            target_connections = get_room_connections(target_room, exclude_connection=connection_id)
        elif broadcast_type == 'user_type' and target_user_type:
            target_connections = get_connections_by_user_type(target_user_type, exclude_connection=connection_id)
        elif broadcast_type == 'all':
            target_connections = get_all_connections(exclude_connection=connection_id)
        
        # Send to target connections
        sent_count = 0
        for target_connection in target_connections:
            if send_message_to_connection(target_connection['connection_id'], broadcast_data):
                sent_count += 1
        
        # Send confirmation to sender
        confirmation = {
            'type': 'broadcast_sent',
            'broadcast_type': broadcast_type,
            'delivered_to_connections': sent_count,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        send_message_to_connection(connection_id, confirmation)
        
        return {'statusCode': 200}
        
    except Exception as e:
        logger.error(f"Error in handle_broadcast_message: {str(e)}")
        return send_error_response(connection_id, 'Failed to broadcast message')

def handle_health_data_message(connection_id: str, message_body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle real-time health data messages"""
    try:
        health_data = message_body.get('health_data')
        patient_id = message_body.get('patient_id')
        data_type = message_body.get('data_type', 'vital_signs')
        
        if not health_data or not patient_id:
            return send_error_response(connection_id, 'Missing health_data or patient_id')
        
        # Get sender info
        sender_info = get_connection_info(connection_id)
        if not sender_info:
            return send_error_response(connection_id, 'Sender not found')
        
        # Prepare health data message
        health_message = {
            'type': 'health_data_update',
            'patient_id': patient_id,
            'data_type': data_type,
            'health_data': health_data,
            'from_user_id': sender_info.get('user_id'),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Send to healthcare providers monitoring this patient
        provider_connections = get_patient_provider_connections(patient_id)
        
        sent_count = 0
        for provider_connection in provider_connections:
            if send_message_to_connection(provider_connection['connection_id'], health_message):
                sent_count += 1
        
        # Send confirmation
        confirmation = {
            'type': 'health_data_sent',
            'patient_id': patient_id,
            'delivered_to_providers': sent_count,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        send_message_to_connection(connection_id, confirmation)
        
        return {'statusCode': 200}
        
    except Exception as e:
        logger.error(f"Error in handle_health_data_message: {str(e)}")
        return send_error_response(connection_id, 'Failed to send health data')

def handle_emergency_alert_message(connection_id: str, message_body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle emergency alert messages"""
    try:
        alert_data = message_body.get('alert_data')
        patient_id = message_body.get('patient_id')
        urgency_level = message_body.get('urgency_level', 'HIGH')
        
        if not alert_data or not patient_id:
            return send_error_response(connection_id, 'Missing alert_data or patient_id')
        
        # Get sender info
        sender_info = get_connection_info(connection_id)
        if not sender_info:
            return send_error_response(connection_id, 'Sender not found')
        
        # Prepare emergency alert message
        alert_message = {
            'type': 'emergency_alert',
            'patient_id': patient_id,
            'urgency_level': urgency_level,
            'alert_data': alert_data,
            'from_user_id': sender_info.get('user_id'),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Send to all healthcare providers (emergency broadcast)
        provider_connections = get_connections_by_user_type('provider')
        admin_connections = get_connections_by_user_type('admin')
        
        all_emergency_connections = provider_connections + admin_connections
        
        sent_count = 0
        for emergency_connection in all_emergency_connections:
            if send_message_to_connection(emergency_connection['connection_id'], alert_message):
                sent_count += 1
        
        # Send confirmation
        confirmation = {
            'type': 'emergency_alert_sent',
            'patient_id': patient_id,
            'urgency_level': urgency_level,
            'delivered_to_responders': sent_count,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        send_message_to_connection(connection_id, confirmation)
        
        return {'statusCode': 200}
        
    except Exception as e:
        logger.error(f"Error in handle_emergency_alert_message: {str(e)}")
        return send_error_response(connection_id, 'Failed to send emergency alert')

# Helper functions
def get_connection_info(connection_id: str) -> Dict[str, Any]:
    """Get connection information from DynamoDB"""
    try:
        table = dynamodb.Table(CONNECTIONS_TABLE)
        response = table.get_item(Key={'connection_id': connection_id})
        return response.get('Item', {})
    except Exception as e:
        logger.error(f"Error getting connection info: {str(e)}")
        return {}

def get_user_connections(user_id: str) -> List[Dict[str, Any]]:
    """Get all connections for a specific user"""
    try:
        table = dynamodb.Table(CONNECTIONS_TABLE)
        response = table.scan(
            FilterExpression='user_id = :user_id AND #status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':user_id': user_id,
                ':status': 'connected'
            }
        )
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error getting user connections: {str(e)}")
        return []

def send_message_to_connection(connection_id: str, message: Dict[str, Any]) -> bool:
    """Send message to specific WebSocket connection"""
    try:
        apigateway_management.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(message)
        )
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'GoneException':
            # Connection is stale, remove it
            remove_stale_connection(connection_id)
        logger.error(f"Error sending message to {connection_id}: {str(e)}")
        return False

def send_error_response(connection_id: str, error_message: str) -> Dict[str, Any]:
    """Send error response to connection"""
    error_response = {
        'type': 'error',
        'message': error_message,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    send_message_to_connection(connection_id, error_response)
    return {'statusCode': 400}

def update_connection_activity(connection_id: str) -> None:
    """Update last activity timestamp for connection"""
    try:
        table = dynamodb.Table(CONNECTIONS_TABLE)
        table.update_item(
            Key={'connection_id': connection_id},
            UpdateExpression='SET last_activity = :timestamp',
            ExpressionAttributeValues={
                ':timestamp': datetime.now(timezone.utc).isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Error updating connection activity: {str(e)}")

def remove_stale_connection(connection_id: str) -> None:
    """Remove stale connection from DynamoDB"""
    try:
        table = dynamodb.Table(CONNECTIONS_TABLE)
        table.delete_item(Key={'connection_id': connection_id})
        logger.info(f"Removed stale connection: {connection_id}")
    except Exception as e:
        logger.error(f"Error removing stale connection: {str(e)}")
