#!/usr/bin/env python3

"""
HealthConnect AI - Device Simulator Script
Production-grade IoT device simulation for development and testing
Version: 1.0.0
Last Updated: 2025-06-20
"""

import asyncio
import json
import logging
import argparse
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid
import signal
import sys
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    import websockets
    import boto3
    from botocore.exceptions import ClientError
    import paho.mqtt.client as mqtt
    import numpy as np
    from faker import Faker
except ImportError as e:
    print(f"Error: Missing required dependency: {e}")
    print("Please run: pip install websockets boto3 paho-mqtt numpy faker")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scripts/logs/device-simulator.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize Faker
fake = Faker()

class DeviceSimulator:
    """Production-grade IoT device simulator with realistic data patterns"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.devices: Dict[str, Dict] = {}
        self.running = False
        self.websocket_connections = {}
        self.mqtt_client = None
        self.aws_iot_client = None
        
        # Device type configurations
        self.device_configs = {
            'heart_rate_monitor': {
                'base_value': 72,
                'normal_range': (60, 100),
                'variance': 5,
                'sampling_rate': 1,  # seconds
                'parameters': ['heart_rate', 'heart_rate_variability']
            },
            'blood_pressure_cuff': {
                'base_value': {'systolic': 120, 'diastolic': 80},
                'normal_range': {'systolic': (110, 140), 'diastolic': (70, 90)},
                'variance': {'systolic': 10, 'diastolic': 5},
                'sampling_rate': 300,  # 5 minutes
                'parameters': ['systolic_pressure', 'diastolic_pressure', 'pulse_rate']
            },
            'glucose_meter': {
                'base_value': 100,
                'normal_range': (80, 140),
                'variance': 15,
                'sampling_rate': 1800,  # 30 minutes
                'parameters': ['glucose_level']
            },
            'temperature_sensor': {
                'base_value': 37.0,
                'normal_range': (36.1, 37.2),
                'variance': 0.3,
                'sampling_rate': 60,  # 1 minute
                'parameters': ['temperature']
            },
            'pulse_oximeter': {
                'base_value': {'oxygen_saturation': 98, 'pulse_rate': 72},
                'normal_range': {'oxygen_saturation': (95, 100), 'pulse_rate': (60, 100)},
                'variance': {'oxygen_saturation': 2, 'pulse_rate': 5},
                'sampling_rate': 30,  # 30 seconds
                'parameters': ['oxygen_saturation', 'pulse_rate']
            },
            'activity_tracker': {
                'base_value': {'steps': 0, 'calories': 0, 'distance': 0},
                'normal_range': {'steps': (0, 15000), 'calories': (0, 3000), 'distance': (0, 10)},
                'variance': {'steps': 100, 'calories': 50, 'distance': 0.1},
                'sampling_rate': 60,  # 1 minute
                'parameters': ['steps', 'calories_burned', 'distance_traveled']
            }
        }
        
        # Initialize AWS IoT if configured
        if config.get('aws_iot_endpoint'):
            self.setup_aws_iot()
        
        # Initialize MQTT if configured
        if config.get('mqtt_broker'):
            self.setup_mqtt()
    
    def setup_aws_iot(self):
        """Setup AWS IoT Core connection"""
        try:
            self.aws_iot_client = boto3.client('iot-data', 
                region_name=self.config.get('aws_region', 'us-east-1'))
            logger.info("AWS IoT client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize AWS IoT client: {e}")
    
    def setup_mqtt(self):
        """Setup MQTT connection"""
        try:
            self.mqtt_client = mqtt.Client()
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
            
            broker_config = self.config['mqtt_broker']
            self.mqtt_client.connect(
                broker_config['host'], 
                broker_config.get('port', 1883), 
                60
            )
            self.mqtt_client.loop_start()
            logger.info("MQTT client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize MQTT client: {e}")
    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            logger.info("Connected to MQTT broker")
        else:
            logger.error(f"Failed to connect to MQTT broker: {rc}")
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        logger.info("Disconnected from MQTT broker")
    
    def create_device(self, device_type: str, device_id: str, patient_id: str) -> Dict:
        """Create a new simulated device"""
        if device_type not in self.device_configs:
            raise ValueError(f"Unsupported device type: {device_type}")
        
        config = self.device_configs[device_type]
        device = {
            'id': device_id,
            'type': device_type,
            'patient_id': patient_id,
            'manufacturer': fake.company(),
            'model': f"Model-{random.randint(100, 999)}",
            'serial_number': f"SN{random.randint(1000000, 9999999)}",
            'firmware_version': f"{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
            'status': 'online',
            'battery_level': random.randint(20, 100),
            'signal_strength': random.randint(70, 100),
            'last_reading': None,
            'config': config,
            'created_at': datetime.now().isoformat(),
            'anomaly_probability': 0.05,  # 5% chance of anomalous readings
            'trend_direction': random.choice(['stable', 'increasing', 'decreasing']),
            'trend_magnitude': random.uniform(0.1, 0.5)
        }
        
        self.devices[device_id] = device
        logger.info(f"Created device: {device_id} ({device_type}) for patient {patient_id}")
        return device
    
    def generate_realistic_reading(self, device: Dict) -> Dict:
        """Generate realistic sensor readings with trends and anomalies"""
        device_type = device['type']
        config = device['config']
        
        reading = {
            'device_id': device['id'],
            'patient_id': device['patient_id'],
            'timestamp': datetime.now().isoformat(),
            'data': {},
            'quality_score': random.uniform(0.85, 1.0),
            'battery_level': device['battery_level'],
            'signal_strength': device['signal_strength']
        }
        
        # Generate anomalous reading occasionally
        is_anomaly = random.random() < device['anomaly_probability']
        
        if device_type == 'heart_rate_monitor':
            base_hr = config['base_value']
            
            # Apply trends
            if device['trend_direction'] == 'increasing':
                base_hr += device['trend_magnitude'] * 10
            elif device['trend_direction'] == 'decreasing':
                base_hr -= device['trend_magnitude'] * 10
            
            if is_anomaly:
                # Generate anomalous heart rate
                heart_rate = random.choice([
                    random.randint(40, 50),  # Bradycardia
                    random.randint(120, 180)  # Tachycardia
                ])
            else:
                heart_rate = int(np.random.normal(base_hr, config['variance']))
                heart_rate = max(min(heart_rate, config['normal_range'][1]), config['normal_range'][0])
            
            reading['data'] = {
                'heart_rate': heart_rate,
                'heart_rate_variability': random.randint(20, 50)
            }
        
        elif device_type == 'blood_pressure_cuff':
            base_sys = config['base_value']['systolic']
            base_dia = config['base_value']['diastolic']
            
            if is_anomaly:
                # Hypertensive crisis
                systolic = random.randint(180, 220)
                diastolic = random.randint(110, 130)
            else:
                systolic = int(np.random.normal(base_sys, config['variance']['systolic']))
                diastolic = int(np.random.normal(base_dia, config['variance']['diastolic']))
                
                systolic = max(min(systolic, config['normal_range']['systolic'][1]), 
                              config['normal_range']['systolic'][0])
                diastolic = max(min(diastolic, config['normal_range']['diastolic'][1]), 
                               config['normal_range']['diastolic'][0])
            
            reading['data'] = {
                'systolic_pressure': systolic,
                'diastolic_pressure': diastolic,
                'pulse_rate': random.randint(60, 100)
            }
        
        elif device_type == 'glucose_meter':
            base_glucose = config['base_value']
            
            if is_anomaly:
                # Hypoglycemia or hyperglycemia
                glucose = random.choice([
                    random.randint(40, 60),   # Hypoglycemia
                    random.randint(250, 400)  # Hyperglycemia
                ])
            else:
                glucose = int(np.random.normal(base_glucose, config['variance']))
                glucose = max(min(glucose, config['normal_range'][1]), config['normal_range'][0])
            
            reading['data'] = {
                'glucose_level': glucose
            }
        
        elif device_type == 'temperature_sensor':
            base_temp = config['base_value']
            
            if is_anomaly:
                # Fever or hypothermia
                temperature = random.choice([
                    random.uniform(34.0, 35.5),  # Hypothermia
                    random.uniform(38.5, 41.0)   # Fever
                ])
            else:
                temperature = np.random.normal(base_temp, config['variance'])
                temperature = max(min(temperature, config['normal_range'][1]), config['normal_range'][0])
            
            reading['data'] = {
                'temperature': round(temperature, 1)
            }
        
        elif device_type == 'pulse_oximeter':
            base_spo2 = config['base_value']['oxygen_saturation']
            base_pulse = config['base_value']['pulse_rate']
            
            if is_anomaly:
                # Hypoxemia
                oxygen_saturation = random.randint(85, 94)
                pulse_rate = random.randint(100, 130)
            else:
                oxygen_saturation = int(np.random.normal(base_spo2, config['variance']['oxygen_saturation']))
                pulse_rate = int(np.random.normal(base_pulse, config['variance']['pulse_rate']))
                
                oxygen_saturation = max(min(oxygen_saturation, config['normal_range']['oxygen_saturation'][1]), 
                                      config['normal_range']['oxygen_saturation'][0])
                pulse_rate = max(min(pulse_rate, config['normal_range']['pulse_rate'][1]), 
                               config['normal_range']['pulse_rate'][0])
            
            reading['data'] = {
                'oxygen_saturation': oxygen_saturation,
                'pulse_rate': pulse_rate
            }
        
        elif device_type == 'activity_tracker':
            # Activity tracker accumulates data throughout the day
            current_time = datetime.now()
            minutes_since_midnight = (current_time.hour * 60) + current_time.minute
            
            # Simulate realistic activity patterns
            if 6 <= current_time.hour <= 22:  # Active hours
                steps_per_minute = random.randint(0, 150)
                calories_per_minute = random.uniform(0.5, 2.0)
            else:  # Sleep hours
                steps_per_minute = random.randint(0, 10)
                calories_per_minute = random.uniform(0.1, 0.3)
            
            total_steps = int(minutes_since_midnight * steps_per_minute * random.uniform(0.8, 1.2))
            total_calories = int(minutes_since_midnight * calories_per_minute)
            total_distance = round(total_steps * 0.0008, 2)  # Rough conversion to km
            
            reading['data'] = {
                'steps': total_steps,
                'calories_burned': total_calories,
                'distance_traveled': total_distance
            }
        
        # Update device state
        device['last_reading'] = reading
        device['battery_level'] = max(device['battery_level'] - random.uniform(0.01, 0.05), 0)
        
        # Occasionally change signal strength
        if random.random() < 0.1:
            device['signal_strength'] = random.randint(60, 100)
        
        return reading
    
    async def publish_reading(self, reading: Dict):
        """Publish reading to configured endpoints"""
        try:
            # Publish to WebSocket if connected
            if self.websocket_connections:
                message = json.dumps(reading)
                for ws in self.websocket_connections.values():
                    try:
                        await ws.send(message)
                    except Exception as e:
                        logger.error(f"Failed to send WebSocket message: {e}")
            
            # Publish to MQTT
            if self.mqtt_client:
                topic = f"healthconnect/devices/{reading['device_id']}/data"
                self.mqtt_client.publish(topic, json.dumps(reading))
            
            # Publish to AWS IoT
            if self.aws_iot_client:
                topic = f"healthconnect/devices/{reading['device_id']}/data"
                self.aws_iot_client.publish(
                    topic=topic,
                    qos=1,
                    payload=json.dumps(reading)
                )
            
            # Log to file for debugging
            if self.config.get('log_readings', False):
                with open('scripts/logs/device-readings.jsonl', 'a') as f:
                    f.write(json.dumps(reading) + '\n')
            
        except Exception as e:
            logger.error(f"Failed to publish reading: {e}")
    
    async def simulate_device(self, device_id: str):
        """Simulate a single device"""
        device = self.devices[device_id]
        config = device['config']
        
        while self.running and device['status'] == 'online':
            try:
                # Generate and publish reading
                reading = self.generate_realistic_reading(device)
                await self.publish_reading(reading)
                
                # Wait for next reading based on sampling rate
                await asyncio.sleep(config['sampling_rate'])
                
                # Occasionally simulate device issues
                if random.random() < 0.001:  # 0.1% chance
                    device['status'] = random.choice(['maintenance', 'error'])
                    logger.warning(f"Device {device_id} status changed to {device['status']}")
                    await asyncio.sleep(random.randint(30, 300))  # Downtime
                    device['status'] = 'online'
                    logger.info(f"Device {device_id} back online")
                
            except Exception as e:
                logger.error(f"Error simulating device {device_id}: {e}")
                await asyncio.sleep(5)
    
    async def websocket_handler(self, websocket, path):
        """Handle WebSocket connections"""
        client_id = str(uuid.uuid4())
        self.websocket_connections[client_id] = websocket
        logger.info(f"WebSocket client connected: {client_id}")
        
        try:
            await websocket.wait_closed()
        finally:
            del self.websocket_connections[client_id]
            logger.info(f"WebSocket client disconnected: {client_id}")
    
    async def start_websocket_server(self):
        """Start WebSocket server for real-time data streaming"""
        if self.config.get('websocket_port'):
            server = await websockets.serve(
                self.websocket_handler, 
                "localhost", 
                self.config['websocket_port']
            )
            logger.info(f"WebSocket server started on port {self.config['websocket_port']}")
            return server
        return None
    
    async def run_simulation(self):
        """Run the complete device simulation"""
        self.running = True
        logger.info("Starting device simulation...")
        
        # Start WebSocket server
        websocket_server = await self.start_websocket_server()
        
        # Create simulation tasks for each device
        tasks = []
        for device_id in self.devices:
            task = asyncio.create_task(self.simulate_device(device_id))
            tasks.append(task)
        
        logger.info(f"Simulating {len(self.devices)} devices")
        
        try:
            # Wait for all tasks to complete
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("Simulation cancelled")
        finally:
            self.running = False
            if websocket_server:
                websocket_server.close()
                await websocket_server.wait_closed()
            
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
    
    def stop_simulation(self):
        """Stop the simulation"""
        self.running = False
        logger.info("Stopping device simulation...")


def load_config() -> Dict[str, Any]:
    """Load configuration from file or environment"""
    config = {
        'websocket_port': 8080,
        'mqtt_broker': {
            'host': 'localhost',
            'port': 1883
        },
        'aws_region': 'us-east-1',
        'aws_iot_endpoint': None,
        'log_readings': True,
        'devices': [
            {'type': 'heart_rate_monitor', 'count': 2, 'patient_id': 'patient-001'},
            {'type': 'blood_pressure_cuff', 'count': 1, 'patient_id': 'patient-001'},
            {'type': 'glucose_meter', 'count': 1, 'patient_id': 'patient-002'},
            {'type': 'temperature_sensor', 'count': 3, 'patient_id': 'patient-003'},
            {'type': 'pulse_oximeter', 'count': 2, 'patient_id': 'patient-004'},
            {'type': 'activity_tracker', 'count': 5, 'patient_id': 'patient-005'}
        ]
    }
    
    # Load from config file if exists
    config_file = Path('config/device-simulator.json')
    if config_file.exists():
        with open(config_file) as f:
            file_config = json.load(f)
            config.update(file_config)
    
    return config


async def main():
    """Main function to run device simulation"""
    parser = argparse.ArgumentParser(description='HealthConnect AI Device Simulator')
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--devices', '-d', type=int, default=10, help='Number of devices to simulate')
    parser.add_argument('--duration', '-t', type=int, help='Simulation duration in seconds')
    parser.add_argument('--websocket-port', '-p', type=int, default=8080, help='WebSocket server port')
    parser.add_argument('--log-level', '-l', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Load configuration
    config = load_config()
    if args.config:
        with open(args.config) as f:
            config.update(json.load(f))
    
    if args.websocket_port:
        config['websocket_port'] = args.websocket_port
    
    # Initialize simulator
    simulator = DeviceSimulator(config)
    
    # Create devices
    device_count = 0
    for device_config in config['devices']:
        for i in range(device_config['count']):
            device_id = f"{device_config['type']}-{device_count + 1:03d}"
            simulator.create_device(
                device_config['type'], 
                device_id, 
                device_config['patient_id']
            )
            device_count += 1
            
            if device_count >= args.devices:
                break
        
        if device_count >= args.devices:
            break
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info("Received shutdown signal")
        simulator.stop_simulation()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run simulation
    try:
        if args.duration:
            # Run for specified duration
            await asyncio.wait_for(simulator.run_simulation(), timeout=args.duration)
        else:
            # Run indefinitely
            await simulator.run_simulation()
    except asyncio.TimeoutError:
        logger.info(f"Simulation completed after {args.duration} seconds")
    except KeyboardInterrupt:
        logger.info("Simulation interrupted by user")
    finally:
        simulator.stop_simulation()


if __name__ == "__main__":
    # Ensure logs directory exists
    Path('scripts/logs').mkdir(exist_ok=True)
    
    # Run the simulation
    asyncio.run(main())
