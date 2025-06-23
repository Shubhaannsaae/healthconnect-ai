/**
 * VideoCall component for HealthConnect AI
 * WebRTC-based video consultation interface
 */

import React, { useRef, useEffect, useState } from 'react';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useWebRTC } from '@/hooks/useWebRTC';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useConsultationStore } from '@/store/consultationStore';
import { 
  Video, 
  VideoOff, 
  Mic, 
  MicOff, 
  Phone, 
  PhoneOff,
  Monitor,
  MonitorOff,
  RotateCcw,
  Settings,
  Users,
  CircleDot,
  Square
} from 'lucide-react';
import { clsx } from 'clsx';

interface VideoCallProps {
  consultationId: string;
  userRole: 'patient' | 'provider';
  onCallEnd?: () => void;
  className?: string;
}

export const VideoCall: React.FC<VideoCallProps> = ({
  consultationId,
  userRole,
  onCallEnd,
  className
}) => {
  const localVideoRef = useRef<HTMLVideoElement>(null);
  const remoteVideoRef = useRef<HTMLVideoElement>(null);
  const [connectionQuality, setConnectionQuality] = useState<'excellent' | 'good' | 'fair' | 'poor'>('good');
  const [showSettings, setShowSettings] = useState(false);
  const [callDuration, setCallDuration] = useState(0);

  const {
    currentSession,
    participants,
    isConnected,
    isRecording,
    mediaEnabled,
    toggleVideo,
    toggleAudio,
    startScreenShare,
    stopScreenShare,
    switchCamera,
    startRecording,
    stopRecording,
    endConsultation
  } = useConsultationStore();

  const {
    localStream,
    remoteStreams,
    isVideoEnabled,
    isAudioEnabled,
    isScreenSharing,
    initializeMedia,
    createPeerConnection,
    createOffer,
    createAnswer,
    setRemoteDescription,
    addIceCandidate,
    cleanup
  } = useWebRTC({
    autoInitialize: true,
    onLocalStream: (stream) => {
      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream;
      }
    },
    onRemoteStream: (stream, peerId) => {
      if (remoteVideoRef.current) {
        remoteVideoRef.current.srcObject = stream;
      }
    },
    onConnectionStateChange: (state, peerId) => {
      // Update connection quality based on state
      switch (state) {
        case 'connected':
          setConnectionQuality('excellent');
          break;
        case 'connecting':
          setConnectionQuality('fair');
          break;
        case 'disconnected':
          setConnectionQuality('poor');
          break;
        default:
          setConnectionQuality('good');
      }
    }
  });

  const { sendSignaling } = useWebSocket({
    onSignaling: async (signal) => {
      try {
        switch (signal.type) {
          case 'offer':
            await setRemoteDescription(signal.senderId, signal.payload);
            const answer = await createAnswer(signal.senderId);
            await sendSignaling({
              type: 'answer',
              consultationId,
              senderId: userRole,
              targetId: signal.senderId,
              payload: answer
            });
            break;
          case 'answer':
            await setRemoteDescription(signal.senderId, signal.payload);
            break;
          case 'ice-candidate':
            await addIceCandidate(signal.senderId, signal.payload);
            break;
        }
      } catch (error) {
        console.error('Error handling signaling:', error);
      }
    }
  });

  // Call duration timer
  useEffect(() => {
    if (isConnected) {
      const timer = setInterval(() => {
        setCallDuration(prev => prev + 1);
      }, 1000);
      return () => clearInterval(timer);
    }
  }, [isConnected]);

  // Initialize peer connection when consultation starts
  useEffect(() => {
    if (consultationId && userRole === 'provider') {
      // Provider initiates the call
      const initializeCall = async () => {
        try {
          const peerId = 'patient'; // In a real app, this would be dynamic
          await createPeerConnection(peerId);
          const offer = await createOffer(peerId);
          await sendSignaling({
            type: 'offer',
            consultationId,
            senderId: userRole,
            targetId: peerId,
            payload: offer
          });
        } catch (error) {
          console.error('Error initializing call:', error);
        }
      };
      initializeCall();
    }
  }, [consultationId, userRole]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanup();
    };
  }, [cleanup]);

  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const handleEndCall = async () => {
    try {
      await endConsultation();
      cleanup();
      onCallEnd?.();
    } catch (error) {
      console.error('Error ending call:', error);
    }
  };

  const getQualityColor = (quality: string) => {
    switch (quality) {
      case 'excellent': return 'text-green-600';
      case 'good': return 'text-blue-600';
      case 'fair': return 'text-yellow-600';
      case 'poor': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const currentParticipant = participants.find(p => p.role === userRole);
  const otherParticipants = participants.filter(p => p.role !== userRole);

  return (
    <div className={clsx('h-full flex flex-col bg-gray-900', className)}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-gray-800 text-white">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className={clsx('w-3 h-3 rounded-full', {
              'bg-green-500': connectionQuality === 'excellent',
              'bg-blue-500': connectionQuality === 'good',
              'bg-yellow-500': connectionQuality === 'fair',
              'bg-red-500': connectionQuality === 'poor'
            })} />
            <span className="text-sm font-medium">
              {connectionQuality.charAt(0).toUpperCase() + connectionQuality.slice(1)} Quality
            </span>
          </div>
          
          {isConnected && (
            <div className="text-sm text-gray-300">
              Duration: {formatDuration(callDuration)}
            </div>
          )}
        </div>

        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-1">
            <Users className="w-4 h-4" />
            <span className="text-sm">{participants.length}</span>
          </div>
          
          {isRecording && (
            <div className="flex items-center space-x-1 text-red-400">
              <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
              <span className="text-sm">Recording</span>
            </div>
          )}
        </div>
      </div>

      {/* Video Area */}
      <div className="flex-1 relative">
        {/* Remote Video (Main) */}
        <div className="w-full h-full bg-gray-800 flex items-center justify-center">
          <video
            ref={remoteVideoRef}
            autoPlay
            playsInline
            className="w-full h-full object-cover"
          />
          
          {remoteStreams.size === 0 && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center text-white">
                <div className="w-24 h-24 bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Users className="w-12 h-12 text-gray-400" />
                </div>
                <p className="text-lg font-medium">Waiting for other participant...</p>
                <p className="text-sm text-gray-400 mt-1">
                  {userRole === 'provider' ? 'Patient will join shortly' : 'Connecting to your provider'}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Local Video (Picture-in-Picture) */}
        <div className="absolute top-4 right-4 w-48 h-36 bg-gray-700 rounded-lg overflow-hidden border-2 border-gray-600">
          <video
            ref={localVideoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-full object-cover"
          />
          
          {!isVideoEnabled && (
            <div className="absolute inset-0 bg-gray-800 flex items-center justify-center">
              <VideoOff className="w-8 h-8 text-gray-400" />
            </div>
          )}
          
          {!isAudioEnabled && (
            <div className="absolute top-2 left-2">
              <MicOff className="w-4 h-4 text-red-400" />
            </div>
          )}
        </div>

        {/* Screen Share Indicator */}
        {isScreenSharing && (
          <div className="absolute top-4 left-4 bg-blue-600 text-white px-3 py-1 rounded-lg text-sm font-medium">
            Screen Sharing Active
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="p-4 bg-gray-800">
        <div className="flex items-center justify-center space-x-4">
          {/* Audio Toggle */}
          <Button
            variant={isAudioEnabled ? "ghost" : "danger"}
            size="lg"
            onClick={toggleAudio}
            className="rounded-full w-12 h-12 p-0"
          >
            {isAudioEnabled ? (
              <Mic className="w-6 h-6 text-white" />
            ) : (
              <MicOff className="w-6 h-6" />
            )}
          </Button>

          {/* Video Toggle */}
          <Button
            variant={isVideoEnabled ? "ghost" : "danger"}
            size="lg"
            onClick={toggleVideo}
            className="rounded-full w-12 h-12 p-0"
          >
            {isVideoEnabled ? (
              <Video className="w-6 h-6 text-white" />
            ) : (
              <VideoOff className="w-6 h-6" />
            )}
          </Button>

          {/* Screen Share */}
          <Button
            variant={isScreenSharing ? "primary" : "ghost"}
            size="lg"
            onClick={isScreenSharing ? stopScreenShare : startScreenShare}
            className="rounded-full w-12 h-12 p-0"
          >
            {isScreenSharing ? (
              <MonitorOff className="w-6 h-6" />
            ) : (
              <Monitor className="w-6 h-6 text-white" />
            )}
          </Button>

          {/* Switch Camera (Mobile) */}
          <Button
            variant="ghost"
            size="lg"
            onClick={switchCamera}
            className="rounded-full w-12 h-12 p-0 md:hidden"
          >
            <RotateCcw className="w-6 h-6 text-white" />
          </Button>

          {/* Recording (Provider only) */}
          {userRole === 'provider' && (
            <Button
              variant={isRecording ? "danger" : "ghost"}
              size="lg"
              onClick={isRecording ? stopRecording : startRecording}
              className="rounded-full w-12 h-12 p-0"
            >
              {isRecording ? (
                <Square className="w-6 h-6" />
              ) : (
                <CircleDot className="w-6 h-6 text-white" />
              )}
            </Button>
          )}

          {/* Settings */}
          <Button
            variant="ghost"
            size="lg"
            onClick={() => setShowSettings(!showSettings)}
            className="rounded-full w-12 h-12 p-0"
          >
            <Settings className="w-6 h-6 text-white" />
          </Button>

          {/* End Call */}
          <Button
            variant="danger"
            size="lg"
            onClick={handleEndCall}
            className="rounded-full w-12 h-12 p-0 ml-8"
          >
            <PhoneOff className="w-6 h-6" />
          </Button>
        </div>

        {/* Settings Panel */}
        {showSettings && (
          <div className="mt-4 p-4 bg-gray-700 rounded-lg">
            <h3 className="text-white font-medium mb-3">Call Settings</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <label className="block text-gray-300 mb-1">Video Quality</label>
                <select className="w-full px-2 py-1 bg-gray-600 text-white rounded">
                  <option>Auto</option>
                  <option>High (720p)</option>
                  <option>Medium (480p)</option>
                  <option>Low (360p)</option>
                </select>
              </div>
              <div>
                <label className="block text-gray-300 mb-1">Audio Quality</label>
                <select className="w-full px-2 py-1 bg-gray-600 text-white rounded">
                  <option>High</option>
                  <option>Medium</option>
                  <option>Low</option>
                </select>
              </div>
              <div>
                <label className="block text-gray-300 mb-1">Noise Cancellation</label>
                <select className="w-full px-2 py-1 bg-gray-600 text-white rounded">
                  <option>Auto</option>
                  <option>On</option>
                  <option>Off</option>
                </select>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Connection Status */}
      {!isConnected && (
        <div className="absolute inset-0 bg-black bg-opacity-75 flex items-center justify-center">
          <div className="text-center text-white">
            <div className="w-16 h-16 border-4 border-white border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-lg font-medium">Connecting...</p>
            <p className="text-sm text-gray-300 mt-1">Please wait while we establish the connection</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default VideoCall;
