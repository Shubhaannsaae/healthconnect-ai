/**
 * ConsultationCard component
 * Displays consultation information in card format
 */

'use client';

import React from 'react';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import type { ConsultationSession } from '@/types/consultation';
import { 
  Video, 
  Calendar, 
  Clock, 
  User,
  Phone,
  MessageSquare
} from 'lucide-react';
import { clsx } from 'clsx';
import Link from 'next/link';

interface ConsultationCardProps {
  consultation: ConsultationSession;
  onJoin?: () => void;
  onCancel?: () => void;
  onReschedule?: () => void;
  className?: string;
}

export const ConsultationCard: React.FC<ConsultationCardProps> = ({
  consultation,
  onJoin,
  onCancel,
  onReschedule,
  className
}) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'scheduled': return 'bg-blue-100 text-blue-800';
      case 'in_progress': return 'bg-green-100 text-green-800';
      case 'completed': return 'bg-gray-100 text-gray-800';
      case 'cancelled': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  // Removed: const provider = consultation.participants?.find(p => p.role === 'provider');
  const isUpcoming = consultation.status === 'scheduled';
  const isActive = consultation.status === 'in_progress';

  return (
    <Card className={clsx('hover:shadow-md transition-shadow', className)}>
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-3 mb-3">
              <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center">
                <User className="w-6 h-6 text-primary-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">
                  {"Healthcare Provider"}
                </h3>
                <p className="text-sm text-gray-600">{consultation.consultationType}</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4 text-sm text-gray-600 mb-4">
              <div className="flex items-center space-x-1">
                <Calendar className="w-4 h-4" />
                <span>{consultation.scheduledTime ? new Date(consultation.scheduledTime).toLocaleDateString() : "N/A"}</span>
              </div>
              <div className="flex items-center space-x-1">
                <Clock className="w-4 h-4" />
                <span>{consultation.scheduledTime ? new Date(consultation.scheduledTime).toLocaleTimeString() : "N/A"}</span>
              </div>
              {consultation.duration && (
                <div className="flex items-center space-x-1">
                  <Clock className="w-4 h-4" />
                  <span>{consultation.duration} min</span>
                </div>
              )}
            </div>

            {consultation.notes && (
              <p className="text-sm text-gray-700 mb-4">{consultation.notes}</p>
            )}
          </div>
          
          <div className="flex flex-col items-end space-y-3">
            <span className={clsx('px-3 py-1 rounded-full text-sm font-medium', getStatusColor(consultation.status))}>
              {consultation.status.replace('_', ' ').toUpperCase()}
            </span>
            
            <div className="flex space-x-2">
              {isActive && (
                <Link href={`/consultation/${consultation.id}`}>
                  <Button size="sm">
                    <Video className="w-4 h-4 mr-1" />
                    Join
                  </Button>
                </Link>
              )}
              
              {isUpcoming && (
                <>
                  <Button variant="outline" size="sm" onClick={onReschedule}>
                    Reschedule
                  </Button>
                  <Button size="sm" onClick={onJoin}>
                    <Video className="w-4 h-4 mr-1" />
                    Join Early
                  </Button>
                </>
              )}
              
              {consultation.status === 'completed' && (
                <Button variant="outline" size="sm">
                  <MessageSquare className="w-4 h-4 mr-1" />
                  View Summary
                </Button>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default ConsultationCard;
