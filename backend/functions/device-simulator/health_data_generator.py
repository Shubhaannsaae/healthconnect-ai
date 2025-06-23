import random
import math
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class HealthDataGenerator:
    """Generates realistic health data for IoT device simulation"""[1][2]
    
    def __init__(self):
        # Initialize random seed for reproducible patterns
        self.random_state = np.random.RandomState(42)
        
        # Physiological correlations matrix
        self.correlations = {
            'heart_rate_systolic': 0.3,
            'heart_rate_temperature': 0.4,
            'systolic_diastolic': 0.8,
            'glucose_stress': 0.5,
            'activity_heart_rate': 0.6,
            'temperature_respiratory': 0.3
        }
        
        # Circadian rhythm patterns
        self.circadian_patterns = {
            'heart_rate': {'amplitude': 10, 'peak_hour': 14, 'trough_hour': 4},
            'blood_pressure': {'amplitude': 15, 'peak_hour': 10, 'trough_hour': 2},
            'temperature': {'amplitude': 0.8, 'peak_hour': 18, 'trough_hour': 6},
            'glucose': {'amplitude': 20, 'peak_hour': 12, 'trough_hour': 4}
        }
        
        # Stress response patterns
        self.stress_multipliers = {
            'heart_rate': 1.3,
            'systolic_pressure': 1.2,
            'respiratory_rate': 1.4,
            'glucose_level': 1.15
        }
    
    def generate_realistic_data(
        self, 
        device_type: str, 
        patient_profile: str, 
        current_state: Dict[str, Any],
        scenario_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate realistic health data based on device type and patient profile"""[1]
        
        if scenario_params is None:
            scenario_params = {}
        
        # Get current time for circadian calculations
        current_time = datetime.now(timezone.utc)
        hour_of_day = current_time.hour
        
        # Apply circadian rhythms
        circadian_factor = self._calculate_circadian_factor(device_type, hour_of_day)
        
        # Apply stress factors from scenario
        stress_factor = scenario_params.get('stress_factor', 1.0)
        
        # Generate data based on device type
        if device_type == 'heart_rate_monitor':
            return self._generate_heart_rate_data(
                patient_profile, current_state, circadian_factor, stress_factor, scenario_params
            )
        elif device_type == 'blood_pressure_cuff':
            return self._generate_blood_pressure_data(
                patient_profile, current_state, circadian_factor, stress_factor, scenario_params
            )
        elif device_type == 'glucose_meter':
            return self._generate_glucose_data(
                patient_profile, current_state, circadian_factor, stress_factor, scenario_params
            )
        elif device_type == 'temperature_sensor':
            return self._generate_temperature_data(
                patient_profile, current_state, circadian_factor, stress_factor, scenario_params
            )
        elif device_type == 'pulse_oximeter':
            return self._generate_pulse_oximeter_data(
                patient_profile, current_state, circadian_factor, stress_factor, scenario_params
            )
        elif device_type == 'activity_tracker':
            return self._generate_activity_data(
                patient_profile, current_state, circadian_factor, stress_factor, scenario_params
            )
        elif device_type == 'ecg_monitor':
            return self._generate_ecg_data(
                patient_profile, current_state, circadian_factor, stress_factor, scenario_params
            )
        elif device_type == 'respiratory_monitor':
            return self._generate_respiratory_data(
                patient_profile, current_state, circadian_factor, stress_factor, scenario_params
            )
        else:
            raise ValueError(f"Unsupported device type: {device_type}")
    
    def _calculate_circadian_factor(self, device_type: str, hour_of_day: int) -> float:
        """Calculate circadian rhythm factor for given hour"""
        if device_type not in self.circadian_patterns:
            return 1.0
        
        pattern = self.circadian_patterns[device_type]
        
        # Calculate sine wave based on hour of day
        # Peak at peak_hour, trough at trough_hour
        peak_hour = pattern['peak_hour']
        amplitude = pattern['amplitude']
        
        # Convert to radians (24 hours = 2π)
        hour_radians = (hour_of_day - peak_hour) * 2 * math.pi / 24
        
        # Calculate factor (1.0 ± amplitude%)
        factor = 1.0 + (amplitude / 100) * math.sin(hour_radians)
        
        return max(0.5, min(1.5, factor))  # Bound between 0.5 and 1.5
    
    def _generate_heart_rate_data(
        self, 
        patient_profile: str, 
        current_state: Dict[str, Any],
        circadian_factor: float,
        stress_factor: float,
        scenario_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate realistic heart rate monitor data"""
        
        baseline_hr = current_state['baseline_values'].get('heart_rate', 75)
        baseline_hrv = current_state['baseline_values'].get('heart_rate_variability', 35)
        
        # Apply patient profile adjustments
        if patient_profile == 'elderly':
            baseline_hr -= 5
            baseline_hrv -= 10
        elif patient_profile == 'cardiac_patient':
            baseline_hr += 10
            baseline_hrv -= 15
        elif patient_profile == 'post_surgery':
            baseline_hr += 15
            baseline_hrv -= 5
        
        # Apply circadian and stress factors
        current_hr = baseline_hr * circadian_factor * stress_factor
        
        # Add realistic variability
        hr_noise = self.random_state.normal(0, 3)
        current_hr += hr_noise
        
        # Emergency scenario modifications
        if scenario_params.get('emergency_trigger', False):
            current_hr *= 1.4  # Significant increase during emergency
            baseline_hrv *= 0.6  # Reduced variability under stress
        
        # Calculate HRV with inverse relationship to HR
        hrv_factor = max(0.5, min(1.5, baseline_hr / current_hr))
        current_hrv = baseline_hrv * hrv_factor + self.random_state.normal(0, 2)
        
        # Ensure realistic bounds
        current_hr = max(40, min(200, current_hr))
        current_hrv = max(10, min(80, current_hrv))
        
        return {
            'heart_rate': round(current_hr, 1),
            'heart_rate_variability': round(current_hrv, 1),
            'signal_quality': random.uniform(0.85, 0.98),
            'motion_artifact': random.choice([True, False]) if random.random() < 0.1 else False
        }
    
    def _generate_blood_pressure_data(
        self,
        patient_profile: str,
        current_state: Dict[str, Any],
        circadian_factor: float,
        stress_factor: float,
        scenario_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate realistic blood pressure data"""
        
        baseline_systolic = current_state['baseline_values'].get('systolic_pressure', 120)
        baseline_diastolic = current_state['baseline_values'].get('diastolic_pressure', 80)
        
        # Patient profile adjustments
        if patient_profile == 'hypertensive':
            baseline_systolic += 20
            baseline_diastolic += 10
        elif patient_profile == 'elderly':
            baseline_systolic += 15
            baseline_diastolic += 5
        elif patient_profile == 'cardiac_patient':
            baseline_systolic += 25
            baseline_diastolic += 8
        
        # Apply factors
        current_systolic = baseline_systolic * circadian_factor * stress_factor
        current_diastolic = baseline_diastolic * circadian_factor * stress_factor
        
        # Maintain physiological relationship (systolic > diastolic)
        if current_systolic <= current_diastolic:
            current_systolic = current_diastolic + 20
        
        # Add noise
        systolic_noise = self.random_state.normal(0, 5)
        diastolic_noise = self.random_state.normal(0, 3)
        
        current_systolic += systolic_noise
        current_diastolic += diastolic_noise
        
        # Emergency modifications
        if scenario_params.get('emergency_trigger', False):
            current_systolic *= 1.3
            current_diastolic *= 1.2
        
        # Calculate derived metrics
        pulse_pressure = current_systolic - current_diastolic
        mean_arterial_pressure = current_diastolic + (pulse_pressure / 3)
        
        # Ensure realistic bounds
        current_systolic = max(70, min(250, current_systolic))
        current_diastolic = max(40, min(150, current_diastolic))
        
        return {
            'blood_pressure': {
                'systolic': round(current_systolic),
                'diastolic': round(current_diastolic)
            },
            'pulse_pressure': round(pulse_pressure),
            'mean_arterial_pressure': round(mean_arterial_pressure, 1),
            'measurement_quality': random.uniform(0.88, 0.97)
        }
    
    def _generate_glucose_data(
        self,
        patient_profile: str,
        current_state: Dict[str, Any],
        circadian_factor: float,
        stress_factor: float,
        scenario_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate realistic glucose monitor data"""
        
        baseline_glucose = current_state['baseline_values'].get('glucose_level', 95)
        
        # Patient profile adjustments
        if patient_profile == 'diabetic':
            baseline_glucose += 60
        elif patient_profile == 'elderly':
            baseline_glucose += 10
        elif patient_profile == 'post_surgery':
            baseline_glucose += 20
        
        # Apply factors
        current_glucose = baseline_glucose * circadian_factor * stress_factor
        
        # Add meal-related variations (simulate post-meal spikes)
        current_hour = datetime.now().hour
        if current_hour in [8, 13, 19]:  # Meal times
            meal_spike = random.uniform(20, 50) if patient_profile == 'diabetic' else random.uniform(10, 25)
            current_glucose += meal_spike
        
        # Add noise
        glucose_noise = self.random_state.normal(0, 8)
        current_glucose += glucose_noise
        
        # Emergency modifications
        if scenario_params.get('emergency_trigger', False):
            if random.random() < 0.5:
                current_glucose *= 1.8  # Hyperglycemia
            else:
                current_glucose *= 0.4  # Hypoglycemia
        
        # Calculate trend and rate of change
        previous_glucose = current_state.get('previous_glucose', current_glucose)
        rate_of_change = (current_glucose - previous_glucose) / 5  # Per minute
        
        if rate_of_change > 2:
            trend = 'rising_rapidly'
        elif rate_of_change > 1:
            trend = 'rising'
        elif rate_of_change < -2:
            trend = 'falling_rapidly'
        elif rate_of_change < -1:
            trend = 'falling'
        else:
            trend = 'stable'
        
        # Ensure realistic bounds
        current_glucose = max(40, min(400, current_glucose))
        rate_of_change = max(-5, min(5, rate_of_change))
        
        return {
            'glucose_level': round(current_glucose, 1),
            'glucose_trend': trend,
            'glucose_rate_of_change': round(rate_of_change, 2),
            'sensor_accuracy': random.uniform(0.85, 0.95),
            'previous_glucose': current_glucose  # Store for next calculation
        }
    
    def _generate_temperature_data(
        self,
        patient_profile: str,
        current_state: Dict[str, Any],
        circadian_factor: float,
        stress_factor: float,
        scenario_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate realistic temperature sensor data"""
        
        baseline_core = current_state['baseline_values'].get('core_temperature', 36.8)
        baseline_skin = current_state['baseline_values'].get('skin_temperature', 33.5)
        baseline_ambient = current_state['baseline_values'].get('ambient_temperature', 22.0)
        
        # Patient profile adjustments
        if patient_profile == 'elderly':
            baseline_core -= 0.2
            baseline_skin -= 0.5
        elif patient_profile == 'post_surgery':
            baseline_core += 0.8  # Post-surgical fever
        
        # Apply factors
        current_core = baseline_core * circadian_factor
        current_skin = baseline_skin * circadian_factor
        
        # Add stress-related temperature increase
        if stress_factor > 1.2:
            current_core += (stress_factor - 1.0) * 0.5
        
        # Add noise
        core_noise = self.random_state.normal(0, 0.1)
        skin_noise = self.random_state.normal(0, 0.2)
        ambient_noise = self.random_state.normal(0, 0.5)
        
        current_core += core_noise
        current_skin += skin_noise
        current_ambient = baseline_ambient + ambient_noise
        
        # Emergency modifications (fever)
        if scenario_params.get('emergency_trigger', False):
            if random.random() < 0.7:  # 70% chance of fever in emergency
                current_core += random.uniform(1.5, 3.0)
        
        # Maintain physiological relationships
        if current_skin > current_core - 1.0:
            current_skin = current_core - random.uniform(1.0, 3.0)
        
        # Ensure realistic bounds
        current_core = max(34.0, min(42.0, current_core))
        current_skin = max(28.0, min(38.0, current_skin))
        current_ambient = max(15.0, min(35.0, current_ambient))
        
        return {
            'core_temperature': round(current_core, 1),
            'skin_temperature': round(current_skin, 1),
            'ambient_temperature': round(current_ambient, 1),
            'sensor_calibration': random.uniform(0.95, 1.0)
        }
    
    def _generate_pulse_oximeter_data(
        self,
        patient_profile: str,
        current_state: Dict[str, Any],
        circadian_factor: float,
        stress_factor: float,
        scenario_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate realistic pulse oximeter data"""
        
        baseline_spo2 = current_state['baseline_values'].get('oxygen_saturation', 98)
        baseline_pulse = current_state['baseline_values'].get('pulse_rate', 75)
        baseline_pi = current_state['baseline_values'].get('perfusion_index', 2.0)
        baseline_pvi = current_state['baseline_values'].get('pleth_variability_index', 15)
        
        # Patient profile adjustments
        if patient_profile == 'elderly':
            baseline_spo2 -= 1
            baseline_pi -= 0.3
        elif patient_profile == 'cardiac_patient':
            baseline_spo2 -= 2
            baseline_pulse += 10
            baseline_pi -= 0.5
        elif patient_profile == 'post_surgery':
            baseline_spo2 -= 1
            baseline_pulse += 15
        
        # Apply factors
        current_pulse = baseline_pulse * circadian_factor * stress_factor
        current_spo2 = baseline_spo2
        current_pi = baseline_pi * circadian_factor
        current_pvi = baseline_pvi
        
        # SpO2 typically doesn't vary much with circadian rhythms
        # but can be affected by stress and health conditions
        if stress_factor > 1.3:
            current_spo2 -= (stress_factor - 1.0) * 2
        
        # Add noise
        pulse_noise = self.random_state.normal(0, 2)
        spo2_noise = self.random_state.normal(0, 0.3)
        pi_noise = self.random_state.normal(0, 0.2)
        pvi_noise = self.random_state.normal(0, 1)
        
        current_pulse += pulse_noise
        current_spo2 += spo2_noise
        current_pi += pi_noise
        current_pvi += pvi_noise
        
        # Emergency modifications
        if scenario_params.get('emergency_trigger', False):
            current_spo2 -= random.uniform(5, 15)  # Hypoxemia
            current_pi *= 0.5  # Poor perfusion
        
        # Ensure realistic bounds
        current_pulse = max(40, min(200, current_pulse))
        current_spo2 = max(70, min(100, current_spo2))
        current_pi = max(0.1, min(20.0, current_pi))
        current_pvi = max(5, min(30, current_pvi))
        
        return {
            'oxygen_saturation': round(current_spo2, 1),
            'pulse_rate': round(current_pulse),
            'perfusion_index': round(current_pi, 1),
            'pleth_variability_index': round(current_pvi),
            'signal_strength': random.uniform(0.8, 0.98)
        }
    
    def _generate_activity_data(
        self,
        patient_profile: str,
        current_state: Dict[str, Any],
        circadian_factor: float,
        stress_factor: float,
        scenario_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate realistic activity tracker data"""
        
        baseline_steps = current_state['baseline_values'].get('steps', 8000)
        baseline_calories = current_state['baseline_values'].get('calories_burned', 2000)
        baseline_distance = current_state['baseline_values'].get('distance', 6.0)
        baseline_active = current_state['baseline_values'].get('active_minutes', 60)
        baseline_sleep = current_state['baseline_values'].get('sleep_quality', 80)
        baseline_stress = current_state['baseline_values'].get('stress_level', 3)
        
        # Patient profile adjustments
        if patient_profile == 'elderly':
            baseline_steps -= 3000
            baseline_active -= 20
            baseline_sleep -= 10
        elif patient_profile == 'cardiac_patient':
            baseline_steps -= 2000
            baseline_active -= 15
            baseline_stress += 2
        elif patient_profile == 'post_surgery':
            baseline_steps -= 5000
            baseline_active -= 40
            baseline_stress += 3
        
        # Current hour affects activity levels
        current_hour = datetime.now().hour
        if 6 <= current_hour <= 22:  # Daytime
            activity_factor = circadian_factor
        else:  # Nighttime
            activity_factor = 0.1
        
        # Calculate current values
        current_steps = baseline_steps * activity_factor
        current_calories = baseline_calories * circadian_factor
        current_distance = baseline_distance * activity_factor
        current_active = baseline_active * activity_factor
        current_sleep = baseline_sleep
        current_stress = baseline_stress * stress_factor
        
        # Add noise
        steps_noise = self.random_state.normal(0, baseline_steps * 0.1)
        calories_noise = self.random_state.normal(0, baseline_calories * 0.05)
        distance_noise = self.random_state.normal(0, baseline_distance * 0.1)
        active_noise = self.random_state.normal(0, baseline_active * 0.1)
        sleep_noise = self.random_state.normal(0, 5)
        stress_noise = self.random_state.normal(0, 0.5)
        
        current_steps += steps_noise
        current_calories += calories_noise
        current_distance += distance_noise
        current_active += active_noise
        current_sleep += sleep_noise
        current_stress += stress_noise
        
        # Emergency modifications
        if scenario_params.get('emergency_trigger', False):
            current_steps *= 0.3  # Reduced activity
            current_stress += 4  # High stress
            current_sleep -= 20  # Poor sleep
        
        # Ensure realistic bounds
        current_steps = max(0, min(30000, current_steps))
        current_calories = max(800, min(5000, current_calories))
        current_distance = max(0, min(50, current_distance))
        current_active = max(0, min(300, current_active))
        current_sleep = max(20, min(100, current_sleep))
        current_stress = max(1, min(10, current_stress))
        
        return {
            'steps': round(current_steps),
            'calories_burned': round(current_calories),
            'distance': round(current_distance, 1),
            'active_minutes': round(current_active),
            'sleep_quality': round(current_sleep),
            'stress_level': round(current_stress, 1)
        }
    
    def _generate_ecg_data(
        self,
        patient_profile: str,
        current_state: Dict[str, Any],
        circadian_factor: float,
        stress_factor: float,
        scenario_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate realistic ECG monitor data"""
        
        baseline_rr = current_state['baseline_values'].get('rr_interval', 800)
        baseline_qt = current_state['baseline_values'].get('qt_interval', 400)
        baseline_pr = current_state['baseline_values'].get('pr_interval', 160)
        baseline_qrs = current_state['baseline_values'].get('qrs_duration', 100)
        
        # Patient profile adjustments
        if patient_profile == 'elderly':
            baseline_pr += 20
            baseline_qrs += 10
        elif patient_profile == 'cardiac_patient':
            baseline_qt += 30
            baseline_pr += 15
            baseline_qrs += 15
        
        # Apply factors
        current_rr = baseline_rr / (circadian_factor * stress_factor)  # Inverse for heart rate
        current_qt = baseline_qt * (1 + (stress_factor - 1) * 0.1)
        current_pr = baseline_pr * (1 + (stress_factor - 1) * 0.05)
        current_qrs = baseline_qrs
        
        # Add noise
        rr_noise = self.random_state.normal(0, 30)
        qt_noise = self.random_state.normal(0, 10)
        pr_noise = self.random_state.normal(0, 5)
        qrs_noise = self.random_state.normal(0, 3)
        
        current_rr += rr_noise
        current_qt += qt_noise
        current_pr += pr_noise
        current_qrs += qrs_noise
        
        # Determine rhythm
        rhythm_options = ['normal_sinus', 'sinus_bradycardia', 'sinus_tachycardia', 'irregular']
        
        if current_rr > 1000:
            rhythm = 'sinus_bradycardia'
        elif current_rr < 600:
            rhythm = 'sinus_tachycardia'
        elif scenario_params.get('emergency_trigger', False) and random.random() < 0.3:
            rhythm = 'irregular'
        else:
            rhythm = 'normal_sinus'
        
        # Emergency modifications
        if scenario_params.get('emergency_trigger', False):
            if random.random() < 0.4:
                current_qt += random.uniform(50, 100)  # QT prolongation
                current_rr *= random.uniform(0.6, 1.4)  # Arrhythmia
        
        # Ensure realistic bounds
        current_rr = max(300, min(2000, current_rr))
        current_qt = max(300, min(600, current_qt))
        current_pr = max(100, min(300, current_pr))
        current_qrs = max(60, min(180, current_qrs))
        
        return {
            'heart_rhythm': rhythm,
            'rr_interval': round(current_rr),
            'qt_interval': round(current_qt),
            'pr_interval': round(current_pr),
            'qrs_duration': round(current_qrs),
            'lead_quality': random.uniform(0.85, 0.98)
        }
    
    def _generate_respiratory_data(
        self,
        patient_profile: str,
        current_state: Dict[str, Any],
        circadian_factor: float,
        stress_factor: float,
        scenario_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate realistic respiratory monitor data"""
        
        baseline_rr = current_state['baseline_values'].get('respiratory_rate', 16)
        baseline_tv = current_state['baseline_values'].get('tidal_volume', 500)
        baseline_mv = current_state['baseline_values'].get('minute_ventilation', 8.0)
        
        # Patient profile adjustments
        if patient_profile == 'elderly':
            baseline_rr += 2
            baseline_tv -= 50
        elif patient_profile == 'cardiac_patient':
            baseline_rr += 3
            baseline_tv -= 30
        elif patient_profile == 'post_surgery':
            baseline_rr += 4
            baseline_tv -= 100
        
        # Apply factors
        current_rr = baseline_rr * circadian_factor * stress_factor
        current_tv = baseline_tv * (2.0 - circadian_factor)  # Inverse relationship
        current_mv = (current_rr * current_tv) / 1000  # L/min
        
        # Add noise
        rr_noise = self.random_state.normal(0, 1)
        tv_noise = self.random_state.normal(0, 30)
        
        current_rr += rr_noise
        current_tv += tv_noise
        current_mv = (current_rr * current_tv) / 1000
        
        # Determine breathing pattern
        if stress_factor > 1.3 or scenario_params.get('emergency_trigger', False):
            if random.random() < 0.4:
                pattern = 'irregular'
            elif current_tv < 300:
                pattern = 'shallow'
            else:
                pattern = 'deep'
        else:
            pattern = 'regular'
        
        # Emergency modifications
        if scenario_params.get('emergency_trigger', False):
            current_rr *= random.uniform(1.5, 2.0)  # Tachypnea
            if random.random() < 0.3:
                current_tv *= 0.6  # Shallow breathing
        
        # Ensure realistic bounds
        current_rr = max(8, min(40, current_rr))
        current_tv = max(200, min(800, current_tv))
        current_mv = max(3, min(20, current_mv))
        
        return {
            'respiratory_rate': round(current_rr),
            'tidal_volume': round(current_tv),
            'minute_ventilation': round(current_mv, 1),
            'breathing_pattern': pattern,
            'sensor_contact': random.uniform(0.9, 1.0)
        }
    
    def update_device_state(
        self, 
        current_state: Dict[str, Any], 
        new_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update device state with new data for continuity"""[3]
        
        updated_state = current_state.copy()
        
        # Update last reading time
        updated_state['last_reading_time'] = new_data.get('timestamp', datetime.now(timezone.utc).isoformat())
        
        # Update baseline values with slight drift
        for key, value in new_data.items():
            if key in updated_state.get('baseline_values', {}):
                if isinstance(value, (int, float)):
                    # Apply small drift to baseline
                    drift_factor = updated_state.get('simulation_parameters', {}).get('drift_rate', 0.001)
                    drift = self.random_state.normal(0, abs(value) * drift_factor)
                    updated_state['baseline_values'][key] += drift
        
        # Update battery level (gradual decrease)
        if 'battery_level' in updated_state:
            battery_drain = random.uniform(0.001, 0.005)  # 0.1-0.5% per reading
            updated_state['battery_level'] = max(0.0, updated_state['battery_level'] - battery_drain)
        
        # Update signal strength (random fluctuation)
        if 'signal_strength' in updated_state:
            signal_change = self.random_state.normal(0, 0.02)
            updated_state['signal_strength'] = max(0.3, min(1.0, updated_state['signal_strength'] + signal_change))
        
        # Store previous values for trend calculation
        for key in ['glucose_level', 'heart_rate', 'systolic_pressure']:
            if key in new_data:
                updated_state[f'previous_{key}'] = new_data[key]
        
        return updated_state
