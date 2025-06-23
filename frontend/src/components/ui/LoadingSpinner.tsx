/**
 * Production-grade Loading Spinner component for HealthConnect AI
 * Accessible loading indicators with various styles
 */

import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { clsx } from 'clsx';

const spinnerVariants = cva(
  'animate-spin',
  {
    variants: {
      variant: {
        default: 'border-gray-300 border-t-primary-600',
        primary: 'border-primary-200 border-t-primary-600',
        success: 'border-success-200 border-t-success-600',
        warning: 'border-warning-200 border-t-warning-600',
        danger: 'border-danger-200 border-t-danger-600',
        white: 'border-white/30 border-t-white',
        dots: 'text-primary-600',
        pulse: 'bg-primary-600'
      },
      size: {
        xs: 'w-3 h-3',
        sm: 'w-4 h-4',
        md: 'w-6 h-6',
        lg: 'w-8 h-8',
        xl: 'w-12 h-12'
      }
    },
    defaultVariants: {
      variant: 'default',
      size: 'md'
    }
  }
);

export interface LoadingSpinnerProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof spinnerVariants> {
  label?: string;
  showLabel?: boolean;
  type?: 'spinner' | 'dots' | 'pulse' | 'bars';
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  className,
  variant,
  size,
  label = 'Loading...',
  showLabel = false,
  type = 'spinner',
  ...props
}) => {
  const renderSpinner = () => {
    switch (type) {
      case 'spinner':
        return (
          <div
            className={clsx(
              spinnerVariants({ variant, size }),
              'rounded-full border-2',
              className
            )}
            role="status"
            aria-label={label}
            {...props}
          />
        );

      case 'dots':
        return (
          <div
            className={clsx('flex space-x-1', className)}
            role="status"
            aria-label={label}
            {...props}
          >
            {[0, 1, 2].map((index) => (
              <div
                key={index}
                className={clsx(
                  'rounded-full animate-pulse',
                  {
                    'w-1 h-1': size === 'xs',
                    'w-1.5 h-1.5': size === 'sm',
                    'w-2 h-2': size === 'md',
                    'w-3 h-3': size === 'lg',
                    'w-4 h-4': size === 'xl'
                  },
                  {
                    'bg-gray-400': variant === 'default',
                    'bg-primary-600': variant === 'primary',
                    'bg-success-600': variant === 'success',
                    'bg-warning-600': variant === 'warning',
                    'bg-danger-600': variant === 'danger',
                    'bg-white': variant === 'white'
                  }
                )}
                style={{
                  animationDelay: `${index * 0.2}s`,
                  animationDuration: '1s'
                }}
              />
            ))}
          </div>
        );

      case 'pulse':
        return (
          <div
            className={clsx(
              'rounded-full animate-pulse',
              spinnerVariants({ variant, size }),
              className
            )}
            role="status"
            aria-label={label}
            {...props}
          />
        );

      case 'bars':
        return (
          <div
            className={clsx('flex items-end space-x-1', className)}
            role="status"
            aria-label={label}
            {...props}
          >
            {[0, 1, 2, 3].map((index) => (
              <div
                key={index}
                className={clsx(
                  'animate-pulse',
                  {
                    'w-0.5': size === 'xs',
                    'w-1': size === 'sm',
                    'w-1.5': size === 'md',
                    'w-2': size === 'lg',
                    'w-3': size === 'xl'
                  },
                  {
                    'h-2': size === 'xs',
                    'h-3': size === 'sm',
                    'h-4': size === 'md',
                    'h-6': size === 'lg',
                    'h-8': size === 'xl'
                  },
                  {
                    'bg-gray-400': variant === 'default',
                    'bg-primary-600': variant === 'primary',
                    'bg-success-600': variant === 'success',
                    'bg-warning-600': variant === 'warning',
                    'bg-danger-600': variant === 'danger',
                    'bg-white': variant === 'white'
                  }
                )}
                style={{
                  animationDelay: `${index * 0.15}s`,
                  animationDuration: '1.2s'
                }}
              />
            ))}
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="flex flex-col items-center justify-center space-y-2">
      {renderSpinner()}
      {showLabel && (
        <span className="text-sm text-gray-600 font-medium">{label}</span>
      )}
    </div>
  );
};

// Specialized loading components for different contexts
export const PageLoader: React.FC<{ message?: string }> = ({ 
  message = 'Loading page...' 
}) => (
  <div className="flex flex-col items-center justify-center min-h-screen space-y-4">
    <LoadingSpinner size="xl" variant="primary" type="spinner" />
    <div className="text-center">
      <p className="text-lg font-medium text-gray-900">{message}</p>
      <p className="text-sm text-gray-500 mt-1">Please wait while we load your content</p>
    </div>
  </div>
);

export const InlineLoader: React.FC<{ 
  message?: string;
  size?: 'sm' | 'md' | 'lg';
}> = ({ 
  message = 'Loading...', 
  size = 'sm' 
}) => (
  <div className="flex items-center space-x-2">
    <LoadingSpinner size={size} variant="primary" type="spinner" />
    <span className="text-sm text-gray-600">{message}</span>
  </div>
);

export const CardLoader: React.FC<{ lines?: number }> = ({ lines = 3 }) => (
  <div className="animate-pulse">
    <div className="h-4 bg-gray-200 rounded w-3/4 mb-3"></div>
    {Array.from({ length: lines }).map((_, index) => (
      <div
        key={index}
        className={clsx(
          'h-3 bg-gray-200 rounded mb-2',
          index === lines - 1 ? 'w-1/2' : 'w-full'
        )}
      ></div>
    ))}
  </div>
);

export const TableLoader: React.FC<{ rows?: number; columns?: number }> = ({ 
  rows = 5, 
  columns = 4 
}) => (
  <div className="animate-pulse">
    {Array.from({ length: rows }).map((_, rowIndex) => (
      <div key={rowIndex} className="flex space-x-4 mb-3">
        {Array.from({ length: columns }).map((_, colIndex) => (
          <div
            key={colIndex}
            className="h-4 bg-gray-200 rounded flex-1"
          ></div>
        ))}
      </div>
    ))}
  </div>
);

export const ChartLoader: React.FC<{ height?: number }> = ({ height = 200 }) => (
  <div className="animate-pulse">
    <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
    <div 
      className="bg-gray-200 rounded"
      style={{ height: `${height}px` }}
    ></div>
  </div>
);

export { LoadingSpinner, spinnerVariants };
export default LoadingSpinner;
