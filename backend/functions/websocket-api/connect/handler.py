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

# Environment variables
CONNECTIONS_TABLE = os.environ['WEBSOCKET_CONNECTIONS_TABLE']

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Handle WebSocket connection events
    
    Args:
        event: WebSocket connection event from API Gateway
        context: Lambda context object
        
    Returns:
        Dict containing status code
    """
    try:
        connection_id = event['requestContext']['connectionId']
        
        # Extract query parameters
        query_params = event.get('queryStringParameters') or {}
        user_id = query_params.get('user_id')
        user_type = query_params.get('user_type', 'patient')  # patient, provider, admin
        session_id = query_params.get('session_id')
        
        # Store connection information
        connection_data = {
            'connection_id': connection_id,
            'user_id': user_id,
            'user_type': user_type,
            'session_id': session_id,
            'connected_at': datetime.now(timezone.utc).isoformat(),
            'last_activity': datetime.now(timezone.utc).isoformat(),
            'status': 'connected',
            'ttl': int(datetime.now().timestamp()) + 7200  # 2 hours TTL
        }
        
        # Save to DynamoDB
        table = dynamodb.Table(CONNECTIONS_TABLE)
        table.put_item(Item=connection_data)
        
        logger.info(f"WebSocket connection established: {connection_id} for user: {user_id}")
        
        return {'statusCode': 200}
        
    except Exception as e:
        logger.error(f"Error handling WebSocket connection: {str(e)}")
        return {'statusCode': 500}
