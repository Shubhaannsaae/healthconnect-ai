/**
 * Emergency page for HealthConnect AI
 * Emergency health alert and response interface
 */

'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { EmergencyAlert } from '@/components/health/EmergencyAlert';
import { useAuthStore } from '@/store/authStore';
import { useHealthStore } from '@/store/healthStore';
import { useConsultationStore } from '@/store/consultationStore';
import { EmergencyContact } from '@/types/health';
import { 
  AlertTriangle, 
  Phone, 
  MapPin, 
  Clock,
  Heart,
  Users,
  Smartphone,
  Shield,
  Activity,
  Zap
} from 'lucide-react';
import { clsx } from 'clsx';

export default function EmergencyPage() {
  const [emergencyType, setEmergencyType] = useState<string>('');
  const [locationShared, setLocationShared] = useState(false);
  const [emergencyContacts, setEmergencyContacts] = useState<EmergencyContact[]>([
    { id: '1', name: 'John Doe', relationship: 'Spouse', phoneNumber: '+1-555-0123', isPrimary: true, canReceiveAlerts: true, preferredContactMethod: 'phone' },
    { id: '2', name: 'Jane Smith', relationship: 'Emergency Contact', phoneNumber: '+1-555-0456', isPrimary: false, canReceiveAlerts: true, preferredContactMethod: 'phone' }
  ]);

  const { userAttributes } = useAuthStore();
  const { currentVitalSigns, getCriticalAlerts } = useHealthStore();
  const { createEmergencyConsultation } = useConsultationStore();

  const emergencyTypes = [
    {
      id: 'cardiac',
      label: 'Cardiac Emergency',
      description: 'Chest pain, heart attack, irregular heartbeat',
      icon: Heart,
      color: 'bg-red-600 hover:bg-red-700',
      severity: 'critical'
    },
    {
      id: 'respiratory',
      label: 'Breathing Problems',
      description: 'Difficulty breathing, shortness of breath',
      icon: Activity,
      color: 'bg-orange-600 hover:bg-orange-700',
      severity: 'high'
    },
    {
      id: 'neurological',
      label: 'Neurological Emergency',
      description: 'Stroke, seizure, severe headache',
      icon: Zap,
      color: 'bg-purple-600 hover:bg-purple-700',
      severity: 'critical'
    },
    {
      id: 'trauma',
      label: 'Injury/Trauma',
      description: 'Severe injury, bleeding, fractures',
      icon: Shield,
      color: 'bg-yellow-600 hover:bg-yellow-700',
      severity: 'high'
    },
    {
      id: 'allergic_reaction',
      label: 'Allergic Reaction',
      description: 'Severe allergic reaction, anaphylaxis',
      icon: AlertTriangle,
      color: 'bg-red-600 hover:bg-red-700',
      severity: 'critical'
    },
    {
      id: 'other',
      label: 'Other Emergency',
      description: 'Other serious medical emergency',
      icon: Phone,
      color: 'bg-gray-600 hover:bg-gray-700',
      severity: 'high'
    }
  ];

  const handleEmergencyCall = async () => {
    // In a real implementation, this would trigger emergency services
    window.open('tel:911');
  };

  const handleLocationShare = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocationShared(true);
          console.log('Location shared:', position.coords);
          // In a real implementation, send location to emergency services
        },
        (error) => {
          console.error('Location sharing failed:', error);
        }
      );
    }
  };

  const handleEmergencyConsultation = async (type: string) => {
    if (!userAttributes?.sub) return;

    try {
      const emergencyData = {
        patientId: userAttributes.sub,
        emergencyType: type as any,
        severity: emergencyTypes.find(t => t.id === type)?.severity as any,
        vitalSigns: currentVitalSigns,
        symptoms: [],
        consciousness: 'alert' as const,
        breathing: 'normal' as const,
        pulse: 'normal' as const,
        emsNotified: false,
        triageLevel: 1 as const,
        disposition: 'treat_and_release' as const
      };

      await createEmergencyConsultation(emergencyData);
      setEmergencyType(type);
    } catch (error) {
      console.error('Failed to create emergency consultation:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Emergency Header */}
      <div className="bg-red-600 text-white rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold mb-2">Emergency Response Center</h1>
            <p className="text-red-100">
              Get immediate medical assistance and emergency care
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <Button
              size="lg"
              className="bg-white text-red-600 hover:bg-gray-100"
              onClick={handleEmergencyCall}
            >
              <Phone className="w-5 h-5 mr-2" />
              Call 911
            </Button>
          </div>
        </div>
      </div>

      {/* Critical Alerts */}
      {getCriticalAlerts().length > 0 && (
        <div className="bg-red-50 border-2 border-red-200 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-4">
            <AlertTriangle className="w-6 h-6 text-red-600" />
            <h2 className="text-lg font-semibold text-red-900">Critical Health Alerts</h2>
          </div>
          <EmergencyAlert 
            patientId={userAttributes?.sub || ''}
            emergencyContacts={emergencyContacts}
          />
        </div>
      )}

      {/* Quick Emergency Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Zap className="w-5 h-5 text-red-600" />
            <span>Quick Emergency Actions</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Button
              size="lg"
              className="bg-red-600 hover:bg-red-700 h-16"
              onClick={handleEmergencyCall}
            >
              <Phone className="w-6 h-6 mr-3" />
              <div className="text-left">
                <div className="font-semibold">Call Emergency Services</div>
                <div className="text-sm opacity-90">Immediate emergency response</div>
              </div>
            </Button>

            <Button
              size="lg"
              variant="outline"
              className="h-16 border-blue-300 hover:bg-blue-50"
              onClick={handleLocationShare}
            >
              <MapPin className="w-6 h-6 mr-3 text-blue-600" />
              <div className="text-left">
                <div className="font-semibold text-blue-900">Share Location</div>
                <div className="text-sm text-blue-700">
                  {locationShared ? 'Location shared' : 'Help responders find you'}
                </div>
              </div>
            </Button>

            <Button
              size="lg"
              variant="outline"
              className="h-16 border-green-300 hover:bg-green-50"
            >
              <Users className="w-6 h-6 mr-3 text-green-600" />
              <div className="text-left">
                <div className="font-semibold text-green-900">Contact Family</div>
                <div className="text-sm text-green-700">Notify emergency contacts</div>
              </div>
            </Button>

            <Button
              size="lg"
              variant="outline"
              className="h-16 border-purple-300 hover:bg-purple-50"
            >
              <Smartphone className="w-6 h-6 mr-3 text-purple-600" />
              <div className="text-left">
                <div className="font-semibold text-purple-900">Emergency Consultation</div>
                <div className="text-sm text-purple-700">Connect with emergency physician</div>
              </div>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Emergency Type Selection */}
      <Card>
        <CardHeader>
          <CardTitle>What type of emergency are you experiencing?</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {emergencyTypes.map((type) => (
              <button
                key={type.id}
                onClick={() => handleEmergencyConsultation(type.id)}
                className={clsx(
                  'p-6 rounded-lg text-white text-left transition-all duration-200 transform hover:scale-105',
                  type.color,
                  emergencyType === type.id && 'ring-4 ring-white ring-opacity-50'
                )}
              >
                <div className="flex items-center space-x-3 mb-3">
                  <type.icon className="w-8 h-8" />
                  <div>
                    <h3 className="font-semibold text-lg">{type.label}</h3>
                    <span className={clsx('text-xs px-2 py-1 rounded', {
                      'bg-red-800': type.severity === 'critical',
                      'bg-orange-800': type.severity === 'high'
                    })}>
                      {type.severity.toUpperCase()}
                    </span>
                  </div>
                </div>
                <p className="text-sm opacity-90">{type.description}</p>
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Current Health Status */}
      {currentVitalSigns && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Activity className="w-5 h-5 text-blue-600" />
              <span>Current Health Status</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="text-center p-4 bg-red-50 rounded-lg">
                <Heart className="w-8 h-8 text-red-600 mx-auto mb-2" />
                <div className="text-2xl font-bold text-red-900">{currentVitalSigns.heartRate}</div>
                <div className="text-sm text-red-700">Heart Rate</div>
              </div>
              
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <Activity className="w-8 h-8 text-purple-600 mx-auto mb-2" />
                <div className="text-2xl font-bold text-purple-900">
                  {currentVitalSigns.bloodPressure.systolic}/{currentVitalSigns.bloodPressure.diastolic}
                </div>
                <div className="text-sm text-purple-700">Blood Pressure</div>
              </div>
              
              <div className="text-center p-4 bg-orange-50 rounded-lg">
                <div className="w-8 h-8 bg-orange-600 rounded-full mx-auto mb-2 flex items-center justify-center text-white font-bold">
                  T
                </div>
                <div className="text-2xl font-bold text-orange-900">{currentVitalSigns.temperature.toFixed(1)}°C</div>
                <div className="text-sm text-orange-700">Temperature</div>
              </div>
              
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="w-8 h-8 bg-blue-600 rounded-full mx-auto mb-2 flex items-center justify-center text-white font-bold">
                  O2
                </div>
                <div className="text-2xl font-bold text-blue-900">{currentVitalSigns.oxygenSaturation}%</div>
                <div className="text-sm text-blue-700">Oxygen Sat</div>
              </div>
              
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <Activity className="w-8 h-8 text-green-600 mx-auto mb-2" />
                <div className="text-2xl font-bold text-green-900">{currentVitalSigns.respiratoryRate}</div>
                <div className="text-sm text-green-700">Resp Rate</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Emergency Contacts */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Users className="w-5 h-5 text-blue-600" />
            <span>Emergency Contacts</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {emergencyContacts.map((contact) => (
              <div key={contact.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                    <Users className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">{contact.name}</div>
                    <div className="text-sm text-gray-600">{contact.relationship}</div>
                  </div>
                </div>
                
                <div className="flex space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => window.open(`tel:${contact.phoneNumber}`)}
                  >
                    <Phone className="w-4 h-4 mr-1" />
                    Call
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => window.open(`sms:${contact.phoneNumber}`)}
                  >
                    <Smartphone className="w-4 h-4 mr-1" />
                    Text
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Emergency Instructions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Shield className="w-5 h-5 text-green-600" />
            <span>Emergency Instructions</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="p-4 bg-blue-50 rounded-lg">
              <h3 className="font-semibold text-blue-900 mb-2">If you're experiencing a life-threatening emergency:</h3>
              <ul className="text-blue-800 space-y-1 text-sm">
                <li>• Call 911 immediately</li>
                <li>• Stay calm and follow dispatcher instructions</li>
                <li>• Share your location if asked</li>
                <li>• Don't hang up until told to do so</li>
              </ul>
            </div>
            
            <div className="p-4 bg-green-50 rounded-lg">
              <h3 className="font-semibold text-green-900 mb-2">While waiting for help:</h3>
              <ul className="text-green-800 space-y-1 text-sm">
                <li>• Stay with the patient if possible</li>
                <li>• Keep the patient comfortable and calm</li>
                <li>• Monitor breathing and pulse</li>
                <li>• Be ready to provide information to responders</li>
              </ul>
            </div>
            
            <div className="p-4 bg-yellow-50 rounded-lg">
              <h3 className="font-semibold text-yellow-900 mb-2">Important information to have ready:</h3>
              <ul className="text-yellow-800 space-y-1 text-sm">
                <li>• Current medications and allergies</li>
                <li>• Medical history and conditions</li>
                <li>• Recent symptoms or changes</li>
                <li>• Emergency contact information</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
