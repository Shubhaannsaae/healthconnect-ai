import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError
from aws_clients import aws_clients
import json

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Production-grade database operations manager for DynamoDB"""[1]
    
    def __init__(self):
        self.dynamodb = aws_clients.get_resource('dynamodb')
    
    def put_item(self, table_name: str, item: Dict[str, Any], condition_expression: Optional[str] = None) -> bool:
        """Put item into DynamoDB table with optional condition"""[1]
        try:
            table = self.dynamodb.Table(table_name)
            
            # Add timestamp if not present
            if 'created_at' not in item:
                item['created_at'] = datetime.now(timezone.utc).isoformat()
            
            item['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            kwargs = {'Item': item}
            if condition_expression:
                kwargs['ConditionExpression'] = condition_expression
            
            table.put_item(**kwargs)
            
            logger.debug(f"Successfully put item in {table_name}")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ConditionalCheckFailedException':
                logger.warning(f"Conditional check failed for {table_name}")
                return False
            else:
                logger.error(f"Error putting item in {table_name}: {str(e)}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error putting item in {table_name}: {str(e)}")
            raise
    
    def get_item(self, table_name: str, key: Dict[str, Any], consistent_read: bool = False) -> Optional[Dict[str, Any]]:
        """Get item from DynamoDB table"""[1]
        try:
            table = self.dynamodb.Table(table_name)
            
            response = table.get_item(
                Key=key,
                ConsistentRead=consistent_read
            )
            
            item = response.get('Item')
            if item:
                logger.debug(f"Successfully retrieved item from {table_name}")
            else:
                logger.debug(f"Item not found in {table_name}")
            
            return item
            
        except ClientError as e:
            logger.error(f"Error getting item from {table_name}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting item from {table_name}: {str(e)}")
            raise
    
    def update_item(
        self, 
        table_name: str, 
        key: Dict[str, Any], 
        update_expression: str,
        expression_attribute_values: Dict[str, Any],
        expression_attribute_names: Optional[Dict[str, str]] = None,
        condition_expression: Optional[str] = None,
        return_values: str = 'UPDATED_NEW'
    ) -> Dict[str, Any]:
        """Update item in DynamoDB table"""[1]
        try:
            table = self.dynamodb.Table(table_name)
            
            # Always update the updated_at timestamp
            if ':updated_at' not in expression_attribute_values:
                if not update_expression.strip().endswith(','):
                    update_expression += ','
                update_expression += ' updated_at = :updated_at'
                expression_attribute_values[':updated_at'] = datetime.now(timezone.utc).isoformat()
            
            kwargs = {
                'Key': key,
                'UpdateExpression': update_expression,
                'ExpressionAttributeValues': expression_attribute_values,
                'ReturnValues': return_values
            }
            
            if expression_attribute_names:
                kwargs['ExpressionAttributeNames'] = expression_attribute_names
            
            if condition_expression:
                kwargs['ConditionExpression'] = condition_expression
            
            response = table.update_item(**kwargs)
            
            logger.debug(f"Successfully updated item in {table_name}")
            return response
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ConditionalCheckFailedException':
                logger.warning(f"Conditional check failed for update in {table_name}")
                raise
            else:
                logger.error(f"Error updating item in {table_name}: {str(e)}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error updating item in {table_name}: {str(e)}")
            raise
    
    def delete_item(self, table_name: str, key: Dict[str, Any], condition_expression: Optional[str] = None) -> bool:
        """Delete item from DynamoDB table"""[1]
        try:
            table = self.dynamodb.Table(table_name)
            
            kwargs = {'Key': key}
            if condition_expression:
                kwargs['ConditionExpression'] = condition_expression
            
            table.delete_item(**kwargs)
            
            logger.debug(f"Successfully deleted item from {table_name}")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ConditionalCheckFailedException':
                logger.warning(f"Conditional check failed for delete in {table_name}")
                return False
            else:
                logger.error(f"Error deleting item from {table_name}: {str(e)}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error deleting item from {table_name}: {str(e)}")
            raise
    
    def query_items(
        self,
        table_name: str,
        key_condition_expression: str,
        expression_attribute_values: Dict[str, Any],
        expression_attribute_names: Optional[Dict[str, str]] = None,
        filter_expression: Optional[str] = None,
        index_name: Optional[str] = None,
        limit: Optional[int] = None,
        scan_index_forward: bool = True,
        exclusive_start_key: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Query items from DynamoDB table"""[1]
        try:
            table = self.dynamodb.Table(table_name)
            
            kwargs = {
                'KeyConditionExpression': key_condition_expression,
                'ExpressionAttributeValues': expression_attribute_values,
                'ScanIndexForward': scan_index_forward
            }
            
            if expression_attribute_names:
                kwargs['ExpressionAttributeNames'] = expression_attribute_names
            
            if filter_expression:
                kwargs['FilterExpression'] = filter_expression
            
            if index_name:
                kwargs['IndexName'] = index_name
            
            if limit:
                kwargs['Limit'] = limit
            
            if exclusive_start_key:
                kwargs['ExclusiveStartKey'] = exclusive_start_key
            
            response = table.query(**kwargs)
            
            logger.debug(f"Successfully queried {len(response.get('Items', []))} items from {table_name}")
            return response
            
        except ClientError as e:
            logger.error(f"Error querying items from {table_name}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error querying items from {table_name}: {str(e)}")
            raise
    
    def scan_items(
        self,
        table_name: str,
        filter_expression: Optional[str] = None,
        expression_attribute_values: Optional[Dict[str, Any]] = None,
        expression_attribute_names: Optional[Dict[str, str]] = None,
        index_name: Optional[str] = None,
        limit: Optional[int] = None,
        exclusive_start_key: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Scan items from DynamoDB table"""[1]
        try:
            table = self.dynamodb.Table(table_name)
            
            kwargs = {}
            
            if filter_expression:
                kwargs['FilterExpression'] = filter_expression
            
            if expression_attribute_values:
                kwargs['ExpressionAttributeValues'] = expression_attribute_values
            
            if expression_attribute_names:
                kwargs['ExpressionAttributeNames'] = expression_attribute_names
            
            if index_name:
                kwargs['IndexName'] = index_name
            
            if limit:
                kwargs['Limit'] = limit
            
            if exclusive_start_key:
                kwargs['ExclusiveStartKey'] = exclusive_start_key
            
            response = table.scan(**kwargs)
            
            logger.debug(f"Successfully scanned {len(response.get('Items', []))} items from {table_name}")
            return response
            
        except ClientError as e:
            logger.error(f"Error scanning items from {table_name}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error scanning items from {table_name}: {str(e)}")
            raise
    
    def batch_write_items(self, table_name: str, items: List[Dict[str, Any]], operation: str = 'put') -> Dict[str, Any]:
        """Batch write items to DynamoDB table"""[1]
        try:
            table = self.dynamodb.Table(table_name)
            
            # Process items in batches of 25 (DynamoDB limit)
            batch_size = 25
            results = {
                'processed_items': 0,
                'failed_items': [],
                'unprocessed_items': []
            }
            
            for i in range(0, len(items), batch_size):
                batch_items = items[i:i + batch_size]
                
                # Prepare batch request
                request_items = {table_name: []}
                
                for item in batch_items:
                    if operation == 'put':
                        # Add timestamps
                        if 'created_at' not in item:
                            item['created_at'] = datetime.now(timezone.utc).isoformat()
                        item['updated_at'] = datetime.now(timezone.utc).isoformat()
                        
                        request_items[table_name].append({
                            'PutRequest': {'Item': item}
                        })
                    elif operation == 'delete':
                        request_items[table_name].append({
                            'DeleteRequest': {'Key': item}
                        })
                
                # Execute batch write
                response = aws_clients.get_client('dynamodb').batch_write_item(
                    RequestItems=request_items
                )
                
                results['processed_items'] += len(batch_items)
                
                # Handle unprocessed items
                unprocessed = response.get('UnprocessedItems', {})
                if unprocessed:
                    results['unprocessed_items'].extend(unprocessed.get(table_name, []))
            
            logger.info(f"Batch write completed: {results['processed_items']} items processed")
            return results
            
        except ClientError as e:
            logger.error(f"Error in batch write to {table_name}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in batch write to {table_name}: {str(e)}")
            raise

# Global instance
db_manager = DatabaseManager()
