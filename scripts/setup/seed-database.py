#!/usr/bin/env python3

"""
HealthConnect AI - Database Seeding Script
Production-grade database initialization with sample data
Version: 1.0.0
Last Updated: 2025-06-20
"""

import os
import sys
import json
import logging
import argparse
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid
import random
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    import asyncpg
    import boto3
    from botocore.exceptions import ClientError
    import bcrypt
    from faker import Faker
except ImportError as e:
    print(f"Error: Missing required dependency: {e}")
    print("Please run: pip install asyncpg boto3 bcrypt faker")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scripts/logs/seed-database.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize Faker for generating sample data
fake = Faker()

class DatabaseSeeder:
    """Production-grade database seeding with comprehensive error handling"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_pool: Optional[asyncpg.Pool] = None
        self.dynamodb = None
        self.s3_client = None
        
        # Initialize AWS clients if configured
        if config.get('aws_region'):
            self.dynamodb = boto3.resource('dynamodb', region_name=config['aws_region'])
            self.s3_client = boto3.client('s3', region_name=config['aws_region'])
    
    async def initialize_database_connection(self) -> None:
        """Initialize PostgreSQL database connection pool"""
        try:
            db_config = self.config['database']
            self.db_pool = await asyncpg.create_pool(
                host=db_config['host'],
                port=db_config['port'],
                user=db_config['user'],
                password=db_config['password'],
                database=db_config['name'],
                min_size=1,
                max_size=10,
                command_timeout=60
            )
            logger.info("Database connection pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            raise
    
    async def create_database_schema(self) -> None:
        """Create database tables and indexes"""
        schema_sql = """
        -- Users table
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            user_type VARCHAR(50) NOT NULL CHECK (user_type IN ('patient', 'provider', 'admin')),
            phone VARCHAR(20),
            date_of_birth DATE,
            gender VARCHAR(10),
            address JSONB,
            emergency_contacts JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            is_active BOOLEAN DEFAULT TRUE,
            last_login TIMESTAMP WITH TIME ZONE,
            email_verified BOOLEAN DEFAULT FALSE,
            phone_verified BOOLEAN DEFAULT FALSE
        );
        
        -- Patients table (extends users)
        CREATE TABLE IF NOT EXISTS patients (
            id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            medical_record_number VARCHAR(50) UNIQUE,
            insurance_info JSONB,
            medical_history JSONB,
            allergies TEXT[],
            medications JSONB,
            primary_care_provider_id UUID REFERENCES users(id),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Healthcare providers table (extends users)
        CREATE TABLE IF NOT EXISTS healthcare_providers (
            id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            license_number VARCHAR(100) UNIQUE NOT NULL,
            specialties TEXT[],
            credentials TEXT[],
            hospital_affiliations JSONB,
            consultation_rate DECIMAL(10,2),
            availability_schedule JSONB,
            rating DECIMAL(3,2) DEFAULT 0.00,
            total_consultations INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Devices table
        CREATE TABLE IF NOT EXISTS devices (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
            device_type VARCHAR(50) NOT NULL,
            manufacturer VARCHAR(100),
            model VARCHAR(100),
            serial_number VARCHAR(100) UNIQUE,
            firmware_version VARCHAR(50),
            status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'maintenance', 'error')),
            battery_level INTEGER CHECK (battery_level >= 0 AND battery_level <= 100),
            last_seen TIMESTAMP WITH TIME ZONE,
            configuration JSONB,
            calibration_data JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Health records table
        CREATE TABLE IF NOT EXISTS health_records (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
            provider_id UUID REFERENCES healthcare_providers(id),
            record_type VARCHAR(50) NOT NULL,
            vital_signs JSONB,
            symptoms TEXT[],
            diagnosis TEXT[],
            treatment_plan TEXT,
            medications JSONB,
            notes TEXT,
            attachments JSONB,
            recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Consultations table
        CREATE TABLE IF NOT EXISTS consultations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
            provider_id UUID NOT NULL REFERENCES healthcare_providers(id) ON DELETE CASCADE,
            consultation_type VARCHAR(50) NOT NULL,
            status VARCHAR(20) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'in_progress', 'completed', 'cancelled', 'no_show')),
            scheduled_time TIMESTAMP WITH TIME ZONE NOT NULL,
            actual_start_time TIMESTAMP WITH TIME ZONE,
            actual_end_time TIMESTAMP WITH TIME ZONE,
            duration_minutes INTEGER,
            consultation_notes TEXT,
            prescription JSONB,
            follow_up_required BOOLEAN DEFAULT FALSE,
            follow_up_date TIMESTAMP WITH TIME ZONE,
            rating INTEGER CHECK (rating >= 1 AND rating <= 5),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Alerts table
        CREATE TABLE IF NOT EXISTS alerts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
            device_id UUID REFERENCES devices(id) ON DELETE SET NULL,
            alert_type VARCHAR(50) NOT NULL,
            severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
            title VARCHAR(200) NOT NULL,
            message TEXT NOT NULL,
            data JSONB,
            acknowledged BOOLEAN DEFAULT FALSE,
            acknowledged_by UUID REFERENCES users(id),
            acknowledged_at TIMESTAMP WITH TIME ZONE,
            resolved BOOLEAN DEFAULT FALSE,
            resolved_by UUID REFERENCES users(id),
            resolved_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Audit log table
        CREATE TABLE IF NOT EXISTS audit_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id),
            action VARCHAR(100) NOT NULL,
            resource_type VARCHAR(50),
            resource_id UUID,
            old_values JSONB,
            new_values JSONB,
            ip_address INET,
            user_agent TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Create indexes for performance
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_users_type ON users(user_type);
        CREATE INDEX IF NOT EXISTS idx_patients_mrn ON patients(medical_record_number);
        CREATE INDEX IF NOT EXISTS idx_devices_patient ON devices(patient_id);
        CREATE INDEX IF NOT EXISTS idx_devices_type ON devices(device_type);
        CREATE INDEX IF NOT EXISTS idx_health_records_patient ON health_records(patient_id);
        CREATE INDEX IF NOT EXISTS idx_health_records_date ON health_records(recorded_at);
        CREATE INDEX IF NOT EXISTS idx_consultations_patient ON consultations(patient_id);
        CREATE INDEX IF NOT EXISTS idx_consultations_provider ON consultations(provider_id);
        CREATE INDEX IF NOT EXISTS idx_consultations_date ON consultations(scheduled_time);
        CREATE INDEX IF NOT EXISTS idx_alerts_patient ON alerts(patient_id);
        CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
        CREATE INDEX IF NOT EXISTS idx_alerts_unresolved ON alerts(resolved) WHERE resolved = FALSE;
        CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_date ON audit_logs(created_at);
        
        -- Create triggers for updated_at timestamps
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        CREATE TRIGGER update_patients_updated_at BEFORE UPDATE ON patients
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        CREATE TRIGGER update_healthcare_providers_updated_at BEFORE UPDATE ON healthcare_providers
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        CREATE TRIGGER update_devices_updated_at BEFORE UPDATE ON devices
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        CREATE TRIGGER update_health_records_updated_at BEFORE UPDATE ON health_records
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        CREATE TRIGGER update_consultations_updated_at BEFORE UPDATE ON consultations
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """
        
        try:
            async with self.db_pool.acquire() as connection:
                await connection.execute(schema_sql)
            logger.info("Database schema created successfully")
        except Exception as e:
            logger.error(f"Failed to create database schema: {e}")
            raise
    
    async def seed_users_and_providers(self) -> Dict[str, List[str]]:
        """Seed users and healthcare providers"""
        user_ids = []
        provider_ids = []
        patient_ids = []
        
        try:
            async with self.db_pool.acquire() as connection:
                # Create admin user
                admin_password = bcrypt.hashpw("admin123!".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                admin_id = await connection.fetchval("""
                    INSERT INTO users (email, password_hash, first_name, last_name, user_type, is_active, email_verified)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING id
                """, "admin@healthconnect-ai.com", admin_password, "System", "Administrator", "admin", True, True)
                user_ids.append(str(admin_id))
                
                # Create healthcare providers
                specialties_list = [
                    ["Cardiology", "Internal Medicine"],
                    ["Emergency Medicine"],
                    ["Family Medicine"],
                    ["Endocrinology", "Diabetes"],
                    ["Pulmonology"],
                    ["Neurology"],
                    ["Psychiatry"],
                    ["Dermatology"]
                ]
                
                for i in range(8):
                    provider_password = bcrypt.hashpw("provider123!".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    provider_id = await connection.fetchval("""
                        INSERT INTO users (email, password_hash, first_name, last_name, user_type, phone, is_active, email_verified)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        RETURNING id
                    """, f"provider{i+1}@healthconnect-ai.com", provider_password, fake.first_name(), fake.last_name(), 
                         "provider", fake.phone_number(), True, True)
                    
                    # Add provider details
                    await connection.execute("""
                        INSERT INTO healthcare_providers (id, license_number, specialties, credentials, consultation_rate, rating, total_consultations)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """, provider_id, f"MD{random.randint(100000, 999999)}", specialties_list[i], 
                         ["MD", "Board Certified"], random.uniform(150.0, 500.0), random.uniform(4.0, 5.0), random.randint(50, 500))
                    
                    user_ids.append(str(provider_id))
                    provider_ids.append(str(provider_id))
                
                # Create patients
                for i in range(20):
                    patient_password = bcrypt.hashpw("patient123!".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    birth_date = fake.date_of_birth(minimum_age=18, maximum_age=85)
                    
                    patient_id = await connection.fetchval("""
                        INSERT INTO users (email, password_hash, first_name, last_name, user_type, phone, date_of_birth, gender, is_active, email_verified)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                        RETURNING id
                    """, f"patient{i+1}@healthconnect-ai.com", patient_password, fake.first_name(), fake.last_name(),
                         "patient", fake.phone_number(), birth_date, random.choice(["male", "female"]), True, True)
                    
                    # Add patient details
                    medical_conditions = random.sample([
                        "Hypertension", "Type 2 Diabetes", "Asthma", "Chronic Kidney Disease", 
                        "Hyperlipidemia", "Osteoarthritis", "Depression", "Anxiety"
                    ], random.randint(0, 3))
                    
                    allergies = random.sample([
                        "Penicillin", "Sulfa drugs", "Aspirin", "Shellfish", "Nuts", "Latex"
                    ], random.randint(0, 2))
                    
                    await connection.execute("""
                        INSERT INTO patients (id, medical_record_number, medical_history, allergies, primary_care_provider_id)
                        VALUES ($1, $2, $3, $4, $5)
                    """, patient_id, f"MRN{random.randint(1000000, 9999999)}", 
                         json.dumps({"conditions": medical_conditions}), allergies, 
                         uuid.UUID(random.choice(provider_ids)) if provider_ids else None)
                    
                    user_ids.append(str(patient_id))
                    patient_ids.append(str(patient_id))
            
            logger.info(f"Created {len(user_ids)} users: 1 admin, {len(provider_ids)} providers, {len(patient_ids)} patients")
            return {"users": user_ids, "providers": provider_ids, "patients": patient_ids}
            
        except Exception as e:
            logger.error(f"Failed to seed users and providers: {e}")
            raise
    
    async def seed_devices(self, patient_ids: List[str]) -> List[str]:
        """Seed medical devices for patients"""
        device_ids = []
        device_types = [
            "heart_rate_monitor", "blood_pressure_cuff", "glucose_meter", 
            "temperature_sensor", "pulse_oximeter", "activity_tracker"
        ]
        
        try:
            async with self.db_pool.acquire() as connection:
                for patient_id in patient_ids:
                    # Each patient gets 2-4 random devices
                    num_devices = random.randint(2, 4)
                    patient_device_types = random.sample(device_types, num_devices)
                    
                    for device_type in patient_device_types:
                        device_id = await connection.fetchval("""
                            INSERT INTO devices (patient_id, device_type, manufacturer, model, serial_number, 
                                               firmware_version, status, battery_level, last_seen)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                            RETURNING id
                        """, uuid.UUID(patient_id), device_type, fake.company(), 
                             f"Model-{random.randint(100, 999)}", f"SN{random.randint(1000000, 9999999)}",
                             f"{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
                             random.choice(["active", "active", "active", "maintenance"]),
                             random.randint(20, 100), fake.date_time_between(start_date='-1d', end_date='now'))
                        
                        device_ids.append(str(device_id))
            
            logger.info(f"Created {len(device_ids)} devices for {len(patient_ids)} patients")
            return device_ids
            
        except Exception as e:
            logger.error(f"Failed to seed devices: {e}")
            raise
    
    async def seed_health_records(self, patient_ids: List[str], provider_ids: List[str]) -> None:
        """Seed health records with realistic vital signs data"""
        try:
            async with self.db_pool.acquire() as connection:
                for patient_id in patient_ids:
                    # Generate 10-30 health records per patient over the last 6 months
                    num_records = random.randint(10, 30)
                    
                    for _ in range(num_records):
                        recorded_date = fake.date_time_between(start_date='-6M', end_date='now')
                        
                        # Generate realistic vital signs
                        vital_signs = {
                            "heart_rate": random.randint(60, 100),
                            "blood_pressure": {
                                "systolic": random.randint(110, 140),
                                "diastolic": random.randint(70, 90)
                            },
                            "temperature": round(random.uniform(36.1, 37.2), 1),
                            "oxygen_saturation": random.randint(95, 100),
                            "respiratory_rate": random.randint(12, 20),
                            "weight": round(random.uniform(50, 120), 1),
                            "height": random.randint(150, 200)
                        }
                        
                        # Occasionally add glucose level for diabetic patients
                        if random.random() < 0.3:
                            vital_signs["glucose_level"] = random.randint(80, 180)
                        
                        await connection.execute("""
                            INSERT INTO health_records (patient_id, provider_id, record_type, vital_signs, 
                                                      symptoms, diagnosis, notes, recorded_at)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        """, uuid.UUID(patient_id), 
                             uuid.UUID(random.choice(provider_ids)) if random.random() < 0.7 else None,
                             random.choice(["routine_checkup", "follow_up", "emergency", "consultation"]),
                             json.dumps(vital_signs),
                             random.sample(["fatigue", "headache", "chest_pain", "shortness_of_breath", "dizziness"], 
                                         random.randint(0, 2)),
                             random.sample(["hypertension", "diabetes", "anxiety", "upper_respiratory_infection"], 
                                         random.randint(0, 2)),
                             fake.text(max_nb_chars=200),
                             recorded_date)
            
            logger.info(f"Created health records for {len(patient_ids)} patients")
            
        except Exception as e:
            logger.error(f"Failed to seed health records: {e}")
            raise
    
    async def seed_consultations(self, patient_ids: List[str], provider_ids: List[str]) -> None:
        """Seed consultation records"""
        try:
            async with self.db_pool.acquire() as connection:
                for patient_id in patient_ids:
                    # Generate 3-8 consultations per patient
                    num_consultations = random.randint(3, 8)
                    
                    for _ in range(num_consultations):
                        scheduled_time = fake.date_time_between(start_date='-3M', end_date='+1M')
                        status = random.choice(['scheduled', 'completed', 'cancelled'])
                        
                        if status == 'completed':
                            actual_start_time = scheduled_time
                            duration_minutes = random.randint(15, 60)
                            actual_end_time = actual_start_time + timedelta(minutes=duration_minutes)
                            consultation_notes = fake.text(max_nb_chars=200)
                            rating = random.randint(3, 5)
                        else:
                            actual_start_time = None
                            actual_end_time = None
                            duration_minutes = None
                            consultation_notes = None
                            rating = None
                        
                        await connection.execute("""
                            INSERT INTO consultations (patient_id, provider_id, consultation_type, status, 
                                                     scheduled_time, actual_start_time, actual_end_time, 
                                                     duration_minutes, consultation_notes, rating)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                        """, uuid.UUID(patient_id), uuid.UUID(random.choice(provider_ids)),
                             random.choice(["routine", "follow_up", "urgent", "emergency"]),
                             status, scheduled_time, actual_start_time, actual_end_time,
                             duration_minutes, consultation_notes, rating)
            
            logger.info(f"Created consultation records for {len(patient_ids)} patients")
            
        except Exception as e:
            logger.error(f"Failed to seed consultations: {e}")
            raise
    
    async def seed_alerts(self, patient_ids: List[str], device_ids: List[str]) -> None:
        """Seed health alerts"""
        try:
            async with self.db_pool.acquire() as connection:
                alert_types = [
                    "vital_signs_abnormal", "device_malfunction", "medication_reminder",
                    "appointment_reminder", "emergency_alert", "low_battery"
                ]
                
                for _ in range(50):  # Create 50 random alerts
                    patient_id = random.choice(patient_ids)
                    device_id = random.choice(device_ids) if random.random() < 0.7 else None
                    alert_type = random.choice(alert_types)
                    severity = random.choice(["low", "medium", "high", "critical"])
                    
                    # Generate alert based on type
                    if alert_type == "vital_signs_abnormal":
                        title = "Abnormal Vital Signs Detected"
                        message = "Heart rate outside normal range detected"
                    elif alert_type == "device_malfunction":
                        title = "Device Malfunction"
                        message = "Device connectivity issues detected"
                    else:
                        title = fake.sentence(nb_words=4)
                        message = fake.text(max_nb_chars=100)
                    
                    acknowledged = random.random() < 0.6
                    resolved = acknowledged and random.random() < 0.8
                    
                    await connection.execute("""
                        INSERT INTO alerts (patient_id, device_id, alert_type, severity, title, message, 
                                          acknowledged, resolved, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """, uuid.UUID(patient_id), uuid.UUID(device_id) if device_id else None,
                         alert_type, severity, title, message, acknowledged, resolved,
                         fake.date_time_between(start_date='-1M', end_date='now'))
            
            logger.info("Created 50 health alerts")
            
        except Exception as e:
            logger.error(f"Failed to seed alerts: {e}")
            raise
    
    def seed_dynamodb_tables(self) -> None:
        """Seed DynamoDB tables with sample data"""
        if not self.dynamodb:
            logger.warning("DynamoDB not configured, skipping DynamoDB seeding")
            return
        
        try:
            # Seed device readings table
            table_name = f"{self.config.get('project_name', 'healthconnect-ai')}-{self.config.get('environment', 'dev')}-device_readings"
            
            try:
                table = self.dynamodb.Table(table_name)
                
                # Generate sample device readings
                for _ in range(100):
                    reading_id = str(uuid.uuid4())
                    device_id = f"device-{random.randint(1, 20)}"
                    timestamp = datetime.now() - timedelta(hours=random.randint(1, 168))
                    
                    item = {
                        'reading_id': reading_id,
                        'device_id': device_id,
                        'timestamp': timestamp.isoformat(),
                        'data': {
                            'heart_rate': random.randint(60, 100),
                            'blood_pressure': {
                                'systolic': random.randint(110, 140),
                                'diastolic': random.randint(70, 90)
                            },
                            'temperature': round(random.uniform(36.1, 37.2), 1)
                        },
                        'quality_score': round(random.uniform(0.8, 1.0), 2)
                    }
                    
                    table.put_item(Item=item)
                
                logger.info(f"Seeded DynamoDB table: {table_name}")
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    logger.warning(f"DynamoDB table {table_name} not found, skipping")
                else:
                    raise
            
        except Exception as e:
            logger.error(f"Failed to seed DynamoDB tables: {e}")
            raise
    
    async def cleanup_and_close(self) -> None:
        """Clean up database connections"""
        if self.db_pool:
            await self.db_pool.close()
            logger.info("Database connection pool closed")
    
    async def run_seeding(self) -> None:
        """Run the complete database seeding process"""
        try:
            logger.info("Starting database seeding process...")
            
            await self.initialize_database_connection()
            await self.create_database_schema()
            
            # Seed data in order
            user_data = await self.seed_users_and_providers()
            device_ids = await self.seed_devices(user_data['patients'])
            await self.seed_health_records(user_data['patients'], user_data['providers'])
            await self.seed_consultations(user_data['patients'], user_data['providers'])
            await self.seed_alerts(user_data['patients'], device_ids)
            
            # Seed DynamoDB if configured
            self.seed_dynamodb_tables()
            
            logger.info("Database seeding completed successfully!")
            
        except Exception as e:
            logger.error(f"Database seeding failed: {e}")
            raise
        finally:
            await self.cleanup_and_close()


def load_config() -> Dict[str, Any]:
    """Load configuration from environment variables and config files"""
    config = {
        'database': {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '5432')),
            'user': os.getenv('DB_USER', 'healthconnect_user'),
            'password': os.getenv('DB_PASSWORD', ''),
            'name': os.getenv('DB_NAME', 'healthconnect_dev')
        },
        'aws_region': os.getenv('AWS_REGION', 'us-east-1'),
        'project_name': os.getenv('PROJECT_NAME', 'healthconnect-ai'),
        'environment': os.getenv('ENVIRONMENT', 'dev')
    }
    
    # Load additional config from file if exists
    config_file = Path('config/database.json')
    if config_file.exists():
        with open(config_file) as f:
            file_config = json.load(f)
            environment = config['environment']
            if environment in file_config:
                config['database'].update(file_config[environment])
    
    return config


async def main():
    """Main function to run database seeding"""
    parser = argparse.ArgumentParser(description='Seed HealthConnect AI database with sample data')
    parser.add_argument('--environment', '-e', default='development', 
                       choices=['development', 'test', 'production'],
                       help='Environment to seed (default: development)')
    parser.add_argument('--skip-schema', action='store_true',
                       help='Skip schema creation (tables already exist)')
    parser.add_argument('--tables-only', action='store_true',
                       help='Only create tables, skip data seeding')
    parser.add_argument('--data-only', action='store_true',
                       help='Only seed data, skip schema creation')
    
    args = parser.parse_args()
    
    # Set environment
    os.environ['ENVIRONMENT'] = args.environment
    
    # Load configuration
    config = load_config()
    
    # Validate required configuration
    if not config['database']['password']:
        logger.error("Database password not configured. Please set DB_PASSWORD environment variable.")
        sys.exit(1)
    
    # Confirm production seeding
    if args.environment == 'production':
        confirm = input("Are you sure you want to seed the PRODUCTION database? (yes/no): ")
        if confirm.lower() != 'yes':
            logger.info("Production seeding cancelled")
            sys.exit(0)
    
    # Initialize seeder
    seeder = DatabaseSeeder(config)
    
    try:
        if args.tables_only:
            await seeder.initialize_database_connection()
            await seeder.create_database_schema()
            logger.info("Schema creation completed")
        elif args.data_only:
            await seeder.initialize_database_connection()
            # Run only data seeding methods
            user_data = await seeder.seed_users_and_providers()
            device_ids = await seeder.seed_devices(user_data['patients'])
            await seeder.seed_health_records(user_data['patients'], user_data['providers'])
            await seeder.seed_consultations(user_data['patients'], user_data['providers'])
            await seeder.seed_alerts(user_data['patients'], device_ids)
            seeder.seed_dynamodb_tables()
            logger.info("Data seeding completed")
        else:
            await seeder.run_seeding()
            
    except KeyboardInterrupt:
        logger.info("Seeding interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        sys.exit(1)
    finally:
        await seeder.cleanup_and_close()


if __name__ == "__main__":
    # Ensure logs directory exists
    os.makedirs('scripts/logs', exist_ok=True)
    
    # Run the seeding process
    asyncio.run(main())
