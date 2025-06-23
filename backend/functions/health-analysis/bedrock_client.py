import json
import logging
from typing import Dict, Any, List, Optional
import boto3
from botocore.exceptions import ClientError
import os

logger = logging.getLogger(__name__)

class BedrockHealthAnalyzer:
    """Production-grade AWS Bedrock client for health analysis"""
    
    def __init__(self):
        self.bedrock_runtime = boto3.client(
            'bedrock-runtime',
            region_name=os.environ.get('AWS_REGION', 'us-east-1')
        )
        self.model_id = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')
        self.max_tokens = 4000
        self.temperature = 0.1  # Low temperature for medical accuracy
        
    def analyze_health_data(self, health_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze health data using AWS Bedrock Claude model
        
        Args:
            health_data: Dictionary containing symptoms, vital signs, history, medications
            
        Returns:
            Dictionary containing analysis results and recommendations
        """
        try:
            # Construct medical analysis prompt
            prompt = self._build_medical_prompt(health_data)
            
            # Prepare request body according to Claude 3 API specification
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "system": self._get_medical_system_prompt()
            }
            
            # Invoke Bedrock model
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType='application/json',
                accept='application/json'
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            analysis_text = response_body['content'][0]['text']
            
            # Parse structured response
            return self._parse_analysis_response(analysis_text)
            
        except ClientError as e:
            logger.error(f"Bedrock API error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error in health analysis: {str(e)}")
            raise
    
    def _build_medical_prompt(self, health_data: Dict[str, Any]) -> str:
        """Build comprehensive medical analysis prompt"""
        
        symptoms_text = ""
        if health_data.get('symptoms'):
            symptoms_text = "Symptoms:\n"
            for symptom in health_data['symptoms']:
                symptoms_text += f"- {symptom.get('text', '')}\n"
        
        vital_signs_text = ""
        if health_data.get('vital_signs'):
            vital_signs_text = "Vital Signs:\n"
            vs = health_data['vital_signs']
            if 'heart_rate' in vs:
                vital_signs_text += f"- Heart Rate: {vs['heart_rate']} bpm\n"
            if 'blood_pressure' in vs:
                bp = vs['blood_pressure']
                vital_signs_text += f"- Blood Pressure: {bp.get('systolic', 'N/A')}/{bp.get('diastolic', 'N/A')} mmHg\n"
            if 'temperature' in vs:
                vital_signs_text += f"- Temperature: {vs['temperature']}°C\n"
            if 'oxygen_saturation' in vs:
                vital_signs_text += f"- Oxygen Saturation: {vs['oxygen_saturation']}%\n"
            if 'respiratory_rate' in vs:
                vital_signs_text += f"- Respiratory Rate: {vs['respiratory_rate']} breaths/min\n"
        
        history_text = ""
        if health_data.get('medical_history'):
            history_text = "Medical History:\n"
            for condition in health_data['medical_history']:
                history_text += f"- {condition}\n"
        
        medications_text = ""
        if health_data.get('medications'):
            medications_text = "Current Medications:\n"
            for medication in health_data['medications']:
                medications_text += f"- {medication}\n"
        
        prompt = f"""
Please analyze the following patient health data and provide a comprehensive medical assessment:

{symptoms_text}

{vital_signs_text}

{history_text}

{medications_text}

Please provide your analysis in the following JSON format:
{{
    "primary_assessment": "Brief primary assessment",
    "differential_diagnosis": ["List of possible conditions"],
    "severity_level": "LOW/MODERATE/HIGH/CRITICAL",
    "immediate_actions": ["List of immediate actions needed"],
    "recommendations": [
        {{
            "category": "category_name",
            "action": "specific recommendation",
            "priority": "HIGH/MEDIUM/LOW",
            "timeframe": "immediate/24h/1week/1month"
        }}
    ],
    "red_flags": ["List of concerning symptoms or findings"],
    "follow_up": {{
        "required": true/false,
        "timeframe": "timeframe for follow-up",
        "specialist": "type of specialist if needed"
    }},
    "confidence_level": 0.0-1.0
}}
"""
        return prompt
    
    def _get_medical_system_prompt(self) -> str:
        """Get system prompt for medical analysis"""
        return """You are a highly skilled medical AI assistant with expertise in clinical assessment and diagnosis. 
        
Your role is to:
1. Analyze patient symptoms, vital signs, and medical history
2. Provide differential diagnoses based on clinical evidence
3. Assess severity and urgency of the patient's condition
4. Recommend appropriate immediate actions and follow-up care
5. Identify red flag symptoms that require immediate attention

Important guidelines:
- Always prioritize patient safety
- Be conservative in your assessments - when in doubt, recommend higher level of care
- Provide evidence-based recommendations
- Clearly indicate when emergency care is needed
- Consider drug interactions and contraindications
- Maintain professional medical terminology while being clear
- Always recommend consulting with healthcare providers for definitive diagnosis and treatment

Remember: You are providing clinical decision support, not replacing professional medical judgment."""
    
    def _parse_analysis_response(self, analysis_text: str) -> Dict[str, Any]:
        """Parse structured analysis response from Claude"""
        try:
            # Find JSON block in response
            start_idx = analysis_text.find('{')
            end_idx = analysis_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")
            
            json_str = analysis_text[start_idx:end_idx]
            parsed_response = json.loads(json_str)
            
            # Validate required fields
            required_fields = ['primary_assessment', 'differential_diagnosis', 'severity_level', 'recommendations']
            for field in required_fields:
                if field not in parsed_response:
                    logger.warning(f"Missing required field in analysis: {field}")
            
            return parsed_response
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse analysis response: {str(e)}")
            # Return fallback response
            return {
                "primary_assessment": "Analysis completed - please review raw output",
                "differential_diagnosis": ["Unable to parse structured diagnosis"],
                "severity_level": "MODERATE",
                "immediate_actions": ["Consult healthcare provider"],
                "recommendations": [
                    {
                        "category": "general",
                        "action": "Seek professional medical evaluation",
                        "priority": "HIGH",
                        "timeframe": "24h"
                    }
                ],
                "red_flags": [],
                "follow_up": {
                    "required": True,
                    "timeframe": "24 hours",
                    "specialist": "primary care physician"
                },
                "confidence_level": 0.5,
                "raw_response": analysis_text
            }
    
    def get_health_insights(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate health insights and wellness recommendations"""
        try:
            prompt = f"""
            Based on the following patient health profile, provide personalized health insights and wellness recommendations:
            
            Health Profile:
            - Age: {patient_data.get('age', 'Not specified')}
            - Gender: {patient_data.get('gender', 'Not specified')}
            - BMI: {patient_data.get('bmi', 'Not specified')}
            - Activity Level: {patient_data.get('activity_level', 'Not specified')}
            - Medical Conditions: {', '.join(patient_data.get('conditions', []))}
            - Recent Vital Signs: {json.dumps(patient_data.get('recent_vitals', {}))}
            
            Provide insights in JSON format with wellness recommendations, risk factors, and preventive measures.
            """
            
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "temperature": 0.3,
                "messages": [{"role": "user", "content": prompt}],
                "system": "You are a wellness and preventive health AI assistant focused on providing personalized health insights."
            }
            
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType='application/json',
                accept='application/json'
            )
            
            response_body = json.loads(response['body'].read())
            return {"insights": response_body['content'][0]['text']}
            
        except Exception as e:
            logger.error(f"Error generating health insights: {str(e)}")
            raise
