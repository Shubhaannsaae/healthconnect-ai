"""Comprehensive validation utilities for HealthConnect AI"""

import re
import logging
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime, timezone
import json
from email_validator import validate_email, EmailNotValidError
import phonenumbers
from phonenumbers import NumberParseException

logger = logging.getLogger(__name__)

class HealthDataValidator:
    """Production-grade validator for healthcare data"""
    
    def __init__(self):
        # Validation patterns
        self.patterns = {
            'patient_id': r'^[A-Za-z0-9]{8,32}$',
            'device_id': r'^[A-Za-z0-9_-]{8,64}$',
            'session_id': r'^[A-Za-z0-9_-]{8,64}$',
            'alert_id': r'^[A-Za-z0-9_-]{8,64}$',
            'provider_id': r'^[A-Za-z0-9]{8,32}$',
            'icd10_code': r'^[A-Z]\d{2}(\.\d{1,2})?$',
            'cpt_code': r'^\d{5}$',
            'ndc_code': r'^\d{4,5}-\d{3,4}-\d{1,2}$'
        }
        
        # Health data ranges
        self.health_ranges = {
            'heart_rate': {'min': 30, 'max': 250, 'unit': 'bpm'},
            'systolic_pressure': {'min': 60, 'max': 300, 'unit': 'mmHg'},
            'diastolic_pressure': {'min': 30, 'max': 200, 'unit': 'mmHg'},
            'temperature': {'min': 30.0, 'max': 45.0, 'unit': '°C'},
            'oxygen_saturation': {'min': 70, 'max': 100, 'unit': '%'},
            'respiratory_rate': {'min': 5, 'max': 60, 'unit': 'breaths/min'},
            'glucose_level': {'min': 20, 'max': 800, 'unit': 'mg/dL'},
            'bmi': {'min': 10.0, 'max': 80.0, 'unit': 'kg/m²'},
            'age': {'min': 0, 'max': 150, 'unit': 'years'},
            'weight': {'min': 0.5, 'max': 500, 'unit': 'kg'},
            'height': {'min': 30, 'max': 250, 'unit': 'cm'}
        }
        
        # Valid enum values
        self.valid_enums = {
            'gender': ['male', 'female', 'other', 'unknown'],
            'urgency_level': ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'],
            'consultation_type': ['emergency', 'urgent', 'routine', 'follow_up', 'mental_health', 'specialist'],
            'device_type': [
                'heart_rate_monitor', 'blood_pressure_cuff', 'glucose_meter',
                'temperature_sensor', 'pulse_oximeter', 'activity_tracker',
                'ecg_monitor', 'respiratory_monitor'
            ],
            'data_type': ['vital_signs', 'symptoms', 'diagnosis', 'medication', 'lab_results', 'imaging'],
            'severity': ['mild', 'moderate', 'severe', 'critical'],
            'medication_route': ['oral', 'intravenous', 'intramuscular', 'subcutaneous', 'topical', 'inhalation']
        }
    
    def validate_health_record(self, health_record: Dict[str, Any]) -> Dict[str, Any]:
        """Validate complete health record"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'sanitized_data': {}
        }
        
        try:
            # Required fields validation
            required_fields = ['patient_id', 'timestamp', 'data_type']
            for field in required_fields:
                if field not in health_record or health_record[field] is None:
                    validation_result['errors'].append(f"Missing required field: {field}")
                    validation_result['valid'] = False
            
            # Validate patient ID
            if 'patient_id' in health_record:
                patient_id_result = self.validate_identifier('patient_id', health_record['patient_id'])
                if not patient_id_result['valid']:
                    validation_result['errors'].extend(patient_id_result['errors'])
                    validation_result['valid'] = False
                else:
                    validation_result['sanitized_data']['patient_id'] = patient_id_result['value']
            
            # Validate timestamp
            if 'timestamp' in health_record:
                timestamp_result = self.validate_timestamp(health_record['timestamp'])
                if not timestamp_result['valid']:
                    validation_result['errors'].extend(timestamp_result['errors'])
                    validation_result['valid'] = False
                else:
                    validation_result['sanitized_data']['timestamp'] = timestamp_result['value']
            
            # Validate data type
            if 'data_type' in health_record:
                data_type_result = self.validate_enum('data_type', health_record['data_type'])
                if not data_type_result['valid']:
                    validation_result['errors'].extend(data_type_result['errors'])
                    validation_result['valid'] = False
                else:
                    validation_result['sanitized_data']['data_type'] = data_type_result['value']
            
            # Validate vital signs if present
            if 'vital_signs' in health_record and health_record['vital_signs']:
                vital_signs_result = self.validate_vital_signs(health_record['vital_signs'])
                if not vital_signs_result['valid']:
                    validation_result['errors'].extend(vital_signs_result['errors'])
                    validation_result['valid'] = False
                else:
                    validation_result['sanitized_data']['vital_signs'] = vital_signs_result['sanitized_data']
                validation_result['warnings'].extend(vital_signs_result['warnings'])
            
            # Validate symptoms if present
            if 'symptoms' in health_record and health_record['symptoms']:
                symptoms_result = self.validate_symptoms(health_record['symptoms'])
                if not symptoms_result['valid']:
                    validation_result['errors'].extend(symptoms_result['errors'])
                    validation_result['valid'] = False
                else:
                    validation_result['sanitized_data']['symptoms'] = symptoms_result['sanitized_data']
            
            # Validate medications if present
            if 'medications' in health_record and health_record['medications']:
                medications_result = self.validate_medications(health_record['medications'])
                if not medications_result['valid']:
                    validation_result['errors'].extend(medications_result['errors'])
                    validation_result['valid'] = False
                else:
                    validation_result['sanitized_data']['medications'] = medications_result['sanitized_data']
            
            # Copy other valid fields
            for key, value in health_record.items():
                if key not in validation_result['sanitized_data'] and value is not None:
                    validation_result['sanitized_data'][key] = value
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating health record: {str(e)}")
            return {
                'valid': False,
                'errors': [f"Validation error: {str(e)}"],
                'warnings': [],
                'sanitized_data': {}
            }
    
    def validate_vital_signs(self, vital_signs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate vital signs data"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'sanitized_data': {}
        }
        
        try:
            for metric, value in vital_signs.items():
                if metric == 'blood_pressure' and isinstance(value, dict):
                    # Special handling for blood pressure
                    bp_result = self.validate_blood_pressure(value)
                    if not bp_result['valid']:
                        validation_result['errors'].extend(bp_result['errors'])
                        validation_result['valid'] = False
                    else:
                        validation_result['sanitized_data']['blood_pressure'] = bp_result['sanitized_data']
                    validation_result['warnings'].extend(bp_result['warnings'])
                    
                elif metric in self.health_ranges:
                    # Validate individual vital sign
                    metric_result = self.validate_numeric_range(metric, value, self.health_ranges[metric])
                    if not metric_result['valid']:
                        validation_result['errors'].extend(metric_result['errors'])
                        validation_result['valid'] = False
                    else:
                        validation_result['sanitized_data'][metric] = metric_result['value']
                    validation_result['warnings'].extend(metric_result['warnings'])
                else:
                    # Unknown metric - pass through with warning
                    validation_result['warnings'].append(f"Unknown vital sign metric: {metric}")
                    validation_result['sanitized_data'][metric] = value
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating vital signs: {str(e)}")
            return {
                'valid': False,
                'errors': [f"Vital signs validation error: {str(e)}"],
                'warnings': [],
                'sanitized_data': {}
            }
    
    def validate_blood_pressure(self, bp_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate blood pressure data"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'sanitized_data': {}
        }
        
        try:
            # Required fields
            if 'systolic' not in bp_data or 'diastolic' not in bp_data:
                validation_result['errors'].append("Blood pressure must include both systolic and diastolic values")
                validation_result['valid'] = False
                return validation_result
            
            # Validate systolic
            systolic_result = self.validate_numeric_range(
                'systolic_pressure', bp_data['systolic'], self.health_ranges['systolic_pressure']
            )
            if not systolic_result['valid']:
                validation_result['errors'].extend(systolic_result['errors'])
                validation_result['valid'] = False
            else:
                validation_result['sanitized_data']['systolic'] = systolic_result['value']
            
            # Validate diastolic
            diastolic_result = self.validate_numeric_range(
                'diastolic_pressure', bp_data['diastolic'], self.health_ranges['diastolic_pressure']
            )
            if not diastolic_result['valid']:
                validation_result['errors'].extend(diastolic_result['errors'])
                validation_result['valid'] = False
            else:
                validation_result['sanitized_data']['diastolic'] = diastolic_result['value']
            
            # Validate relationship between systolic and diastolic
            if validation_result['valid']:
                systolic = validation_result['sanitized_data']['systolic']
                diastolic = validation_result['sanitized_data']['diastolic']
                
                if systolic <= diastolic:
                    validation_result['errors'].append("Systolic pressure must be higher than diastolic pressure")
                    validation_result['valid'] = False
                
                pulse_pressure = systolic - diastolic
                if pulse_pressure < 20:
                    validation_result['warnings'].append("Pulse pressure is unusually low")
                elif pulse_pressure > 100:
                    validation_result['warnings'].append("Pulse pressure is unusually high")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating blood pressure: {str(e)}")
            return {
                'valid': False,
                'errors': [f"Blood pressure validation error: {str(e)}"],
                'warnings': [],
                'sanitized_data': {}
            }
    
    def validate_symptoms(self, symptoms: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate symptoms array"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'sanitized_data': []
        }
        
        try:
            if not isinstance(symptoms, list):
                validation_result['errors'].append("Symptoms must be an array")
                validation_result['valid'] = False
                return validation_result
            
            for i, symptom in enumerate(symptoms):
                if not isinstance(symptom, dict):
                    validation_result['errors'].append(f"Symptom {i} must be an object")
                    validation_result['valid'] = False
                    continue
                
                sanitized_symptom = {}
                
                # Required fields
                if 'symptom' not in symptom or not symptom['symptom']:
                    validation_result['errors'].append(f"Symptom {i} missing required 'symptom' field")
                    validation_result['valid'] = False
                    continue
                else:
                    sanitized_symptom['symptom'] = str(symptom['symptom']).strip()
                
                if 'severity' not in symptom:
                    validation_result['errors'].append(f"Symptom {i} missing required 'severity' field")
                    validation_result['valid'] = False
                    continue
                else:
                    severity_result = self.validate_enum('severity', symptom['severity'])
                    if not severity_result['valid']:
                        validation_result['errors'].append(f"Symptom {i} has invalid severity")
                        validation_result['valid'] = False
                        continue
                    else:
                        sanitized_symptom['severity'] = severity_result['value']
                
                # Optional fields
                if 'duration' in symptom and symptom['duration']:
                    sanitized_symptom['duration'] = str(symptom['duration']).strip()
                
                if 'onset' in symptom and symptom['onset']:
                    onset_result = self.validate_timestamp(symptom['onset'])
                    if onset_result['valid']:
                        sanitized_symptom['onset'] = onset_result['value']
                    else:
                        validation_result['warnings'].append(f"Symptom {i} has invalid onset timestamp")
                
                validation_result['sanitized_data'].append(sanitized_symptom)
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating symptoms: {str(e)}")
            return {
                'valid': False,
                'errors': [f"Symptoms validation error: {str(e)}"],
                'warnings': [],
                'sanitized_data': []
            }
    
    def validate_medications(self, medications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate medications array"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'sanitized_data': []
        }
        
        try:
            if not isinstance(medications, list):
                validation_result['errors'].append("Medications must be an array")
                validation_result['valid'] = False
                return validation_result
            
            for i, medication in enumerate(medications):
                if not isinstance(medication, dict):
                    validation_result['errors'].append(f"Medication {i} must be an object")
                    validation_result['valid'] = False
                    continue
                
                sanitized_medication = {}
                
                # Required fields
                required_fields = ['medication_name', 'dosage', 'frequency']
                for field in required_fields:
                    if field not in medication or not medication[field]:
                        validation_result['errors'].append(f"Medication {i} missing required '{field}' field")
                        validation_result['valid'] = False
                        break
                    else:
                        sanitized_medication[field] = str(medication[field]).strip()
                
                if not validation_result['valid']:
                    continue
                
                # Optional route validation
                if 'route' in medication and medication['route']:
                    route_result = self.validate_enum('medication_route', medication['route'])
                    if route_result['valid']:
                        sanitized_medication['route'] = route_result['value']
                    else:
                        validation_result['warnings'].append(f"Medication {i} has invalid route")
                
                # Optional date validations
                for date_field in ['start_date', 'end_date']:
                    if date_field in medication and medication[date_field]:
                        date_result = self.validate_date(medication[date_field])
                        if date_result['valid']:
                            sanitized_medication[date_field] = date_result['value']
                        else:
                            validation_result['warnings'].append(f"Medication {i} has invalid {date_field}")
                
                validation_result['sanitized_data'].append(sanitized_medication)
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating medications: {str(e)}")
            return {
                'valid': False,
                'errors': [f"Medications validation error: {str(e)}"],
                'warnings': [],
                'sanitized_data': []
            }
    
    def validate_identifier(self, id_type: str, value: Any) -> Dict[str, Any]:
        """Validate identifier format"""
        try:
            if not isinstance(value, str):
                return {
                    'valid': False,
                    'errors': [f"{id_type} must be a string"],
                    'value': None
                }
            
            sanitized_value = value.strip()
            
            if id_type not in self.patterns:
                return {
                    'valid': False,
                    'errors': [f"Unknown identifier type: {id_type}"],
                    'value': None
                }
            
            if not re.match(self.patterns[id_type], sanitized_value):
                return {
                    'valid': False,
                    'errors': [f"Invalid {id_type} format"],
                    'value': None
                }
            
            return {
                'valid': True,
                'errors': [],
                'value': sanitized_value
            }
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"{id_type} validation error: {str(e)}"],
                'value': None
            }
    
    def validate_numeric_range(self, field_name: str, value: Any, range_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate numeric value within range"""
        try:
            # Convert to appropriate numeric type
            try:
                if field_name in ['temperature', 'bmi', 'weight', 'height']:
                    numeric_value = float(value)
                else:
                    numeric_value = int(float(value))
            except (ValueError, TypeError):
                return {
                    'valid': False,
                    'errors': [f"{field_name} must be numeric"],
                    'warnings': [],
                    'value': None
                }
            
            # Check range
            min_val = range_config['min']
            max_val = range_config['max']
            
            if numeric_value < min_val:
                return {
                    'valid': False,
                    'errors': [f"{field_name} value {numeric_value} below minimum {min_val}"],
                    'warnings': [],
                    'value': None
                }
            elif numeric_value > max_val:
                return {
                    'valid': False,
                    'errors': [f"{field_name} value {numeric_value} above maximum {max_val}"],
                    'warnings': [],
                    'value': None
                }
            
            # Check for warning thresholds
            warnings = []
            warning_thresholds = self._get_warning_thresholds(field_name)
            if warning_thresholds:
                if (numeric_value < warning_thresholds['low'] or 
                    numeric_value > warning_thresholds['high']):
                    warnings.append(f"{field_name} value {numeric_value} is outside normal range")
            
            return {
                'valid': True,
                'errors': [],
                'warnings': warnings,
                'value': numeric_value
            }
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"{field_name} validation error: {str(e)}"],
                'warnings': [],
                'value': None
            }
    
    def validate_enum(self, field_name: str, value: Any) -> Dict[str, Any]:
        """Validate enum value"""
        try:
            if field_name not in self.valid_enums:
                return {
                    'valid': False,
                    'errors': [f"Unknown enum field: {field_name}"],
                    'value': None
                }
            
            if not isinstance(value, str):
                return {
                    'valid': False,
                    'errors': [f"{field_name} must be a string"],
                    'value': None
                }
            
            sanitized_value = value.strip().lower()
            valid_values = self.valid_enums[field_name]
            
            if sanitized_value not in [v.lower() for v in valid_values]:
                return {
                    'valid': False,
                    'errors': [f"{field_name} must be one of: {', '.join(valid_values)}"],
                    'value': None
                }
            
            # Return original case from valid values
            for valid_value in valid_values:
                if valid_value.lower() == sanitized_value:
                    return {
                        'valid': True,
                        'errors': [],
                        'value': valid_value
                    }
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"{field_name} validation error: {str(e)}"],
                'value': None
            }
    
    def validate_timestamp(self, timestamp: Any) -> Dict[str, Any]:
        """Validate ISO 8601 timestamp"""
        try:
            if not isinstance(timestamp, str):
                return {
                    'valid': False,
                    'errors': ["Timestamp must be a string"],
                    'value': None
                }
            
            # Try to parse ISO 8601 format
            try:
                parsed_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                
                # Check if timestamp is reasonable (not too far in future/past)
                current_time = datetime.now(timezone.utc)
                time_diff = abs((parsed_time - current_time).total_seconds())
                
                # Allow up to 1 year in past or 1 day in future
                if time_diff > 31536000:  # 1 year
                    if parsed_time > current_time:
                        return {
                            'valid': False,
                            'errors': ["Timestamp cannot be more than 1 day in the future"],
                            'value': None
                        }
                    else:
                        return {
                            'valid': False,
                            'errors': ["Timestamp cannot be more than 1 year in the past"],
                            'value': None
                        }
                
                return {
                    'valid': True,
                    'errors': [],
                    'value': parsed_time.isoformat()
                }
                
            except ValueError as e:
                return {
                    'valid': False,
                    'errors': [f"Invalid timestamp format: {str(e)}"],
                    'value': None
                }
                
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"Timestamp validation error: {str(e)}"],
                'value': None
            }
    
    def validate_date(self, date_value: Any, date_format: str = '%Y-%m-%d') -> Dict[str, Any]:
        """Validate date format"""
        try:
            if not isinstance(date_value, str):
                return {
                    'valid': False,
                    'errors': ["Date must be a string"],
                    'value': None
                }
            
            try:
                parsed_date = datetime.strptime(date_value, date_format)
                
                # Check if date is reasonable
                current_date = datetime.now()
                if parsed_date > current_date:
                    return {
                        'valid': False,
                        'errors': ["Date cannot be in the future"],
                        'value': None
                    }
                
                if parsed_date.year < 1900:
                    return {
                        'valid': False,
                        'errors': ["Date cannot be before 1900"],
                        'value': None
                    }
                
                return {
                    'valid': True,
                    'errors': [],
                    'value': parsed_date.strftime(date_format)
                }
                
            except ValueError:
                return {
                    'valid': False,
                    'errors': [f"Invalid date format (expected {date_format})"],
                    'value': None
                }
                
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"Date validation error: {str(e)}"],
                'value': None
            }
    
    def _get_warning_thresholds(self, field_name: str) -> Optional[Dict[str, float]]:
        """Get warning thresholds for health metrics"""
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
        
        return warning_thresholds.get(field_name)

# Global instance
health_validator = HealthDataValidator()
