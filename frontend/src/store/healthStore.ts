/**
 * Health data state management for HealthConnect AI
 * Managing vital signs, health records, and medical data
 */

import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { 
  VitalSigns, 
  HealthRecord, 
  HealthMetrics, 
  HealthAlert, 
  HealthTrend,
  HealthInsight,
  HealthGoal,
  HealthSummary
} from '@/types/health';
import { apiClient, getApiEndpoint } from '@/lib/aws-config';
import { analyzeVitalSigns, calculateHealthTrends, generateHealthInsights } from '@/lib/health-utils';

interface HealthStore {
  // State
  currentVitalSigns: VitalSigns | null;
  healthRecords: HealthRecord[];
  healthMetrics: HealthMetrics | null;
  healthAlerts: HealthAlert[];
  healthTrends: HealthTrend[];
  healthInsights: HealthInsight[];
  healthGoals: HealthGoal[];
  healthSummary: HealthSummary | null;
  loading: boolean;
  error: string | null;
  lastUpdated: string | null;

  // Actions
  setCurrentVitalSigns: (vitalSigns: VitalSigns) => void;
  addHealthRecord: (record: HealthRecord) => Promise<void>;
  updateHealthRecord: (recordId: string, updates: Partial<HealthRecord>) => Promise<void>;
  deleteHealthRecord: (recordId: string) => Promise<void>;
  fetchHealthRecords: (patientId: string, filters?: any) => Promise<void>;
  fetchVitalSigns: (patientId: string, timeframe?: string) => Promise<void>;
  addHealthAlert: (alert: HealthAlert) => void;
  acknowledgeAlert: (alertId: string) => Promise<void>;
  resolveAlert: (alertId: string) => Promise<void>;
  fetchHealthAlerts: (patientId: string) => Promise<void>;
  updateHealthMetrics: (metrics: HealthMetrics) => void;
  addHealthGoal: (goal: HealthGoal) => Promise<void>;
  updateHealthGoal: (goalId: string, updates: Partial<HealthGoal>) => Promise<void>;
  deleteHealthGoal: (goalId: string) => Promise<void>;
  fetchHealthGoals: (patientId: string) => Promise<void>;
  generateHealthSummary: (patientId: string, period: { start: string; end: string }) => Promise<void>;
  analyzeHealthData: (patientId: string) => Promise<void>;
  clearError: () => void;
  reset: () => void;

  // Computed values
  getLatestVitalSigns: () => VitalSigns | null;
  getActiveAlerts: () => HealthAlert[];
  getCriticalAlerts: () => HealthAlert[];
  getHealthScore: () => number;
  getAbnormalVitals: () => Array<{ parameter: string; value: number; severity: string }>;
}

