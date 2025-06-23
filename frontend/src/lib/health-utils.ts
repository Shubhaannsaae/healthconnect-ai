/**
 * Health data utilities and calculations for HealthConnect AI
 * Following medical standards and clinical guidelines
 */

import type { VitalSigns, HealthMetrics, HealthTrend, HealthInsight } from '@/types/health';
import { format, subDays, subWeeks, subMonths, subYears, parseISO } from 'date-fns';

export interface HealthCalculationResult {
  value: number;
  unit: string;
  category: 'normal' | 'borderline' | 'abnormal' | 'critical';
  interpretation: string;
  recommendations?: string[];
}

export interface VitalSignsAnalysis {
  overall: 'normal' | 'concerning' | 'critical';
  abnormalValues: Array<{
    parameter: string;
    value: number;
    normalRange: string;
    severity: 'mild' | 'moderate' | 'severe';
  }>;
  recommendations: string[];
  urgentCareNeeded: boolean;
}

export interface HealthRiskAssessment {
  overallRisk: 'low' | 'medium' | 'high' | 'very_high';
  riskFactors: Array<{
    factor: string;
    impact: 'low' | 'medium' | 'high';
    modifiable: boolean;
  }>;
  protectiveFactors: string[];
  recommendations: string[];
  timeframe: '1_year' | '5_years' | '10_years';
}

/**
 * Calculate Body Mass Index (BMI)
 */
export const calculateBMI = (weightKg: number, heightM: number): HealthCalculationResult => {
  if (weightKg <= 0 || heightM <= 0) {
    throw new Error('Weight and height must be positive values');
  }

  const bmi = weightKg / (heightM * heightM);
  let category: 'normal' | 'borderline' | 'abnormal' | 'critical';
  let interpretation: string;
  let recommendations: string[] = [];

  if (bmi < 18.5) {
    category = 'abnormal';
    interpretation = 'Underweight';
    recommendations = [
      'Consult with a healthcare provider about healthy weight gain',
      'Consider nutritional counseling',
      'Evaluate for underlying medical conditions'
    ];
  } else if (bmi >= 18.5 && bmi < 25) {
    category = 'normal';
    interpretation = 'Normal weight';
    recommendations = [
      'Maintain current weight through balanced diet and exercise',
      'Continue regular physical activity'
    ];
  } else if (bmi >= 25 && bmi < 30) {
    category = 'borderline';
    interpretation = 'Overweight';
    recommendations = [
      'Consider weight reduction through diet and exercise',
      'Aim for 5-10% weight loss',
      'Increase physical activity to 150 minutes per week'
    ];
  } else if (bmi >= 30 && bmi < 35) {
    category = 'abnormal';
    interpretation = 'Obesity Class I';
    recommendations = [
      'Consult healthcare provider for weight management plan',
      'Consider structured weight loss program',
      'Screen for obesity-related health conditions'
    ];
  } else if (bmi >= 35 && bmi < 40) {
    category = 'abnormal';
    interpretation = 'Obesity Class II';
    recommendations = [
      'Medical evaluation and treatment recommended',
      'Consider comprehensive weight management program',
      'Evaluate for bariatric surgery candidacy'
    ];
  } else {
    category = 'critical';
    interpretation = 'Obesity Class III (Severe)';
    recommendations = [
      'Immediate medical evaluation required',
      'Consider bariatric surgery evaluation',
      'Comprehensive medical management needed'
    ];
  }

  return {
    value: Math.round(bmi * 10) / 10,
    unit: 'kg/m²',
    category,
    interpretation,
    recommendations
  };
};

/**
 * Calculate Blood Pressure Category
 */
export const calculateBloodPressureCategory = (
  systolic: number, 
  diastolic: number
): HealthCalculationResult => {
  let category: 'normal' | 'borderline' | 'abnormal' | 'critical';
  let interpretation: string;
  let recommendations: string[] = [];

  if (systolic < 120 && diastolic < 80) {
    category = 'normal';
    interpretation = 'Normal';
    recommendations = [
      'Maintain healthy lifestyle',
      'Continue regular exercise and healthy diet'
    ];
  } else if (systolic >= 120 && systolic <= 129 && diastolic < 80) {
    category = 'borderline';
    interpretation = 'Elevated';
    recommendations = [
      'Lifestyle modifications recommended',
      'Reduce sodium intake',
      'Increase physical activity',
      'Monitor blood pressure regularly'
    ];
  } else if ((systolic >= 130 && systolic <= 139) || (diastolic >= 80 && diastolic <= 89)) {
    category = 'abnormal';
    interpretation = 'Stage 1 Hypertension';
    recommendations = [
      'Consult healthcare provider',
      'Lifestyle changes and possible medication',
      'Monitor blood pressure at home',
      'Reduce sodium, increase potassium intake'
    ];
  } else if ((systolic >= 140 && systolic <= 179) || (diastolic >= 90 && diastolic <= 119)) {
    category = 'abnormal';
    interpretation = 'Stage 2 Hypertension';
    recommendations = [
      'Medical treatment required',
      'Antihypertensive medication likely needed',
      'Regular medical monitoring',
      'Comprehensive lifestyle modifications'
    ];
  } else {
    category = 'critical';
    interpretation = 'Hypertensive Crisis';
    recommendations = [
      'Seek immediate medical attention',
      'Emergency medical evaluation required',
      'Do not delay treatment'
    ];
  }

  return {
    value: systolic,
    unit: 'mmHg',
    category,
    interpretation,
    recommendations
  };
};

