"""Device type constants and specifications for IoT health devices"""

# Device Type Definitions
DEVICE_TYPES = {
    'heart_rate_monitor': {
        'name': 'Heart Rate Monitor',
        'category': 'cardiovascular',
        'data_frequency': 30,  # seconds
        'metrics': ['heart_rate', 'heart_rate_variability'],
        'accuracy': 0.95,
        'battery_life_hours': 168,
        'connectivity': ['bluetooth_5.0', 'wifi'],
        'certifications': ['FDA', 'CE', 'ISO13485']
    },
    'blood_pressure_cuff': {
        'name': 'Automated Blood Pressure Monitor',
        'category': 'cardiovascular',
        'data_frequency': 300,  # 5 minutes
        'metrics': ['systolic_pressure', 'diastolic_pressure', 'pulse_pressure', 'mean_arterial_pressure'],
        'accuracy': 0.92,
        'battery_life_hours': 720,
        'connectivity': ['wifi', 'bluetooth'],
        'certifications': ['FDA', 'CE', 'ISO13485', 'AHA_Validated']
    },
    'glucose_meter': {
        'name': 'Continuous Glucose Monitor',
        'category': 'metabolic',
        'data_frequency': 60,  # 1 minute
        'metrics': ['glucose_level', 'glucose_trend', 'glucose_rate_of_change'],
        'accuracy': 0.89,
        'battery_life_hours': 336,  # 14 days
        'connectivity': ['bluetooth_le'],
        'certifications': ['FDA', 'CE', 'ISO15197']
    },
    'temperature_sensor': {
        'name': 'Continuous Temperature Monitor',
        'category': 'general',
        'data_frequency': 120,  # 2 minutes
        'metrics': ['core_temperature', 'skin_temperature', 'ambient_temperature'],
        'accuracy': 0.98,
        'battery_life_hours': 504,  # 21 days
        'connectivity': ['zigbee', 'wifi'],
        'certifications': ['FDA', 'CE', 'ISO80601']
    },
    'pulse_oximeter': {
        'name': 'Pulse Oximeter',
        'category': 'respiratory',
        'data_frequency': 15,  # seconds
        'metrics': ['oxygen_saturation', 'pulse_rate', 'perfusion_index', 'pleth_variability_index'],
        'accuracy': 0.96,
        'battery_life_hours': 72,
        'connectivity': ['bluetooth_5.0'],
        'certifications': ['FDA', 'CE', 'ISO80601']
    },
    'activity_tracker': {
        'name': 'Medical Grade Activity Tracker',
        'category': 'fitness',
        'data_frequency': 900,  # 15 minutes
        'metrics': ['steps', 'calories_burned', 'distance', 'active_minutes', 'sleep_quality', 'stress_level'],
        'accuracy': 0.91,
        'battery_life_hours': 168,  # 7 days
        'connectivity': ['bluetooth_le'],
        'certifications': ['FDA', 'CE', 'FCC']
    },
    'ecg_monitor': {
        'name': 'Portable ECG Monitor',
        'category': 'cardiovascular',
        'data_frequency': 1,  # 1 second
        'metrics': ['heart_rhythm', 'rr_interval', 'qt_interval', 'pr_interval', 'qrs_duration'],
        'accuracy': 0.97,
        'battery_life_hours': 48,
        'connectivity': ['wifi', 'cellular'],
        'certifications': ['FDA', 'CE', 'ISO13485', 'AHA_Approved']
    },
    'respiratory_monitor': {
        'name': 'Respiratory Rate Monitor',
        'category': 'respiratory',
        'data_frequency': 60,  # 1 minute
        'metrics': ['respiratory_rate', 'tidal_volume', 'minute_ventilation', 'breathing_pattern'],
        'accuracy': 0.93,
        'battery_life_hours': 120,  # 5 days
        'connectivity': ['bluetooth_5.0', 'wifi'],
        'certifications': ['FDA', 'CE', 'ISO80601']
    }
}

# Device Status Codes
DEVICE_STATUS_CODES = {
    'ACTIVE': 'Device is active and transmitting data',
    'INACTIVE': 'Device is inactive or offline',
    'LOW_BATTERY': 'Device battery is low',
    'MAINTENANCE': 'Device requires maintenance',
    'ERROR': 'Device has encountered an error',
    'CALIBRATION_REQUIRED': 'Device requires calibration',
    'FIRMWARE_UPDATE': 'Device firmware needs updating'
}

# Data Quality Indicators
DATA_QUALITY_LEVELS = {
    'EXCELLENT': {'score': 0.95, 'description': 'High quality, reliable data'},
    'GOOD': {'score': 0.85, 'description': 'Good quality data with minor artifacts'},
    'FAIR': {'score': 0.70, 'description': 'Acceptable quality with some interference'},
    'POOR': {'score': 0.50, 'description': 'Poor quality, may have significant artifacts'},
    'UNUSABLE': {'score': 0.25, 'description': 'Data quality too poor for clinical use'}
}

