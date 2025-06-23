/**
 * Device simulator for HealthConnect AI
 * Simulates various medical devices for testing and demonstration
 */

import type { DeviceType, DeviceData, DeviceSimulation, DeviceScenario } from '@/types/devices';
import type { VitalSigns } from '@/types/health';

export interface SimulationConfig {
  deviceType: DeviceType;
  patientId: string;
  baselineValues: Record<string, number>;
  variability: Record<string, number>;
  anomalyProbability: number;
  dataFrequency: number; // seconds
  duration?: number; // minutes
}

export interface SimulatedReading {
  deviceId: string;
  timestamp: string;
  data: Record<string, any>;
  quality: 'excellent' | 'good' | 'fair' | 'poor';
  anomaly: boolean;
}

class DeviceSimulator {
  private activeSimulations = new Map<string, NodeJS.Timeout>();
  private simulationConfigs = new Map<string, SimulationConfig>();
  private deviceConfigurations: Record<DeviceType, any> = {
    heart_rate_monitor: {
      metrics: ['heart_rate', 'heart_rate_variability'],
      baselineValues: { heart_rate: 72, heart_rate_variability: 45 },
      variability: { heart_rate: 0.1, heart_rate_variability: 0.2 },
      units: { heart_rate: 'bpm', heart_rate_variability: 'ms' },
      ranges: { 
        heart_rate: { min: 40, max: 200 },
        heart_rate_variability: { min: 20, max: 80 }
      }
    },
    blood_pressure_cuff: {
      metrics: ['systolic_pressure', 'diastolic_pressure', 'pulse_pressure', 'mean_arterial_pressure'],
      baselineValues: { 
        systolic_pressure: 120, 
        diastolic_pressure: 80,
        pulse_pressure: 40,
        mean_arterial_pressure: 93
      },
      variability: { 
        systolic_pressure: 0.08, 
        diastolic_pressure: 0.1,
        pulse_pressure: 0.15,
        mean_arterial_pressure: 0.08
      },
      units: { 
        systolic_pressure: 'mmHg', 
        diastolic_pressure: 'mmHg',
        pulse_pressure: 'mmHg',
        mean_arterial_pressure: 'mmHg'
      },
      ranges: {
        systolic_pressure: { min: 70, max: 250 },
        diastolic_pressure: { min: 40, max: 150 },
        pulse_pressure: { min: 20, max: 100 },
        mean_arterial_pressure: { min: 60, max: 180 }
      }
    },
    glucose_meter: {
      metrics: ['glucose_level', 'glucose_trend', 'glucose_rate_of_change'],
      baselineValues: { 
        glucose_level: 95, 
        glucose_trend: 0,
        glucose_rate_of_change: 0
      },
      variability: { 
        glucose_level: 0.15, 
        glucose_trend: 0.3,
        glucose_rate_of_change: 0.5
      },
      units: { 
        glucose_level: 'mg/dL', 
        glucose_trend: '',
        glucose_rate_of_change: 'mg/dL/min'
      },
      ranges: {
        glucose_level: { min: 40, max: 400 },
        glucose_trend: { min: -3, max: 3 },
        glucose_rate_of_change: { min: -5, max: 5 }
      }
    },
    temperature_sensor: {
      metrics: ['core_temperature', 'skin_temperature', 'ambient_temperature'],
      baselineValues: { 
        core_temperature: 37.0, 
        skin_temperature: 33.5,
        ambient_temperature: 22.0
      },
      variability: { 
        core_temperature: 0.02, 
        skin_temperature: 0.05,
        ambient_temperature: 0.1
      },
      units: { 
        core_temperature: '°C', 
        skin_temperature: '°C',
        ambient_temperature: '°C'
      },
      ranges: {
        core_temperature: { min: 35.0, max: 42.0 },
        skin_temperature: { min: 25.0, max: 40.0 },
        ambient_temperature: { min: 15.0, max: 35.0 }
      }
    },
    pulse_oximeter: {
      metrics: ['oxygen_saturation', 'pulse_rate', 'perfusion_index', 'pleth_variability_index'],
      baselineValues: { 
        oxygen_saturation: 98, 
        pulse_rate: 72,
        perfusion_index: 8.5,
        pleth_variability_index: 15
      },
      variability: { 
        oxygen_saturation: 0.02, 
        pulse_rate: 0.1,
        perfusion_index: 0.2,
        pleth_variability_index: 0.3
      },
      units: { 
        oxygen_saturation: '%', 
        pulse_rate: 'bpm',
        perfusion_index: '%',
        pleth_variability_index: '%'
      },
      ranges: {
        oxygen_saturation: { min: 70, max: 100 },
        pulse_rate: { min: 40, max: 200 },
        perfusion_index: { min: 0.5, max: 20 },
        pleth_variability_index: { min: 5, max: 50 }
      }
    },
    activity_tracker: {
      metrics: ['steps', 'calories_burned', 'distance', 'active_minutes', 'sleep_quality', 'stress_level'],
      baselineValues: { 
        steps: 8000, 
        calories_burned: 2200,
        distance: 6.4,
        active_minutes: 45,
        sleep_quality: 85,
        stress_level: 25
      },
      variability: { 
        steps: 0.3, 
        calories_burned: 0.2,
        distance: 0.3,
        active_minutes: 0.4,
        sleep_quality: 0.15,
        stress_level: 0.4
      },
      units: { 
        steps: 'steps', 
        calories_burned: 'kcal',
        distance: 'km',
        active_minutes: 'min',
        sleep_quality: '%',
        stress_level: '%'
      },
      ranges: {
        steps: { min: 0, max: 30000 },
        calories_burned: { min: 1200, max: 5000 },
        distance: { min: 0, max: 50 },
        active_minutes: { min: 0, max: 300 },
        sleep_quality: { min: 0, max: 100 },
        stress_level: { min: 0, max: 100 }
      }
    },
    ecg_monitor: {
      metrics: ['heart_rhythm', 'rr_interval', 'qt_interval', 'pr_interval', 'qrs_duration'],
      baselineValues: { 
        heart_rhythm: 1, // 1 = normal sinus rhythm
        rr_interval: 833,
        qt_interval: 400,
        pr_interval: 160,
        qrs_duration: 90
      },
      variability: { 
        heart_rhythm: 0, // Rhythm changes are scenario-based
        rr_interval: 0.1,
        qt_interval: 0.05,
        pr_interval: 0.08,
        qrs_duration: 0.1
      },
      units: { 
        heart_rhythm: '', 
        rr_interval: 'ms',
        qt_interval: 'ms',
        pr_interval: 'ms',
        qrs_duration: 'ms'
      },
      ranges: {
        heart_rhythm: { min: 1, max: 10 },
        rr_interval: { min: 300, max: 2000 },
        qt_interval: { min: 300, max: 500 },
        pr_interval: { min: 120, max: 220 },
        qrs_duration: { min: 70, max: 120 }
      }
    },
    respiratory_monitor: {
      metrics: ['respiratory_rate', 'tidal_volume', 'minute_ventilation', 'breathing_pattern'],
      baselineValues: { 
        respiratory_rate: 16, 
        tidal_volume: 500,
        minute_ventilation: 8000,
        breathing_pattern: 1 // 1 = regular
      },
      variability: { 
        respiratory_rate: 0.1, 
        tidal_volume: 0.15,
        minute_ventilation: 0.2,
        breathing_pattern: 0
      },
      units: { 
        respiratory_rate: '/min', 
        tidal_volume: 'mL',
        minute_ventilation: 'mL/min',
        breathing_pattern: ''
      },
      ranges: {
        respiratory_rate: { min: 8, max: 40 },
        tidal_volume: { min: 300, max: 800 },
        minute_ventilation: { min: 4000, max: 15000 },
        breathing_pattern: { min: 1, max: 5 }
      }
    }
  };

