"""Data formatting utilities for HealthConnect AI"""

import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone
import re

logger = logging.getLogger(__name__)

class HealthDataFormatter:
    """Production-grade formatter for healthcare data"""
    
    def __init__(self):
        self.date_formats = {
            'iso8601': '%Y-%m-%dT%H:%M:%S.%fZ',
            'iso_date': '%Y-%m-%d',
            'us_date': '%m/%d/%Y',
            'display_datetime': '%Y-%m-%d %H:%M:%S UTC'
        }
    
    def format_health_record(self, health_record: Dict[str, Any]) -> Dict[str, Any]:
        """Format health record for API response"""
        try:
            formatted_record = {}
            
            # Format basic fields
            formatted_record['patient_id'] = health_record.get('patient_id')
            formatted_record['record_id'] = health_record.get('record_id')
            formatted_record['timestamp'] = self.format_timestamp(health_record.get('timestamp'))
            formatted_record['data_type'] = health_record.get('data_type')
            
            # Format vital signs
            if 'vital_signs' in health_record:
                formatted_record['vital_signs'] = self.format_vital_signs(health_record['vital_signs'])
            
            # Format symptoms
            if 'symptoms' in health_record:
                formatted_record['symptoms'] = self.format_symptoms(health_record['symptoms'])
            
            # Format medications
            if 'medications' in health_record:
                formatted_record['medications'] = self.format_medications(health_record['medications'])
            
            # Format metadata
            if 'metadata' in health_record:
                formatted_record['metadata'] = self.format_metadata(health_record['metadata'])
            
            return formatted_record
            
        except Exception as e:
            logger.error(f"Error formatting health record: {str(e)}")
            return health_record
    
    def format_vital_signs(self, vital_signs: Dict[str, Any]) -> Dict[str, Any]:
        """Format vital signs with units and ranges"""
        try:
            formatted_vitals = {}
            
            # Heart rate
            if 'heart_rate' in vital_signs:
                formatted_vitals['heart_rate'] = {
                    'value': vital_signs['heart_rate'],
                    'unit': 'bpm',
                    'normal_range': '60-100',
                    'status': self._get_vital_status('heart_rate', vital_signs['heart_rate'])
                }
            
            # Blood pressure
            if 'blood_pressure' in vital_signs:
                bp = vital_signs['blood_pressure']
                if isinstance(bp, dict) and 'systolic' in bp and 'diastolic' in bp:
                    formatted_vitals['blood_pressure'] = {
                        'systolic': {
                            'value': bp['systolic'],
                            'unit': 'mmHg'
                        },
                        'diastolic': {
                            'value': bp['diastolic'],
                            'unit': 'mmHg'
                        },
                        'display': f"{bp['systolic']}/{bp['diastolic']} mmHg",
                        'category': self._get_bp_category(bp['systolic'], bp['diastolic'])
                    }
            
            # Temperature
            if 'temperature' in vital_signs:
                temp_c = vital_signs['temperature']
                temp_f = (temp_c * 9/5) + 32
                formatted_vitals['temperature'] = {
                    'celsius': {
                        'value': round(temp_c, 1),
                        'unit': '°C'
                    },
                    'fahrenheit': {
                        'value': round(temp_f, 1),
                        'unit': '°F'
                    },
                    'status': self._get_vital_status('temperature', temp_c)
                }
            
            # Oxygen saturation
            if 'oxygen_saturation' in vital_signs:
                formatted_vitals['oxygen_saturation'] = {
                    'value': vital_signs['oxygen_saturation'],
                    'unit': '%',
                    'normal_range': '95-100%',
                    'status': self._get_vital_status('oxygen_saturation', vital_signs['oxygen_saturation'])
                }
            
            # Respiratory rate
            if 'respiratory_rate' in vital_signs:
                formatted_vitals['respiratory_rate'] = {
                    'value': vital_signs['respiratory_rate'],
                    'unit': 'breaths/min',
                    'normal_range': '12-20',
                    'status': self._get_vital_status('respiratory_rate', vital_signs['respiratory_rate'])
                }
            
            # Glucose level
            if 'glucose_level' in vital_signs:
                glucose_mg = vital_signs['glucose_level']
                glucose_mmol = glucose_mg * 0.0555  # Convert mg/dL to mmol/L
                formatted_vitals['glucose_level'] = {
                    'mg_dl': {
                        'value': glucose_mg,
                        'unit': 'mg/dL'
                    },
                    'mmol_l': {
                        'value': round(glucose_mmol, 1),
                        'unit': 'mmol/L'
                    },
                    'status': self._get_vital_status('glucose_level', glucose_mg)
                }
            
            return formatted_vitals
            
        except Exception as e:
            logger.error(f"Error formatting vital signs: {str(e)}")
            return vital_signs
    
    def format_symptoms(self, symptoms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format symptoms list"""
        try:
            formatted_symptoms = []
            
            for symptom in symptoms:
                formatted_symptom = {
                    'symptom': symptom.get('symptom', '').title(),
                    'severity': symptom.get('severity', '').title(),
                    'severity_score': self._get_severity_score(symptom.get('severity', '')),
                    'duration': symptom.get('duration', ''),
                    'onset': self.format_timestamp(symptom.get('onset'))
                }
                
                # Add severity color coding
                formatted_symptom['severity_color'] = self._get_severity_color(symptom.get('severity', ''))
                
                formatted_symptoms.append(formatted_symptom)
            
            # Sort by severity score (highest first)
            formatted_symptoms.sort(key=lambda x: x['severity_score'], reverse=True)
            
            return formatted_symptoms
            
        except Exception as e:
            logger.error(f"Error formatting symptoms: {str(e)}")
            return symptoms
    
    def format_medications(self, medications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format medications list"""
        try:
            formatted_medications = []
            
            for medication in medications:
                formatted_med = {
                    'name': medication.get('medication_name', '').title(),
                    'dosage': medication.get('dosage', ''),
                    'frequency': medication.get('frequency', ''),
                    'route': medication.get('route', '').title(),
                    'start_date': self.format_date(medication.get('start_date')),
                    'end_date': self.format_date(medication.get('end_date')),
                    'display_name': self._format_medication_display(medication)
                }
                
                # Add medication status
                formatted_med['status'] = self._get_medication_status(medication)
                
                formatted_medications.append(formatted_med)
            
            return formatted_medications
            
        except Exception as e:
            logger.error(f"Error formatting medications: {str(e)}")
            return medications
    
    def format_emergency_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Format emergency alert for display"""
        try:
            formatted_alert = {
                'alert_id': alert.get('alert_id'),
                'patient_id': alert.get('patient_id'),
                'alert_type': alert.get('alert_type', '').replace('_', ' ').title(),
                'urgency_level': alert.get('urgency_level'),
                'timestamp': self.format_timestamp(alert.get('timestamp')),
                'time_ago': self._get_time_ago(alert.get('timestamp')),
                'status': alert.get('status', 'active').title()
            }
            
            # Format urgency with color coding
            formatted_alert['urgency_display'] = {
                'level': alert.get('urgency_level'),
                'color': self._get_urgency_color(alert.get('urgency_level')),
                'icon': self._get_urgency_icon(alert.get('urgency_level'))
            }
            
            # Format health data if present
            if 'health_data' in alert:
                formatted_alert['health_data'] = self.format_vital_signs(alert['health_data'])
            
            # Format location if present
            if 'location' in alert:
                formatted_alert['location'] = self.format_location(alert['location'])
            
            return formatted_alert
            
        except Exception as e:
            logger.error(f"Error formatting emergency alert: {str(e)}")
            return alert
    
    def format_consultation_session(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Format consultation session for display"""
        try:
            formatted_session = {
                'session_id': session.get('session_id'),
                'patient_id': session.get('patient_id'),
                'provider_id': session.get('provider_id'),
                'consultation_type': session.get('consultation_type', '').replace('_', ' ').title(),
                'status': session.get('status', '').replace('_', ' ').title(),
                'urgency_level': session.get('urgency_level'),
                'created_at': self.format_timestamp(session.get('created_at')),
                'scheduled_time': self.format_timestamp(session.get('scheduled_time')),
                'started_at': self.format_timestamp(session.get('started_at')),
                'ended_at': self.format_timestamp(session.get('ended_at'))
            }
            
            # Calculate duration if session has started and ended
            if session.get('started_at') and session.get('ended_at'):
                formatted_session['duration'] = self._calculate_duration(
                    session['started_at'], session['ended_at']
                )
            
            # Format participants
            if 'participants' in session:
                formatted_session['participants'] = self.format_participants(session['participants'])
            
            # Format quality metrics
            if 'quality_metrics' in session:
                formatted_session['quality_metrics'] = self.format_quality_metrics(session['quality_metrics'])
            
            return formatted_session
            
        except Exception as e:
            logger.error(f"Error formatting consultation session: {str(e)}")
            return session
    
    def format_analytics_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Format analytics results for display"""
        try:
            formatted_results = {
                'analysis_id': results.get('analysis_id'),
                'analysis_type': results.get('analysis_type', '').replace('_', ' ').title(),
                'generated_at': self.format_timestamp(results.get('generated_at')),
                'time_ago': self._get_time_ago(results.get('generated_at'))
            }
            
            # Format population metrics
            if 'population_metrics' in results:
                formatted_results['population_metrics'] = self.format_population_metrics(
                    results['population_metrics']
                )
            
            # Format predictions
            if 'predictions' in results:
                formatted_results['predictions'] = self.format_predictions(results['predictions'])
            
            # Format insights
            if 'insights' in results:
                formatted_results['insights'] = self.format_insights(results['insights'])
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error formatting analytics results: {str(e)}")
            return results
    
    def format_timestamp(self, timestamp: Optional[str]) -> Optional[str]:
        """Format timestamp for display"""
        try:
            if not timestamp:
                return None
            
            # Parse timestamp
            if isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                return None
            
            # Format for display
            return dt.strftime(self.date_formats['display_datetime'])
            
        except Exception as e:
            logger.error(f"Error formatting timestamp: {str(e)}")
            return timestamp
    
    def format_date(self, date_value: Optional[str]) -> Optional[str]:
        """Format date for display"""
        try:
            if not date_value:
                return None
            
            # Parse date
            if isinstance(date_value, str):
                dt = datetime.strptime(date_value, '%Y-%m-%d')
                return dt.strftime('%B %d, %Y')  # e.g., "January 15, 2024"
            
            return date_value
            
        except Exception as e:
            logger.error(f"Error formatting date: {str(e)}")
            return date_value
    
    def _get_vital_status(self, vital_type: str, value: float) -> str:
        """Get status for vital sign value"""
        normal_ranges = {
            'heart_rate': {'low': 60, 'high': 100},
            'temperature': {'low': 36.1, 'high': 37.2},
            'oxygen_saturation': {'low': 95, 'high': 100},
            'respiratory_rate': {'low': 12, 'high': 20},
            'glucose_level': {'low': 70, 'high': 140}
        }
        
        if vital_type not in normal_ranges:
            return 'unknown'
        
        range_info = normal_ranges[vital_type]
        
        if value < range_info['low']:
            return 'low'
        elif value > range_info['high']:
            return 'high'
        else:
            return 'normal'
    
    def _get_bp_category(self, systolic: int, diastolic: int) -> str:
        """Get blood pressure category"""
        if systolic < 120 and diastolic < 80:
            return 'Normal'
        elif systolic < 130 and diastolic < 80:
            return 'Elevated'
        elif systolic < 140 or diastolic < 90:
            return 'Stage 1 Hypertension'
        elif systolic < 180 or diastolic < 120:
            return 'Stage 2 Hypertension'
        else:
            return 'Hypertensive Crisis'
    
    def _get_severity_score(self, severity: str) -> int:
        """Get numeric score for severity"""
        severity_scores = {
            'mild': 1,
            'moderate': 2,
            'severe': 3,
            'critical': 4
        }
        return severity_scores.get(severity.lower(), 0)
    
    def _get_severity_color(self, severity: str) -> str:
        """Get color code for severity"""
        severity_colors = {
            'mild': '#28a745',      # Green
            'moderate': '#ffc107',  # Yellow
            'severe': '#fd7e14',    # Orange
            'critical': '#dc3545'   # Red
        }
        return severity_colors.get(severity.lower(), '#6c757d')
    
    def _get_urgency_color(self, urgency: str) -> str:
        """Get color code for urgency level"""
        urgency_colors = {
            'LOW': '#28a745',       # Green
            'MEDIUM': '#ffc107',    # Yellow
            'HIGH': '#fd7e14',      # Orange
            'CRITICAL': '#dc3545'   # Red
        }
        return urgency_colors.get(urgency, '#6c757d')
    
    def _get_urgency_icon(self, urgency: str) -> str:
        """Get icon for urgency level"""
        urgency_icons = {
            'LOW': 'info-circle',
            'MEDIUM': 'exclamation-triangle',
            'HIGH': 'exclamation-circle',
            'CRITICAL': 'exclamation-triangle'
        }
        return urgency_icons.get(urgency, 'question-circle')
    
    def _format_medication_display(self, medication: Dict[str, Any]) -> str:
        """Format medication for display"""
        name = medication.get('medication_name', '')
        dosage = medication.get('dosage', '')
        frequency = medication.get('frequency', '')
        
        return f"{name} {dosage} {frequency}".strip()
    
    def _get_medication_status(self, medication: Dict[str, Any]) -> str:
        """Get medication status"""
        end_date = medication.get('end_date')
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                if end_dt < datetime.now():
                    return 'completed'
                else:
                    return 'active'
            except:
                return 'active'
        return 'active'
    
    def _get_time_ago(self, timestamp: Optional[str]) -> str:
        """Get human-readable time ago"""
        try:
            if not timestamp:
                return 'Unknown'
            
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            diff = now - dt
            
            seconds = diff.total_seconds()
            
            if seconds < 60:
                return 'Just now'
            elif seconds < 3600:
                minutes = int(seconds / 60)
                return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            elif seconds < 86400:
                hours = int(seconds / 3600)
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
            else:
                days = int(seconds / 86400)
                return f"{days} day{'s' if days != 1 else ''} ago"
                
        except Exception as e:
            logger.error(f"Error calculating time ago: {str(e)}")
            return 'Unknown'
    
    def _calculate_duration(self, start_time: str, end_time: str) -> str:
        """Calculate duration between two timestamps"""
        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            duration = end_dt - start_dt
            total_seconds = duration.total_seconds()
            
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = int(total_seconds % 60)
            
            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"
                
        except Exception as e:
            logger.error(f"Error calculating duration: {str(e)}")
            return 'Unknown'

# Global instance
health_formatter = HealthDataFormatter()
