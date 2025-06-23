import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
import boto3
from botocore.exceptions import ClientError
import uuid

logger = logging.getLogger(__name__)

class ConsultationSessionManager:
    """Production-grade consultation session manager for healthcare video calls"""
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.eventbridge = boto3.client('events')
        self.bedrock_runtime = boto3.client('bedrock-runtime')
        
        # Environment variables
        self.sessions_table_name = os.environ.get('CONSULTATION_SESSIONS_TABLE')
        self.providers_table_name = os.environ.get('HEALTHCARE_PROVIDERS_TABLE')
        self.event_bus_name = os.environ.get('EVENT_BUS_NAME')
        
        # Session status definitions
        self.session_statuses = {
            'created': 'Session created, waiting for provider assignment',
            'queued': 'Session queued, waiting for available provider',
            'provider_assigned': 'Provider assigned, waiting for connection',
            'connecting': 'Participants connecting to session',
            'active': 'Session active with participants connected',
            'paused': 'Session temporarily paused',
            'ended': 'Session completed normally',
            'cancelled': 'Session cancelled before completion',
            'failed': 'Session failed due to technical issues'
        }
        
        # Consultation types and their characteristics
        self.consultation_types = {
            'emergency': {
                'max_duration_minutes': 60,
                'priority': 1,
                'required_provider_level': 'emergency_physician',
                'auto_recording': True,
                'requires_immediate_response': True
            },
            'urgent': {
                'max_duration_minutes': 45,
                'priority': 2,
                'required_provider_level': 'physician',
                'auto_recording': True,
                'requires_immediate_response': False
            },
            'routine': {
                'max_duration_minutes': 30,
                'priority': 3,
                'required_provider_level': 'nurse_practitioner',
                'auto_recording': False,
                'requires_immediate_response': False
            },
            'follow_up': {
                'max_duration_minutes': 20,
                'priority': 4,
                'required_provider_level': 'nurse',
                'auto_recording': False,
                'requires_immediate_response': False
            },
            'mental_health': {
                'max_duration_minutes': 60,
                'priority': 3,
                'required_provider_level': 'mental_health_professional',
                'auto_recording': False,
                'requires_immediate_response': False
            },
            'specialist': {
                'max_duration_minutes': 45,
                'priority': 3,
                'required_provider_level': 'specialist',
                'auto_recording': True,
                'requires_immediate_response': False
            }
        }
    
    def create_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new consultation session"""
        try:
            # Generate unique session ID
            session_id = str(uuid.uuid4())
            
            # Get consultation type configuration
            consultation_type = session_data.get('consultation_type', 'routine')
            type_config = self.consultation_types.get(consultation_type, self.consultation_types['routine'])
            
            # Create session record
            session_record = {
                'session_id': session_id,
                'patient_id': session_data['patient_id'],
                'consultation_type': consultation_type,
                'urgency_level': session_data.get('urgency_level', 'MEDIUM'),
                'status': 'created',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat(),
                'scheduled_time': session_data.get('scheduled_time'),
                'estimated_duration': type_config['max_duration_minutes'],
                'max_duration': type_config['max_duration_minutes'],
                'priority': type_config['priority'],
                'required_provider_level': type_config['required_provider_level'],
                'auto_recording': type_config['auto_recording'],
                'consultation_mode': session_data.get('consultation_mode', 'video'),
                'language_preference': session_data.get('language_preference', 'en'),
                'symptoms': session_data.get('symptoms', []),
                'health_data': session_data.get('health_data', {}),
                'auto_triggered': session_data.get('auto_triggered', False),
                'emergency_context': session_data.get('emergency_context', {}),
                'session_metadata': {
                    'created_by': 'system' if session_data.get('auto_triggered') else 'patient',
                    'creation_source': session_data.get('source', 'web_app'),
                    'device_info': session_data.get('device_info', {}),
                    'network_info': session_data.get('network_info', {})
                },
                'participants': [],
                'session_events': [],
                'quality_metrics': {},
                'ttl': int(datetime.now().timestamp()) + 2592000  # 30 days TTL
            }
            
            # Add initial session event
            session_record['session_events'].append({
                'event_type': 'session_created',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'details': {
                    'consultation_type': consultation_type,
                    'urgency_level': session_record['urgency_level']
                }
            })
            
            # Store session in DynamoDB
            table = self.dynamodb.Table(self.sessions_table_name)
            table.put_item(Item=session_record)
            
            # Send session created event
            self._send_session_event(session_record, 'session_created')
            
            # Generate AI-powered session preparation if health data available
            if session_record['health_data']:
                preparation_result = self._generate_session_preparation(session_record)
                if preparation_result:
                    session_record['ai_preparation'] = preparation_result
                    self.update_session(session_record)
            
            logger.info(f"Created consultation session: {session_id}")
            
            return {
                'success': True,
                'session': session_record
            }
            
        except Exception as e:
            logger.error(f"Error creating consultation session: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get consultation session by ID"""
        try:
            table = self.dynamodb.Table(self.sessions_table_name)
            
            response = table.get_item(Key={'session_id': session_id})
            
            if 'Item' in response:
                return response['Item']
            else:
                logger.warning(f"Session not found: {session_id}")
                return None
                
        except ClientError as e:
            logger.error(f"Error getting session {session_id}: {str(e)}")
            return None
    
    def update_session(self, session_data: Dict[str, Any]) -> bool:
        """Update consultation session"""
        try:
            session_data['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            table = self.dynamodb.Table(self.sessions_table_name)
            table.put_item(Item=session_data)
            
            # Send session updated event
            self._send_session_event(session_data, 'session_updated')
            
            logger.info(f"Updated consultation session: {session_data['session_id']}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating session: {str(e)}")
            return False
    
    def start_session(self, session_id: str, provider_id: str) -> Dict[str, Any]:
        """Start consultation session"""
        try:
            session = self.get_session(session_id)
            if not session:
                return {'success': False, 'error': 'Session not found'}
            
            # Update session status
            session['status'] = 'active'
            session['provider_id'] = provider_id
            session['started_at'] = datetime.now(timezone.utc).isoformat()
            session['actual_start_time'] = datetime.now(timezone.utc).isoformat()
            
            # Add session event
            session['session_events'].append({
                'event_type': 'session_started',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'details': {
                    'provider_id': provider_id,
                    'start_method': 'provider_initiated'
                }
            })
            
            # Initialize quality metrics
            session['quality_metrics'] = {
                'start_time': datetime.now(timezone.utc).isoformat(),
                'connection_quality': {},
                'audio_quality': {},
                'video_quality': {},
                'participant_feedback': {}
            }
            
            # Update session
            self.update_session(session)
            
            # Send session started event
            self._send_session_event(session, 'session_started')
            
            # Start session monitoring
            self._start_session_monitoring(session_id)
            
            logger.info(f"Started consultation session: {session_id} with provider: {provider_id}")
            
            return {
                'success': True,
                'session': session
            }
            
        except Exception as e:
            logger.error(f"Error starting session: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def end_session(self, session_id: str, ended_by: str, reason: str = 'completed') -> Dict[str, Any]:
        """End consultation session"""
        try:
            session = self.get_session(session_id)
            if not session:
                return {'success': False, 'error': 'Session not found'}
            
            # Calculate session duration
            if session.get('started_at'):
                start_time = datetime.fromisoformat(session['started_at'].replace('Z', '+00:00'))
                end_time = datetime.now(timezone.utc)
                duration_seconds = (end_time - start_time).total_seconds()
            else:
                duration_seconds = 0
            
            # Update session status
            session['status'] = 'ended'
            session['ended_at'] = datetime.now(timezone.utc).isoformat()
            session['ended_by'] = ended_by
            session['end_reason'] = reason
            session['actual_duration_seconds'] = duration_seconds
            session['actual_duration_minutes'] = round(duration_seconds / 60, 2)
            
            # Add session event
            session['session_events'].append({
                'event_type': 'session_ended',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'details': {
                    'ended_by': ended_by,
                    'reason': reason,
                    'duration_seconds': duration_seconds
                }
            })
            
            # Finalize quality metrics
            if 'quality_metrics' in session:
                session['quality_metrics']['end_time'] = datetime.now(timezone.utc).isoformat()
                session['quality_metrics']['total_duration_seconds'] = duration_seconds
            
            # Update session
            self.update_session(session)
            
            # Send session ended event
            self._send_session_event(session, 'session_ended')
            
            # Generate session summary
            summary_result = self._generate_session_summary(session)
            if summary_result:
                session['session_summary'] = summary_result
                self.update_session(session)
            
            # Update provider availability
            if session.get('provider_id'):
                self._update_provider_availability(session['provider_id'], 'available')
            
            logger.info(f"Ended consultation session: {session_id} (Duration: {duration_seconds}s)")
            
            return {
                'success': True,
                'session': session,
                'duration_seconds': duration_seconds
            }
            
        except Exception as e:
            logger.error(f"Error ending session: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def add_participant(self, session_id: str, participant_data: Dict[str, Any]) -> bool:
        """Add participant to consultation session"""
        try:
            session = self.get_session(session_id)
            if not session:
                return False
            
            # Add participant
            participant = {
                'user_id': participant_data['user_id'],
                'user_type': participant_data['user_type'],  # patient, provider, observer
                'connection_id': participant_data.get('connection_id'),
                'joined_at': datetime.now(timezone.utc).isoformat(),
                'device_info': participant_data.get('device_info', {}),
                'network_info': participant_data.get('network_info', {}),
                'permissions': participant_data.get('permissions', {
                    'can_speak': True,
                    'can_video': True,
                    'can_share_screen': participant_data['user_type'] == 'provider',
                    'can_record': participant_data['user_type'] == 'provider'
                })
            }
            
            session['participants'].append(participant)
            
            # Add session event
            session['session_events'].append({
                'event_type': 'participant_joined',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'details': {
                    'user_id': participant_data['user_id'],
                    'user_type': participant_data['user_type']
                }
            })
            
            # Update session
            self.update_session(session)
            
            logger.info(f"Added participant {participant_data['user_id']} to session {session_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding participant: {str(e)}")
            return False
    
    def remove_participant(self, session_id: str, user_id: str) -> bool:
        """Remove participant from consultation session"""
        try:
            session = self.get_session(session_id)
            if not session:
                return False
            
            # Find and remove participant
            participants = session.get('participants', [])
            session['participants'] = [p for p in participants if p['user_id'] != user_id]
            
            # Add session event
            session['session_events'].append({
                'event_type': 'participant_left',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'details': {
                    'user_id': user_id
                }
            })
            
            # Update session
            self.update_session(session)
            
            logger.info(f"Removed participant {user_id} from session {session_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error removing participant: {str(e)}")
            return False
    
    def update_quality_metrics(self, session_id: str, metrics: Dict[str, Any]) -> bool:
        """Update session quality metrics"""
        try:
            session = self.get_session(session_id)
            if not session:
                return False
            
            if 'quality_metrics' not in session:
                session['quality_metrics'] = {}
            
            # Update metrics
            session['quality_metrics'].update(metrics)
            session['quality_metrics']['last_updated'] = datetime.now(timezone.utc).isoformat()
            
            # Update session
            self.update_session(session)
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating quality metrics: {str(e)}")
            return False
    
    def _generate_session_preparation(self, session: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate AI-powered session preparation"""
        try:
            health_data = session.get('health_data', {})
            symptoms = session.get('symptoms', [])
            consultation_type = session.get('consultation_type', 'routine')
            
            if not health_data and not symptoms:
                return None
            
            # Prepare prompt for Bedrock
            prompt = f"""
            Analyze the following patient data and provide consultation preparation recommendations:
            
            Consultation Type: {consultation_type}
            Patient Symptoms: {json.dumps(symptoms)}
            Health Data: {json.dumps(health_data)}
            
            Please provide:
            1. Key areas to focus on during consultation
            2. Recommended questions to ask
            3. Potential diagnoses to consider
            4. Suggested tests or examinations
            5. Red flags to watch for
            
            Format as JSON with clear sections.
            """
            
            # Call Bedrock
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "temperature": 0.1,
                "messages": [{"role": "user", "content": prompt}],
                "system": "You are a medical AI assistant helping healthcare providers prepare for patient consultations."
            }
            
            response = self.bedrock_runtime.invoke_model(
                modelId=os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0'),
                body=json.dumps(request_body),
                contentType='application/json',
                accept='application/json'
            )
            
            response_body = json.loads(response['body'].read())
            preparation_content = response_body['content'][0]['text']
            
            return {
                'preparation_content': preparation_content,
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'model_used': os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')
            }
            
        except Exception as e:
            logger.error(f"Error generating session preparation: {str(e)}")
            return None
    
    def _generate_session_summary(self, session: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate AI-powered session summary"""
        try:
            # Prepare session data for summary
            session_data = {
                'duration_minutes': session.get('actual_duration_minutes', 0),
                'consultation_type': session.get('consultation_type'),
                'participants': len(session.get('participants', [])),
                'quality_metrics': session.get('quality_metrics', {}),
                'session_events': session.get('session_events', [])
            }
            
            # Generate summary using Bedrock
            prompt = f"""
            Generate a consultation session summary based on the following data:
            
            Session Data: {json.dumps(session_data)}
            
            Please provide:
            1. Session overview
            2. Key metrics and statistics
            3. Quality assessment
            4. Recommendations for improvement
            
            Format as JSON with clear sections.
            """
            
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1500,
                "temperature": 0.1,
                "messages": [{"role": "user", "content": prompt}],
                "system": "You are a medical AI assistant generating consultation session summaries."
            }
            
            response = self.bedrock_runtime.invoke_model(
                modelId=os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0'),
                body=json.dumps(request_body),
                contentType='application/json',
                accept='application/json'
            )
            
            response_body = json.loads(response['body'].read())
            summary_content = response_body['content'][0]['text']
            
            return {
                'summary_content': summary_content,
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'session_duration_minutes': session.get('actual_duration_minutes', 0),
                'quality_score': self._calculate_session_quality_score(session)
            }
            
        except Exception as e:
            logger.error(f"Error generating session summary: {str(e)}")
            return None
    
    def _calculate_session_quality_score(self, session: Dict[str, Any]) -> float:
        """Calculate overall session quality score"""
        try:
            quality_metrics = session.get('quality_metrics', {})
            
            # Base score
            score = 0.8
            
            # Adjust based on connection quality
            connection_quality = quality_metrics.get('connection_quality', {})
            if connection_quality.get('average_latency', 0) > 200:
                score -= 0.1
            if connection_quality.get('packet_loss', 0) > 0.05:
                score -= 0.1
            
            # Adjust based on audio/video quality
            audio_quality = quality_metrics.get('audio_quality', {})
            video_quality = quality_metrics.get('video_quality', {})
            
            if audio_quality.get('average_quality', 1.0) < 0.7:
                score -= 0.1
            if video_quality.get('average_quality', 1.0) < 0.7:
                score -= 0.1
            
            # Adjust based on session completion
            if session.get('end_reason') == 'completed':
                score += 0.1
            elif session.get('end_reason') in ['technical_failure', 'connection_lost']:
                score -= 0.2
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.error(f"Error calculating quality score: {str(e)}")
            return 0.5
    
    def _send_session_event(self, session: Dict[str, Any], event_type: str) -> None:
        """Send session event to EventBridge"""
        try:
            event_detail = {
                'session_id': session['session_id'],
                'patient_id': session['patient_id'],
                'provider_id': session.get('provider_id'),
                'consultation_type': session['consultation_type'],
                'urgency_level': session['urgency_level'],
                'status': session['status'],
                'event_type': event_type,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            self.eventbridge.put_events(
                Entries=[
                    {
                        'Source': 'healthconnect.consultation',
                        'DetailType': f'Consultation {event_type.replace("_", " ").title()}',
                        'Detail': json.dumps(event_detail),
                        'EventBusName': self.event_bus_name
                    }
                ]
            )
            
        except Exception as e:
            logger.error(f"Error sending session event: {str(e)}")
    
    def _start_session_monitoring(self, session_id: str) -> None:
        """Start monitoring session quality and duration"""
        try:
            # In production, this would set up CloudWatch metrics and alarms
            logger.info(f"Started monitoring for session: {session_id}")
            
        except Exception as e:
            logger.error(f"Error starting session monitoring: {str(e)}")
    
    def _update_provider_availability(self, provider_id: str, status: str) -> None:
        """Update provider availability status"""
        try:
            table = self.dynamodb.Table(self.providers_table_name)
            
            table.update_item(
                Key={'provider_id': provider_id},
                UpdateExpression='SET availability_status = :status, last_updated = :timestamp',
                ExpressionAttributeValues={
                    ':status': status,
                    ':timestamp': datetime.now(timezone.utc).isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error updating provider availability: {str(e)}")