  /**
   * Start device simulation
   */
  startSimulation(config: SimulationConfig): string {
    const simulationId = `${config.deviceType}_${config.patientId}_${Date.now()}`;
    const deviceId = `${config.deviceType}_${Math.random().toString(36).substr(2, 9)}`;
    
    this.simulationConfigs.set(simulationId, {
      ...config,
      baselineValues: {
        ...this.deviceConfigurations[config.deviceType].baselineValues,
        ...config.baselineValues
      },
      variability: {
        ...this.deviceConfigurations[config.deviceType].variability,
        ...config.variability
      }
    });

    const interval = setInterval(() => {
      const reading = this.generateReading(simulationId, deviceId);
      this.onDataGenerated?.(reading);
    }, config.dataFrequency * 1000);

    this.activeSimulations.set(simulationId, interval);

    // Auto-stop simulation if duration is specified
    if (config.duration) {
      setTimeout(() => {
        this.stopSimulation(simulationId);
      }, config.duration * 60 * 1000);
    }

    return simulationId;
  }

  /**
   * Stop device simulation
   */
  stopSimulation(simulationId: string): void {
    const interval = this.activeSimulations.get(simulationId);
    if (interval) {
      clearInterval(interval);
      this.activeSimulations.delete(simulationId);
      this.simulationConfigs.delete(simulationId);
    }
  }

  /**
   * Stop all simulations
   */
  stopAllSimulations(): void {
    this.activeSimulations.forEach((interval, simulationId) => {
      clearInterval(interval);
    });
    this.activeSimulations.clear();
    this.simulationConfigs.clear();
  }

