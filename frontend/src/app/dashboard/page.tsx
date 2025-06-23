/**
 * Dashboard overview page for HealthConnect AI
 * Main dashboard with health overview and quick actions
 */

'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { VitalSigns } from '@/components/health/VitalSigns';
import { HealthChart } from '@/components/health/HealthChart';
import { AIAssistant } from '@/components/health/AIAssistant';
import { EmergencyAlert } from '@/components/health/EmergencyAlert';
import { DeviceList } from '@/components/devices/DeviceList';
import { HealthVisualization } from '@/components/3d/HealthVisualization';
import { useAuthStore } from '@/store/authStore';
import { useHealthStore } from '@/store/healthStore';
import { useDeviceStore } from '@/store/deviceStore';
import { 
  Heart, 
  Activity, 
  TrendingUp, 
  Calendar,
  Users,
  Shield,
  AlertTriangle,
  CheckCircle,
  Clock,
  Zap
} from 'lucide-react';
import Link from 'next/link';

export default function DashboardPage() {
  const { userAttributes } = useAuthStore();
  const {
    currentVitalSigns,
    healthRecords,
    getActiveAlerts,
    getCriticalAlerts,
    getHealthScore,
    getAbnormalVitals
  } = useHealthStore();

  const activeAlerts = getActiveAlerts();
  const criticalAlerts = getCriticalAlerts();
  
  const {
    devices,
    getOnlineDevices,
    getOfflineDevices
  } = useDeviceStore();

  const deviceCriticalAlerts = getCriticalAlerts();

  const [selectedTimeframe, setSelectedTimeframe] = useState<'24h' | '7d' | '30d'>('24h');

  const healthScore = getHealthScore();
  const abnormalVitals = getAbnormalVitals();
  const onlineDevices = getOnlineDevices();
  const offlineDevices = getOfflineDevices();
  const deviceAlerts = deviceCriticalAlerts;

  // Quick stats for dashboard cards
  const dashboardStats = [
    {
      title: 'Health Score',
      value: healthScore,
      unit: '/100',
      icon: Heart,
      color: healthScore >= 80 ? 'text-green-600' : healthScore >= 60 ? 'text-yellow-600' : 'text-red-600',
      bgColor: healthScore >= 80 ? 'bg-green-100' : healthScore >= 60 ? 'bg-yellow-100' : 'bg-red-100',
      trend: '+2.5%',
      trendDirection: 'up' as const
    },
    {
      title: 'Active Devices',
      value: onlineDevices.length,
      unit: `/${devices.length}`,
      icon: Activity,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
      trend: `${offlineDevices.length} offline`,
      trendDirection: offlineDevices.length === 0 ? 'up' : 'down' as const
    },
    {
      title: 'Health Records',
      value: healthRecords.length,
      unit: 'total',
      icon: TrendingUp,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
      trend: '+12 this week',
      trendDirection: 'up' as const
    },
    {
      title: 'Active Alerts',
      value: activeAlerts.length,
      unit: criticalAlerts.length > 0 ? `${criticalAlerts.length} critical` : 'none critical',
      icon: AlertTriangle,
      color: criticalAlerts.length > 0 ? 'text-red-600' : 'text-green-600',
      bgColor: criticalAlerts.length > 0 ? 'bg-red-100' : 'bg-green-100',
      trend: criticalAlerts.length === 0 ? 'All clear' : 'Needs attention',
      trendDirection: criticalAlerts.length === 0 ? 'up' : 'down' as const
    }
  ];

  const quickActions = [
    {
      title: 'Start Consultation',
      description: 'Connect with a healthcare provider',
      icon: Users,
      href: '/consultation',
      color: 'bg-blue-600 hover:bg-blue-700'
    },
    {
      title: 'Emergency Alert',
      description: 'Immediate medical assistance',
      icon: AlertTriangle,
      href: '/emergency',
      color: 'bg-red-600 hover:bg-red-700'
    },
    {
      title: 'Add Health Data',
      description: 'Record new health information',
      icon: Heart,
      href: '/dashboard/health/add',
      color: 'bg-green-600 hover:bg-green-700'
    },
    {
      title: 'Device Setup',
      description: 'Connect new medical devices',
      icon: Activity,
      href: '/devices/setup',
      color: 'bg-purple-600 hover:bg-purple-700'
    }
  ];

  const upcomingAppointments = [
    {
      id: 1,
      provider: 'Dr. Sarah Johnson',
      specialty: 'Cardiology',
      date: '2025-06-22',
      time: '10:00 AM',
      type: 'Video Consultation'
    },
    {
      id: 2,
      provider: 'Dr. Michael Chen',
      specialty: 'General Practice',
      date: '2025-06-25',
      time: '2:30 PM',
      type: 'Follow-up'
    }
  ];

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-primary-600 to-purple-600 rounded-lg p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold mb-2">
              Welcome back, {userAttributes?.given_name}!
            </h1>
            <p className="text-blue-100">
              Here's your health overview for today. Your health score is {healthScore}/100.
            </p>
          </div>
          <div className="hidden md:flex items-center space-x-4">
            <div className="text-center">
              <div className="text-3xl font-bold">{healthScore}</div>
              <div className="text-sm text-blue-100">Health Score</div>
            </div>
          </div>
        </div>
      </div>

      {/* Critical Alerts */}
      {criticalAlerts.length > 0 && (
        <EmergencyAlert
          patientId={userAttributes?.sub || ''}
          className="mb-6"
        />
      )}

      {/* Dashboard Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {dashboardStats.map((stat, index) => (
          <Card key={index} className="hover:shadow-lg transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                  <div className="flex items-baseline mt-2">
                    <p className="text-2xl font-semibold text-gray-900">
                      {stat.value}
                    </p>
                    <p className="ml-1 text-sm text-gray-500">{stat.unit}</p>
                  </div>
                  <div className="flex items-center mt-2">
                    <span className={`text-xs font-medium ${
                      stat.trendDirection === 'up' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {stat.trend}
                    </span>
                  </div>
                </div>
                <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                  <stat.icon className="w-6 h-6 ${stat.color}" />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Health Data */}
        <div className="lg:col-span-2 space-y-6">
          {/* Vital Signs */}
          <VitalSigns
            patientId={userAttributes?.sub || ''}
            showTrends={true}
            showAlerts={false}
          />

          {/* Health Chart */}
          {currentVitalSigns && (
            <HealthChart
              data={healthRecords
                .filter(record => record.vitalSigns)
                .map(record => record.vitalSigns!)
                .slice(-20)
              }
              metric="heartRate"
              title="Heart Rate Trend"
              timeframe={selectedTimeframe}
              onTimeframeChange={(tf) => setSelectedTimeframe(tf as any)}
              height={300}
            />
          )}

          {/* 3D Visualization */}
          {currentVitalSigns && (
            <HealthVisualization
              vitalSigns={currentVitalSigns}
              visualizationType="heart"
              isAnimated={true}
              showControls={true}
            />
          )}

          {currentVitalSigns && (
            <HealthVisualization
              vitalSigns={currentVitalSigns}
              visualizationType="data_flow"
              isAnimated={true}
              showControls={true}
            />
          )}
        </div>

        {/* Right Column - Sidebar */}
        <div className="space-y-6">
          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Zap className="w-5 h-5 text-primary-600" />
                <span>Quick Actions</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {quickActions.map((action, index) => (
                <Link key={index} href={action.href}>
                  <Button 
                    variant="ghost" 
                    className="w-full justify-start h-auto p-3 hover:bg-gray-50"
                  >
                    <div className={`p-2 rounded-lg ${action.color} mr-3`}>
                      <action.icon className="w-4 h-4 text-white" />
                    </div>
                    <div className="text-left">
                      <div className="font-medium text-gray-900">{action.title}</div>
                      <div className="text-sm text-gray-500">{action.description}</div>
                    </div>
                  </Button>
                </Link>
              ))}
            </CardContent>
          </Card>

          {/* Upcoming Appointments */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Calendar className="w-5 h-5 text-primary-600" />
                <span>Upcoming Appointments</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {upcomingAppointments.length > 0 ? (
                <div className="space-y-3">
                  {upcomingAppointments.map((appointment) => (
                    <div key={appointment.id} className="p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <div className="font-medium text-gray-900">
                          {appointment.provider}
                        </div>
                        <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                          {appointment.type}
                        </span>
                      </div>
                      <div className="text-sm text-gray-600">
                        {appointment.specialty}
                      </div>
                      <div className="flex items-center mt-2 text-sm text-gray-500">
                        <Clock className="w-4 h-4 mr-1" />
                        {appointment.date} at {appointment.time}
                      </div>
                    </div>
                  ))}
                  <Link href="/consultation">
                    <Button variant="outline" size="sm" className="w-full">
                      View All Appointments
                    </Button>
                  </Link>
                </div>
              ) : (
                <div className="text-center py-4 text-gray-500">
                  <Calendar className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>No upcoming appointments</p>
                  <Link href="/consultation">
                    <Button variant="outline" size="sm" className="mt-2">
                      Schedule Consultation
                    </Button>
                  </Link>
                </div>
              )}
            </CardContent>
          </Card>

          {/* AI Assistant */}
          {currentVitalSigns && (
            <AIAssistant
              patientId={userAttributes?.sub || ''}
              vitalSigns={currentVitalSigns}
              className="h-96"
            />
          )}
        </div>
      </div>

      {/* Device Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Activity className="w-5 h-5 text-primary-600" />
              <span>Connected Devices</span>
            </div>
            <Link href="/devices">
              <Button variant="outline" size="sm">
                Manage Devices
              </Button>
            </Link>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {devices.length > 0 ? (
            <DeviceList
              patientId={userAttributes?.sub || ''}
              showFilters={false}
              showAddDevice={false}
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
            />
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Activity className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <h3 className="text-lg font-medium mb-2">No devices connected</h3>
              <p className="text-sm mb-4">
                Connect your medical devices to start monitoring your health automatically.
              </p>
              <Link href="/devices/setup">
                <Button>
                  Connect Your First Device
                </Button>
              </Link>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
