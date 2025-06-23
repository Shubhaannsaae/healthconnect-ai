/**
 * Device state management for HealthConnect AI
 * Managing IoT devices, simulations, and device data
 */

import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { 
  DeviceInfo, 
  DeviceStatus, 
  DeviceData, 
  DeviceSimulation, 
  DeviceConfiguration,
  DeviceAlert,
  DeviceAnalytics,
  DeviceFilter
} from '@/types/devices';
import { apiClient } from '@/lib/aws-config';
import { deviceSimulator, startDeviceSimulation, stopDeviceSimulation } from '@/lib/device-simulator';

interface DeviceStore {
  // State
  devices: DeviceInfo[];
  deviceStatuses: Map<string, DeviceStatus>;
  deviceData: Map<string, DeviceData[]>;
  activeSimulations: Map<string, DeviceSimulation>;
  deviceAlerts: DeviceAlert[];
  deviceAnalytics: Map<string, DeviceAnalytics>;
  selectedDevice: DeviceInfo | null;
  loading: boolean;
  error: string | null;
  lastUpdated: string | null;

  // Actions
  registerDevice: (deviceInfo: DeviceInfo, patientId: string) => Promise<void>;
  unregisterDevice: (deviceId: string) => Promise<void>;
  updateDeviceConfiguration: (deviceId: string, config: Partial<DeviceConfiguration>) => Promise<void>;
  fetchDevices: (patientId?: string, filters?: DeviceFilter) => Promise<void>;
  fetchDeviceStatus: (deviceId: string) => Promise<void>;
  fetchDeviceData: (deviceId: string, timeframe?: string) => Promise<void>;
  sendDeviceCommand: (deviceId: string, command: string, parameters?: any) => Promise<void>;
  startSimulation: (config: any) => Promise<string>;
  stopSimulation: (simulationId: string) => Promise<void>;
  addDeviceAlert: (alert: DeviceAlert) => void;
  acknowledgeDeviceAlert: (alertId: string) => Promise<void>;
  resolveDeviceAlert: (alertId: string) => Promise<void>;
  fetchDeviceAnalytics: (deviceId: string, period: any) => Promise<void>;
  setSelectedDevice: (device: DeviceInfo | null) => void;
  clearError: () => void;
  reset: () => void;

  // Computed values
  getOnlineDevices: () => DeviceInfo[];
  getOfflineDevices: () => DeviceInfo[];
  getDevicesByType: (deviceType: string) => DeviceInfo[];
  getActiveAlerts: () => DeviceAlert[];
  getCriticalAlerts: () => DeviceAlert[];
  getDeviceHealth: (deviceId: string) => 'healthy' | 'warning' | 'critical' | 'unknown';
}