  /**
   * Generate simulated reading
   */
  private generateReading(simulationId: string, deviceId: string): SimulatedReading {
    const config = this.simulationConfigs.get(simulationId);
    if (!config) {
      throw new Error(`Simulation config not found for ${simulationId}`);
    }

    const deviceConfig = this.deviceConfigurations[config.deviceType];
    const data: Record<string, any> = {};
    let anomaly = false;
    let quality: 'excellent' | 'good' | 'fair' | 'poor' = 'excellent';

    // Generate data for each metric
    deviceConfig.metrics.forEach((metric: string) => {
      const baseline = config.baselineValues[metric] || deviceConfig.baselineValues[metric];
      const variability = config.variability[metric] || deviceConfig.variability[metric];
      const range = deviceConfig.ranges[metric];

      // Check for anomaly
      const isAnomalous = Math.random() < config.anomalyProbability;
      if (isAnomalous) {
        anomaly = true;
        quality = 'fair';
      }

      let value: number;
      if (isAnomalous) {
        // Generate anomalous value
        if (Math.random() < 0.5) {
          // High anomaly
          value = baseline * (1 + variability * 3 + Math.random() * 0.5);
        } else {
          // Low anomaly
          value = baseline * (1 - variability * 3 - Math.random() * 0.3);
        }
      } else {
        // Normal variation
        const variation = (Math.random() - 0.5) * 2 * variability;
        value = baseline * (1 + variation);
      }

      // Ensure value is within possible range
      value = Math.max(range.min, Math.min(range.max, value));

      // Round to appropriate decimal places
      if (metric.includes('temperature')) {
        value = Math.round(value * 10) / 10;
      } else if (metric.includes('percentage') || metric.includes('saturation')) {
        value = Math.round(value);
      } else {
        value = Math.round(value);
      }

      data[metric] = value;
    });

    // Add device-specific processing
    this.processDeviceSpecificData(config.deviceType, data);

    // Simulate quality degradation
    const qualityRandom = Math.random();
    if (qualityRandom < 0.05) {
      quality = 'poor';
    } else if (qualityRandom < 0.15) {
      quality = 'fair';
    } else if (qualityRandom < 0.3) {
      quality = 'good';
    }

    return {
      deviceId,
      timestamp: new Date().toISOString(),
      data,
      quality,
      anomaly
    };
  }

  /**
   * Process device-specific data relationships
   */
  private processDeviceSpecificData(deviceType: DeviceType, data: Record<string, any>): void {
    switch (deviceType) {
      case 'blood_pressure_cuff':
        // Ensure physiological relationships
        if (data.systolic_pressure && data.diastolic_pressure) {
          // Ensure systolic > diastolic
          if (data.systolic_pressure <= data.diastolic_pressure) {
            data.systolic_pressure = data.diastolic_pressure + 20 + Math.random() * 30;
          }
          
          // Calculate pulse pressure
          data.pulse_pressure = data.systolic_pressure - data.diastolic_pressure;
          
          // Calculate mean arterial pressure
          data.mean_arterial_pressure = Math.round(
            data.diastolic_pressure + (data.pulse_pressure / 3)
          );
        }
        break;

      case 'glucose_meter':
        // Add glucose trend based on current level
        if (data.glucose_level) {
          if (data.glucose_level > 180) {
            data.glucose_trend = Math.random() < 0.7 ? -1 : 0; // Likely decreasing
          } else if (data.glucose_level < 70) {
            data.glucose_trend = Math.random() < 0.7 ? 1 : 0; // Likely increasing
          } else {
            data.glucose_trend = Math.floor(Math.random() * 3) - 1; // -1, 0, or 1
          }
          
          // Calculate rate of change
          data.glucose_rate_of_change = data.glucose_trend * (0.5 + Math.random() * 2);
        }
        break;

      case 'pulse_oximeter':
        // Ensure heart rate consistency with pulse rate
        if (data.pulse_rate) {
          data.pulse_rate = data.pulse_rate || data.heart_rate;
        }
        break;

      case 'ecg_monitor':
        // Calculate intervals based on heart rate
        if (data.rr_interval) {
          const heartRate = Math.round(60000 / data.rr_interval);
          
          // Adjust QT interval based on heart rate (QTc)
          const qtc = data.qt_interval / Math.sqrt(data.rr_interval / 1000);
          if (qtc > 440) {
            data.qt_interval = Math.round(440 * Math.sqrt(data.rr_interval / 1000));
          }
        }
        break;

      case 'respiratory_monitor':
        // Calculate minute ventilation
        if (data.respiratory_rate && data.tidal_volume) {
          data.minute_ventilation = data.respiratory_rate * data.tidal_volume;
        }
        break;
    }
  }

