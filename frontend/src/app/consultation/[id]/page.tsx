/**
 * Individual consultation page for HealthConnect AI
 * Dynamic route for specific consultation sessions
 */

'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { VideoCall } from '@/components/consultation/VideoCall';
import { ChatInterface } from '@/components/consultation/ChatInterface';
import { VoiceInterface } from '@/components/consultation/VoiceInterface';
import { useConsultationStore } from '@/store/consultationStore';
import { useAuthStore } from '@/store/authStore';
import { 
  Video, 
  MessageSquare, 
  Mic, 
  Phone,
  PhoneOff,
  Users,
  Clock,
  Settings,
  Share2
} from 'lucide-react';
import { clsx } from 'clsx';

export default function ConsultationSessionPage() {
  const params = useParams();
  const router = useRouter();
  const consultationId = params.id as string;
  
  const [activeInterface, setActiveInterface] = useState<'video' | 'chat' | 'voice'>('video');
  const [sessionDuration, setSessionDuration] = useState(0);
  
  const { userAttributes } = useAuthStore();
  const {
    currentSession,
    participants,
    isConnected,
    joinConsultation,
    leaveConsultation,
    endConsultation,
    getSessionDuration
  } = useConsultationStore();

  useEffect(() => {
    if (consultationId && userAttributes?.sub) {
      const userRole = userAttributes['custom:user_type'] === 'provider' ? 'provider' : 'patient';
      joinConsultation(consultationId, userRole);
    }
  }, [consultationId, userAttributes, joinConsultation]);

  useEffect(() => {
    const interval = setInterval(() => {
      setSessionDuration(getSessionDuration());
    }, 1000);

    return () => clearInterval(interval);
  }, [getSessionDuration]);

  const handleEndSession = async () => {
    try {
      await endConsultation();
      router.push('/consultation');
    } catch (error) {
      console.error('Failed to end consultation:', error);
    }
  };

  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const interfaceOptions = [
    { id: 'video', label: 'Video Call', icon: Video },
    { id: 'chat', label: 'Chat', icon: MessageSquare },
    { id: 'voice', label: 'Voice Only', icon: Mic }
  ];

  if (!currentSession) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="p-8 text-center">
            <Video className="w-16 h-16 mx-auto mb-4 text-gray-400" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Consultation Not Found
            </h2>
            <p className="text-gray-600 mb-6">
              The consultation session you're looking for doesn't exist or has ended.
            </p>
            <Button onClick={() => router.push('/consultation')}>
              Back to Consultations
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-xl font-semibold text-gray-900">
              Consultation Session
            </h1>
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <Clock className="w-4 h-4" />
              <span>{formatDuration(sessionDuration)}</span>
            </div>
            <div className={clsx('flex items-center space-x-2 text-sm', {
              'text-green-600': isConnected,
              'text-red-600': !isConnected
            })}>
              <div className={clsx('w-2 h-2 rounded-full', {
                'bg-green-500': isConnected,
                'bg-red-500': !isConnected
              })} />
              <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-1 text-sm text-gray-600">
              <Users className="w-4 h-4" />
              <span>{participants.length} participant{participants.length !== 1 ? 's' : ''}</span>
            </div>
            
            <Button variant="outline" size="sm">
              <Share2 className="w-4 h-4 mr-1" />
              Share
            </Button>
            
            <Button variant="outline" size="sm">
              <Settings className="w-4 h-4 mr-1" />
              Settings
            </Button>
            
            <Button variant="danger" onClick={handleEndSession}>
              <PhoneOff className="w-4 h-4 mr-1" />
              End Session
            </Button>
          </div>
        </div>

        {/* Interface Selection */}
        <div className="flex space-x-2 mt-4">
          {interfaceOptions.map((option) => (
            <Button
              key={option.id}
              variant={activeInterface === option.id ? 'default' : 'outline'}
              size="sm"
              onClick={() => setActiveInterface(option.id as any)}
              className="flex items-center space-x-2"
            >
              <option.icon className="w-4 h-4" />
              <span>{option.label}</span>
            </Button>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex h-[calc(100vh-120px)]">
        {/* Primary Interface */}
        <div className="flex-1">
          {activeInterface === 'video' && (
            <VideoCall
              consultationId={consultationId}
              userRole={userAttributes?.['custom:user_type'] === 'provider' ? 'provider' : 'patient'}
              onCallEnd={handleEndSession}
              className="h-full"
            />
          )}
          
          {activeInterface === 'voice' && (
            <VoiceInterface
              consultationId={consultationId}
              className="h-full"
            />
          )}
          
          {activeInterface === 'chat' && (
            <ChatInterface
              consultationId={consultationId}
              currentUserId={userAttributes?.sub || ''}
              currentUserRole={userAttributes?.['custom:user_type'] === 'provider' ? 'provider' : 'patient'}
              className="h-full"
            />
          )}
        </div>

        {/* Sidebar Chat (when not primary) */}
        {activeInterface !== 'chat' && (
          <div className="w-80 border-l border-gray-200 bg-white">
            <ChatInterface
              consultationId={consultationId}
              currentUserId={userAttributes?.sub || ''}
              currentUserRole={userAttributes?.['custom:user_type'] === 'provider' ? 'provider' : 'patient'}
              className="h-full"
            />
          </div>
        )}
      </div>
    </div>
  );
}
