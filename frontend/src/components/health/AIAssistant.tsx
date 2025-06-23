/**
 * AI Assistant component for HealthConnect AI
 * Provides AI-powered health insights and recommendations
 */

import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { useVoiceRecognition } from '@/hooks/useVoiceRecognition';
import { apiClient } from '@/lib/aws-config';
import type { VitalSigns, HealthInsight } from '@/types/health';
import { 
  Bot, 
  Mic, 
  MicOff, 
  Send, 
  Volume2, 
  VolumeX, 
  MessageSquare,
  Lightbulb,
  AlertTriangle,
  CheckCircle
} from 'lucide-react';
import { clsx } from 'clsx';

interface AIAssistantProps {
  patientId?: string;
  vitalSigns?: VitalSigns;
  className?: string;
}

interface Message {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  insights?: HealthInsight[];
  recommendations?: string[];
}

interface AIResponse {
  message: string;
  insights: HealthInsight[];
  recommendations: string[];
  urgencyLevel: 'low' | 'medium' | 'high' | 'critical';
}

export const AIAssistant: React.FC<AIAssistantProps> = ({
  patientId,
  vitalSigns,
  className
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const speechSynthesis = useRef<SpeechSynthesis | null>(null);

  const {
    start: startListening,
    stop: stopListening,
    isSupported: isVoiceSupported,
    lastResult
  } = useVoiceRecognition({
    onResult: (result) => {
      if (result.isFinal) {
        setInputValue(result.transcript);
        setIsListening(false);
      }
    },
    onError: (error) => {
      console.error('Voice recognition error:', error);
      setIsListening(false);
    }
  });

  // Initialize speech synthesis
  useEffect(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      speechSynthesis.current = window.speechSynthesis;
    }
  }, []);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Add welcome message on mount
  useEffect(() => {
    const welcomeMessage: Message = {
      id: 'welcome',
      type: 'assistant',
      content: "Hello! I'm your AI health assistant. I can help analyze your health data, answer questions about your vital signs, and provide personalized health recommendations. How can I assist you today?",
      timestamp: new Date().toISOString()
    };
    setMessages([welcomeMessage]);
  }, []);

  const sendMessage = async (content: string) => {
    if (!content.trim() || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: content.trim(),
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.post({
        apiName: 'HealthConnectAPI',
        path: '/health/ai-assistant',
        options: {
          body: {
            message: content,
            patientId,
            vitalSigns,
            context: messages.slice(-5) // Last 5 messages for context
          }
        }
      });

      if (response.success) {
        const aiResponse: AIResponse = response.data;
        
        const assistantMessage: Message = {
          id: `assistant-${Date.now()}`,
          type: 'assistant',
          content: aiResponse.message,
          timestamp: new Date().toISOString(),
          insights: aiResponse.insights,
          recommendations: aiResponse.recommendations
        };

        setMessages(prev => [...prev, assistantMessage]);

        // Speak the response if enabled
        if (speechSynthesis.current && !isSpeaking) {
          speakText(aiResponse.message);
        }
      } else {
        throw new Error(response.error?.message || 'Failed to get AI response');
      }
    } catch (error) {
      const errorMessage = (error as Error).message;
      setError(errorMessage);
      
      const errorResponse: Message = {
        id: `error-${Date.now()}`,
        type: 'system',
        content: `I apologize, but I'm having trouble processing your request right now. Please try again later. Error: ${errorMessage}`,
        timestamp: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, errorResponse]);
    } finally {
      setIsLoading(false);
    }
  };

  const speakText = (text: string) => {
    if (!speechSynthesis.current) return;

    // Cancel any ongoing speech
    speechSynthesis.current.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    utterance.pitch = 1;
    utterance.volume = 0.8;

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    speechSynthesis.current.speak(utterance);
  };

  const stopSpeaking = () => {
    if (speechSynthesis.current) {
      speechSynthesis.current.cancel();
      setIsSpeaking(false);
    }
  };

  const handleVoiceToggle = () => {
    if (isListening) {
      stopListening();
      setIsListening(false);
    } else {
      startListening();
      setIsListening(true);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(inputValue);
  };

  const renderMessage = (message: Message) => {
    const isUser = message.type === 'user';
    const isSystem = message.type === 'system';

    return (
      <div
        key={message.id}
        className={clsx('flex mb-4', {
          'justify-end': isUser,
          'justify-start': !isUser
        })}
      >
        <div
          className={clsx('max-w-[80%] rounded-lg px-4 py-3', {
            'bg-primary-600 text-white': isUser,
            'bg-gray-100 text-gray-900': !isUser && !isSystem,
            'bg-red-50 text-red-800 border border-red-200': isSystem
          })}
        >
          <div className="flex items-start space-x-2">
            {!isUser && !isSystem && (
              <Bot className="w-5 h-5 mt-0.5 text-primary-600 flex-shrink-0" />
            )}
            <div className="flex-1">
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>
              
              {/* Insights */}
              {message.insights && message.insights.length > 0 && (
                <div className="mt-3 space-y-2">
                  <p className="text-xs font-medium text-gray-600">Health Insights:</p>
                  {message.insights.map((insight, index) => (
                    <div
                      key={index}
                      className={clsx('flex items-start space-x-2 p-2 rounded text-xs', {
                        'bg-green-50 text-green-800': insight.priority === 'low',
                        'bg-yellow-50 text-yellow-800': insight.priority === 'medium',
                        'bg-red-50 text-red-800': insight.priority === 'high'
                      })}
                    >
                      <Lightbulb className="w-3 h-3 mt-0.5 flex-shrink-0" />
                      <span>{insight.description}</span>
                    </div>
                  ))}
                </div>
              )}
              
              {/* Recommendations */}
              {message.recommendations && message.recommendations.length > 0 && (
                <div className="mt-3 space-y-1">
                  <p className="text-xs font-medium text-gray-600">Recommendations:</p>
                  {message.recommendations.map((rec, index) => (
                    <div key={index} className="flex items-start space-x-2 text-xs">
                      <CheckCircle className="w-3 h-3 mt-0.5 text-green-600 flex-shrink-0" />
                      <span>{rec}</span>
                    </div>
                  ))}
                </div>
              )}
              
              <p className="text-xs opacity-70 mt-2">
                {new Date(message.timestamp).toLocaleTimeString()}
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <Card className={clsx('flex flex-col h-[600px]', className)}>
      <CardHeader className="border-b">
        <CardTitle className="flex items-center space-x-2">
          <Bot className="w-5 h-5 text-primary-600" />
          <span>AI Health Assistant</span>
          {isSpeaking && (
            <div className="flex items-center space-x-1 text-sm text-green-600">
              <Volume2 className="w-4 h-4" />
              <span>Speaking...</span>
            </div>
          )}
        </CardTitle>
      </CardHeader>
      
      <CardContent className="flex-1 flex flex-col p-0">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map(renderMessage)}
          
          {isLoading && (
            <div className="flex justify-start mb-4">
              <div className="bg-gray-100 rounded-lg px-4 py-3 max-w-[80%]">
                <div className="flex items-center space-x-2">
                  <Bot className="w-5 h-5 text-primary-600" />
                  <LoadingSpinner size="sm" type="dots" variant="primary" />
                  <span className="text-sm text-gray-600">Analyzing...</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
        
        {/* Input */}
        <div className="border-t p-4">
          <form onSubmit={handleSubmit} className="flex items-center space-x-2">
            <div className="flex-1 relative">
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Ask about your health data, symptoms, or get recommendations..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                disabled={isLoading}
              />
              {isListening && (
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                  <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                </div>
              )}
            </div>
            
            {/* Voice input button */}
            {isVoiceSupported && (
              <Button
                type="button"
                variant={isListening ? "danger" : "ghost"}
                size="icon"
                onClick={handleVoiceToggle}
                disabled={isLoading}
              >
                {isListening ? (
                  <MicOff className="w-4 h-4" />
                ) : (
                  <Mic className="w-4 h-4" />
                )}
              </Button>
            )}
            
            {/* Speech toggle button */}
            {speechSynthesis.current && (
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={isSpeaking ? stopSpeaking : undefined}
                disabled={!isSpeaking}
              >
                {isSpeaking ? (
                  <VolumeX className="w-4 h-4" />
                ) : (
                  <Volume2 className="w-4 h-4" />
                )}
              </Button>
            )}
            
            {/* Send button */}
            <Button
              type="submit"
              disabled={!inputValue.trim() || isLoading}
              size="icon"
            >
              <Send className="w-4 h-4" />
            </Button>
          </form>
          
          {error && (
            <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-red-800 text-sm">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4" />
                <span>{error}</span>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default AIAssistant;
