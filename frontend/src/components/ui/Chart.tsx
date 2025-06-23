/**
 * Production-grade Chart component for HealthConnect AI
 * Wrapper around Recharts with health-specific configurations
 */

import React from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { clsx } from 'clsx';

export interface ChartData {
  [key: string]: any;
}

export interface ChartProps {
  data: ChartData[];
  type: 'line' | 'area' | 'bar' | 'pie';
  width?: number | string;
  height?: number | string;
  className?: string;
  colors?: string[];
  showGrid?: boolean;
  showTooltip?: boolean;
  showLegend?: boolean;
  xAxisKey?: string;
  yAxisKeys?: string[];
  title?: string;
  subtitle?: string;
  loading?: boolean;
  error?: string;
  formatTooltip?: (value: any, name: string, props: any) => [string, string];
  formatXAxis?: (value: any) => string;
  formatYAxis?: (value: any) => string;
}

const defaultColors = [
  '#0ea5e9', // Primary blue
  '#22c55e', // Success green
  '#f59e0b', // Warning yellow
  '#ef4444', // Danger red
  '#8b5cf6', // Purple
  '#06b6d4', // Cyan
  '#84cc16', // Lime
  '#f97316'  // Orange
];

const healthColors = {
  heartRate: '#e74c3c',
  bloodPressure: '#9b59b6',
  temperature: '#e67e22',
  oxygenSaturation: '#3498db',
  glucose: '#f39c12',
  respiratoryRate: '#00bcd4'
};

export const Chart: React.FC<ChartProps> = ({
  data,
  type,
  width = '100%',
  height = 300,
  className,
  colors = defaultColors,
  showGrid = true,
  showTooltip = true,
  showLegend = true,
  xAxisKey = 'timestamp',
  yAxisKeys = [],
  title,
  subtitle,
  loading = false,
  error,
  formatTooltip,
  formatXAxis,
  formatYAxis
}) => {
  // Loading state
  if (loading) {
    return (
      <div className={clsx('flex items-center justify-center', className)} style={{ height }}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-32 mb-2"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className={clsx('flex items-center justify-center text-red-500', className)} style={{ height }}>
        <div className="text-center">
          <p className="text-sm font-medium">Error loading chart</p>
          <p className="text-xs text-gray-500 mt-1">{error}</p>
        </div>
      </div>
    );
  }

  // No data state
  if (!data || data.length === 0) {
    return (
      <div className={clsx('flex items-center justify-center text-gray-500', className)} style={{ height }}>
        <div className="text-center">
          <p className="text-sm font-medium">No data available</p>
          <p className="text-xs text-gray-400 mt-1">Data will appear here when available</p>
        </div>
      </div>
    );
  }

  const commonProps = {
    width,
    height,
    data,
    margin: { top: 20, right: 30, left: 20, bottom: 20 }
  };

  const renderChart = () => {
    switch (type) {
      case 'line':
        return (
          <LineChart {...commonProps}>
            {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />}
            <XAxis
              dataKey={xAxisKey}
              tick={{ fontSize: 12 }}
              tickFormatter={formatXAxis}
              stroke="#666"
            />
            <YAxis
              tick={{ fontSize: 12 }}
              tickFormatter={formatYAxis}
              stroke="#666"
            />
            {showTooltip && (
              <Tooltip
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                }}
                formatter={formatTooltip}
              />
            )}
            {showLegend && <Legend />}
            {yAxisKeys.map((key, index) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                stroke={colors[index % colors.length]}
                strokeWidth={2}
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
              />
            ))}
          </LineChart>
        );

      case 'area':
        return (
          <AreaChart {...commonProps}>
            {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />}
            <XAxis
              dataKey={xAxisKey}
              tick={{ fontSize: 12 }}
              tickFormatter={formatXAxis}
              stroke="#666"
            />
            <YAxis
              tick={{ fontSize: 12 }}
              tickFormatter={formatYAxis}
              stroke="#666"
            />
            {showTooltip && (
              <Tooltip
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                }}
                formatter={formatTooltip}
              />
            )}
            {showLegend && <Legend />}
            {yAxisKeys.map((key, index) => (
              <Area
                key={key}
                type="monotone"
                dataKey={key}
                stackId="1"
                stroke={colors[index % colors.length]}
                fill={colors[index % colors.length]}
                fillOpacity={0.3}
              />
            ))}
          </AreaChart>
        );

      case 'bar':
        return (
          <BarChart {...commonProps}>
            {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />}
            <XAxis
              dataKey={xAxisKey}
              tick={{ fontSize: 12 }}
              tickFormatter={formatXAxis}
              stroke="#666"
            />
            <YAxis
              tick={{ fontSize: 12 }}
              tickFormatter={formatYAxis}
              stroke="#666"
            />
            {showTooltip && (
              <Tooltip
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                }}
                formatter={formatTooltip}
              />
            )}
            {showLegend && <Legend />}
            {yAxisKeys.map((key, index) => (
              <Bar
                key={key}
                dataKey={key}
                fill={colors[index % colors.length]}
                radius={[4, 4, 0, 0]}
              />
            ))}
          </BarChart>
        );

      case 'pie':
        return (
          <PieChart {...commonProps}>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              outerRadius={80}
              fill="#8884d8"
              dataKey={yAxisKeys[0] || 'value'}
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
              ))}
            </Pie>
            {showTooltip && <Tooltip />}
            {showLegend && <Legend />}
          </PieChart>
        );

      default:
        return null;
    }
  };

  return (
    <div className={clsx('w-full', className)}>
      {(title || subtitle) && (
        <div className="mb-4">
          {title && (
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          )}
          {subtitle && (
            <p className="text-sm text-gray-600 mt-1">{subtitle}</p>
          )}
        </div>
      )}
      
      <ResponsiveContainer width={width} height={height}>
        {renderChart()}
      </ResponsiveContainer>
    </div>
  );
};

// Specialized health chart components
export const VitalSignsChart: React.FC<Omit<ChartProps, 'colors' | 'yAxisKeys'> & {
  vitalType: keyof typeof healthColors;
}> = ({ vitalType, ...props }) => (
  <Chart
    {...props}
    colors={[healthColors[vitalType]]}
    yAxisKeys={[vitalType]}
    formatTooltip={(value, name) => [
      `${value} ${getVitalSignUnit(vitalType)}`,
      getVitalSignLabel(vitalType)
    ]}
  />
);

function getVitalSignUnit(vitalType: keyof typeof healthColors): string {
  const units = {
    heartRate: 'bpm',
    bloodPressure: 'mmHg',
    temperature: '°C',
    oxygenSaturation: '%',
    glucose: 'mg/dL',
    respiratoryRate: '/min'
  };
  return units[vitalType] || '';
}

function getVitalSignLabel(vitalType: keyof typeof healthColors): string {
  const labels = {
    heartRate: 'Heart Rate',
    bloodPressure: 'Blood Pressure',
    temperature: 'Temperature',
    oxygenSaturation: 'Oxygen Saturation',
    glucose: 'Glucose Level',
    respiratoryRate: 'Respiratory Rate'
  };
  return labels[vitalType] || vitalType;
}

export default Chart;
