/**
 * DeviceSimulator component for HealthConnect AI
 * Interface for simulating IoT medical devices
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { useDeviceSimulator } from '@/hooks/useDeviceSimulator';
import { useAuthStore } from '@/store/authStore';
import type { DeviceType, SimulatedReading } from '@/types/devices';
import { 
  Play, 
  Pause, 
  Square, 
  Settings, 
  TrendingUp, 
  Activity,
  Heart,
  Thermometer,
  Droplets,
  Gauge,
  Wind,
  BarChart3
} from 'lucide-react';
import { clsx } from 'clsx';

interface DeviceSimulatorProps {
  className?: string;
}

interface SimulationConfigForm {
  deviceType: DeviceType;
  duration: number;
  dataFrequency: number;
  anomalyProbability: number;
  baselineValues: Record<string, number>;
  variability: Record<string, number>;
}

const deviceTypeOptions = [
  { value: 'heart_rate_monitor', label: 'Heart Rate Monitor', icon: Heart },
  { value: 'blood_pressure_cuff', label: 'Blood Pressure Cuff', icon: Gauge },
  { value: 'glucose_meter', label: 'Glucose Meter', icon: Droplets },
  { value: 'temperature_sensor', label: 'Temperature Sensor', icon: Thermometer },
  { value: 'pulse_oximeter', label: 'Pulse Oximeter', icon: Activity },
  { value: 'activity_tracker', label: 'Activity Tracker', icon: TrendingUp },
  { value: 'ecg_monitor', label: 'ECG Monitor', icon: Heart },
  { value: 'respiratory_monitor', label: 'Respiratory Monitor', icon: Wind }
];

const scenarioOptions = [
  { value: 'normal', label: 'Normal Operation', description: 'Simulate normal device readings' },
  { value: 'hypertensive_crisis', label: 'Hypertensive Crisis', description: 'Simulate high blood pressure emergency' },
  { value: 'hypoglycemic_episode', label: 'Hypoglycemic Episode', description: 'Simulate low blood sugar event' },
  { value: 'cardiac_arrhythmia', label: 'Cardiac Arrhythmia', description: 'Simulate irregular heart rhythm' },
  { value: 'respiratory_distress', label: 'Respiratory Distress', description: 'Simulate breathing difficulties' }
];

export const DeviceSimulator: React.FC<DeviceSimulatorProps> = ({ className }) => {
  const { userAttributes } = useAuthStore();
  const {
    activeSimulations,
    simulatedData,
    isSimulating,
    error,
    startSimulation,
    stopSimulation,
    stopAllSimulations,
    createScenario,
    getDeviceConfiguration,
    clearError
  } = useDeviceSimulator({
    patientId: userAttributes?.sub
  });

  const [showConfigForm, setShowConfigForm] = useState(false);
  const [selectedDeviceType, setSelectedDeviceType] = useState<DeviceType>('heart_rate_monitor');
  const [selectedScenario, setSelectedScenario] = useState('normal');
  const [configForm, setConfigForm] = useState<SimulationConfigForm>({
    deviceType: 'heart_rate_monitor',
    duration: 30,
    dataFrequency: 10,
    anomalyProbability: 0.05,
    baselineValues: {},
    variability: {}
  });

  // Update config form when device type changes
  useEffect(() => {
    const deviceConfig = getDeviceConfiguration(selectedDeviceType);
    setConfigForm(prev => ({
      ...prev,
      deviceType: selectedDeviceType,
      baselineValues: deviceConfig.baselineValues,
      variability: deviceConfig.variability,
      dataFrequency: deviceConfig.dataFrequency,
      anomalyProbability: deviceConfig.anomalyProbability
    }));
  }, [selectedDeviceType, getDeviceConfiguration]);

  const handleStartSimulation = async () => {
    if (!userAttributes?.sub) return;

    try {
      const config = {
        ...configForm,
        patientId: userAttributes.sub
      };

      await startSimulation(config);
      setShowConfigForm(false);
    } catch (error) {
      console.error('Failed to start simulation:', error);
    }
  };

  const handleStopSimulation = async (simulationId: string) => {
    try {
      await stopSimulation(simulationId);
    } catch (error) {
      console.error('Failed to stop simulation:', error);
    }
  };

  const handleStopAllSimulations = async () => {
    try {
      await stopAllSimulations();
    } catch (error) {
      console.error('Failed to stop all simulations:', error);
    }
  };

  const handleScenarioStart = async (scenarioType: string) => {
    if (!userAttributes?.sub) return;

    try {
      const scenario = createScenario(scenarioType, userAttributes.sub);
      // Start simulation with scenario parameters
      const config = {
        deviceType: selectedDeviceType,
        patientId: userAttributes.sub,
        duration: scenario.duration,
        dataFrequency: 5,
        anomalyProbability: scenarioType === 'normal' ? 0.02 : 0.8,
        baselineValues: getDeviceConfiguration(selectedDeviceType).baselineValues,
        variability: getDeviceConfiguration(selectedDeviceType).variability
      };

      await startSimulation(config);
    } catch (error) {
      console.error('Failed to start scenario:', error);
    }
  };

  const getLatestReading = (deviceId: string): SimulatedReading | null => {
    const readings = simulatedData.get(deviceId);
    return readings && readings.length > 0 ? readings[0] : null;
  };

  return (
    <div className={clsx('space-y-6', className)}>
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center space-x-2">
              <Activity className="w-5 h-5 text-primary-600" />
              <span>Device Simulator</span>
            </CardTitle>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                onClick={() => setShowConfigForm(true)}
                disabled={isSimulating}
              >
                <Settings className="w-4 h-4 mr-2" />
                Configure
              </Button>
              {isSimulating && (
                <Button
                  variant="danger"
                  onClick={handleStopAllSimulations}
                >
                  <Square className="w-4 h-4 mr-2" />
                  Stop All
                </Button>
              )}
            </div>
          </div>
        </CardHeader>

        <CardContent>
          {/* Quick Start Scenarios */}
          <div className="space-y-4">
            <h3 className="font-medium text-gray-900">Quick Start Scenarios</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {scenarioOptions.map((scenario) => (
                <Card
                  key={scenario.value}
                  className="cursor-pointer hover:shadow-md transition-shadow"
                  onClick={() => handleScenarioStart(scenario.value)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="font-medium text-gray-900">{scenario.label}</h4>
                        <p className="text-sm text-gray-600 mt-1">{scenario.description}</p>
                      </div>
                      <Play className="w-5 h-5 text-primary-600 flex-shrink-0 mt-1" />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          {/* Device Type Selection */}
          <div className="mt-6 space-y-4">
            <h3 className="font-medium text-gray-900">Select Device Type</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {deviceTypeOptions.map((option) => {
                const IconComponent = option.icon;
                return (
                  <button
                    key={option.value}
                    onClick={() => setSelectedDeviceType(option.value as DeviceType)}
                    className={clsx(
                      'p-3 rounded-lg border-2 transition-colors text-center',
                      selectedDeviceType === option.value
                        ? 'border-primary-500 bg-primary-50 text-primary-700'
                        : 'border-gray-200 hover:border-gray-300 text-gray-700'
                    )}
                  >
                    <IconComponent className="w-6 h-6 mx-auto mb-2" />
                    <span className="text-xs font-medium">{option.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Active Simulations */}
      {activeSimulations.size > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Active Simulations</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Array.from(activeSimulations.entries()).map(([simulationId, simulation]) => {
                const latestReading = getLatestReading(simulationId);
                const IconComponent = deviceTypeOptions.find(
                  opt => opt.value === simulation.deviceType
                )?.icon || Activity;

                return (
                  <div
                    key={simulationId}
                    className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="p-2 bg-primary-100 rounded-lg">
                        <IconComponent className="w-5 h-5 text-primary-600" />
                      </div>
                      <div>
                        <h4 className="font-medium text-gray-900">
                          {deviceTypeOptions.find(opt => opt.value === simulation.deviceType)?.label}
                        </h4>
                        <p className="text-sm text-gray-600">
                          Running for {Math.floor((Date.now() - new Date(simulation.createdAt).getTime()) / 60000)} minutes
                        </p>
                        {latestReading && (
                          <div className="flex items-center space-x-4 mt-1 text-xs text-gray-500">
                            <span>Quality: {latestReading.quality}</span>
                            <span>Anomaly: {latestReading.anomaly ? 'Yes' : 'No'}</span>
                            <span>Last: {new Date(latestReading.timestamp).toLocaleTimeString()}</span>
                          </div>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleStopSimulation(simulationId)}
                      >
                        <Square className="w-4 h-4 mr-1" />
                        Stop
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Simulated Data Display */}
      {simulatedData.size > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <BarChart3 className="w-5 h-5" />
              <span>Live Data</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Array.from(simulatedData.entries()).map(([deviceId, readings]) => {
                const latestReading = readings[0];
                if (!latestReading) return null;

                return (
                  <div key={deviceId} className="p-4 bg-gray-50 rounded-lg">
                    <h4 className="font-medium text-gray-900 mb-3">Device Data</h4>
                    <div className="space-y-2">
                      {Object.entries(latestReading.data).map(([key, value]) => (
                        <div key={key} className="flex justify-between text-sm">
                          <span className="text-gray-600 capitalize">
                            {key.replace(/_/g, ' ')}:
                          </span>
                          <span className="font-medium">
                            {typeof value === 'number' ? value.toFixed(1) : value}
                          </span>
                        </div>
                      ))}
                    </div>
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <div className="flex items-center justify-between text-xs text-gray-500">
                        <span>Quality: {latestReading.quality}</span>
                        <span className={clsx(
                          'px-2 py-1 rounded',
                          latestReading.anomaly 
                            ? 'bg-red-100 text-red-700' 
                            : 'bg-green-100 text-green-700'
                        )}>
                          {latestReading.anomaly ? 'Anomaly' : 'Normal'}
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Configuration Modal */}
      {showConfigForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">Simulation Configuration</h3>
            
            <div className="space-y-4">
              {/* Device Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Device Type
                </label>
                <select
                  value={configForm.deviceType}
                  onChange={(e) => setConfigForm(prev => ({ 
                    ...prev, 
                    deviceType: e.target.value as DeviceType 
                  }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500"
                >
                  {deviceTypeOptions.map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Duration */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Duration (minutes)
                </label>
                <input
                  type="number"
                  min="1"
                  max="1440"
                  value={configForm.duration}
                  onChange={(e) => setConfigForm(prev => ({ 
                    ...prev, 
                    duration: parseInt(e.target.value) 
                  }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500"
                />
              </div>

              {/* Data Frequency */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Data Frequency (seconds)
                </label>
                <input
                  type="number"
                  min="1"
                  max="3600"
                  value={configForm.dataFrequency}
                  onChange={(e) => setConfigForm(prev => ({ 
                    ...prev, 
                    dataFrequency: parseInt(e.target.value) 
                  }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500"
                />
              </div>

              {/* Anomaly Probability */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Anomaly Probability (0-1)
                </label>
                <input
                  type="number"
                  min="0"
                  max="1"
                  step="0.01"
                  value={configForm.anomalyProbability}
                  onChange={(e) => setConfigForm(prev => ({ 
                    ...prev, 
                    anomalyProbability: parseFloat(e.target.value) 
                  }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500"
                />
              </div>
            </div>

            <div className="flex items-center justify-end space-x-3 mt-6">
              <Button
                variant="ghost"
                onClick={() => setShowConfigForm(false)}
              >
                Cancel
              </Button>
              <Button onClick={handleStartSimulation}>
                <Play className="w-4 h-4 mr-2" />
                Start Simulation
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                <span className="text-red-800 font-medium">Simulation Error</span>
              </div>
              <Button variant="ghost" size="sm" onClick={clearError}>
                Dismiss
              </Button>
            </div>
            <p className="text-red-700 text-sm mt-1">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* No Simulations State */}
      {!isSimulating && activeSimulations.size === 0 && (
        <Card>
          <CardContent className="p-8 text-center">
            <Activity className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Active Simulations</h3>
            <p className="text-gray-600 mb-4">
              Start a simulation to generate test data from medical devices
            </p>
            <Button onClick={() => setShowConfigForm(true)}>
              <Play className="w-4 h-4 mr-2" />
              Start Simulation
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default DeviceSimulator;
