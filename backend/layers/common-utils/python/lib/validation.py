import re
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone
import json
from email_validator import validate_email, EmailNotValidError
import phonenumbers
from phonenumbers import NumberParseException

logger = logging.getLogger(__name__)

class ValidationManager:
    """Production-grade validation manager for healthcare data"""[1]
    
    def __init__(self):
        # Medical data validation patterns
        self.patterns = {
            'patient_id': r'^[A-Za-z0-9]{8,32}$',
            'device_id': r'^[A-Za-z0-9_-]{8,64}$',
            'session_id': r'^[A-Za-z0-9_-]{8,64}$',
            'phone_number': r'^\+?[1-9]\d{1,14}$',
            'postal_code': r'^[A-Za-z0-9\s-]{3,10}$',
            'medication_code': r'^[A-Za-z0-9]{4,20}$',
            'icd_code': r'^[A-Z]\d{2}(\.\d{1,2})?$'
        }
        
        # Health data ranges
        self.health_ranges = {
            'heart_rate': {'min': 30, 'max': 250},
            'systolic_pressure': {'min': 60, 'max': 300},
            'diastolic_pressure': {'min': 30, 'max': 200},
            'temperature': {'min': 30.0, 'max': 45.0},
            'oxygen_saturation': {'min': 70, 'max': 100},
            'respiratory_rate': {'min': 5, 'max': 60},
            'glucose_level': {'min': 20, 'max': 800},
            'bmi': {'min': 10.0, 'max': 80.0},
            'age': {'min': 0, 'max': 150}
        }
    
    def validate_patient_data(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate patient data comprehensively"""[1]
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'sanitized_data': {}
        }
        
        try:
            # Required fields validation
            required_fields = ['patient_id']
            for field in required_fields:
                if field not in patient_data or not patient_data[field]:
                    validation_result['errors'].append(f"Missing required field: {field}")
                    validation_result['valid'] = False
            
            # Validate patient ID
            if 'patient_id' in patient_data:
                patient_id_result = self.validate_patient_id(patient_data['patient_id'])
                if not patient_id_result['valid']:
                    validation_result['errors'].extend(patient_id_result['errors'])
                    validation_result['valid'] = False
                else:
                    validation_result['sanitized_data']['patient_id'] = patient_id_result['sanitized_value']
            
            # Validate email if present
            if 'email' in patient_data and patient_data['email']:
                email_result = self.validate_email_address(patient_data['email'])
                if not email_result['valid']:
                    validation_result['errors'].extend(email_result['errors'])
                    validation_result['valid'] = False
                else:
                    validation_result['sanitized_data']['email'] = email_result['sanitized_value']
            
            # Validate phone number if present
            if 'phone' in patient_data and patient_data['phone']:
                phone_result = self.validate_phone_number(patient_data['phone'])
                if not phone_result['valid']:
                    validation_result['errors'].extend(phone_result['errors'])
                    validation_result['valid'] = False
                else:
                    validation_result['sanitized_data']['phone'] = phone_result['sanitized_value']
            
            # Validate age if present
            if 'age' in patient_data:
                age_result = self.validate_health_metric('age', patient_data['age'])
                if not age_result['valid']:
                    validation_result['errors'].extend(age_result['errors'])
                    validation_result['valid'] = False
                else:
                    validation_result['sanitized_data']['age'] = age_result['sanitized_value']
            
            # Validate date of birth if present
            if 'date_of_birth' in patient_data and patient_data['date_of_birth']:
                dob_result = self.validate_date(patient_data['date_of_birth'])
                if not dob_result['valid']:
                    validation_result['errors'].extend(dob_result['errors'])
                    validation_result['valid'] = False
                else:
                    validation_result['sanitized_data']['date_of_birth'] = dob_result['sanitized_value']
            
            # Copy other valid fields
            for key, value in patient_data.items():
                if key not in validation_result['sanitized_data'] and value is not None:
                    validation_result['sanitized_data'][key] = value
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating patient data: {str(e)}")
            return {
                'valid': False,
                'errors': [f"Validation error: {str(e)}"],
                'warnings': [],
                'sanitized_data': {}
            }
    
    def validate_health_data(self, health_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate health/vital signs data"""[1]
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'sanitized_data': {}
        }
        
        try:
            # Validate individual health metrics
            for metric, value in health_data.items():
                if metric in self.health_ranges:
                    metric_result = self.validate_health_metric(metric, value)
                    
                    if not metric_result['valid']:
                        validation_result['errors'].extend(metric_result['errors'])
                        validation_result['valid'] = False
                    else:
                        validation_result['sanitized_data'][metric] = metric_result['sanitized_value']
                        
                        # Add warnings for borderline values
                        if metric_result.get('warnings'):
                            validation_result['warnings'].extend(metric_result['warnings'])
                else:
                    # Unknown metric - pass through with warning
                    validation_result['warnings'].append(f"Unknown health metric: {metric}")
                    validation_result['sanitized_data'][metric] = value
            
            # Validate blood pressure combination
            if 'systolic_pressure' in health_data and 'diastolic_pressure' in health_data:
                bp_result = self.validate_blood_pressure(
                    health_data['systolic_pressure'],
                    health_data['diastolic_pressure']
                )
                if not bp_result['valid']:
                    validation_result['errors'].extend(bp_result['errors'])
                    validation_result['valid'] = False
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating health data: {str(e)}")
            return {
                'valid': False,
                'errors': [f"Health data validation error: {str(e)}"],
                'warnings': [],
                'sanitized_data': {}
            }
    
    def validate_patient_id(self, patient_id: Any) -> Dict[str, Any]:
        """Validate patient ID format"""[1]
        try:
            if not isinstance(patient_id, str):
                return {
                    'valid': False,
                    'errors': ['Patient ID must be a string'],
                    'sanitized_value': None
                }
            
            # Remove whitespace
            sanitized_id = patient_id.strip()
            
            if not re.match(self.patterns['patient_id'], sanitized_id):
                return {
                    'valid': False,
                    'errors': ['Patient ID format invalid (8-32 alphanumeric characters)'],
                    'sanitized_value': None
                }
            
            return {
                'valid': True,
                'errors': [],
                'sanitized_value': sanitized_id
            }
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"Patient ID validation error: {str(e)}"],
                'sanitized_value': None
            }
    
    def validate_email_address(self, email: str) -> Dict[str, Any]:
        """Validate email address format"""[1]
        try:
            # Use email-validator library
            validated_email = validate_email(email)
            
            return {
                'valid': True,
                'errors': [],
                'sanitized_value': validated_email.email
            }
            
        except EmailNotValidError as e:
            return {
                'valid': False,
                'errors': [f"Invalid email format: {str(e)}"],
                'sanitized_value': None
            }
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"Email validation error: {str(e)}"],
                'sanitized_value': None
            }
    
    def validate_phone_number(self, phone: str, region: str = 'US') -> Dict[str, Any]:
        """Validate phone number format"""[1]
        try:
            # Parse phone number
            parsed_number = phonenumbers.parse(phone, region)
            
            # Validate phone number
            if not phonenumbers.is_valid_number(parsed_number):
                return {
                    'valid': False,
                    'errors': ['Invalid phone number'],
                    'sanitized_value': None
                }
            
            # Format phone number
            formatted_number = phonenumbers.format_number(
                parsed_number, 
                phonenumbers.PhoneNumberFormat.E164
            )
            
            return {
                'valid': True,
                'errors': [],
                'sanitized_value': formatted_number
            }
            
        except NumberParseException as e:
            return {
                'valid': False,
                'errors': [f"Phone number parse error: {str(e)}"],
                'sanitized_value': None
            }
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"Phone validation error: {str(e)}"],
                'sanitized_value': None
            }
    
    def validate_health_metric(self, metric_name: str, value: Any) -> Dict[str, Any]:
        """Validate individual health metric"""[1]
        try:
            if metric_name not in self.health_ranges:
                return {
                    'valid': True,
                    'errors': [],
                    'warnings': [f"Unknown health metric: {metric_name}"],
                    'sanitized_value': value
                }
            
            # Convert to appropriate type
            try:
                if metric_name in ['temperature', 'bmi']:
                    numeric_value = float(value)
                else:
                    numeric_value = int(float(value))
            except (ValueError, TypeError):
                return {
                    'valid': False,
                    'errors': [f"{metric_name} must be numeric"],
                    'sanitized_value': None
                }
            
            # Check range
            range_info = self.health_ranges[metric_name]
            min_val = range_info['min']
            max_val = range_info['max']
            
            warnings = []
            
            if numeric_value < min_val:
                return {
                    'valid': False,
                    'errors': [f"{metric_name} value {numeric_value} below minimum {min_val}"],
                    'sanitized_value': None
                }
            elif numeric_value > max_val:
                return {
                    'valid': False,
                    'errors': [f"{metric_name} value {numeric_value} above maximum {max_val}"],
                    'sanitized_value': None
                }
            
            # Check for borderline values (warning thresholds)
            warning_thresholds = self._get_warning_thresholds(metric_name)
            if warning_thresholds:
                if (numeric_value < warning_thresholds['low'] or 
                    numeric_value > warning_thresholds['high']):
                    warnings.append(f"{metric_name} value {numeric_value} is outside normal range")
            
            return {
                'valid': True,
                'errors': [],
                'warnings': warnings,
                'sanitized_value': numeric_value
            }
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"Health metric validation error: {str(e)}"],
                'sanitized_value': None
            }
    
    def validate_blood_pressure(self, systolic: Any, diastolic: Any) -> Dict[str, Any]:
        """Validate blood pressure combination"""[1]
        try:
            # Convert to numeric
            try:
                sys_val = int(float(systolic))
                dia_val = int(float(diastolic))
            except (ValueError, TypeError):
                return {
                    'valid': False,
                    'errors': ['Blood pressure values must be numeric']
                }
            
            # Systolic should be higher than diastolic
            if sys_val <= dia_val:
                return {
                    'valid': False,
                    'errors': ['Systolic pressure must be higher than diastolic pressure']
                }
            
            # Check pulse pressure (difference)
            pulse_pressure = sys_val - dia_val
            if pulse_pressure < 20:
                return {
                    'valid': False,
                    'errors': ['Pulse pressure too low (systolic - diastolic < 20)']
                }
            elif pulse_pressure > 100:
                return {
                    'valid': False,
                    'errors': ['Pulse pressure too high (systolic - diastolic > 100)']
                }
            
            return {
                'valid': True,
                'errors': []
            }
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"Blood pressure validation error: {str(e)}"]
            }
    
    def validate_date(self, date_value: Any, date_format: str = '%Y-%m-%d') -> Dict[str, Any]:
        """Validate date format and value"""[1]
        try:
            if isinstance(date_value, str):
                # Try to parse the date
                try:
                    parsed_date = datetime.strptime(date_value, date_format)
                    
                    # Check if date is reasonable (not in future, not too old)
                    current_date = datetime.now()
                    if parsed_date > current_date:
                        return {
                            'valid': False,
                            'errors': ['Date cannot be in the future'],
                            'sanitized_value': None
                        }
                    
                    # Check if date is not too old (e.g., before 1900)
                    if parsed_date.year < 1900:
                        return {
                            'valid': False,
                            'errors': ['Date is too old (before 1900)'],
                            'sanitized_value': None
                        }
                    
                    return {
                        'valid': True,
                        'errors': [],
                        'sanitized_value': parsed_date.strftime(date_format)
                    }
                    
                except ValueError:
                    return {
                        'valid': False,
                        'errors': [f'Invalid date format (expected {date_format})'],
                        'sanitized_value': None
                    }
            else:
                return {
                    'valid': False,
                    'errors': ['Date must be a string'],
                    'sanitized_value': None
                }
                
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"Date validation error: {str(e)}"],
                'sanitized_value': None
            }
    
    def _get_warning_thresholds(self, metric_name: str) -> Optional[Dict[str, float]]:
        """Get warning thresholds for health metrics"""[1]
        warning_thresholds = {
            'heart_rate': {'low': 60, 'high': 100},
            'systolic_pressure': {'low': 90, 'high': 140},
            'diastolic_pressure': {'low': 60, 'high': 90},
            'temperature': {'low': 36.1, 'high': 37.2},
            'oxygen_saturation': {'low': 95, 'high': 100},
            'respiratory_rate': {'low': 12, 'high': 20},
            'glucose_level': {'low': 70, 'high': 140},
            'bmi': {'low': 18.5, 'high': 25.0}
        }
        
        return warning_thresholds.get(metric_name)

# Global instance
validation_manager = ValidationManager()