/**
 * Analyze vital signs comprehensively
 */
export const analyzeVitalSigns = (vitalSigns: VitalSigns): VitalSignsAnalysis => {
  const abnormalValues: Array<{
    parameter: string;
    value: number;
    normalRange: string;
    severity: 'mild' | 'moderate' | 'severe';
  }> = [];

  let urgentCareNeeded = false;
  let overallSeverity: 'normal' | 'concerning' | 'critical' = 'normal';

  // Analyze heart rate
  if (vitalSigns.heartRate < 60 || vitalSigns.heartRate > 100) {
    const severity = (vitalSigns.heartRate < 50 || vitalSigns.heartRate > 120) ? 'severe' :
                    (vitalSigns.heartRate < 55 || vitalSigns.heartRate > 110) ? 'moderate' : 'mild';
    
    abnormalValues.push({
      parameter: 'Heart Rate',
      value: vitalSigns.heartRate,
      normalRange: '60-100 bpm',
      severity
    });

    if (severity === 'severe') {
      urgentCareNeeded = true;
      overallSeverity = 'critical';
    } else if (overallSeverity !== 'critical') {
      overallSeverity = 'concerning';
    }
  }

  // Analyze blood pressure
  const bpCategory = calculateBloodPressureCategory(
    vitalSigns.bloodPressure.systolic,
    vitalSigns.bloodPressure.diastolic
  );

  if (bpCategory.category === 'critical') {
    urgentCareNeeded = true;
    overallSeverity = 'critical';
    abnormalValues.push({
      parameter: 'Blood Pressure',
      value: vitalSigns.bloodPressure.systolic,
      normalRange: '<120/80 mmHg',
      severity: 'severe'
    });
  } else if (bpCategory.category === 'abnormal') {
    abnormalValues.push({
      parameter: 'Blood Pressure',
      value: vitalSigns.bloodPressure.systolic,
      normalRange: '<120/80 mmHg',
      severity: 'moderate'
    });
    if (overallSeverity !== 'critical') {
      overallSeverity = 'concerning';
    }
  }

  // Analyze temperature
  if (vitalSigns.temperature < 36.1 || vitalSigns.temperature > 37.2) {
    const severity = (vitalSigns.temperature < 35 || vitalSigns.temperature > 40) ? 'severe' :
                    (vitalSigns.temperature < 35.5 || vitalSigns.temperature > 38.5) ? 'moderate' : 'mild';
    
    abnormalValues.push({
      parameter: 'Temperature',
      value: vitalSigns.temperature,
      normalRange: '36.1-37.2°C',
      severity
    });

    if (severity === 'severe') {
      urgentCareNeeded = true;
      overallSeverity = 'critical';
    } else if (overallSeverity !== 'critical') {
      overallSeverity = 'concerning';
    }
  }

  // Analyze oxygen saturation
  if (vitalSigns.oxygenSaturation < 95) {
    const severity = vitalSigns.oxygenSaturation < 88 ? 'severe' :
                    vitalSigns.oxygenSaturation < 92 ? 'moderate' : 'mild';
    
    abnormalValues.push({
      parameter: 'Oxygen Saturation',
      value: vitalSigns.oxygenSaturation,
      normalRange: '95-100%',
      severity
    });

    if (severity === 'severe') {
      urgentCareNeeded = true;
      overallSeverity = 'critical';
    } else if (overallSeverity !== 'critical') {
      overallSeverity = 'concerning';
    }
  }

  // Analyze respiratory rate
  if (vitalSigns.respiratoryRate < 12 || vitalSigns.respiratoryRate > 20) {
    const severity = (vitalSigns.respiratoryRate < 8 || vitalSigns.respiratoryRate > 30) ? 'severe' :
                    (vitalSigns.respiratoryRate < 10 || vitalSigns.respiratoryRate > 25) ? 'moderate' : 'mild';
    
    abnormalValues.push({
      parameter: 'Respiratory Rate',
      value: vitalSigns.respiratoryRate,
      normalRange: '12-20 breaths/min',
      severity
    });

    if (severity === 'severe') {
      urgentCareNeeded = true;
      overallSeverity = 'critical';
    } else if (overallSeverity !== 'critical') {
      overallSeverity = 'concerning';
    }
  }

  // Generate recommendations
  const recommendations: string[] = [];
  
  if (urgentCareNeeded) {
    recommendations.push('Seek immediate medical attention');
    recommendations.push('Contact emergency services if symptoms worsen');
  } else if (overallSeverity === 'concerning') {
    recommendations.push('Consult with healthcare provider within 24 hours');
    recommendations.push('Continue monitoring vital signs');
  } else {
    recommendations.push('Continue regular health monitoring');
    recommendations.push('Maintain healthy lifestyle habits');
  }

  return {
    overall: overallSeverity,
    abnormalValues,
    recommendations,
    urgentCareNeeded
  };
};

