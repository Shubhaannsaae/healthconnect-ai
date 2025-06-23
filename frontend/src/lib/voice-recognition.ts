/**
 * Voice recognition and speech-to-text implementation for HealthConnect AI
 * Following Web Speech API standards and medical terminology processing
 */

import type { VoiceRecognitionResult } from '@/types/consultation';

export interface VoiceRecognitionConfig {
  language: string;
  continuous: boolean;
  interimResults: boolean;
  maxAlternatives: number;
  enableMedicalTerms: boolean;
  enablePunctuation: boolean;
  enableProfanityFilter: boolean;
  confidenceThreshold: number;
}

export interface VoiceRecognitionHandlers {
  onResult?: (result: VoiceRecognitionResult) => void;
  onError?: (error: Error) => void;
  onStart?: () => void;
  onEnd?: () => void;
  onSpeechStart?: () => void;
  onSpeechEnd?: () => void;
  onNoMatch?: () => void;
}

class VoiceRecognitionManager {
  private recognition: SpeechRecognition | null = null;
  private config: VoiceRecognitionConfig;
  private handlers: VoiceRecognitionHandlers = {};
  private isListening = false;
  private medicalTermsDatabase: Map<string, string> = new Map();
  private lastResult: string = '';

  constructor(config?: Partial<VoiceRecognitionConfig>) {
    this.config = {
      language: 'en-US',
      continuous: true,
      interimResults: true,
      maxAlternatives: 3,
      enableMedicalTerms: true,
      enablePunctuation: true,
      enableProfanityFilter: false,
      confidenceThreshold: 0.7,
      ...config
    };

    this.initializeMedicalTerms();
    this.setupRecognition();
  }

  /**
   * Initialize speech recognition
   */
  private setupRecognition(): void {
    if (!this.isSupported()) {
      console.warn('Speech recognition not supported in this browser');
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    this.recognition = new SpeechRecognition();

    // Configure recognition
    this.recognition.lang = this.config.language;
    this.recognition.continuous = this.config.continuous;
    this.recognition.interimResults = this.config.interimResults;
    this.recognition.maxAlternatives = this.config.maxAlternatives;

    // Set up event handlers
    this.setupEventHandlers();
  }

  /**
   * Set up event handlers for speech recognition
   */
  private setupEventHandlers(): void {
    if (!this.recognition) return;

    this.recognition.onstart = () => {
      this.isListening = true;
      this.handlers.onStart?.();
    };

    this.recognition.onend = () => {
      this.isListening = false;
      this.handlers.onEnd?.();
    };

    this.recognition.onspeechstart = () => {
      this.handlers.onSpeechStart?.();
    };

    this.recognition.onspeechend = () => {
      this.handlers.onSpeechEnd?.();
    };

    this.recognition.onresult = (event: SpeechRecognitionEvent) => {
      this.handleRecognitionResult(event);
    };

    this.recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      this.handleRecognitionError(event);
    };

    this.recognition.onnomatch = () => {
      this.handlers.onNoMatch?.();
    };
  }

  /**
   * Handle recognition results
   */
  private handleRecognitionResult(event: SpeechRecognitionEvent): void {
    const lastResultIndex = event.results.length - 1;
    const result = event.results[lastResultIndex];
    
    if (!result) return;

    const transcript = result[0].transcript;
    const confidence = result[0].confidence;
    const isFinal = result.isFinal;

    // Skip if confidence is too low
    if (confidence < this.config.confidenceThreshold && isFinal) {
      return;
    }

    // Process transcript
    const processedTranscript = this.processTranscript(transcript);
    
    // Extract medical terms if enabled
    const medicalTerms = this.config.enableMedicalTerms 
      ? this.extractMedicalTerms(processedTranscript)
      : [];

    // Create alternatives array
    const alternatives: Array<{ transcript: string; confidence: number }> = [];
    for (let i = 1; i < Math.min(result.length, this.config.maxAlternatives); i++) {
      alternatives.push({
        transcript: this.processTranscript(result[i].transcript),
        confidence: result[i].confidence
      });
    }

    const recognitionResult: VoiceRecognitionResult = {
      transcript: processedTranscript,
      confidence,
      language: this.config.language,
      isFinal,
      alternatives,
      medicalTerms,
      timestamp: new Date().toISOString()
    };

    this.lastResult = processedTranscript;
    this.handlers.onResult?.(recognitionResult);
  }

