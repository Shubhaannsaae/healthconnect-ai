"""Error handling utilities for HealthConnect AI"""

import logging
import traceback
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone
import json

logger = logging.getLogger(__name__)

class HealthConnectError(Exception):
    """Base exception class for HealthConnect AI"""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code or 'UNKNOWN_ERROR'
        self.details = details or {}
        self.timestamp = datetime.now(timezone.utc).isoformat()
        super().__init__(self.message)

class ValidationError(HealthConnectError):
    """Exception for data validation errors"""
    pass

class AuthenticationError(HealthConnectError):
    """Exception for authentication errors"""
    pass

class AuthorizationError(HealthConnectError):
    """Exception for authorization errors"""
    pass

class DeviceError(HealthConnectError):
    """Exception for device-related errors"""
    pass

class ConsultationError(HealthConnectError):
    """Exception for consultation-related errors"""
    pass

class EmergencyError(HealthConnectError):
    """Exception for emergency system errors"""
    pass

class AnalyticsError(HealthConnectError):
    """Exception for analytics processing errors"""
    pass

class ErrorHandler:
    """Production-grade error handler for HealthConnect AI"""
    
    def __init__(self):
        self.error_mappings = {
            # Validation errors
            ValidationError: {
                'http_status': 422,
                'error_category': 'validation_error',
                'user_message': 'The provided data is invalid. Please check your input and try again.'
            },
            
            # Authentication errors
            AuthenticationError: {
                'http_status': 401,
                'error_category': 'authentication_error',
                'user_message': 'Authentication failed. Please check your credentials.'
            },
            
            # Authorization errors
            AuthorizationError: {
                'http_status': 403,
                'error_category': 'authorization_error',
                'user_message': 'You do not have permission to access this resource.'
            },
            
            # Device errors
            DeviceError: {
                'http_status': 503,
                'error_category': 'device_error',
                'user_message': 'There was an issue with the medical device. Please check the device status.'
            },
            
            # Consultation errors
            ConsultationError: {
                'http_status': 503,
                'error_category': 'consultation_error',
                'user_message': 'The consultation service is currently unavailable. Please try again later.'
            },
            
            # Emergency errors
            EmergencyError: {
                'http_status': 500,
                'error_category': 'emergency_error',
                'user_message': 'There was an issue with the emergency response system. Please contact support immediately.'
            },
            
            # Analytics errors
            AnalyticsError: {
                'http_status': 500,
                'error_category': 'analytics_error',
                'user_message': 'Analytics processing failed. Please try again later.'
            }
        }
    
    def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle and format error for API response"""
        try:
            context = context or {}
            
            # Log the error
            self._log_error(error, context)
            
            # Determine error type and get mapping
            error_mapping = self._get_error_mapping(error)
            
            # Create error response
            error_response = {
                'error': True,
                'error_code': getattr(error, 'error_code', 'UNKNOWN_ERROR'),
                'error_category': error_mapping['error_category'],
                'message': error_mapping['user_message'],
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'request_id': context.get('request_id', 'unknown')
            }
            
            # Add technical details in development mode
            if context.get('environment') == 'development':
                error_response['technical_details'] = {
                    'exception_type': type(error).__name__,
                    'exception_message': str(error),
                    'details': getattr(error, 'details', {}),
                    'traceback': traceback.format_exc()
                }
            
            # Add HTTP status code
            error_response['http_status'] = error_mapping['http_status']
            
            return error_response
            
        except Exception as e:
            # Fallback error handling
            logger.error(f"Error in error handler: {str(e)}")
            return self._create_fallback_error_response(error)
    
    def handle_lambda_error(self, error: Exception, event: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle errors specifically for Lambda functions"""
        try:
            context = {
                'environment': 'production',  # Assume production unless specified
                'request_id': event.get('requestContext', {}).get('requestId', 'unknown') if event else 'unknown',
                'function_name': event.get('requestContext', {}).get('functionName') if event else 'unknown'
            }
            
            error_response = self.handle_error(error, context)
            
            # Format for Lambda response
            lambda_response = {
                'statusCode': error_response['http_status'],
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                },
                'body': json.dumps({
                    'error': error_response['error'],
                    'error_code': error_response['error_code'],
                    'message': error_response['message'],
                    'timestamp': error_response['timestamp'],
                    'request_id': error_response['request_id']
                })
            }
            
            return lambda_response
            
        except Exception as e:
            logger.error(f"Error in Lambda error handler: {str(e)}")
            return self._create_fallback_lambda_response()
    
    def handle_websocket_error(self, error: Exception, connection_id: str = None) -> Dict[str, Any]:
        """Handle errors for WebSocket connections"""
        try:
            context = {
                'environment': 'production',
                'connection_id': connection_id or 'unknown',
                'protocol': 'websocket'
            }
            
            error_response = self.handle_error(error, context)
            
            # Format for WebSocket response
            websocket_response = {
                'type': 'error',
                'error_code': error_response['error_code'],
                'message': error_response['message'],
                'timestamp': error_response['timestamp'],
                'connection_id': connection_id
            }
            
            return websocket_response
            
        except Exception as e:
            logger.error(f"Error in WebSocket error handler: {str(e)}")
            return {
                'type': 'error',
                'error_code': 'WEBSOCKET_ERROR',
                'message': 'An unexpected error occurred',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def create_validation_error(self, validation_errors: List[str], field: str = None) -> ValidationError:
        """Create a validation error with details"""
        if field:
            message = f"Validation failed for field '{field}': {'; '.join(validation_errors)}"
        else:
            message = f"Validation failed: {'; '.join(validation_errors)}"
        
        details = {
            'validation_errors': validation_errors,
            'field': field
        }
        
        return ValidationError(message, 'VALIDATION_FAILED', details)
    
    def create_device_error(self, device_id: str, error_type: str, details: Dict[str, Any] = None) -> DeviceError:
        """Create a device-specific error"""
        message = f"Device {device_id} error: {error_type}"
        
        error_details = {
            'device_id': device_id,
            'error_type': error_type,
            **(details or {})
        }
        
        return DeviceError(message, f'DEVICE_{error_type.upper()}', error_details)
    
    def create_consultation_error(self, session_id: str, error_type: str, details: Dict[str, Any] = None) -> ConsultationError:
        """Create a consultation-specific error"""
        message = f"Consultation {session_id} error: {error_type}"
        
        error_details = {
            'session_id': session_id,
            'error_type': error_type,
            **(details or {})
        }
        
        return ConsultationError(message, f'CONSULTATION_{error_type.upper()}', error_details)
    
    def create_emergency_error(self, alert_id: str, error_type: str, details: Dict[str, Any] = None) -> EmergencyError:
        """Create an emergency-specific error"""
        message = f"Emergency alert {alert_id} error: {error_type}"
        
        error_details = {
            'alert_id': alert_id,
            'error_type': error_type,
            **(details or {})
        }
        
        return EmergencyError(message, f'EMERGENCY_{error_type.upper()}', error_details)
    
    def _get_error_mapping(self, error: Exception) -> Dict[str, Any]:
        """Get error mapping for exception type"""
        error_type = type(error)
        
        # Check for specific error type mapping
        if error_type in self.error_mappings:
            return self.error_mappings[error_type]
        
        # Check for parent class mappings
        for mapped_type, mapping in self.error_mappings.items():
            if isinstance(error, mapped_type):
                return mapping
        
        # Default mapping for unknown errors
        return {
            'http_status': 500,
            'error_category': 'internal_error',
            'user_message': 'An unexpected error occurred. Please try again later.'
        }
    
    def _log_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """Log error with context"""
        try:
            log_data = {
                'error_type': type(error).__name__,
                'error_message': str(error),
                'error_code': getattr(error, 'error_code', 'UNKNOWN'),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'context': context,
                'traceback': traceback.format_exc()
            }
            
            # Log as JSON for structured logging
            logger.error(json.dumps(log_data, indent=2))
            
        except Exception as e:
            # Fallback logging
            logger.error(f"Error logging failed: {str(e)}")
            logger.error(f"Original error: {str(error)}")
    
    def _create_fallback_error_response(self, error: Exception) -> Dict[str, Any]:
        """Create fallback error response when error handling fails"""
        return {
            'error': True,
            'error_code': 'INTERNAL_ERROR',
            'error_category': 'internal_error',
            'message': 'An unexpected error occurred. Please try again later.',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'request_id': 'unknown',
            'http_status': 500
        }
    
    def _create_fallback_lambda_response(self) -> Dict[str, Any]:
        """Create fallback Lambda response when error handling fails"""
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': True,
                'error_code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred. Please try again later.',
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }

# Global instance
error_handler = ErrorHandler()

# Convenience functions
def handle_error(error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Global error handling function"""
    return error_handler.handle_error(error, context)

def handle_lambda_error(error: Exception, event: Dict[str, Any] = None) -> Dict[str, Any]:
    """Global Lambda error handling function"""
    return error_handler.handle_lambda_error(error, event)

def handle_websocket_error(error: Exception, connection_id: str = None) -> Dict[str, Any]:
    """Global WebSocket error handling function"""
    return error_handler.handle_websocket_error(error, connection_id)
