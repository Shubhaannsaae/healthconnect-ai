/**
 * VitalSigns component for HealthConnect AI
 * Displays comprehensive vital signs data with real-time updates
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Chart } from '@/components/ui/Chart';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { useHealthData } from '@/hooks/useHealthData';
import type { VitalSigns as VitalSignsType } from '@/types/health';
import { formatHealthValue, getHealthStatusColor, isHealthValueNormal } from '@/lib/health-utils';
import { Heart, Thermometer, Activity, Droplets, Wind, Gauge } from 'lucide-react';
import { clsx } from 'clsx';

interface VitalSignsProps {
  patientId?: string;
  showTrends?: boolean;
  showAlerts?: boolean;
  refreshInterval?: number;
  className?: string;
}

interface VitalSignCardProps {
  icon: React.ReactNode;
  label: string;
  value: number | undefined;
  unit: string;
  metric: string;
  trend?: 'up' | 'down' | 'stable';
  trendValue?: number;
  isNormal: boolean;
  timestamp?: string;
}

const VitalSignCard: React.FC<VitalSignCardProps> = ({
  icon,
  label,
  value,
  unit,
  metric,
  trend,
  trendValue,
  isNormal,
  timestamp
}) => {
  const statusColor = value ? getHealthStatusColor(value, metric) : 'text-gray-400';
  
  return (
    <Card className={clsx('transition-all duration-200', {
      'border-green-200 bg-green-50': isNormal && value,
      'border-yellow-200 bg-yellow-50': !isNormal && value && statusColor.includes('yellow'),
      'border-red-200 bg-red-50': !isNormal && value && statusColor.includes('red')
    })}>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={clsx('p-2 rounded-lg', {
              'bg-green-100 text-green-600': isNormal && value,
              'bg-yellow-100 text-yellow-600': !isNormal && value && statusColor.includes('yellow'),
              'bg-red-100 text-red-600': !isNormal && value && statusColor.includes('red'),
              'bg-gray-100 text-gray-400': !value
            })}>
              {icon}
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">{label}</p>
              <div className="flex items-baseline space-x-1">
                <span className={clsx('text-2xl font-bold', statusColor)}>
                  {value ? value.toFixed(metric === 'temperature' ? 1 : 0) : '--'}
                </span>
                <span className="text-sm text-gray-500">{unit}</span>
              </div>
            </div>
          </div>
          
          {trend && trendValue && (
            <div className={clsx('flex items-center text-xs', {
              'text-green-600': trend === 'up' && isNormal,
              'text-red-600': trend === 'up' && !isNormal,
              'text-red-600': trend === 'down' && isNormal,
              'text-green-600': trend === 'down' && !isNormal,
              'text-gray-500': trend === 'stable'
            })}>
              <span className="mr-1">
                {trend === 'up' ? '↗' : trend === 'down' ? '↘' : '→'}
              </span>
              <span>{Math.abs(trendValue).toFixed(1)}%</span>
            </div>
          )}
        </div>
        
        {timestamp && (
          <p className="text-xs text-gray-400 mt-2">
            Last updated: {new Date(timestamp).toLocaleTimeString()}
          </p>
        )}
      </CardContent>
    </Card>
  );
};

export const VitalSigns: React.FC<VitalSignsProps> = ({
  patientId,
  showTrends = true,
  showAlerts = true,
  refreshInterval = 30000,
  className
}) => {
  const {
    currentVitalSigns,
    healthTrends,
    loading,
    error,
    refreshData
  } = useHealthData({
    patientId,
    autoFetch: true,
    refreshInterval
  });

  const [selectedMetric, setSelectedMetric] = useState<string>('heartRate');

  if (loading && !currentVitalSigns) {
    return (
      <div className={clsx('space-y-4', className)}>
        <Card>
          <CardHeader>
            <CardTitle>Vital Signs</CardTitle>
          </CardHeader>
          <CardContent>
            <LoadingSpinner size="lg" showLabel label="Loading vital signs..." />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className={clsx('space-y-4', className)}>
        <Card>
          <CardHeader>
            <CardTitle>Vital Signs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center py-8">
              <p className="text-red-600 font-medium">Error loading vital signs</p>
              <p className="text-sm text-gray-500 mt-1">{error}</p>
              <button
                onClick={refreshData}
                className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
              >
                Retry
              </button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const vitalSignsData = [
    {
      icon: <Heart className="w-5 h-5" />,
      label: 'Heart Rate',
      value: currentVitalSigns?.heartRate,
      unit: 'bpm',
      metric: 'heart_rate',
      isNormal: currentVitalSigns ? isHealthValueNormal(currentVitalSigns.heartRate, 'heart_rate') : false
    },
    {
      icon: <Gauge className="w-5 h-5" />,
      label: 'Blood Pressure',
      value: currentVitalSigns?.bloodPressure.systolic,
      unit: `/${currentVitalSigns?.bloodPressure.diastolic || '--'} mmHg`,
      metric: 'systolic_pressure',
      isNormal: currentVitalSigns ? isHealthValueNormal(currentVitalSigns.bloodPressure.systolic, 'systolic_pressure') : false
    },
    {
      icon: <Thermometer className="w-5 h-5" />,
      label: 'Temperature',
      value: currentVitalSigns?.temperature,
      unit: '°C',
      metric: 'temperature',
      isNormal: currentVitalSigns ? isHealthValueNormal(currentVitalSigns.temperature, 'temperature') : false
    },
    {
      icon: <Droplets className="w-5 h-5" />,
      label: 'Oxygen Saturation',
      value: currentVitalSigns?.oxygenSaturation,
      unit: '%',
      metric: 'oxygen_saturation',
      isNormal: currentVitalSigns ? isHealthValueNormal(currentVitalSigns.oxygenSaturation, 'oxygen_saturation') : false
    },
    {
      icon: <Wind className="w-5 h-5" />,
      label: 'Respiratory Rate',
      value: currentVitalSigns?.respiratoryRate,
      unit: '/min',
      metric: 'respiratory_rate',
      isNormal: currentVitalSigns ? isHealthValueNormal(currentVitalSigns.respiratoryRate, 'respiratory_rate') : false
    },
    {
      icon: <Activity className="w-5 h-5" />,
      label: 'Glucose Level',
      value: currentVitalSigns?.glucoseLevel,
      unit: 'mg/dL',
      metric: 'glucose_level',
      isNormal: currentVitalSigns?.glucoseLevel ? isHealthValueNormal(currentVitalSigns.glucoseLevel, 'glucose_level') : true
    }
  ];

  const selectedTrend = healthTrends.find(trend => trend.metric === selectedMetric);

  return (
    <div className={clsx('space-y-6', className)}>
      {/* Vital Signs Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {vitalSignsData.map((vital, index) => (
          <VitalSignCard
            key={index}
            {...vital}
            timestamp={currentVitalSigns?.timestamp}
          />
        ))}
      </div>

      {/* Trends Chart */}
      {showTrends && (
        <Card>
          <CardHeader>
            <CardTitle>Vital Signs Trends</CardTitle>
            <div className="flex flex-wrap gap-2 mt-4">
              {vitalSignsData.map((vital, index) => (
                <button
                  key={index}
                  onClick={() => setSelectedMetric(vital.metric)}
                  className={clsx(
                    'px-3 py-1 rounded-full text-sm font-medium transition-colors',
                    selectedMetric === vital.metric
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  )}
                >
                  {vital.label}
                </button>
              ))}
            </div>
          </CardHeader>
          <CardContent>
            {selectedTrend ? (
              <Chart
                data={selectedTrend.dataPoints}
                type="line"
                height={300}
                xAxisKey="timestamp"
                yAxisKeys={['value']}
                formatXAxis={(value) => new Date(value).toLocaleDateString()}
                formatTooltip={(value, name) => [
                  formatHealthValue(value as number, selectedMetric),
                  vitalSignsData.find(v => v.metric === selectedMetric)?.label || name
                ]}
              />
            ) : (
              <div className="flex items-center justify-center h-64 text-gray-500">
                <div className="text-center">
                  <Activity className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No trend data available</p>
                  <p className="text-sm mt-1">Data will appear as more readings are collected</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Summary Card */}
      <Card>
        <CardHeader>
          <CardTitle>Health Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600 mb-1">
                {vitalSignsData.filter(v => v.isNormal && v.value).length}
              </div>
              <p className="text-sm text-gray-600">Normal Values</p>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-yellow-600 mb-1">
                {vitalSignsData.filter(v => !v.isNormal && v.value).length}
              </div>
              <p className="text-sm text-gray-600">Abnormal Values</p>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-primary-600 mb-1">
                {currentVitalSigns ? '85' : '--'}
              </div>
              <p className="text-sm text-gray-600">Health Score</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default VitalSigns;
