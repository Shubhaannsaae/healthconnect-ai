/**
 * WebSocket client implementation for HealthConnect AI
 * Following WebSocket API standards and real-time communication best practices
 */

import { io, Socket } from 'socket.io-client';
import { awsConfig } from './aws-config';
import type { 
  SignalingMessage, 
  ConsultationMessage, 
  DeviceDataMessage,
  WebSocketMessage 
} from '@/types/consultation';

export interface WebSocketConfig {
  url: string;
  autoConnect: boolean;
  reconnection: boolean;
  reconnectionAttempts: number;
  reconnectionDelay: number;
  timeout: number;
  forceNew: boolean;
}

export interface WebSocketEventHandlers {
  onConnect?: () => void;
  onDisconnect?: (reason: string) => void;
  onError?: (error: Error) => void;
  onReconnect?: (attemptNumber: number) => void;
  onReconnectError?: (error: Error) => void;
  onMessage?: (message: any) => void;
  onConsultationMessage?: (message: ConsultationMessage) => void;
  onDeviceData?: (data: DeviceDataMessage) => void;
  onSignaling?: (signal: SignalingMessage) => void;
  onEmergencyAlert?: (alert: any) => void;
}

class WebSocketManager {
  private socket: Socket | null = null;
  private config: WebSocketConfig;
  private handlers: WebSocketEventHandlers = {};
  private connectionState: 'disconnected' | 'connecting' | 'connected' | 'reconnecting' = 'disconnected';
  private reconnectAttempts = 0;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private messageQueue: any[] = [];
  private subscriptions = new Set<string>();

  constructor(config?: Partial<WebSocketConfig>) {
    this.config = {
      url: awsConfig.webSocketUrl,
      autoConnect: false,
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      timeout: 20000,
      forceNew: false,
      ...config
    };
  }