  /**
   * Handle recognition errors
   */
  private handleRecognitionError(event: SpeechRecognitionErrorEvent): void {
    let errorMessage: string;

    switch (event.error) {
      case 'no-speech':
        errorMessage = 'No speech was detected. Please try speaking again.';
        break;
      case 'audio-capture':
        errorMessage = 'Audio capture failed. Please check your microphone.';
        break;
      case 'not-allowed':
        errorMessage = 'Microphone access denied. Please allow microphone permissions.';
        break;
      case 'network':
        errorMessage = 'Network error occurred during speech recognition.';
        break;
      case 'service-not-allowed':
        errorMessage = 'Speech recognition service not allowed.';
        break;
      case 'bad-grammar':
        errorMessage = 'Grammar error in speech recognition.';
        break;
      case 'language-not-supported':
        errorMessage = `Language '${this.config.language}' is not supported.`;
        break;
      default:
        errorMessage = `Speech recognition error: ${event.error}`;
    }

    this.handlers.onError?.(new Error(errorMessage));
  }

  /**
   * Process transcript text
   */
  private processTranscript(transcript: string): string {
    let processed = transcript.trim();

    // Add punctuation if enabled
    if (this.config.enablePunctuation) {
      processed = this.addPunctuation(processed);
    }

    // Apply profanity filter if enabled
    if (this.config.enableProfanityFilter) {
      processed = this.filterProfanity(processed);
    }

    // Correct medical terms
    if (this.config.enableMedicalTerms) {
      processed = this.correctMedicalTerms(processed);
    }

    return processed;
  }

  /**
   * Add punctuation to transcript
   */
  private addPunctuation(text: string): string {
    // Simple punctuation rules
    let punctuated = text;

    // Add periods for sentence endings
    punctuated = punctuated.replace(/\b(period|full stop)\b/gi, '.');
    punctuated = punctuated.replace(/\b(comma)\b/gi, ',');
    punctuated = punctuated.replace(/\b(question mark)\b/gi, '?');
    punctuated = punctuated.replace(/\b(exclamation mark|exclamation point)\b/gi, '!');

    // Capitalize first letter of sentences
    punctuated = punctuated.replace(/(^|[.!?]\s+)([a-z])/g, (match, p1, p2) => 
      p1 + p2.toUpperCase()
    );

    return punctuated;
  }

  /**
   * Filter profanity from transcript
   */
  private filterProfanity(text: string): string {
    // Basic profanity filter - in production, use a comprehensive library
    const profanityWords = ['damn', 'hell', 'crap']; // Add more as needed
    let filtered = text;

    profanityWords.forEach(word => {
      const regex = new RegExp(`\\b${word}\\b`, 'gi');
      filtered = filtered.replace(regex, '*'.repeat(word.length));
    });

    return filtered;
  }

  /**
   * Correct medical terms in transcript
   */
  private correctMedicalTerms(text: string): string {
    let corrected = text;

    this.medicalTermsDatabase.forEach((correct, incorrect) => {
      const regex = new RegExp(`\\b${incorrect}\\b`, 'gi');
      corrected = corrected.replace(regex, correct);
    });

    return corrected;
  }

  /**
   * Extract medical terms from transcript
   */
  private extractMedicalTerms(text: string): Array<{
    term: string;
    confidence: number;
    category: 'symptom' | 'condition' | 'medication' | 'procedure';
  }> {
    const medicalTerms: Array<{
      term: string;
      confidence: number;
      category: 'symptom' | 'condition' | 'medication' | 'procedure';
    }> = [];

    // Medical term categories and patterns
    const categories = {
      symptoms: [
        'pain', 'ache', 'fever', 'nausea', 'vomiting', 'dizziness', 'fatigue',
        'shortness of breath', 'chest pain', 'headache', 'cough', 'sore throat'
      ],
      conditions: [
        'diabetes', 'hypertension', 'asthma', 'depression', 'anxiety',
        'arthritis', 'migraine', 'pneumonia', 'bronchitis', 'flu'
      ],
      medications: [
        'aspirin', 'ibuprofen', 'acetaminophen', 'insulin', 'metformin',
        'lisinopril', 'atorvastatin', 'amlodipine', 'omeprazole'
      ],
      procedures: [
        'x-ray', 'mri', 'ct scan', 'blood test', 'biopsy', 'surgery',
        'vaccination', 'injection', 'examination', 'consultation'
      ]
    };

    // Search for medical terms in each category
    Object.entries(categories).forEach(([category, terms]) => {
      terms.forEach(term => {
        const regex = new RegExp(`\\b${term}\\b`, 'gi');
        const matches = text.match(regex);
        
        if (matches) {
          matches.forEach(() => {
            medicalTerms.push({
              term,
              confidence: 0.8, // Base confidence for known terms
              category: category.slice(0, -1) as any // Remove 's' from category name
            });
          });
        }
      });
    });

    return medicalTerms;
  }