export const useDeviceStore = create<DeviceStore>()(
  subscribeWithSelector(
    persist(
      (set, get) => ({
        // Initial state
        devices: [],
        deviceStatuses: new Map(),
        deviceData: new Map(),
        activeSimulations: new Map(),
        deviceAlerts: [],
        deviceAnalytics: new Map(),
        selectedDevice: null,
        loading: false,
        error: null,
        lastUpdated: null,

        // Register new device
        registerDevice: async (deviceInfo: DeviceInfo, patientId: string) => {
          set({ loading: true, error: null });
          
          try {
            const response = await apiClient.post({
              apiName: 'HealthConnectAPI',
              path: '/devices/register',
              options: {
                body: {
                  deviceInfo,
                  patientId,
                  registrationDate: new Date().toISOString()
                }
              }
            });

            if (response.success) {
              set(state => ({
                devices: [...state.devices, response.data],
                loading: false,
                lastUpdated: new Date().toISOString()
              }));
            } else {
              throw new Error(response.error?.message || 'Failed to register device');
            }
          } catch (error: any) {
            set({ loading: false, error: error.message });
            throw error;
          }
        },

        // Unregister device
        unregisterDevice: async (deviceId: string) => {
          set({ loading: true, error: null });
          
          try {
            const response = await apiClient.del({
              apiName: 'HealthConnectAPI',
              path: `/devices/${deviceId}`
            });

            if (response.success) {
              set(state => ({
                devices: state.devices.filter(device => device.id !== deviceId),
                loading: false,
                lastUpdated: new Date().toISOString()
              }));

              // Clean up related data
              const { deviceStatuses, deviceData, deviceAnalytics } = get();
              deviceStatuses.delete(deviceId);
              deviceData.delete(deviceId);
              deviceAnalytics.delete(deviceId);
              
              set({ deviceStatuses, deviceData, deviceAnalytics });
            } else {
              throw new Error(response.error?.message || 'Failed to unregister device');
            }
          } catch (error: any) {
            set({ loading: false, error: error.message });
            throw error;
          }
        },

        // Update device configuration
        updateDeviceConfiguration: async (deviceId: string, config: Partial<DeviceConfiguration>) => {
          set({ loading: true, error: null });
          
          try {
            const response = await apiClient.put({
              apiName: 'HealthConnectAPI',
              path: `/devices/${deviceId}/configuration`,
              options: {
                body: config
              }
            });

            if (response.success) {
              set({ loading: false, lastUpdated: new Date().toISOString() });
            } else {
              throw new Error(response.error?.message || 'Failed to update device configuration');
            }
          } catch (error: any) {
            set({ loading: false, error: error.message });
            throw error;
          }
        },

        // Fetch devices
        fetchDevices: async (patientId?: string, filters?: DeviceFilter) => {
          set({ loading: true, error: null });
          
          try {
            const queryParams = new URLSearchParams();
            if (patientId) queryParams.append('patientId', patientId);
            if (filters) {
              Object.entries(filters).forEach(([key, value]) => {
                if (value !== undefined && value !== null) {
                  if (Array.isArray(value)) {
                    value.forEach(v => queryParams.append(key, v));
                  } else {
                    queryParams.append(key, String(value));
                  }
                }
              });
            }

            const response = await apiClient.get({
              apiName: 'HealthConnectAPI',
              path: `/devices?${queryParams.toString()}`
            });

            if (response.success) {
              set({
                devices: response.data || [],
                loading: false,
                lastUpdated: new Date().toISOString()
              });
            } else {
              throw new Error(response.error?.message || 'Failed to fetch devices');
            }
          } catch (error: any) {
            set({ loading: false, error: error.message });
            throw error;
          }
        },

        // Fetch device status
        fetchDeviceStatus: async (deviceId: string) => {
          try {
            const response = await apiClient.get({
              apiName: 'HealthConnectAPI',
              path: `/devices/${deviceId}/status`
            });

            if (response.success) {
              const { deviceStatuses } = get();
              deviceStatuses.set(deviceId, response.data);
              set({ 
                deviceStatuses: new Map(deviceStatuses),
                lastUpdated: new Date().toISOString()
              });
            }
          } catch (error: any) {
            console.error(`Failed to fetch status for device ${deviceId}:`, error);
          }
        },

        // Fetch device data
        fetchDeviceData: async (deviceId: string, timeframe: string = '24h') => {
          set({ loading: true, error: null });
          
          try {
            const response = await apiClient.get({
              apiName: 'HealthConnectAPI',
              path: `/devices/${deviceId}/data?timeframe=${timeframe}`
            });

            if (response.success) {
              const { deviceData } = get();
              deviceData.set(deviceId, response.data || []);
              set({ 
                deviceData: new Map(deviceData),
                loading: false,
                lastUpdated: new Date().toISOString()
              });
            } else {
              throw new Error(response.error?.message || 'Failed to fetch device data');
            }
          } catch (error: any) {
            set({ loading: false, error: error.message });
            throw error;
          }
        },

        // Send device command
        sendDeviceCommand: async (deviceId: string, command: string, parameters?: any) => {
          set({ loading: true, error: null });
          
          try {
            const response = await apiClient.post({
              apiName: 'HealthConnectAPI',
              path: `/devices/${deviceId}/commands`,
              options: {
                body: {
                  command,
                  parameters,
                  timestamp: new Date().toISOString()
                }
              }
            });

            if (response.success) {
              set({ loading: false });
            } else {
              throw new Error(response.error?.message || 'Failed to send device command');
            }
          } catch (error: any) {
            set({ loading: false, error: error.message });
            throw error;
          }
        },

        // Start device simulation
        startSimulation: async (config: any) => {
          set({ loading: true, error: null });
          
          try {
            // Set up data callback
            deviceSimulator.setDataCallback((reading) => {
              // Handle simulated device data
              const { deviceData } = get();
              const existingData = deviceData.get(reading.deviceId) || [];
              deviceData.set(reading.deviceId, [reading as any, ...existingData.slice(0, 99)]);
              set({ deviceData: new Map(deviceData) });
            });

            const simulationId = startDeviceSimulation(config);
            
            const simulation: DeviceSimulation = {
              id: simulationId,
              deviceType: config.deviceType,
              patientId: config.patientId,
              isActive: true,
              simulationParameters: config,
              scenarios: [],
              createdAt: new Date().toISOString(),
              lastUpdate: new Date().toISOString()
            };

            const { activeSimulations } = get();
            activeSimulations.set(simulationId, simulation);
            
            set({ 
              activeSimulations: new Map(activeSimulations),
              loading: false,
              lastUpdated: new Date().toISOString()
            });

            return simulationId;
          } catch (error: any) {
            set({ loading: false, error: error.message });
            throw error;
          }
        },

        // Stop device simulation
        stopSimulation: async (simulationId: string) => {
          try {
            stopDeviceSimulation(simulationId);
            
            const { activeSimulations } = get();
            activeSimulations.delete(simulationId);
            
            set({ 
              activeSimulations: new Map(activeSimulations),
              lastUpdated: new Date().toISOString()
            });
          } catch (error: any) {
            set({ error: error.message });
            throw error;
          }
        },

        // Add device alert
        addDeviceAlert: (alert: DeviceAlert) => {
          set(state => ({
            deviceAlerts: [alert, ...state.deviceAlerts],
            lastUpdated: new Date().toISOString()
          }));
        },

        // Acknowledge device alert
        acknowledgeDeviceAlert: async (alertId: string) => {
          set({ loading: true, error: null });
          
          try {
            const response = await apiClient.put({
              apiName: 'HealthConnectAPI',
              path: `/devices/alerts/${alertId}/acknowledge`
            });

            if (response.success) {
              set(state => ({
                deviceAlerts: state.deviceAlerts.map(alert =>
                  alert.id === alertId 
                    ? { ...alert, acknowledged: true, acknowledgedAt: new Date().toISOString() }
                    : alert
                ),
                loading: false
              }));
            } else {
              throw new Error(response.error?.message || 'Failed to acknowledge device alert');
            }
          } catch (error: any) {
            set({ loading: false, error: error.message });
            throw error;
          }
        },

        // Resolve device alert
        resolveDeviceAlert: async (alertId: string) => {
          set({ loading: true, error: null });
          
          try {
            const response = await apiClient.put({
              apiName: 'HealthConnectAPI',
              path: `/devices/alerts/${alertId}/resolve`
            });

            if (response.success) {
              set(state => ({
                deviceAlerts: state.deviceAlerts.map(alert =>
                  alert.id === alertId 
                    ? { ...alert, resolved: true, resolvedAt: new Date().toISOString() }
                    : alert
                ),
                loading: false
              }));
            } else {
              throw new Error(response.error?.message || 'Failed to resolve device alert');
            }
          } catch (error: any) {
            set({ loading: false, error: error.message });
            throw error;
          }
        },

        // Fetch device analytics
        fetchDeviceAnalytics: async (deviceId: string, period: any) => {
          set({ loading: true, error: null });
          
          try {
            const response = await apiClient.get({
              apiName: 'HealthConnectAPI',
              path: `/devices/${deviceId}/analytics?period=${JSON.stringify(period)}`
            });

            if (response.success) {
              const { deviceAnalytics } = get();
              deviceAnalytics.set(deviceId, response.data);
              set({ 
                deviceAnalytics: new Map(deviceAnalytics),
                loading: false,
                lastUpdated: new Date().toISOString()
              });
            } else {
              throw new Error(response.error?.message || 'Failed to fetch device analytics');
            }
          } catch (error: any) {
            set({ loading: false, error: error.message });
            throw error;
          }
        },

        // Set selected device
        setSelectedDevice: (device: DeviceInfo | null) => {
          set({ selectedDevice: device });
        },

        // Clear error
        clearError: () => {
          set({ error: null });
        },

        // Reset store
        reset: () => {
          // Stop all active simulations
          const { activeSimulations } = get();
          activeSimulations.forEach((_, simulationId) => {
            try {
              stopDeviceSimulation(simulationId);
            } catch (error) {
              console.error(`Failed to stop simulation ${simulationId}:`, error);
            }
          });

          set({
            devices: [],
            deviceStatuses: new Map(),
            deviceData: new Map(),
            activeSimulations: new Map(),
            deviceAlerts: [],
            deviceAnalytics: new Map(),
            selectedDevice: null,
            loading: false,
            error: null,
            lastUpdated: null
          });
        },

        // Computed values
        getOnlineDevices: () => {
          const { devices, deviceStatuses } = get();
          return devices.filter(device => {
            const status = deviceStatuses.get(device.id);
            return status?.status === 'online';
          });
        },

        getOfflineDevices: () => {
          const { devices, deviceStatuses } = get();
          return devices.filter(device => {
            const status = deviceStatuses.get(device.id);
            return status?.status === 'offline';
          });
        },

        getDevicesByType: (deviceType: string) => {
          const { devices } = get();
          return devices.filter(device => device.type === deviceType);
        },

        getActiveAlerts: () => {
          const { deviceAlerts } = get();
          return deviceAlerts.filter(alert => !alert.resolved);
        },

        getCriticalAlerts: () => {
          const { deviceAlerts } = get();
          return deviceAlerts.filter(alert => 
            !alert.resolved && (alert.severity === 'critical' || alert.severity === 'high')
          );
        },

        getDeviceHealth: (deviceId: string) => {
          const { deviceStatuses, deviceAlerts } = get();
          const status = deviceStatuses.get(deviceId);
          const deviceAlertsList = deviceAlerts.filter(alert => 
            alert.deviceId === deviceId && !alert.resolved
          );

          if (!status) return 'unknown';

          // Check for critical alerts
          const criticalAlerts = deviceAlertsList.filter(alert => 
            alert.severity === 'critical'
          );
          if (criticalAlerts.length > 0) return 'critical';

          // Check device status
          if (status.status === 'error' || status.status === 'maintenance') {
            return 'critical';
          }

          // Check for warning conditions
          const warningAlerts = deviceAlertsList.filter(alert => 
            alert.severity === 'high' || alert.severity === 'medium'
          );
          if (warningAlerts.length > 0) return 'warning';

          if (status.status === 'low_battery' || status.status === 'offline') {
            return 'warning';
          }

          return 'healthy';
        }
      }),
      {
        name: 'healthconnect-devices',
        storage: createJSONStorage(() => localStorage),
        partialize: (state) => ({
          devices: state.devices,
          selectedDevice: state.selectedDevice,
          lastUpdated: state.lastUpdated
        })
      }
    )
  )
);

export default useDeviceStore;
