/**
 * Consultation page for HealthConnect AI
 * Telemedicine consultation interface
 */

'use client';

import React, { useState, useEffect } from 'react';
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
  Calendar,
  Clock,
  Users,
  Phone,
  Settings,
  Monitor
} from 'lucide-react';
import { clsx } from 'clsx';

export default function ConsultationPage() {
  const [activeTab, setActiveTab] = useState<'upcoming' | 'active' | 'history'>('upcoming');
  const [selectedInterface, setSelectedInterface] = useState<'video' | 'chat' | 'voice'>('video');
  
  const { userAttributes } = useAuthStore();
  const {
    currentSession,
    consultationHistory,
    availableProviders,
    isInConsultation,
    fetchConsultationHistory,
    fetchAvailableProviders
  } = useConsultationStore();

  useEffect(() => {
    if (userAttributes?.sub) {
      fetchConsultationHistory(userAttributes.sub);
      fetchAvailableProviders();
    }
  }, [userAttributes?.sub, fetchConsultationHistory, fetchAvailableProviders]);

  const upcomingConsultations = [
    {
      id: '1',
      provider: 'Dr. Sarah Johnson',
      specialty: 'Cardiology',
      date: '2025-06-22',
      time: '10:00 AM',
      type: 'Video Consultation',
      status: 'confirmed'
    },
    {
      id: '2',
      provider: 'Dr. Michael Chen',
      specialty: 'General Practice',
      date: '2025-06-25',
      time: '2:30 PM',
      type: 'Follow-up',
      status: 'pending'
    }
  ];

  const tabs = [
    { id: 'upcoming', label: 'Upcoming', icon: Calendar },
    { id: 'active', label: 'Active', icon: Video },
    { id: 'history', label: 'History', icon: Clock }
  ];

  const interfaceTabs = [
    { id: 'video', label: 'Video Call', icon: Video },
    { id: 'chat', label: 'Chat', icon: MessageSquare },
    { id: 'voice', label: 'Voice', icon: Mic }
  ];

  const renderUpcomingConsultations = () => (
    <div className="space-y-4">
      {upcomingConsultations.map((consultation) => (
        <Card key={consultation.id} className="hover:shadow-md transition-shadow">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center">
                    <Users className="w-6 h-6 text-primary-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{consultation.provider}</h3>
                    <p className="text-sm text-gray-600">{consultation.specialty}</p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-4 text-sm text-gray-600">
                  <div className="flex items-center space-x-1">
                    <Calendar className="w-4 h-4" />
                    <span>{consultation.date}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Clock className="w-4 h-4" />
                    <span>{consultation.time}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Video className="w-4 h-4" />
                    <span>{consultation.type}</span>
                  </div>
                </div>
              </div>
              
              <div className="flex items-center space-x-3">
                <span className={clsx('px-3 py-1 rounded-full text-sm font-medium', {
                  'bg-green-100 text-green-800': consultation.status === 'confirmed',
                  'bg-yellow-100 text-yellow-800': consultation.status === 'pending'
                })}>
                  {consultation.status}
                </span>
                
                <div className="flex space-x-2">
                  <Button variant="outline" size="sm">
                    <Settings className="w-4 h-4 mr-1" />
                    Reschedule
                  </Button>
                  <Button size="sm">
                    <Video className="w-4 h-4 mr-1" />
                    Join
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
      
      {upcomingConsultations.length === 0 && (
        <Card>
          <CardContent className="p-12 text-center">
            <Calendar className="w-16 h-16 mx-auto mb-4 text-gray-400" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No upcoming consultations</h3>
            <p className="text-gray-600 mb-6">Schedule a consultation with one of our healthcare providers.</p>
            <Button>
              <Calendar className="w-4 h-4 mr-2" />
              Schedule Consultation
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );

  const renderActiveConsultation = () => {
    if (!isInConsultation || !currentSession) {
      return (
        <Card>
          <CardContent className="p-12 text-center">
            <Video className="w-16 h-16 mx-auto mb-4 text-gray-400" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No active consultation</h3>
            <p className="text-gray-600 mb-6">Start a new consultation or join a scheduled one.</p>
            <div className="flex justify-center space-x-4">
              <Button variant="outline">
                <Phone className="w-4 h-4 mr-2" />
                Emergency Call
              </Button>
              <Button>
                <Video className="w-4 h-4 mr-2" />
                Start Consultation
              </Button>
            </div>
          </CardContent>
        </Card>
      );
    }

    return (
      <div className="space-y-6">
        {/* Interface Selection */}
        <Card>
          <CardHeader>
            <CardTitle>Consultation Interface</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex space-x-2">
              {interfaceTabs.map((tab) => (
                <Button
                  key={tab.id}
                  variant={selectedInterface === tab.id ? 'default' : 'outline'}
                  onClick={() => setSelectedInterface(tab.id as any)}
                  className="flex items-center space-x-2"
                >
                  <tab.icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Active Interface */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            {selectedInterface === 'video' && (
              <VideoCall
                consultationId={currentSession.id}
                userRole={userAttributes?.['custom:user_type'] === 'provider' ? 'provider' : 'patient'}
              />
            )}
            
            {selectedInterface === 'voice' && (
              <VoiceInterface
                consultationId={currentSession.id}
              />
            )}
            
            {selectedInterface === 'chat' && (
              <ChatInterface
                consultationId={currentSession.id}
                currentUserId={userAttributes?.sub || ''}
                currentUserRole={userAttributes?.['custom:user_type'] === 'provider' ? 'provider' : 'patient'}
              />
            )}
          </div>
          
          {/* Sidebar with chat when video/voice is active */}
          {selectedInterface !== 'chat' && (
            <div>
              <ChatInterface
                consultationId={currentSession.id}
                currentUserId={userAttributes?.sub || ''}
                currentUserRole={userAttributes?.['custom:user_type'] === 'provider' ? 'provider' : 'patient'}
                className="h-96"
              />
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderConsultationHistory = () => (
    <div className="space-y-4">
      {consultationHistory.map((consultation) => (
        <Card key={consultation.id} className="hover:shadow-md transition-shadow">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <div className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center">
                    <Users className="w-5 h-5 text-gray-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">
                      {'Healthcare Provider'}
                    </h3>
                    <p className="text-sm text-gray-600">{consultation.consultationType}</p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-4 text-sm text-gray-600">
                  <div className="flex items-center space-x-1">
                    <Calendar className="w-4 h-4" />
                    <span>{consultation.scheduledTime ? new Date(consultation.scheduledTime).toLocaleDateString() : 'N/A'}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Clock className="w-4 h-4" />
                    <span>{consultation.scheduledTime ? new Date(consultation.scheduledTime).toLocaleTimeString() : 'N/A'}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Clock className="w-4 h-4" />
                    <span>{consultation.duration} minutes</span>
                  </div>
                  <span className={clsx('px-2 py-1 rounded text-xs font-medium', {
                    'bg-green-100 text-green-800': consultation.status === 'completed',
                    'bg-red-100 text-red-800': consultation.status === 'cancelled',
                    'bg-yellow-100 text-yellow-800': consultation.status === 'no_show'
                  })}>
                    {consultation.status}
                  </span>
                </div>
              </div>
              
              <div className="flex space-x-2">
                <Button variant="outline" size="sm">
                  <Monitor className="w-4 h-4 mr-1" />
                  View Summary
                </Button>
                <Button variant="outline" size="sm">
                  <Calendar className="w-4 h-4 mr-1" />
                  Book Follow-up
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
      
      {consultationHistory.length === 0 && (
        <Card>
          <CardContent className="p-12 text-center">
            <Clock className="w-16 h-16 mx-auto mb-4 text-gray-400" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No consultation history</h3>
            <p className="text-gray-600">Your completed consultations will appear here.</p>
          </CardContent>
        </Card>
      )}
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Consultations</h1>
          <p className="text-gray-600">Manage your telemedicine appointments and consultations</p>
        </div>
        
        <div className="flex space-x-3">
          <Button variant="outline">
            <Phone className="w-4 h-4 mr-2" />
            Emergency Call
          </Button>
          <Button>
            <Calendar className="w-4 h-4 mr-2" />
            Schedule New
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <Card>
        <CardHeader className="border-b">
          <div className="flex space-x-1">
            {tabs.map((tab) => (
              <Button
                key={tab.id}
                variant={activeTab === tab.id ? 'default' : 'ghost'}
                onClick={() => setActiveTab(tab.id as any)}
                className="flex items-center space-x-2"
              >
                <tab.icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </Button>
            ))}
          </div>
        </CardHeader>
        
        <CardContent className="p-6">
          {activeTab === 'upcoming' && renderUpcomingConsultations()}
          {activeTab === 'active' && renderActiveConsultation()}
          {activeTab === 'history' && renderConsultationHistory()}
        </CardContent>
      </Card>

      {/* Available Providers */}
      {activeTab === 'upcoming' && (
        <Card>
          <CardHeader>
            <CardTitle>Available Healthcare Providers</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {availableProviders.slice(0, 6).map((provider) => (
                <div key={provider.providerId} className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow">
                  <div className="flex items-center space-x-3 mb-3">
                    <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center">
                      <Users className="w-6 h-6 text-primary-600" />
                    </div>
                    <div>
                      <h3 className="font-medium text-gray-900">Dr. Provider</h3>
                      <p className="text-sm text-gray-600">{provider.specialties[0]}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div className={clsx('w-2 h-2 rounded-full', {
                        'bg-green-500': provider.status === 'available',
                        'bg-yellow-500': provider.status === 'busy',
                        'bg-gray-500': provider.status === 'offline'
                      })} />
                      <span className="text-sm text-gray-600 capitalize">{provider.status}</span>
                    </div>
                    
                    <Button size="sm" disabled={provider.status !== 'available'}>
                      Book Now
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
