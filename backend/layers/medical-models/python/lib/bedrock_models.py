import json
import logging
from typing import Dict, Any, List, Optional
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class BedrockModelManager:
    """Production-grade Bedrock model manager for healthcare AI"""
    
    def __init__(self):
        self.bedrock_runtime = boto3.client('bedrock-runtime')
        
        # Model configurations for different healthcare use cases
        self.model_configs = {
            'medical_analysis': {
                'model_id': 'anthropic.claude-3-sonnet-20240229-v1:0',
                'max_tokens': 4000,
                'temperature': 0.1,
                'system_prompt': self._get_medical_analysis_prompt()
            },
            'symptom_assessment': {
                'model_id': 'anthropic.claude-3-haiku-20240307-v1:0',
                'max_tokens': 2000,
                'temperature': 0.2,
                'system_prompt': self._get_symptom_assessment_prompt()
            },
            'drug_interaction': {
                'model_id': 'anthropic.claude-3-sonnet-20240229-v1:0',
                'max_tokens': 3000,
                'temperature': 0.05,
                'system_prompt': self._get_drug_interaction_prompt()
            },
            'health_insights': {
                'model_id': 'anthropic.claude-3-sonnet-20240229-v1:0',
                'max_tokens': 3500,
                'temperature': 0.3,
                'system_prompt': self._get_health_insights_prompt()
            }
        }
    
    def invoke_medical_model(
        self, 
        model_type: str, 
        prompt: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Invoke Bedrock model for medical analysis"""
        try:
            if model_type not in self.model_configs:
                raise ValueError(f"Unknown model type: {model_type}")
            
            config = self.model_configs[model_type]
            
            # Prepare request body
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": config['max_tokens'],
                "temperature": config['temperature'],
                "messages": [{"role": "user", "content": prompt}],
                "system": config['system_prompt']
            }
            
            # Add context if provided
            if context:
                enhanced_prompt = f"Context: {json.dumps(context)}\n\nQuery: {prompt}"
                request_body["messages"][0]["content"] = enhanced_prompt
            
            # Invoke model
            response = self.bedrock_runtime.invoke_model(
                modelId=config['model_id'],
                body=json.dumps(request_body),
                contentType='application/json',
                accept='application/json'
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            return {
                'success': True,
                'response': response_body['content'][0]['text'],
                'model_id': config['model_id'],
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error invoking medical model: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def _get_medical_analysis_prompt(self) -> str:
        """System prompt for medical analysis"""
        return """You are a highly skilled medical AI assistant with expertise in clinical assessment, diagnosis, and treatment recommendations. Your role is to:

1. Analyze patient symptoms, vital signs, and medical history
2. Provide differential diagnoses based on clinical evidence
3. Assess severity and urgency of conditions
4. Recommend appropriate diagnostic tests and treatments
5. Identify red flag symptoms requiring immediate attention

Guidelines:
- Always prioritize patient safety
- Provide evidence-based recommendations
- Clearly indicate when emergency care is needed
- Consider drug interactions and contraindications
- Maintain professional medical terminology
- Always recommend consulting with healthcare providers for definitive diagnosis

Remember: You provide clinical decision support, not definitive medical diagnosis."""
    
    def _get_symptom_assessment_prompt(self) -> str:
        """System prompt for symptom assessment"""
        return """You are a medical AI assistant specialized in symptom assessment and triage. Your role is to:

1. Evaluate patient-reported symptoms
2. Assess symptom severity and urgency
3. Provide initial triage recommendations
4. Identify concerning symptom patterns
5. Guide patients on appropriate care levels

Guidelines:
- Use clear, patient-friendly language
- Err on the side of caution for safety
- Provide specific guidance on when to seek immediate care
- Consider symptom combinations and patterns
- Always recommend professional medical evaluation for concerning symptoms"""
    
    def _get_drug_interaction_prompt(self) -> str:
        """System prompt for drug interaction analysis"""
        return """You are a clinical pharmacology AI assistant specialized in medication safety and drug interactions. Your role is to:

1. Analyze potential drug-drug interactions
2. Assess medication contraindications
3. Evaluate dosing appropriateness
4. Identify adverse drug reactions
5. Provide medication safety recommendations

Guidelines:
- Prioritize patient safety above all
- Consider patient-specific factors (age, kidney/liver function, allergies)
- Provide clear severity ratings for interactions
- Recommend monitoring parameters when appropriate
- Always defer to clinical pharmacists for complex cases"""
    
    def _get_health_insights_prompt(self) -> str:
        """System prompt for health insights generation"""
        return """You are a population health AI assistant specialized in generating actionable health insights. Your role is to:

1. Analyze health data patterns and trends
2. Identify risk factors and protective factors
3. Generate personalized health recommendations
4. Provide population health insights
5. Suggest preventive care measures

Guidelines:
- Focus on actionable, evidence-based recommendations
- Consider social determinants of health
- Provide clear, understandable explanations
- Emphasize preventive care and lifestyle modifications
- Respect cultural and individual preferences"""

# Global instance
bedrock_models = BedrockModelManager()