  /**
   * Create predefined simulation scenarios
   */
  createScenario(scenarioType: string, patientId: string): DeviceScenario {
    const scenarios: Record<string, Partial<DeviceScenario>> = {
      'hypertensive_crisis': {
        name: 'Hypertensive Crisis',
        description: 'Simulates severe high blood pressure episode',
        duration: 30,
        triggers: [
          {
            condition: 'time > 5',
            action: 'increase_bp',
            parameters: { systolic: 200, diastolic: 120 }
          }
        ],
        expectedOutcomes: ['Emergency alert triggered', 'Provider notification sent']
      },
      'hypoglycemic_episode': {
        name: 'Hypoglycemic Episode',
        description: 'Simulates low blood sugar event',
        duration: 45,
        triggers: [
          {
            condition: 'time > 10',
            action: 'decrease_glucose',
            parameters: { glucose_level: 55 }
          }
        ],
        expectedOutcomes: ['Low glucose alert', 'Patient notification']
      },
      'cardiac_arrhythmia': {
        name: 'Cardiac Arrhythmia',
        description: 'Simulates irregular heart rhythm',
        duration: 20,
        triggers: [
          {
            condition: 'time > 3',
            action: 'irregular_rhythm',
            parameters: { heart_rate_variability: 80 }
          }
        ],
        expectedOutcomes: ['Arrhythmia detection', 'ECG analysis triggered']
      },
      'respiratory_distress': {
        name: 'Respiratory Distress',
        description: 'Simulates breathing difficulties',
        duration: 25,
        triggers: [
          {
            condition: 'time > 5',
            action: 'respiratory_changes',
            parameters: { respiratory_rate: 35, oxygen_saturation: 88 }
          }
        ],
        expectedOutcomes: ['Respiratory alert', 'Emergency protocol activated']
      }
    };

    const scenario = scenarios[scenarioType];
    if (!scenario) {
      throw new Error(`Unknown scenario type: ${scenarioType}`);
    }

    return {
      id: `scenario_${scenarioType}_${Date.now()}`,
      name: scenario.name!,
      description: scenario.description!,
      duration: scenario.duration!,
      triggers: scenario.triggers!,
      expectedOutcomes: scenario.expectedOutcomes!,
      isActive: false
    };
  }

  /**
   * Get active simulations
   */
  getActiveSimulations(): string[] {
    return Array.from(this.activeSimulations.keys());
  }

  /**
   * Get simulation status
   */
  getSimulationStatus(simulationId: string): {
    active: boolean;
    config?: SimulationConfig;
    duration?: number;
  } {
    const active = this.activeSimulations.has(simulationId);
    const config = this.simulationConfigs.get(simulationId);
    
    return {
      active,
      config,
      duration: config?.duration
    };
  }

  /**
   * Event handler for generated data
   */
  onDataGenerated?: (reading: SimulatedReading) => void;

  /**
   * Set data generation callback
   */
  setDataCallback(callback: (reading: SimulatedReading) => void): void {
    this.onDataGenerated = callback;
  }

  /**
   * Generate batch of historical data
   */
  generateHistoricalData(
    deviceType: DeviceType,
    patientId: string,
    startDate: Date,
    endDate: Date,
    intervalMinutes: number = 15
  ): SimulatedReading[] {
    const readings: SimulatedReading[] = [];
    const deviceId = `${deviceType}_${Math.random().toString(36).substr(2, 9)}`;
    const config = this.deviceConfigurations[deviceType];
    
    let currentTime = new Date(startDate);
    
    while (currentTime <= endDate) {
      const data: Record<string, any> = {};
      
      config.metrics.forEach((metric: string) => {
        const baseline = config.baselineValues[metric];
        const variability = config.variability[metric];
        const range = config.ranges[metric];
        
        const variation = (Math.random() - 0.5) * 2 * variability;
        let value = baseline * (1 + variation);
        
        // Ensure value is within range
        value = Math.max(range.min, Math.min(range.max, value));
        
        // Round appropriately
        if (metric.includes('temperature')) {
          value = Math.round(value * 10) / 10;
        } else {
          value = Math.round(value);
        }
        
        data[metric] = value;
      });
      
      this.processDeviceSpecificData(deviceType, data);
      
      readings.push({
        deviceId,
        timestamp: currentTime.toISOString(),
        data,
        quality: 'good',
        anomaly: Math.random() < 0.02 // 2% chance of anomaly
      });
      
      currentTime = new Date(currentTime.getTime() + intervalMinutes * 60 * 1000);
    }
    
    return readings;
  }
}

// Create singleton instance
export const deviceSimulator = new DeviceSimulator();

// Utility functions
export const startDeviceSimulation = (config: SimulationConfig): string => {
  return deviceSimulator.startSimulation(config);
};

export const stopDeviceSimulation = (simulationId: string): void => {
  deviceSimulator.stopSimulation(simulationId);
};

export const createSimulationScenario = (scenarioType: string, patientId: string): DeviceScenario => {
  return deviceSimulator.createScenario(scenarioType, patientId);
};

export default deviceSimulator;
