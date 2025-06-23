"""Standard API response codes and messages for HealthConnect AI"""

# HTTP Status Codes with Healthcare Context
HTTP_STATUS_CODES = {
    # Success Responses
    200: {
        'code': 'SUCCESS',
        'message': 'Request completed successfully',
        'category': 'success'
    },
    201: {
        'code': 'CREATED',
        'message': 'Resource created successfully',
        'category': 'success'
    },
    202: {
        'code': 'ACCEPTED',
        'message': 'Request accepted for processing',
        'category': 'success'
    },
    204: {
        'code': 'NO_CONTENT',
        'message': 'Request successful, no content to return',
        'category': 'success'
    },
    
    # Client Error Responses
    400: {
        'code': 'BAD_REQUEST',
        'message': 'Invalid request format or parameters',
        'category': 'client_error'
    },
    401: {
        'code': 'UNAUTHORIZED',
        'message': 'Authentication required',
        'category': 'client_error'
    },
    403: {
        'code': 'FORBIDDEN',
        'message': 'Access denied - insufficient permissions',
        'category': 'client_error'
    },
    404: {
        'code': 'NOT_FOUND',
        'message': 'Requested resource not found',
        'category': 'client_error'
    },
    409: {
        'code': 'CONFLICT',
        'message': 'Request conflicts with current state',
        'category': 'client_error'
    },
    422: {
        'code': 'UNPROCESSABLE_ENTITY',
        'message': 'Request format valid but content invalid',
        'category': 'client_error'
    },
    429: {
        'code': 'TOO_MANY_REQUESTS',
        'message': 'Rate limit exceeded',
        'category': 'client_error'
    },
    
    # Server Error Responses
    500: {
        'code': 'INTERNAL_SERVER_ERROR',
        'message': 'Internal server error occurred',
        'category': 'server_error'
    },
    502: {
        'code': 'BAD_GATEWAY',
        'message': 'Invalid response from upstream server',
        'category': 'server_error'
    },
    503: {
        'code': 'SERVICE_UNAVAILABLE',
        'message': 'Service temporarily unavailable',
        'category': 'server_error'
    },
    504: {
        'code': 'GATEWAY_TIMEOUT',
        'message': 'Upstream server timeout',
        'category': 'server_error'
    }
}

# Healthcare-Specific Error Codes
HEALTHCARE_ERROR_CODES = {
    'PATIENT_NOT_FOUND': {
        'http_status': 404,
        'code': 'HC001',
        'message': 'Patient record not found',
        'description': 'The specified patient ID does not exist in the system'
    },
    'INVALID_HEALTH_DATA': {
        'http_status': 422,
        'code': 'HC002',
        'message': 'Invalid health data format',
        'description': 'Health data does not meet validation requirements'
    },
    'DEVICE_NOT_REGISTERED': {
        'http_status': 404,
        'code': 'HC003',
        'message': 'Device not registered',
        'description': 'The specified device is not registered in the system'
    },
    'CONSULTATION_NOT_AVAILABLE': {
        'http_status': 503,
        'code': 'HC004',
        'message': 'Consultation service unavailable',
        'description': 'No healthcare providers available for consultation'
    },
    'EMERGENCY_ALERT_FAILED': {
        'http_status': 500,
        'code': 'HC005',
        'message': 'Emergency alert system failure',
        'description': 'Failed to process emergency alert'
    },
    'HIPAA_VIOLATION': {
        'http_status': 403,
        'code': 'HC006',
        'message': 'HIPAA compliance violation',
        'description': 'Request violates HIPAA privacy requirements'
    },
    'MEDICATION_INTERACTION': {
        'http_status': 422,
        'code': 'HC007',
        'message': 'Medication interaction detected',
        'description': 'Potential adverse drug interaction identified'
    },
    'VITAL_SIGNS_OUT_OF_RANGE': {
        'http_status': 422,
        'code': 'HC008',
        'message': 'Vital signs outside normal range',
        'description': 'Submitted vital signs exceed safe parameters'
    },
    'PROVIDER_UNAVAILABLE': {
        'http_status': 503,
        'code': 'HC009',
        'message': 'Healthcare provider unavailable',
        'description': 'Requested healthcare provider is not available'
    },
    'ANALYTICS_PROCESSING_ERROR': {
        'http_status': 500,
        'code': 'HC010',
        'message': 'Analytics processing failed',
        'description': 'Error occurred during health analytics processing'
    }
}

# Success Response Templates
SUCCESS_RESPONSES = {
    'HEALTH_DATA_SAVED': {
        'code': 'SUCCESS',
        'message': 'Health data saved successfully',
        'data_template': {
            'record_id': None,
            'patient_id': None,
            'timestamp': None,
            'data_type': None
        }
    },
    'CONSULTATION_CREATED': {
        'code': 'SUCCESS',
        'message': 'Consultation session created successfully',
        'data_template': {
            'session_id': None,
            'patient_id': None,
            'provider_id': None,
            'scheduled_time': None,
            'consultation_type': None
        }
    },
    'EMERGENCY_ALERT_SENT': {
        'code': 'SUCCESS',
        'message': 'Emergency alert sent successfully',
        'data_template': {
            'alert_id': None,
            'patient_id': None,
            'urgency_level': None,
            'notifications_sent': None,
            'response_time_seconds': None
        }
    },
    'ANALYTICS_COMPLETED': {
        'code': 'SUCCESS',
        'message': 'Analytics processing completed',
        'data_template': {
            'analysis_id': None,
            'analysis_type': None,
            'records_processed': None,
            'insights_generated': None,
            'completion_time': None
        }
    },
    'DEVICE_REGISTERED': {
        'code': 'SUCCESS',
        'message': 'Device registered successfully',
        'data_template': {
            'device_id': None,
            'device_type': None,
            'patient_id': None,
            'registration_time': None,
            'status': 'active'
        }
    }
}

