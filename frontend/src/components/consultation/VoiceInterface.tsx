/**
 * VoiceInterface component for HealthConnect AI
 * Voice-controlled consultation interface with medical transcription
 */

import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useVoiceRecognition } from '@/hooks/useVoiceRecognition';
import { useConsultationStore } from '@/store/consultationStore';
import type { VoiceRecognitionResult } from '@/types/consultation';
import { 
  Mic, 
  MicOff, 
  Volume2, 
  VolumeX, 
  Play, 
  Pause,
  RotateCcw,
  Download,
  FileText,
  Stethoscope,
  MessageSquare
} from 'lucide-react';
import { clsx } from 'clsx';

interface VoiceInterfaceProps {
  consultationId: string;
  onTranscriptUpdate?: (transcript: string) => void;
  className?: string;
}

interface TranscriptEntry {
  id: string;
  speaker: 'patient' | 'provider' | 'system';
  text: string;
  timestamp: string;
  confidence: number;
  medicalTerms?: Array<{
    term: string;
    category: string;
    confidence: number;
  }>;
}

export const VoiceInterface: React.FC<VoiceInterfaceProps> = ({
  consultationId,
  onTranscriptUpdate,
  className
}) => {
  const [transcriptEntries, setTranscriptEntries] = useState<TranscriptEntry[]>([]);
  const [currentSpeaker, setCurrentSpeaker] = useState<'patient' | 'provider'>('patient');
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackPosition, setPlaybackPosition] = useState(0);
  const [showMedicalTerms, setShowMedicalTerms] = useState(true);
  const [autoScroll, setAutoScroll] = useState(true);
  
  const transcriptRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);

  const {
    isListening,
    isSupported,
    lastResult,
    results,
    error,
    start: startListening,
    stop: stopListening,
    clearResults
  } = useVoiceRecognition({
    config: {
      continuous: true,
      interimResults: true,
      enableMedicalTerms: true,
      confidenceThreshold: 0.7
    },
    onResult: (result: VoiceRecognitionResult) => {
      if (result.isFinal) {
        addTranscriptEntry(result);
        onTranscriptUpdate?.(result.transcript);
      }
    },
    onError: (error) => {
      console.error('Voice recognition error:', error);
    }
  });

  const { sendConsultationMessage } = useConsultationStore();

  // Auto-scroll to bottom when new entries are added
  useEffect(() => {
    if (autoScroll && transcriptRef.current) {
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
    }
  }, [transcriptEntries, autoScroll]);

  const addTranscriptEntry = (result: VoiceRecognitionResult) => {
    const entry: TranscriptEntry = {
      id: `transcript-${Date.now()}`,
      speaker: currentSpeaker,
      text: result.transcript,
      timestamp: new Date().toISOString(),
      confidence: result.confidence,
      medicalTerms: result.medicalTerms
    };

    setTranscriptEntries(prev => [...prev, entry]);

    // Send as consultation message
    sendConsultationMessage({
      consultationId,
      senderId: currentSpeaker,
      senderRole: currentSpeaker,
      messageType: 'text',
      content: result.transcript
    });
  };

  const toggleListening = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  const clearTranscript = () => {
    setTranscriptEntries([]);
    clearResults();
  };

  const exportTranscript = () => {
    const transcript = transcriptEntries
      .map(entry => `[${new Date(entry.timestamp).toLocaleTimeString()}] ${entry.speaker.toUpperCase()}: ${entry.text}`)
      .join('\n');
    
    const blob = new Blob([transcript], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `consultation-transcript-${consultationId}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const generateSummary = async () => {
    try {
      // This would integrate with the AI service to generate a medical summary
      const summaryText = transcriptEntries
        .map(entry => entry.text)
        .join(' ');
      
      // Add summary as system message
      const summaryEntry: TranscriptEntry = {
        id: `summary-${Date.now()}`,
        speaker: 'system',
        text: `AI Summary: Based on the consultation, key points discussed include...`,
        timestamp: new Date().toISOString(),
        confidence: 1.0
      };
      
      setTranscriptEntries(prev => [...prev, summaryEntry]);
    } catch (error) {
      console.error('Error generating summary:', error);
    }
  };

  const getMedicalTermsCount = () => {
    return transcriptEntries.reduce((count, entry) => {
      return count + (entry.medicalTerms?.length || 0);
    }, 0);
  };

  const getAverageConfidence = () => {
    if (transcriptEntries.length === 0) return 0;
    const total = transcriptEntries.reduce((sum, entry) => sum + entry.confidence, 0);
    return Math.round((total / transcriptEntries.length) * 100);
  };

  if (!isSupported) {
    return (
      <Card className={className}>
        <CardContent className="p-8 text-center">
          <MicOff className="w-12 h-12 mx-auto mb-4 text-gray-400" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Voice Recognition Not Supported</h3>
          <p className="text-gray-600">
            Your browser doesn't support voice recognition. Please use a modern browser like Chrome or Edge.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={clsx('flex flex-col h-full', className)}>
      {/* Header */}
      <Card className="mb-4">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center space-x-2">
              <Stethoscope className="w-5 h-5 text-primary-600" />
              <span>Voice Transcription</span>
            </CardTitle>
            
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowMedicalTerms(!showMedicalTerms)}
              >
                Medical Terms: {showMedicalTerms ? 'On' : 'Off'}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={exportTranscript}
                disabled={transcriptEntries.length === 0}
              >
                <Download className="w-4 h-4 mr-1" />
                Export
              </Button>
            </div>
          </div>
        </CardHeader>
        
        <CardContent className="pt-0">
          {/* Statistics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-900">{transcriptEntries.length}</div>
              <p className="text-sm text-gray-600">Entries</p>
            </div>
            <div className="text-center p-3 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{getMedicalTermsCount()}</div>
              <p className="text-sm text-gray-600">Medical Terms</p>
            </div>
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{getAverageConfidence()}%</div>
              <p className="text-sm text-gray-600">Avg Confidence</p>
            </div>
            <div className="text-center p-3 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {Math.floor(transcriptEntries.length * 0.5)}
              </div>
              <p className="text-sm text-gray-600">Minutes</p>
            </div>
          </div>

          {/* Controls */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              {/* Recording Control */}
              <Button
                variant={isListening ? "danger" : "primary"}
                size="lg"
                onClick={toggleListening}
                className="rounded-full"
              >
                {isListening ? (
                  <>
                    <MicOff className="w-5 h-5 mr-2" />
                    Stop Recording
                  </>
                ) : (
                  <>
                    <Mic className="w-5 h-5 mr-2" />
                    Start Recording
                  </>
                )}
              </Button>

              {/* Speaker Selection */}
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium text-gray-700">Speaker:</span>
                <select
                  value={currentSpeaker}
                  onChange={(e) => setCurrentSpeaker(e.target.value as 'patient' | 'provider')}
                  className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-primary-500"
                >
                  <option value="patient">Patient</option>
                  <option value="provider">Provider</option>
                </select>
              </div>

              {/* Auto-scroll Toggle */}
              <Button
                variant={autoScroll ? "primary" : "outline"}
                size="sm"
                onClick={() => setAutoScroll(!autoScroll)}
              >
                Auto-scroll: {autoScroll ? 'On' : 'Off'}
              </Button>
            </div>

            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={generateSummary}
                disabled={transcriptEntries.length === 0}
              >
                <FileText className="w-4 h-4 mr-1" />
                AI Summary
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={clearTranscript}
                disabled={transcriptEntries.length === 0}
              >
                <RotateCcw className="w-4 h-4 mr-1" />
                Clear
              </Button>
            </div>
          </div>

          {/* Recording Status */}
          {isListening && (
            <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                <span className="text-red-800 font-medium">Recording in progress...</span>
                <span className="text-red-600 text-sm">Speaking as {currentSpeaker}</span>
              </div>
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Transcript */}
      <Card className="flex-1 flex flex-col">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center space-x-2">
            <MessageSquare className="w-5 h-5" />
            <span>Live Transcript</span>
          </CardTitle>
        </CardHeader>
        
        <CardContent className="flex-1 flex flex-col pt-0">
          <div
            ref={transcriptRef}
            className="flex-1 overflow-y-auto space-y-3 p-4 bg-gray-50 rounded-lg"
          >
            {transcriptEntries.length === 0 ? (
              <div className="text-center text-gray-500 py-8">
                <Mic className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No transcript yet. Start recording to begin transcription.</p>
              </div>
            ) : (
              transcriptEntries.map((entry) => (
                <div
                  key={entry.id}
                  className={clsx('p-3 rounded-lg', {
                    'bg-blue-100 border-l-4 border-blue-500': entry.speaker === 'patient',
                    'bg-green-100 border-l-4 border-green-500': entry.speaker === 'provider',
                    'bg-yellow-100 border-l-4 border-yellow-500': entry.speaker === 'system'
                  })}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <span className={clsx('font-medium text-sm', {
                        'text-blue-800': entry.speaker === 'patient',
                        'text-green-800': entry.speaker === 'provider',
                        'text-yellow-800': entry.speaker === 'system'
                      })}>
                        {entry.speaker.toUpperCase()}
                      </span>
                      <span className="text-xs text-gray-500">
                        {new Date(entry.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <span className="text-xs text-gray-500">
                        {Math.round(entry.confidence * 100)}% confidence
                      </span>
                    </div>
                  </div>
                  
                  <p className="text-gray-900 mb-2">{entry.text}</p>
                  
                  {/* Medical Terms */}
                  {showMedicalTerms && entry.medicalTerms && entry.medicalTerms.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-gray-200">
                      <p className="text-xs font-medium text-gray-600 mb-1">Medical Terms:</p>
                      <div className="flex flex-wrap gap-1">
                        {entry.medicalTerms.map((term, index) => (
                          <span
                            key={index}
                            className={clsx('px-2 py-1 text-xs rounded-full', {
                              'bg-red-200 text-red-800': term.category === 'symptom',
                              'bg-blue-200 text-blue-800': term.category === 'condition',
                              'bg-green-200 text-green-800': term.category === 'medication',
                              'bg-purple-200 text-purple-800': term.category === 'procedure'
                            })}
                          >
                            {term.term} ({Math.round(term.confidence * 100)}%)
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default VoiceInterface;