/**
 * Calculate health trends from historical data
 */
export const calculateHealthTrends = (
  dataPoints: Array<{ timestamp: string; value: number }>,
  timeframe: '24h' | '7d' | '30d' | '90d' | '1y'
): HealthTrend => {
  if (dataPoints.length < 2) {
    throw new Error('At least 2 data points required for trend analysis');
  }

  // Sort data points by timestamp
  const sortedData = dataPoints
    .map(point => ({
      ...point,
      date: parseISO(point.timestamp)
    }))
    .sort((a, b) => a.date.getTime() - b.date.getTime());

  // Calculate trend direction
  const firstValue = sortedData[0].value;
  const lastValue = sortedData[sortedData.length - 1].value;
  const changePercentage = ((lastValue - firstValue) / firstValue) * 100;

  let trend: 'improving' | 'stable' | 'declining' | 'fluctuating';
  
  // Calculate variance to determine if fluctuating
  const mean = sortedData.reduce((sum, point) => sum + point.value, 0) / sortedData.length;
  const variance = sortedData.reduce((sum, point) => sum + Math.pow(point.value - mean, 2), 0) / sortedData.length;
  const standardDeviation = Math.sqrt(variance);
  const coefficientOfVariation = (standardDeviation / mean) * 100;

  if (coefficientOfVariation > 20) {
    trend = 'fluctuating';
  } else if (Math.abs(changePercentage) < 5) {
    trend = 'stable';
  } else if (changePercentage > 0) {
    trend = 'improving';
  } else {
    trend = 'declining';
  }

  return {
    metric: 'generic',
    timeframe,
    trend,
    changePercentage: Math.round(changePercentage * 100) / 100,
    dataPoints: sortedData.map(point => ({
      timestamp: point.timestamp,
      value: point.value
    }))
  };
};

/**
 * Assess cardiovascular risk based on multiple factors
 */