# Connectivity Standards
CONNECTIVITY_STANDARDS = {
    'bluetooth_5.0': {
        'range_meters': 50,
        'power_consumption': 'low',
        'data_rate_mbps': 2,
        'security': 'AES-128'
    },
    'bluetooth_le': {
        'range_meters': 30,
        'power_consumption': 'very_low',
        'data_rate_mbps': 1,
        'security': 'AES-128'
    },
    'wifi': {
        'range_meters': 100,
        'power_consumption': 'medium',
        'data_rate_mbps': 150,
        'security': 'WPA3'
    },
    'cellular': {
        'range_meters': 'unlimited',
        'power_consumption': 'high',
        'data_rate_mbps': 100,
        'security': 'carrier_grade'
    },
    'zigbee': {
        'range_meters': 20,
        'power_consumption': 'low',
        'data_rate_mbps': 0.25,
        'security': 'AES-128'
    }
}

# Regulatory Certifications
REGULATORY_CERTIFICATIONS = {
    'FDA': {
        'name': 'Food and Drug Administration',
        'region': 'United States',
        'description': 'FDA clearance for medical devices'
    },
    'CE': {
        'name': 'Conformité Européenne',
        'region': 'European Union',
        'description': 'CE marking for European compliance'
    },
    'ISO13485': {
        'name': 'Medical devices quality management systems',
        'region': 'International',
        'description': 'ISO standard for medical device quality management'
    },
    'ISO15197': {
        'name': 'In vitro diagnostic test systems',
        'region': 'International',
        'description': 'ISO standard for blood glucose monitoring systems'
    },
    'ISO80601': {
        'name': 'Medical electrical equipment',
        'region': 'International',
        'description': 'ISO standard for medical electrical equipment safety'
    },
    'AHA_Validated': {
        'name': 'American Heart Association Validated',
        'region': 'United States',
        'description': 'AHA validation for blood pressure monitors'
    },
    'AHA_Approved': {
        'name': 'American Heart Association Approved',
        'region': 'United States',
        'description': 'AHA approval for cardiac monitoring devices'
    },
    'FCC': {
        'name': 'Federal Communications Commission',
        'region': 'United States',
        'description': 'FCC certification for wireless devices'
    }
}

# Device Manufacturers
DEVICE_MANUFACTURERS = {
    'healthtech_pro': {
        'name': 'HealthTech Pro',
        'specialties': ['heart_rate_monitors', 'activity_trackers'],
        'certifications': ['FDA', 'CE', 'ISO13485'],
        'support_contact': 'support@healthtechpro.com'
    },
    'cardiomed_systems': {
        'name': 'CardioMed Systems',
        'specialties': ['blood_pressure_cuff', 'ecg_monitor'],
        'certifications': ['FDA', 'CE', 'ISO13485', 'AHA_Validated'],
        'support_contact': 'support@cardiomed.com'
    },
    'glucosense_tech': {
        'name': 'GlucoSense Technologies',
        'specialties': ['glucose_meter'],
        'certifications': ['FDA', 'CE', 'ISO15197'],
        'support_contact': 'support@glucosense.com'
    },
    'thermohealth_inc': {
        'name': 'ThermoHealth Inc',
        'specialties': ['temperature_sensor'],
        'certifications': ['FDA', 'CE', 'ISO80601'],
        'support_contact': 'support@thermohealth.com'
    },
    'oxymed_solutions': {
        'name': 'OxyMed Solutions',
        'specialties': ['pulse_oximeter'],
        'certifications': ['FDA', 'CE', 'ISO80601'],
        'support_contact': 'support@oxymed.com'
    },
    'respitech_solutions': {
        'name': 'RespiTech Solutions',
        'specialties': ['respiratory_monitor'],
        'certifications': ['FDA', 'CE', 'ISO80601'],
        'support_contact': 'support@respitech.com'
    }
}

# Maintenance Schedules
MAINTENANCE_SCHEDULES = {
    'daily': {
        'frequency_hours': 24,
        'tasks': ['battery_check', 'connectivity_test', 'basic_functionality']
    },
    'weekly': {
        'frequency_hours': 168,
        'tasks': ['sensor_cleaning', 'calibration_check', 'firmware_update_check']
    },
    'monthly': {
        'frequency_hours': 720,
        'tasks': ['full_calibration', 'accuracy_verification', 'wear_inspection']
    },
    'quarterly': {
        'frequency_hours': 2160,
        'tasks': ['professional_servicing', 'certification_renewal', 'replacement_assessment']
    }
}
