/**
 * Custom React hook for WebSocket functionality
 * Provides real-time communication for HealthConnect AI
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { webSocketManager } from '@/lib/websocket';
import type { WebSocketEventHandlers, ConsultationMessage, DeviceDataMessage, SignalingMessage } from '@/types/consultation';

interface UseWebSocketOptions {
  autoConnect?: boolean;
  token?: string;
  onConnect?: () => void;
  onDisconnect?: (reason: string) => void;
  onError?: (error: Error) => void;
  onMessage?: (message: any) => void;
  onConsultationMessage?: (message: ConsultationMessage) => void;
  onDeviceData?: (data: DeviceDataMessage) => void;
  onSignaling?: (signal: SignalingMessage) => void;
  onEmergencyAlert?: (alert: any) => void;
}

interface UseWebSocketReturn {
  connectionState: string;
  isConnected: boolean;
  error: string | null;
  
  // Actions
  connect: (token?: string) => Promise<void>;
  disconnect: () => void;
  send: (event: string, data: any) => Promise<void>;
  subscribe: (channel: string) => Promise<void>;
  unsubscribe: (channel: string) => Promise<void>;
  
  // Consultation methods
  joinConsultation: (consultationId: string, userRole: string) => Promise<void>;
  leaveConsultation: (consultationId: string) => Promise<void>;
  sendConsultationMessage: (message: Omit<ConsultationMessage, 'id' | 'timestamp'>) => Promise<void>;
  sendSignaling: (signal: Omit<SignalingMessage, 'timestamp'>) => Promise<void>;
  
  // Device methods
  sendDeviceData: (deviceData: DeviceDataMessage) => Promise<void>;
  
  // Emergency methods
  sendEmergencyAlert: (alert: any) => Promise<void>;
}

export const useWebSocket = (options: UseWebSocketOptions = {}): UseWebSocketReturn => {
  const [connectionState, setConnectionState] = useState(webSocketManager.getConnectionState());
  const [isConnected, setIsConnected] = useState(webSocketManager.isConnected());
  const [error, setError] = useState<string | null>(null);
  
  const handlersRef = useRef<WebSocketEventHandlers>({});

  // Update handlers when options change
  useEffect(() => {
    handlersRef.current = {
      onConnect: () => {
        setConnectionState('connected');
        setIsConnected(true);
        setError(null);
        options.onConnect?.();
      },
      onDisconnect: (reason) => {
        setConnectionState('disconnected');
        setIsConnected(false);
        options.onDisconnect?.(reason);
      },
      onError: (error) => {
        setError(error.message);
        options.onError?.(error);
      },
      onReconnect: (attemptNumber) => {
        setConnectionState('connected');
        setIsConnected(true);
        setError(null);
      },
      onReconnectError: (error) => {
        setError(error.message);
      },
      onMessage: options.onMessage,
      onConsultationMessage: options.onConsultationMessage,
      onDeviceData: options.onDeviceData,
      onSignaling: options.onSignaling,
      onEmergencyAlert: options.onEmergencyAlert
    };

    webSocketManager.setHandlers(handlersRef.current);
  }, [
    options.onConnect,
    options.onDisconnect,
    options.onError,
    options.onMessage,
    options.onConsultationMessage,
    options.onDeviceData,
    options.onSignaling,
    options.onEmergencyAlert
  ]);

  // Auto-connect if enabled
  useEffect(() => {
    if (options.autoConnect && !isConnected) {
      connect(options.token).catch(console.error);
    }
  }, [options.autoConnect, options.token, isConnected]);

  // Connect to WebSocket
  const connect = useCallback(async (token?: string): Promise<void> => {
    try {
      setError(null);
      await webSocketManager.connect(token);
    } catch (error) {
      setError((error as Error).message);
      throw error;
    }
  }, []);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    webSocketManager.disconnect();
    setConnectionState('disconnected');
    setIsConnected(false);
  }, []);

  // Send message
  const send = useCallback(async (event: string, data: any): Promise<void> => {
    try {
      await webSocketManager.send(event, data);
    } catch (error) {
      setError((error as Error).message);
      throw error;
    }
  }, []);

  // Subscribe to channel
  const subscribe = useCallback(async (channel: string): Promise<void> => {
    try {
      await webSocketManager.subscribe(channel);
    } catch (error) {
      setError((error as Error).message);
      throw error;
    }
  }, []);

  // Unsubscribe from channel
  const unsubscribe = useCallback(async (channel: string): Promise<void> => {
    try {
      await webSocketManager.unsubscribe(channel);
    } catch (error) {
      setError((error as Error).message);
      throw error;
    }
  }, []);

  // Join consultation
  const joinConsultation = useCallback(async (consultationId: string, userRole: string): Promise<void> => {
    try {
      await webSocketManager.joinConsultation(consultationId, userRole);
    } catch (error) {
      setError((error as Error).message);
      throw error;
    }
  }, []);

  // Leave consultation
  const leaveConsultation = useCallback(async (consultationId: string): Promise<void> => {
    try {
      await webSocketManager.leaveConsultation(consultationId);
    } catch (error) {
      setError((error as Error).message);
      throw error;
    }
  }, []);

  // Send consultation message
  const sendConsultationMessage = useCallback(async (message: Omit<ConsultationMessage, 'id' | 'timestamp'>): Promise<void> => {
    try {
      await webSocketManager.sendConsultationMessage(message);
    } catch (error) {
      setError((error as Error).message);
      throw error;
    }
  }, []);

  // Send signaling
  const sendSignaling = useCallback(async (signal: Omit<SignalingMessage, 'timestamp'>): Promise<void> => {
    try {
      await webSocketManager.sendSignaling(signal);
    } catch (error) {
      setError((error as Error).message);
      throw error;
    }
  }, []);

  // Send device data
  const sendDeviceData = useCallback(async (deviceData: DeviceDataMessage): Promise<void> => {
    try {
      await webSocketManager.sendDeviceData(deviceData);
    } catch (error) {
      setError((error as Error).message);
      throw error;
    }
  }, []);

  // Send emergency alert
  const sendEmergencyAlert = useCallback(async (alert: any): Promise<void> => {
    try {
      await webSocketManager.sendEmergencyAlert(alert);
    } catch (error) {
      setError((error as Error).message);
      throw error;
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (isConnected) {
        disconnect();
      }
    };
  }, []);

  return {
    connectionState,
    isConnected,
    error,
    
    // Actions
    connect,
    disconnect,
    send,
    subscribe,
    unsubscribe,
    
    // Consultation methods
    joinConsultation,
    leaveConsultation,
    sendConsultationMessage,
    sendSignaling,
    
    // Device methods
    sendDeviceData,
    
    // Emergency methods
    sendEmergencyAlert
  };
};

export default useWebSocket;
