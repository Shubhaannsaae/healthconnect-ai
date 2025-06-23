/**
 * Custom React hook for device simulation functionality
 * Provides IoT device simulation capabilities for HealthConnect AI
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useAuthStore } from '@/store/authStore';
import { useDeviceStore } from '@/store/deviceStore';
import { deviceSimulator, startDeviceSimulation, stopDeviceSimulation } from '@/lib/device-simulator';
import type { DeviceType, DeviceSimulation, SimulatedReading } from '@/types/devices';

interface UseDeviceSimulatorOptions {
  patientId?: string;
  autoStart?: boolean;
  onDataGenerated?: (reading: SimulatedReading) => void;
  onError?: (error: Error) => void;
}

interface SimulationConfig {
  deviceType: DeviceType;
  patientId: string;
  baselineValues: Record<string, number>;
  variability: Record<string, number>;
  anomalyProbability: number;
  dataFrequency: number;
  duration?: number;
}

interface UseDeviceSimulatorReturn {
  // State
  activeSimulations: Map<string, DeviceSimulation>;
  simulatedData: Map<string, SimulatedReading[]>;
  isSimulating: boolean;
  error: string | null;
  
  // Actions
  startSimulation: (config: SimulationConfig) => Promise<string>;
  stopSimulation: (simulationId: string) => Promise<void>;
  stopAllSimulations: () => Promise<void>;
  createScenario: (scenarioType: string) => any;
  generateHistoricalData: (deviceType: DeviceType, startDate: Date, endDate: Date, intervalMinutes?: number) => SimulatedReading[];
  
  // Utilities
  getSimulationStatus: (simulationId: string) => any;
  getAvailableDeviceTypes: () => DeviceType[];
  getDeviceConfiguration: (deviceType: DeviceType) => any;
  clearError: () => void;
}

export const useDeviceSimulator = (options: UseDeviceSimulatorOptions = {}): UseDeviceSimulatorReturn => {
  const { userAttributes } = useAuthStore();
  const { 
    activeSimulations,
    startSimulation: storeStartSimulation,
    stopSimulation: storeStopSimulation,
    clearError: storeClearError
  } = useDeviceStore();

  const [simulatedData, setSimulatedData] = useState<Map<string, SimulatedReading[]>>(new Map());
  const [error, setError] = useState<string | null>(null);
  const dataCallbackRef = useRef<((reading: SimulatedReading) => void) | null>(null);

  // Determine patient ID
  const patientId = options.patientId || userAttributes?.sub || '';

  // Set up data callback
  useEffect(() => {
    dataCallbackRef.current = (reading: SimulatedReading) => {
      // Add to local state
      setSimulatedData(prev => {
        const deviceData = prev.get(reading.deviceId) || [];
        const newData = new Map(prev);
        newData.set(reading.deviceId, [reading, ...deviceData.slice(0, 99)]); // Keep last 100 readings
        return newData;
      });

      // Call user callback
      options.onDataGenerated?.(reading);
    };

    deviceSimulator.setDataCallback(dataCallbackRef.current);
  }, [options.onDataGenerated]);

  // Start simulation
  const startSimulation = useCallback(async (config: SimulationConfig): Promise<string> => {
    try {
      setError(null);
      const simulationId = await storeStartSimulation(config);
      return simulationId;
    } catch (error) {
      const errorMessage = (error as Error).message;
      setError(errorMessage);
      options.onError?.(error as Error);
      throw error;
    }
  }, [storeStartSimulation, options.onError]);

  // Stop simulation
  const stopSimulation = useCallback(async (simulationId: string): Promise<void> => {
    try {
      await storeStopSimulation(simulationId);
      setError(null);
    } catch (error) {
      const errorMessage = (error as Error).message;
      setError(errorMessage);
      options.onError?.(error as Error);
      throw error;
    }
  }, [storeStopSimulation, options.onError]);

  // Stop all simulations
  const stopAllSimulations = useCallback(async (): Promise<void> => {
    try {
      const simulationIds = Array.from(activeSimulations.keys());
      await Promise.all(simulationIds.map(id => stopSimulation(id)));
      setSimulatedData(new Map());
      setError(null);
    } catch (error) {
      const errorMessage = (error as Error).message;
      setError(errorMessage);
      options.onError?.(error as Error);
      throw error;
    }
  }, [activeSimulations, stopSimulation, options.onError]);

  // Create scenario
  const createScenario = useCallback((scenarioType: string) => {
    try {
      return deviceSimulator.createScenario(scenarioType, patientId);
    } catch (error) {
      const errorMessage = (error as Error).message;
      setError(errorMessage);
      options.onError?.(error as Error);
      throw error;
    }
  }, [patientId, options.onError]);

  // Generate historical data
  const generateHistoricalData = useCallback((
    deviceType: DeviceType,
    startDate: Date,
    endDate: Date,
    intervalMinutes: number = 15
  ): SimulatedReading[] => {
    try {
      return deviceSimulator.generateHistoricalData(
        deviceType,
        patientId,
        startDate,
        endDate,
        intervalMinutes
      );
    } catch (error) {
      const errorMessage = (error as Error).message;
      setError(errorMessage);
      options.onError?.(error as Error);
      throw error;
    }
  }, [patientId, options.onError]);

  // Get simulation status
  const getSimulationStatus = useCallback((simulationId: string) => {
    return deviceSimulator.getSimulationStatus(simulationId);
  }, []);

  // Get available device types
  const getAvailableDeviceTypes = useCallback((): DeviceType[] => {
    return [
      'heart_rate_monitor',
      'blood_pressure_cuff',
      'glucose_meter',
      'temperature_sensor',
      'pulse_oximeter',
      'activity_tracker',
      'ecg_monitor',
      'respiratory_monitor'
    ];
  }, []);

  // Get device configuration
  const getDeviceConfiguration = useCallback((deviceType: DeviceType) => {
    // Return default configuration for device type
    const configurations = {
      heart_rate_monitor: {
        baselineValues: { heart_rate: 72, heart_rate_variability: 45 },
        variability: { heart_rate: 0.1, heart_rate_variability: 0.2 },
        anomalyProbability: 0.05,
        dataFrequency: 10
      },
      blood_pressure_cuff: {
        baselineValues: { systolic_pressure: 120, diastolic_pressure: 80 },
        variability: { systolic_pressure: 0.08, diastolic_pressure: 0.1 },
        anomalyProbability: 0.03,
        dataFrequency: 300
      },
      glucose_meter: {
        baselineValues: { glucose_level: 95 },
        variability: { glucose_level: 0.15 },
        anomalyProbability: 0.08,
        dataFrequency: 900
      },
      temperature_sensor: {
        baselineValues: { core_temperature: 37.0 },
        variability: { core_temperature: 0.02 },
        anomalyProbability: 0.02,
        dataFrequency: 60
      },
      pulse_oximeter: {
        baselineValues: { oxygen_saturation: 98, pulse_rate: 72 },
        variability: { oxygen_saturation: 0.02, pulse_rate: 0.1 },
        anomalyProbability: 0.04,
        dataFrequency: 30
      },
      activity_tracker: {
        baselineValues: { steps: 8000, calories_burned: 2200 },
        variability: { steps: 0.3, calories_burned: 0.2 },
        anomalyProbability: 0.01,
        dataFrequency: 3600
      },
      ecg_monitor: {
        baselineValues: { heart_rhythm: 1, rr_interval: 833 },
        variability: { rr_interval: 0.1 },
        anomalyProbability: 0.06,
        dataFrequency: 1
      },
      respiratory_monitor: {
        baselineValues: { respiratory_rate: 16, tidal_volume: 500 },
        variability: { respiratory_rate: 0.1, tidal_volume: 0.15 },
        anomalyProbability: 0.03,
        dataFrequency: 15
      }
    };

    return configurations[deviceType] || configurations.heart_rate_monitor;
  }, []);

  // Clear error
  const clearError = useCallback(() => {
    setError(null);
    storeClearError();
  }, [storeClearError]);

  // Computed values
  const isSimulating = activeSimulations.size > 0;

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopAllSimulations().catch(console.error);
    };
  }, []);

  return {
    // State
    activeSimulations,
    simulatedData,
    isSimulating,
    error,
    
    // Actions
    startSimulation,
    stopSimulation,
    stopAllSimulations,
    createScenario,
    generateHistoricalData,
    
    // Utilities
    getSimulationStatus,
    getAvailableDeviceTypes,
    getDeviceConfiguration,
    clearError
  };
};

export default useDeviceSimulator;
