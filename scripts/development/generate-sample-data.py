#!/usr/bin/env python3

"""
HealthConnect AI - Sample Data Generation Script
Production-grade sample data generation for development and testing
Version: 1.0.0
Last Updated: 2025-06-20
"""

import json
import logging
import argparse
import random
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid
import sys
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from faker import Faker
    import numpy as np
    from scipy import stats
except ImportError as e:
    print(f"Error: Missing required dependency: {e}")
    print("Please run: pip install faker numpy scipy")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scripts/logs/sample-data-generation.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize Faker
fake = Faker()

class SampleDataGenerator:
    """Production-grade sample data generator for healthcare platform"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.output_dir = Path(config.get('output_dir', 'data/generated'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Medical data configurations
        self.medical_conditions = [
            "Hypertension", "Type 2 Diabetes", "Asthma", "Chronic Kidney Disease",
            "Hyperlipidemia", "Osteoarthritis", "Depression", "Anxiety",
            "COPD", "Heart Disease", "Stroke", "Cancer"
        ]
        
        self.medications = [
            "Lisinopril", "Metformin", "Albuterol", "Atorvastatin",
            "Amlodipine", "Omeprazole", "Levothyroxine", "Ibuprofen",
            "Aspirin", "Insulin", "Warfarin", "Prednisone"
        ]
        
        self.allergies = [
            "Penicillin", "Sulfa drugs", "Aspirin", "Shellfish",
            "Nuts", "Latex", "Eggs", "Dairy", "Soy", "Wheat"
        ]
        
        self.specialties = [
            "Cardiology", "Endocrinology", "Pulmonology", "Nephrology",
            "Neurology", "Psychiatry", "Dermatology", "Orthopedics",
            "Emergency Medicine", "Family Medicine", "Internal Medicine"
        ]
    
    def generate_patients(self, count: int) -> List[Dict[str, Any]]:
        """Generate realistic patient profiles"""
        patients = []
        
        for i in range(count):
            birth_date = fake.date_of_birth(minimum_age=18, maximum_age=85)
            age = (datetime.now().date() - birth_date).days // 365
            
            # Age-based condition probability
            condition_probability = min(0.8, age / 100)
            num_conditions = np.random.poisson(condition_probability * 3)
            
            patient = {
                'id': f"PAT-{i+1:06d}",
                'email': fake.email(),
                'first_name': fake.first_name(),
                'last_name': fake.last_name(),
                'date_of_birth': birth_date.isoformat(),
                'age': age,
                'gender': random.choice(['male', 'female', 'other']),
                'phone': fake.phone_number(),
                'address': {
                    'street': fake.street_address(),
                    'city': fake.city(),
                    'state': fake.state_abbr(),
                    'zip_code': fake.zipcode(),
                    'country': 'US'
                },
                'emergency_contacts': [
                    {
                        'name': fake.name(),
                        'relationship': random.choice(['spouse', 'parent', 'child', 'sibling', 'friend']),
                        'phone': fake.phone_number(),
                        'email': fake.email()
                    }
                ],
                'medical_record_number': f"MRN{random.randint(1000000, 9999999)}",
                'insurance': {
                    'provider': random.choice(['Blue Cross', 'Aetna', 'Cigna', 'UnitedHealth', 'Kaiser']),
                    'policy_number': fake.bothify('POL-########'),
                    'group_number': fake.bothify('GRP-####'),
                    'valid_until': (datetime.now() + timedelta(days=random.randint(30, 365))).date().isoformat()
                },
                'medical_history': {
                    'conditions': random.sample(self.medical_conditions, min(num_conditions, len(self.medical_conditions))),
                    'surgeries': self.generate_surgeries(age),
                    'family_history': random.sample(self.medical_conditions, random.randint(0, 3))
                },
                'current_medications': self.generate_medications(num_conditions),
                'allergies': random.sample(self.allergies, random.randint(0, 3)),
                'lifestyle': {
                    'smoking': random.choice(['never', 'former', 'current']),
                    'alcohol': random.choice(['none', 'occasional', 'moderate', 'heavy']),
                    'exercise': random.choice(['sedentary', 'light', 'moderate', 'active']),
                    'diet': random.choice(['poor', 'fair', 'good', 'excellent'])
                },
                'created_at': fake.date_time_between(start_date='-2y', end_date='now').isoformat(),
                'last_visit': fake.date_time_between(start_date='-6M', end_date='now').isoformat()
            }
            
            patients.append(patient)
        
        return patients
    
    def generate_surgeries(self, age: int) -> List[Dict[str, Any]]:
        """Generate realistic surgery history based on age"""
        surgeries = []
        surgery_types = [
            "Appendectomy", "Cholecystectomy", "Hernia Repair", "Knee Replacement",
            "Hip Replacement", "Cataract Surgery", "Coronary Bypass", "Angioplasty"
        ]
        
        # Older patients more likely to have surgeries
        num_surgeries = np.random.poisson(age / 30)
        
        for _ in range(min(num_surgeries, 5)):
            surgery_date = fake.date_between(start_date='-20y', end_date='-1y')
            surgeries.append({
                'procedure': random.choice(surgery_types),
                'date': surgery_date.isoformat(),
                'hospital': fake.company() + " Medical Center",
                'surgeon': f"Dr. {fake.name()}",
                'complications': random.choice([None, "Minor bleeding", "Infection", "Delayed healing"]) if random.random() < 0.1 else None
            })
        
        return surgeries
    
    def generate_medications(self, condition_count: int) -> List[Dict[str, Any]]:
        """Generate realistic medication list"""
        medications = []
        num_meds = min(condition_count + random.randint(0, 2), 8)
        
        for _ in range(num_meds):
            medication = {
                'name': random.choice(self.medications),
                'dosage': f"{random.randint(5, 500)}{random.choice(['mg', 'mcg', 'units'])}",
                'frequency': random.choice(['once daily', 'twice daily', 'three times daily', 'as needed']),
                'route': random.choice(['oral', 'injection', 'topical', 'inhaled']),
                'prescriber': f"Dr. {fake.name()}",
                'start_date': fake.date_between(start_date='-2y', end_date='now').isoformat(),
                'active': random.choice([True, True, True, False])  # 75% active
            }
            medications.append(medication)
        
        return medications
    
    def generate_providers(self, count: int) -> List[Dict[str, Any]]:
        """Generate healthcare provider profiles"""
        providers = []
        
        for i in range(count):
            years_experience = random.randint(5, 35)
            graduation_year = datetime.now().year - years_experience - random.randint(4, 8)
            
            provider = {
                'id': f"PROV-{i+1:04d}",
                'email': fake.email(),
                'first_name': fake.first_name(),
                'last_name': fake.last_name(),
                'title': random.choice(['MD', 'DO', 'NP', 'PA']),
                'specialties': random.sample(self.specialties, random.randint(1, 2)),
                'license_number': f"MD{random.randint(100000, 999999)}",
                'npi_number': f"{random.randint(1000000000, 9999999999)}",
                'phone': fake.phone_number(),
                'education': {
                    'medical_school': fake.company() + " School of Medicine",
                    'graduation_year': graduation_year,
                    'residency': fake.company() + " Medical Center",
                    'fellowship': fake.company() + " Hospital" if random.random() < 0.6 else None
                },
                'certifications': [
                    f"Board Certified in {specialty}" for specialty in random.sample(self.specialties, random.randint(1, 2))
                ],
                'hospital_affiliations': [
                    fake.company() + " Medical Center" for _ in range(random.randint(1, 3))
                ],
                'years_experience': years_experience,
                'consultation_rate': round(random.uniform(150.0, 500.0), 2),
                'rating': round(random.uniform(3.5, 5.0), 1),
                'total_consultations': random.randint(100, 2000),
                'languages': random.sample(['English', 'Spanish', 'French', 'German', 'Chinese'], random.randint(1, 3)),
                'availability': {
                    'monday': {'start': '09:00', 'end': '17:00'},
                    'tuesday': {'start': '09:00', 'end': '17:00'},
                    'wednesday': {'start': '09:00', 'end': '17:00'},
                    'thursday': {'start': '09:00', 'end': '17:00'},
                    'friday': {'start': '09:00', 'end': '17:00'},
                    'saturday': {'start': '09:00', 'end': '13:00'} if random.random() < 0.3 else None,
                    'sunday': None
                },
                'created_at': fake.date_time_between(start_date='-5y', end_date='-1y').isoformat()
            }
            
            providers.append(provider)
        
        return providers
    
    def generate_vital_signs_data(self, patient_count: int, days: int = 90) -> List[Dict[str, Any]]:
        """Generate realistic vital signs data with trends and anomalies"""
        vital_signs = []
        
        for patient_idx in range(patient_count):
            patient_id = f"PAT-{patient_idx+1:06d}"
            
            # Generate baseline values for this patient
            baseline = {
                'heart_rate': random.randint(65, 85),
                'systolic_bp': random.randint(110, 130),
                'diastolic_bp': random.randint(70, 85),
                'temperature': round(random.uniform(36.5, 37.1), 1),
                'oxygen_saturation': random.randint(96, 99),
                'respiratory_rate': random.randint(14, 18),
                'weight': round(random.uniform(50, 120), 1),
                'height': random.randint(150, 190)
            }
            
            # Generate trend (stable, improving, declining)
            trend = random.choice(['stable', 'improving', 'declining'])
            trend_magnitude = random.uniform(0.1, 0.3)
            
            for day in range(days):
                date = datetime.now() - timedelta(days=days-day)
                
                # Generate 1-4 readings per day
                readings_per_day = random.randint(1, 4)
                
                for reading_idx in range(readings_per_day):
                    timestamp = date + timedelta(
                        hours=random.randint(6, 22),
                        minutes=random.randint(0, 59)
                    )
                    
                    # Apply trend over time
                    day_factor = day / days
                    if trend == 'improving':
                        trend_factor = 1 - (trend_magnitude * day_factor)
                    elif trend == 'declining':
                        trend_factor = 1 + (trend_magnitude * day_factor)
                    else:
                        trend_factor = 1
                    
                    # Add daily variation
                    daily_variation = random.uniform(0.95, 1.05)
                    
                    # Generate anomaly occasionally (2% chance)
                    is_anomaly = random.random() < 0.02
                    
                    if is_anomaly:
                        # Generate anomalous values
                        heart_rate = random.choice([random.randint(40, 55), random.randint(110, 150)])
                        systolic_bp = random.choice([random.randint(90, 100), random.randint(160, 200)])
                        temperature = random.choice([random.uniform(34, 36), random.uniform(38, 40)])
                        oxygen_saturation = random.randint(88, 94)
                    else:
                        # Normal variation around baseline
                        heart_rate = int(baseline['heart_rate'] * trend_factor * daily_variation + random.randint(-5, 5))
                        systolic_bp = int(baseline['systolic_bp'] * trend_factor * daily_variation + random.randint(-10, 10))
                        temperature = round(baseline['temperature'] * trend_factor * daily_variation + random.uniform(-0.3, 0.3), 1)
                        oxygen_saturation = int(baseline['oxygen_saturation'] * daily_variation + random.randint(-2, 2))
                    
                    diastolic_bp = int(baseline['diastolic_bp'] * trend_factor * daily_variation + random.randint(-5, 5))
                    respiratory_rate = int(baseline['respiratory_rate'] * daily_variation + random.randint(-2, 2))
                    
                    # Ensure values stay within reasonable bounds
                    heart_rate = max(30, min(200, heart_rate))
                    systolic_bp = max(70, min(250, systolic_bp))
                    diastolic_bp = max(40, min(150, diastolic_bp))
                    temperature = max(32.0, min(43.0, temperature))
                    oxygen_saturation = max(70, min(100, oxygen_saturation))
                    respiratory_rate = max(8, min(40, respiratory_rate))
                    
                    vital_sign = {
                        'id': str(uuid.uuid4()),
                        'patient_id': patient_id,
                        'timestamp': timestamp.isoformat(),
                        'heart_rate': heart_rate,
                        'blood_pressure': {
                            'systolic': systolic_bp,
                            'diastolic': diastolic_bp
                        },
                        'temperature': temperature,
                        'oxygen_saturation': oxygen_saturation,
                        'respiratory_rate': respiratory_rate,
                        'weight': baseline['weight'] + random.uniform(-0.5, 0.5),
                        'height': baseline['height'],
                        'device_id': f"device-{random.randint(1, 10)}",
                        'quality_score': round(random.uniform(0.85, 1.0), 2),
                        'is_anomaly': is_anomaly,
                        'recorded_by': random.choice(['patient', 'device', 'provider'])
                    }
                    
                    vital_signs.append(vital_sign)
        
        return vital_signs
    
    def generate_consultations(self, patient_count: int, provider_count: int, count: int) -> List[Dict[str, Any]]:
        """Generate consultation records"""
        consultations = []
        
        for i in range(count):
            patient_id = f"PAT-{random.randint(1, patient_count):06d}"
            provider_id = f"PROV-{random.randint(1, provider_count):04d}"
            
            scheduled_time = fake.date_time_between(start_date='-6M', end_date='+1M')
            status = random.choice(['scheduled', 'completed', 'cancelled', 'no_show'])
            
            consultation = {
                'id': f"CONS-{i+1:08d}",
                'patient_id': patient_id,
                'provider_id': provider_id,
                'consultation_type': random.choice(['routine', 'follow_up', 'urgent', 'emergency']),
                'status': status,
                'scheduled_time': scheduled_time.isoformat(),
                'duration_minutes': random.randint(15, 60) if status == 'completed' else None,
                'consultation_method': random.choice(['video', 'phone', 'in_person']),
                'chief_complaint': random.choice([
                    'Chest pain', 'Shortness of breath', 'Headache', 'Fatigue',
                    'Abdominal pain', 'Back pain', 'Cough', 'Fever'
                ]),
                'diagnosis': random.sample(self.medical_conditions, random.randint(0, 2)) if status == 'completed' else None,
                'treatment_plan': fake.text(max_nb_chars=200) if status == 'completed' else None,
                'prescriptions': self.generate_medications(random.randint(0, 2)) if status == 'completed' else None,
                'follow_up_required': random.choice([True, False]) if status == 'completed' else None,
                'follow_up_date': (scheduled_time + timedelta(days=random.randint(7, 90))).isoformat() if status == 'completed' and random.random() < 0.3 else None,
                'rating': random.randint(3, 5) if status == 'completed' and random.random() < 0.8 else None,
                'notes': fake.text(max_nb_chars=500) if status == 'completed' else None,
                'created_at': fake.date_time_between(start_date='-6M', end_date='now').isoformat()
            }
            
            consultations.append(consultation)
        
        return consultations
    
    def generate_devices(self, patient_count: int) -> List[Dict[str, Any]]:
        """Generate medical device records"""
        devices = []
        device_types = [
            'heart_rate_monitor', 'blood_pressure_cuff', 'glucose_meter',
            'temperature_sensor', 'pulse_oximeter', 'activity_tracker'
        ]
        
        device_id = 1
        for patient_idx in range(patient_count):
            patient_id = f"PAT-{patient_idx+1:06d}"
            
            # Each patient has 2-4 devices
            num_devices = random.randint(2, 4)
            patient_device_types = random.sample(device_types, num_devices)
            
            for device_type in patient_device_types:
                device = {
                    'id': f"DEV-{device_id:08d}",
                    'patient_id': patient_id,
                    'device_type': device_type,
                    'manufacturer': random.choice(['HealthTech', 'MedDevice', 'VitalCorp', 'BioSense']),
                    'model': f"Model-{random.randint(100, 999)}",
                    'serial_number': f"SN{random.randint(1000000, 9999999)}",
                    'firmware_version': f"{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
                    'status': random.choice(['active', 'active', 'active', 'maintenance', 'inactive']),
                    'battery_level': random.randint(10, 100),
                    'signal_strength': random.randint(60, 100),
                    'last_seen': fake.date_time_between(start_date='-1d', end_date='now').isoformat(),
                    'installation_date': fake.date_between(start_date='-2y', end_date='-1M').isoformat(),
                    'warranty_expiry': fake.date_between(start_date='now', end_date='+2y').isoformat(),
                    'configuration': {
                        'measurement_interval': random.choice([30, 60, 300, 900]),  # seconds
                        'auto_sync': random.choice([True, False]),
                        'alerts_enabled': random.choice([True, False])
                    },
                    'calibration_date': fake.date_between(start_date='-6M', end_date='now').isoformat(),
                    'created_at': fake.date_time_between(start_date='-2y', end_date='-1M').isoformat()
                }
                
                devices.append(device)
                device_id += 1
        
        return devices
    
    def save_data(self, data: List[Dict[str, Any]], filename: str, format: str = 'json'):
        """Save generated data to file"""
        filepath = self.output_dir / f"{filename}.{format}"
        
        if format == 'json':
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        elif format == 'csv':
            if data:
                with open(filepath, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
        
        logger.info(f"Saved {len(data)} records to {filepath}")
    
    def generate_all_data(self):
        """Generate all sample data"""
        config = self.config
        
        logger.info("Starting sample data generation...")
        
        # Generate patients
        patients = self.generate_patients(config.get('patient_count', 100))
        self.save_data(patients, 'patients', 'json')
        
        # Generate providers
        providers = self.generate_providers(config.get('provider_count', 20))
        self.save_data(providers, 'providers', 'json')
        
        # Generate vital signs
        vital_signs = self.generate_vital_signs_data(
            config.get('patient_count', 100),
            config.get('vital_signs_days', 90)
        )
        self.save_data(vital_signs, 'vital_signs', 'json')
        self.save_data(vital_signs, 'vital_signs', 'csv')
        
        # Generate consultations
        consultations = self.generate_consultations(
            config.get('patient_count', 100),
            config.get('provider_count', 20),
            config.get('consultation_count', 500)
        )
        self.save_data(consultations, 'consultations', 'json')
        
        # Generate devices
        devices = self.generate_devices(config.get('patient_count', 100))
        self.save_data(devices, 'devices', 'json')
        
        logger.info("Sample data generation completed successfully!")
        logger.info(f"Generated data saved to: {self.output_dir}")


def load_config() -> Dict[str, Any]:
    """Load configuration from file or use defaults"""
    config = {
        'patient_count': 100,
        'provider_count': 20,
        'consultation_count': 500,
        'vital_signs_days': 90,
        'output_dir': 'data/generated'
    }
    
    # Load from config file if exists
    config_file = Path('config/sample-data.json')
    if config_file.exists():
        with open(config_file) as f:
            file_config = json.load(f)
            config.update(file_config)
    
    return config


def main():
    """Main function to generate sample data"""
    parser = argparse.ArgumentParser(description='HealthConnect AI Sample Data Generator')
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--patients', '-p', type=int, help='Number of patients to generate')
    parser.add_argument('--providers', type=int, help='Number of providers to generate')
    parser.add_argument('--consultations', type=int, help='Number of consultations to generate')
    parser.add_argument('--days', '-d', type=int, help='Days of vital signs data to generate')
    parser.add_argument('--output', '-o', help='Output directory')
    parser.add_argument('--log-level', '-l', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Load configuration
    config = load_config()
    if args.config:
        with open(args.config) as f:
            config.update(json.load(f))
    
    # Override with command line arguments
    if args.patients:
        config['patient_count'] = args.patients
    if args.providers:
        config['provider_count'] = args.providers
    if args.consultations:
        config['consultation_count'] = args.consultations
    if args.days:
        config['vital_signs_days'] = args.days
    if args.output:
        config['output_dir'] = args.output
    
    # Generate data
    generator = SampleDataGenerator(config)
    generator.generate_all_data()


if __name__ == "__main__":
    # Ensure logs directory exists
    Path('scripts/logs').mkdir(exist_ok=True)
    
    # Run the generator
    main()
