import boto3
import logging
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError, NoCredentialsError
import os
from functools import lru_cache

logger = logging.getLogger(__name__)

class AWSClientManager:
    """Production-grade AWS client manager with connection pooling and error handling"""[1]
    
    def __init__(self):
        self.region = os.environ.get('AWS_REGION', 'us-east-1')
        self._clients = {}
        self._resources = {}
    
    @lru_cache(maxsize=32)
    def get_client(self, service_name: str, region: Optional[str] = None) -> boto3.client:
        """Get AWS service client with caching"""[1]
        try:
            client_key = f"{service_name}_{region or self.region}"
            
            if client_key not in self._clients:
                config = boto3.session.Config(
                    region_name=region or self.region,
                    retries={
                        'max_attempts': 3,
                        'mode': 'adaptive'
                    },
                    max_pool_connections=50
                )
                
                self._clients[client_key] = boto3.client(
                    service_name,
                    config=config
                )
                
                logger.debug(f"Created {service_name} client for region {region or self.region}")
            
            return self._clients[client_key]
            
        except NoCredentialsError:
            logger.error(f"No AWS credentials found for {service_name}")
            raise
        except Exception as e:
            logger.error(f"Error creating {service_name} client: {str(e)}")
            raise
    
    @lru_cache(maxsize=32)
    def get_resource(self, service_name: str, region: Optional[str] = None) -> boto3.resource:
        """Get AWS service resource with caching"""[1]
        try:
            resource_key = f"{service_name}_{region or self.region}"
            
            if resource_key not in self._resources:
                config = boto3.session.Config(
                    region_name=region or self.region,
                    retries={
                        'max_attempts': 3,
                        'mode': 'adaptive'
                    }
                )
                
                self._resources[resource_key] = boto3.resource(
                    service_name,
                    config=config
                )
                
                logger.debug(f"Created {service_name} resource for region {region or self.region}")
            
            return self._resources[resource_key]
            
        except NoCredentialsError:
            logger.error(f"No AWS credentials found for {service_name}")
            raise
        except Exception as e:
            logger.error(f"Error creating {service_name} resource: {str(e)}")
            raise
    
    def get_dynamodb_table(self, table_name: str, region: Optional[str] = None):
        """Get DynamoDB table resource"""[1]
        try:
            dynamodb = self.get_resource('dynamodb', region)
            return dynamodb.Table(table_name)
        except Exception as e:
            logger.error(f"Error getting DynamoDB table {table_name}: {str(e)}")
            raise
    
    def execute_with_retry(self, func, max_retries: int = 3, **kwargs) -> Any:
        """Execute function with exponential backoff retry"""[1]
        import time
        import random
        
        for attempt in range(max_retries):
            try:
                return func(**kwargs)
            except ClientError as e:
                error_code = e.response['Error']['Code']
                
                # Don't retry on certain errors
                if error_code in ['ValidationException', 'ResourceNotFoundException']:
                    raise
                
                if attempt == max_retries - 1:
                    raise
                
                # Exponential backoff with jitter
                delay = (2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay:.2f}s: {str(e)}")
                time.sleep(delay)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                
                delay = (2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay:.2f}s: {str(e)}")
                time.sleep(delay)

# Global instance
aws_clients = AWSClientManager()
