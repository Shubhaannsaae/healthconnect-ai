import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
import json
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import xgboost as xgb
import lightgbm as lgb
from prophet import Prophet
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class PredictiveModelEngine:
    """Production-grade predictive modeling engine for healthcare analytics"""[4]
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        
        # Model configurations
        self.model_configs = {
            'risk_prediction': {
                'algorithm': 'xgboost',
                'features': ['age', 'heart_rate', 'blood_pressure', 'glucose_level', 'bmi'],
                'target': 'high_risk',
                'model_type': 'classification'
            },
            'readmission_prediction': {
                'algorithm': 'random_forest',
                'features': ['age', 'length_of_stay', 'comorbidities', 'previous_admissions'],
                'target': 'readmission_30_days',
                'model_type': 'classification'
            },
            'outbreak_detection': {
                'algorithm': 'isolation_forest',
                'features': ['disease_cases', 'geographic_cluster', 'temporal_pattern'],
                'target': 'outbreak_probability',
                'model_type': 'anomaly_detection'
            },
            'resource_optimization': {
                'algorithm': 'prophet',
                'features': ['timestamp', 'resource_demand'],
                'target': 'future_demand',
                'model_type': 'time_series'
            }
        }
    
    def predict_patient_risk(
        self, 
        historical_data: List[Dict[str, Any]], 
        forecast_horizon: str = '7_days',
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """Predict patient risk using machine learning models"""[4]
        
        try:
            if not historical_data:
                return {'error': 'No historical data provided'}
            
            # Prepare data for modeling
            df = pd.DataFrame(historical_data)
            features_df = self._prepare_risk_features(df)
            
            if features_df.empty:
                return {'error': 'Insufficient features for risk prediction'}
            
            # Train or load risk prediction model
            model_result = self._train_risk_model(features_df)
            
            if not model_result['success']:
                return model_result
            
            model = model_result['model']
            feature_columns = model_result['feature_columns']
            
            # Generate predictions for current patients
            current_patients = self._get_current_patients(df)
            predictions = []
            
            for patient_data in current_patients:
                try:
                    # Prepare patient features
                    patient_features = self._extract_patient_features(patient_data, feature_columns)
                    
                    # Make prediction
                    risk_probability = model.predict_proba([patient_features])[0][1]
                    risk_category = self._categorize_risk(risk_probability)
                    
                    # Calculate confidence interval
                    confidence_interval = self._calculate_prediction_confidence(
                        model, patient_features, confidence_level
                    )
                    
                    predictions.append({
                        'patient_id': patient_data.get('patient_id'),
                        'risk_probability': float(risk_probability),
                        'risk_category': risk_category,
                        'confidence_interval': confidence_interval,
                        'contributing_factors': self._identify_risk_factors(patient_features, feature_columns),
                        'prediction_timestamp': datetime.now(timezone.utc).isoformat()
                    })
                    
                except Exception as patient_error:
                    logger.error(f"Error predicting risk for patient: {str(patient_error)}")
                    continue
            
            # Calculate model performance metrics
            performance_metrics = self._calculate_model_performance(model, features_df)
            
            return {
                'success': True,
                'predictions': predictions,
                'model_performance': performance_metrics,
                'forecast_horizon': forecast_horizon,
                'confidence_level': confidence_level,
                'total_predictions': len(predictions),
                'high_risk_count': len([p for p in predictions if p['risk_category'] == 'HIGH']),
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in patient risk prediction: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def detect_disease_outbreaks(
        self, 
        historical_data: List[Dict[str, Any]], 
        sensitivity_threshold: float = 0.8
    ) -> Dict[str, Any]:
        """Detect potential disease outbreaks using anomaly detection"""[4]
        
        try:
            df = pd.DataFrame(historical_data)
            
            # Prepare outbreak detection features
            outbreak_features = self._prepare_outbreak_features(df)
            
            if outbreak_features.empty:
                return {'error': 'Insufficient data for outbreak detection'}
            
            # Apply outbreak detection algorithms
            outbreak_signals = []
            
            # Statistical outbreak detection
            statistical_signals = self._statistical_outbreak_detection(outbreak_features)
            outbreak_signals.extend(statistical_signals)
            
            # Geographic clustering analysis
            if 'location' in df.columns:
                geographic_signals = self._geographic_outbreak_detection(df)
                outbreak_signals.extend(geographic_signals)
            
            # Temporal pattern analysis
            temporal_signals = self._temporal_outbreak_detection(outbreak_features)
            outbreak_signals.extend(temporal_signals)
            
            # Machine learning-based detection
            ml_signals = self._ml_outbreak_detection(outbreak_features, sensitivity_threshold)
            outbreak_signals.extend(ml_signals)
            
            # Consolidate and rank outbreak signals
            consolidated_signals = self._consolidate_outbreak_signals(outbreak_signals)
            
            # Generate outbreak risk assessment
            risk_assessment = self._assess_outbreak_risk(consolidated_signals)
            
            return {
                'success': True,
                'outbreak_signals': consolidated_signals,
                'risk_assessment': risk_assessment,
                'sensitivity_threshold': sensitivity_threshold,
                'detection_methods': ['statistical', 'geographic', 'temporal', 'machine_learning'],
                'total_signals': len(consolidated_signals),
                'high_risk_signals': len([s for s in consolidated_signals if s['risk_level'] == 'HIGH']),
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in outbreak detection: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def optimize_resource_allocation(
        self, 
        historical_data: List[Dict[str, Any]], 
        forecast_horizon: str = '7_days'
    ) -> Dict[str, Any]:
        """Optimize healthcare resource allocation using predictive modeling"""[4]
        
        try:
            df = pd.DataFrame(historical_data)
            
            # Prepare resource utilization data
            resource_data = self._prepare_resource_data(df)
            
            if resource_data.empty:
                return {'error': 'Insufficient resource utilization data'}
            
            # Forecast resource demand
            demand_forecasts = {}
            
            resource_types = ['emergency_visits', 'consultations', 'device_usage', 'staff_hours']
            
            for resource_type in resource_types:
                if resource_type in resource_data.columns:
                    try:
                        forecast = self._forecast_resource_demand(
                            resource_data, resource_type, forecast_horizon
                        )
                        demand_forecasts[resource_type] = forecast
                    except Exception as forecast_error:
                        logger.error(f"Error forecasting {resource_type}: {str(forecast_error)}")
                        continue
            
            # Optimize allocation based on forecasts
            optimization_results = self._optimize_allocation(demand_forecasts, forecast_horizon)
            
            # Calculate efficiency metrics
            efficiency_metrics = self._calculate_efficiency_metrics(
                resource_data, demand_forecasts, optimization_results
            )
            
            # Generate resource recommendations
            recommendations = self._generate_resource_recommendations(
                demand_forecasts, optimization_results
            )
            
            return {
                'success': True,
                'demand_forecasts': demand_forecasts,
                'optimization_results': optimization_results,
                'efficiency_metrics': efficiency_metrics,
                'recommendations': recommendations,
                'forecast_horizon': forecast_horizon,
                'resource_types_analyzed': list(demand_forecasts.keys()),
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in resource optimization: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def predict_readmission_risk(
        self, 
        historical_data: List[Dict[str, Any]], 
        time_window: str = '30_days'
    ) -> Dict[str, Any]:
        """Predict patient readmission risk"""[4]
        
        try:
            df = pd.DataFrame(historical_data)
            
            # Prepare readmission features
            readmission_features = self._prepare_readmission_features(df, time_window)
            
            if readmission_features.empty:
                return {'error': 'Insufficient data for readmission prediction'}
            
            # Train readmission model
            model_result = self._train_readmission_model(readmission_features)
            
            if not model_result['success']:
                return model_result
            
            model = model_result['model']
            feature_columns = model_result['feature_columns']
            
            # Generate readmission predictions
            current_discharges = self._get_recent_discharges(df, time_window)
            predictions = []
            
            for discharge_data in current_discharges:
                try:
                    # Extract features for discharged patient
                    patient_features = self._extract_readmission_features(
                        discharge_data, feature_columns
                    )
                    
                    # Predict readmission probability
                    readmission_prob = model.predict_proba([patient_features])[0][1]
                    risk_category = self._categorize_readmission_risk(readmission_prob)
                    
                    # Identify key risk factors
                    risk_factors = self._identify_readmission_risk_factors(
                        patient_features, feature_columns, model
                    )
                    
                    predictions.append({
                        'patient_id': discharge_data.get('patient_id'),
                        'discharge_date': discharge_data.get('discharge_date'),
                        'readmission_probability': float(readmission_prob),
                        'risk_category': risk_category,
                        'key_risk_factors': risk_factors,
                        'time_window': time_window,
                        'prediction_timestamp': datetime.now(timezone.utc).isoformat()
                    })
                    
                except Exception as patient_error:
                    logger.error(f"Error predicting readmission for patient: {str(patient_error)}")
                    continue
            
            # Calculate model performance
            performance_metrics = self._calculate_readmission_model_performance(
                model, readmission_features
            )
            
            return {
                'success': True,
                'predictions': predictions,
                'model_performance': performance_metrics,
                'time_window': time_window,
                'total_predictions': len(predictions),
                'high_risk_count': len([p for p in predictions if p['risk_category'] == 'HIGH']),
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in readmission prediction: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def predict_medication_adherence(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Predict medication adherence patterns"""[4]
        
        try:
            df = pd.DataFrame(historical_data)
            
            # Prepare medication adherence features
            adherence_features = self._prepare_adherence_features(df)
            
            if adherence_features.empty:
                return {'error': 'Insufficient medication data for adherence prediction'}
            
            # Train adherence model
            model_result = self._train_adherence_model(adherence_features)
            
            if not model_result['success']:
                return model_result
            
            model = model_result['model']
            feature_columns = model_result['feature_columns']
            
            # Generate adherence predictions
            current_patients = self._get_patients_on_medication(df)
            predictions = []
            
            for patient_data in current_patients:
                try:
                    # Extract adherence features
                    patient_features = self._extract_adherence_features(
                        patient_data, feature_columns
                    )
                    
                    # Predict adherence probability
                    adherence_prob = model.predict_proba([patient_features])[0][1]
                    adherence_category = self._categorize_adherence(adherence_prob)
                    
                    # Identify adherence barriers
                    barriers = self._identify_adherence_barriers(
                        patient_features, feature_columns
                    )
                    
                    # Generate intervention recommendations
                    interventions = self._recommend_adherence_interventions(
                        adherence_prob, barriers
                    )
                    
                    predictions.append({
                        'patient_id': patient_data.get('patient_id'),
                        'adherence_probability': float(adherence_prob),
                        'adherence_category': adherence_category,
                        'identified_barriers': barriers,
                        'recommended_interventions': interventions,
                        'prediction_timestamp': datetime.now(timezone.utc).isoformat()
                    })
                    
                except Exception as patient_error:
                    logger.error(f"Error predicting adherence for patient: {str(patient_error)}")
                    continue
            
            # Calculate model performance
            performance_metrics = self._calculate_adherence_model_performance(
                model, adherence_features
            )
            
            return {
                'success': True,
                'predictions': predictions,
                'model_performance': performance_metrics,
                'total_predictions': len(predictions),
                'low_adherence_count': len([p for p in predictions if p['adherence_category'] == 'LOW']),
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in medication adherence prediction: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def calculate_model_performance(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive model performance metrics"""[4]
        
        try:
            performance_summary = {
                'models_evaluated': [],
                'overall_performance': {},
                'individual_performance': {}
            }
            
            for model_name, model_results in results.items():
                if isinstance(model_results, dict) and model_results.get('success', False):
                    performance_summary['models_evaluated'].append(model_name)
                    
                    # Extract model-specific performance metrics
                    model_performance = model_results.get('model_performance', {})
                    performance_summary['individual_performance'][model_name] = model_performance
            
            # Calculate overall performance metrics
            if performance_summary['individual_performance']:
                accuracy_scores = []
                precision_scores = []
                
                for model_perf in performance_summary['individual_performance'].values():
                    if 'accuracy' in model_perf:
                        accuracy_scores.append(model_perf['accuracy'])
                    if 'precision' in model_perf:
                        precision_scores.append(model_perf['precision'])
                
                performance_summary['overall_performance'] = {
                    'average_accuracy': np.mean(accuracy_scores) if accuracy_scores else 0,
                    'average_precision': np.mean(precision_scores) if precision_scores else 0,
                    'models_count': len(performance_summary['individual_performance'])
                }
            
            return performance_summary
            
        except Exception as e:
            logger.error(f"Error calculating model performance: {str(e)}")
            return {}
    
    # Helper methods for data preparation and model training
    def _prepare_risk_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for risk prediction model"""
        
        try:
            features_df = pd.DataFrame()
            
            # Basic demographic features
            if 'age' in df.columns:
                features_df['age'] = pd.to_numeric(df['age'], errors='coerce')
            
            if 'gender' in df.columns:
                le = LabelEncoder()
                features_df['gender_encoded'] = le.fit_transform(df['gender'].fillna('unknown'))
            
            # Vital signs features
            vital_signs = ['heart_rate', 'systolic_pressure', 'diastolic_pressure', 'temperature']
            for vs in vital_signs:
                if vs in df.columns:
                    features_df[vs] = pd.to_numeric(df[vs], errors='coerce')
            
            # Health indicators
            if 'glucose_level' in df.columns:
                features_df['glucose_level'] = pd.to_numeric(df['glucose_level'], errors='coerce')
            
            if 'bmi' in df.columns:
                features_df['bmi'] = pd.to_numeric(df['bmi'], errors='coerce')
            
            # Create target variable (high risk indicator)
            features_df['high_risk'] = self._create_risk_target(df)
            
            # Remove rows with too many missing values
            features_df = features_df.dropna(thresh=len(features_df.columns) * 0.7)
            
            return features_df
            
        except Exception as e:
            logger.error(f"Error preparing risk features: {str(e)}")
            return pd.DataFrame()
    
    def _create_risk_target(self, df: pd.DataFrame) -> pd.Series:
        """Create binary risk target variable"""
        
        risk_indicators = []
        
        for _, row in df.iterrows():
            risk_score = 0
            
            # Age risk
            age = pd.to_numeric(row.get('age', 0), errors='coerce')
            if age > 65:
                risk_score += 1
            
            # Vital signs risk
            hr = pd.to_numeric(row.get('heart_rate', 75), errors='coerce')
            if hr < 50 or hr > 120:
                risk_score += 1
            
            # Emergency history
            if 'emergency_visits' in row and pd.to_numeric(row['emergency_visits'], errors='coerce') > 0:
                risk_score += 1
            
            # Chronic conditions
            conditions = str(row.get('conditions', '')).lower()
            if any(condition in conditions for condition in ['diabetes', 'hypertension', 'heart']):
                risk_score += 1
            
            # High risk if 2 or more risk factors
            risk_indicators.append(1 if risk_score >= 2 else 0)
        
        return pd.Series(risk_indicators)
    
    def _train_risk_model(self, features_df: pd.DataFrame) -> Dict[str, Any]:
        """Train risk prediction model"""
        
        try:
            # Prepare features and target
            target_col = 'high_risk'
            feature_cols = [col for col in features_df.columns if col != target_col]
            
            X = features_df[feature_cols].fillna(features_df[feature_cols].median())
            y = features_df[target_col]
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train XGBoost model
            model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
            
            model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            y_pred = model.predict(X_test_scaled)
            y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
            
            performance_metrics = {
                'accuracy': accuracy_score(y_test, y_pred),
                'precision': precision_score(y_test, y_pred),
                'recall': recall_score(y_test, y_pred),
                'f1_score': f1_score(y_test, y_pred),
                'roc_auc': roc_auc_score(y_test, y_pred_proba)
            }
            
            # Store model and scaler
            self.models['risk_prediction'] = model
            self.scalers['risk_prediction'] = scaler
            
            return {
                'success': True,
                'model': model,
                'scaler': scaler,
                'feature_columns': feature_cols,
                'performance_metrics': performance_metrics
            }
            
        except Exception as e:
            logger.error(f"Error training risk model: {str(e)}")
            return {'success': False, 'error': str(e)}
