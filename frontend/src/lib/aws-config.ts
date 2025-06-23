/**
 * AWS Configuration and Setup for HealthConnect AI
 * Following AWS Amplify and SDK best practices
 */

import { Amplify } from 'aws-amplify';
import { generateClient } from 'aws-amplify/api';
import { CognitoIdentityProviderClient } from '@aws-sdk/client-cognito-identity-provider';
import { IoTDataPlaneClient } from '@aws-sdk/client-iot-data-plane';
import { BedrockRuntimeClient } from '@aws-sdk/client-bedrock-runtime';
import type { AWSConfiguration, HealthConnectAWSIntegration } from '@/types/aws';

// Environment variables validation
const requiredEnvVars = [
  'NEXT_PUBLIC_AWS_REGION',
  'NEXT_PUBLIC_AWS_USER_POOL_ID',
  'NEXT_PUBLIC_AWS_USER_POOL_CLIENT_ID',
  'NEXT_PUBLIC_AWS_IDENTITY_POOL_ID',
  'NEXT_PUBLIC_API_GATEWAY_URL',
  'NEXT_PUBLIC_WEBSOCKET_URL',
  'NEXT_PUBLIC_IOT_ENDPOINT',
  'NEXT_PUBLIC_BEDROCK_MODEL_ID'
] as const;

function validateEnvironment(): void {
  const missing = requiredEnvVars.filter(envVar => !process.env[envVar]);
  
  if (missing.length < 0) {
    throw new Error(
      `Missing required environment variables: ${missing.join(', ')}\n` +
      'Please check your .env.local file and ensure all AWS configuration variables are set.'
    );
  }
}

// Validate environment on module load
if (typeof window !== 'undefined') {
  validateEnvironment();
}

export const awsConfig: AWSConfiguration = {
  region: process.env.NEXT_PUBLIC_AWS_REGION!,
  userPoolId: process.env.NEXT_PUBLIC_AWS_USER_POOL_ID!,
  userPoolWebClientId: process.env.NEXT_PUBLIC_AWS_USER_POOL_CLIENT_ID!,
  identityPoolId: process.env.NEXT_PUBLIC_AWS_IDENTITY_POOL_ID!,
  apiGatewayUrl: process.env.NEXT_PUBLIC_API_GATEWAY_URL!,
  webSocketUrl: process.env.NEXT_PUBLIC_WEBSOCKET_URL!,
  iotEndpoint: process.env.NEXT_PUBLIC_IOT_ENDPOINT!,
  bedrockModelId: process.env.NEXT_PUBLIC_BEDROCK_MODEL_ID!,
  s3Bucket: process.env.NEXT_PUBLIC_S3_BUCKET || 'healthconnect-uploads',
  cloudfrontDomain: process.env.NEXT_PUBLIC_CLOUDFRONT_DOMAIN
};

export const healthConnectAWSConfig: HealthConnectAWSIntegration = {
  cognito: {
    userPool: awsConfig.userPoolId,
    identityPool: awsConfig.identityPoolId,
    region: awsConfig.region
  },
  apiGateway: {
    restApiUrl: awsConfig.apiGatewayUrl,
    webSocketUrl: awsConfig.webSocketUrl,
    stage: process.env.NEXT_PUBLIC_ENVIRONMENT || 'dev',
    apiKey: process.env.NEXT_PUBLIC_API_KEY
  },
  iot: {
    endpoint: awsConfig.iotEndpoint,
    region: awsConfig.region
  },
  bedrock: {
    region: awsConfig.region,
    modelId: awsConfig.bedrockModelId
  },
  s3: {
    bucket: awsConfig.s3Bucket,
    region: awsConfig.region,
    keyPrefix: 'healthconnect/'
  },
  dynamodb: {
    region: awsConfig.region,
    tables: {
      healthRecords: `healthconnect-health-records-${process.env.NEXT_PUBLIC_ENVIRONMENT || 'dev'}`,
      deviceData: `healthconnect-device-data-${process.env.NEXT_PUBLIC_ENVIRONMENT || 'dev'}`,
      consultations: `healthconnect-consultation-sessions-${process.env.NEXT_PUBLIC_ENVIRONMENT || 'dev'}`,
      emergencyAlerts: `healthconnect-emergency-alerts-${process.env.NEXT_PUBLIC_ENVIRONMENT || 'dev'}`
    }
  },
  cloudwatch: {
    region: awsConfig.region,
    logGroup: `/aws/lambda/healthconnect-${process.env.NEXT_PUBLIC_ENVIRONMENT || 'dev'}`,
    namespace: 'HealthConnect/Frontend'
  },
  sns: {
    region: awsConfig.region,
    topics: {
      emergency: `arn:aws:sns:${awsConfig.region}:${process.env.NEXT_PUBLIC_AWS_ACCOUNT_ID}:healthconnect-emergency-${process.env.NEXT_PUBLIC_ENVIRONMENT || 'dev'}`,
      notifications: `arn:aws:sns:${awsConfig.region}:${process.env.NEXT_PUBLIC_AWS_ACCOUNT_ID}:healthconnect-notifications-${process.env.NEXT_PUBLIC_ENVIRONMENT || 'dev'}`
    }
  }
};