export const assessCardiovascularRisk = (
  age: number,
  gender: 'male' | 'female',
  systolicBP: number,
  totalCholesterol: number,
  hdlCholesterol: number,
  smoker: boolean,
  diabetes: boolean
): HealthRiskAssessment => {
  let riskScore = 0;
  const riskFactors: Array<{
    factor: string;
    impact: 'low' | 'medium' | 'high';
    modifiable: boolean;
  }> = [];

  // Age factor
  if (gender === 'male') {
    if (age >= 45) riskScore += age >= 55 ? 2 : 1;
  } else {
    if (age >= 55) riskScore += age >= 65 ? 2 : 1;
  }

  if (age >= 45) {
    riskFactors.push({
      factor: 'Age',
      impact: age >= 65 ? 'high' : 'medium',
      modifiable: false
    });
  }

  // Blood pressure
  if (systolicBP >= 140) {
    riskScore += 2;
    riskFactors.push({
      factor: 'High Blood Pressure',
      impact: 'high',
      modifiable: true
    });
  } else if (systolicBP >= 130) {
    riskScore += 1;
    riskFactors.push({
      factor: 'Elevated Blood Pressure',
      impact: 'medium',
      modifiable: true
    });
  }

  // Cholesterol
  if (totalCholesterol >= 240) {
    riskScore += 2;
    riskFactors.push({
      factor: 'High Cholesterol',
      impact: 'high',
      modifiable: true
    });
  } else if (totalCholesterol >= 200) {
    riskScore += 1;
    riskFactors.push({
      factor: 'Borderline High Cholesterol',
      impact: 'medium',
      modifiable: true
    });
  }

  // HDL Cholesterol (protective factor)
  const protectiveFactors: string[] = [];
  if (hdlCholesterol >= 60) {
    riskScore -= 1;
    protectiveFactors.push('High HDL Cholesterol');
  } else if (hdlCholesterol < 40) {
    riskScore += 1;
    riskFactors.push({
      factor: 'Low HDL Cholesterol',
      impact: 'medium',
      modifiable: true
    });
  }

  // Smoking
  if (smoker) {
    riskScore += 2;
    riskFactors.push({
      factor: 'Smoking',
      impact: 'high',
      modifiable: true
    });
  }

  // Diabetes
  if (diabetes) {
    riskScore += 2;
    riskFactors.push({
      factor: 'Diabetes',
      impact: 'high',
      modifiable: true
    });
  }

  // Determine overall risk
  let overallRisk: 'low' | 'medium' | 'high' | 'very_high';
  if (riskScore <= 2) {
    overallRisk = 'low';
  } else if (riskScore <= 4) {
    overallRisk = 'medium';
  } else if (riskScore <= 6) {
    overallRisk = 'high';
  } else {
    overallRisk = 'very_high';
  }

  // Generate recommendations
  const recommendations: string[] = [];
  
  if (overallRisk === 'very_high' || overallRisk === 'high') {
    recommendations.push('Consult cardiologist for comprehensive evaluation');
    recommendations.push('Consider statin therapy if appropriate');
    recommendations.push('Aggressive lifestyle modifications needed');
  } else if (overallRisk === 'medium') {
    recommendations.push('Lifestyle modifications recommended');
    recommendations.push('Regular monitoring of risk factors');
    recommendations.push('Consider preventive medications if indicated');
  } else {
    recommendations.push('Maintain healthy lifestyle');
    recommendations.push('Regular health screenings');
  }

  // Add specific recommendations based on risk factors
  if (smoker) {
    recommendations.push('Smoking cessation is critical');
  }
  if (systolicBP >= 130) {
    recommendations.push('Blood pressure management essential');
  }
  if (totalCholesterol >= 200) {
    recommendations.push('Cholesterol management needed');
  }

  return {
    overallRisk,
    riskFactors,
    protectiveFactors,
    recommendations,
    timeframe: '10_years'
  };
};

/**
 * Generate health insights from data patterns
 */
export const generateHealthInsights = (
  vitalSigns: VitalSigns[],
  timeframe: '7d' | '30d' | '90d'
): HealthInsight[] => {
  const insights: HealthInsight[] = [];

  if (vitalSigns.length < 7) {
    return insights;
  }

  // Analyze heart rate patterns
  const heartRates = vitalSigns.map(vs => vs.heartRate);
  const avgHeartRate = heartRates.reduce((sum, hr) => sum + hr, 0) / heartRates.length;
  const heartRateVariability = Math.sqrt(
    heartRates.reduce((sum, hr) => sum + Math.pow(hr - avgHeartRate, 2), 0) / heartRates.length
  );

  if (heartRateVariability > 15) {
    insights.push({
      id: `hr-variability-${Date.now()}`,
      patientId: '',
      type: 'trend_analysis',
      title: 'High Heart Rate Variability Detected',
      description: `Your heart rate has been varying significantly (±${Math.round(heartRateVariability)} bpm). This could indicate stress, irregular sleep, or other factors.`,
      confidence: 0.8,
      priority: 'medium',
      category: 'cardiovascular',
      generatedAt: new Date().toISOString(),
      actionable: true,
      actions: [
        'Monitor stress levels and sleep quality',
        'Consider relaxation techniques',
        'Consult healthcare provider if pattern continues'
      ],
      relatedMetrics: ['heart_rate'],
      aiGenerated: true,
      modelVersion: '1.0'
    });
  }

  // Analyze blood pressure trends
  const systolicReadings = vitalSigns.map(vs => vs.bloodPressure.systolic);
  const recentSystolic = systolicReadings.slice(-7); // Last 7 readings
  const avgRecentSystolic = recentSystolic.reduce((sum, bp) => sum + bp, 0) / recentSystolic.length;

  if (avgRecentSystolic > 130) {
    insights.push({
      id: `bp-trend-${Date.now()}`,
      patientId: '',
      type: 'risk_assessment',
      title: 'Elevated Blood Pressure Pattern',
      description: `Your average blood pressure over the last week has been ${Math.round(avgRecentSystolic)} mmHg, which is above the normal range.`,
      confidence: 0.9,
      priority: 'high',
      category: 'cardiovascular',
      generatedAt: new Date().toISOString(),
      actionable: true,
      actions: [
        'Reduce sodium intake',
        'Increase physical activity',
        'Schedule appointment with healthcare provider',
        'Monitor blood pressure daily'
      ],
      relatedMetrics: ['blood_pressure'],
      aiGenerated: true,
      modelVersion: '1.0'
    });
  }

  return insights;
};

