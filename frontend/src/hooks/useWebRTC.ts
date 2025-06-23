/**
 * Custom React hook for WebRTC functionality
 * Provides video calling capabilities for HealthConnect AI consultations
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { webRTCManager } from '@/lib/webrtc';
import type { WebRTCConfig, WebRTCEventHandlers, MediaConstraints } from '@/types/consultation';

interface UseWebRTCOptions {
  config?: Partial<WebRTCConfig>;
  autoInitialize?: boolean;
  onLocalStream?: (stream: MediaStream) => void;
  onRemoteStream?: (stream: MediaStream, peerId: string) => void;
  onConnectionStateChange?: (state: RTCPeerConnectionState, peerId: string) => void;
  onError?: (error: Error) => void;
}

interface UseWebRTCReturn {
  localStream: MediaStream | null;
  remoteStreams: Map<string, MediaStream>;
  isInitialized: boolean;
  isVideoEnabled: boolean;
  isAudioEnabled: boolean;
  isScreenSharing: boolean;
  connectionStates: Map<string, RTCPeerConnectionState>;
  
  // Actions
  initializeMedia: (constraints?: Partial<MediaConstraints>) => Promise<MediaStream>;
  createPeerConnection: (peerId: string) => Promise<RTCPeerConnection>;
  createOffer: (peerId: string) => Promise<RTCSessionDescriptionInit>;
  createAnswer: (peerId: string) => Promise<RTCSessionDescriptionInit>;
  setRemoteDescription: (peerId: string, description: RTCSessionDescriptionInit) => Promise<void>;
  addIceCandidate: (peerId: string, candidate: RTCIceCandidateInit) => Promise<void>;
  toggleVideo: () => void;
  toggleAudio: () => void;
  switchCamera: () => Promise<void>;
  startScreenShare: () => Promise<void>;
  stopScreenShare: () => Promise<void>;
  startRecording: () => void;
  stopRecording: () => void;
  cleanup: () => void;
  
  // Utilities
  getConnectionStats: (peerId: string) => Promise<RTCStatsReport | null>;
  getMediaDevices: () => Promise<MediaDeviceInfo[]>;
}

export const useWebRTC = (options: UseWebRTCOptions = {}): UseWebRTCReturn => {
  const [localStream, setLocalStream] = useState<MediaStream | null>(null);
  const [remoteStreams, setRemoteStreams] = useState<Map<string, MediaStream>>(new Map());
  const [isInitialized, setIsInitialized] = useState(false);
  const [isVideoEnabled, setIsVideoEnabled] = useState(true);
  const [isAudioEnabled, setIsAudioEnabled] = useState(true);
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  const [connectionStates, setConnectionStates] = useState<Map<string, RTCPeerConnectionState>>(new Map());
  
  const handlersRef = useRef<WebRTCEventHandlers>({});

  // Update handlers when options change
  useEffect(() => {
    handlersRef.current = {
      onLocalStream: (stream) => {
        setLocalStream(stream);
        options.onLocalStream?.(stream);
      },
      onRemoteStream: (stream, peerId) => {
        setRemoteStreams(prev => new Map(prev.set(peerId, stream)));
        options.onRemoteStream?.(stream, peerId);
      },
      onConnectionStateChange: (state, peerId) => {
        setConnectionStates(prev => new Map(prev.set(peerId, state)));
        options.onConnectionStateChange?.(state, peerId);
      },
      onError: options.onError
    };

    webRTCManager.setHandlers(handlersRef.current);
  }, [options.onLocalStream, options.onRemoteStream, options.onConnectionStateChange, options.onError]);

  // Initialize WebRTC if autoInitialize is true
  useEffect(() => {
    if (options.autoInitialize && !isInitialized) {
      initializeMedia().catch(console.error);
    }
  }, [options.autoInitialize, isInitialized]);

  // Initialize media stream
  const initializeMedia = useCallback(async (constraints?: Partial<MediaConstraints>): Promise<MediaStream> => {
    try {
      const stream = await webRTCManager.initializeLocalStream(constraints);
      setIsInitialized(true);
      return stream;
    } catch (error) {
      options.onError?.(error as Error);
      throw error;
    }
  }, [options.onError]);

  // Create peer connection
  const createPeerConnection = useCallback(async (peerId: string): Promise<RTCPeerConnection> => {
    try {
      return await webRTCManager.createPeerConnection(peerId);
    } catch (error) {
      options.onError?.(error as Error);
      throw error;
    }
  }, [options.onError]);

  // Create offer
  const createOffer = useCallback(async (peerId: string): Promise<RTCSessionDescriptionInit> => {
    try {
      return await webRTCManager.createOffer(peerId);
    } catch (error) {
      options.onError?.(error as Error);
      throw error;
    }
  }, [options.onError]);

  // Create answer
  const createAnswer = useCallback(async (peerId: string): Promise<RTCSessionDescriptionInit> => {
    try {
      return await webRTCManager.createAnswer(peerId);
    } catch (error) {
      options.onError?.(error as Error);
      throw error;
    }
  }, [options.onError]);

  // Set remote description
  const setRemoteDescription = useCallback(async (peerId: string, description: RTCSessionDescriptionInit): Promise<void> => {
    try {
      await webRTCManager.setRemoteDescription(peerId, description);
    } catch (error) {
      options.onError?.(error as Error);
      throw error;
    }
  }, [options.onError]);

  // Add ICE candidate
  const addIceCandidate = useCallback(async (peerId: string, candidate: RTCIceCandidateInit): Promise<void> => {
    try {
      await webRTCManager.addIceCandidate(peerId, candidate);
    } catch (error) {
      options.onError?.(error as Error);
      throw error;
    }
  }, [options.onError]);

  // Toggle video
  const toggleVideo = useCallback(() => {
    const newState = !isVideoEnabled;
    webRTCManager.toggleVideo(newState);
    setIsVideoEnabled(newState);
  }, [isVideoEnabled]);

  // Toggle audio
  const toggleAudio = useCallback(() => {
    const newState = !isAudioEnabled;
    webRTCManager.toggleAudio(newState);
    setIsAudioEnabled(newState);
  }, [isAudioEnabled]);

  // Switch camera
  const switchCamera = useCallback(async (): Promise<void> => {
    try {
      await webRTCManager.switchCamera();
    } catch (error) {
      options.onError?.(error as Error);
      throw error;
    }
  }, [options.onError]);

  // Start screen share
  const startScreenShare = useCallback(async (): Promise<void> => {
    try {
      await webRTCManager.startScreenShare();
      setIsScreenSharing(true);
    } catch (error) {
      options.onError?.(error as Error);
      throw error;
    }
  }, [options.onError]);

  // Stop screen share
  const stopScreenShare = useCallback(async (): Promise<void> => {
    try {
      await webRTCManager.stopScreenShare();
      setIsScreenSharing(false);
    } catch (error) {
      options.onError?.(error as Error);
      throw error;
    }
  }, [options.onError]);

  // Start recording
  const startRecording = useCallback(() => {
    webRTCManager.startRecording();
  }, []);

  // Stop recording
  const stopRecording = useCallback(() => {
    webRTCManager.stopRecording();
  }, []);

  // Cleanup
  const cleanup = useCallback(() => {
    webRTCManager.cleanup();
    setLocalStream(null);
    setRemoteStreams(new Map());
    setIsInitialized(false);
    setIsVideoEnabled(true);
    setIsAudioEnabled(true);
    setIsScreenSharing(false);
    setConnectionStates(new Map());
  }, []);

  // Get connection stats
  const getConnectionStats = useCallback(async (peerId: string): Promise<RTCStatsReport | null> => {
    return await webRTCManager.getConnectionStats(peerId);
  }, []);

  // Get media devices
  const getMediaDevices = useCallback(async (): Promise<MediaDeviceInfo[]> => {
    return await webRTCManager.getMediaDevices();
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanup();
    };
  }, [cleanup]);

  return {
    localStream,
    remoteStreams,
    isInitialized,
    isVideoEnabled,
    isAudioEnabled,
    isScreenSharing,
    connectionStates,
    
    // Actions
    initializeMedia,
    createPeerConnection,
    createOffer,
    createAnswer,
    setRemoteDescription,
    addIceCandidate,
    toggleVideo,
    toggleAudio,
    switchCamera,
    startScreenShare,
    stopScreenShare,
    startRecording,
    stopRecording,
    cleanup,
    
    // Utilities
    getConnectionStats,
    getMediaDevices
  };
};

export default useWebRTC;
