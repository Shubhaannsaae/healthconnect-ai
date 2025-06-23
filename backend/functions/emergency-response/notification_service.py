import logging
import os
from typing import Dict, Any, List, Optional
import boto3
from botocore.exceptions import ClientError
import json
from datetime import datetime, timezone
import phonenumbers
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests

logger = logging.getLogger(__name__)

class NotificationService:
    """Production-grade notification service for emergency alerts"""[2]
    
    def __init__(self):
        # Initialize AWS clients
        self.sns = boto3.client('sns')
        self.ses = boto3.client('ses')
        self.pinpoint = boto3.client('pinpoint')
        
        # Environment variables
        self.twilio_account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        self.twilio_auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        self.twilio_phone_number = os.environ.get('TWILIO_PHONE_NUMBER', '+1234567890')
        self.ses_sender_email = os.environ.get('SES_SENDER_EMAIL', 'alerts@healthconnect.ai')
        self.pinpoint_app_id = os.environ.get('PINPOINT_APP_ID')
        
        # Notification templates
        self.templates = {
            'emergency_sms': {
                'critical': "🚨 CRITICAL EMERGENCY: {patient_id} - {emergency_type}. Location: {location}. Call 911 immediately. Alert ID: {alert_id}",
                'high': "⚠️ HIGH PRIORITY: Health emergency for {patient_id} - {emergency_type}. Please respond immediately. Alert ID: {alert_id}",
                'medium': "⚠️ HEALTH ALERT: {patient_id} - {emergency_type}. Please check on patient. Alert ID: {alert_id}",
                'low': "ℹ️ Health notification for {patient_id}. Alert ID: {alert_id}"
            },
            'emergency_email': {
                'subject': "🚨 {urgency_level} Health Emergency Alert - Patient {patient_id}",
                'body_template': """
<!DOCTYPE html>
<html>
<head>
    <style>
        .emergency-alert {{
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 0 auto;
            border: 3px solid #dc3545;
            border-radius: 8px;
            padding: 20px;
        }}
        .header {{
            background-color: #dc3545;
            color: white;
            padding: 15px;
            text-align: center;
            margin: -20px -20px 20px -20px;
            border-radius: 5px 5px 0 0;
        }}
        .critical {{ background-color: #dc3545; }}
        .high {{ background-color: #fd7e14; }}
        .medium {{ background-color: #ffc107; color: black; }}
        .low {{ background-color: #28a745; }}
        .vital-signs {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
        }}
        .actions {{
            background-color: #e9ecef;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
        }}
        .footer {{
            font-size: 12px;
            color: #6c757d;
            text-align: center;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #dee2e6;
        }}
    </style>
</head>
<body>
    <div class="emergency-alert">
        <div class="header {urgency_class}">
            <h1>🚨 {urgency_level} HEALTH EMERGENCY</h1>
            <h2>Patient: {patient_id}</h2>
        </div>
        
        <div class="content">
            <h3>Emergency Details</h3>
            <ul>
                <li><strong>Alert ID:</strong> {alert_id}</li>
                <li><strong>Emergency Type:</strong> {emergency_type}</li>
                <li><strong>Time:</strong> {timestamp}</li>
                <li><strong>Source:</strong> {source}</li>
            </ul>
            
            <div class="vital-signs">
                <h3>Critical Health Data</h3>
                {health_data_html}
            </div>
            
            <div class="actions">
                <h3>Immediate Actions Required</h3>
                {actions_html}
            </div>
            
            <h3>Contact Information</h3>
            <p>For immediate assistance, call emergency services: <strong>911</strong></p>
            <p>For system support: <strong>support@healthconnect.ai</strong></p>
        </div>
        
        <div class="footer">
            <p>This is an automated emergency alert from HealthConnect AI Emergency Response System.</p>
            <p>Alert generated at: {timestamp}</p>
        </div>
    </div>
</body>
</html>
"""
            }
        }
    
    def send_sms(self, phone_number: str, message: str, urgency_level: str = 'HIGH') -> Dict[str, Any]:
        """Send SMS notification using multiple providers for reliability"""[2]
        
        try:
            # Validate and format phone number
            formatted_phone = self._format_phone_number(phone_number)
            if not formatted_phone:
                return {
                    'success': False,
                    'error': 'Invalid phone number format',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            
            # Try Twilio first (most reliable for emergency notifications)
            if self.twilio_account_sid and self.twilio_auth_token:
                twilio_result = self._send_sms_twilio(formatted_phone, message, urgency_level)
                if twilio_result['success']:
                    return twilio_result
                else:
                    logger.warning(f"Twilio SMS failed, trying AWS SNS: {twilio_result.get('error')}")
            
            # Fallback to AWS SNS
            sns_result = self._send_sms_sns(formatted_phone, message, urgency_level)
            return sns_result
            
        except Exception as e:
            logger.error(f"Error sending SMS: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def _send_sms_twilio(self, phone_number: str, message: str, urgency_level: str) -> Dict[str, Any]:
        """Send SMS using Twilio API"""
        
        try:
            from twilio.rest import Client
            
            client = Client(self.twilio_account_sid, self.twilio_auth_token)
            
            # Add urgency indicator to message
            priority_message = f"[{urgency_level}] {message}"
            
            message_obj = client.messages.create(
                body=priority_message,
                from_=self.twilio_phone_number,
                to=phone_number
            )
            
            logger.info(f"Twilio SMS sent successfully: {message_obj.sid}")
            
            return {
                'success': True,
                'provider': 'twilio',
                'message_id': message_obj.sid,
                'status': message_obj.status,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Twilio SMS error: {str(e)}")
            return {
                'success': False,
                'provider': 'twilio',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def _send_sms_sns(self, phone_number: str, message: str, urgency_level: str) -> Dict[str, Any]:
        """Send SMS using AWS SNS"""
        
        try:
            # Add urgency indicator to message
            priority_message = f"[{urgency_level}] {message}"
            
            response = self.sns.publish(
                PhoneNumber=phone_number,
                Message=priority_message,
                MessageAttributes={
                    'AWS.SNS.SMS.SenderID': {
                        'DataType': 'String',
                        'StringValue': 'HealthConnect'
                    },
                    'AWS.SNS.SMS.SMSType': {
                        'DataType': 'String',
                        'StringValue': 'Transactional'  # Higher priority
                    }
                }
            )
            
            logger.info(f"AWS SNS SMS sent successfully: {response['MessageId']}")
            
            return {
                'success': True,
                'provider': 'aws_sns',
                'message_id': response['MessageId'],
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except ClientError as e:
            logger.error(f"AWS SNS SMS error: {str(e)}")
            return {
                'success': False,
                'provider': 'aws_sns',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def send_email(
        self, 
        email_address: str, 
        subject: str, 
        body: str, 
        urgency_level: str = 'HIGH',
        html_body: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send email notification using AWS SES"""[2]
        
        try:
            # Validate email address
            if not self._validate_email(email_address):
                return {
                    'success': False,
                    'error': 'Invalid email address',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            
            # Add urgency indicator to subject
            priority_subject = f"[{urgency_level}] {subject}"
            
            # Prepare email content
            if html_body:
                # Send both text and HTML versions
                response = self.ses.send_email(
                    Source=self.ses_sender_email,
                    Destination={'ToAddresses': [email_address]},
                    Message={
                        'Subject': {'Data': priority_subject, 'Charset': 'UTF-8'},
                        'Body': {
                            'Text': {'Data': body, 'Charset': 'UTF-8'},
                            'Html': {'Data': html_body, 'Charset': 'UTF-8'}
                        }
                    },
                    Tags=[
                        {'Name': 'Purpose', 'Value': 'EmergencyAlert'},
                        {'Name': 'UrgencyLevel', 'Value': urgency_level}
                    ]
                )
            else:
                # Send text only
                response = self.ses.send_email(
                    Source=self.ses_sender_email,
                    Destination={'ToAddresses': [email_address]},
                    Message={
                        'Subject': {'Data': priority_subject, 'Charset': 'UTF-8'},
                        'Body': {'Text': {'Data': body, 'Charset': 'UTF-8'}}
                    },
                    Tags=[
                        {'Name': 'Purpose', 'Value': 'EmergencyAlert'},
                        {'Name': 'UrgencyLevel', 'Value': urgency_level}
                    ]
                )
            
            logger.info(f"Email sent successfully: {response['MessageId']}")
            
            return {
                'success': True,
                'provider': 'aws_ses',
                'message_id': response['MessageId'],
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except ClientError as e:
            logger.error(f"AWS SES email error: {str(e)}")
            return {
                'success': False,
                'provider': 'aws_ses',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def send_push_notification(
        self, 
        patient_id: str, 
        title: str, 
        message: str, 
        urgency_level: str = 'HIGH'
    ) -> Dict[str, Any]:
        """Send push notification using AWS Pinpoint"""[2]
        
        try:
            if not self.pinpoint_app_id:
                logger.warning("Pinpoint app ID not configured, skipping push notification")
                return {
                    'success': False,
                    'error': 'Push notifications not configured',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            
            # Add urgency indicator to title
            priority_title = f"[{urgency_level}] {title}"
            
            # Send push notification
            response = self.pinpoint.send_messages(
                ApplicationId=self.pinpoint_app_id,
                MessageRequest={
                    'Addresses': {
                        patient_id: {
                            'ChannelType': 'GCM'  # Android push notifications
                        }
                    },
                    'MessageConfiguration': {
                        'GCMMessage': {
                            'Action': 'OPEN_APP',
                            'Body': message,
                            'Priority': 'high',
                            'SilentPush': False,
                            'Title': priority_title,
                            'Data': {
                                'urgency_level': urgency_level,
                                'alert_type': 'emergency',
                                'timestamp': datetime.now(timezone.utc).isoformat()
                            }
                        },
                        'APNSMessage': {  # iOS push notifications
                            'Action': 'OPEN_APP',
                            'Body': message,
                            'Priority': 'high',
                            'SilentPush': False,
                            'Title': priority_title,
                            'Data': {
                                'urgency_level': urgency_level,
                                'alert_type': 'emergency',
                                'timestamp': datetime.now(timezone.utc).isoformat()
                            }
                        }
                    }
                }
            )
            
            logger.info(f"Push notification sent successfully: {response['MessageResponse']['RequestId']}")
            
            return {
                'success': True,
                'provider': 'aws_pinpoint',
                'request_id': response['MessageResponse']['RequestId'],
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except ClientError as e:
            logger.error(f"AWS Pinpoint push notification error: {str(e)}")
            return {
                'success': False,
                'provider': 'aws_pinpoint',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def send_voice_call(
        self, 
        phone_number: str, 
        message: str, 
        urgency_level: str = 'CRITICAL'
    ) -> Dict[str, Any]:
        """Send voice call notification for critical emergencies"""[2]
        
        try:
            # Only send voice calls for critical emergencies
            if urgency_level != 'CRITICAL':
                return {
                    'success': False,
                    'error': 'Voice calls only sent for CRITICAL emergencies',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            
            if not self.twilio_account_sid:
                return {
                    'success': False,
                    'error': 'Voice call service not configured',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            
            from twilio.rest import Client
            from twilio.twiml import VoiceResponse
            
            client = Client(self.twilio_account_sid, self.twilio_auth_token)
            
            # Create TwiML for voice message
            response_twiml = VoiceResponse()
            response_twiml.say(
                f"This is a critical health emergency alert from HealthConnect AI. {message}. "
                f"Please respond immediately. This message will repeat.",
                voice='alice',
                language='en-US'
            )
            response_twiml.pause(length=2)
            response_twiml.say(
                f"Repeating: {message}. Please take immediate action.",
                voice='alice',
                language='en-US'
            )
            
            # Make the call
            call = client.calls.create(
                twiml=str(response_twiml),
                to=phone_number,
                from_=self.twilio_phone_number,
                timeout=30
            )
            
            logger.info(f"Voice call initiated successfully: {call.sid}")
            
            return {
                'success': True,
                'provider': 'twilio_voice',
                'call_id': call.sid,
                'status': call.status,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Voice call error: {str(e)}")
            return {
                'success': False,
                'provider': 'twilio_voice',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def send_multi_channel_notification(
        self, 
        contact_info: Dict[str, Any], 
        alert_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send notification through multiple channels for maximum reliability"""[2]
        
        try:
            results = {
                'channels_attempted': 0,
                'channels_successful': 0,
                'results': [],
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            urgency_level = alert_data.get('urgency_level', 'HIGH')
            
            # Prepare message content
            sms_message = self._format_sms_message(alert_data)
            email_subject = self._format_email_subject(alert_data)
            email_body = self._format_email_body(alert_data)
            push_title = alert_data.get('emergency_type', 'Health Emergency')
            push_message = self._format_push_message(alert_data)
            
            # Send SMS if phone number available
            if contact_info.get('phone_number'):
                results['channels_attempted'] += 1
                sms_result = self.send_sms(
                    contact_info['phone_number'], 
                    sms_message, 
                    urgency_level
                )
                results['results'].append({
                    'channel': 'sms',
                    'success': sms_result['success'],
                    'details': sms_result
                })
                if sms_result['success']:
                    results['channels_successful'] += 1
            
            # Send email if email address available
            if contact_info.get('email'):
                results['channels_attempted'] += 1
                html_body = self._format_html_email(alert_data)
                email_result = self.send_email(
                    contact_info['email'], 
                    email_subject, 
                    email_body, 
                    urgency_level,
                    html_body
                )
                results['results'].append({
                    'channel': 'email',
                    'success': email_result['success'],
                    'details': email_result
                })
                if email_result['success']:
                    results['channels_successful'] += 1
            
            # Send push notification if patient ID available
            if contact_info.get('patient_id'):
                results['channels_attempted'] += 1
                push_result = self.send_push_notification(
                    contact_info['patient_id'], 
                    push_title, 
                    push_message, 
                    urgency_level
                )
                results['results'].append({
                    'channel': 'push',
                    'success': push_result['success'],
                    'details': push_result
                })
                if push_result['success']:
                    results['channels_successful'] += 1
            
            # Send voice call for critical emergencies
            if urgency_level == 'CRITICAL' and contact_info.get('phone_number'):
                results['channels_attempted'] += 1
                voice_result = self.send_voice_call(
                    contact_info['phone_number'], 
                    sms_message, 
                    urgency_level
                )
                results['results'].append({
                    'channel': 'voice',
                    'success': voice_result['success'],
                    'details': voice_result
                })
                if voice_result['success']:
                    results['channels_successful'] += 1
            
            # Calculate success rate
            results['success_rate'] = (
                results['channels_successful'] / results['channels_attempted'] 
                if results['channels_attempted'] > 0 else 0
            )
            
            logger.info(
                f"Multi-channel notification completed: "
                f"{results['channels_successful']}/{results['channels_attempted']} successful"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Multi-channel notification error: {str(e)}")
            return {
                'channels_attempted': 0,
                'channels_successful': 0,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def _format_phone_number(self, phone_number: str) -> Optional[str]:
        """Format and validate phone number"""
        
        try:
            # Parse phone number
            parsed = phonenumbers.parse(phone_number, "US")
            
            # Validate phone number
            if phonenumbers.is_valid_number(parsed):
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            else:
                return None
                
        except phonenumbers.NumberParseException:
            return None
    
    def _validate_email(self, email: str) -> bool:
        """Validate email address format"""
        
        try:
            from email_validator import validate_email
            validate_email(email)
            return True
        except:
            # Basic regex validation as fallback
            import re
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            return re.match(pattern, email) is not None
    
    def _format_sms_message(self, alert_data: Dict[str, Any]) -> str:
        """Format SMS message based on alert data"""
        
        urgency_level = alert_data.get('urgency_level', 'HIGH')
        template = self.templates['emergency_sms'].get(urgency_level.lower(), 
                                                      self.templates['emergency_sms']['high'])
        
        return template.format(
            patient_id=alert_data.get('patient_id', 'Unknown'),
            emergency_type=alert_data.get('emergency_type', 'Health Emergency'),
            location=alert_data.get('location', 'Unknown Location'),
            alert_id=alert_data.get('alert_id', 'N/A')
        )
    
    def _format_email_subject(self, alert_data: Dict[str, Any]) -> str:
        """Format email subject based on alert data"""
        
        return self.templates['emergency_email']['subject'].format(
            urgency_level=alert_data.get('urgency_level', 'HIGH'),
            patient_id=alert_data.get('patient_id', 'Unknown')
        )
    
    def _format_email_body(self, alert_data: Dict[str, Any]) -> str:
        """Format plain text email body"""
        
        return f"""
EMERGENCY HEALTH ALERT

Patient ID: {alert_data.get('patient_id', 'Unknown')}
Alert Level: {alert_data.get('urgency_level', 'HIGH')}
Emergency Type: {alert_data.get('emergency_type', 'Health Emergency')}
Time: {alert_data.get('timestamp', datetime.now(timezone.utc).isoformat())}

Health Data:
{json.dumps(alert_data.get('health_data', {}), indent=2)}

This is an automated emergency alert from HealthConnect AI.
Please take immediate action and contact emergency services if necessary.

Alert ID: {alert_data.get('alert_id', 'N/A')}
"""
    
    def _format_html_email(self, alert_data: Dict[str, Any]) -> str:
        """Format HTML email body"""
        
        urgency_level = alert_data.get('urgency_level', 'HIGH')
        urgency_class = urgency_level.lower()
        
        # Format health data as HTML
        health_data = alert_data.get('health_data', {})
        health_data_html = "<ul>"
        for key, value in health_data.items():
            health_data_html += f"<li><strong>{key.replace('_', ' ').title()}:</strong> {value}</li>"
        health_data_html += "</ul>"
        
        # Format actions as HTML
        actions = [
            "Contact emergency services if needed",
            "Monitor patient continuously",
            "Document all observations",
            "Stay with patient until help arrives"
        ]
        actions_html = "<ul>"
        for action in actions:
            actions_html += f"<li>{action}</li>"
        actions_html += "</ul>"
        
        return self.templates['emergency_email']['body_template'].format(
            urgency_level=urgency_level,
            urgency_class=urgency_class,
            patient_id=alert_data.get('patient_id', 'Unknown'),
            alert_id=alert_data.get('alert_id', 'N/A'),
            emergency_type=alert_data.get('emergency_type', 'Health Emergency'),
            timestamp=alert_data.get('timestamp', datetime.now(timezone.utc).isoformat()),
            source=alert_data.get('source', 'System'),
            health_data_html=health_data_html,
            actions_html=actions_html
        )
    
    def _format_push_message(self, alert_data: Dict[str, Any]) -> str:
        """Format push notification message"""
        
        return f"Emergency detected for patient {alert_data.get('patient_id', 'Unknown')}. " \
               f"Type: {alert_data.get('emergency_type', 'Health Emergency')}. " \
               f"Please respond immediately."
