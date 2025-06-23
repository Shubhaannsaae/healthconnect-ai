/**
 * AWS-specific TypeScript definitions for HealthConnect AI
 * Following AWS SDK and service specifications
 */

import { CognitoUser, CognitoUserSession } from 'amazon-cognito-identity-js';

export interface AWSConfiguration {
  region: string;
  userPoolId: string;
  userPoolWebClientId: string;
  identityPoolId: string;
  apiGatewayUrl: string;
  webSocketUrl: string;
  iotEndpoint: string;
  bedrockModelId: string;
  s3Bucket: string;
  cloudfrontDomain?: string;
}

export interface CognitoAuthState {
  isAuthenticated: boolean;
  user: CognitoUser | null;
  session: CognitoUserSession | null;
  userAttributes: CognitoUserAttributes | null;
  loading: boolean;
  error: string | null;
}

export interface CognitoUserAttributes {
  sub: string;
  email: string;
  email_verified: boolean;
  given_name: string;
  family_name: string;
  phone_number?: string;
  phone_number_verified?: boolean;
  'custom:user_type': 'patient' | 'provider' | 'admin';
  'custom:organization'?: string;
  'custom:license_number'?: string;
  'custom:specialty'?: string;
  preferred_username?: string;
  picture?: string;
  locale?: string;
  zoneinfo?: string;
}

export interface CognitoSignUpData {
  username: string;
  password: string;
  email: string;
  givenName: string;
  familyName: string;
  phoneNumber?: string;
  userType: 'patient' | 'provider' | 'admin';
  organization?: string;
  licenseNumber?: string;
  specialty?: string;
}

export interface CognitoSignInData {
  username: string;
  password: string;
  rememberMe?: boolean;
}

export interface CognitoMFAData {
  challengeName: string;
  challengeParameters: Record<string, string>;
  session: string;
}

export interface BedrockRequest {
  modelId: string;
  contentType: string;
  accept: string;
  body: string;
}

export interface BedrockResponse {
  contentType: string;
  body: Uint8Array;
  metadata?: {
    requestId: string;
    httpStatusCode: number;
    httpHeaders: Record<string, string>;
  };
}

export interface BedrockModelInvocation {
  modelId: string;
  prompt: string;
  maxTokens?: number;
  temperature?: number;
  topP?: number;
  stopSequences?: string[];
  anthropicVersion?: string;
}

export interface BedrockHealthAnalysisRequest {
  patientData: {
    vitalSigns?: any;
    symptoms?: string[];
    medicalHistory?: string[];
    currentMedications?: string[];
    age?: number;
    gender?: string;
  };
  analysisType: 'symptom_assessment' | 'risk_analysis' | 'drug_interaction' | 'health_insights';
  context?: string;
  urgencyLevel?: 'low' | 'medium' | 'high' | 'critical';
}

export interface BedrockHealthAnalysisResponse {
  analysis: {
    summary: string;
    findings: string[];
    recommendations: string[];
    riskLevel: 'low' | 'medium' | 'high' | 'critical';
    confidence: number;
    urgentCareNeeded: boolean;
    followUpRecommended: boolean;
  };
  medicalInsights: {
    possibleConditions: Array<{
      condition: string;
      probability: number;
      reasoning: string;
    }>;
    drugInteractions: Array<{
      medications: string[];
      severity: 'minor' | 'moderate' | 'major';
      description: string;
    }>;
    vitalSignsAnalysis?: {
      abnormalValues: string[];
      trends: string[];
      concerns: string[];
    };
  };
  disclaimer: string;
  generatedAt: string;
  modelVersion: string;
}

export interface IoTDeviceMessage {
  deviceId: string;
  timestamp: string;
  messageType: 'telemetry' | 'status' | 'alert' | 'command_response';
  payload: Record<string, any>;
  qos: 0 | 1 | 2;
  retain?: boolean;
  messageId?: string;
}

export interface IoTDeviceCommand {
  deviceId: string;
  command: string;
  parameters?: Record<string, any>;
  timeout?: number;
  qos?: 0 | 1 | 2;
  correlationId?: string;
}

