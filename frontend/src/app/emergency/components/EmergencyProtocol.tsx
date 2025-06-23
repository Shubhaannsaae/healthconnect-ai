/**
 * EmergencyProtocol component
 * Step-by-step emergency response protocols
 */

'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { 
  AlertTriangle, 
  Heart, 
  Activity, 
  Brain,
  Shield,
  Phone,
  CheckCircle,
  Clock,
  ArrowRight
} from 'lucide-react';
import { clsx } from 'clsx';

interface EmergencyProtocolProps {
  emergencyType: string;
  onComplete?: () => void;
  className?: string;
}

interface ProtocolStep {
  id: string;
  title: string;
  description: string;
  action?: string;
  critical?: boolean;
  timeLimit?: number;
}

const emergencyProtocols: Record<string, {
  title: string;
  icon: React.ComponentType<any>;
  color: string;
  steps: ProtocolStep[];
}> = {
  cardiac: {
    title: 'Cardiac Emergency Protocol',
    icon: Heart,
    color: 'text-red-600',
    steps: [
      {
        id: 'assess',
        title: 'Assess Consciousness',
        description: 'Check if the person is responsive. Tap shoulders and shout "Are you okay?"',
        critical: true,
        timeLimit: 10
      },
      {
        id: 'call',
        title: 'Call Emergency Services',
        description: 'Call 911 immediately. State "cardiac emergency" and provide location.',
        action: 'call_911',
        critical: true,
        timeLimit: 30
      },
      {
        id: 'position',
        title: 'Position Patient',
        description: 'If conscious, help them sit comfortably. If unconscious, place on back on firm surface.',
        timeLimit: 60
      },
      {
        id: 'cpr_check',
        title: 'Check for Pulse',
        description: 'Check for pulse at neck (carotid) for 10 seconds. If no pulse, begin CPR.',
        critical: true,
        timeLimit: 10
      },
      {
        id: 'cpr',
        title: 'Begin CPR if Needed',
        description: 'Push hard and fast in center of chest, 100-120 compressions per minute.',
        critical: true
      }
    ]
  },
  respiratory: {
    title: 'Respiratory Emergency Protocol',
    icon: Activity,
    color: 'text-blue-600',
    steps: [
      {
        id: 'assess',
        title: 'Assess Breathing',
        description: 'Look, listen, and feel for breathing. Check for chest movement.',
        critical: true,
        timeLimit: 10
      },
      {
        id: 'position',
        title: 'Position for Breathing',
        description: 'Help patient sit upright or in tripod position to ease breathing.',
        timeLimit: 30
      },
      {
        id: 'clear_airway',
        title: 'Clear Airway',
        description: 'Remove any visible obstructions. Tilt head back slightly.',
        timeLimit: 15
      },
      {
        id: 'call',
        title: 'Call Emergency Services',
        description: 'Call 911 and report breathing difficulty. Stay on line for instructions.',
        action: 'call_911',
        critical: true
      },
      {
        id: 'monitor',
        title: 'Monitor Continuously',
        description: 'Watch for changes in breathing, consciousness, and skin color.',
        critical: true
      }
    ]
  }
};

