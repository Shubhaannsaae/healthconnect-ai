import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import json

logger = logging.getLogger(__name__)

class EmergencyAlertSystem:
    """Production-grade emergency alert system for healthcare emergencies"""[2]
    
    def __init__(self):
        # Emergency response protocols based on medical standards
        self.response_protocols = {
            'CRITICAL': {
                'response_time_seconds': 60,
                'auto_call_ems': True,
                'notify_emergency_contacts': True,
                'alert_healthcare_providers': True,
                'require_immediate_consultation': True,
                'increase_monitoring': True,
                'send_sms': True,
                'send_email': True,
                'send_push': True,
                'escalation_levels': 3,
                'follow_up_intervals': [5, 15, 30]  # minutes
            },
            'HIGH': {
                'response_time_seconds': 180,
                'auto_call_ems': False,
                'notify_emergency_contacts': True,
                'alert_healthcare_providers': True,
                'require_immediate_consultation': True,
                'increase_monitoring': True,
                'send_sms': True,
                'send_email': True,
                'send_push': True,
                'escalation_levels': 2,
                'follow_up_intervals': [10, 30]
            },
            'MEDIUM': {
                'response_time_seconds': 600,
                'auto_call_ems': False,
                'notify_emergency_contacts': True,
                'alert_healthcare_providers': False,
                'require_immediate_consultation': False,
                'increase_monitoring': True,
                'send_sms': True,
                'send_email': False,
                'send_push': True,
                'escalation_levels': 1,
                'follow_up_intervals': [30]
            },
            'LOW': {
                'response_time_seconds': 1800,
                'auto_call_ems': False,
                'notify_emergency_contacts': False,
                'alert_healthcare_providers': False,
                'require_immediate_consultation': False,
                'increase_monitoring': False,
                'send_sms': False,
                'send_email': False,
                'send_push': True,
                'escalation_levels': 0,
                'follow_up_intervals': []
            }
        }
        
        # Medical emergency classifications
        self.emergency_classifications = {
            'cardiac_arrest': {
                'urgency_level': 'CRITICAL',
                'ems_required': True,
                'response_time_seconds': 30,
                'medical_code': 'Code Blue'
            },
            'stroke': {
                'urgency_level': 'CRITICAL',
                'ems_required': True,
                'response_time_seconds': 60,
                'medical_code': 'Code Stroke'
            },
            'severe_hypoglycemia': {
                'urgency_level': 'CRITICAL',
                'ems_required': True,
                'response_time_seconds': 90,
                'medical_code': 'Hypoglycemic Emergency'
            },
            'hypertensive_crisis': {
                'urgency_level': 'HIGH',
                'ems_required': False,
                'response_time_seconds': 180,
                'medical_code': 'Hypertensive Emergency'
            },
            'severe_hypotension': {
                'urgency_level': 'HIGH',
                'ems_required': True,
                'response_time_seconds': 120,
                'medical_code': 'Shock Protocol'
            },
            'respiratory_distress': {
                'urgency_level': 'HIGH',
                'ems_required': True,
                'response_time_seconds': 90,
                'medical_code': 'Respiratory Emergency'
            },
            'severe_hypoxemia': {
                'urgency_level': 'CRITICAL',
                'ems_required': True,
                'response_time_seconds': 60,
                'medical_code': 'Oxygen Emergency'
            },
            'diabetic_ketoacidosis': {
                'urgency_level': 'HIGH',
                'ems_required': True,
                'response_time_seconds': 180,
                'medical_code': 'DKA Protocol'
            },
            'severe_arrhythmia': {
                'urgency_level': 'CRITICAL',
                'ems_required': True,
                'response_time_seconds': 45,
                'medical_code': 'Cardiac Emergency'
            },
            'hyperthermia': {
                'urgency_level': 'HIGH',
                'ems_required': False,
                'response_time_seconds': 300,
                'medical_code': 'Heat Emergency'
            }
        }
    
    def determine_response_protocol(
        self, 
        urgency_level: str, 
        alert_type: str, 
        health_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Determine appropriate response protocol based on emergency parameters"""[2]
        
        try:
            # Get base protocol for urgency level
            base_protocol = self.response_protocols.get(urgency_level, self.response_protocols['MEDIUM'])
            protocol = base_protocol.copy()
            
            # Classify emergency type based on health data
            emergency_classification = self._classify_emergency(health_data, alert_type)
            
            if emergency_classification:
                # Override protocol settings based on specific emergency type
                classification_data = self.emergency_classifications[emergency_classification]
                
                if classification_data['ems_required']:
                    protocol['auto_call_ems'] = True
                
                if classification_data['response_time_seconds'] < protocol['response_time_seconds']:
                    protocol['response_time_seconds'] = classification_data['response_time_seconds']
                
                protocol['emergency_classification'] = emergency_classification
                protocol['medical_code'] = classification_data['medical_code']
            
            # Add contextual modifications
            protocol = self._apply_contextual_modifications(protocol, health_data, alert_type)
            
            # Add timestamp and metadata
            protocol['determined_at'] = datetime.now(timezone.utc).isoformat()
            protocol['protocol_version'] = '2024.1'
            
            logger.info(f"Response protocol determined: {urgency_level} - {emergency_classification}")
            
            return protocol
            
        except Exception as e:
            logger.error(f"Error determining response protocol: {str(e)}")
            # Return safe default protocol
            return self.response_protocols['HIGH']
    
    def _classify_emergency(self, health_data: Dict[str, Any], alert_type: str) -> Optional[str]:
        """Classify emergency type based on health data patterns"""
        
        try:
            # Cardiac emergencies
            if 'heart_rate' in health_data:
                hr = health_data['heart_rate']
                if hr < 30 or hr > 180:
                    return 'cardiac_arrest'
                elif hr < 40 or hr > 150:
                    return 'severe_arrhythmia'
            
            # Blood pressure emergencies
            if 'blood_pressure' in health_data:
                bp = health_data['blood_pressure']
                systolic = bp.get('systolic', 120)
                diastolic = bp.get('diastolic', 80)
                
                if systolic > 220 or diastolic > 130:
                    return 'hypertensive_crisis'
                elif systolic < 70 or diastolic < 40:
                    return 'severe_hypotension'
            
            # Glucose emergencies
            if 'glucose_level' in health_data:
                glucose = health_data['glucose_level']
                if glucose < 40:
                    return 'severe_hypoglycemia'
                elif glucose > 500:
                    return 'diabetic_ketoacidosis'
            
            # Oxygen emergencies
            if 'oxygen_saturation' in health_data:
                spo2 = health_data['oxygen_saturation']
                if spo2 < 80:
                    return 'severe_hypoxemia'
            
            # Respiratory emergencies
            if 'respiratory_rate' in health_data:
                rr = health_data['respiratory_rate']
                if rr < 6 or rr > 35:
                    return 'respiratory_distress'
            
            # Temperature emergencies
            if 'core_temperature' in health_data:
                temp = health_data['core_temperature']
                if temp > 41.0:
                    return 'hyperthermia'
            
            # ECG-based emergencies
            if 'heart_rhythm' in health_data:
                rhythm = health_data['heart_rhythm']
                if rhythm in ['ventricular_fibrillation', 'ventricular_tachycardia', 'asystole']:
                    return 'cardiac_arrest'
                elif rhythm == 'atrial_fibrillation' and 'heart_rate' in health_data:
                    if health_data['heart_rate'] > 150:
                        return 'severe_arrhythmia'
            
            # Stroke indicators (would need more sophisticated analysis in production)
            if alert_type == 'neurological' or 'confusion' in str(health_data).lower():
                return 'stroke'
            
            return None
            
        except Exception as e:
            logger.error(f"Error classifying emergency: {str(e)}")
            return None
    
    def _apply_contextual_modifications(
        self, 
        protocol: Dict[str, Any], 
        health_data: Dict[str, Any], 
        alert_type: str
    ) -> Dict[str, Any]:
        """Apply contextual modifications to response protocol"""
        
        try:
            # Multiple abnormal vitals increase urgency
            abnormal_count = self._count_abnormal_vitals(health_data)
            if abnormal_count >= 3:
                protocol['escalation_levels'] += 1
                protocol['response_time_seconds'] = max(30, protocol['response_time_seconds'] // 2)
                protocol['require_immediate_consultation'] = True
            
            # Device-specific modifications
            if alert_type == 'device_reading':
                # Increase monitoring for device alerts
                protocol['increase_monitoring'] = True
                protocol['monitoring_duration_minutes'] = 120
            
            # Time-based modifications
            current_hour = datetime.now().hour
            if 22 <= current_hour or current_hour <= 6:  # Night hours
                protocol['night_protocol'] = True
                protocol['escalation_levels'] += 1
                if not protocol.get('auto_call_ems', False):
                    protocol['alert_healthcare_providers'] = True
            
            # Age-based modifications (would get from patient profile in production)
            # For hackathon, we simulate based on baseline vitals
            if self._is_elderly_patient(health_data):
                protocol['elderly_patient'] = True
                protocol['escalation_levels'] += 1
                protocol['follow_up_intervals'] = [interval // 2 for interval in protocol['follow_up_intervals']]
            
            return protocol
            
        except Exception as e:
            logger.error(f"Error applying contextual modifications: {str(e)}")
            return protocol
    
    def _count_abnormal_vitals(self, health_data: Dict[str, Any]) -> int:
        """Count number of abnormal vital signs"""
        
        abnormal_count = 0
        
        # Heart rate
        if 'heart_rate' in health_data:
            hr = health_data['heart_rate']
            if hr < 50 or hr > 120:
                abnormal_count += 1
        
        # Blood pressure
        if 'blood_pressure' in health_data:
            bp = health_data['blood_pressure']
            systolic = bp.get('systolic', 120)
            diastolic = bp.get('diastolic', 80)
            if systolic > 160 or systolic < 90 or diastolic > 100 or diastolic < 60:
                abnormal_count += 1
        
        # Temperature
        if 'core_temperature' in health_data:
            temp = health_data['core_temperature']
            if temp > 38.5 or temp < 35.5:
                abnormal_count += 1
        
        # Oxygen saturation
        if 'oxygen_saturation' in health_data:
            spo2 = health_data['oxygen_saturation']
            if spo2 < 92:
                abnormal_count += 1
        
        # Respiratory rate
        if 'respiratory_rate' in health_data:
            rr = health_data['respiratory_rate']
            if rr < 10 or rr > 24:
                abnormal_count += 1
        
        # Glucose
        if 'glucose_level' in health_data:
            glucose = health_data['glucose_level']
            if glucose < 70 or glucose > 200:
                abnormal_count += 1
        
        return abnormal_count
    
    def _is_elderly_patient(self, health_data: Dict[str, Any]) -> bool:
        """Determine if patient is elderly based on health data patterns"""
        
        # In production, this would check patient age from profile
        # For hackathon, we use health data patterns as proxy
        
        elderly_indicators = 0
        
        # Lower baseline heart rate
        if 'heart_rate' in health_data and health_data['heart_rate'] < 65:
            elderly_indicators += 1
        
        # Higher baseline blood pressure
        if 'blood_pressure' in health_data:
            bp = health_data['blood_pressure']
            if bp.get('systolic', 120) > 140:
                elderly_indicators += 1
        
        # Lower activity levels
        if 'steps' in health_data and health_data['steps'] < 3000:
            elderly_indicators += 1
        
        return elderly_indicators >= 2
    
    def calculate_risk_score(self, health_data: Dict[str, Any], alert_type: str) -> float:
        """Calculate comprehensive risk score for emergency assessment"""
        
        try:
            risk_score = 0.0
            
            # Vital signs risk assessment
            vital_risk = self._assess_vital_signs_risk(health_data)
            risk_score += vital_risk * 0.4
            
            # Trend analysis risk
            trend_risk = self._assess_trend_risk(health_data)
            risk_score += trend_risk * 0.3
            
            # Combination risk (multiple abnormal values)
            combination_risk = self._assess_combination_risk(health_data)
            risk_score += combination_risk * 0.2
            
            # Alert type specific risk
            type_risk = self._assess_alert_type_risk(alert_type)
            risk_score += type_risk * 0.1
            
            # Normalize to 0-1 range
            risk_score = min(1.0, max(0.0, risk_score))
            
            return round(risk_score, 3)
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {str(e)}")
            return 0.5  # Default moderate risk
    
    def _assess_vital_signs_risk(self, health_data: Dict[str, Any]) -> float:
        """Assess risk based on individual vital signs"""
        
        max_risk = 0.0
        
        # Heart rate risk
        if 'heart_rate' in health_data:
            hr = health_data['heart_rate']
            if hr < 30 or hr > 180:
                max_risk = max(max_risk, 1.0)
            elif hr < 40 or hr > 150:
                max_risk = max(max_risk, 0.8)
            elif hr < 50 or hr > 120:
                max_risk = max(max_risk, 0.4)
        
        # Blood pressure risk
        if 'blood_pressure' in health_data:
            bp = health_data['blood_pressure']
            systolic = bp.get('systolic', 120)
            diastolic = bp.get('diastolic', 80)
            
            if systolic > 220 or diastolic > 130 or systolic < 70:
                max_risk = max(max_risk, 1.0)
            elif systolic > 180 or diastolic > 110 or systolic < 90:
                max_risk = max(max_risk, 0.7)
            elif systolic > 160 or diastolic > 100:
                max_risk = max(max_risk, 0.4)
        
        # Temperature risk
        if 'core_temperature' in health_data:
            temp = health_data['core_temperature']
            if temp > 41.0 or temp < 34.0:
                max_risk = max(max_risk, 1.0)
            elif temp > 39.5 or temp < 35.0:
                max_risk = max(max_risk, 0.6)
            elif temp > 38.5 or temp < 36.0:
                max_risk = max(max_risk, 0.3)
        
        # Oxygen saturation risk
        if 'oxygen_saturation' in health_data:
            spo2 = health_data['oxygen_saturation']
            if spo2 < 80:
                max_risk = max(max_risk, 1.0)
            elif spo2 < 88:
                max_risk = max(max_risk, 0.8)
            elif spo2 < 92:
                max_risk = max(max_risk, 0.4)
        
        return max_risk
    
    def _assess_trend_risk(self, health_data: Dict[str, Any]) -> float:
        """Assess risk based on trends in health data"""
        
        trend_risk = 0.0
        
        # Glucose trend risk
        if 'glucose_trend' in health_data:
            trend = health_data['glucose_trend']
            if trend in ['falling_rapidly', 'rising_rapidly']:
                trend_risk += 0.6
            elif trend in ['falling', 'rising']:
                trend_risk += 0.3
        
        # Heart rate variability trend
        if 'heart_rate_variability' in health_data:
            hrv = health_data['heart_rate_variability']
            if hrv < 15:  # Very low HRV indicates stress
                trend_risk += 0.4
        
        # Blood pressure trend (if multiple readings available)
        if 'blood_pressure_trend' in health_data:
            bp_trend = health_data['blood_pressure_trend']
            if bp_trend == 'rapidly_increasing':
                trend_risk += 0.5
        
        return min(1.0, trend_risk)
    
    def _assess_combination_risk(self, health_data: Dict[str, Any]) -> float:
        """Assess risk based on combination of abnormal values"""
        
        abnormal_count = self._count_abnormal_vitals(health_data)
        
        if abnormal_count >= 4:
            return 1.0
        elif abnormal_count == 3:
            return 0.7
        elif abnormal_count == 2:
            return 0.4
        elif abnormal_count == 1:
            return 0.2
        else:
            return 0.0
    
    def _assess_alert_type_risk(self, alert_type: str) -> float:
        """Assess risk based on alert type"""
        
        high_risk_types = ['device_reading', 'ai_analysis', 'manual_trigger']
        medium_risk_types = ['scheduled_check', 'trend_analysis']
        
        if alert_type in high_risk_types:
            return 0.8
        elif alert_type in medium_risk_types:
            return 0.4
        else:
            return 0.2
    
    def generate_emergency_summary(
        self, 
        alert_record: Dict[str, Any], 
        protocol: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive emergency summary for responders"""[2]
        
        try:
            summary = {
                'alert_id': alert_record['alert_id'],
                'patient_id': alert_record['patient_id'],
                'emergency_classification': protocol.get('emergency_classification', 'unclassified'),
                'medical_code': protocol.get('medical_code', 'General Emergency'),
                'urgency_level': alert_record['urgency_level'],
                'risk_score': self.calculate_risk_score(
                    alert_record.get('health_data', {}), 
                    alert_record['alert_type']
                ),
                'critical_vitals': self._extract_critical_vitals(alert_record.get('health_data', {})),
                'recommended_actions': self._generate_recommended_actions(protocol),
                'estimated_response_time': f"{protocol['response_time_seconds']} seconds",
                'ems_required': protocol.get('auto_call_ems', False),
                'consultation_required': protocol.get('require_immediate_consultation', False),
                'monitoring_instructions': self._generate_monitoring_instructions(protocol),
                'escalation_plan': self._generate_escalation_plan(protocol),
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating emergency summary: {str(e)}")
            return {
                'alert_id': alert_record.get('alert_id', 'unknown'),
                'error': 'Failed to generate emergency summary',
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
    
    def _extract_critical_vitals(self, health_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract critical vital signs from health data"""
        
        critical_vitals = []
        
        # Define critical thresholds
        critical_thresholds = {
            'heart_rate': {'min': 40, 'max': 150},
            'systolic_pressure': {'min': 80, 'max': 200},
            'diastolic_pressure': {'min': 50, 'max': 120},
            'core_temperature': {'min': 35.0, 'max': 39.5},
            'oxygen_saturation': {'min': 88, 'max': 100},
            'respiratory_rate': {'min': 8, 'max': 30},
            'glucose_level': {'min': 60, 'max': 300}
        }
        
        for vital, thresholds in critical_thresholds.items():
            if vital in health_data:
                value = health_data[vital]
                if vital == 'systolic_pressure' and 'blood_pressure' in health_data:
                    value = health_data['blood_pressure'].get('systolic')
                elif vital == 'diastolic_pressure' and 'blood_pressure' in health_data:
                    value = health_data['blood_pressure'].get('diastolic')
                
                if value and (value < thresholds['min'] or value > thresholds['max']):
                    critical_vitals.append({
                        'vital_sign': vital,
                        'value': value,
                        'normal_range': f"{thresholds['min']}-{thresholds['max']}",
                        'severity': 'critical' if (
                            value < thresholds['min'] * 0.8 or 
                            value > thresholds['max'] * 1.2
                        ) else 'abnormal'
                    })
        
        return critical_vitals
    
    def _generate_recommended_actions(self, protocol: Dict[str, Any]) -> List[str]:
        """Generate recommended immediate actions"""
        
        actions = []
        
        if protocol.get('auto_call_ems', False):
            actions.append("Call Emergency Medical Services (911) immediately")
        
        if protocol.get('require_immediate_consultation', False):
            actions.append("Initiate immediate medical consultation")
        
        if protocol.get('notify_emergency_contacts', False):
            actions.append("Notify emergency contacts")
        
        if protocol.get('increase_monitoring', False):
            actions.append("Increase patient monitoring frequency")
        
        if protocol.get('emergency_classification'):
            classification = protocol['emergency_classification']
            if classification == 'cardiac_arrest':
                actions.extend([
                    "Begin CPR if patient is unresponsive",
                    "Prepare AED if available",
                    "Ensure airway is clear"
                ])
            elif classification == 'stroke':
                actions.extend([
                    "Note time of symptom onset",
                    "Perform FAST assessment",
                    "Do not give food or water"
                ])
            elif classification == 'severe_hypoglycemia':
                actions.extend([
                    "Administer glucose if patient is conscious",
                    "Do not give insulin",
                    "Monitor consciousness level"
                ])
        
        # Add general emergency actions
        actions.extend([
            "Stay with patient",
            "Monitor vital signs continuously",
            "Document all observations",
            "Prepare for emergency transport if needed"
        ])
        
        return actions
    
    def _generate_monitoring_instructions(self, protocol: Dict[str, Any]) -> Dict[str, Any]:
        """Generate monitoring instructions"""
        
        instructions = {
            'frequency': 'every 5 minutes' if protocol.get('increase_monitoring') else 'every 15 minutes',
            'duration': f"{protocol.get('monitoring_duration_minutes', 60)} minutes",
            'parameters': [
                'Heart rate and rhythm',
                'Blood pressure',
                'Respiratory rate',
                'Oxygen saturation',
                'Level of consciousness',
                'Temperature'
            ],
            'alert_conditions': [
                'Any vital sign deterioration',
                'Loss of consciousness',
                'Difficulty breathing',
                'Chest pain',
                'Severe headache',
                'Confusion or disorientation'
            ]
        }
        
        return instructions
    
    def _generate_escalation_plan(self, protocol: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate escalation plan"""
        
        escalation_plan = []
        
        for level in range(1, protocol.get('escalation_levels', 1) + 1):
            if level == 1:
                escalation_plan.append({
                    'level': 1,
                    'trigger': 'Initial alert',
                    'actions': ['Notify emergency contacts', 'Begin monitoring'],
                    'timeframe': 'Immediate'
                })
            elif level == 2:
                escalation_plan.append({
                    'level': 2,
                    'trigger': 'No improvement in 10 minutes',
                    'actions': ['Alert healthcare providers', 'Consider EMS'],
                    'timeframe': '10 minutes'
                })
            elif level == 3:
                escalation_plan.append({
                    'level': 3,
                    'trigger': 'Deterioration or no response',
                    'actions': ['Call EMS immediately', 'Prepare for transport'],
                    'timeframe': '15 minutes'
                })
        
        return escalation_plan