export const useHealthStore = create<HealthStore>()(
  subscribeWithSelector(
    persist(
      (set, get) => ({
        // Initial state
        currentVitalSigns: null,
        healthRecords: [],
        healthMetrics: null,
        healthAlerts: [],
        healthTrends: [],
        healthInsights: [],
        healthGoals: [],
        healthSummary: null,
        loading: false,
        error: null,
        lastUpdated: null,

        // Set current vital signs
        setCurrentVitalSigns: (vitalSigns: VitalSigns) => {
          set({ 
            currentVitalSigns: vitalSigns,
            lastUpdated: new Date().toISOString()
          });

          // Analyze vital signs for alerts
          const analysis = analyzeVitalSigns(vitalSigns);
          if (analysis.urgentCareNeeded || analysis.overall === 'critical') {
            const alert: HealthAlert = {
              id: `alert_${Date.now()}`,
              patientId: '', // Will be set by calling component
              alertType: 'vital_signs_critical',
              severity: analysis.overall === 'critical' ? 'critical' : 'high',
              title: 'Critical Vital Signs Detected',
              message: `Abnormal vital signs detected: ${analysis.abnormalValues.map(v => v.parameter).join(', ')}`,
              timestamp: new Date().toISOString(),
              acknowledged: false,
              resolved: false,
              actions: [
                {
                  id: 'contact_provider',
                  label: 'Contact Healthcare Provider',
                  action: 'contact_provider',
                  confirmationRequired: false
                },
                {
                  id: 'call_emergency',
                  label: 'Call Emergency Services',
                  action: 'call_emergency',
                  confirmationRequired: true
                }
              ]
            };
            
            get().addHealthAlert(alert);
          }
        },

        // Add health record
        addHealthRecord: async (record: HealthRecord) => {
          set({ loading: true, error: null });
          
          try {
            const response = await apiClient.post({
              apiName: 'HealthConnectAPI',
              path: '/health/records',
              options: {
                body: record
              }
            });

            if (response.success) {
              set(state => ({
                healthRecords: [response.data, ...state.healthRecords],
                loading: false,
                lastUpdated: new Date().toISOString()
              }));
            } else {
              throw new Error(response.error?.message || 'Failed to add health record');
            }
          } catch (error: any) {
            set({ loading: false, error: error.message });
            throw error;
          }
        },

        // Update health record
        updateHealthRecord: async (recordId: string, updates: Partial<HealthRecord>) => {
          set({ loading: true, error: null });
          
          try {
            const response = await apiClient.put({
              apiName: 'HealthConnectAPI',
              path: `/health/records/${recordId}`,
              options: {
                body: updates
              }
            });

            if (response.success) {
              set(state => ({
                healthRecords: state.healthRecords.map(record =>
                  record.id === recordId ? { ...record, ...updates } : record
                ),
                loading: false,
                lastUpdated: new Date().toISOString()
              }));
            } else {
              throw new Error(response.error?.message || 'Failed to update health record');
            }
          } catch (error: any) {
            set({ loading: false, error: error.message });
            throw error;
          }
        },

        // Delete health record
        deleteHealthRecord: async (recordId: string) => {
          set({ loading: true, error: null });
          
          try {
            const response = await apiClient.del({
              apiName: 'HealthConnectAPI',
              path: `/health/records/${recordId}`
            });

            if (response.success) {
              set(state => ({
                healthRecords: state.healthRecords.filter(record => record.id !== recordId),
                loading: false,
                lastUpdated: new Date().toISOString()
              }));
            } else {
              throw new Error(response.error?.message || 'Failed to delete health record');
            }
          } catch (error: any) {
            set({ loading: false, error: error.message });
            throw error;
          }
        },

        // Fetch health records
        fetchHealthRecords: async (patientId: string, filters?: any) => {
          set({ loading: true, error: null });
          
          try {
            const queryParams = new URLSearchParams({
              patientId,
              ...filters
            });

            const response = await apiClient.get({
              apiName: 'HealthConnectAPI',
              path: `/health/records?${queryParams.toString()}`
            });

            if (response.success) {
              set({
                healthRecords: response.data || [],
                loading: false,
                lastUpdated: new Date().toISOString()
              });
            } else {
              throw new Error(response.error?.message || 'Failed to fetch health records');
            }
          } catch (error: any) {
            set({ loading: false, error: error.message });
            throw error;
          }
        },

        // Fetch vital signs
        fetchVitalSigns: async (patientId: string, timeframe: string = '24h') => {
          set({ loading: true, error: null });
          
          try {
            const response = await apiClient.get({
              apiName: 'HealthConnectAPI',
              path: `/health/vital-signs?patientId=${patientId}&timeframe=${timeframe}`
            });

            if (response.success && response.data.length > 0) {
              const latestVitalSigns = response.data[0];
              set({
                currentVitalSigns: latestVitalSigns,
                loading: false,
                lastUpdated: new Date().toISOString()
              });

              // Generate trends if we have multiple data points
              if (response.data.length > 1) {
                const trends = calculateHealthTrends(
                  response.data.map((vs: VitalSigns) => ({
                    timestamp: vs.timestamp,
                    value: vs.heartRate
                  })),
                  timeframe as any
                );
                
                set(state => ({
                  healthTrends: [...state.healthTrends, trends]
                }));
              }
            } else {
              set({ loading: false });
            }
          } catch (error: any) {
            set({ loading: false, error: error.message });
            throw error;
          }
        },

        // Add health alert
        addHealthAlert: (alert: HealthAlert) => {
          set(state => ({
            healthAlerts: [alert, ...state.healthAlerts],
            lastUpdated: new Date().toISOString()
          }));
        },

        // Acknowledge alert
        acknowledgeAlert: async (alertId: string) => {
          set({ loading: true, error: null });
          
          try {
            const response = await apiClient.put({
              apiName: 'HealthConnectAPI',
              path: `/health/alerts/${alertId}/acknowledge`
            });

            if (response.success) {
              set(state => ({
                healthAlerts: state.healthAlerts.map(alert =>
                  alert.id === alertId 
                    ? { 
                        ...alert, 
                        acknowledged: true, 
                        acknowledgedAt: new Date().toISOString() 
                      }
                    : alert
                ),
                loading: false
              }));
            } else {
              throw new Error(response.error?.message || 'Failed to acknowledge alert');
            }
          } catch (error: any) {
            set({ loading: false, error: error.message });
            throw error;
          }
        },

        // Resolve alert
        resolveAlert: async (alertId: string) => {
          set({ loading: true, error: null });
          
          try {
            const response = await apiClient.put({
              apiName: 'HealthConnectAPI',
              path: `/health/alerts/${alertId}/resolve`
            });

            if (response.success) {
              set(state => ({
                healthAlerts: state.healthAlerts.map(alert =>
                  alert.id === alertId 
                    ? { 
                        ...alert, 
                        resolved: true, 
                        resolvedAt: new Date().toISOString() 
                      }
                    : alert
                ),
                loading: false
              }));
            } else {
              throw new Error(response.error?.message || 'Failed to resolve alert');
            }
          } catch (error: any) {
            set({ loading: false, error: error.message });
            throw error;
          }
        },

        // Fetch health alerts
        fetchHealthAlerts: async (patientId: string) => {
          set({ loading: true, error: null });
          
          try {
            const response = await apiClient.get({
              apiName: 'HealthConnectAPI',
              path: `/health/alerts?patientId=${patientId}`
            });

            if (response.success) {
              set({
                healthAlerts: response.data || [],
                loading: false,
                lastUpdated: new Date().toISOString()
              });
            } else {
              throw new Error(response.error?.message || 'Failed to fetch health alerts');
            }
          } catch (error: any) {
            set({ loading: false, error: error.message });
            throw error;
          }
        },

        // Update health metrics
        updateHealthMetrics: (metrics: HealthMetrics) => {
          set({ 
            healthMetrics: metrics,
            lastUpdated: new Date().toISOString()
          });
        },

        // Add health goal
        addHealthGoal: async (goal: HealthGoal) => {
          set({ loading: true, error: null });
          
          try {
            const response = await apiClient.post({
              apiName: 'HealthConnectAPI',
              path: '/health/goals',
              options: {
                body: goal
              }
            });

            if (response.success) {
              set(state => ({
                healthGoals: [response.data, ...state.healthGoals],
                loading: false,
                lastUpdated: new Date().toISOString()
              }));
            } else {
              throw new Error(response.error?.message || 'Failed to add health goal');
            }
          } catch (error: any) {
            set({ loading: false, error: error.message });
            throw error;
          }
        },

        // Update health goal
        updateHealthGoal: async (goalId: string, updates: Partial<HealthGoal>) => {
          set({ loading: true, error: null });
          
          try {
            const response = await apiClient.put({
              apiName: 'HealthConnectAPI',
              path: `/health/goals/${goalId}`,
              options: {
                body: updates
              }
            });

            if (response.success) {
              set(state => ({
                healthGoals: state.healthGoals.map(goal =>
                  goal.id === goalId ? { ...goal, ...updates } : goal
                ),
                loading: false,
                lastUpdated: new Date().toISOString()
              }));
            } else {
              throw new Error(response.error?.message || 'Failed to update health goal');
            }
          } catch (error: any) {
            set({ loading: false, error: error.message });
            throw error;
          }
        },

        // Delete health goal
        deleteHealthGoal: async (goalId: string) => {
          set({ loading: true, error: null });
          
          try {
            const response = await apiClient.del({
              apiName: 'HealthConnectAPI',
              path: `/health/goals/${goalId}`
            });

            if (response.success) {
              set(state => ({
                healthGoals: state.healthGoals.filter(goal => goal.id !== goalId),
                loading: false,
                lastUpdated: new Date().toISOString()
              }));
            } else {
              throw new Error(response.error?.message || 'Failed to delete health goal');
            }
          } catch (error: any) {
            set({ loading: false, error: error.message });
            throw error;
          }
        },

        // Fetch health goals
        fetchHealthGoals: async (patientId: string) => {
          set({ loading: true, error: null });
          
          try {
            const response = await apiClient.get({
              apiName: 'HealthConnectAPI',
              path: `/health/goals?patientId=${patientId}`
            });

            if (response.success) {
              set({
                healthGoals: response.data || [],
                loading: false,
                lastUpdated: new Date().toISOString()
              });
            } else {
              throw new Error(response.error?.message || 'Failed to fetch health goals');
            }
          } catch (error: any) {
            set({ loading: false, error: error.message });
            throw error;
          }
        },

        // Generate health summary
        generateHealthSummary: async (patientId: string, period: { start: string; end: string }) => {
          set({ loading: true, error: null });
          
          try {
            const response = await apiClient.post({
              apiName: 'HealthConnectAPI',
              path: '/health/summary',
              options: {
                body: { patientId, period }
              }
            });

            if (response.success) {
              set({
                healthSummary: response.data,
                loading: false,
                lastUpdated: new Date().toISOString()
              });
            } else {
              throw new Error(response.error?.message || 'Failed to generate health summary');
            }
          } catch (error: any) {
            set({ loading: false, error: error.message });
            throw error;
          }
        },

        // Analyze health data
        analyzeHealthData: async (patientId: string) => {
          set({ loading: true, error: null });
          
          try {
            const { healthRecords } = get();
            const vitalSignsRecords = healthRecords
              .filter(record => record.vitalSigns)
              .map(record => record.vitalSigns!)
              .slice(0, 30); // Last 30 readings

            if (vitalSignsRecords.length > 0) {
              const insights = generateHealthInsights(vitalSignsRecords, '30d');
              
              set(state => ({
                healthInsights: [...insights, ...state.healthInsights.slice(0, 10)], // Keep last 10 insights
                loading: false,
                lastUpdated: new Date().toISOString()
              }));
            } else {
              set({ loading: false });
            }
          } catch (error: any) {
            set({ loading: false, error: error.message });
            throw error;
          }
        },

        // Clear error
        clearError: () => {
          set({ error: null });
        },

        // Reset store
        reset: () => {
          set({
            currentVitalSigns: null,
            healthRecords: [],
            healthMetrics: null,
            healthAlerts: [],
            healthTrends: [],
            healthInsights: [],
            healthGoals: [],
            healthSummary: null,
            loading: false,
            error: null,
            lastUpdated: null
          });
        },

        // Computed values
        getLatestVitalSigns: () => {
          const { currentVitalSigns, healthRecords } = get();
          
          if (currentVitalSigns) {
            return currentVitalSigns;
          }
          
          // Find latest vital signs from health records
          const vitalSignsRecord = healthRecords
            .filter(record => record.vitalSigns)
            .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())[0];
          
          return vitalSignsRecord?.vitalSigns || null;
        },

        getActiveAlerts: () => {
          const { healthAlerts } = get();
          return healthAlerts.filter(alert => !alert.resolved);
        },

        getCriticalAlerts: () => {
          const { healthAlerts } = get();
          return healthAlerts.filter(alert => 
            !alert.resolved && (alert.severity === 'critical' || alert.severity === 'high')
          );
        },

        getHealthScore: () => {
          const { currentVitalSigns } = get();
          if (!currentVitalSigns) return 0;
          
          // Calculate health score based on vital signs
          let score = 100;
          
          // Heart rate scoring
          if (currentVitalSigns.heartRate < 60 || currentVitalSigns.heartRate > 100) {
            score -= 10;
          }
          
          // Blood pressure scoring
          if (currentVitalSigns.bloodPressure.systolic > 140 || currentVitalSigns.bloodPressure.diastolic > 90) {
            score -= 15;
          }
          
          // Temperature scoring
          if (currentVitalSigns.temperature < 36.1 || currentVitalSigns.temperature > 37.2) {
            score -= 10;
          }
          
          // Oxygen saturation scoring
          if (currentVitalSigns.oxygenSaturation < 95) {
            score -= 20;
          }
          
          // Respiratory rate scoring
          if (currentVitalSigns.respiratoryRate < 12 || currentVitalSigns.respiratoryRate > 20) {
            score -= 10;
          }
          
          return Math.max(0, score);
        },

        getAbnormalVitals: () => {
          const { currentVitalSigns } = get();
          if (!currentVitalSigns) return [];
          
          const abnormal: Array<{ parameter: string; value: number; severity: string }> = [];
          
          // Check each vital sign
          if (currentVitalSigns.heartRate < 60 || currentVitalSigns.heartRate > 100) {
            abnormal.push({
              parameter: 'Heart Rate',
              value: currentVitalSigns.heartRate,
              severity: currentVitalSigns.heartRate < 50 || currentVitalSigns.heartRate > 120 ? 'severe' : 'moderate'
            });
          }
          
          if (currentVitalSigns.bloodPressure.systolic > 140 || currentVitalSigns.bloodPressure.diastolic > 90) {
            abnormal.push({
              parameter: 'Blood Pressure',
              value: currentVitalSigns.bloodPressure.systolic,
              severity: currentVitalSigns.bloodPressure.systolic > 180 ? 'severe' : 'moderate'
            });
          }
          
          if (currentVitalSigns.temperature < 36.1 || currentVitalSigns.temperature > 37.2) {
            abnormal.push({
              parameter: 'Temperature',
              value: currentVitalSigns.temperature,
              severity: currentVitalSigns.temperature < 35 || currentVitalSigns.temperature > 40 ? 'severe' : 'moderate'
            });
          }
          
          if (currentVitalSigns.oxygenSaturation < 95) {
            abnormal.push({
              parameter: 'Oxygen Saturation',
              value: currentVitalSigns.oxygenSaturation,
              severity: currentVitalSigns.oxygenSaturation < 88 ? 'severe' : 'moderate'
            });
          }
          
          if (currentVitalSigns.respiratoryRate < 12 || currentVitalSigns.respiratoryRate > 20) {
            abnormal.push({
              parameter: 'Respiratory Rate',
              value: currentVitalSigns.respiratoryRate,
              severity: currentVitalSigns.respiratoryRate < 8 || currentVitalSigns.respiratoryRate > 30 ? 'severe' : 'moderate'
            });
          }
          
          return abnormal;
        }
      }),
      {
        name: 'healthconnect-health',
        storage: createJSONStorage(() => localStorage),
        partialize: (state) => ({
          currentVitalSigns: state.currentVitalSigns,
          healthMetrics: state.healthMetrics,
          healthGoals: state.healthGoals,
          lastUpdated: state.lastUpdated
        })
      }
    )
  )
);

export default useHealthStore;
