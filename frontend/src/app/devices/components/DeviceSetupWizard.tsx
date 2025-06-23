/**
 * DeviceSetupWizard component
 * Step-by-step device setup and configuration
 */

'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useDeviceStore } from '@/store/deviceStore';
import { useAuthStore } from '@/store/authStore';
import type { DeviceInfo, DeviceType } from '@/types/devices';
import { 
  Smartphone, 
  Wifi, 
  Bluetooth, 
  CheckCircle,
  AlertTriangle,
  ArrowRight,
  ArrowLeft,
  Search,
  Settings,
  Heart,
  Activity,
  Thermometer,
  Droplets
} from 'lucide-react';
import { clsx } from 'clsx';

interface DeviceSetupWizardProps {
  onComplete?: (device: DeviceInfo) => void;
  onCancel?: () => void;
  className?: string;
}

interface SetupStep {
  id: string;
  title: string;
  description: string;
  component: React.ComponentType<any>;
}

const deviceTypes = [
  {
    type: 'heart_rate_monitor' as DeviceType,
    name: 'Heart Rate Monitor',
    description: 'Monitor heart rate and rhythm',
    icon: Heart,
    color: 'text-red-600',
    bgColor: 'bg-red-100'
  },
  {
    type: 'blood_pressure_cuff' as DeviceType,
    name: 'Blood Pressure Cuff',
    description: 'Measure blood pressure readings',
    icon: Activity,
    color: 'text-purple-600',
    bgColor: 'bg-purple-100'
  },
  {
    type: 'temperature_sensor' as DeviceType,
    name: 'Temperature Sensor',
    description: 'Track body temperature',
    icon: Thermometer,
    color: 'text-orange-600',
    bgColor: 'bg-orange-100'
  },
  {
    type: 'pulse_oximeter' as DeviceType,
    name: 'Pulse Oximeter',
    description: 'Monitor oxygen saturation',
    icon: Droplets,
    color: 'text-blue-600',
    bgColor: 'bg-blue-100'
  }
];

const DeviceTypeSelection: React.FC<{
  selectedType: DeviceType | null;
  onSelect: (type: DeviceType) => void;
}> = ({ selectedType, onSelect }) => (
  <div className="space-y-4">
    <h3 className="text-lg font-medium text-gray-900">Select Device Type</h3>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {deviceTypes.map((device) => (
        <button
          key={device.type}
          onClick={() => onSelect(device.type)}
          className={clsx(
            'p-6 rounded-lg border-2 text-left transition-all duration-200',
            selectedType === device.type
              ? 'border-primary-500 bg-primary-50'
              : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
          )}
        >
          <div className="flex items-center space-x-4">
            <div className={clsx('p-3 rounded-lg', device.bgColor)}>
              <device.icon className={clsx('w-6 h-6', device.color)} />
            </div>
            <div>
              <h4 className="font-medium text-gray-900">{device.name}</h4>
              <p className="text-sm text-gray-600">{device.description}</p>
            </div>
          </div>
        </button>
      ))}
    </div>
  </div>
);

