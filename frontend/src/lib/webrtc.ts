/**
 * WebRTC implementation for HealthConnect AI video consultations
 * Following WebRTC standards and best practices for healthcare applications
 */

import type { 
    WebRTCConfiguration, 
    MediaConstraints, 
    PeerConnectionState,
    SignalingMessage 
  } from '@/types/consultation';
  
  export interface WebRTCConfig {
    iceServers: RTCIceServer[];
    mediaConstraints: MediaConstraints;
    enableDataChannel: boolean;
    enableRecording: boolean;
    recordingOptions?: {
      mimeType: string;
      videoBitsPerSecond: number;
      audioBitsPerSecond: number;
    };
  }
  
  export interface WebRTCEventHandlers {
    onLocalStream?: (stream: MediaStream) => void;
    onRemoteStream?: (stream: MediaStream, peerId: string) => void;
    onDataChannelMessage?: (message: any, peerId: string) => void;
    onConnectionStateChange?: (state: RTCPeerConnectionState, peerId: string) => void;
    onIceCandidate?: (candidate: RTCIceCandidate, peerId: string) => void;
    onError?: (error: Error) => void;
    onRecordingStart?: () => void;
    onRecordingStop?: (blob: Blob) => void;
  }
  
  class WebRTCManager {
    private localStream: MediaStream | null = null;
    private peerConnections = new Map<string, RTCPeerConnection>();
    private dataChannels = new Map<string, RTCDataChannel>();
    private remoteStreams = new Map<string, MediaStream>();
    private config: WebRTCConfig;
    private handlers: WebRTCEventHandlers = {};
    private mediaRecorder: MediaRecorder | null = null;
    private recordedChunks: Blob[] = [];
  
    constructor(config?: Partial<WebRTCConfig>) {
      this.config = {
        iceServers: [
          { urls: 'stun:stun.l.google.com:19302' },
          { urls: 'stun:stun1.l.google.com:19302' },
          { urls: 'stun:stun2.l.google.com:19302' }
        ],
        mediaConstraints: {
          video: {
            width: { min: 640, ideal: 1280, max: 1920 },
            height: { min: 480, ideal: 720, max: 1080 },
            frameRate: { min: 15, ideal: 30, max: 60 }
          },
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
            sampleRate: 48000,
            channelCount: 2
          }
        },
        enableDataChannel: true,
        enableRecording: false,
        recordingOptions: {
          mimeType: 'video/webm;codecs=vp9,opus',
          videoBitsPerSecond: 2500000,
          audioBitsPerSecond: 128000
        },
        ...config
      };
    }
  
    /**
     * Initialize local media stream
     */
    async initializeLocalStream(constraints?: Partial<MediaConstraints>): Promise<MediaStream> {
      try {
        const mediaConstraints = {
          video: { ...this.config.mediaConstraints.video, ...constraints?.video },
          audio: { ...this.config.mediaConstraints.audio, ...constraints?.audio }
        };
  
        this.localStream = await navigator.mediaDevices.getUserMedia(mediaConstraints);
        this.handlers.onLocalStream?.(this.localStream);
  
        return this.localStream;
      } catch (error) {
        const errorMessage = this.getMediaErrorMessage(error);
        this.handlers.onError?.(new Error(errorMessage));
        throw error;
      }
    }
  
    /**
     * Create peer connection for a specific peer
     */
    async createPeerConnection(peerId: string): Promise<RTCPeerConnection> {
      const peerConnection = new RTCPeerConnection({
        iceServers: this.config.iceServers,
        iceCandidatePoolSize: 10
      });
  
      // Add local stream tracks
      if (this.localStream) {
        this.localStream.getTracks().forEach(track => {
          peerConnection.addTrack(track, this.localStream!);
        });
      }
  
      // Handle remote stream
      peerConnection.ontrack = (event) => {
        const [remoteStream] = event.streams;
        this.remoteStreams.set(peerId, remoteStream);
        this.handlers.onRemoteStream?.(remoteStream, peerId);
      };
  
      // Handle ICE candidates
      peerConnection.onicecandidate = (event) => {
        if (event.candidate) {
          this.handlers.onIceCandidate?.(event.candidate, peerId);
        }
      };
  
      // Handle connection state changes
      peerConnection.onconnectionstatechange = () => {
        this.handlers.onConnectionStateChange?.(peerConnection.connectionState, peerId);
      };
  
      // Create data channel if enabled
      if (this.config.enableDataChannel) {
        const dataChannel = peerConnection.createDataChannel('healthconnect', {
          ordered: true
        });
        
        dataChannel.onopen = () => {
          console.log(`Data channel opened for peer ${peerId}`);
        };
        
        dataChannel.onmessage = (event) => {
          this.handlers.onDataChannelMessage?.(JSON.parse(event.data), peerId);
        };
        
        this.dataChannels.set(peerId, dataChannel);
      }
  
      // Handle incoming data channels
      peerConnection.ondatachannel = (event) => {
        const channel = event.channel;
        channel.onmessage = (event) => {
          this.handlers.onDataChannelMessage?.(JSON.parse(event.data), peerId);
        };
        this.dataChannels.set(peerId, channel);
      };
  
      this.peerConnections.set(peerId, peerConnection);
      return peerConnection;
    }
  
    /**
     * Create offer for peer connection
     */
    async createOffer(peerId: string): Promise<RTCSessionDescriptionInit> {
      const peerConnection = this.peerConnections.get(peerId);
      if (!peerConnection) {
        throw new Error(`Peer connection not found for ${peerId}`);
      }
  
      const offer = await peerConnection.createOffer({
        offerToReceiveAudio: true,
        offerToReceiveVideo: true
      });
  
      await peerConnection.setLocalDescription(offer);
      return offer;
    }
  
    /**
     * Create answer for peer connection
     */
    async createAnswer(peerId: string): Promise<RTCSessionDescriptionInit> {
      const peerConnection = this.peerConnections.get(peerId);
      if (!peerConnection) {
        throw new Error(`Peer connection not found for ${peerId}`);
      }
  
      const answer = await peerConnection.createAnswer();
      await peerConnection.setLocalDescription(answer);
      return answer;
    }
  
    /**
     * Set remote description
     */
    async setRemoteDescription(peerId: string, description: RTCSessionDescriptionInit): Promise<void> {
      const peerConnection = this.peerConnections.get(peerId);
      if (!peerConnection) {
        throw new Error(`Peer connection not found for ${peerId}`);
      }
  
      await peerConnection.setRemoteDescription(description);
    }
  
    /**
     * Add ICE candidate
     */
    async addIceCandidate(peerId: string, candidate: RTCIceCandidateInit): Promise<void> {
      const peerConnection = this.peerConnections.get(peerId);
      if (!peerConnection) {
        throw new Error(`Peer connection not found for ${peerId}`);
      }
  
      await peerConnection.addIceCandidate(candidate);
    }
  
    /**
     * Send data through data channel
     */
    sendData(peerId: string, data: any): void {
      const dataChannel = this.dataChannels.get(peerId);
      if (dataChannel && dataChannel.readyState === 'open') {
        dataChannel.send(JSON.stringify(data));
      } else {
        console.warn(`Data channel not available for peer ${peerId}`);
      }
    }
  
    /**
     * Toggle video track
     */
    toggleVideo(enabled: boolean): void {
      if (this.localStream) {
        const videoTracks = this.localStream.getVideoTracks();
        videoTracks.forEach(track => {
          track.enabled = enabled;
        });
      }
    }
  
    /**
     * Toggle audio track
     */
    toggleAudio(enabled: boolean): void {
      if (this.localStream) {
        const audioTracks = this.localStream.getAudioTracks();
        audioTracks.forEach(track => {
          track.enabled = enabled;
        });
      }
    }
  
    /**
     * Switch camera (front/back)
     */
    async switchCamera(): Promise<void> {
      if (!this.localStream) return;
  
      const videoTrack = this.localStream.getVideoTracks()[0];
      if (!videoTrack) return;
  
      const currentFacingMode = videoTrack.getSettings().facingMode;
      const newFacingMode = currentFacingMode === 'user' ? 'environment' : 'user';
  
      try {
        const newStream = await navigator.mediaDevices.getUserMedia({
          video: {
            ...this.config.mediaConstraints.video,
            facingMode: newFacingMode
          },
          audio: this.config.mediaConstraints.audio
        });
  
        // Replace video track in all peer connections
        const newVideoTrack = newStream.getVideoTracks()[0];
        this.peerConnections.forEach(async (peerConnection) => {
          const sender = peerConnection.getSenders().find(s => 
            s.track && s.track.kind === 'video'
          );
          if (sender) {
            await sender.replaceTrack(newVideoTrack);
          }
        });
  
        // Stop old video track
        videoTrack.stop();
  
        // Update local stream
        this.localStream.removeTrack(videoTrack);
        this.localStream.addTrack(newVideoTrack);
  
        this.handlers.onLocalStream?.(this.localStream);
      } catch (error) {
        this.handlers.onError?.(new Error('Failed to switch camera'));
      }
    }
  
    /**
     * Start screen sharing
     */
    async startScreenShare(): Promise<void> {
      try {
        const screenStream = await navigator.mediaDevices.getDisplayMedia({
          video: true,
          audio: true
        });
  
        const videoTrack = screenStream.getVideoTracks()[0];
  
        // Replace video track in all peer connections
        this.peerConnections.forEach(async (peerConnection) => {
          const sender = peerConnection.getSenders().find(s => 
            s.track && s.track.kind === 'video'
          );
          if (sender) {
            await sender.replaceTrack(videoTrack);
          }
        });
  
        // Handle screen share end
        videoTrack.onended = () => {
          this.stopScreenShare();
        };
  
      } catch (error) {
        this.handlers.onError?.(new Error('Failed to start screen sharing'));
      }
    }
  
    /**
     * Stop screen sharing
     */
    async stopScreenShare(): Promise<void> {
      if (!this.localStream) return;
  
      try {
        // Get camera stream again
        const cameraStream = await navigator.mediaDevices.getUserMedia({
          video: this.config.mediaConstraints.video,
          audio: false // Keep existing audio
        });
  
        const videoTrack = cameraStream.getVideoTracks()[0];
  
        // Replace screen share track with camera track
        this.peerConnections.forEach(async (peerConnection) => {
          const sender = peerConnection.getSenders().find(s => 
            s.track && s.track.kind === 'video'
          );
          if (sender) {
            await sender.replaceTrack(videoTrack);
          }
        });
  
      } catch (error) {
        this.handlers.onError?.(new Error('Failed to stop screen sharing'));
      }
    }
  
    /**
     * Start recording
     */
    startRecording(): void {
      if (!this.config.enableRecording || !this.localStream) return;
  
      try {
        this.recordedChunks = [];
        this.mediaRecorder = new MediaRecorder(this.localStream, this.config.recordingOptions);
  
        this.mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            this.recordedChunks.push(event.data);
          }
        };
  
        this.mediaRecorder.onstop = () => {
          const blob = new Blob(this.recordedChunks, { 
            type: this.config.recordingOptions?.mimeType || 'video/webm' 
          });
          this.handlers.onRecordingStop?.(blob);
        };
  
        this.mediaRecorder.start(1000); // Collect data every second
        this.handlers.onRecordingStart?.();
      } catch (error) {
        this.handlers.onError?.(new Error('Failed to start recording'));
      }
    }
  
    /**
     * Stop recording
     */
    stopRecording(): void {
      if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
        this.mediaRecorder.stop();
      }
    }
  
    /**
     * Get connection statistics
     */
    async getConnectionStats(peerId: string): Promise<RTCStatsReport | null> {
      const peerConnection = this.peerConnections.get(peerId);
      if (!peerConnection) return null;
  
      return await peerConnection.getStats();
    }
  
    /**
     * Close peer connection
     */
    closePeerConnection(peerId: string): void {
      const peerConnection = this.peerConnections.get(peerId);
      if (peerConnection) {
        peerConnection.close();
        this.peerConnections.delete(peerId);
      }
  
      const dataChannel = this.dataChannels.get(peerId);
      if (dataChannel) {
        dataChannel.close();
        this.dataChannels.delete(peerId);
      }
  
      this.remoteStreams.delete(peerId);
    }
  
    /**
     * Close all connections and cleanup
     */
    cleanup(): void {
      // Close all peer connections
      this.peerConnections.forEach((_, peerId) => {
        this.closePeerConnection(peerId);
      });
  
      // Stop local stream
      if (this.localStream) {
        this.localStream.getTracks().forEach(track => track.stop());
        this.localStream = null;
      }
  
      // Stop recording
      this.stopRecording();
  
      // Clear collections
      this.peerConnections.clear();
      this.dataChannels.clear();
      this.remoteStreams.clear();
    }
  
    /**
     * Set event handlers
     */
    setHandlers(handlers: WebRTCEventHandlers): void {
      this.handlers = { ...this.handlers, ...handlers };
    }
  
    /**
     * Get local stream
     */
    getLocalStream(): MediaStream | null {
      return this.localStream;
    }
  
    /**
     * Get remote stream for peer
     */
    getRemoteStream(peerId: string): MediaStream | null {
      return this.remoteStreams.get(peerId) || null;
    }
  
    /**
     * Get peer connection state
     */
    getPeerConnectionState(peerId: string): PeerConnectionState | null {
      const peerConnection = this.peerConnections.get(peerId);
      if (!peerConnection) return null;
  
      return {
        connectionState: peerConnection.connectionState,
        iceConnectionState: peerConnection.iceConnectionState,
        iceGatheringState: peerConnection.iceGatheringState,
        signalingState: peerConnection.signalingState,
        localDescription: peerConnection.localDescription,
        remoteDescription: peerConnection.remoteDescription
      };
    }
  
    /**
     * Get available media devices
     */
    async getMediaDevices(): Promise<MediaDeviceInfo[]> {
      try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        return devices;
      } catch (error) {
        this.handlers.onError?.(new Error('Failed to enumerate media devices'));
        return [];
      }
    }
  
    /**
     * Get media error message
     */
    private getMediaErrorMessage(error: any): string {
      switch (error.name) {
        case 'NotAllowedError':
          return 'Camera and microphone access denied. Please allow permissions and try again.';
        case 'NotFoundError':
          return 'No camera or microphone found. Please connect a device and try again.';
        case 'NotReadableError':
          return 'Camera or microphone is already in use by another application.';
        case 'OverconstrainedError':
          return 'Camera or microphone constraints cannot be satisfied.';
        case 'SecurityError':
          return 'Media access blocked due to security restrictions.';
        case 'AbortError':
          return 'Media access was aborted.';
        default:
          return error.message || 'An error occurred while accessing media devices.';
      }
    }
  }
  
  // Create singleton instance
  export const webRTCManager = new WebRTCManager();
  
  // Utility functions
  export const initializeWebRTC = (config?: Partial<WebRTCConfig>): WebRTCManager => {
    return new WebRTCManager(config);
  };
  
  export const checkWebRTCSupport = (): boolean => {
    return !!(
      navigator.mediaDevices &&
      navigator.mediaDevices.getUserMedia &&
      window.RTCPeerConnection &&
      window.RTCSessionDescription &&
      window.RTCIceCandidate
    );
  };
  
  export default webRTCManager;
  