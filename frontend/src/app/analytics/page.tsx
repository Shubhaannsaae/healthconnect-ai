/**
 * Analytics page for HealthConnect AI
 * Health data analytics and insights dashboard
 */

'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { HealthChart } from '@/components/health/HealthChart';
import { VitalSignsViz } from '@/components/3d/VitalSignsViz';
import { useAuthStore } from '@/store/authStore';
import { useHealthStore } from '@/store/healthStore';
import { 
  BarChart3, 
  TrendingUp, 
  TrendingDown,
  Calendar,
  Download,
  Share2,
  Filter,
  RefreshCw,
  Activity,
  Heart,
  Thermometer,
  Droplets
} from 'lucide-react';
import { clsx } from 'clsx';

export default function AnalyticsPage() {
  const [selectedTimeframe, setSelectedTimeframe] = useState<'7d' | '30d' | '90d' | '1y'>('30d');
  const [selectedMetrics, setSelectedMetrics] = useState(['heartRate', 'bloodPressure', 'temperature']);
  const [viewMode, setViewMode] = useState<'2d' | '3d'>('2d');

  const { userAttributes } = useAuthStore();
  const {
    healthRecords,
    currentVitalSigns,
    healthTrends,
    healthInsights,
    fetchHealthRecords,
    generateHealthSummary,
    analyzeHealthData
  } = useHealthStore();

  useEffect(() => {
    if (userAttributes?.sub) {
      fetchHealthRecords(userAttributes.sub);
      analyzeHealthData(userAttributes.sub);
    }
  }, [userAttributes?.sub, fetchHealthRecords, analyzeHealthData]);

  const timeframeOptions = [
    { value: '7d', label: '7 Days' },
    { value: '30d', label: '30 Days' },
    { value: '90d', label: '90 Days' },
    { value: '1y', label: '1 Year' }
  ];

  const metricOptions = [
    { id: 'heartRate', label: 'Heart Rate', icon: Heart, color: '#ef4444' },
    { id: 'bloodPressure', label: 'Blood Pressure', icon: Activity, color: '#8b5cf6' },
    { id: 'temperature', label: 'Temperature', icon: Thermometer, color: '#f59e0b' },
    { id: 'oxygenSaturation', label: 'Oxygen Saturation', icon: Droplets, color: '#3b82f6' }
  ];

  const vitalSignsData = healthRecords
    .filter(record => record.vitalSigns)
    .map(record => record.vitalSigns!)
    .slice(-50); // Last 50 readings

  const analyticsCards = [
    {
      title: 'Health Score Trend',
      value: '85',
      change: '+2.5%',
      trend: 'up' as const,
      description: 'Overall health improvement'
    },
    {
      title: 'Average Heart Rate',
      value: '72',
      change: '-1.2%',
      trend: 'down' as const,
      description: 'Within normal range'
    },
    {
      title: 'Blood Pressure',
      value: '120/80',
      change: '+0.8%',
      trend: 'up' as const,
      description: 'Slightly elevated'
    },
    {
      title: 'Data Points',
      value: healthRecords.length.toString(),
      change: '+12',
      trend: 'up' as const,
      description: 'This month'
    }
  ];

  const handleExportData = () => {
    const csvData = healthRecords.map(record => ({
      timestamp: record.timestamp,
      heartRate: record.vitalSigns?.heartRate || '',
      systolic: record.vitalSigns?.bloodPressure.systolic || '',
      diastolic: record.vitalSigns?.bloodPressure.diastolic || '',
      temperature: record.vitalSigns?.temperature || '',
      oxygenSaturation: record.vitalSigns?.oxygenSaturation || '',
      respiratoryRate: record.vitalSigns?.respiratoryRate || ''
    }));

    const csvContent = [
      Object.keys(csvData[0] || {}).join(','),
      ...csvData.map(row => Object.values(row).join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `health-analytics-${selectedTimeframe}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleGenerateReport = async () => {
    if (!userAttributes?.sub) return;

    const endDate = new Date().toISOString();
    const startDate = new Date(Date.now() - (
      selectedTimeframe === '7d' ? 7 * 24 * 60 * 60 * 1000 :
      selectedTimeframe === '30d' ? 30 * 24 * 60 * 60 * 1000 :
      selectedTimeframe === '90d' ? 90 * 24 * 60 * 60 * 1000 :
      365 * 24 * 60 * 60 * 1000
    )).toISOString();

    try {
      await generateHealthSummary(userAttributes.sub, { start: startDate, end: endDate });
    } catch (error) {
      console.error('Failed to generate health summary:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Health Analytics</h1>
          <p className="text-gray-600">Comprehensive analysis of your health data and trends</p>
        </div>
        
        <div className="flex space-x-3">
          <Button variant="outline" onClick={handleExportData}>
            <Download className="w-4 h-4 mr-2" />
            Export Data
          </Button>
          <Button variant="outline">
            <Share2 className="w-4 h-4 mr-2" />
            Share Report
          </Button>
          <Button onClick={handleGenerateReport}>
            <BarChart3 className="w-4 h-4 mr-2" />
            Generate Report
          </Button>
        </div>
      </div>

      {/* Controls */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Calendar className="w-4 h-4 text-gray-500" />
                <span className="text-sm font-medium text-gray-700">Timeframe:</span>
                <div className="flex space-x-1">
                  {timeframeOptions.map((option) => (
                    <Button
                      key={option.value}
                      variant={selectedTimeframe === option.value ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setSelectedTimeframe(option.value as any)}
                    >
                      {option.label}
                    </Button>
                  ))}
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium text-gray-700">View:</span>
                <div className="flex space-x-1">
                  <Button
                    variant={viewMode === '2d' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setViewMode('2d')}
                  >
                    2D Charts
                  </Button>
                  <Button
                    variant={viewMode === '3d' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setViewMode('3d')}
                  >
                    3D Visualization
                  </Button>
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <Button variant="outline" size="sm">
                <Filter className="w-4 h-4 mr-1" />
                Filters
              </Button>
              <Button variant="outline" size="sm">
                <RefreshCw className="w-4 h-4 mr-1" />
                Refresh
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Analytics Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {analyticsCards.map((card, index) => (
          <Card key={index} className="hover:shadow-lg transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{card.title}</p>
                  <div className="flex items-baseline mt-2">
                    <p className="text-2xl font-semibold text-gray-900">{card.value}</p>
                    <div className={clsx('ml-2 flex items-center text-sm', {
                      'text-green-600': card.trend === 'up',
                      'text-red-600': card.trend === 'down'
                    })}>
                      {card.trend === 'up' ? (
                        <TrendingUp className="w-4 h-4 mr-1" />
                      ) : (
        // Conditionally render VitalSignsViz only if currentVitalSigns is not null

                        <TrendingDown className="w-4 h-4 mr-1" />
                      )}
                      <span>{card.change}</span>
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">{card.description}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Metric Selection */}
      <Card>
        <CardHeader>
          <CardTitle>Select Metrics to Analyze</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            {metricOptions.map((metric) => (
              <button
                key={metric.id}
                onClick={() => {
                  setSelectedMetrics(prev => 
                    prev.includes(metric.id)
                      ? prev.filter(m => m !== metric.id)
                      : [...prev, metric.id]
                  );
                }}
                className={clsx(
                  'flex items-center space-x-2 px-4 py-2 rounded-lg border transition-colors',
                  selectedMetrics.includes(metric.id)
                    ? 'bg-primary-50 border-primary-200 text-primary-700'
                    : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50'
                )}
              >
                <metric.icon className="w-4 h-4" />
                <span className="text-sm font-medium">{metric.label}</span>
                <div 
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: metric.color }}
                />
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Main Analytics Display */}
      {viewMode === '2d' ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {selectedMetrics.map((metric) => {
            const metricConfig = metricOptions.find(m => m.id === metric);
            if (!metricConfig) return null;

            return (
              <HealthChart
                key={metric}
                data={vitalSignsData}
                metric={metric as any}
                title={metricConfig.label}
                timeframe={selectedTimeframe}
                showNormalRange={true}
                showTrend={true}
                height={300}
              />
            );
          })}
        </div>
      ) : (
        currentVitalSigns && (
          <VitalSignsViz
            vitalSigns={vitalSignsData}
            realTimeData={currentVitalSigns}
            maxDataPoints={100}
            autoRotate={false}
            showGrid={true}
          />
        )
      )}

      {/* Health Insights */}
      {healthInsights.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>AI Health Insights</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {healthInsights.slice(0, 5).map((insight) => (
                <div key={insight.id} className={clsx('p-4 rounded-lg border-l-4', {
                  'bg-blue-50 border-blue-500': insight.priority === 'low',
                  'bg-yellow-50 border-yellow-500': insight.priority === 'medium',
                  'bg-red-50 border-red-500': insight.priority === 'high'
                })}>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900 mb-1">{insight.title}</h3>
                      <p className="text-gray-700 text-sm mb-2">{insight.description}</p>
                      {insight.actions && insight.actions.length > 0 && (
                        <div className="flex flex-wrap gap-2">
                          {insight.actions.map((action, index) => (
                            <Button key={index} variant="outline" size="sm">
                              {action}
                            </Button>
                          ))}
                        </div>
                      )}
                    </div>
                    <div className="ml-4">
                      <span className={clsx('px-2 py-1 rounded text-xs font-medium', {
                        'bg-blue-100 text-blue-800': insight.priority === 'low',
                        'bg-yellow-100 text-yellow-800': insight.priority === 'medium',
                        'bg-red-100 text-red-800': insight.priority === 'high'
                      })}>
                        {insight.priority} priority
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Health Trends Summary */}
      {healthTrends.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Health Trends Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {healthTrends.slice(0, 6).map((trend, index) => (
                <div key={index} className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium text-gray-900 capitalize">
                      {trend.metric.replace(/([A-Z])/g, ' $1').trim()}
                    </h3>
                    <div className={clsx('flex items-center text-sm', {
                      'text-green-600': trend.trend === 'improving',
                      'text-red-600': trend.trend === 'declining',
                      'text-blue-600': trend.trend === 'stable',
                      'text-yellow-600': trend.trend === 'fluctuating'
                    })}>
                      {trend.trend === 'improving' && <TrendingUp className="w-4 h-4 mr-1" />}
                      {trend.trend === 'declining' && <TrendingDown className="w-4 h-4 mr-1" />}
                      <span className="capitalize">{trend.trend}</span>
                    </div>
                  </div>
                  <div className="text-2xl font-bold text-gray-900 mb-1">
                    {trend.changePercentage > 0 ? '+' : ''}{trend.changePercentage.toFixed(1)}%
                  </div>
                  <div className="text-sm text-gray-600">
                    Over {trend.timeframe}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