export interface IoTDeviceStatus {
  deviceId: string;
  connected: boolean;
  lastSeen: string;
  version: string;
  batteryLevel?: number;
  signalStrength?: number;
  location?: {
    latitude: number;
    longitude: number;
    accuracy: number;
  };
  metadata?: Record<string, any>;
}

export interface S3UploadRequest {
  file: File;
  key: string;
  bucket?: string;
  contentType?: string;
  metadata?: Record<string, string>;
  tags?: Record<string, string>;
  serverSideEncryption?: 'AES256' | 'aws:kms';
  kmsKeyId?: string;
  acl?: 'private' | 'public-read' | 'public-read-write';
}

export interface S3UploadResponse {
  success: boolean;
  key: string;
  bucket: string;
  location: string;
  etag: string;
  versionId?: string;
  error?: {
    code: string;
    message: string;
  };
}

export interface S3PresignedUrlRequest {
  key: string;
  bucket?: string;
  operation: 'getObject' | 'putObject' | 'deleteObject';
  expiresIn?: number; // seconds
  conditions?: Array<any>;
  fields?: Record<string, string>;
}

export interface CloudWatchMetric {
  namespace: string;
  metricName: string;
  dimensions?: Array<{
    name: string;
    value: string;
  }>;
  value: number;
  unit: 'Count' | 'Bytes' | 'Seconds' | 'Percent' | 'None';
  timestamp?: Date;
}

export interface CloudWatchLog {
  logGroupName: string;
  logStreamName: string;
  timestamp: number;
  message: string;
  level: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR' | 'FATAL';
  metadata?: Record<string, any>;
}

export interface LambdaInvocation {
  functionName: string;
  invocationType: 'RequestResponse' | 'Event' | 'DryRun';
  payload: any;
  qualifier?: string;
  clientContext?: string;
}

export interface LambdaResponse {
  statusCode: number;
  functionError?: string;
  logResult?: string;
  payload: any;
  executedVersion: string;
}

export interface APIGatewayRequest {
  httpMethod: string;
  path: string;
  pathParameters?: Record<string, string>;
  queryStringParameters?: Record<string, string>;
  headers: Record<string, string>;
  body?: string;
  isBase64Encoded: boolean;
  requestContext: {
    requestId: string;
    stage: string;
    resourcePath: string;
    httpMethod: string;
    requestTime: string;
    requestTimeEpoch: number;
    identity: {
      sourceIp: string;
      userAgent: string;
      cognitoIdentityId?: string;
      cognitoAuthenticationProvider?: string;
      cognitoAuthenticationType?: string;
    };
    authorizer?: {
      claims?: Record<string, string>;
      principalId?: string;
    };
  };
}

export interface APIGatewayResponse {
  statusCode: number;
  headers?: Record<string, string>;
  multiValueHeaders?: Record<string, string[]>;
  body: string;
  isBase64Encoded?: boolean;
}

export interface WebSocketMessage {
  requestContext: {
    connectionId: string;
    routeKey: string;
    messageId: string;
    eventType: 'CONNECT' | 'MESSAGE' | 'DISCONNECT';
    requestTime: string;
    requestTimeEpoch: number;
    stage: string;
    connectedAt: number;
    identity: {
      sourceIp: string;
      userAgent: string;
    };
  };
  body?: string;
  isBase64Encoded: boolean;
}

export interface DynamoDBItem {
  [key: string]: any;
}

export interface DynamoDBQueryParams {
  TableName: string;
  IndexName?: string;
  KeyConditionExpression: string;
  FilterExpression?: string;
  ExpressionAttributeNames?: Record<string, string>;
  ExpressionAttributeValues: Record<string, any>;
  ProjectionExpression?: string;
  ScanIndexForward?: boolean;
  Limit?: number;
  ExclusiveStartKey?: Record<string, any>;
  ConsistentRead?: boolean;
}

export interface DynamoDBScanParams {
  TableName: string;
  IndexName?: string;
  FilterExpression?: string;
  ExpressionAttributeNames?: Record<string, string>;
  ExpressionAttributeValues?: Record<string, any>;
  ProjectionExpression?: string;
  Limit?: number;
  ExclusiveStartKey?: Record<string, any>;
  ConsistentRead?: boolean;
  Segment?: number;
  TotalSegments?: number;
}

