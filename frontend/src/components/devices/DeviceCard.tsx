/**
 * DeviceCard component for HealthConnect AI
 * Individual device card with status and actions
 */

import React, { useState } from 'react';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useDeviceStore } from '@/store/deviceStore';
import type { DeviceInfo } from '@/types/devices';
import { 
  Wifi, 
  WifiOff, 
  Battery, 
  BatteryLow, 
  Settings, 
  MoreVertical,
  Power,
  AlertTriangle,
  CheckCircle,
  Activity,
  Heart,
  Thermometer,
  Droplets,
  Gauge,
  Wind
} from 'lucide-react';
import { clsx } from 'clsx';

interface DeviceCardProps {
  device: DeviceInfo;
  onClick?: () => void;
  showActions?: boolean;
  className?: string;
}

const deviceIcons = {
  heart_rate_monitor: Heart,
  blood_pressure_cuff: Gauge,
  glucose_meter: Droplets,
  temperature_sensor: Thermometer,
  pulse_oximeter: Activity,
  activity_tracker: Activity,
  ecg_monitor: Heart,
  respiratory_monitor: Wind
};

export const DeviceCard: React.FC<DeviceCardProps> = ({
  device,
  onClick,
  showActions = false,
  className
}) => {
  const [showMenu, setShowMenu] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const {
    deviceStatuses,
    getDeviceHealth,
    sendDeviceCommand,
    updateDeviceConfiguration
  } = useDeviceStore();

  const deviceStatus = deviceStatuses.get(device.id);
  const deviceHealth = getDeviceHealth(device.id);
  const DeviceIcon = deviceIcons[device.type] || Activity;

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'online': return 'text-green-600 bg-green-100';
      case 'offline': return 'text-gray-600 bg-gray-100';
      case 'error': return 'text-red-600 bg-red-100';
      case 'maintenance': return 'text-yellow-600 bg-yellow-100';
      case 'low_battery': return 'text-orange-600 bg-orange-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getHealthColor = (health: string) => {
    switch (health) {
      case 'healthy': return 'text-green-600';
      case 'warning': return 'text-yellow-600';
      case 'critical': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getBatteryIcon = (level?: number) => {
    if (!level) return Battery;
    return level < 20 ? BatteryLow : Battery;
  };

  const handleDeviceAction = async (action: string) => {
    setIsLoading(true);
    try {
      switch (action) {
        case 'restart':
          await sendDeviceCommand(device.id, 'restart');
          break;
        case 'calibrate':
          await sendDeviceCommand(device.id, 'calibrate');
          break;
        case 'sync':
          await sendDeviceCommand(device.id, 'sync_data');
          break;
        case 'configure':
          // Open configuration modal
          break;
        default:
          break;
      }
    } catch (error) {
      console.error('Device action failed:', error);
    } finally {
      setIsLoading(false);
      setShowMenu(false);
    }
  };

  const formatLastSeen = (timestamp?: string) => {
    if (!timestamp) return 'Never';
    
    const now = new Date();
    const lastSeen = new Date(timestamp);
    const diffMs = now.getTime() - lastSeen.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  const BatteryIcon = getBatteryIcon(deviceStatus?.batteryLevel);

  return (
    <Card 
      className={clsx(
        'transition-all duration-200 hover:shadow-lg cursor-pointer relative',
        {
          'border-green-200 bg-green-50': deviceHealth === 'healthy',
          'border-yellow-200 bg-yellow-50': deviceHealth === 'warning',
          'border-red-200 bg-red-50': deviceHealth === 'critical',
          'border-gray-200': deviceHealth === 'unknown'
        },
        className
      )}
      onClick={onClick}
    >
      <CardContent className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center space-x-3">
            <div className={clsx(
              'p-2 rounded-lg',
              getStatusColor(deviceStatus?.status)
            )}>
              <DeviceIcon className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 truncate">{device.name}</h3>
              <p className="text-sm text-gray-600">{device.manufacturer} {device.model}</p>
            </div>
          </div>
          
          {showActions && (
            <div className="relative">
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  setShowMenu(!showMenu);
                }}
              >
                <MoreVertical className="w-4 h-4" />
              </Button>
              
              {showMenu && (
                <div className="absolute right-0 top-8 w-48 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
                  <div className="py-1">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeviceAction('sync');
                      }}
                      disabled={isLoading}
                      className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      Sync Data
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeviceAction('calibrate');
                      }}
                      disabled={isLoading}
                      className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      Calibrate
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeviceAction('restart');
                      }}
                      disabled={isLoading}
                      className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      Restart Device
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeviceAction('configure');
                      }}
                      className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      <Settings className="w-4 h-4 inline mr-2" />
                      Configure
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Status Indicators */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-4">
            {/* Connection Status */}
            <div className="flex items-center space-x-1">
              {deviceStatus?.status === 'online' ? (
                <Wifi className="w-4 h-4 text-green-600" />
              ) : (
                <WifiOff className="w-4 h-4 text-gray-600" />
              )}
              <span className={clsx('text-xs font-medium', {
                'text-green-600': deviceStatus?.status === 'online',
                'text-gray-600': deviceStatus?.status === 'offline',
                'text-red-600': deviceStatus?.status === 'error',
                'text-yellow-600': deviceStatus?.status === 'maintenance',
                'text-orange-600': deviceStatus?.status === 'low_battery'
              })}>
                {deviceStatus?.status ? deviceStatus.status.replace('_', ' ').toUpperCase() : 'UNKNOWN'}
              </span>
            </div>

            {/* Health Status */}
            <div className="flex items-center space-x-1">
              {deviceHealth === 'healthy' && <CheckCircle className="w-4 h-4 text-green-600" />}
              {deviceHealth === 'warning' && <AlertTriangle className="w-4 h-4 text-yellow-600" />}
              {deviceHealth === 'critical' && <AlertTriangle className="w-4 h-4 text-red-600" />}
              <span className={clsx('text-xs font-medium', getHealthColor(deviceHealth))}>
                {deviceHealth.toUpperCase()}
              </span>
            </div>
          </div>

          {/* Battery Level */}
          {deviceStatus?.batteryLevel !== undefined && (
            <div className="flex items-center space-x-1">
              <BatteryIcon className={clsx('w-4 h-4', {
                'text-green-600': deviceStatus.batteryLevel > 50,
                'text-yellow-600': deviceStatus.batteryLevel > 20 && deviceStatus.batteryLevel <= 50,
                'text-red-600': deviceStatus.batteryLevel <= 20
              })} />
              <span className="text-xs font-medium text-gray-600">
                {deviceStatus.batteryLevel}%
              </span>
            </div>
          )}
        </div>

        {/* Device Details */}
        <div className="space-y-2 text-xs text-gray-600">
          <div className="flex justify-between">
            <span>Serial Number:</span>
            <span className="font-mono">{device.serialNumber}</span>
          </div>
          <div className="flex justify-between">
            <span>Firmware:</span>
            <span>{device.firmwareVersion}</span>
          </div>
          <div className="flex justify-between">
            <span>Last Seen:</span>
            <span>{formatLastSeen(deviceStatus?.lastSeen)}</span>
          </div>
          {deviceStatus?.signalStrength !== undefined && (
            <div className="flex justify-between">
              <span>Signal:</span>
              <span>{deviceStatus.signalStrength}%</span>
            </div>
          )}
        </div>

        {/* Certifications */}
        {device.certifications && device.certifications.length > 0 && (
          <div className="mt-3 pt-3 border-t border-gray-200">
            <div className="flex flex-wrap gap-1">
              {device.certifications.slice(0, 3).map((cert, index) => (
                <span
                  key={index}
                  className="inline-block px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded"
                >
                  {cert.type}
                </span>
              ))}
              {device.certifications.length > 3 && (
                <span className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">
                  +{device.certifications.length - 3} more
                </span>
              )}
            </div>
          </div>
        )}

        {/* Quick Actions */}
        {showActions && deviceStatus?.status === 'online' && (
          <div className="mt-3 pt-3 border-t border-gray-200">
            <div className="flex space-x-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  handleDeviceAction('sync');
                }}
                disabled={isLoading}
                className="flex-1 text-xs"
              >
                Sync
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  handleDeviceAction('calibrate');
                }}
                disabled={isLoading}
                className="flex-1 text-xs"
              >
                Calibrate
              </Button>
            </div>
          </div>
        )}
      </CardContent>
      
      {/* Loading Overlay */}
      {isLoading && (
        <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center rounded-lg">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 border-2 border-primary-600 border-t-transparent rounded-full animate-spin"></div>
            <span className="text-sm text-gray-600">Processing...</span>
          </div>
        </div>
      )}
    </Card>
  );
};

export default DeviceCard;
