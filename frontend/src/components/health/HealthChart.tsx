/**
 * HealthChart component for HealthConnect AI
 * Specialized chart component for health data visualization
 */

import React, { useState, useMemo } from 'react';
import { Chart } from '@/components/ui/Chart';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import type { VitalSigns, HealthTrend } from '@/types/health';
import { formatHealthValue, getHealthMetricRange } from '@/lib/health-utils';
import { Calendar, TrendingUp, TrendingDown, Minus, Download, Share2 } from 'lucide-react';
import { clsx } from 'clsx';

interface HealthChartProps {
  data: VitalSigns[];
  metric: string;
  title: string;
  timeframe: '24h' | '7d' | '30d' | '90d' | '1y';
  onTimeframeChange?: (timeframe: string) => void;
  showNormalRange?: boolean;
  showTrend?: boolean;
  showControls?: boolean;
  height?: number;
  loading?: boolean;
  error?: string;
  className?: string;
}

const timeframeOptions = [
  { value: '24h', label: '24 Hours' },
  { value: '7d', label: '7 Days' },
  { value: '30d', label: '30 Days' },
  { value: '90d', label: '90 Days' },
  { value: '1y', label: '1 Year' }
];

export const HealthChart: React.FC<HealthChartProps> = ({
  data,
  metric,
  title,
  timeframe,
  onTimeframeChange,
  showNormalRange = true,
  showTrend = true,
  showControls = true,
  height = 400,
  loading = false,
  error,
  className
}) => {
  const [chartType, setChartType] = useState<'line' | 'area'>('line');

  // Process data for chart
  const chartData = useMemo(() => {
    return data.map(reading => {
      let value: number;
      
      // Extract the relevant metric value
      switch (metric) {
        case 'heartRate':
          value = reading.heartRate;
          break;
        case 'systolicPressure':
          value = reading.bloodPressure.systolic;
          break;
        case 'diastolicPressure':
          value = reading.bloodPressure.diastolic;
          break;
        case 'temperature':
          value = reading.temperature;
          break;
        case 'oxygenSaturation':
          value = reading.oxygenSaturation;
          break;
        case 'respiratoryRate':
          value = reading.respiratoryRate;
          break;
        case 'glucoseLevel':
          value = reading.glucoseLevel || 0;
          break;
        default:
          value = 0;
      }

      return {
        timestamp: reading.timestamp,
        value,
        formattedTime: new Date(reading.timestamp).toLocaleString(),
        date: new Date(reading.timestamp).toLocaleDateString(),
        time: new Date(reading.timestamp).toLocaleTimeString()
      };
    }).sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
  }, [data, metric]);

  // Calculate trend
  const trend = useMemo(() => {
    if (chartData.length < 2) return null;
    
    const firstValue = chartData[0].value;
    const lastValue = chartData[chartData.length - 1].value;
    const change = lastValue - firstValue;
    const percentChange = (change / firstValue) * 100;
    
    return {
      direction: change > 0 ? 'up' : change < 0 ? 'down' : 'stable',
      value: Math.abs(change),
      percent: Math.abs(percentChange)
    };
  }, [chartData]);

  // Get normal range for the metric
  const normalRange = useMemo(() => {
    return getHealthMetricRange(metric);
  }, [metric]);

  // Add normal range lines to chart data
  const chartDataWithRange = useMemo(() => {
    if (!showNormalRange) return chartData;
    
    return chartData.map(point => ({
      ...point,
      normalMin: normalRange.min,
      normalMax: normalRange.max
    }));
  }, [chartData, showNormalRange, normalRange]);

  const handleExport = () => {
    const csvContent = [
      ['Timestamp', 'Value', 'Date', 'Time'],
      ...chartData.map(point => [
        point.timestamp,
        point.value.toString(),
        point.date,
        point.time
      ])
    ].map(row => row.join(',')).join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title.toLowerCase().replace(/\s+/g, '-')}-${timeframe}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: `${title} - Health Data`,
          text: `Check out my ${title.toLowerCase()} data from HealthConnect AI`,
          url: window.location.href
        });
      } catch (error) {
        console.log('Error sharing:', error);
      }
    } else {
      // Fallback: copy to clipboard
      navigator.clipboard.writeText(window.location.href);
    }
  };

  if (loading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <LoadingSpinner size="lg" showLabel label="Loading chart data..." />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <p className="text-red-600 font-medium">Error loading chart data</p>
            <p className="text-sm text-gray-500 mt-1">{error}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center space-x-2">
              <span>{title}</span>
              {showTrend && trend && (
                <div className={clsx('flex items-center text-sm', {
                  'text-green-600': trend.direction === 'up' && metric !== 'bloodPressure',
                  'text-red-600': trend.direction === 'up' && metric === 'bloodPressure',
                  'text-red-600': trend.direction === 'down' && metric !== 'bloodPressure',
                  'text-green-600': trend.direction === 'down' && metric === 'bloodPressure',
                  'text-gray-500': trend.direction === 'stable'
                })}>
                  {trend.direction === 'up' && <TrendingUp className="w-4 h-4 mr-1" />}
                  {trend.direction === 'down' && <TrendingDown className="w-4 h-4 mr-1" />}
                  {trend.direction === 'stable' && <Minus className="w-4 h-4 mr-1" />}
                  <span>{trend.percent.toFixed(1)}%</span>
                </div>
              )}
            </CardTitle>
            {showNormalRange && (
              <p className="text-sm text-gray-500 mt-1">
                Normal range: {normalRange.min} - {normalRange.max} {normalRange.unit}
              </p>
            )}
          </div>
          
          {showControls && (
            <div className="flex items-center space-x-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleExport}
                className="text-gray-600"
              >
                <Download className="w-4 h-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleShare}
                className="text-gray-600"
              >
                <Share2 className="w-4 h-4" />
              </Button>
            </div>
          )}
        </div>
        
        {showControls && (
          <div className="flex items-center justify-between mt-4">
            <div className="flex items-center space-x-2">
              {timeframeOptions.map((option) => (
                <Button
                  key={option.value}
                  variant={timeframe === option.value ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => onTimeframeChange?.(option.value)}
                >
                  {option.label}
                </Button>
              ))}
            </div>
            
            <div className="flex items-center space-x-2">
              <Button
                variant={chartType === 'line' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setChartType('line')}
              >
                Line
              </Button>
              <Button
                variant={chartType === 'area' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setChartType('area')}
              >
                Area
              </Button>
            </div>
          </div>
        )}
      </CardHeader>
      
      <CardContent>
        {chartData.length > 0 ? (
          <Chart
            data={chartDataWithRange}
            type={chartType}
            height={height}
            xAxisKey="timestamp"
            yAxisKeys={showNormalRange ? ['value', 'normalMin', 'normalMax'] : ['value']}
            colors={['#0ea5e9', '#22c55e', '#22c55e']}
            formatXAxis={(value) => {
              const date = new Date(value);
              if (timeframe === '24h') {
                return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
              } else if (timeframe === '7d') {
                return date.toLocaleDateString([], { weekday: 'short' });
              } else {
                return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
              }
            }}
            formatYAxis={(value) => formatHealthValue(value, metric, false)}
            formatTooltip={(value, name) => {
              if (name === 'normalMin' || name === 'normalMax') {
                return [formatHealthValue(value as number, metric), 'Normal Range'];
              }
              return [formatHealthValue(value as number, metric), title];
            }}
          />
        ) : (
          <div className="flex items-center justify-center h-64 text-gray-500">
            <div className="text-center">
              <Calendar className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No data available for this timeframe</p>
              <p className="text-sm mt-1">Data will appear as readings are collected</p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default HealthChart;
