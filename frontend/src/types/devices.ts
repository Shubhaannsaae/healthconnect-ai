/**
 * IoT Device-related TypeScript definitions for HealthConnect AI
 * Following IoT and medical device standards
 */

export interface DeviceInfo {
    id: string;
    name: string;
    type: DeviceType;
    manufacturer: string;
    model: string;
    serialNumber: string;
    firmwareVersion: string;
    hardwareVersion?: string;
    macAddress?: string;
    imei?: string; // for cellular devices
    certifications: DeviceCertification[];
    regulatoryApprovals: string[]; // FDA, CE, etc.
    configuration: DeviceConfiguration;
    capabilities: string[];
  }
  
  export type DeviceType = 
    | 'heart_rate_monitor'
    | 'blood_pressure_cuff'
    | 'glucose_meter'
    | 'temperature_sensor'
    | 'pulse_oximeter'
    | 'activity_tracker'
    | 'ecg_monitor'
    | 'respiratory_monitor'
    | 'weight_scale'
    | 'sleep_monitor'
    | 'medication_dispenser'
    | 'emergency_button'
    | 'fall_detector'
    | 'air_quality_monitor';
  
  export interface DeviceCertification {
    type: 'FDA' | 'CE' | 'ISO13485' | 'ISO15197' | 'ISO80601' | 'FCC' | 'AHA_Validated';
    number: string;
    issuedDate: string;
    expiryDate?: string;
    issuingAuthority: string;
  }
  
  export interface DeviceStatus {
    deviceId: string;
    status: 'online' | 'offline' | 'error' | 'maintenance' | 'low_battery' | 'calibration_required';
    lastSeen: string;
    batteryLevel?: number; // 0-100 percentage
    signalStrength?: number; // 0-100 percentage
    connectionType: 'wifi' | 'bluetooth' | 'cellular' | 'zigbee' | 'lora';
    location?: {
      latitude: number;
      longitude: number;
      accuracy: number; // meters
      timestamp: string;
    };
    diagnostics?: DeviceDiagnostics;
  }
  
  export interface DeviceDiagnostics {
    temperature: number; // device internal temperature
    memoryUsage: number; // percentage
    cpuUsage?: number; // percentage
    storageUsage?: number; // percentage
    networkLatency?: number; // milliseconds
    errorCount: number;
    lastError?: {
      code: string;
      message: string;
      timestamp: string;
    };
    uptime: number; // seconds
    dataTransmissionRate?: number; // bytes per second
  }
  
  export interface DeviceConfiguration {
    deviceId: string;
    samplingRate: number; // Hz or samples per minute
    transmissionInterval: number; // seconds
    measurementInterval: number; // New property
    autoSync: boolean; // New property
    notifications: boolean; // New property
    dataRetention: string; // New property
    alertThresholds: Record<string, {
      min?: number;
      max?: number;
      enabled: boolean;
    }>;
    powerManagement: {
      mode: 'performance' | 'balanced' | 'power_saver';
      sleepTimeout: number; // seconds
      wakeOnMotion: boolean;
    };
    connectivity: {
      preferredNetwork: 'wifi' | 'cellular' | 'bluetooth';
      fallbackNetworks: string[];
      encryptionEnabled: boolean;
    };
    calibration: {
      lastCalibrated: string;
      nextCalibration: string;
      autoCalibration: boolean;
      calibrationData?: Record<string, number>;
    };
    firmware: {
      currentVersion: string;
      availableVersion?: string;
      autoUpdate: boolean;
      updateSchedule?: string; // cron expression
    };
  }
  
  export interface DeviceData {
    deviceId: string;
    patientId: string;
    timestamp: string;
    dataType: string;
    rawData: Record<string, any>;
    processedData: Record<string, any>;
    metadata: {
      batchId?: string;
      sequenceNumber?: number;
      checksum?: string;
      compression?: string;
      encryption?: string;
    };
    qualityMetrics: {
      signalQuality: 'excellent' | 'good' | 'fair' | 'poor';
      noiseLevel: number; // 0-100
      artifactDetected: boolean;
      confidence: number; // 0-1
      calibrationStatus: 'valid' | 'expired' | 'required';
    };
    alerts?: DeviceAlert[];
  }
  
  export interface DeviceAlert {
    id: string;
    deviceId: string;
    alertType: 'threshold_exceeded' | 'device_malfunction' | 'battery_low' | 'connection_lost' | 'calibration_required';
    severity: 'low' | 'medium' | 'high' | 'critical';
    message: string;
    timestamp: string;
    acknowledged: boolean;
    acknowledgedBy?: string;
    acknowledgedAt?: string;
    resolved: boolean;
    resolvedBy?: string;
    resolvedAt?: string;
    metadata?: Record<string, any>;
  }
  
  export interface DeviceRegistration {
    deviceInfo: DeviceInfo;
    patientId: string;
    registeredBy: string; // user ID
    registrationDate: string;
    activationCode?: string;
    pairingMethod: 'qr_code' | 'bluetooth' | 'nfc' | 'manual_entry';
    initialConfiguration: Partial<DeviceConfiguration>;
    warrantyInfo?: {
      startDate: string;
      endDate: string;
      provider: string;
      terms: string;
    };
  }
  
  export interface DeviceSimulation {
    id: string;
    deviceType: DeviceType;
    patientId: string;
    isActive: boolean;
    simulationParameters: {
      baselineValues: Record<string, number>;
      variability: Record<string, number>; // percentage variation
      trendDirection: Record<string, 'increasing' | 'decreasing' | 'stable' | 'random'>;
      anomalyProbability: number; // 0-1
      dataFrequency: number; // seconds between readings
    };
    scenarios: DeviceScenario[];
    createdAt: string;
    lastUpdate: string;
  }
  
  export interface DeviceScenario {
    id: string;
    name: string;
    description: string;
    duration: number; // minutes
    triggers: Array<{
      condition: string;
      action: string;
      parameters: Record<string, any>;
    }>;
    expectedOutcomes: string[];
    isActive: boolean;
  }
  
  export interface DeviceMaintenanceRecord {
    id: string;
    deviceId: string;
    maintenanceType: 'calibration' | 'cleaning' | 'repair' | 'replacement' | 'software_update';
    scheduledDate: string;
    completedDate?: string;
    performedBy: string;
    description: string;
    partsReplaced?: Array<{
      partName: string;
      partNumber: string;
      serialNumber: string;
    }>;
    cost?: number;
    nextMaintenanceDate?: string;
    notes?: string;
    attachments?: Array<{
      filename: string;
      url: string;
      type: string;
    }>;
  }
  
  export interface DeviceAnalytics {
    deviceId: string;
    period: {
      start: string;
      end: string;
    };
    usage: {
      totalReadings: number;
      averageReadingsPerDay: number;
      uptimePercentage: number;
      dataQualityScore: number; // 0-100
    };
    performance: {
      averageResponseTime: number; // milliseconds
      errorRate: number; // percentage
      batteryLifeRemaining: number; // days
      signalStrengthAverage: number; // percentage
    };
    healthMetrics: {
      readingsWithinNormalRange: number; // percentage
      alertsGenerated: number;
      criticalAlertsGenerated: number;
      falsePositiveRate: number; // percentage
    };
    trends: Array<{
      metric: string;
      trend: 'improving' | 'stable' | 'declining';
      changePercentage: number;
    }>;
    recommendations: string[];
  }
  
  export interface DeviceGroup {
    id: string;
    name: string;
    description: string;
    deviceIds: string[];
    groupType: 'patient_devices' | 'device_type' | 'location' | 'custom';
    configuration: Partial<DeviceConfiguration>;
    policies: Array<{
      name: string;
      rule: string;
      action: string;
      enabled: boolean;
    }>;
    createdBy: string;
    createdAt: string;
    lastModified: string;
  }
  
  export interface DeviceCommand {
    id: string;
    deviceId: string;
    command: string;
    parameters: Record<string, any>;
    sentAt: string;
    sentBy: string;
    status: 'pending' | 'sent' | 'acknowledged' | 'executed' | 'failed' | 'timeout';
    response?: {
      data: any;
      receivedAt: string;
      executionTime: number; // milliseconds
    };
    retryCount: number;
    maxRetries: number;
    timeout: number; // seconds
  }
  
  // Device management interfaces
  export interface DeviceFleet {
    totalDevices: number;
    activeDevices: number;
    offlineDevices: number;
    devicesByType: Record<DeviceType, number>;
    devicesByStatus: Record<string, number>;
    averageUptimePercentage: number;
    totalAlertsLast24h: number;
    criticalAlertsLast24h: number;
    devicesRequiringMaintenance: number;
    batteryLowDevices: number;
    lastUpdated: string;
  }
  
  export interface DeviceFilter {
    deviceTypes?: DeviceType[];
    statuses?: string[];
    patients?: string[];
    manufacturers?: string[];
    batteryLevel?: {
      min: number;
      max: number;
    };
    lastSeenRange?: {
      start: string;
      end: string;
    };
    location?: {
      latitude: number;
      longitude: number;
      radius: number; // meters
    };
    hasAlerts?: boolean;
    requiresMaintenance?: boolean;
  }
  
  export interface DeviceApiResponse<T = any> {
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
      deviceCount?: number;
    };
  }
  
  // Real-time device data streaming
  export interface DeviceDataStream {
    deviceId: string;
    streamId: string;
    isActive: boolean;
    dataRate: number; // messages per second
    lastMessage: string;
    messageCount: number;
    errorCount: number;
    qualityScore: number; // 0-100
    subscribers: string[]; // user IDs
  }
  
  export interface DeviceDataMessage {
    streamId: string;
    deviceId: string;
    timestamp: string;
    messageType: 'data' | 'status' | 'alert' | 'heartbeat';
    payload: any;
    sequenceNumber: number;
    checksum: string;
  }
  
  // Device security and compliance
  export interface DeviceSecurity {
    deviceId: string;
    encryptionStatus: 'enabled' | 'disabled' | 'partial';
    certificateStatus: 'valid' | 'expired' | 'revoked' | 'pending';
    lastSecurityScan: string;
    vulnerabilities: Array<{
      id: string;
      severity: 'low' | 'medium' | 'high' | 'critical';
      description: string;
      cvssScore?: number;
      patchAvailable: boolean;
      mitigated: boolean;
    }>;
    complianceStatus: {
      hipaa: boolean;
      gdpr: boolean;
      fda: boolean;
      iso27001: boolean;
    };
    accessLog: Array<{
      timestamp: string;
      action: string;
      userId: string;
      ipAddress: string;
      success: boolean;
    }>;
  }
  