export const EmergencyProtocol: React.FC<EmergencyProtocolProps> = ({
  emergencyType,
  onComplete,
  className
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<string[]>([]);
  const [timeRemaining, setTimeRemaining] = useState<number | null>(null);

  const protocol = emergencyProtocols[emergencyType];
  
  if (!protocol) {
    return (
      <Card className={className}>
        <CardContent className="p-8 text-center">
          <AlertTriangle className="w-16 h-16 mx-auto mb-4 text-gray-400" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Protocol Not Available
          </h3>
          <p className="text-gray-600">
            Emergency protocol for this type is not available.
          </p>
        </CardContent>
      </Card>
    );
  }

  const currentProtocolStep = protocol.steps[currentStep];

  React.useEffect(() => {
    if (currentProtocolStep?.timeLimit) {
      setTimeRemaining(currentProtocolStep.timeLimit);
      
      const timer = setInterval(() => {
        setTimeRemaining(prev => {
          if (prev && prev > 1) {
            return prev - 1;
          } else {
            clearInterval(timer);
            return null;
          }
        });
      }, 1000);

      return () => clearInterval(timer);
    }
    return undefined;
  }, [currentStep, currentProtocolStep]);

  const handleStepComplete = () => {
    if (!currentProtocolStep) return;
    const stepId = currentProtocolStep.id;
    setCompletedSteps(prev => [...prev, stepId]);
    
    if (currentStep < protocol.steps.length - 1) {
      setCurrentStep(prev => prev + 1);
    } else {
      onComplete?.();
    }
  };

  const handleAction = (action: string) => {
    if (!currentProtocolStep) return;
    switch (action) {
      case 'call_911':
        window.open('tel:911');
        break;
      default:
        break;
    }
  };

  const IconComponent = protocol.icon;

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <IconComponent className={clsx('w-6 h-6', protocol.color)} />
          <span>{protocol.title}</span>
        </CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Progress */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium">Progress</span>
            <span>{completedSteps.length} of {protocol.steps.length} completed</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-primary-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${(completedSteps.length / protocol.steps.length) * 100}%` }}
            />
          </div>
        </div>

        {/* Current Step */}
        <div className={clsx('p-6 rounded-lg border-2', {
          'border-red-500 bg-red-50': currentProtocolStep?.critical,
          'border-blue-500 bg-blue-50': !currentProtocolStep?.critical
        })}>
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Step {currentStep + 1}: {currentProtocolStep?.title}
              </h3>
              <p className="text-gray-700">{currentProtocolStep?.description}</p>
            </div>
            
            {timeRemaining && (
              <div className="ml-4 text-center">
                <div className={clsx('text-2xl font-bold', {
                  'text-red-600': timeRemaining <= 10,
                  'text-yellow-600': timeRemaining <= 30 && timeRemaining > 10,
                  'text-blue-600': timeRemaining > 30
                })}>
                  {timeRemaining}
                </div>
                <div className="text-xs text-gray-600">seconds</div>
              </div>
            )}
          </div>

          <div className="flex items-center space-x-3">
            {currentProtocolStep?.action && (
              <Button
                variant="danger"
                onClick={() => handleAction(currentProtocolStep.action!)}
                className="flex items-center space-x-2"
              >
                <Phone className="w-4 h-4" />
                <span>
                  {currentProtocolStep.action === 'call_911' ? 'Call 911 Now' : 'Take Action'}
                </span>
              </Button>
            )}
            
            <Button
              onClick={handleStepComplete}
              className="flex items-center space-x-2"
            >
              <CheckCircle className="w-4 h-4" />
              <span>Step Complete</span>
            </Button>
          </div>
        </div>

        {/* Step List */}
        <div className="space-y-2">
          <h4 className="font-medium text-gray-900">All Steps:</h4>
          {protocol.steps.map((step, index) => (
            <div
              key={step.id}
              className={clsx('flex items-center space-x-3 p-3 rounded-lg', {
                'bg-green-50 border border-green-200': completedSteps.includes(step.id),
                'bg-blue-50 border border-blue-200': index === currentStep,
                'bg-gray-50': index > currentStep && !completedSteps.includes(step.id)
              })}
            >
              <div className={clsx('w-6 h-6 rounded-full flex items-center justify-center text-sm font-medium', {
                'bg-green-600 text-white': completedSteps.includes(step.id),
                'bg-blue-600 text-white': index === currentStep,
                'bg-gray-300 text-gray-600': index > currentStep && !completedSteps.includes(step.id)
              })}>
                {completedSteps.includes(step.id) ? (
                  <CheckCircle className="w-4 h-4" />
                ) : (
                  index + 1
                )}
              </div>
              
              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  <span className={clsx('font-medium', {
                    'text-green-900': completedSteps.includes(step.id),
                    'text-blue-900': index === currentStep,
                    'text-gray-700': index > currentStep && !completedSteps.includes(step.id)
                  })}>
                    {step.title}
                  </span>
                  {step.critical && (
                    <span className="px-2 py-1 bg-red-100 text-red-800 text-xs rounded-full">
                      CRITICAL
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-600">{step.description}</p>
              </div>
              
              {index === currentStep && (
                <ArrowRight className="w-5 h-5 text-blue-600" />
              )}
            </div>
          ))}
        </div>

        {/* Emergency Contacts */}
        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <h4 className="font-medium text-yellow-900 mb-2">Important Numbers:</h4>
          <div className="space-y-1 text-sm text-yellow-800">
            <div>Emergency Services: 911</div>
            <div>Poison Control: 1-800-222-1222</div>
            <div>Crisis Hotline: 988</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default EmergencyProtocol;