/**
 * Format health values for display
 */
export const formatHealthValue = (
  value: number,
  metric: string,
  includeUnit: boolean = true
): string => {
  const units: Record<string, string> = {
    heart_rate: 'bpm',
    systolic_pressure: 'mmHg',
    diastolic_pressure: 'mmHg',
    temperature: '°C',
    oxygen_saturation: '%',
    respiratory_rate: '/min',
    glucose_level: 'mg/dL',
    bmi: 'kg/m²',
    weight: 'kg',
    height: 'cm'
  };

  const decimals = ['temperature', 'bmi'].includes(metric) ? 1 : 0;
  const formattedValue = value.toFixed(decimals);
  
  if (includeUnit && units[metric]) {
    return `${formattedValue} ${units[metric]}`;
  }
  
  return formattedValue;
};

/**
 * Get health metric normal ranges
 */
export const getHealthMetricRange = (metric: string): { min: number; max: number; unit: string } => {
  const ranges: Record<string, { min: number; max: number; unit: string }> = {
    heart_rate: { min: 60, max: 100, unit: 'bpm' },
    systolic_pressure: { min: 90, max: 120, unit: 'mmHg' },
    diastolic_pressure: { min: 60, max: 80, unit: 'mmHg' },
    temperature: { min: 36.1, max: 37.2, unit: '°C' },
    oxygen_saturation: { min: 95, max: 100, unit: '%' },
    respiratory_rate: { min: 12, max: 20, unit: '/min' },
    glucose_level: { min: 70, max: 140, unit: 'mg/dL' },
    bmi: { min: 18.5, max: 24.9, unit: 'kg/m²' }
  };

  return ranges[metric] || { min: 0, max: 100, unit: '' };
};

/**
 * Check if health value is within normal range
 */
export const isHealthValueNormal = (value: number, metric: string): boolean => {
  const range = getHealthMetricRange(metric);
  return value >= range.min && value <= range.max;
};

/**
 * Get health status color based on value
 */
export const getHealthStatusColor = (value: number, metric: string): string => {
  const range = getHealthMetricRange(metric);
  
  if (value >= range.min && value <= range.max) {
    return 'text-green-600'; // Normal
  } else if (
    (value >= range.min * 0.9 && value < range.min) ||
    (value > range.max && value <= range.max * 1.1)
  ) {
    return 'text-yellow-600'; // Borderline
  } else {
    return 'text-red-600'; // Abnormal
  }
};

/**
 * Calculate health score from multiple metrics
 */
export const calculateHealthScore = (vitalSigns: VitalSigns): number => {
  let score = 100;
  let totalMetrics = 0;

  const metrics = [
    { value: vitalSigns.heartRate, metric: 'heart_rate', weight: 20 },
    { value: vitalSigns.bloodPressure.systolic, metric: 'systolic_pressure', weight: 25 },
    { value: vitalSigns.temperature, metric: 'temperature', weight: 15 },
    { value: vitalSigns.oxygenSaturation, metric: 'oxygen_saturation', weight: 20 },
    { value: vitalSigns.respiratoryRate, metric: 'respiratory_rate', weight: 20 }
  ];

  metrics.forEach(({ value, metric, weight }) => {
    if (value !== undefined && value !== null) {
      const range = getHealthMetricRange(metric);
      const isNormal = isHealthValueNormal(value, metric);
      
      if (!isNormal) {
        // Calculate deviation from normal range
        let deviation = 0;
        if (value < range.min) {
          deviation = (range.min - value) / range.min;
        } else if (value > range.max) {
          deviation = (value - range.max) / range.max;
        }
        
        // Reduce score based on deviation and weight
        const reduction = Math.min(deviation * weight, weight);
        score -= reduction;
      }
      
      totalMetrics += weight;
    }
  });

  // Normalize score to 0-100 range
  return Math.max(0, Math.round(score));
};

export default {
  calculateBMI,
  calculateBloodPressureCategory,
  analyzeVitalSigns,
  calculateHealthTrends,
  assessCardiovascularRisk,
  generateHealthInsights,
  formatHealthValue,
  getHealthMetricRange,
  isHealthValueNormal,
  getHealthStatusColor,
  calculateHealthScore
};
