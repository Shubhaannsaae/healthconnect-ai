/**
 * Health-related TypeScript definitions for HealthConnect AI
 * Following medical standards and best practices
 */

export interface VitalSigns {
    heartRate: number; // beats per minute
    bloodPressure: {
      systolic: number; // mmHg
      diastolic: number; // mmHg
      meanArterialPressure?: number; // mmHg
      pulseWave?: number[];
    };
    temperature: number; // Celsius
    oxygenSaturation: number; // percentage (0-100)
    respiratoryRate: number; // breaths per minute
    glucoseLevel?: number; // mg/dL
    timestamp: string; // ISO 8601 format
    deviceId?: string;
    accuracy?: number; // 0-1 confidence score
    qualityIndicators?: {
      signalQuality: 'excellent' | 'good' | 'fair' | 'poor';
      motionArtifact: boolean;
      measurementConfidence: number;
    };
  }
  
  export interface HealthMetrics {
    bmi?: number;
    bodyFatPercentage?: number;
    muscleMass?: number;
    boneDensity?: number;
    metabolicRate?: number;
    hydrationLevel?: number;
    stressLevel?: number; // 0-100 scale
    sleepQuality?: number; // 0-100 scale
    activityLevel?: number; // steps or activity units
    caloriesBurned?: number;
    vo2Max?: number; // ml/kg/min
  }
  
  export interface Symptom {
    id: string;
    name: string;
    description: string;
    severity: 'mild' | 'moderate' | 'severe' | 'critical';
    duration: string; // human readable duration
    onset: string; // ISO 8601 timestamp
    location?: string; // body part/location
    triggers?: string[];
    relievingFactors?: string[];
    associatedSymptoms?: string[];
    painScale?: number; // 0-10 scale
    frequency?: 'constant' | 'intermittent' | 'occasional' | 'rare';
    pattern?: 'improving' | 'worsening' | 'stable' | 'fluctuating';
  }
  
  export interface MedicalCondition {
    id: string;
    name: string;
    icd10Code?: string;
    snomedCode?: string;
    category: 'acute' | 'chronic' | 'genetic' | 'infectious' | 'autoimmune' | 'mental_health';
    diagnosisDate: string;
    status: 'active' | 'resolved' | 'in_remission' | 'managed';
    severity: 'mild' | 'moderate' | 'severe';
    notes?: string;
    treatmentPlan?: string[];
    medications?: Medication[];
    lastReview?: string;
    nextReview?: string;
  }
  
  export interface Medication {
    id: string;
    name: string;
    genericName?: string;
    dosage: string;
    frequency: string;
    route: 'oral' | 'intravenous' | 'intramuscular' | 'subcutaneous' | 'topical' | 'inhalation';
    startDate: string;
    endDate?: string;
    prescribedBy: string; // provider ID
    indication: string; // reason for prescription
    sideEffects?: string[];
    interactions?: string[];
    adherence?: {
      percentage: number; // 0-100
      missedDoses: number;
      lastTaken?: string;
    };
    rxNormCode?: string;
    ndcCode?: string;
  }
  
  export interface HealthRecord {
    id: string;
    patientId: string;
    providerId?: string;
    timestamp: string;
    recordType: 'vital_signs' | 'symptoms' | 'diagnosis' | 'medication' | 'lab_results' | 'imaging' | 'procedure';
    vitalSigns?: VitalSigns;
    symptoms?: Symptom[];
    conditions?: MedicalCondition[];
    medications?: Medication[];
    labResults?: LabResult[];
    notes?: string;
    attachments?: HealthAttachment[];
    metadata?: {
      source: 'manual_entry' | 'device' | 'ehr_import' | 'api';
      deviceId?: string;
      accuracy?: number;
      verified?: boolean;
      verifiedBy?: string;
      verifiedAt?: string;
    };
  }
  
  export interface LabResult {
    id: string;
    testName: string;
    loincCode?: string;
    value: number | string;
    unit: string;
    referenceRange: {
      min?: number;
      max?: number;
      text?: string;
    };
    status: 'normal' | 'abnormal' | 'critical' | 'pending';
    orderedBy: string; // provider ID
    performedAt: string;
    resultDate: string;
    labName?: string;
    notes?: string;
  }
  
  export interface HealthAttachment {
    id: string;
    filename: string;
    fileType: string;
    fileSize: number;
    url: string;
    uploadedAt: string;
    uploadedBy: string;
    description?: string;
    category: 'image' | 'document' | 'audio' | 'video' | 'other';
  }
  
  export interface HealthAlert {
    id: string;
    patientId: string;
    alertType: 'vital_signs_critical' | 'medication_reminder' | 'appointment_reminder' | 'device_malfunction' | 'emergency';
    severity: 'low' | 'medium' | 'high' | 'critical';
    title: string;
    message: string;
    timestamp: string;
    acknowledged?: boolean;
    acknowledgedBy?: string;
    acknowledgedAt?: string;
    resolved?: boolean;
    resolvedBy?: string;
    resolvedAt?: string;
    actions?: AlertAction[];
    metadata?: Record<string, any>;
  }
  
  export interface AlertAction {
    id: string;
    label: string;
    action: 'acknowledge' | 'resolve' | 'escalate' | 'contact_provider' | 'call_emergency';
    url?: string;
    confirmationRequired?: boolean;
  }
  
  export interface HealthTrend {
    metric: keyof VitalSigns | keyof HealthMetrics;
    timeframe: '24h' | '7d' | '30d' | '90d' | '1y';
    trend: 'improving' | 'stable' | 'declining' | 'fluctuating';
    changePercentage: number;
    dataPoints: Array<{
      timestamp: string;
      value: number;
    }>;
    analysis?: {
      pattern: string;
      insights: string[];
      recommendations: string[];
      confidence: number;
    };
  }
  
  export interface HealthGoal {
    id: string;
    patientId: string;
    title: string;
    description: string;
    category: 'weight_management' | 'fitness' | 'medication_adherence' | 'vital_signs' | 'lifestyle';
    targetValue: number;
    currentValue: number;
    unit: string;
    targetDate: string;
    createdAt: string;
    status: 'active' | 'achieved' | 'paused' | 'cancelled';
    progress: number; // 0-100 percentage
    milestones?: Array<{
      value: number;
      date: string;
      achieved: boolean;
    }>;
  }
  
  export interface HealthInsight {
    id: string;
    patientId: string;
    type: 'trend_analysis' | 'risk_assessment' | 'recommendation' | 'anomaly_detection';
    title: string;
    description: string;
    confidence: number; // 0-1
    priority: 'low' | 'medium' | 'high';
    category: string;
    generatedAt: string;
    validUntil?: string;
    actionable: boolean;
    actions?: string[];
    relatedMetrics?: string[];
    aiGenerated: boolean;
    modelVersion?: string;
  }
  
  export interface EmergencyContact {
    id: string;
    name: string;
    relationship: string;
    phoneNumber: string;
    email?: string;
    address?: Address;
    isPrimary: boolean;
    canReceiveAlerts: boolean;
    preferredContactMethod: 'phone' | 'sms' | 'email';
  }
  
  export interface Address {
    street: string;
    city: string;
    state: string;
    zipCode: string;
    country: string;
    coordinates?: {
      latitude: number;
      longitude: number;
    };
  }
  
  export interface HealthProvider {
    id: string;
    name: string;
    title: string;
    specialty: string;
    licenseNumber: string;
    phoneNumber: string;
    email: string;
    address: Address;
    availability: {
      schedule: Array<{
        dayOfWeek: number; // 0-6 (Sunday-Saturday)
        startTime: string; // HH:mm format
        endTime: string; // HH:mm format
      }>;
      timeZone: string;
      bookingWindow: number; // days in advance
    };
    credentials: string[];
    languages: string[];
    rating?: number; // 0-5
    reviewCount?: number;
    acceptsInsurance: string[];
    consultationTypes: ('in_person' | 'video' | 'phone' | 'chat')[];
  }
  
  // Health data aggregation and analysis types
  export interface HealthSummary {
    patientId: string;
    period: {
      start: string;
      end: string;
    };
    vitalSignsSummary: {
      averages: Partial<VitalSigns>;
      ranges: Record<keyof VitalSigns, { min: number; max: number }>;
      trends: HealthTrend[];
      anomalies: Array<{
        metric: string;
        value: number;
        timestamp: string;
        severity: 'low' | 'medium' | 'high';
      }>;
    };
    medicationAdherence: {
      overall: number; // percentage
      byMedication: Record<string, number>;
      missedDoses: number;
      sideEffectsReported: number;
    };
    symptomsReported: {
      count: number;
      categories: Record<string, number>;
      severity: Record<string, number>;
    };
    goalsProgress: Array<{
      goalId: string;
      progress: number;
      onTrack: boolean;
    }>;
    riskAssessment: {
      overallRisk: 'low' | 'medium' | 'high';
      riskFactors: string[];
      recommendations: string[];
    };
    generatedAt: string;
  }
  
  // Type guards and utility types
  export type HealthDataType = 'vital_signs' | 'symptoms' | 'medications' | 'lab_results' | 'conditions';
  
  export interface HealthDataFilter {
    dateRange?: {
      start: string;
      end: string;
    };
    dataTypes?: HealthDataType[];
    providers?: string[];
    devices?: string[];
    severity?: ('mild' | 'moderate' | 'severe' | 'critical')[];
  }
  
  export interface HealthDataExport {
    format: 'json' | 'csv' | 'pdf' | 'fhir';
    includeAttachments: boolean;
    dateRange: {
      start: string;
      end: string;
    };
    dataTypes: HealthDataType[];
    encryption?: {
      enabled: boolean;
      password?: string;
    };
  }
  
  // API response types
  export interface HealthApiResponse<T = any> {
    success: boolean;
    data?: T;
    error?: {
      code: string;
      message: string;
      details?: any;
    };
    metadata?: {
      timestamp: string;
      requestId: string;
      version: string;
    };
  }
  
  export interface PaginatedHealthResponse<T> extends HealthApiResponse<T[]> {
    pagination: {
      page: number;
      limit: number;
      total: number;
      totalPages: number;
      hasNext: boolean;
      hasPrevious: boolean;
    };
  }
  