# Validation Error Messages
VALIDATION_ERRORS = {
    'REQUIRED_FIELD_MISSING': 'Required field "{field}" is missing',
    'INVALID_FORMAT': 'Field "{field}" has invalid format',
    'VALUE_OUT_OF_RANGE': 'Field "{field}" value {value} is outside valid range ({min}-{max})',
    'INVALID_ENUM_VALUE': 'Field "{field}" must be one of: {valid_values}',
    'INVALID_DATE_FORMAT': 'Field "{field}" must be in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)',
    'INVALID_EMAIL_FORMAT': 'Field "{field}" must be a valid email address',
    'INVALID_PHONE_FORMAT': 'Field "{field}" must be a valid phone number',
    'STRING_TOO_LONG': 'Field "{field}" exceeds maximum length of {max_length} characters',
    'STRING_TOO_SHORT': 'Field "{field}" must be at least {min_length} characters',
    'INVALID_PATIENT_ID': 'Patient ID must be 8-32 alphanumeric characters',
    'INVALID_DEVICE_ID': 'Device ID must be 8-64 alphanumeric characters with hyphens/underscores'
}

# Rate Limiting Messages
RATE_LIMIT_MESSAGES = {
    'API_RATE_LIMIT': {
        'message': 'API rate limit exceeded',
        'description': 'Too many requests. Please wait before making another request.',
        'retry_after_seconds': 60
    },
    'CONSULTATION_RATE_LIMIT': {
        'message': 'Consultation request limit exceeded',
        'description': 'Maximum consultation requests per hour exceeded.',
        'retry_after_seconds': 3600
    },
    'EMERGENCY_ALERT_RATE_LIMIT': {
        'message': 'Emergency alert rate limit exceeded',
        'description': 'Too many emergency alerts. Please verify before sending more.',
        'retry_after_seconds': 300
    }
}

# WebSocket Response Codes
WEBSOCKET_RESPONSES = {
    'CONNECTION_ESTABLISHED': {
        'type': 'connection_status',
        'status': 'connected',
        'message': 'WebSocket connection established successfully'
    },
    'AUTHENTICATION_REQUIRED': {
        'type': 'error',
        'code': 'AUTH_REQUIRED',
        'message': 'Authentication required for WebSocket connection'
    },
    'INVALID_MESSAGE_FORMAT': {
        'type': 'error',
        'code': 'INVALID_FORMAT',
        'message': 'Invalid message format received'
    },
    'MESSAGE_DELIVERED': {
        'type': 'confirmation',
        'status': 'delivered',
        'message': 'Message delivered successfully'
    },
    'ROOM_JOINED': {
        'type': 'room_status',
        'status': 'joined',
        'message': 'Successfully joined room'
    },
    'ROOM_LEFT': {
        'type': 'room_status',
        'status': 'left',
        'message': 'Successfully left room'
    }
}

# Emergency Response Codes
EMERGENCY_RESPONSE_CODES = {
    'CRITICAL_ALERT': {
        'priority': 1,
        'response_time_seconds': 60,
        'escalation_required': True,
        'auto_call_ems': True
    },
    'HIGH_PRIORITY': {
        'priority': 2,
        'response_time_seconds': 180,
        'escalation_required': True,
        'auto_call_ems': False
    },
    'MEDIUM_PRIORITY': {
        'priority': 3,
        'response_time_seconds': 600,
        'escalation_required': False,
        'auto_call_ems': False
    },
    'LOW_PRIORITY': {
        'priority': 4,
        'response_time_seconds': 1800,
        'escalation_required': False,
        'auto_call_ems': False
    }
}

# Analytics Response Codes
ANALYTICS_RESPONSE_CODES = {
    'ANALYSIS_COMPLETE': {
        'code': 'ANALYTICS_001',
        'message': 'Analysis completed successfully',
        'status': 'completed'
    },
    'ANALYSIS_IN_PROGRESS': {
        'code': 'ANALYTICS_002',
        'message': 'Analysis is currently in progress',
        'status': 'processing'
    },
    'INSUFFICIENT_DATA': {
        'code': 'ANALYTICS_003',
        'message': 'Insufficient data for analysis',
        'status': 'failed'
    },
    'MODEL_TRAINING_COMPLETE': {
        'code': 'ANALYTICS_004',
        'message': 'Predictive model training completed',
        'status': 'completed'
    },
    'INSIGHTS_GENERATED': {
        'code': 'ANALYTICS_005',
        'message': 'Health insights generated successfully',
        'status': 'completed'
    }
}

# Device Status Response Codes
DEVICE_STATUS_RESPONSES = {
    'DEVICE_ONLINE': {
        'status': 'online',
        'message': 'Device is online and transmitting data',
        'last_seen': None
    },
    'DEVICE_OFFLINE': {
        'status': 'offline',
        'message': 'Device is offline or not responding',
        'last_seen': None
    },
    'DEVICE_LOW_BATTERY': {
        'status': 'low_battery',
        'message': 'Device battery level is low',
        'battery_level': None
    },
    'DEVICE_ERROR': {
        'status': 'error',
        'message': 'Device has encountered an error',
        'error_code': None
    },
    'DEVICE_MAINTENANCE': {
        'status': 'maintenance',
        'message': 'Device is in maintenance mode',
        'maintenance_type': None
    }
}
