import logging
import re
from typing import Dict, List, Any, Optional, Tuple
import boto3
from botocore.exceptions import ClientError
import json
import os

logger = logging.getLogger(__name__)

class MedicalNLPProcessor:
    """Production-grade medical NLP processor using AWS Comprehend Medical"""
    
    def __init__(self):
        self.comprehend_medical = boto3.client(
            'comprehendmedical',
            region_name=os.environ.get('AWS_REGION', 'us-east-1')
        )
        
        # Medical term patterns for enhanced processing
        self.symptom_patterns = {
            'pain': r'\b(?:pain|ache|aching|hurt|hurting|sore|tender|throbbing|stabbing|burning|sharp|dull)\b',
            'breathing': r'\b(?:breath|breathing|dyspnea|shortness of breath|sob|wheezing|cough|coughing)\b',
            'cardiac': r'\b(?:chest pain|palpitations|heart|cardiac|tachycardia|bradycardia|arrhythmia)\b',
            'neurological': r'\b(?:headache|dizziness|dizzy|confusion|confused|seizure|numbness|tingling)\b',
            'gastrointestinal': r'\b(?:nausea|vomiting|diarrhea|constipation|abdominal|stomach|belly)\b',
            'fever': r'\b(?:fever|febrile|hot|chills|sweating|temperature)\b'
        }
        
    def extract_medical_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract medical entities from text using AWS Comprehend Medical
        
        Args:
            text: Input text containing medical information
            
        Returns:
            List of extracted medical entities with metadata
        """
        try:
            if not text or not text.strip():
                return []
            
            # Use Comprehend Medical to detect entities
            response = self.comprehend_medical.detect_entities_v2(Text=text)
            
            entities = []
            for entity in response.get('Entities', []):
                processed_entity = {
                    'text': entity['Text'],
                    'category': entity['Category'],
                    'type': entity['Type'],
                    'confidence': entity['Score'],
                    'begin_offset': entity['BeginOffset'],
                    'end_offset': entity['EndOffset'],
                    'attributes': []
                }
                
                # Process attributes
                for attr in entity.get('Attributes', []):
                    processed_entity['attributes'].append({
                        'type': attr['Type'],
                        'text': attr['Text'],
                        'confidence': attr['Score'],
                        'relationship_type': attr.get('RelationshipType'),
                        'begin_offset': attr['BeginOffset'],
                        'end_offset': attr['EndOffset']
                    })
                
                # Add severity and context analysis
                processed_entity['severity'] = self._analyze_severity(entity['Text'], text)
                processed_entity['context'] = self._extract_context(entity, text)
                processed_entity['normalized_term'] = self._normalize_medical_term(entity['Text'])
                
                entities.append(processed_entity)
            
            # Enhance with pattern-based detection
            pattern_entities = self._extract_pattern_entities(text)
            entities.extend(pattern_entities)
            
            # Remove duplicates and sort by confidence
            entities = self._deduplicate_entities(entities)
            entities.sort(key=lambda x: x['confidence'], reverse=True)
            
            return entities
            
        except ClientError as e:
            logger.error(f"Comprehend Medical API error: {str(e)}")
            # Fallback to pattern-based extraction
            return self._extract_pattern_entities(text)
        except Exception as e:
            logger.error(f"Error in medical entity extraction: {str(e)}")
            return []
    
    def detect_phi(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect Protected Health Information (PHI) in text
        
        Args:
            text: Input text to analyze for PHI
            
        Returns:
            List of detected PHI entities
        """
        try:
            response = self.comprehend_medical.detect_phi(Text=text)
            
            phi_entities = []
            for entity in response.get('Entities', []):
                phi_entities.append({
                    'text': entity['Text'],
                    'category': entity['Category'],
                    'type': entity['Type'],
                    'confidence': entity['Score'],
                    'begin_offset': entity['BeginOffset'],
                    'end_offset': entity['EndOffset']
                })
            
            return phi_entities
            
        except ClientError as e:
            logger.error(f"PHI detection error: {str(e)}")
            return []
    
    def infer_icd10_codes(self, text: str) -> List[Dict[str, Any]]:
        """
        Infer ICD-10-CM codes from medical text
        
        Args:
            text: Medical text to analyze
            
        Returns:
            List of inferred ICD-10 codes with confidence scores
        """
        try:
            response = self.comprehend_medical.infer_icd10_cm(Text=text)
            
            icd_codes = []
            for entity in response.get('Entities', []):
                for code in entity.get('ICD10CMConcepts', []):
                    icd_codes.append({
                        'entity_text': entity['Text'],
                        'entity_category': entity['Category'],
                        'entity_type': entity['Type'],
                        'icd10_code': code['Code'],
                        'icd10_description': code['Description'],
                        'confidence': code['Score']
                    })
            
            return sorted(icd_codes, key=lambda x: x['confidence'], reverse=True)
            
        except ClientError as e:
            logger.error(f"ICD-10 inference error: {str(e)}")
            return []
    
    def infer_rx_norm_codes(self, text: str) -> List[Dict[str, Any]]:
        """
        Infer RxNorm codes for medications
        
        Args:
            text: Text containing medication information
            
        Returns:
            List of RxNorm codes with confidence scores
        """
        try:
            response = self.comprehend_medical.infer_rx_norm(Text=text)
            
            rx_codes = []
            for entity in response.get('Entities', []):
                for concept in entity.get('RxNormConcepts', []):
                    rx_codes.append({
                        'entity_text': entity['Text'],
                        'entity_category': entity['Category'],
                        'entity_type': entity['Type'],
                        'rxnorm_code': concept['Code'],
                        'rxnorm_description': concept['Description'],
                        'confidence': concept['Score']
                    })
            
            return sorted(rx_codes, key=lambda x: x['confidence'], reverse=True)
            
        except ClientError as e:
            logger.error(f"RxNorm inference error: {str(e)}")
            return []
    
    def _extract_pattern_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities using regex patterns as fallback"""
        entities = []
        
        for category, pattern in self.symptom_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append({
                    'text': match.group(),
                    'category': 'MEDICAL_CONDITION',
                    'type': category.upper(),
                    'confidence': 0.7,  # Lower confidence for pattern matching
                    'begin_offset': match.start(),
                    'end_offset': match.end(),
                    'attributes': [],
                    'severity': self._analyze_severity(match.group(), text),
                    'context': text[max(0, match.start()-50):match.end()+50],
                    'normalized_term': self._normalize_medical_term(match.group()),
                    'source': 'pattern_matching'
                })
        
        return entities
    
    def _analyze_severity(self, entity_text: str, full_text: str) -> str:
        """Analyze severity of medical entity based on context"""
        entity_lower = entity_text.lower()
        text_lower = full_text.lower()
        
        # High severity indicators
        high_severity_terms = [
            'severe', 'intense', 'excruciating', 'unbearable', 'crushing',
            'sharp', 'stabbing', 'burning', 'throbbing', 'pounding'
        ]
        
        # Medium severity indicators
        medium_severity_terms = [
            'moderate', 'noticeable', 'uncomfortable', 'bothersome',
            'persistent', 'constant', 'recurring'
        ]
        
        # Low severity indicators
        low_severity_terms = [
            'mild', 'slight', 'minor', 'occasional', 'intermittent',
            'dull', 'aching', 'tender'
        ]
        
        # Check for severity indicators in context
        context_start = max(0, full_text.lower().find(entity_lower) - 100)
        context_end = min(len(full_text), full_text.lower().find(entity_lower) + len(entity_lower) + 100)
        context = text_lower[context_start:context_end]
        
        if any(term in context for term in high_severity_terms):
            return 'HIGH'
        elif any(term in context for term in medium_severity_terms):
            return 'MEDIUM'
        elif any(term in context for term in low_severity_terms):
            return 'LOW'
        else:
            return 'UNKNOWN'
    
    def _extract_context(self, entity: Dict, full_text: str) -> str:
        """Extract relevant context around the entity"""
        begin = max(0, entity['BeginOffset'] - 50)
        end = min(len(full_text), entity['EndOffset'] + 50)
        return full_text[begin:end].strip()
    
    def _normalize_medical_term(self, term: str) -> str:
        """Normalize medical terms to standard format"""
        # Basic normalization - can be enhanced with medical ontologies
        normalized = term.lower().strip()
        
        # Common medical term mappings
        term_mappings = {
            'sob': 'shortness of breath',
            'cp': 'chest pain',
            'ha': 'headache',
            'n/v': 'nausea and vomiting',
            'abd pain': 'abdominal pain',
            'diff breathing': 'difficulty breathing'
        }
        
        return term_mappings.get(normalized, normalized)
    
    def _deduplicate_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate entities based on text and position"""
        seen = set()
        unique_entities = []
        
        for entity in entities:
            # Create unique key based on text and position
            key = (
                entity['text'].lower(),
                entity['begin_offset'],
                entity['end_offset']
            )
            
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        return unique_entities
    
    def analyze_medication_adherence(self, text: str) -> Dict[str, Any]:
        """Analyze medication adherence patterns from text"""
        try:
            # Extract medication entities
            entities = self.extract_medical_entities(text)
            medications = [e for e in entities if e['category'] == 'MEDICATION']
            
            # Analyze adherence indicators
            adherence_indicators = {
                'positive': ['taking', 'compliant', 'adherent', 'regular', 'as prescribed'],
                'negative': ['not taking', 'missed', 'forgot', 'stopped', 'non-compliant'],
                'partial': ['sometimes', 'occasionally', 'when needed', 'as needed']
            }
            
            text_lower = text.lower()
            adherence_score = 0.5  # Neutral starting point
            
            for indicator_type, terms in adherence_indicators.items():
                for term in terms:
                    if term in text_lower:
                        if indicator_type == 'positive':
                            adherence_score += 0.2
                        elif indicator_type == 'negative':
                            adherence_score -= 0.3
                        elif indicator_type == 'partial':
                            adherence_score -= 0.1
            
            adherence_score = max(0.0, min(1.0, adherence_score))
            
            return {
                'medications_mentioned': len(medications),
                'adherence_score': adherence_score,
                'adherence_level': self._categorize_adherence(adherence_score),
                'medications': medications
            }
            
        except Exception as e:
            logger.error(f"Error analyzing medication adherence: {str(e)}")
            return {
                'medications_mentioned': 0,
                'adherence_score': 0.5,
                'adherence_level': 'UNKNOWN',
                'medications': []
            }
    
    def _categorize_adherence(self, score: float) -> str:
        """Categorize adherence score into levels"""
        if score >= 0.8:
            return 'HIGH'
        elif score >= 0.6:
            return 'MODERATE'
        elif score >= 0.4:
            return 'LOW'
        else:
            return 'POOR'
