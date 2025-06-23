/**
 * Providers component for HealthConnect AI
 * Wraps the app with necessary providers and context
 */

'use client';

import React, { useEffect } from 'react';
import { useAuthStore } from '@/store/authStore';
import { isAWSConfigured } from '@/lib/aws-config';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

interface ProvidersProps {
  children: React.ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  const { initialize, loading } = useAuthStore();

  useEffect(() => {
    // Initialize AWS configuration and auth state
    if (isAWSConfigured()) {
      initialize();
    } else {
      console.warn('AWS configuration is incomplete. Please check environment variables.');
    }
  }, [initialize]);

  // Show loading spinner while initializing
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <LoadingSpinner size="xl" variant="primary" />
          <p className="mt-4 text-lg font-medium text-gray-900">Initializing HealthConnect AI...</p>
          <p className="mt-2 text-sm text-gray-600">Setting up your secure healthcare environment</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
