/**
 * Devices page for HealthConnect AI
 * IoT medical device management interface
 */

'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { DeviceList } from '@/components/devices/DeviceList';
import { DeviceSimulator } from '@/components/devices/DeviceSimulator';
import { useAuthStore } from '@/store/authStore';
import { useDeviceStore } from '@/store/deviceStore';
import { 
  Smartphone, 
  Plus, 
  Activity, 
  Wifi,
  WifiOff,
  AlertTriangle,
  Settings,
  BarChart3,
  Zap
} from 'lucide-react';
import { clsx } from 'clsx';

export default function DevicesPage() {
  const [activeTab, setActiveTab] = useState<'devices' | 'simulator' | 'analytics'>('devices');
  const [showAddDevice, setShowAddDevice] = useState(false);

  const { userAttributes } = useAuthStore();
  const {
    devices,
    getOnlineDevices,
    getOfflineDevices,
    getActiveAlerts,
    getCriticalAlerts,
    fetchDevices
  } = useDeviceStore();

  useEffect(() => {
    if (userAttributes?.sub) {
      fetchDevices(userAttributes.sub);
    }
  }, [userAttributes?.sub, fetchDevices]);

  const onlineDevices = getOnlineDevices();
  const offlineDevices = getOfflineDevices();
  const activeAlerts = getActiveAlerts();
  const criticalAlerts = getCriticalAlerts();

  const deviceStats = [
    {
      title: 'Total Devices',
      value: devices.length,
      icon: Smartphone,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100'
    },
    {
      title: 'Online',
      value: onlineDevices.length,
      icon: Wifi,
      color: 'text-green-600',
      bgColor: 'bg-green-100'
    },
    {
      title: 'Offline',
      value: offlineDevices.length,
      icon: WifiOff,
      color: 'text-gray-600',
      bgColor: 'bg-gray-100'
    },
    {
      title: 'Alerts',
      value: activeAlerts.length,
      icon: AlertTriangle,
      color: criticalAlerts.length > 0 ? 'text-red-600' : 'text-yellow-600',
      bgColor: criticalAlerts.length > 0 ? 'bg-red-100' : 'bg-yellow-100'
    }
  ];

  const tabs = [
    { id: 'devices', label: 'My Devices', icon: Smartphone },
    { id: 'simulator', label: 'Device Simulator', icon: Zap },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Medical Devices</h1>
          <p className="text-gray-600">Manage and monitor your connected medical devices</p>
        </div>
        
        <div className="flex space-x-3">
          <Button variant="outline">
            <Settings className="w-4 h-4 mr-2" />
            Settings
          </Button>
          <Button onClick={() => setShowAddDevice(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Add Device
          </Button>
        </div>
      </div>

      {/* Device Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {deviceStats.map((stat, index) => (
          <Card key={index} className="hover:shadow-lg transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                  <p className="text-2xl font-semibold text-gray-900 mt-2">{stat.value}</p>
                </div>
                <div className={clsx('p-3 rounded-lg', stat.bgColor)}>
                  <stat.icon className={clsx('w-6 h-6', stat.color)} />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
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
          {activeTab === 'devices' && (
            <DeviceList
              patientId={userAttributes?.sub}
              showFilters={true}
              showAddDevice={true}
              onAddDevice={() => setShowAddDevice(true)}
            />
          )}
          
          {activeTab === 'simulator' && (
            <DeviceSimulator />
          )}
          
          {activeTab === 'analytics' && (
            <div className="text-center py-12">
              <BarChart3 className="w-16 h-16 mx-auto mb-4 text-gray-400" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Device Analytics</h3>
              <p className="text-gray-600">Detailed analytics and insights coming soon.</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Actions for Empty State */}
      {devices.length === 0 && activeTab === 'devices' && (
        <Card>
          <CardContent className="p-12 text-center">
            <Smartphone className="w-16 h-16 mx-auto mb-4 text-gray-400" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No devices connected</h3>
            <p className="text-gray-600 mb-6">
              Connect your medical devices to start monitoring your health automatically.
            </p>
            <div className="flex justify-center space-x-4">
              <Button onClick={() => setShowAddDevice(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Add Your First Device
              </Button>
              <Button variant="outline" onClick={() => setActiveTab('simulator')}>
                <Zap className="w-4 h-4 mr-2" />
                Try Device Simulator
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