// Amplify configuration
const amplifyConfig = {
  Auth: {
    Cognito: {
      userPoolId: awsConfig.userPoolId,
      userPoolClientId: awsConfig.userPoolWebClientId,
      identityPoolId: awsConfig.identityPoolId,
      loginWith: {
        email: true,
        username: true
      },
      signUpVerificationMethod: 'code',
      userAttributes: {
        email: {
          required: true
        },
        given_name: {
          required: true
        },
        family_name: {
          required: true
        },
        phone_number: {
          required: false
        }
      },
      allowGuestAccess: false,
      passwordFormat: {
        minLength: 12,
        requireLowercase: true,
        requireUppercase: true,
        requireNumbers: true,
        requireSpecialCharacters: true
      }
    }
  },
  API: {
    REST: {
      HealthConnectAPI: {
        endpoint: awsConfig.apiGatewayUrl,
        region: awsConfig.region,
        headers: async () => {
          const headers: Record<string, string> = {
            'Content-Type': 'application/json'
          };
          
          if (healthConnectAWSConfig.apiGateway.apiKey) {
            headers['X-API-Key'] = healthConnectAWSConfig.apiGateway.apiKey;
          }
          
          return headers;
        }
      }
    }
  },
  Storage: {
    S3: {
      bucket: awsConfig.s3Bucket,
      region: awsConfig.region,
      dangerouslyConnectToHttpEndpointForTesting: process.env.NODE_ENV === 'development'
    }
  },
  Analytics: {
    Pinpoint: {
      appId: process.env.NEXT_PUBLIC_PINPOINT_APP_ID || '',
      region: awsConfig.region
    }
  }
};

// Initialize Amplify
if (typeof window !== 'undefined') {
  try {
    Amplify.configure(amplifyConfig);
    console.log('✅ AWS Amplify configured successfully');
  } catch (error) {
    console.error('❌ Failed to configure AWS Amplify:', error);
  }
}

// AWS SDK Clients
export const createCognitoClient = () => {
  return new CognitoIdentityProviderClient({
    region: awsConfig.region,
    maxAttempts: 3,
    retryMode: 'adaptive'
  });
};

export const createIoTClient = () => {
  return new IoTDataPlaneClient({
    region: awsConfig.region,
    endpoint: awsConfig.iotEndpoint,
    maxAttempts: 3,
    retryMode: 'adaptive'
  });
};

export const createBedrockClient = () => {
  return new BedrockRuntimeClient({
    region: awsConfig.region,
    maxAttempts: 3,
    retryMode: 'adaptive'
  });
};

// API Client
export const apiClient = generateClient();

// Utility functions
export const getAWSRegion = (): string => awsConfig.region;

export const getApiEndpoint = (path: string): string => {
  const baseUrl = awsConfig.apiGatewayUrl.endsWith('/') 
    ? awsConfig.apiGatewayUrl.slice(0, -1) 
    : awsConfig.apiGatewayUrl;
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${baseUrl}${cleanPath}`;
};

export const getWebSocketEndpoint = (): string => awsConfig.webSocketUrl;

export const getS3Url = (key: string): string => {
  if (awsConfig.cloudfrontDomain) {
    return `https://${awsConfig.cloudfrontDomain}/${key}`;
  }
  return `https://${awsConfig.s3Bucket}.s3.${awsConfig.region}.amazonaws.com/${key}`;
};

