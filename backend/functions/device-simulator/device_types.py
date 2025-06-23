import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import random

logger = logging.getLogger(__name__)

class DeviceTypeManager:
    """Manages different types of medical IoT devices and their specifications"""
    
    def __init__(self):
        self.device_specifications = {
            'heart_rate_monitor': {
                'name': 'Heart Rate Monitor',
                'manufacturer': 'HealthTech Pro',
                'model': 'HRM-2024',
                'data_frequency': 30,  # seconds
                'metrics': ['heart_rate', 'heart_rate_variability'],
                'normal_ranges': {
                    'heart_rate': {'min': 60, 'max': 100, 'unit': 'bpm'},
                    'heart_rate_variability': {'min': 20, 'max': 50, 'unit': 'ms'}
                },
                'accuracy': 0.95,
                'battery_life': 168,  # hours
                'connectivity': 'bluetooth_5.0',
                'certifications': ['FDA', 'CE', 'ISO13485']
            },
            'blood_pressure_cuff': {
                'name': 'Automated Blood Pressure Monitor',
                'manufacturer': 'CardioMed Systems',
                'model': 'BPM-Pro-2024',
                'data_frequency': 300,  # 5 minutes
                'metrics': ['systolic_pressure', 'diastolic_pressure', 'pulse_pressure', 'mean_arterial_pressure'],
                'normal_ranges': {
                    'systolic_pressure': {'min': 90, 'max': 140, 'unit': 'mmHg'},
                    'diastolic_pressure': {'min': 60, 'max': 90, 'unit': 'mmHg'},
                    'pulse_pressure': {'min': 30, 'max': 60, 'unit': 'mmHg'},
                    'mean_arterial_pressure': {'min': 70, 'max': 105, 'unit': 'mmHg'}
                },
                'accuracy': 0.92,
                'battery_life': 720,  # hours
                'connectivity': 'wifi',
                'certifications': ['FDA', 'CE', 'ISO13485', 'AHA_Validated']
            },
            'glucose_meter': {
                'name': 'Continuous Glucose Monitor',
                'manufacturer': 'GlucoSense Technologies',
                'model': 'CGM-Advanced-2024',
                'data_frequency': 60,  # 1 minute
                'metrics': ['glucose_level', 'glucose_trend', 'glucose_rate_of_change'],
                'normal_ranges': {
                    'glucose_level': {'min': 70, 'max': 140, 'unit': 'mg/dL'},
                    'glucose_trend': {'values': ['rising_rapidly', 'rising', 'stable', 'falling', 'falling_rapidly']},
                    'glucose_rate_of_change': {'min': -3, 'max': 3, 'unit': 'mg/dL/min'}
                },
                'accuracy': 0.89,
                'battery_life': 336,  # 14 days
                'connectivity': 'bluetooth_le',
                'certifications': ['FDA', 'CE', 'ISO15197']
            },
            'temperature_sensor': {
                'name': 'Continuous Temperature Monitor',
                'manufacturer': 'ThermoHealth Inc',
                'model': 'TempSense-2024',
                'data_frequency': 120,  # 2 minutes
                'metrics': ['core_temperature', 'skin_temperature', 'ambient_temperature'],
                'normal_ranges': {
                    'core_temperature': {'min': 36.1, 'max': 37.2, 'unit': '°C'},
                    'skin_temperature': {'min': 32.0, 'max': 35.0, 'unit': '°C'},
                    'ambient_temperature': {'min': 18.0, 'max': 26.0, 'unit': '°C'}
                },
                'accuracy': 0.98,
                'battery_life': 504,  # 21 days
                'connectivity': 'zigbee',
                'certifications': ['FDA', 'CE', 'ISO80601']
            },
            'pulse_oximeter': {
                'name': 'Pulse Oximeter',
                'manufacturer': 'OxyMed Solutions',
                'model': 'SpO2-Pro-2024',
                'data_frequency': 15,  # seconds
                'metrics': ['oxygen_saturation', 'pulse_rate', 'perfusion_index', 'pleth_variability_index'],
                'normal_ranges': {
                    'oxygen_saturation': {'min': 95, 'max': 100, 'unit': '%'},
                    'pulse_rate': {'min': 60, 'max': 100, 'unit': 'bpm'},
                    'perfusion_index': {'min': 0.3, 'max': 20.0, 'unit': '%'},
                    'pleth_variability_index': {'min': 9, 'max': 25, 'unit': '%'}
                },
                'accuracy': 0.96,
                'battery_life': 72,  # hours
                'connectivity': 'bluetooth_5.0',
                'certifications': ['FDA', 'CE', 'ISO80601']
            },
            'activity_tracker': {
                'name': 'Medical Grade Activity Tracker',
                'manufacturer': 'FitMed Technologies',
                'model': 'ActivityPro-2024',
                'data_frequency': 900,  # 15 minutes
                'metrics': ['steps', 'calories_burned', 'distance', 'active_minutes', 'sleep_quality', 'stress_level'],
                'normal_ranges': {
                    'steps': {'min': 5000, 'max': 15000, 'unit': 'steps/day'},
                    'calories_burned': {'min': 1200, 'max': 3000, 'unit': 'kcal/day'},
                    'distance': {'min': 2.0, 'max': 12.0, 'unit': 'km/day'},
                    'active_minutes': {'min': 30, 'max': 120, 'unit': 'minutes/day'},
                    'sleep_quality': {'min': 60, 'max': 100, 'unit': 'score'},
                    'stress_level': {'min': 1, 'max': 10, 'unit': 'scale'}
                },
                'accuracy': 0.91,
                'battery_life': 168,  # 7 days
                'connectivity': 'bluetooth_le',
                'certifications': ['FDA', 'CE', 'FCC']
            },
            'ecg_monitor': {
                'name': 'Portable ECG Monitor',
                'manufacturer': 'CardioTech Systems',
                'model': 'ECG-Portable-2024',
                'data_frequency': 1,  # 1 second
                'metrics': ['heart_rhythm', 'rr_interval', 'qt_interval', 'pr_interval', 'qrs_duration'],
                'normal_ranges': {
                    'heart_rhythm': {'values': ['normal_sinus', 'sinus_bradycardia', 'sinus_tachycardia', 'irregular']},
                    'rr_interval': {'min': 600, 'max': 1000, 'unit': 'ms'},
                    'qt_interval': {'min': 350, 'max': 450, 'unit': 'ms'},
                    'pr_interval': {'min': 120, 'max': 200, 'unit': 'ms'},
                    'qrs_duration': {'min': 80, 'max': 120, 'unit': 'ms'}
                },
                'accuracy': 0.97,
                'battery_life': 48,  # hours
                'connectivity': 'wifi',
                'certifications': ['FDA', 'CE', 'ISO13485', 'AHA_Approved']
            },
            'respiratory_monitor': {
                'name': 'Respiratory Rate Monitor',
                'manufacturer': 'RespiTech Solutions',
                'model': 'RespMon-2024',
                'data_frequency': 60,  # 1 minute
                'metrics': ['respiratory_rate', 'tidal_volume', 'minute_ventilation', 'breathing_pattern'],
                'normal_ranges': {
                    'respiratory_rate': {'min': 12, 'max': 20, 'unit': 'breaths/min'},
                    'tidal_volume': {'min': 400, 'max': 600, 'unit': 'mL'},
                    'minute_ventilation': {'min': 5, 'max': 10, 'unit': 'L/min'},
                    'breathing_pattern': {'values': ['regular', 'irregular', 'shallow', 'deep']}
                },
                'accuracy': 0.93,
                'battery_life': 120,  # 5 days
                'connectivity': 'bluetooth_5.0',
                'certifications': ['FDA', 'CE', 'ISO80601']
            }
        }
        
        self.patient_profiles = {
            'normal': {
                'description': 'Healthy adult patient',
                'age_range': (25, 65),
                'risk_factors': [],
                'baseline_adjustments': {}
            },
            'hypertensive': {
                'description': 'Patient with hypertension',
                'age_range': (40, 75),
                'risk_factors': ['high_blood_pressure'],
                'baseline_adjustments': {
                    'systolic_pressure': 15,
                    'diastolic_pressure': 10,
                    'heart_rate': 5
                }
            },
            'diabetic': {
                'description': 'Patient with diabetes',
                'age_range': (35, 70),
                'risk_factors': ['diabetes'],
                'baseline_adjustments': {
                    'glucose_level': 40,
                    'heart_rate': 8
                }
            },
            'elderly': {
                'description': 'Elderly patient (65+)',
                'age_range': (65, 90),
                'risk_factors': ['age_related'],
                'baseline_adjustments': {
                    'heart_rate': -10,
                    'systolic_pressure': 20,
                    'steps': -3000
                }
            },
            'cardiac_patient': {
                'description': 'Patient with cardiac conditions',
                'age_range': (45, 80),
                'risk_factors': ['heart_disease'],
                'baseline_adjustments': {
                    'heart_rate': 10,
                    'systolic_pressure': 20,
                    'diastolic_pressure': 5,
                    'oxygen_saturation': -2
                }
            },
            'post_surgery': {
                'description': 'Post-surgical patient',
                'age_range': (30, 75),
                'risk_factors': ['recent_surgery'],
                'baseline_adjustments': {
                    'heart_rate': 15,
                    'temperature': 0.5,
                    'respiratory_rate': 3
                }
            }
        }
    
    def get_device_specification(self, device_type: str) -> Dict[str, Any]:
        """Get complete specification for a device type"""
        if device_type not in self.device_specifications:
            raise ValueError(f"Unknown device type: {device_type}")
        
        return self.device_specifications[device_type].copy()
    
    def get_supported_device_types(self) -> List[str]:
        """Get list of all supported device types"""
        return list(self.device_specifications.keys())
    
    def get_device_metrics(self, device_type: str) -> List[str]:
        """Get list of metrics for a specific device type"""
        spec = self.get_device_specification(device_type)
        return spec['metrics']
    
    def get_normal_ranges(self, device_type: str) -> Dict[str, Any]:
        """Get normal ranges for device metrics"""
        spec = self.get_device_specification(device_type)
        return spec['normal_ranges']
    
    def get_patient_profile(self, profile_name: str) -> Dict[str, Any]:
        """Get patient profile configuration"""
        if profile_name not in self.patient_profiles:
            raise ValueError(f"Unknown patient profile: {profile_name}")
        
        return self.patient_profiles[profile_name].copy()
    
    def get_supported_patient_profiles(self) -> List[str]:
        """Get list of all supported patient profiles"""
        return list(self.patient_profiles.keys())
    
    def get_initial_state(self, device_type: str, patient_profile: str) -> Dict[str, Any]:
        """Get initial device state for a patient profile"""
        spec = self.get_device_specification(device_type)
        profile = self.get_patient_profile(patient_profile)
        
        initial_state = {
            'device_type': device_type,
            'patient_profile': patient_profile,
            'last_reading_time': None,
            'battery_level': random.uniform(0.7, 1.0),
            'signal_strength': random.uniform(0.8, 1.0),
            'calibration_status': 'calibrated',
            'error_count': 0,
            'baseline_values': {}
        }
        
        # Set baseline values based on normal ranges and patient profile
        normal_ranges = spec['normal_ranges']
        adjustments = profile.get('baseline_adjustments', {})
        
        for metric, range_info in normal_ranges.items():
            if 'min' in range_info and 'max' in range_info:
                # Numeric range
                baseline = random.uniform(range_info['min'], range_info['max'])
                
                # Apply patient profile adjustments
                if metric in adjustments:
                    baseline += adjustments[metric]
                    # Ensure it stays within reasonable bounds
                    baseline = max(range_info['min'] * 0.5, 
                                 min(range_info['max'] * 1.5, baseline))
                
                initial_state['baseline_values'][metric] = baseline
            elif 'values' in range_info:
                # Categorical values
                initial_state['baseline_values'][metric] = random.choice(range_info['values'])
        
        return initial_state
    
    def validate_device_data(self, device_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate device data against specifications"""
        spec = self.get_device_specification(device_type)
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        expected_metrics = set(spec['metrics'])
        provided_metrics = set(data.keys()) - {'timestamp', 'device_id', 'patient_id'}
        
        # Check for missing metrics
        missing_metrics = expected_metrics - provided_metrics
        if missing_metrics:
            validation_result['errors'].append(f"Missing metrics: {list(missing_metrics)}")
            validation_result['valid'] = False
        
        # Check for unexpected metrics
        unexpected_metrics = provided_metrics - expected_metrics
        if unexpected_metrics:
            validation_result['warnings'].append(f"Unexpected metrics: {list(unexpected_metrics)}")
        
        # Validate metric values against normal ranges
        normal_ranges = spec['normal_ranges']
        for metric, value in data.items():
            if metric in normal_ranges:
                range_info = normal_ranges[metric]
                
                if 'min' in range_info and 'max' in range_info:
                    # Numeric validation
                    if not isinstance(value, (int, float)):
                        validation_result['errors'].append(f"Metric {metric} should be numeric")
                        validation_result['valid'] = False
                    elif value < range_info['min'] * 0.3 or value > range_info['max'] * 2.0:
                        validation_result['warnings'].append(
                            f"Metric {metric} value {value} is outside expected range"
                        )
                elif 'values' in range_info:
                    # Categorical validation
                    if value not in range_info['values']:
                        validation_result['errors'].append(
                            f"Metric {metric} value '{value}' not in allowed values: {range_info['values']}"
                        )
                        validation_result['valid'] = False
        
        return validation_result
    
    def get_device_compatibility(self, device_type1: str, device_type2: str) -> Dict[str, Any]:
        """Check compatibility between two device types"""
        spec1 = self.get_device_specification(device_type1)
        spec2 = self.get_device_specification(device_type2)
        
        # Check for overlapping metrics
        metrics1 = set(spec1['metrics'])
        metrics2 = set(spec2['metrics'])
        common_metrics = metrics1.intersection(metrics2)
        
        # Check connectivity compatibility
        connectivity_compatible = (
            spec1['connectivity'] == spec2['connectivity'] or
            'bluetooth' in spec1['connectivity'] and 'bluetooth' in spec2['connectivity']
        )
        
        return {
            'compatible': len(common_metrics) > 0 and connectivity_compatible,
            'common_metrics': list(common_metrics),
            'connectivity_match': connectivity_compatible,
            'data_frequency_ratio': spec1['data_frequency'] / spec2['data_frequency']
        }
    
    def estimate_data_volume(self, device_type: str, duration_hours: int) -> Dict[str, Any]:
        """Estimate data volume for a device over specified duration"""
        spec = self.get_device_specification(device_type)
        
        readings_per_hour = 3600 / spec['data_frequency']
        total_readings = readings_per_hour * duration_hours
        
        # Estimate data size (rough calculation)
        metrics_count = len(spec['metrics'])
        bytes_per_reading = metrics_count * 8 + 50  # 8 bytes per metric + metadata
        total_bytes = total_readings * bytes_per_reading
        
        return {
            'total_readings': int(total_readings),
            'readings_per_hour': readings_per_hour,
            'estimated_bytes': int(total_bytes),
            'estimated_mb': round(total_bytes / (1024 * 1024), 2),
            'storage_requirements': {
                'raw_data': f"{round(total_bytes / (1024 * 1024), 2)} MB",
                'compressed': f"{round(total_bytes * 0.3 / (1024 * 1024), 2)} MB",
                'with_indexes': f"{round(total_bytes * 1.5 / (1024 * 1024), 2)} MB"
            }
        }
    
    def get_maintenance_schedule(self, device_type: str) -> Dict[str, Any]:
        """Get maintenance schedule for a device type"""
        spec = self.get_device_specification(device_type)
        
        # Calculate maintenance intervals based on device characteristics
        battery_life = spec['battery_life']
        accuracy = spec['accuracy']
        
        return {
            'battery_replacement': f"Every {battery_life} hours",
            'calibration_check': f"Every {max(24, battery_life // 7)} hours",
            'accuracy_verification': f"Every {max(168, battery_life // 2)} hours",
            'firmware_update': "Monthly",
            'deep_cleaning': "Weekly",
            'sensor_replacement': f"Every {battery_life * 10} hours or as needed"
        }