const DeviceDiscovery: React.FC<{
  deviceType: DeviceType;
  onDeviceFound: (device: any) => void;
}> = ({ deviceType, onDeviceFound }) => {
  const [isScanning, setIsScanning] = useState(false);
  const [foundDevices, setFoundDevices] = useState<any[]>([]);

  const startScanning = () => {
    setIsScanning(true);
    
    // Simulate device discovery
    setTimeout(() => {
      const mockDevices = [
        {
          id: 'device-1',
          name: `${deviceType.replace('_', ' ')} - Model A`,
          manufacturer: 'HealthTech',
          model: 'HT-100',
          serialNumber: 'HT100-12345',
          signalStrength: 85
        },
        {
          id: 'device-2',
          name: `${deviceType.replace('_', ' ')} - Model B`,
          manufacturer: 'MedDevice',
          model: 'MD-200',
          serialNumber: 'MD200-67890',
          signalStrength: 72
        }
      ];
      
      setFoundDevices(mockDevices);
      setIsScanning(false);
    }, 3000);
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Discover {deviceType.replace('_', ' ')}
        </h3>
        <p className="text-gray-600">
          Make sure your device is powered on and in pairing mode
        </p>
      </div>

      <div className="flex justify-center">
        <Button
          onClick={startScanning}
          disabled={isScanning}
          className="flex items-center space-x-2"
        >
          <Search className={clsx('w-4 h-4', { 'animate-spin': isScanning })} />
          <span>{isScanning ? 'Scanning...' : 'Start Scanning'}</span>
        </Button>
      </div>

      {foundDevices.length > 0 && (
        <div className="space-y-3">
          <h4 className="font-medium text-gray-900">Found Devices:</h4>
          {foundDevices.map((device) => (
            <div
              key={device.id}
              className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer"
              onClick={() => onDeviceFound(device)}
            >
              <div className="flex items-center justify-between">
                <div>
                  <h5 className="font-medium text-gray-900">{device.name}</h5>
                  <p className="text-sm text-gray-600">
                    {device.manufacturer} {device.model}
                  </p>
                  <p className="text-xs text-gray-500">S/N: {device.serialNumber}</p>
                </div>
                <div className="text-right">
                  <div className="flex items-center space-x-1 text-sm text-gray-600">
                    <Wifi className="w-4 h-4" />
                    <span>{device.signalStrength}%</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const DeviceConfiguration: React.FC<{
  device: any;
  onConfigured: (config: any) => void;
}> = ({ device, onConfigured }) => {
  const [config, setConfig] = useState({
    deviceName: device.name,
    measurementInterval: 60,
    autoSync: true,
    notifications: true,
    dataRetention: 30
  });

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Configure Device
        </h3>
        <p className="text-gray-600">
          Set up your device preferences and settings
        </p>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Device Name
          </label>
          <input
            type="text"
            value={config.deviceName}
            onChange={(e) => setConfig(prev => ({ ...prev, deviceName: e.target.value }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Measurement Interval (seconds)
          </label>
          <select
            value={config.measurementInterval}
            onChange={(e) => setConfig(prev => ({ ...prev, measurementInterval: parseInt(e.target.value) }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
            <option value={30}>30 seconds</option>
            <option value={60}>1 minute</option>
            <option value={300}>5 minutes</option>
            <option value={900}>15 minutes</option>
          </select>
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium text-gray-700">
              Auto Sync Data
            </label>
            <button
              onClick={() => setConfig(prev => ({ ...prev, autoSync: !prev.autoSync }))}
              className={clsx(
                'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                config.autoSync ? 'bg-primary-600' : 'bg-gray-200'
              )}
            >
              <span
                className={clsx(
                  'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                  config.autoSync ? 'translate-x-6' : 'translate-x-1'
                )}
              />
            </button>
          </div>

          <div className="flex items-center justify-between">
            <label className="text-sm font-medium text-gray-700">
              Enable Notifications
            </label>
            <button
              onClick={() => setConfig(prev => ({ ...prev, notifications: !prev.notifications }))}
              className={clsx(
                'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                config.notifications ? 'bg-primary-600' : 'bg-gray-200'
              )}
            >
              <span
                className={clsx(
                  'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                  config.notifications ? 'translate-x-6' : 'translate-x-1'
                )}
              />
            </button>
          </div>
        </div>

        <div className="flex justify-center pt-4">
          <Button onClick={() => onConfigured(config)}>
            Complete Setup
          </Button>
        </div>
      </div>
    </div>
  );
};

export const DeviceSetupWizard: React.FC<DeviceSetupWizardProps> = ({
  onComplete,
  onCancel,
  className
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedDeviceType, setSelectedDeviceType] = useState<DeviceType | null>(null);
  const [selectedDevice, setSelectedDevice] = useState<any>(null);
  const [deviceConfig, setDeviceConfig] = useState<any>(null);

  const { registerDevice } = useDeviceStore();
  const { userAttributes } = useAuthStore();

  const steps = [
    {
      id: 'type',
      title: 'Device Type',
      description: 'Select the type of device you want to add',
      component: DeviceTypeSelection
    },
    {
      id: 'discovery',
      title: 'Device Discovery',
      description: 'Find and connect to your device',
      component: DeviceDiscovery
    },
    {
      id: 'configuration',
      title: 'Configuration',
      description: 'Configure device settings',
      component: DeviceConfiguration
    }
  ];

  const currentStepData = steps[currentStep];

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(prev => prev + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
    }
  };

  const handleComplete = async () => {
    if (!selectedDevice || !deviceConfig || !userAttributes?.sub) return;

    try {
      const deviceInfo: DeviceInfo = {
        id: selectedDevice.id,
        name: deviceConfig.deviceName,
        type: selectedDeviceType!,
        manufacturer: selectedDevice.manufacturer,
        model: selectedDevice.model,
        serialNumber: selectedDevice.serialNumber,
        firmwareVersion: '1.0.0',
        regulatoryApprovals: [],
        configuration: {
          deviceId: selectedDevice.id,
          samplingRate: 1, // Placeholder
          transmissionInterval: 5, // Placeholder
          measurementInterval: deviceConfig.measurementInterval,
          autoSync: deviceConfig.autoSync,
          notifications: deviceConfig.notifications,
          dataRetention: deviceConfig.dataRetention,
          alertThresholds: {}, // Placeholder
          powerManagement: { mode: 'balanced', sleepTimeout: 300, wakeOnMotion: false }, // Placeholder
          connectivity: { preferredNetwork: 'wifi', fallbackNetworks: [], encryptionEnabled: true }, // Placeholder
          calibration: { lastCalibrated: new Date().toISOString(), nextCalibration: new Date().toISOString(), autoCalibration: true }, // Placeholder
          firmware: { currentVersion: '1.0.0', autoUpdate: true } // Placeholder
        },
        capabilities: ['real_time_monitoring', 'data_storage', 'alerts'],
        certifications: [
          { type: 'FDA', number: 'FDA-510K-123456', issuedDate: '2023-01-01', expiryDate: '2026-12-31', issuingAuthority: 'FDA' },
          { type: 'CE', number: 'CE-MD-789012', issuedDate: '2023-01-01', expiryDate: '2026-12-31', issuingAuthority: 'CE' }
        ]
      };

      await registerDevice(deviceInfo, userAttributes.sub);
      onComplete?.(deviceInfo);
    } catch (error) {
      console.error('Failed to register device:', error);
    }
  };

  const canProceed = () => {
    switch (currentStep) {
      case 0: return selectedDeviceType !== null;
      case 1: return selectedDevice !== null;
      case 2: return deviceConfig !== null;
      default: return false;
    }
  };

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Smartphone className="w-6 h-6 text-primary-600" />
          <span>Add New Device</span>
        </CardTitle>
        
        {/* Progress */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span>Step {currentStep + 1} of {steps.length}</span>
            <span>{Math.round(((currentStep + 1) / steps.length) * 100)}% complete</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-primary-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
            />
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Step Content */}
        <div className="min-h-[400px]">
          {currentStep === 0 && (
            <DeviceTypeSelection
              selectedType={selectedDeviceType}
              onSelect={setSelectedDeviceType}
            />
          )}
          
          {currentStep === 1 && selectedDeviceType && (
            <DeviceDiscovery
              deviceType={selectedDeviceType}
              onDeviceFound={(device) => {
                setSelectedDevice(device);
                handleNext();
              }}
            />
          )}
          
          {currentStep === 2 && selectedDevice && (
            <DeviceConfiguration
              device={selectedDevice}
              onConfigured={(config) => {
                setDeviceConfig(config);
                handleComplete();
              }}
            />
          )}
        </div>

        {/* Navigation */}
        <div className="flex items-center justify-between pt-6 border-t">
          <div className="flex space-x-2">
            <Button variant="outline" onClick={onCancel}>
              Cancel
            </Button>
            {currentStep > 0 && (
              <Button variant="outline" onClick={handleBack}>
                <ArrowLeft className="w-4 h-4 mr-1" />
                Back
              </Button>
            )}
          </div>
          
          <div className="flex space-x-2">
            {currentStep < steps.length - 1 && (
              <Button 
                onClick={handleNext}
                disabled={!canProceed()}
              >
                Next
                <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default DeviceSetupWizard;