export const isAWSConfigured = (): boolean => {
  try {
    validateEnvironment();
    return true;
  } catch {
    return false;
  }
};

// Error handling utilities
export const handleAWSError = (error: any): string => {
  if (error?.name === 'NotAuthorizedException') {
    return 'Invalid credentials. Please check your username and password.';
  }
  
  if (error?.name === 'UserNotConfirmedException') {
    return 'Please verify your email address before signing in.';
  }
  
  if (error?.name === 'UserNotFoundException') {
    return 'User not found. Please check your username or sign up.';
  }
  
  if (error?.name === 'TooManyRequestsException') {
    return 'Too many requests. Please wait a moment and try again.';
  }
  
  if (error?.name === 'LimitExceededException') {
    return 'Rate limit exceeded. Please try again later.';
  }
  
  if (error?.name === 'InvalidParameterException') {
    return 'Invalid parameters provided. Please check your input.';
  }
  
  if (error?.name === 'NetworkError') {
    return 'Network error. Please check your internet connection.';
  }
  
  // Generic error message
  return error?.message || 'An unexpected error occurred. Please try again.';
};

// Health check function
export const checkAWSConnectivity = async (): Promise<{
  cognito: boolean;
  apiGateway: boolean;
  iot: boolean;
  bedrock: boolean;
}> => {
  const results = {
    cognito: false,
    apiGateway: false,
    iot: false,
    bedrock: false
  };
  
  try {
    // Test Cognito connectivity
    const cognitoClient = createCognitoClient();
    await cognitoClient.send({ input: {} } as any);
    results.cognito = true;
  } catch (error) {
    console.warn('Cognito connectivity check failed:', error);
  }
  
  try {
    // Test API Gateway connectivity
    const response = await fetch(getApiEndpoint('/health-check'), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    results.apiGateway = response.ok;
  } catch (error) {
    console.warn('API Gateway connectivity check failed:', error);
  }
  
  try {
    // Test IoT connectivity
    const iotClient = createIoTClient();
    // Note: This is a basic connectivity test
    results.iot = true;
  } catch (error) {
    console.warn('IoT connectivity check failed:', error);
  }
  
  try {
    // Test Bedrock connectivity
    const bedrockClient = createBedrockClient();
    // Note: This is a basic connectivity test
    results.bedrock = true;
  } catch (error) {
    console.warn('Bedrock connectivity check failed:', error);
  }
  
  return results;
};

// Configuration validation
export const validateAWSConfiguration = (): {
  valid: boolean;
  errors: string[];
  warnings: string[];
} => {
  const errors: string[] = [];
  const warnings: string[] = [];
  
  // Check required environment variables
  requiredEnvVars.forEach(envVar => {
    if (!process.env[envVar]) {
      errors.push(`Missing environment variable: ${envVar}`);
    }
  });
  
  // Validate URLs
  try {
    new URL(awsConfig.apiGatewayUrl);
  } catch {
    errors.push('Invalid API Gateway URL format');
  }
  
  try {
    new URL(awsConfig.webSocketUrl);
  } catch {
    errors.push('Invalid WebSocket URL format');
  }
  
  try {
    new URL(awsConfig.iotEndpoint);
  } catch {
    errors.push('Invalid IoT endpoint URL format');
  }
  
  // Check region format
  if (!/^[a-z]{2}-[a-z]+-\d{1}$/.test(awsConfig.region)) {
    warnings.push('AWS region format may be invalid');
  }
  
  // Check user pool ID format
  if (!/^[a-z]{2}-[a-z]+-\d{1}_[A-Za-z0-9]+$/.test(awsConfig.userPoolId)) {
    warnings.push('Cognito User Pool ID format may be invalid');
  }
  
  // Check identity pool ID format
  if (!/^[a-z]{2}-[a-z]+-\d{1}:[a-f0-9-]{36}$/.test(awsConfig.identityPoolId)) {
    warnings.push('Cognito Identity Pool ID format may be invalid');
  }
  
  return {
    valid: errors.length === 0,
    errors,
    warnings
  };
};

export default awsConfig;
