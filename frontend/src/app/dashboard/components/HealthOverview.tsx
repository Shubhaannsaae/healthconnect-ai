/**
 * HealthOverview component for dashboard
 * Comprehensive health status overview with key metrics
 */

'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useHealthStore } from '@/store/healthStore';
import { formatHealthValue, getHealthStatusColor } from '@/lib/health-utils';
import { 
  Heart, 
  Thermometer, 
  Activity, 
  Droplets, 
  Wind,
  TrendingUp,
  TrendingDown,
  Minus,
  AlertTriangle,
  CheckCircle
} from 'lucide-react';
import { clsx } from 'clsx';
import Link from 'next/link';

interface HealthOverviewProps {
  patientId?: string;
  className?: string;
}

export const HealthOverview: React.FC<HealthOverviewProps> = ({
  patientId,
  className
}) => {
  const {
    currentVitalSigns,
    getHealthScore,
    getAbnormalVitals,
    getActiveAlerts
  } = useHealthStore();

  const healthScore = getHealthScore();
  const abnormalVitals = getAbnormalVitals();
  const activeAlerts = getActiveAlerts();

  const vitalSignsData = [
    {
      label: 'Heart Rate',
      value: currentVitalSigns?.heartRate,
      unit: 'bpm',
      icon: Heart,
      normalRange: '60-100',
      color: 'text-red-500'
    },
    {
      label: 'Blood Pressure',
      value: currentVitalSigns?.bloodPressure.systolic,
      unit: `/${currentVitalSigns?.bloodPressure.diastolic} mmHg`,
      icon: Activity,
      normalRange: '<120/80',
      color: 'text-purple-500'
    },
    {
      label: 'Temperature',
      value: currentVitalSigns?.temperature,
      unit: '°C',
      icon: Thermometer,
      normalRange: '36.1-37.2',
      color: 'text-orange-500'
    },
    {
      label: 'Oxygen Saturation',
      value: currentVitalSigns?.oxygenSaturation,
      unit: '%',
      icon: Droplets,
      normalRange: '95-100',
      color: 'text-blue-500'
    },
    {
      label: 'Respiratory Rate',
      value: currentVitalSigns?.respiratoryRate,
      unit: '/min',
      icon: Wind,
      normalRange: '12-20',
      color: 'text-green-500'
    }
  ];

  const getHealthScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getHealthScoreBg = (score: number) => {
    if (score >= 80) return 'bg-green-100';
    if (score >= 60) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  return (
    <div className={clsx('space-y-6', className)}>
      {/* Health Score Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Overall Health Score</span>
            <div className={clsx('px-3 py-1 rounded-full text-sm font-medium', getHealthScoreBg(healthScore))}>
              <span className={getHealthScoreColor(healthScore)}>
                {healthScore}/100
              </span>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between mb-4">
            <div className="flex-1">
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div 
                  className={clsx('h-3 rounded-full transition-all duration-500', {
                    'bg-green-500': healthScore >= 80,
                    'bg-yellow-500': healthScore >= 60 && healthScore < 80,
                    'bg-red-500': healthScore < 60
                  })}
                  style={{ width: `${healthScore}%` }}
                />
              </div>
            </div>
            <div className="ml-4 text-right">
              <div className={clsx('text-2xl font-bold', getHealthScoreColor(healthScore))}>
                {healthScore}
              </div>
              <div className="text-sm text-gray-500">Score</div>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-lg font-semibold text-green-600">
                {vitalSignsData.filter(v => v.value && !abnormalVitals.find(a => a.parameter.includes(v.label))).length}
              </div>
              <div className="text-sm text-gray-600">Normal Values</div>
            </div>
            <div>
              <div className="text-lg font-semibold text-yellow-600">
                {abnormalVitals.filter(v => v.severity === 'moderate').length}
              </div>
              <div className="text-sm text-gray-600">Borderline</div>
            </div>
            <div>
              <div className="text-lg font-semibold text-red-600">
                {abnormalVitals.filter(v => v.severity === 'severe').length}
              </div>
              <div className="text-sm text-gray-600">Abnormal</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Vital Signs Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {vitalSignsData.map((vital, index) => {
          const isAbnormal = abnormalVitals.find(a => a.parameter.includes(vital.label));
          
          return (
            <Card key={index} className={clsx('transition-all duration-200', {
              'border-green-200 bg-green-50': !isAbnormal && vital.value,
              'border-yellow-200 bg-yellow-50': isAbnormal?.severity === 'moderate',
              'border-red-200 bg-red-50': isAbnormal?.severity === 'severe'
            })}>
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className={clsx('p-2 rounded-lg', {
                    'bg-green-100': !isAbnormal && vital.value,
                    'bg-yellow-100': isAbnormal?.severity === 'moderate',
                    'bg-red-100': isAbnormal?.severity === 'severe',
                    'bg-gray-100': !vital.value
                  })}>
                    <vital.icon className={clsx('w-5 h-5', {
                      'text-green-600': !isAbnormal && vital.value,
                      'text-yellow-600': isAbnormal?.severity === 'moderate',
                      'text-red-600': isAbnormal?.severity === 'severe',
                      'text-gray-400': !vital.value
                    })} />
                  </div>
                  
                  {isAbnormal ? (
                    <AlertTriangle className={clsx('w-4 h-4', {
                      'text-yellow-600': isAbnormal.severity === 'moderate',
                      'text-red-600': isAbnormal.severity === 'severe'
                    })} />
                  ) : vital.value ? (
                    <CheckCircle className="w-4 h-4 text-green-600" />
                  ) : null}
                </div>
                
                <div>
                  <h3 className="font-medium text-gray-900 mb-1">{vital.label}</h3>
                  <div className="flex items-baseline space-x-1">
                    <span className="text-2xl font-bold text-gray-900">
                      {vital.value ? (typeof vital.value === 'number' ? vital.value.toFixed(vital.label === 'Temperature' ? 1 : 0) : vital.value) : '--'}
                    </span>
                    <span className="text-sm text-gray-500">{vital.unit}</span>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    Normal: {vital.normalRange}
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Active Alerts Summary */}
      {activeAlerts.length > 0 && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2 text-yellow-800">
              <AlertTriangle className="w-5 h-5" />
              <span>Active Health Alerts</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {activeAlerts.slice(0, 3).map((alert) => (
                <div key={alert.id} className="flex items-center justify-between p-2 bg-white rounded border">
                  <div>
                    <div className="font-medium text-gray-900">{alert.title}</div>
                    <div className="text-sm text-gray-600">{alert.message}</div>
                  </div>
                  <span className={clsx('px-2 py-1 rounded text-xs font-medium', {
                    'bg-red-100 text-red-800': alert.severity === 'critical',
                    'bg-orange-100 text-orange-800': alert.severity === 'high',
                    'bg-yellow-100 text-yellow-800': alert.severity === 'medium'
                  })}>
                    {alert.severity}
                  </span>
                </div>
              ))}
              
              {activeAlerts.length > 3 && (
                <div className="text-center pt-2">
                  <Link href="/dashboard/alerts">
                    <Button variant="outline" size="sm">
                      View All {activeAlerts.length} Alerts
                    </Button>
                  </Link>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Health Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <Link href="/dashboard/health/add">
              <Button variant="outline" className="w-full justify-start">
                <Heart className="w-4 h-4 mr-2" />
                Record Vital Signs
              </Button>
            </Link>
            <Link href="/consultation">
              <Button variant="outline" className="w-full justify-start">
                <Activity className="w-4 h-4 mr-2" />
                Start Consultation
              </Button>
            </Link>
            <Link href="/devices">
              <Button variant="outline" className="w-full justify-start">
                <Droplets className="w-4 h-4 mr-2" />
                Check Devices
              </Button>
            </Link>
            <Link href="/analytics">
              <Button variant="outline" className="w-full justify-start">
                <TrendingUp className="w-4 h-4 mr-2" />
                View Analytics
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default HealthOverview;