  /**
   * Initialize medical terms database
   */
  private initializeMedicalTerms(): void {
    // Common speech recognition errors for medical terms
    const medicalCorrections = new Map([
      ['hyper tension', 'hypertension'],
      ['die a betes', 'diabetes'],
      ['as ma', 'asthma'],
      ['new monia', 'pneumonia'],
      ['anti biotic', 'antibiotic'],
      ['in su lin', 'insulin'],
      ['ace ta min o fen', 'acetaminophen'],
      ['i bu pro fen', 'ibuprofen'],
      ['met for min', 'metformin'],
      ['li sin o pril', 'lisinopril'],
      ['a tor va stat in', 'atorvastatin'],
      ['am lo di pine', 'amlodipine'],
      ['o mep ra zole', 'omeprazole']
    ]);

    this.medicalTermsDatabase = medicalCorrections;
  }

  /**
   * Start voice recognition
   */
  start(): void {
    if (!this.recognition) {
      this.handlers.onError?.(new Error('Speech recognition not supported'));
      return;
    }

    if (this.isListening) {
      console.warn('Voice recognition is already running');
      return;
    }

    try {
      this.recognition.start();
    } catch (error) {
      this.handlers.onError?.(new Error('Failed to start voice recognition'));
    }
  }

  /**
   * Stop voice recognition
   */
  stop(): void {
    if (this.recognition && this.isListening) {
      this.recognition.stop();
    }
  }

  /**
   * Abort voice recognition
   */
  abort(): void {
    if (this.recognition && this.isListening) {
      this.recognition.abort();
    }
  }

  /**
   * Check if speech recognition is supported
   */
  isSupported(): boolean {
    return !!(window.SpeechRecognition || window.webkitSpeechRecognition);
  }

  /**
   * Check if currently listening
   */
  getIsListening(): boolean {
    return this.isListening;
  }

  /**
   * Set event handlers
   */
  setHandlers(handlers: VoiceRecognitionHandlers): void {
    this.handlers = { ...this.handlers, ...handlers };
  }

  /**
   * Update configuration
   */
  updateConfig(config: Partial<VoiceRecognitionConfig>): void {
    this.config = { ...this.config, ...config };
    
    if (this.recognition) {
      this.recognition.lang = this.config.language;
      this.recognition.continuous = this.config.continuous;
      this.recognition.interimResults = this.config.interimResults;
      this.recognition.maxAlternatives = this.config.maxAlternatives;
    }
  }

  /**
   * Get last recognition result
   */
  getLastResult(): string {
    return this.lastResult;
  }

  /**
   * Get supported languages
   */
  getSupportedLanguages(): string[] {
    // Common languages supported by most browsers
    return [
      'en-US', 'en-GB', 'en-AU', 'en-CA', 'en-IN',
      'es-ES', 'es-MX', 'fr-FR', 'de-DE', 'it-IT',
      'pt-BR', 'ru-RU', 'ja-JP', 'ko-KR', 'zh-CN',
      'ar-SA', 'hi-IN', 'th-TH', 'vi-VN', 'tr-TR'
    ];
  }

  /**
   * Add custom medical term correction
   */
  addMedicalTermCorrection(incorrect: string, correct: string): void {
    this.medicalTermsDatabase.set(incorrect.toLowerCase(), correct);
  }

  /**
   * Remove medical term correction
   */
  removeMedicalTermCorrection(incorrect: string): void {
    this.medicalTermsDatabase.delete(incorrect.toLowerCase());
  }

  /**
   * Get all medical term corrections
   */
  getMedicalTermCorrections(): Map<string, string> {
    return new Map(this.medicalTermsDatabase);
  }
}

// Create singleton instance
export const voiceRecognitionManager = new VoiceRecognitionManager();

// Utility functions
export const startVoiceRecognition = (): void => {
  voiceRecognitionManager.start();
};

export const stopVoiceRecognition = (): void => {
  voiceRecognitionManager.stop();
};

export const isVoiceRecognitionSupported = (): boolean => {
  return voiceRecognitionManager.isSupported();
};

export const checkVoiceRecognitionPermissions = async (): Promise<boolean> => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    stream.getTracks().forEach(track => track.stop());
    return true;
  } catch {
    return false;
  }
};

export default voiceRecognitionManager;
