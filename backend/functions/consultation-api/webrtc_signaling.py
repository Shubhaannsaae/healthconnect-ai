import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError
import uuid

logger = logging.getLogger(__name__)

class WebRTCSignalingServer:
    """Production-grade WebRTC signaling server for healthcare video consultations"""
    
    def __init__(self, apigateway_management_client):
        self.apigateway_management = apigateway_management_client
        self.active_sessions = {}  # In production, this would be stored in DynamoDB
        
        # WebRTC configuration for healthcare-grade video calls
        self.ice_servers = [
            {
                'urls': ['stun:stun.l.google.com:19302']
            },
            {
                'urls': ['turn:turnserver.healthconnect.ai:3478'],
                'username': 'healthconnect',
                'credential': 'secure_credential'  # Would be from environment/secrets
            }
        ]
        
        # Media constraints for healthcare consultations
        self.media_constraints = {
            'video': {
                'width': {'min': 640, 'ideal': 1280, 'max': 1920},
                'height': {'min': 480, 'ideal': 720, 'max': 1080},
                'frameRate': {'min': 15, 'ideal': 30, 'max': 60},
                'facingMode': 'user'
            },
            'audio': {
                'echoCancellation': True,
                'noiseSuppression': True,
                'autoGainControl': True,
                'sampleRate': 48000,
                'channelCount': 1
            }
        }
    
    def handle_offer(self, connection_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle WebRTC offer from client"""
        try:
            session_id = message.get('session_id')
            offer = message.get('offer')
            sender_id = message.get('sender_id')
            
            if not all([session_id, offer, sender_id]):
                logger.error("Missing required fields in offer message")
                return {'statusCode': 400}
            
            # Validate offer format
            if not self._validate_sdp_offer(offer):
                logger.error("Invalid SDP offer format")
                return {'statusCode': 400}
            
            # Store offer in session
            if session_id not in self.active_sessions:
                self.active_sessions[session_id] = {
                    'participants': {},
                    'offers': {},
                    'answers': {},
                    'ice_candidates': {},
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
            
            self.active_sessions[session_id]['offers'][sender_id] = {
                'offer': offer,
                'connection_id': connection_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            # Forward offer to other participants in the session
            forwarded_count = self._forward_to_session_participants(
                session_id, 
                connection_id, 
                {
                    'type': 'offer',
                    'session_id': session_id,
                    'sender_id': sender_id,
                    'offer': offer,
                    'ice_servers': self.ice_servers,
                    'media_constraints': self.media_constraints,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            )
            
            logger.info(f"WebRTC offer forwarded to {forwarded_count} participants in session {session_id}")
            
            return {'statusCode': 200}
            
        except Exception as e:
            logger.error(f"Error handling WebRTC offer: {str(e)}")
            return {'statusCode': 500}
    
    def handle_answer(self, connection_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle WebRTC answer from client"""
        try:
            session_id = message.get('session_id')
            answer = message.get('answer')
            sender_id = message.get('sender_id')
            target_id = message.get('target_id')  # Who this answer is for
            
            if not all([session_id, answer, sender_id, target_id]):
                logger.error("Missing required fields in answer message")
                return {'statusCode': 400}
            
            # Validate answer format
            if not self._validate_sdp_answer(answer):
                logger.error("Invalid SDP answer format")
                return {'statusCode': 400}
            
            # Store answer in session
            if session_id in self.active_sessions:
                if 'answers' not in self.active_sessions[session_id]:
                    self.active_sessions[session_id]['answers'] = {}
                
                self.active_sessions[session_id]['answers'][f"{sender_id}-{target_id}"] = {
                    'answer': answer,
                    'connection_id': connection_id,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            
            # Forward answer to the target participant
            target_connection = self._get_participant_connection(session_id, target_id)
            
            if target_connection:
                try:
                    self.apigateway_management.post_to_connection(
                        ConnectionId=target_connection,
                        Data=json.dumps({
                            'type': 'answer',
                            'session_id': session_id,
                            'sender_id': sender_id,
                            'answer': answer,
                            'timestamp': datetime.now(timezone.utc).isoformat()
                        })
                    )
                    
                    logger.info(f"WebRTC answer forwarded from {sender_id} to {target_id} in session {session_id}")
                    
                except ClientError as e:
                    logger.error(f"Failed to forward answer to {target_id}: {str(e)}")
                    # Remove stale connection
                    self._remove_stale_connection(session_id, target_id)
            
            return {'statusCode': 200}
            
        except Exception as e:
            logger.error(f"Error handling WebRTC answer: {str(e)}")
            return {'statusCode': 500}
    
    def handle_ice_candidate(self, connection_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ICE candidate from client"""
        try:
            session_id = message.get('session_id')
            candidate = message.get('candidate')
            sender_id = message.get('sender_id')
            target_id = message.get('target_id')  # Optional: specific target
            
            if not all([session_id, candidate, sender_id]):
                logger.error("Missing required fields in ICE candidate message")
                return {'statusCode': 400}
            
            # Validate ICE candidate format
            if not self._validate_ice_candidate(candidate):
                logger.error("Invalid ICE candidate format")
                return {'statusCode': 400}
            
            # Store ICE candidate in session
            if session_id in self.active_sessions:
                if 'ice_candidates' not in self.active_sessions[session_id]:
                    self.active_sessions[session_id]['ice_candidates'] = {}
                
                if sender_id not in self.active_sessions[session_id]['ice_candidates']:
                    self.active_sessions[session_id]['ice_candidates'][sender_id] = []
                
                self.active_sessions[session_id]['ice_candidates'][sender_id].append({
                    'candidate': candidate,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
            
            # Forward ICE candidate to target or all participants
            if target_id:
                # Send to specific target
                target_connection = self._get_participant_connection(session_id, target_id)
                if target_connection:
                    self._send_ice_candidate(target_connection, session_id, sender_id, candidate)
            else:
                # Send to all other participants
                forwarded_count = self._forward_to_session_participants(
                    session_id,
                    connection_id,
                    {
                        'type': 'ice_candidate',
                        'session_id': session_id,
                        'sender_id': sender_id,
                        'candidate': candidate,
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }
                )
                
                logger.debug(f"ICE candidate forwarded to {forwarded_count} participants")
            
            return {'statusCode': 200}
            
        except Exception as e:
            logger.error(f"Error handling ICE candidate: {str(e)}")
            return {'statusCode': 500}
    
    def handle_session_control(self, connection_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle session control messages (mute, unmute, video on/off, etc.)"""
        try:
            session_id = message.get('session_id')
            control_type = message.get('control_type')
            sender_id = message.get('sender_id')
            control_data = message.get('data', {})
            
            if not all([session_id, control_type, sender_id]):
                logger.error("Missing required fields in session control message")
                return {'statusCode': 400}
            
            # Validate control type
            valid_controls = [
                'mute_audio', 'unmute_audio', 'disable_video', 'enable_video',
                'share_screen', 'stop_screen_share', 'end_call', 'pause_recording',
                'resume_recording', 'request_attention', 'raise_hand', 'lower_hand'
            ]
            
            if control_type not in valid_controls:
                logger.error(f"Invalid control type: {control_type}")
                return {'statusCode': 400}
            
            # Process control message
            control_message = {
                'type': 'session_control',
                'session_id': session_id,
                'sender_id': sender_id,
                'control_type': control_type,
                'data': control_data,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            # Handle specific control types
            if control_type == 'end_call':
                return self._handle_end_call(session_id, sender_id, connection_id)
            elif control_type in ['mute_audio', 'unmute_audio', 'disable_video', 'enable_video']:
                return self._handle_media_control(session_id, sender_id, control_type, control_data)
            elif control_type in ['share_screen', 'stop_screen_share']:
                return self._handle_screen_share(session_id, sender_id, control_type, control_data)
            
            # Forward control message to other participants
            forwarded_count = self._forward_to_session_participants(
                session_id,
                connection_id,
                control_message
            )
            
            logger.info(f"Session control '{control_type}' forwarded to {forwarded_count} participants")
            
            return {'statusCode': 200}
            
        except Exception as e:
            logger.error(f"Error handling session control: {str(e)}")
            return {'statusCode': 500}
    
    def _validate_sdp_offer(self, offer: Dict[str, Any]) -> bool:
        """Validate SDP offer format"""
        try:
            required_fields = ['type', 'sdp']
            if not all(field in offer for field in required_fields):
                return False
            
            if offer['type'] != 'offer':
                return False
            
            # Basic SDP validation
            sdp = offer['sdp']
            if not isinstance(sdp, str) or len(sdp) < 10:
                return False
            
            # Check for required SDP lines
            required_sdp_lines = ['v=', 'm=', 'c=']
            if not all(line in sdp for line in required_sdp_lines):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating SDP offer: {str(e)}")
            return False
    
    def _validate_sdp_answer(self, answer: Dict[str, Any]) -> bool:
        """Validate SDP answer format"""
        try:
            required_fields = ['type', 'sdp']
            if not all(field in answer for field in required_fields):
                return False
            
            if answer['type'] != 'answer':
                return False
            
            # Basic SDP validation
            sdp = answer['sdp']
            if not isinstance(sdp, str) or len(sdp) < 10:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating SDP answer: {str(e)}")
            return False
    
    def _validate_ice_candidate(self, candidate: Dict[str, Any]) -> bool:
        """Validate ICE candidate format"""
        try:
            if not isinstance(candidate, dict):
                return False
            
            # Check for required fields
            if 'candidate' not in candidate:
                return False
            
            # Basic candidate string validation
            candidate_str = candidate['candidate']
            if not isinstance(candidate_str, str) or len(candidate_str) < 10:
                return False
            
            # Check for basic ICE candidate format
            if not candidate_str.startswith('candidate:'):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating ICE candidate: {str(e)}")
            return False
    
    def _forward_to_session_participants(
        self, 
        session_id: str, 
        sender_connection_id: str, 
        message: Dict[str, Any]
    ) -> int:
        """Forward message to all participants in session except sender"""
        try:
            forwarded_count = 0
            
            if session_id not in self.active_sessions:
                return 0
            
            participants = self.active_sessions[session_id].get('participants', {})
            
            for participant_id, participant_data in participants.items():
                connection_id = participant_data.get('connection_id')
                
                # Skip sender
                if connection_id == sender_connection_id:
                    continue
                
                try:
                    self.apigateway_management.post_to_connection(
                        ConnectionId=connection_id,
                        Data=json.dumps(message)
                    )
                    forwarded_count += 1
                    
                except ClientError as e:
                    if e.response['Error']['Code'] == 'GoneException':
                        # Remove stale connection
                        logger.info(f"Removing stale connection: {connection_id}")
                        self._remove_stale_connection(session_id, participant_id)
                    else:
                        logger.error(f"Error forwarding message to {connection_id}: {str(e)}")
            
            return forwarded_count
            
        except Exception as e:
            logger.error(f"Error forwarding to session participants: {str(e)}")
            return 0
    
    def _get_participant_connection(self, session_id: str, participant_id: str) -> Optional[str]:
        """Get connection ID for a specific participant"""
        try:
            if session_id not in self.active_sessions:
                return None
            
            participants = self.active_sessions[session_id].get('participants', {})
            participant_data = participants.get(participant_id)
            
            if participant_data:
                return participant_data.get('connection_id')
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting participant connection: {str(e)}")
            return None
    
    def _send_ice_candidate(
        self, 
        connection_id: str, 
        session_id: str, 
        sender_id: str, 
        candidate: Dict[str, Any]
    ) -> bool:
        """Send ICE candidate to specific connection"""
        try:
            message = {
                'type': 'ice_candidate',
                'session_id': session_id,
                'sender_id': sender_id,
                'candidate': candidate,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            self.apigateway_management.post_to_connection(
                ConnectionId=connection_id,
                Data=json.dumps(message)
            )
            
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'GoneException':
                logger.info(f"Connection {connection_id} is gone")
            else:
                logger.error(f"Error sending ICE candidate: {str(e)}")
            return False
    
    def _remove_stale_connection(self, session_id: str, participant_id: str) -> None:
        """Remove stale connection from session"""
        try:
            if session_id in self.active_sessions:
                participants = self.active_sessions[session_id].get('participants', {})
                if participant_id in participants:
                    del participants[participant_id]
                    logger.info(f"Removed stale participant {participant_id} from session {session_id}")
        except Exception as e:
            logger.error(f"Error removing stale connection: {str(e)}")
    
    def _handle_end_call(self, session_id: str, sender_id: str, connection_id: str) -> Dict[str, Any]:
        """Handle end call request"""
        try:
            # Notify all participants that call is ending
            end_call_message = {
                'type': 'call_ended',
                'session_id': session_id,
                'ended_by': sender_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            self._forward_to_session_participants(session_id, connection_id, end_call_message)
            
            # Clean up session
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            logger.info(f"Call ended in session {session_id} by {sender_id}")
            
            return {'statusCode': 200}
            
        except Exception as e:
            logger.error(f"Error handling end call: {str(e)}")
            return {'statusCode': 500}
    
    def _handle_media_control(
        self, 
        session_id: str, 
        sender_id: str, 
        control_type: str, 
        control_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle media control (mute/unmute, video on/off)"""
        try:
            # Update participant media state
            if session_id in self.active_sessions:
                participants = self.active_sessions[session_id].get('participants', {})
                if sender_id in participants:
                    if 'media_state' not in participants[sender_id]:
                        participants[sender_id]['media_state'] = {}
                    
                    if control_type == 'mute_audio':
                        participants[sender_id]['media_state']['audio_enabled'] = False
                    elif control_type == 'unmute_audio':
                        participants[sender_id]['media_state']['audio_enabled'] = True
                    elif control_type == 'disable_video':
                        participants[sender_id]['media_state']['video_enabled'] = False
                    elif control_type == 'enable_video':
                        participants[sender_id]['media_state']['video_enabled'] = True
            
            logger.info(f"Media control '{control_type}' applied for {sender_id} in session {session_id}")
            
            return {'statusCode': 200}
            
        except Exception as e:
            logger.error(f"Error handling media control: {str(e)}")
            return {'statusCode': 500}
    
    def _handle_screen_share(
        self, 
        session_id: str, 
        sender_id: str, 
        control_type: str, 
        control_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle screen sharing control"""
        try:
            # Update session screen sharing state
            if session_id in self.active_sessions:
                session_data = self.active_sessions[session_id]
                
                if control_type == 'share_screen':
                    session_data['screen_sharing'] = {
                        'active': True,
                        'presenter': sender_id,
                        'started_at': datetime.now(timezone.utc).isoformat()
                    }
                elif control_type == 'stop_screen_share':
                    session_data['screen_sharing'] = {
                        'active': False,
                        'presenter': None,
                        'stopped_at': datetime.now(timezone.utc).isoformat()
                    }
            
            logger.info(f"Screen share control '{control_type}' applied for {sender_id} in session {session_id}")
            
            return {'statusCode': 200}
            
        except Exception as e:
            logger.error(f"Error handling screen share: {str(e)}")
            return {'statusCode': 500}
    
    def add_participant_to_session(
        self, 
        session_id: str, 
        participant_id: str, 
        connection_id: str, 
        participant_type: str
    ) -> bool:
        """Add participant to WebRTC session"""
        try:
            if session_id not in self.active_sessions:
                self.active_sessions[session_id] = {
                    'participants': {},
                    'offers': {},
                    'answers': {},
                    'ice_candidates': {},
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
            
            self.active_sessions[session_id]['participants'][participant_id] = {
                'connection_id': connection_id,
                'participant_type': participant_type,
                'joined_at': datetime.now(timezone.utc).isoformat(),
                'media_state': {
                    'audio_enabled': True,
                    'video_enabled': True
                }
            }
            
            logger.info(f"Added participant {participant_id} to session {session_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding participant to session: {str(e)}")
            return False
    
    def remove_participant_from_session(self, session_id: str, participant_id: str) -> bool:
        """Remove participant from WebRTC session"""
        try:
            if session_id in self.active_sessions:
                participants = self.active_sessions[session_id].get('participants', {})
                if participant_id in participants:
                    del participants[participant_id]
                    
                    # If no participants left, clean up session
                    if not participants:
                        del self.active_sessions[session_id]
                        logger.info(f"Cleaned up empty session {session_id}")
                    
                    logger.info(f"Removed participant {participant_id} from session {session_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error removing participant from session: {str(e)}")
            return False
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a WebRTC session"""
        try:
            if session_id in self.active_sessions:
                session_data = self.active_sessions[session_id].copy()
                
                # Add computed fields
                session_data['participant_count'] = len(session_data.get('participants', {}))
                session_data['duration_seconds'] = (
                    datetime.now(timezone.utc) - 
                    datetime.fromisoformat(session_data['created_at'].replace('Z', '+00:00'))
                ).total_seconds()
                
                return session_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting session info: {str(e)}")
            return None