  /**
   * Connect to WebSocket server
   */
  connect(token?: string): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.socket?.connected) {
        resolve();
        return;
      }

      this.connectionState = 'connecting';

      const socketOptions: any = {
        transports: ['websocket', 'polling'],
        timeout: this.config.timeout,
        forceNew: this.config.forceNew,
        reconnection: this.config.reconnection,
        reconnectionAttempts: this.config.reconnectionAttempts,
        reconnectionDelay: this.config.reconnectionDelay,
        autoConnect: false
      };

      // Add authentication token if provided
      if (token) {
        socketOptions.auth = { token };
        socketOptions.query = { token };
      }

      try {
        this.socket = io(this.config.url, socketOptions);
        this.setupEventHandlers(resolve, reject);
        this.socket.connect();
      } catch (error) {
        this.connectionState = 'disconnected';
        reject(error);
      }
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.connectionState = 'disconnected';
    this.clearHeartbeat();
    this.messageQueue = [];
    this.subscriptions.clear();
  }

  /**
   * Send message through WebSocket
   */
  send(event: string, data: any): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this.socket?.connected) {
        // Queue message if not connected
        this.messageQueue.push({ event, data, resolve, reject });
        return;
      }

      try {
        this.socket.emit(event, data, (response: any) => {
          if (response?.error) {
            reject(new Error(response.error));
          } else {
            resolve(response);
          }
        });
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Subscribe to a specific channel or room
   */
  subscribe(channel: string): Promise<void> {
    this.subscriptions.add(channel);
    return this.send('subscribe', { channel });
  }

  /**
   * Unsubscribe from a channel or room
   */
  unsubscribe(channel: string): Promise<void> {
    this.subscriptions.delete(channel);
    return this.send('unsubscribe', { channel });
  }

  /**
   * Join a consultation room
   */
  joinConsultation(consultationId: string, userRole: string): Promise<void> {
    return this.send('join_consultation', {
      consultationId,
      userRole,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Leave a consultation room
   */
  leaveConsultation(consultationId: string): Promise<void> {
    return this.send('leave_consultation', {
      consultationId,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Send consultation message
   */
  sendConsultationMessage(message: Omit<ConsultationMessage, 'id' | 'timestamp'>): Promise<void> {
    return this.send('consultation_message', {
      ...message,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Send WebRTC signaling data
   */
  sendSignaling(signal: Omit<SignalingMessage, 'timestamp'>): Promise<void> {
    return this.send('webrtc_signal', {
      ...signal,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Send device data
   */
  sendDeviceData(deviceData: DeviceDataMessage): Promise<void> {
    return this.send('device_data', deviceData);
  }

  /**
   * Send emergency alert
   */
  sendEmergencyAlert(alert: any): Promise<void> {
    return this.send('emergency_alert', {
      ...alert,
      timestamp: new Date().toISOString(),
      urgency: 'high'
    });
  }

  /**
   * Get connection state
   */
  getConnectionState(): string {
    return this.connectionState;
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.socket?.connected || false;
  }

  /**
   * Set event handlers
   */
  setHandlers(handlers: WebSocketEventHandlers): void {
    this.handlers = { ...this.handlers, ...handlers };
  }

  /**
   * Get socket instance
   */
  getSocket(): Socket | null {
    return this.socket;
  }

  /**
   * Setup event handlers for socket
   */
  private setupEventHandlers(resolve: () => void, reject: (error: Error) => void): void {
    if (!this.socket) return;

    // Connection events
    this.socket.on('connect', () => {
      this.connectionState = 'connected';
      this.reconnectAttempts = 0;
      this.startHeartbeat();
      this.processMessageQueue();
      this.resubscribeToChannels();
      this.handlers.onConnect?.();
      resolve();
    });

    this.socket.on('disconnect', (reason: string) => {
      this.connectionState = 'disconnected';
      this.clearHeartbeat();
      this.handlers.onDisconnect?.(reason);
    });

    this.socket.on('connect_error', (error: Error) => {
      this.connectionState = 'disconnected';
      this.handlers.onError?.(error);
      reject(error);
    });

    this.socket.on('reconnect', (attemptNumber: number) => {
      this.connectionState = 'connected';
      this.reconnectAttempts = 0;
      this.handlers.onReconnect?.(attemptNumber);
    });

    this.socket.on('reconnect_attempt', () => {
      this.connectionState = 'reconnecting';
      this.reconnectAttempts++;
    });

    this.socket.on('reconnect_error', (error: Error) => {
      this.handlers.onReconnectError?.(error);
    });

    // Application-specific events
    this.socket.on('message', (message: any) => {
      this.handlers.onMessage?.(message);
    });

    this.socket.on('consultation_message', (message: ConsultationMessage) => {
      this.handlers.onConsultationMessage?.(message);
    });

    this.socket.on('device_data', (data: DeviceDataMessage) => {
      this.handlers.onDeviceData?.(data);
    });

    this.socket.on('webrtc_signal', (signal: SignalingMessage) => {
      this.handlers.onSignaling?.(signal);
    });

    this.socket.on('emergency_alert', (alert: any) => {
      this.handlers.onEmergencyAlert?.(alert);
    });

    // Heartbeat response
    this.socket.on('pong', () => {
      // Heartbeat acknowledged
    });

    // Error handling
    this.socket.on('error', (error: Error) => {
      console.error('WebSocket error:', error);
      this.handlers.onError?.(error);
    });
  }

  /**
   * Start heartbeat to keep connection alive
   */
  private startHeartbeat(): void {
    this.clearHeartbeat();
    this.heartbeatInterval = setInterval(() => {
      if (this.socket?.connected) {
        this.socket.emit('ping');
      }
    }, 30000); // Send ping every 30 seconds
  }

  /**
   * Clear heartbeat interval
   */
  private clearHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * Process queued messages when connection is restored
   */
  private processMessageQueue(): void {
    while (this.messageQueue.length > 0) {
      const { event, data, resolve, reject } = this.messageQueue.shift()!;
      this.send(event, data).then(resolve).catch(reject);
    }
  }

  /**
   * Resubscribe to channels after reconnection
   */
  private resubscribeToChannels(): void {
    this.subscriptions.forEach(channel => {
      this.subscribe(channel).catch(error => {
        console.error(`Failed to resubscribe to channel ${channel}:`, error);
      });
    });
  }
}

// Create singleton instance
export const webSocketManager = new WebSocketManager();

// Utility functions
export const connectWebSocket = (token?: string): Promise<void> => {
  return webSocketManager.connect(token);
};

export const disconnectWebSocket = (): void => {
  webSocketManager.disconnect();
};

export const sendWebSocketMessage = (event: string, data: any): Promise<void> => {
  return webSocketManager.send(event, data);
};

export const subscribeToChannel = (channel: string): Promise<void> => {
  return webSocketManager.subscribe(channel);
};

export const unsubscribeFromChannel = (channel: string): Promise<void> => {
  return webSocketManager.unsubscribe(channel);
};

// React hook for WebSocket
export const useWebSocket = (handlers?: WebSocketEventHandlers) => {
  const [connectionState, setConnectionState] = useState(webSocketManager.getConnectionState());
  const [isConnected, setIsConnected] = useState(webSocketManager.isConnected());

  useEffect(() => {
    if (handlers) {
      webSocketManager.setHandlers({
        ...handlers,
        onConnect: () => {
          setConnectionState('connected');
          setIsConnected(true);
          handlers.onConnect?.();
        },
        onDisconnect: (reason) => {
          setConnectionState('disconnected');
          setIsConnected(false);
          handlers.onDisconnect?.(reason);
        },
        onReconnect: (attemptNumber) => {
          setConnectionState('connected');
          setIsConnected(true);
          handlers.onReconnect?.(attemptNumber);
        }
      });
    }

    // Cleanup on unmount
    return () => {
      // Don't disconnect on unmount as other components might be using it
    };
  }, [handlers]);

  return {
    connectionState,
    isConnected,
    connect: webSocketManager.connect.bind(webSocketManager),
    disconnect: webSocketManager.disconnect.bind(webSocketManager),
    send: webSocketManager.send.bind(webSocketManager),
    subscribe: webSocketManager.subscribe.bind(webSocketManager),
    unsubscribe: webSocketManager.unsubscribe.bind(webSocketManager),
    joinConsultation: webSocketManager.joinConsultation.bind(webSocketManager),
    leaveConsultation: webSocketManager.leaveConsultation.bind(webSocketManager),
    sendConsultationMessage: webSocketManager.sendConsultationMessage.bind(webSocketManager),
    sendSignaling: webSocketManager.sendSignaling.bind(webSocketManager),
    sendDeviceData: webSocketManager.sendDeviceData.bind(webSocketManager),
    sendEmergencyAlert: webSocketManager.sendEmergencyAlert.bind(webSocketManager)
  };
};

export default webSocketManager;
