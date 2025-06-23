/**
 * Consultation and telemedicine TypeScript definitions for HealthConnect AI
 * Following telemedicine standards and WebRTC specifications
 */

export interface ConsultationSession {
    id: string;
    patientId: string;
    providerId?: string;
    consultationType: ConsultationType;
    status: ConsultationStatus;
    urgencyLevel: 'low' | 'medium' | 'high' | 'critical';
    scheduledTime?: string;
    startTime?: string;
    endTime?: string;
    duration?: number; // minutes
    chiefComplaint: string;
    symptoms?: string[];
    vitalSigns?: VitalSigns;
    notes?: string;
    diagnosis?: string;
    treatmentPlan?: string;
    prescriptions?: Prescription[];
    followUpRequired: boolean;
    followUpDate?: string;
    recordingEnabled: boolean;
    recordingUrl?: string;
    metadata: ConsultationMetadata;
    createdAt: string;
    updatedAt: string;
  }
  
  export type ConsultationType = 
    | 'emergency'
    | 'urgent_care'
    | 'routine'
    | 'follow_up'
    | 'mental_health'
    | 'specialist'
    | 'second_opinion'
    | 'medication_review'
    | 'lab_review';
  
  export type ConsultationStatus = 
    | 'scheduled'
    | 'waiting_for_provider'
    | 'provider_assigned'
    | 'connecting'
    | 'in_progress'
    | 'on_hold'
    | 'completed'
    | 'cancelled'
    | 'no_show'
    | 'technical_issues';
  
  export interface ConsultationMetadata {
    platform: 'web' | 'mobile' | 'tablet';
    connectionType: 'video' | 'audio' | 'chat';
    qualityMetrics: QualityMetrics;
    technicalIssues?: TechnicalIssue[];
    participantCount: number;
    dataUsage?: number; // MB
    encryptionEnabled: boolean;
    complianceFlags: {
      hipaaCompliant: boolean;
      recordingConsent: boolean;
      dataRetentionPolicy: string;
    };
  }
  
  export interface QualityMetrics {
    video?: {
      resolution: string;
      frameRate: number;
      bitrate: number;
      packetsLost: number;
      jitter: number; // milliseconds
      latency: number; // milliseconds
      qualityScore: number; // 0-5
    };
    audio?: {
      bitrate: number;
      packetsLost: number;
      jitter: number;
      latency: number;
      qualityScore: number; // 0-5
      echoCancellation: boolean;
      noiseSuppression: boolean;
    };
    connection?: {
      bandwidth: number; // kbps
      stability: number; // 0-100 percentage
      reconnections: number;
      totalDowntime: number; // seconds
    };
  }
  
  export interface TechnicalIssue {
    id: string;
    type: 'connection' | 'audio' | 'video' | 'browser' | 'device' | 'network';
    severity: 'low' | 'medium' | 'high' | 'critical';
    description: string;
    timestamp: string;
    resolved: boolean;
    resolution?: string;
    impact: 'none' | 'minor' | 'moderate' | 'severe';
  }
  
  export interface WebRTCConfiguration {
    iceServers: RTCIceServer[];
    iceTransportPolicy: RTCIceTransportPolicy;
    bundlePolicy: RTCBundlePolicy;
    rtcpMuxPolicy: RTCRtcpMuxPolicy;
    iceCandidatePoolSize: number;
    certificates?: RTCCertificate[];
  }
  
  export interface MediaConstraints {
    video: {
      width: { min: number; ideal: number; max: number };
      height: { min: number; ideal: number; max: number };
      frameRate: { min: number; ideal: number; max: number };
      facingMode?: 'user' | 'environment';
      deviceId?: string;
    };
    audio: {
      echoCancellation: boolean;
      noiseSuppression: boolean;
      autoGainControl: boolean;
      sampleRate: number;
      channelCount: number;
      deviceId?: string;
    };
  }
  
  export interface Prescription {
    id: string;
    medicationName: string;
    dosage: string;
    frequency: string;
    duration: string;
    instructions: string;
    refills: number;
    prescribedBy: string; // provider ID
    prescribedAt: string;
    pharmacyInstructions?: string;
    interactions?: string[];
    sideEffects?: string[];
    rxNormCode?: string;
    ndcCode?: string;
  }
  
  export interface ConsultationParticipant {
    id: string;
    userId: string;
    role: 'patient' | 'provider' | 'observer' | 'interpreter' | 'family_member';
    name: string;
    joinedAt?: string;
    leftAt?: string;
    connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'reconnecting';
    mediaStatus: {
      video: boolean;
      audio: boolean;
      screenShare: boolean;
    };
    permissions: {
      canSpeak: boolean;
      canVideo: boolean;
      canScreenShare: boolean;
      canRecord: boolean;
      canInviteOthers: boolean;
    };
    deviceInfo?: {
      browser: string;
      os: string;
      device: string;
      capabilities: {
        video: boolean;
        audio: boolean;
        screenShare: boolean;
      };
    };
  }
  
  export interface ConsultationMessage {
    id: string;
    consultationId: string;
    senderId: string;
    senderRole: 'patient' | 'provider' | 'system';
    messageType: 'text' | 'image' | 'file' | 'system_notification' | 'prescription' | 'vital_signs';
    content: string;
    attachments?: ConsultationAttachment[];
    timestamp: string;
    edited?: boolean;
    editedAt?: string;
    readBy: Array<{
      userId: string;
      readAt: string;
    }>;
    metadata?: Record<string, any>;
  }
  
  export interface ConsultationAttachment {
    id: string;
    filename: string;
    fileType: string;
    fileSize: number;
    url: string;
    thumbnailUrl?: string;
    uploadedBy: string;
    uploadedAt: string;
    description?: string;
    category: 'medical_image' | 'lab_result' | 'prescription' | 'document' | 'other';
    encryptionStatus: 'encrypted' | 'not_encrypted';
  }
  
  export interface ConsultationRecording {
    id: string;
    consultationId: string;
    filename: string;
    duration: number; // seconds
    fileSize: number; // bytes
    format: 'mp4' | 'webm' | 'audio_only';
    quality: 'low' | 'medium' | 'high' | 'hd';
    url: string;
    thumbnailUrl?: string;
    startTime: string;
    endTime: string;
    participants: string[]; // user IDs
    consentGiven: boolean;
    retentionPolicy: {
      deleteAfter: number; // days
      autoDelete: boolean;
    };
    encryptionKey?: string;
    accessLog: Array<{
      userId: string;
      accessedAt: string;
      action: 'view' | 'download' | 'share';
    }>;
  }
  
  export interface ConsultationQueue {
    id: string;
    patientId: string;
    consultationType: ConsultationType;
    urgencyLevel: 'low' | 'medium' | 'high' | 'critical';
    estimatedWaitTime: number; // minutes
    queuePosition: number;
    requestedAt: string;
    symptoms: string[];
    preferredProvider?: string;
    preferredLanguage?: string;
    specialRequirements?: string[];
    insurance?: {
      provider: string;
      policyNumber: string;
      groupNumber: string;
    };
    status: 'waiting' | 'assigned' | 'connecting' | 'cancelled' | 'expired';
  }
  
  export interface ProviderAvailability {
    providerId: string;
    status: 'available' | 'busy' | 'away' | 'offline';
    currentConsultations: number;
    maxConcurrentConsultations: number;
    specialties: string[];
    languages: string[];
    schedule: Array<{
      dayOfWeek: number; // 0-6
      startTime: string; // HH:mm
      endTime: string; // HH:mm
      timeZone: string;
    }>;
    breaks: Array<{
      startTime: string;
      endTime: string;
      reason: string;
    }>;
    nextAvailable?: string;
    averageConsultationDuration: number; // minutes
  }
  
  export interface ConsultationFeedback {
    id: string;
    consultationId: string;
    providedBy: 'patient' | 'provider';
    rating: number; // 1-5
    categories: {
      communication: number;
      professionalism: number;
      technicalQuality: number;
      overallSatisfaction: number;
    };
    comments?: string;
    wouldRecommend: boolean;
    technicalIssues?: string[];
    suggestions?: string;
    submittedAt: string;
    anonymous: boolean;
  }
  
  export interface ConsultationAnalytics {
    consultationId: string;
    duration: number; // minutes
    participantCount: number;
    messageCount: number;
    attachmentCount: number;
    qualityScore: number; // 0-100
    completionRate: number; // 0-100 percentage
    patientSatisfaction?: number; // 1-5
    providerSatisfaction?: number; // 1-5
    technicalIssueCount: number;
    reconnectionCount: number;
    averageLatency: number; // milliseconds
    bandwidthUsage: number; // MB
    deviceTypes: string[];
    browserTypes: string[];
    geographicLocations: string[];
  }
  
  export interface VoiceRecognitionResult {
    transcript: string;
    confidence: number; // 0-1
    language: string;
    isFinal: boolean;
    alternatives?: Array<{
      transcript: string;
      confidence: number;
    }>;
    medicalTerms?: Array<{
      term: string;
      confidence: number;
      category: 'symptom' | 'condition' | 'medication' | 'procedure';
    }>;
    timestamp: string;
  }
  
  export interface ConsultationAI {
    sessionId: string;
    enabled: boolean;
    features: {
      transcription: boolean;
      translation: boolean;
      medicalTermExtraction: boolean;
      symptomAnalysis: boolean;
      drugInteractionCheck: boolean;
      clinicalDecisionSupport: boolean;
    };
    transcripts: VoiceRecognitionResult[];
    insights: Array<{
      type: 'symptom_detected' | 'drug_interaction' | 'clinical_guideline' | 'follow_up_needed';
      content: string;
      confidence: number;
      timestamp: string;
      actionable: boolean;
    }>;
    summaryGenerated: boolean;
    summary?: {
      chiefComplaint: string;
      symptoms: string[];
      assessment: string;
      plan: string;
      followUp: string;
      generatedAt: string;
    };
  }
  
  export interface EmergencyConsultation {
    id: string;
    patientId: string;
    emergencyType: 'cardiac' | 'respiratory' | 'neurological' | 'trauma' | 'poisoning' | 'allergic_reaction' | 'other';
    severity: 'life_threatening' | 'urgent' | 'semi_urgent' | 'non_urgent';
    location?: {
      latitude: number;
      longitude: number;
      address: string;
    };
    emergencyContacts: string[]; // contact IDs
    vitalSigns?: VitalSigns;
    symptoms: string[];
    consciousness: 'alert' | 'confused' | 'drowsy' | 'unconscious';
    breathing: 'normal' | 'difficulty' | 'stopped';
    pulse: 'normal' | 'weak' | 'strong' | 'irregular' | 'absent';
    firstAidProvided?: string[];
    emsNotified: boolean;
    emsEta?: number; // minutes
    hospitalDestination?: string;
    triageLevel: 1 | 2 | 3 | 4 | 5; // ESI triage levels
    disposition: 'ems_transport' | 'self_transport' | 'treat_and_release' | 'refer_to_pcp' | 'no_treatment_needed';
  }
  
  // API response types for consultations
  export interface ConsultationApiResponse<T = any> {
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
      consultationId?: string;
    };
  }
  
  export interface ConsultationFilter {
    dateRange?: {
      start: string;
      end: string;
    };
    statuses?: ConsultationStatus[];
    types?: ConsultationType[];
    providers?: string[];
    urgencyLevels?: string[];
    completedOnly?: boolean;
    withRecordings?: boolean;
  }
  
  // WebRTC and real-time communication types
  export interface SignalingMessage {
    type: 'offer' | 'answer' | 'ice-candidate' | 'join' | 'leave' | 'chat' | 'status';
    consultationId: string;
    senderId: string;
    targetId?: string;
    payload: any;
    timestamp: string;
  }
  
  export interface PeerConnectionState {
    connectionState: RTCPeerConnectionState;
    iceConnectionState: RTCIceConnectionState;
    iceGatheringState: RTCIceGatheringState;
    signalingState: RTCSignalingState;
    localDescription?: RTCSessionDescription;
    remoteDescription?: RTCSessionDescription;
    stats?: RTCStatsReport;
  }
  
  export interface MediaDeviceInfo {
    deviceId: string;
    kind: 'videoinput' | 'audioinput' | 'audiooutput';
    label: string;
    groupId: string;
    capabilities?: MediaTrackCapabilities;
  }
  
  export interface ConsultationSettings {
    video: {
      enabled: boolean;
      quality: 'low' | 'medium' | 'high' | 'hd';
      frameRate: number;
      deviceId?: string;
    };
    audio: {
      enabled: boolean;
      deviceId?: string;
      echoCancellation: boolean;
      noiseSuppression: boolean;
      autoGainControl: boolean;
    };
    recording: {
      enabled: boolean;
      quality: 'low' | 'medium' | 'high';
      includeAudio: boolean;
      includeVideo: boolean;
      autoStart: boolean;
    };
    notifications: {
      sound: boolean;
      desktop: boolean;
      email: boolean;
      sms: boolean;
    };
    privacy: {
      allowRecording: boolean;
      shareVitalSigns: boolean;
      shareLocation: boolean;
      dataRetention: number; // days
    };
  }
  
  