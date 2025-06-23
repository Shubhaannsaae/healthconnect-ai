/**
 * Custom React hook for health data management
 * Provides comprehensive health data operations for HealthConnect AI
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuthStore } from '@/store/authStore';
import { useHealthStore } from '@/store/healthStore';
import type { VitalSigns, HealthRecord, HealthAlert, HealthGoal, HealthTrend } from '@/types/health';
import { analyzeVitalSigns, calculateHealthScore } from '@/lib/health-utils';

interface UseHealthDataOptions {
  patientId?: string;
  autoFetch?: boolean;
  refreshInterval?: number;
  enableRealTimeUpdates?: boolean;
}

interface UseHealthDataReturn {
  // Current data
  currentVitalSigns: VitalSigns | null;
  healthRecords: HealthRecord[];
  healthAlerts: HealthAlert[];
  healthGoals: HealthGoal[];
  healthTrends: HealthTrend[];
  
  // Computed values
  healthScore: number;
  abnormalVitals: Array<{ parameter: string; value: number; severity: string }>;
  activeAlerts: HealthAlert[];
  criticalAlerts: HealthAlert[];
  
  // State
  loading: boolean;
  error: string | null;
  lastUpdated: string | null;
  
  // Actions
  addVitalSigns: (vitalSigns: VitalSigns) => void;
  addHealthRecord: (record: HealthRecord) => Promise<void>;
  updateHealthRecord: (recordId: string, updates: Partial<HealthRecord>) => Promise<void>;
  deleteHealthRecord: (recordId: string) => Promise<void>;
  acknowledgeAlert: (alertId: string) => Promise<void>;
  resolveAlert: (alertId: string) => Promise<void>;
  addHealthGoal: (goal: HealthGoal) => Promise<void>;
  updateHealthGoal: (goalId: string, updates: Partial<HealthGoal>) => Promise<void>;
  deleteHealthGoal: (goalId: string) => Promise<void>;
  refreshData: () => Promise<void>;
  analyzeHealthData: () => Promise<void>;
  clearError: () => void;
  
  // Utilities
  getVitalSignsTrend: (metric: string, timeframe: string) => HealthTrend | null;
  getHealthInsights: () => any[];
  exportHealthData: (format: 'json' | 'csv' | 'pdf') => Promise<Blob>;
}

export const useHealthData = (options: UseHealthDataOptions = {}): UseHealthDataReturn => {
  const { userAttributes } = useAuthStore();
  const {
    currentVitalSigns,
    healthRecords,
    healthAlerts,
    healthGoals,
    healthTrends,
    healthInsights,
    loading,
    error,
    lastUpdated,
    setCurrentVitalSigns,
    addHealthRecord: storeAddHealthRecord,
    updateHealthRecord: storeUpdateHealthRecord,
    deleteHealthRecord: storeDeleteHealthRecord,
    acknowledgeAlert: storeAcknowledgeAlert,
    resolveAlert: storeResolveAlert,
    addHealthGoal: storeAddHealthGoal,
    updateHealthGoal: storeUpdateHealthGoal,
    deleteHealthGoal: storeDeleteHealthGoal,
    fetchHealthRecords,
    fetchVitalSigns,
    fetchHealthAlerts,
    fetchHealthGoals,
    analyzeHealthData: storeAnalyzeHealthData,
    getActiveAlerts,
    getCriticalAlerts,
    getHealthScore,
    getAbnormalVitals,
    clearError: storeClearError
  } = useHealthStore();

  const [refreshTimer, setRefreshTimer] = useState<NodeJS.Timeout | null>(null);

  // Determine patient ID
  const patientId = options.patientId || userAttributes?.sub || '';

  // Auto-fetch data on mount and when patientId changes
  useEffect(() => {
    if (options.autoFetch && patientId) {
      refreshData();
    }
  }, [options.autoFetch, patientId]);

  // Set up refresh interval
  useEffect(() => {
    if (options.refreshInterval && options.refreshInterval > 0) {
      const timer = setInterval(() => {
        if (patientId) {
          refreshData();
        }
      }, options.refreshInterval);
      
      setRefreshTimer(timer);
      
      return () => {
        clearInterval(timer);
      };
    }
  }, [options.refreshInterval, patientId]);

  // Add vital signs
  const addVitalSigns = useCallback((vitalSigns: VitalSigns) => {
    setCurrentVitalSigns(vitalSigns);
  }, [setCurrentVitalSigns]);

  // Add health record
  const addHealthRecord = useCallback(async (record: HealthRecord): Promise<void> => {
    await storeAddHealthRecord(record);
  }, [storeAddHealthRecord]);

  // Update health record
  const updateHealthRecord = useCallback(async (recordId: string, updates: Partial<HealthRecord>): Promise<void> => {
    await storeUpdateHealthRecord(recordId, updates);
  }, [storeUpdateHealthRecord]);

  // Delete health record
  const deleteHealthRecord = useCallback(async (recordId: string): Promise<void> => {
    await storeDeleteHealthRecord(recordId);
  }, [storeDeleteHealthRecord]);

  // Acknowledge alert
  const acknowledgeAlert = useCallback(async (alertId: string): Promise<void> => {
    await storeAcknowledgeAlert(alertId);
  }, [storeAcknowledgeAlert]);

  // Resolve alert
  const resolveAlert = useCallback(async (alertId: string): Promise<void> => {
    await storeResolveAlert(alertId);
  }, [storeResolveAlert]);

  // Add health goal
  const addHealthGoal = useCallback(async (goal: HealthGoal): Promise<void> => {
    await storeAddHealthGoal(goal);
  }, [storeAddHealthGoal]);

  // Update health goal
  const updateHealthGoal = useCallback(async (goalId: string, updates: Partial<HealthGoal>): Promise<void> => {
    await storeUpdateHealthGoal(goalId, updates);
  }, [storeUpdateHealthGoal]);

  // Delete health goal
  const deleteHealthGoal = useCallback(async (goalId: string): Promise<void> => {
    await storeDeleteHealthGoal(goalId);
  }, [storeDeleteHealthGoal]);

  // Refresh all data
  const refreshData = useCallback(async (): Promise<void> => {
    if (!patientId) return;

    try {
      await Promise.all([
        fetchHealthRecords(patientId),
        fetchVitalSigns(patientId),
        fetchHealthAlerts(patientId),
        fetchHealthGoals(patientId)
      ]);
    } catch (error) {
      console.error('Error refreshing health data:', error);
    }
  }, [patientId, fetchHealthRecords, fetchVitalSigns, fetchHealthAlerts, fetchHealthGoals]);

  // Analyze health data
  const analyzeHealthData = useCallback(async (): Promise<void> => {
    if (!patientId) return;
    await storeAnalyzeHealthData(patientId);
  }, [patientId, storeAnalyzeHealthData]);

  // Clear error
  const clearError = useCallback(() => {
    storeClearError();
  }, [storeClearError]);

  // Get vital signs trend
  const getVitalSignsTrend = useCallback((metric: string, timeframe: string): HealthTrend | null => {
    return healthTrends.find(trend => 
      trend.metric === metric && trend.timeframe === timeframe
    ) || null;
  }, [healthTrends]);

  // Get health insights
  const getHealthInsights = useCallback(() => {
    return healthInsights || [];
  }, [healthInsights]);

  // Export health data
  const exportHealthData = useCallback(async (format: 'json' | 'csv' | 'pdf'): Promise<Blob> => {
    const exportData = {
      patientId,
      currentVitalSigns,
      healthRecords,
      healthGoals,
      exportedAt: new Date().toISOString()
    };

    switch (format) {
      case 'json':
        return new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
      
      case 'csv':
        // Convert to CSV format
        const csvData = healthRecords.map(record => ({
          timestamp: record.timestamp,
          type: record.recordType,
          heartRate: record.vitalSigns?.heartRate || '',
          bloodPressure: record.vitalSigns ? 
            `${record.vitalSigns.bloodPressure.systolic}/${record.vitalSigns.bloodPressure.diastolic}` : '',
          temperature: record.vitalSigns?.temperature || '',
          oxygenSaturation: record.vitalSigns?.oxygenSaturation || '',
          notes: record.notes || ''
        }));
        
        const csvHeaders = Object.keys(csvData[0] || {}).join(',');
        const csvRows = csvData.map(row => Object.values(row).join(','));
        const csvContent = [csvHeaders, ...csvRows].join('\n');
        
        return new Blob([csvContent], { type: 'text/csv' });
      
      case 'pdf':
        // For PDF export, you would typically use a library like jsPDF
        // This is a placeholder implementation
        return new Blob([JSON.stringify(exportData)], { type: 'application/pdf' });
      
      default:
        throw new Error(`Unsupported export format: ${format}`);
    }
  }, [patientId, currentVitalSigns, healthRecords, healthGoals]);

  // Computed values
  const healthScore = useMemo(() => getHealthScore(), [getHealthScore]);
  const abnormalVitals = useMemo(() => getAbnormalVitals(), [getAbnormalVitals]);
  const activeAlerts = useMemo(() => getActiveAlerts(), [getActiveAlerts]);
  const criticalAlerts = useMemo(() => getCriticalAlerts(), [getCriticalAlerts]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (refreshTimer) {
        clearInterval(refreshTimer);
      }
    };
  }, [refreshTimer]);

  return {
    // Current data
    currentVitalSigns,
    healthRecords,
    healthAlerts,
    healthGoals,
    healthTrends,
    
    // Computed values
    healthScore,
    abnormalVitals,
    activeAlerts,
    criticalAlerts,
    
    // State
    loading,
    error,
    lastUpdated,
    
    // Actions
    addVitalSigns,
    addHealthRecord,
    updateHealthRecord,
    deleteHealthRecord,
    acknowledgeAlert,
    resolveAlert,
    addHealthGoal,
    updateHealthGoal,
    deleteHealthGoal,
    refreshData,
    analyzeHealthData,
    clearError,
    
    // Utilities
    getVitalSignsTrend,
    getHealthInsights,
    exportHealthData
  };
};

export default useHealthData;
