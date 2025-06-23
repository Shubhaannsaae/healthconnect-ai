/**
 * Custom React hook for voice recognition functionality
 * Provides speech-to-text capabilities for HealthConnect AI
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { voiceRecognitionManager } from '@/lib/voice-recognition';
import type { VoiceRecognitionConfig, VoiceRecognitionHandlers, VoiceRecognitionResult } from '@/types/consultation';

interface UseVoiceRecognitionOptions {
  config?: Partial<VoiceRecognitionConfig>;
  autoStart?: boolean;
  onResult?: (result: VoiceRecognitionResult) => void;
  onError?: (error: Error) => void;
  onStart?: () => void;
  onEnd?: () => void;
}

interface UseVoiceRecognitionReturn {
  isListening: boolean;
  isSupported: boolean;
  lastResult: string;
  results: VoiceRecognitionResult[];
  error: string | null;
  
  // Actions
  start: () => void;
  stop: () => void;
  abort: () => void;
  clearResults: () => void;
  updateConfig: (config: Partial<VoiceRecognitionConfig>) => void;
  
  // Utilities
  getSupportedLanguages: () => string[];
  addMedicalTermCorrection: (incorrect: string, correct: string) => void;
  removeMedicalTermCorrection: (incorrect: string) => void;
}

export const useVoiceRecognition = (options: UseVoiceRecognitionOptions = {}): UseVoiceRecognitionReturn => {
  const [isListening, setIsListening] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const [lastResult, setLastResult] = useState('');
  const [results, setResults] = useState<VoiceRecognitionResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  
  const handlersRef = useRef<VoiceRecognitionHandlers>({});

  // Check if voice recognition is supported
  useEffect(() => {
    setIsSupported(voiceRecognitionManager.isSupported());
  }, []);

  // Update handlers when options change
  useEffect(() => {
    handlersRef.current = {
      onResult: (result) => {
        setLastResult(result.transcript);
        setResults(prev => [result, ...prev.slice(0, 49)]); // Keep last 50 results
        setError(null);
        options.onResult?.(result);
      },
      onError: (error) => {
        setError(error.message);
        setIsListening(false);
        options.onError?.(error);
      },
      onStart: () => {
        setIsListening(true);
        setError(null);
        options.onStart?.();
      },
      onEnd: () => {
        setIsListening(false);
        options.onEnd?.();
      },
      onSpeechStart: () => {
        setError(null);
      },
      onSpeechEnd: () => {
        // Speech ended
      },
      onNoMatch: () => {
        setError('No speech was recognized');
      }
    };

    voiceRecognitionManager.setHandlers(handlersRef.current);
  }, [options.onResult, options.onError, options.onStart, options.onEnd]);

  // Update configuration when options change
  useEffect(() => {
    if (options.config) {
      voiceRecognitionManager.updateConfig(options.config);
    }
  }, [options.config]);

  // Auto-start if enabled
  useEffect(() => {
    if (options.autoStart && isSupported && !isListening) {
      start();
    }
  }, [options.autoStart, isSupported]);

  // Start voice recognition
  const start = useCallback(() => {
    if (!isSupported) {
      setError('Voice recognition is not supported in this browser');
      return;
    }

    if (isListening) {
      console.warn('Voice recognition is already running');
      return;
    }

    setError(null);
    voiceRecognitionManager.start();
  }, [isSupported, isListening]);

  // Stop voice recognition
  const stop = useCallback(() => {
    if (isListening) {
      voiceRecognitionManager.stop();
    }
  }, [isListening]);

  // Abort voice recognition
  const abort = useCallback(() => {
    if (isListening) {
      voiceRecognitionManager.abort();
      setIsListening(false);
    }
  }, [isListening]);

  // Clear results
  const clearResults = useCallback(() => {
    setResults([]);
    setLastResult('');
    setError(null);
  }, []);

  // Update configuration
  const updateConfig = useCallback((config: Partial<VoiceRecognitionConfig>) => {
    voiceRecognitionManager.updateConfig(config);
  }, []);

  // Get supported languages
  const getSupportedLanguages = useCallback(() => {
    return voiceRecognitionManager.getSupportedLanguages();
  }, []);

  // Add medical term correction
  const addMedicalTermCorrection = useCallback((incorrect: string, correct: string) => {
    voiceRecognitionManager.addMedicalTermCorrection(incorrect, correct);
  }, []);

  // Remove medical term correction
  const removeMedicalTermCorrection = useCallback((incorrect: string) => {
    voiceRecognitionManager.removeMedicalTermCorrection(incorrect);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (isListening) {
        voiceRecognitionManager.abort();
      }
    };
  }, [isListening]);

  return {
    isListening,
    isSupported,
    lastResult,
    results,
    error,
    
    // Actions
    start,
    stop,
    abort,
    clearResults,
    updateConfig,
    
    // Utilities
    getSupportedLanguages,
    addMedicalTermCorrection,
    removeMedicalTermCorrection
  };
};

export default useVoiceRecognition;
