import json
import logging
import os
from typing import Dict, Any
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
eventbridge = boto3.client('events')

# Environment variables
CONNECTIONS_TABLE = os.environ['WEBSOCKET_CONNECTIONS_TABLE']
EVENT_BUS_NAME = os.environ.get('EVENT_BUS_NAME')

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Handle WebSocket disconnection events
    
    Args:
        event: WebSocket disconnection event from API Gateway
        context: Lambda context object
        
    Returns:
        Dict containing status code
    """
    try:
        connection_id = event['requestContext']['connectionId']
        
        # Get connection info before deletion
        table = dynamodb.Table(CONNECTIONS_TABLE)
        
        try:
            response = table.get_item(Key={'connection_id': connection_id})
            connection_data = response.get('Item', {})
        except ClientError:
            connection_data = {}
        
        # Delete connection from table
        try:
            table.delete_item(Key={'connection_id': connection_id})
        except ClientError as e:
            logger.warning(f"Failed to delete connection {connection_id}: {str(e)}")
        
        # Send disconnection event if user was identified
        if connection_data.get('user_id') and EVENT_BUS_NAME:
            try:
                event_detail = {
                    'connection_id': connection_id,
                    'user_id': connection_data['user_id'],
                    'user_type': connection_data.get('user_type', 'unknown'),
                    'session_id': connection_data.get('session_id'),
                    'connected_duration': calculate_connection_duration(connection_data),
                    'disconnected_at': datetime.now(timezone.utc).isoformat()
                }
                
                eventbridge.put_events(
                    Entries=[
                        {
                            'Source': 'healthconnect.websocket',
                            'DetailType': 'WebSocket Disconnection',
                            'Detail': json.dumps(event_detail),
                            'EventBusName': EVENT_BUS_NAME
                        }
                    ]
                )
            except Exception as event_error:
                logger.error(f"Failed to send disconnection event: {str(event_error)}")
        
        logger.info(f"WebSocket disconnection handled: {connection_id}")
        
        return {'statusCode': 200}
        
    except Exception as e:
        logger.error(f"Error handling WebSocket disconnection: {str(e)}")
        return {'statusCode': 500}

def calculate_connection_duration(connection_data: Dict[str, Any]) -> int:
    """Calculate connection duration in seconds"""
    try:
        connected_at = connection_data.get('connected_at')
        if connected_at:
            connected_time = datetime.fromisoformat(connected_at.replace('Z', '+00:00'))
            duration = (datetime.now(timezone.utc) - connected_time).total_seconds()
            return int(duration)
    except Exception:
        pass
    return 0
