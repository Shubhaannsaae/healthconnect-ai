/**
 * DeviceList component for HealthConnect AI
 * Displays and manages IoT medical devices
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { useDeviceStore } from '@/store/deviceStore';
import { DeviceCard } from './DeviceCard';
import type { DeviceInfo, DeviceFilter } from '@/types/devices';
import { 
  Plus, 
  Filter, 
  Search, 
  Wifi, 
  WifiOff, 
  AlertTriangle,
  CheckCircle,
  RefreshCw
} from 'lucide-react';
import { clsx } from 'clsx';

interface DeviceListProps {
  patientId: string | undefined;
  showFilters?: boolean;
  showAddDevice?: boolean;
  onDeviceSelect?: (device: DeviceInfo) => void;
  onAddDevice?: () => void;
  className?: string;
}

const deviceTypeOptions = [
  { value: 'heart_rate_monitor', label: 'Heart Rate Monitor' },
  { value: 'blood_pressure_cuff', label: 'Blood Pressure Cuff' },
  { value: 'glucose_meter', label: 'Glucose Meter' },
  { value: 'temperature_sensor', label: 'Temperature Sensor' },
  { value: 'pulse_oximeter', label: 'Pulse Oximeter' },
  { value: 'activity_tracker', label: 'Activity Tracker' },
  { value: 'ecg_monitor', label: 'ECG Monitor' },
  { value: 'respiratory_monitor', label: 'Respiratory Monitor' }
];

const statusOptions = [
  { value: 'online', label: 'Online', color: 'text-green-600' },
  { value: 'offline', label: 'Offline', color: 'text-gray-600' },
  { value: 'error', label: 'Error', color: 'text-red-600' },
  { value: 'maintenance', label: 'Maintenance', color: 'text-yellow-600' },
  { value: 'low_battery', label: 'Low Battery', color: 'text-orange-600' }
];

export const DeviceList: React.FC<DeviceListProps> = ({
  patientId,
  showFilters = true,
  showAddDevice = true,
  onDeviceSelect,
  onAddDevice,
  className
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFilters, setSelectedFilters] = useState<DeviceFilter>({});
  const [showFilterPanel, setShowFilterPanel] = useState(false);

  const {
    devices,
    loading,
    error,
    fetchDevices,
    getOnlineDevices,
    getOfflineDevices,
    getDevicesByType,
    getActiveAlerts,
    clearError
  } = useDeviceStore();

  // Fetch devices on mount and when patientId changes
  useEffect(() => {
    if (patientId) {
      fetchDevices(patientId, selectedFilters);
    }
  }, [patientId, selectedFilters, fetchDevices]);

  // Filter devices based on search term
  const filteredDevices = devices.filter(device => {
    const matchesSearch = !searchTerm || 
      device.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      device.manufacturer.toLowerCase().includes(searchTerm.toLowerCase()) ||
      device.model.toLowerCase().includes(searchTerm.toLowerCase());
    
    return matchesSearch;
  });

  const handleFilterChange = (key: keyof DeviceFilter, value: any) => {
    setSelectedFilters(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const clearFilters = () => {
    setSelectedFilters({});
    setSearchTerm('');
  };

  const refreshDevices = () => {
    if (patientId) {
      fetchDevices(patientId, selectedFilters);
    }
  };

  // Device statistics
  const onlineDevices = getOnlineDevices();
  const offlineDevices = getOfflineDevices();
  const activeAlerts = getActiveAlerts();

  if (loading && devices.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Medical Devices</CardTitle>
        </CardHeader>
        <CardContent>
          <LoadingSpinner size="lg" showLabel label="Loading devices..." />
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={clsx('space-y-6', className)}>
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Medical Devices</CardTitle>
            <div className="flex items-center space-x-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={refreshDevices}
                disabled={loading}
              >
                <RefreshCw className={clsx('w-4 h-4', { 'animate-spin': loading })} />
              </Button>
              {showAddDevice && (
                <Button onClick={onAddDevice} size="sm">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Device
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        
        <CardContent>
          {/* Statistics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-900">{devices.length}</div>
              <p className="text-sm text-gray-600">Total Devices</p>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="flex items-center justify-center mb-1">
                <Wifi className="w-5 h-5 text-green-600 mr-1" />
                <span className="text-2xl font-bold text-green-600">{onlineDevices.length}</span>
              </div>
              <p className="text-sm text-gray-600">Online</p>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-center mb-1">
                <WifiOff className="w-5 h-5 text-gray-600 mr-1" />
                <span className="text-2xl font-bold text-gray-600">{offlineDevices.length}</span>
              </div>
              <p className="text-sm text-gray-600">Offline</p>
            </div>
            <div className="text-center p-4 bg-red-50 rounded-lg">
              <div className="flex items-center justify-center mb-1">
                <AlertTriangle className="w-5 h-5 text-red-600 mr-1" />
                <span className="text-2xl font-bold text-red-600">{activeAlerts.length}</span>
              </div>
              <p className="text-sm text-gray-600">Alerts</p>
            </div>
          </div>

          {/* Search and Filters */}
          {showFilters && (
            <div className="space-y-4">
              <div className="flex items-center space-x-4">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <input
                    type="text"
                    placeholder="Search devices..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>
                <Button
                  variant="outline"
                  onClick={() => setShowFilterPanel(!showFilterPanel)}
                >
                  <Filter className="w-4 h-4 mr-2" />
                  Filters
                </Button>
              </div>

              {/* Filter Panel */}
              {showFilterPanel && (
                <div className="p-4 bg-gray-50 rounded-lg space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Device Type Filter */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Device Type
                      </label>
                      <select
                        value={selectedFilters.deviceTypes?.[0] || ''}
                        onChange={(e) => handleFilterChange('deviceTypes', e.target.value ? [e.target.value] : undefined)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                      >
                        <option value="">All Types</option>
                        {deviceTypeOptions.map(option => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Status Filter */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Status
                      </label>
                      <select
                        value={selectedFilters.statuses?.[0] || ''}
                        onChange={(e) => handleFilterChange('statuses', e.target.value ? [e.target.value] : undefined)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                      >
                        <option value="">All Statuses</option>
                        {statusOptions.map(option => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Battery Level Filter */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Battery Level
                      </label>
                      <select
                        value={selectedFilters.batteryLevel ? 'low' : ''}
                        onChange={(e) => handleFilterChange('batteryLevel', e.target.value ? { min: 0, max: 20 } : undefined)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                      >
                        <option value="">All Levels</option>
                        <option value="low">Low Battery (&lt; 20%)</option>
                      </select>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Button variant="outline" size="sm" onClick={clearFilters}>
                      Clear Filters
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => setShowFilterPanel(false)}>
                      Hide Filters
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Error State */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="w-5 h-5 text-red-600" />
                <div>
                  <p className="font-medium text-red-900">Error loading devices</p>
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              </div>
              <Button variant="outline" size="sm" onClick={clearError}>
                Dismiss
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Device Grid */}
      {filteredDevices.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredDevices.map((device) => (
            <DeviceCard
              key={device.id}
              device={device}
              onClick={() => onDeviceSelect?.(device)}
              showActions={true}
            />
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="p-8 text-center">
            <div className="text-gray-500">
              <CheckCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <h3 className="text-lg font-medium mb-2">No devices found</h3>
              <p className="text-sm mb-4">
                {searchTerm || Object.keys(selectedFilters).length > 0
                  ? 'No devices match your current search or filters.'
                  : 'No medical devices have been registered yet.'}
              </p>
              {showAddDevice && (
                <Button onClick={onAddDevice}>
                  <Plus className="w-4 h-4 mr-2" />
                  Add Your First Device
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default DeviceList;