export interface DynamoDBResponse<T = DynamoDBItem> {
  Items?: T[];
  Count: number;
  ScannedCount: number;
  LastEvaluatedKey?: Record<string, any>;
  ConsumedCapacity?: {
    TableName: string;
    CapacityUnits: number;
    Table?: {
      CapacityUnits: number;
    };
    LocalSecondaryIndexes?: Record<string, {
      CapacityUnits: number;
    }>;
    GlobalSecondaryIndexes?: Record<string, {
      CapacityUnits: number;
    }>;
  };
}

export interface SNSMessage {
  topicArn: string;
  message: string;
  subject?: string;
  messageAttributes?: Record<string, {
    DataType: 'String' | 'Number' | 'Binary';
    StringValue?: string;
    BinaryValue?: Uint8Array;
  }>;
  messageGroupId?: string;
  messageDeduplicationId?: string;
}

export interface SESEmail {
  source: string;
  destination: {
    toAddresses: string[];
    ccAddresses?: string[];
    bccAddresses?: string[];
  };
  message: {
    subject: {
      data: string;
      charset?: string;
    };
    body: {
      text?: {
        data: string;
        charset?: string;
      };
      html?: {
        data: string;
        charset?: string;
      };
    };
  };
  replyToAddresses?: string[];
  returnPath?: string;
  tags?: Array<{
    name: string;
    value: string;
  }>;
}

export interface KinesisRecord {
  partitionKey: string;
  data: Uint8Array | string;
  explicitHashKey?: string;
  sequenceNumberForOrdering?: string;
}

export interface KinesisStreamRecord {
  eventSource: string;
  eventVersion: string;
  eventID: string;
  eventName: string;
  invokeIdentityArn: string;
  awsRegion: string;
  eventSourceARN: string;
  kinesis: {
    kinesisSchemaVersion: string;
    partitionKey: string;
    sequenceNumber: string;
    data: string;
    approximateArrivalTimestamp: number;
  };
}

// AWS Error types
export interface AWSError {
  name: string;
  message: string;
  code: string;
  statusCode?: number;
  retryable?: boolean;
  requestId?: string;
  cfId?: string;
  extendedRequestId?: string;
  region?: string;
  hostname?: string;
  retryDelay?: number;
  time?: Date;
}

// AWS SDK Configuration
export interface AWSCredentials {
  accessKeyId: string;
  secretAccessKey: string;
  sessionToken?: string;
  expiration?: Date;
}

export interface AWSConfig {
  region: string;
  credentials?: AWSCredentials;
  endpoint?: string;
  maxRetries?: number;
  retryDelayOptions?: {
    customBackoff?: (retryCount: number) => number;
  };
  httpOptions?: {
    timeout?: number;
    connectTimeout?: number;
  };
  logger?: {
    log: (message: string) => void;
  };
  systemClockOffset?: number;
  signatureVersion?: string;
  signatureCache?: boolean;
  dynamoDbCrc32?: boolean;
  useAccelerateEndpoint?: boolean;
  clientSideMonitoring?: boolean;
  endpointDiscoveryEnabled?: boolean;
  endpointCacheSize?: number;
  hostPrefixEnabled?: boolean;
  stsRegionalEndpoints?: 'legacy' | 'regional';
}

// Health-specific AWS integrations
export interface HealthConnectAWSIntegration {
  cognito: {
    userPool: string;
    identityPool: string;
    region: string;
  };
  apiGateway: {
    restApiUrl: string;
    webSocketUrl: string;
    stage: string;
    apiKey?: string;
  };
  iot: {
    endpoint: string;
    region: string;
    thingName?: string;
  };
  bedrock: {
    region: string;
    modelId: string;
    roleArn?: string;
  };
  s3: {
    bucket: string;
    region: string;
    keyPrefix?: string;
  };
  dynamodb: {
    region: string;
    tables: {
      healthRecords: string;
      deviceData: string;
      consultations: string;
      emergencyAlerts: string;
    };
  };
  cloudwatch: {
    region: string;
    logGroup: string;
    namespace: string;
  };
  sns: {
    region: string;
    topics: {
      emergency: string;
      notifications: string;
    };
  };
}
