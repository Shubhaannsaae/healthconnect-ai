import json
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from bedrock_client import BedrockHealthAnalyzer
from medical_nlp import MedicalNLPProcessor
import traceback

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
eventbridge = boto3.client('events')

# Environment variables
HEALTH_RECORDS_TABLE = os.environ['HEALTH_RECORDS_TABLE']
ANALYSIS_RESULTS_TABLE = os.environ['ANALYSIS_RESULTS_TABLE']
EMERGENCY_TOPIC_ARN = os.environ['EMERGENCY_TOPIC_ARN']
EVENT_BUS_NAME = os.environ['EVENT_BUS_NAME']

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Main Lambda handler for health analysis using AWS Bedrock
    
    Args:
        event: API Gateway event or direct invocation event
        context: Lambda context object
        
    Returns:
        Dict containing status code and response body
    """
    try:
        # Parse request body
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
            
        # Validate required fields
        required_fields = ['patient_id', 'symptoms', 'vital_signs']
        for field in required_fields:
            if field not in body:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': f'Missing required field: {field}',
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    })
                }
        
        patient_id = body['patient_id']
        symptoms = body['symptoms']
        vital_signs = body['vital_signs']
        medical_history = body.get('medical_history', [])
        medications = body.get('medications', [])
        
        logger.info(f"Processing health analysis for patient: {patient_id}")
        
        # Initialize analyzers
        bedrock_analyzer = BedrockHealthAnalyzer()
        nlp_processor = MedicalNLPProcessor()
        
        # Process symptoms with NLP
        processed_symptoms = nlp_processor.extract_medical_entities(symptoms)
        
        # Perform health analysis using Bedrock
        analysis_result = bedrock_analyzer.analyze_health_data({
            'symptoms': processed_symptoms,
            'vital_signs': vital_signs,
            'medical_history': medical_history,
            'medications': medications
        })
        
        # Calculate risk scores
        risk_assessment = calculate_risk_scores(vital_signs, processed_symptoms, medical_history)
        
        # Store analysis results
        analysis_record = {
            'analysis_id': f"{patient_id}_{int(datetime.now().timestamp())}",
            'patient_id': patient_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'symptoms': processed_symptoms,
            'vital_signs': vital_signs,
            'analysis_result': analysis_result,
            'risk_assessment': risk_assessment,
            'recommendations': analysis_result.get('recommendations', []),
            'urgency_level': determine_urgency_level(risk_assessment),
            'ttl': int(datetime.now().timestamp()) + 31536000  # 1 year TTL
        }
        
        # Save to DynamoDB
        table = dynamodb.Table(ANALYSIS_RESULTS_TABLE)
        table.put_item(Item=analysis_record)
        
        # Check for emergency conditions
        if risk_assessment['emergency_risk'] > 0.8:
            await handle_emergency_alert(patient_id, analysis_record)
        
        # Send analysis complete event
        await send_analysis_event(patient_id, analysis_record)
        
        # Prepare response
        response_body = {
            'analysis_id': analysis_record['analysis_id'],
            'patient_id': patient_id,
            'analysis_result': analysis_result,
            'risk_assessment': risk_assessment,
            'urgency_level': analysis_record['urgency_level'],
            'recommendations': analysis_result.get('recommendations', []),
            'timestamp': analysis_record['timestamp']
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response_body)
        }
        
    except ClientError as e:
        logger.error(f"AWS Client Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'AWS service error occurred',
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }

def calculate_risk_scores(vital_signs: Dict, symptoms: List, medical_history: List) -> Dict[str, float]:
    """Calculate comprehensive risk scores based on health data"""
    
    # Vital signs risk calculation
    vital_risk = 0.0
    if 'heart_rate' in vital_signs:
        hr = vital_signs['heart_rate']
        if hr < 60 or hr > 100:
            vital_risk += 0.3
        if hr < 50 or hr > 120:
            vital_risk += 0.4
            
    if 'blood_pressure' in vital_signs:
        bp = vital_signs['blood_pressure']
        systolic = bp.get('systolic', 120)
        diastolic = bp.get('diastolic', 80)
        if systolic > 140 or diastolic > 90:
            vital_risk += 0.4
        if systolic > 180 or diastolic > 110:
            vital_risk += 0.6
            
    if 'temperature' in vital_signs:
        temp = vital_signs['temperature']
        if temp > 38.0 or temp < 36.0:
            vital_risk += 0.2
        if temp > 39.5 or temp < 35.0:
            vital_risk += 0.5
    
    # Symptom severity risk
    symptom_risk = 0.0
    high_risk_symptoms = ['chest pain', 'difficulty breathing', 'severe headache', 'confusion']
    for symptom in symptoms:
        if any(hrs in symptom['text'].lower() for hrs in high_risk_symptoms):
            symptom_risk += 0.4
    
    # Medical history risk
    history_risk = 0.0
    high_risk_conditions = ['diabetes', 'hypertension', 'heart disease', 'stroke']
    for condition in medical_history:
        if any(hrc in condition.lower() for hrc in high_risk_conditions):
            history_risk += 0.2
    
    # Calculate overall emergency risk
    emergency_risk = min(1.0, vital_risk + symptom_risk + (history_risk * 0.5))
    
    return {
        'vital_signs_risk': min(1.0, vital_risk),
        'symptom_risk': min(1.0, symptom_risk),
        'medical_history_risk': min(1.0, history_risk),
        'emergency_risk': emergency_risk,
        'overall_risk': min(1.0, (vital_risk + symptom_risk + history_risk) / 3)
    }

def determine_urgency_level(risk_assessment: Dict[str, float]) -> str:
    """Determine urgency level based on risk assessment"""
    emergency_risk = risk_assessment['emergency_risk']
    
    if emergency_risk >= 0.8:
        return 'CRITICAL'
    elif emergency_risk >= 0.6:
        return 'HIGH'
    elif emergency_risk >= 0.4:
        return 'MEDIUM'
    else:
        return 'LOW'

async def handle_emergency_alert(patient_id: str, analysis_record: Dict) -> None:
    """Handle emergency alert notifications"""
    try:
        message = {
            'patient_id': patient_id,
            'analysis_id': analysis_record['analysis_id'],
            'urgency_level': analysis_record['urgency_level'],
            'risk_score': analysis_record['risk_assessment']['emergency_risk'],
            'timestamp': analysis_record['timestamp'],
            'vital_signs': analysis_record['vital_signs'],
            'symptoms': analysis_record['symptoms']
        }
        
        # Send SNS notification
        sns.publish(
            TopicArn=EMERGENCY_TOPIC_ARN,
            Message=json.dumps(message),
            Subject=f'EMERGENCY ALERT - Patient {patient_id}'
        )
        
        logger.info(f"Emergency alert sent for patient: {patient_id}")
        
    except Exception as e:
        logger.error(f"Failed to send emergency alert: {str(e)}")

async def send_analysis_event(patient_id: str, analysis_record: Dict) -> None:
    """Send analysis completion event to EventBridge"""
    try:
        event_detail = {
            'patient_id': patient_id,
            'analysis_id': analysis_record['analysis_id'],
            'urgency_level': analysis_record['urgency_level'],
            'timestamp': analysis_record['timestamp']
        }
        
        eventbridge.put_events(
            Entries=[
                {
                    'Source': 'healthconnect.analysis',
                    'DetailType': 'Health Analysis Complete',
                    'Detail': json.dumps(event_detail),
                    'EventBusName': EVENT_BUS_NAME
                }
            ]
        )
        
    except Exception as e:
        logger.error(f"Failed to send analysis event: {str(e)}")
