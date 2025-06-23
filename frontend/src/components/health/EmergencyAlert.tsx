/**
 * EmergencyAlert component for HealthConnect AI
 * Handles emergency health alerts and notifications
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { useHealthData } from '@/hooks/useHealthData';
import { useWebSocket } from '@/hooks/useWebSocket';
import type { HealthAlert, EmergencyContact } from '@/types/health';
import { 
  AlertTriangle, 
  Phone, 
  MessageSquare, 
  Clock, 
  MapPin, 
  Heart,
  Thermometer,
  Activity,
  User,
  X,
  Check
} from 'lucide-react';
import { clsx } from 'clsx';

interface EmergencyAlertProps {
  patientId?: string;
  emergencyContacts?: EmergencyContact[];
  onAlertAction?: (alertId: string, action: string) => void;
  className?: string;
}

interface EmergencyAlertModalProps {
  alert: HealthAlert;
  isOpen: boolean;
  onClose: () => void;
  onAction: (action: string) => void;
  emergencyContacts?: EmergencyContact[];
}

const EmergencyAlertModal: React.FC<EmergencyAlertModalProps> = ({
  alert,
  isOpen,
  onClose,
  onAction,
  emergencyContacts = []
}) => {
  const [selectedAction, setSelectedAction] = useState<string>('');
  const [isActioning, setIsActioning] = useState(false);

  const handleAction = async (action: string) => {
    setIsActioning(true);
    setSelectedAction(action);
    
    try {
      await onAction(action);
      if (action === 'acknowledge' || action === 'resolve') {
        onClose();
      }
    } catch (error) {
      console.error('Error performing action:', error);
    } finally {
      setIsActioning(false);
      setSelectedAction('');
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-600 bg-red-50 border-red-200';
      case 'high': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default: return 'text-blue-600 bg-blue-50 border-blue-200';
    }
  };

  const getAlertIcon = (alertType: string) => {
    switch (alertType) {
      case 'vital_signs_critical': return <Heart className="w-6 h-6" />;
      case 'device_malfunction': return <Activity className="w-6 h-6" />;
      case 'medication_reminder': return <Clock className="w-6 h-6" />;
      default: return <AlertTriangle className="w-6 h-6" />;
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Emergency Health Alert"
      size="lg"
      closeOnOverlayClick={false}
    >
      <div className="space-y-6">
        {/* Alert Header */}
        <div className={clsx('p-4 rounded-lg border-2', getSeverityColor(alert.severity))}>
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              {getAlertIcon(alert.alertType)}
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-lg">{alert.title}</h3>
              <p className="mt-1">{alert.message}</p>
              <div className="flex items-center space-x-4 mt-3 text-sm">
                <div className="flex items-center space-x-1">
                  <Clock className="w-4 h-4" />
                  <span>{new Date(alert.timestamp).toLocaleString()}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <AlertTriangle className="w-4 h-4" />
                  <span className="capitalize">{alert.severity} Priority</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {alert.actions?.map((action) => (
            <Button
              key={action.id}
              variant={action.action === 'call_emergency' ? 'danger' : 'default'}
              size="lg"
              onClick={() => handleAction(action.action)}
              disabled={isActioning}
              loading={isActioning && selectedAction === action.action}
              className="h-auto py-4"
            >
              <div className="flex flex-col items-center space-y-2">
                {action.action === 'call_emergency' && <Phone className="w-6 h-6" />}
                {action.action === 'contact_provider' && <MessageSquare className="w-6 h-6" />}
                {action.action === 'acknowledge' && <Check className="w-6 h-6" />}
                <span className="text-sm font-medium">{action.label}</span>
              </div>
            </Button>
          ))}
        </div>

        {/* Emergency Contacts */}
        {emergencyContacts.length > 0 && (
          <div>
            <h4 className="font-semibold mb-3">Emergency Contacts</h4>
            <div className="space-y-2">
              {emergencyContacts.slice(0, 3).map((contact) => (
                <div
                  key={contact.id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    <User className="w-5 h-5 text-gray-600" />
                    <div>
                      <p className="font-medium">{contact.name}</p>
                      <p className="text-sm text-gray-600">{contact.relationship}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => window.open(`tel:${contact.phoneNumber}`)}
                    >
                      <Phone className="w-4 h-4" />
                    </Button>
                    {contact.email && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => window.open(`mailto:${contact.email}`)}
                      >
                        <MessageSquare className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Location Services */}
        <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-start space-x-3">
            <MapPin className="w-5 h-5 text-blue-600 mt-0.5" />
            <div>
              <h4 className="font-medium text-blue-900">Location Services</h4>
              <p className="text-sm text-blue-700 mt-1">
                Your location may be shared with emergency services to provide faster assistance.
              </p>
              <Button
                variant="ghost"
                size="sm"
                className="mt-2 text-blue-600"
                onClick={() => {
                  if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(
                      (position) => {
                        console.log('Location:', position.coords);
                        // Handle location sharing
                      },
                      (error) => {
                        console.error('Location error:', error);
                      }
                    );
                  }
                }}
              >
                Share Location
              </Button>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-between pt-4 border-t">
          <Button
            variant="ghost"
            onClick={onClose}
            disabled={isActioning}
          >
            Dismiss
          </Button>
          <div className="flex items-center space-x-3">
            <Button
              variant="outline"
              onClick={() => handleAction('acknowledge')}
              disabled={isActioning || alert.acknowledged}
              loading={isActioning && selectedAction === 'acknowledge'}
            >
              {alert.acknowledged ? 'Acknowledged' : 'Acknowledge'}
            </Button>
            <Button
              variant="success"
              onClick={() => handleAction('resolve')}
              disabled={isActioning || alert.resolved}
              loading={isActioning && selectedAction === 'resolve'}
            >
              {alert.resolved ? 'Resolved' : 'Mark as Resolved'}
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  );
};

export const EmergencyAlert: React.FC<EmergencyAlertProps> = ({
  patientId,
  emergencyContacts = [],
  onAlertAction,
  className
}) => {
  const [selectedAlert, setSelectedAlert] = useState<HealthAlert | null>(null);
  const [showModal, setShowModal] = useState(false);

  const {
    activeAlerts,
    criticalAlerts,
    acknowledgeAlert,
    resolveAlert
  } = useHealthData({ patientId });

  const { sendEmergencyAlert } = useWebSocket({
    onEmergencyAlert: (alert) => {
      // Handle incoming emergency alerts
      console.log('Emergency alert received:', alert);
    }
  });

  // Auto-show modal for critical alerts
  useEffect(() => {
    const unacknowledgedCritical = criticalAlerts.find(alert => !alert.acknowledged);
    if (unacknowledgedCritical && !showModal) {
      setSelectedAlert(unacknowledgedCritical);
      setShowModal(true);
    }
  }, [criticalAlerts, showModal]);

  const handleAlertClick = (alert: HealthAlert) => {
    setSelectedAlert(alert);
    setShowModal(true);
  };

  const handleAlertAction = async (action: string) => {
    if (!selectedAlert) return;

    try {
      switch (action) {
        case 'acknowledge':
          await acknowledgeAlert(selectedAlert.id);
          break;
        case 'resolve':
          await resolveAlert(selectedAlert.id);
          break;
        case 'call_emergency':
          window.open('tel:911');
          break;
        case 'contact_provider':
          // Handle provider contact
          break;
        default:
          break;
      }
      
      onAlertAction?.(selectedAlert.id, action);
    } catch (error) {
      console.error('Error handling alert action:', error);
      throw error;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'border-red-500 bg-red-50';
      case 'high': return 'border-orange-500 bg-orange-50';
      case 'medium': return 'border-yellow-500 bg-yellow-50';
      default: return 'border-blue-500 bg-blue-50';
    }
  };

  if (activeAlerts.length === 0) {
    return (
      <Card className={clsx('border-green-200 bg-green-50', className)}>
        <CardContent className="p-4">
          <div className="flex items-center space-x-3">
            <Check className="w-6 h-6 text-green-600" />
            <div>
              <p className="font-medium text-green-900">All Clear</p>
              <p className="text-sm text-green-700">No active health alerts</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <div className={clsx('space-y-3', className)}>
        {activeAlerts.map((alert) => (
          <Card
            key={alert.id}
            className={clsx(
              'border-2 cursor-pointer transition-all duration-200 hover:shadow-lg',
              getSeverityColor(alert.severity)
            )}
            onClick={() => handleAlertClick(alert)}
          >
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3 flex-1">
                  <div className="flex-shrink-0 mt-1">
                    <AlertTriangle className={clsx('w-5 h-5', {
                      'text-red-600': alert.severity === 'critical',
                      'text-orange-600': alert.severity === 'high',
                      'text-yellow-600': alert.severity === 'medium',
                      'text-blue-600': alert.severity === 'low'
                    })} />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900">{alert.title}</h3>
                    <p className="text-sm text-gray-700 mt-1">{alert.message}</p>
                    <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                      <span>{new Date(alert.timestamp).toLocaleString()}</span>
                      <span className="capitalize">{alert.severity} Priority</span>
                      {alert.acknowledged && (
                        <span className="text-green-600">Acknowledged</span>
                      )}
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2 ml-4">
                  {alert.severity === 'critical' && (
                    <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Emergency Alert Modal */}
      {selectedAlert && (
        <EmergencyAlertModal
          alert={selectedAlert}
          isOpen={showModal}
          onClose={() => setShowModal(false)}
          onAction={handleAlertAction}
          emergencyContacts={emergencyContacts}
        />
      )}
    </>
  );
};

export default EmergencyAlert;
