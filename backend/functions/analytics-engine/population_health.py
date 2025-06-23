import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
import json
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class PopulationHealthAnalyzer:
    """Production-grade population health analytics engine"""[2]
    
    def __init__(self):
        self.scaler = StandardScaler()
        
        # Population health metrics definitions
        self.health_indicators = {
            'cardiovascular': {
                'metrics': ['heart_rate', 'blood_pressure', 'cholesterol'],
                'risk_thresholds': {
                    'heart_rate': {'low': 60, 'high': 100},
                    'systolic_bp': {'low': 90, 'high': 140},
                    'diastolic_bp': {'low': 60, 'high': 90}
                }
            },
            'metabolic': {
                'metrics': ['glucose_level', 'bmi', 'hba1c'],
                'risk_thresholds': {
                    'glucose_level': {'low': 70, 'high': 140},
                    'bmi': {'low': 18.5, 'high': 25},
                    'hba1c': {'low': 4, 'high': 5.7}
                }
            },
            'respiratory': {
                'metrics': ['oxygen_saturation', 'respiratory_rate'],
                'risk_thresholds': {
                    'oxygen_saturation': {'low': 95, 'high': 100},
                    'respiratory_rate': {'low': 12, 'high': 20}
                }
            }
        }
        
        # Disease prevalence tracking
        self.disease_categories = {
            'chronic': ['diabetes', 'hypertension', 'heart_disease', 'copd'],
            'infectious': ['flu', 'covid', 'pneumonia', 'bronchitis'],
            'mental_health': ['depression', 'anxiety', 'bipolar', 'ptsd'],
            'autoimmune': ['rheumatoid_arthritis', 'lupus', 'multiple_sclerosis']
        }
    
    def analyze_population_health(
        self, 
        health_data: List[Dict[str, Any]], 
        include_demographics: bool = True,
        include_risk_stratification: bool = True,
        include_outcome_metrics: bool = True
    ) -> Dict[str, Any]:
        """Comprehensive population health analysis"""[2]
        
        try:
            if not health_data:
                return {'error': 'No health data provided'}
            
            # Convert to DataFrame for analysis
            df = pd.DataFrame(health_data)
            
            analysis_results = {
                'population_size': len(df),
                'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
                'data_quality_score': self._calculate_data_quality_score(df)
            }
            
            # Basic population statistics
            analysis_results['basic_statistics'] = self._calculate_basic_statistics(df)
            
            # Demographics analysis
            if include_demographics:
                analysis_results['demographics'] = self._analyze_demographics(df)
            
            # Health indicators analysis
            analysis_results['health_indicators'] = self._analyze_health_indicators(df)
            
            # Disease prevalence analysis
            analysis_results['disease_prevalence'] = self._analyze_disease_prevalence(df)
            
            # Risk stratification
            if include_risk_stratification:
                analysis_results['risk_stratification'] = self._perform_risk_stratification(df)
            
            # Outcome metrics
            if include_outcome_metrics:
                analysis_results['outcome_metrics'] = self._calculate_outcome_metrics(df)
            
            # Population clustering
            analysis_results['population_clusters'] = self._perform_population_clustering(df)
            
            # Health disparities analysis
            analysis_results['health_disparities'] = self._analyze_health_disparities(df)
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error in population health analysis: {str(e)}")
            return {'error': str(e)}
    
    def calculate_key_population_metrics(self, health_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate key population health metrics"""[2]
        
        try:
            df = pd.DataFrame(health_data)
            
            metrics = {
                'total_population': len(df),
                'active_patients': len(df[df['timestamp'] >= (datetime.now() - timedelta(days=30)).isoformat()]),
                'emergency_rate': self._calculate_emergency_rate(df),
                'chronic_disease_prevalence': self._calculate_chronic_disease_prevalence(df),
                'average_health_score': self._calculate_average_health_score(df),
                'mortality_indicators': self._calculate_mortality_indicators(df),
                'healthcare_utilization': self._calculate_healthcare_utilization(df),
                'preventive_care_metrics': self._calculate_preventive_care_metrics(df)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating key metrics: {str(e)}")
            return {}
    
    def detect_health_trends(self, health_data: List[Dict[str, Any]], time_range: str) -> Dict[str, Any]:
        """Detect health trends over time"""[4]
        
        try:
            df = pd.DataFrame(health_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            trends = {}
            
            # Vital signs trends
            trends['vital_signs'] = self._analyze_vital_signs_trends(df)
            
            # Disease incidence trends
            trends['disease_incidence'] = self._analyze_disease_incidence_trends(df)
            
            # Emergency events trends
            trends['emergency_events'] = self._analyze_emergency_trends(df)
            
            # Seasonal patterns
            trends['seasonal_patterns'] = self._detect_seasonal_patterns(df)
            
            # Age group trends
            trends['age_group_trends'] = self._analyze_age_group_trends(df)
            
            # Geographic trends (if location data available)
            if 'location' in df.columns:
                trends['geographic_trends'] = self._analyze_geographic_trends(df)
            
            return trends
            
        except Exception as e:
            logger.error(f"Error detecting health trends: {str(e)}")
            return {}
    
    def generate_population_health_alerts(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate population health alerts based on analysis"""[2]
        
        alerts = []
        
        try:
            # Check for disease outbreak indicators
            disease_prevalence = analysis_results.get('disease_prevalence', {})
            for disease, prevalence in disease_prevalence.items():
                if prevalence.get('current_rate', 0) > prevalence.get('baseline_rate', 0) * 1.5:
                    alerts.append({
                        'alert_type': 'disease_outbreak',
                        'disease': disease,
                        'severity': 'HIGH',
                        'current_rate': prevalence.get('current_rate'),
                        'baseline_rate': prevalence.get('baseline_rate'),
                        'description': f'Significant increase in {disease} cases detected',
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    })
            
            # Check for emergency rate spikes
            emergency_rate = analysis_results.get('emergency_rate', 0)
            if emergency_rate > 0.1:  # More than 10% emergency rate
                alerts.append({
                    'alert_type': 'high_emergency_rate',
                    'severity': 'MEDIUM',
                    'emergency_rate': emergency_rate,
                    'description': f'Emergency rate elevated at {emergency_rate:.2%}',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
            
            # Check for health disparities
            disparities = analysis_results.get('health_disparities', {})
            for disparity_type, disparity_data in disparities.items():
                if disparity_data.get('significance_level', 1.0) < 0.05:
                    alerts.append({
                        'alert_type': 'health_disparity',
                        'disparity_type': disparity_type,
                        'severity': 'MEDIUM',
                        'significance_level': disparity_data.get('significance_level'),
                        'description': f'Significant health disparity detected in {disparity_type}',
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error generating population health alerts: {str(e)}")
            return []
    
    def _calculate_basic_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate basic population statistics"""
        
        stats = {
            'total_records': len(df),
            'unique_patients': df['patient_id'].nunique() if 'patient_id' in df.columns else 0,
            'date_range': {
                'start': df['timestamp'].min() if 'timestamp' in df.columns else None,
                'end': df['timestamp'].max() if 'timestamp' in df.columns else None
            }
        }
        
        # Calculate age statistics if available
        if 'age' in df.columns:
            stats['age_statistics'] = {
                'mean_age': df['age'].mean(),
                'median_age': df['age'].median(),
                'age_range': {
                    'min': df['age'].min(),
                    'max': df['age'].max()
                }
            }
        
        return stats
    
    def _analyze_demographics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze population demographics"""
        
        demographics = {}
        
        # Age distribution
        if 'age' in df.columns:
            demographics['age_distribution'] = {
                'pediatric_0_17': len(df[df['age'] < 18]) / len(df),
                'adult_18_64': len(df[(df['age'] >= 18) & (df['age'] < 65)]) / len(df),
                'elderly_65_plus': len(df[df['age'] >= 65]) / len(df)
            }
        
        # Gender distribution
        if 'gender' in df.columns:
            gender_counts = df['gender'].value_counts(normalize=True)
            demographics['gender_distribution'] = gender_counts.to_dict()
        
        # Geographic distribution
        if 'location' in df.columns:
            location_counts = df['location'].value_counts(normalize=True)
            demographics['geographic_distribution'] = location_counts.head(10).to_dict()
        
        return demographics
    
    def _analyze_health_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze health indicators across population"""
        
        indicators = {}
        
        for category, config in self.health_indicators.items():
            category_results = {}
            
            for metric in config['metrics']:
                if metric in df.columns:
                    values = df[metric].dropna()
                    if len(values) > 0:
                        category_results[metric] = {
                            'mean': values.mean(),
                            'median': values.median(),
                            'std': values.std(),
                            'percentiles': {
                                '25th': values.quantile(0.25),
                                '75th': values.quantile(0.75),
                                '95th': values.quantile(0.95)
                            },
                            'out_of_range_percentage': self._calculate_out_of_range_percentage(
                                values, config['risk_thresholds'].get(metric, {})
                            )
                        }
            
            if category_results:
                indicators[category] = category_results
        
        return indicators
    
    def _analyze_disease_prevalence(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze disease prevalence in population"""
        
        prevalence = {}
        
        # Extract disease information from health data
        for category, diseases in self.disease_categories.items():
            category_prevalence = {}
            
            for disease in diseases:
                # Look for disease mentions in various fields
                disease_cases = 0
                total_cases = len(df)
                
                # Check in diagnosis fields, symptoms, etc.
                for col in df.columns:
                    if 'diagnosis' in col.lower() or 'condition' in col.lower() or 'symptom' in col.lower():
                        disease_mentions = df[col].astype(str).str.contains(disease, case=False, na=False)
                        disease_cases += disease_mentions.sum()
                
                if total_cases > 0:
                    prevalence_rate = disease_cases / total_cases
                    category_prevalence[disease] = {
                        'cases': disease_cases,
                        'prevalence_rate': prevalence_rate,
                        'per_100k': prevalence_rate * 100000
                    }
            
            if category_prevalence:
                prevalence[category] = category_prevalence
        
        return prevalence
    
    def _perform_risk_stratification(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Perform population risk stratification"""
        
        try:
            # Calculate composite risk scores
            risk_scores = []
            
            for _, row in df.iterrows():
                risk_score = self._calculate_individual_risk_score(row)
                risk_scores.append(risk_score)
            
            df['risk_score'] = risk_scores
            
            # Stratify into risk categories
            risk_stratification = {
                'low_risk': len(df[df['risk_score'] < 0.3]) / len(df),
                'medium_risk': len(df[(df['risk_score'] >= 0.3) & (df['risk_score'] < 0.7)]) / len(df),
                'high_risk': len(df[df['risk_score'] >= 0.7]) / len(df)
            }
            
            # Risk factor analysis
            risk_factors = self._analyze_risk_factors(df)
            
            return {
                'risk_distribution': risk_stratification,
                'risk_factors': risk_factors,
                'average_risk_score': np.mean(risk_scores),
                'risk_score_std': np.std(risk_scores)
            }
            
        except Exception as e:
            logger.error(f"Error in risk stratification: {str(e)}")
            return {}
    
    def _calculate_individual_risk_score(self, patient_data: pd.Series) -> float:
        """Calculate individual patient risk score"""
        
        risk_score = 0.0
        
        # Age risk
        age = patient_data.get('age', 0)
        if age > 65:
            risk_score += 0.3
        elif age > 45:
            risk_score += 0.1
        
        # Vital signs risk
        if 'heart_rate' in patient_data:
            hr = patient_data['heart_rate']
            if hr < 50 or hr > 120:
                risk_score += 0.2
        
        if 'blood_pressure' in patient_data:
            bp_data = patient_data['blood_pressure']
            if isinstance(bp_data, dict):
                systolic = bp_data.get('systolic', 120)
                if systolic > 160:
                    risk_score += 0.3
                elif systolic > 140:
                    risk_score += 0.1
        
        # Chronic conditions risk
        chronic_conditions = ['diabetes', 'hypertension', 'heart_disease']
        for condition in chronic_conditions:
            if condition in str(patient_data.get('conditions', '')).lower():
                risk_score += 0.2
        
        return min(1.0, risk_score)
    
    def _perform_population_clustering(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Perform population clustering analysis"""
        
        try:
            # Prepare features for clustering
            numeric_features = []
            feature_names = []
            
            # Add age if available
            if 'age' in df.columns:
                numeric_features.append(df['age'].fillna(df['age'].median()))
                feature_names.append('age')
            
            # Add vital signs
            vital_signs = ['heart_rate', 'systolic_pressure', 'diastolic_pressure', 'temperature']
            for vs in vital_signs:
                if vs in df.columns:
                    numeric_features.append(df[vs].fillna(df[vs].median()))
                    feature_names.append(vs)
            
            if len(numeric_features) < 2:
                return {'error': 'Insufficient numeric features for clustering'}
            
            # Prepare feature matrix
            X = np.column_stack(numeric_features)
            X_scaled = self.scaler.fit_transform(X)
            
            # Perform K-means clustering
            optimal_k = self._find_optimal_clusters(X_scaled)
            kmeans = KMeans(n_clusters=optimal_k, random_state=42)
            cluster_labels = kmeans.fit_predict(X_scaled)
            
            # Analyze clusters
            cluster_analysis = {}
            for i in range(optimal_k):
                cluster_mask = cluster_labels == i
                cluster_data = df[cluster_mask]
                
                cluster_analysis[f'cluster_{i}'] = {
                    'size': len(cluster_data),
                    'percentage': len(cluster_data) / len(df),
                    'characteristics': self._analyze_cluster_characteristics(cluster_data, feature_names, X[cluster_mask])
                }
            
            return {
                'optimal_clusters': optimal_k,
                'cluster_analysis': cluster_analysis,
                'feature_names': feature_names
            }
            
        except Exception as e:
            logger.error(f"Error in population clustering: {str(e)}")
            return {}
    
    def _find_optimal_clusters(self, X: np.ndarray) -> int:
        """Find optimal number of clusters using elbow method"""
        
        try:
            inertias = []
            k_range = range(2, min(11, len(X) // 2))
            
            for k in k_range:
                kmeans = KMeans(n_clusters=k, random_state=42)
                kmeans.fit(X)
                inertias.append(kmeans.inertia_)
            
            # Find elbow point
            if len(inertias) >= 3:
                # Simple elbow detection
                diffs = np.diff(inertias)
                diff2 = np.diff(diffs)
                elbow_idx = np.argmax(diff2) + 2
                return k_range[elbow_idx] if elbow_idx < len(k_range) else 3
            else:
                return 3
                
        except Exception:
            return 3
    
    def _analyze_cluster_characteristics(self, cluster_data: pd.DataFrame, feature_names: List[str], feature_values: np.ndarray) -> Dict[str, Any]:
        """Analyze characteristics of a population cluster"""
        
        characteristics = {}
        
        # Feature means
        for i, feature in enumerate(feature_names):
            characteristics[f'avg_{feature}'] = np.mean(feature_values[:, i])
        
        # Demographics
        if 'age' in cluster_data.columns:
            characteristics['age_distribution'] = {
                'mean': cluster_data['age'].mean(),
                'std': cluster_data['age'].std()
            }
        
        # Health conditions prevalence
        if 'conditions' in cluster_data.columns:
            conditions = cluster_data['conditions'].astype(str).str.lower()
            for condition in ['diabetes', 'hypertension', 'heart_disease']:
                prevalence = conditions.str.contains(condition, na=False).mean()
                characteristics[f'{condition}_prevalence'] = prevalence
        
        return characteristics
    
    def _analyze_health_disparities(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze health disparities across different groups"""
        
        disparities = {}
        
        try:
            # Age-based disparities
            if 'age' in df.columns:
                disparities['age_based'] = self._analyze_age_disparities(df)
            
            # Gender-based disparities
            if 'gender' in df.columns:
                disparities['gender_based'] = self._analyze_gender_disparities(df)
            
            # Geographic disparities
            if 'location' in df.columns:
                disparities['geographic'] = self._analyze_geographic_disparities(df)
            
            return disparities
            
        except Exception as e:
            logger.error(f"Error analyzing health disparities: {str(e)}")
            return {}
    
    def _calculate_data_quality_score(self, df: pd.DataFrame) -> float:
        """Calculate data quality score for the dataset"""
        
        try:
            total_cells = df.shape[0] * df.shape[1]
            missing_cells = df.isnull().sum().sum()
            completeness = 1 - (missing_cells / total_cells)
            
            # Check for duplicate records
            duplicates = df.duplicated().sum()
            uniqueness = 1 - (duplicates / len(df))
            
            # Overall quality score
            quality_score = (completeness * 0.7) + (uniqueness * 0.3)
            
            return round(quality_score, 3)
            
        except Exception:
            return 0.5
    
    def assess_data_quality(self, health_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Comprehensive data quality assessment"""
        
        try:
            df = pd.DataFrame(health_data)
            
            assessment = {
                'completeness': self._assess_completeness(df),
                'consistency': self._assess_consistency(df),
                'accuracy': self._assess_accuracy(df),
                'timeliness': self._assess_timeliness(df),
                'overall_score': self._calculate_data_quality_score(df)
            }
            
            return assessment
            
        except Exception as e:
            logger.error(f"Error in data quality assessment: {str(e)}")
            return {}
    
    def generate_population_recommendations(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate population health recommendations based on analysis"""[2]
        
        recommendations = []
        
        try:
            # Risk stratification recommendations
            risk_data = analysis_results.get('risk_stratification', {})
            high_risk_percentage = risk_data.get('risk_distribution', {}).get('high_risk', 0)
            
            if high_risk_percentage > 0.2:  # More than 20% high risk
                recommendations.append({
                    'category': 'risk_management',
                    'priority': 'HIGH',
                    'recommendation': 'Implement targeted intervention programs for high-risk population',
                    'rationale': f'{high_risk_percentage:.1%} of population classified as high-risk',
                    'expected_impact': 'Reduce emergency events by 25-40%'
                })
            
            # Disease prevalence recommendations
            disease_data = analysis_results.get('disease_prevalence', {})
            for category, diseases in disease_data.items():
                for disease, prevalence_info in diseases.items():
                    if prevalence_info.get('prevalence_rate', 0) > 0.1:  # More than 10% prevalence
                        recommendations.append({
                            'category': 'disease_prevention',
                            'priority': 'MEDIUM',
                            'recommendation': f'Enhance {disease} prevention and management programs',
                            'rationale': f'High prevalence of {disease} detected ({prevalence_info.get("prevalence_rate", 0):.1%})',
                            'expected_impact': 'Reduce disease progression and complications'
                        })
            
            # Health disparities recommendations
            disparities = analysis_results.get('health_disparities', {})
            if disparities:
                recommendations.append({
                    'category': 'health_equity',
                    'priority': 'HIGH',
                    'recommendation': 'Address identified health disparities through targeted interventions',
                    'rationale': 'Significant health disparities detected across population groups',
                    'expected_impact': 'Improve health outcomes for underserved populations'
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return []
