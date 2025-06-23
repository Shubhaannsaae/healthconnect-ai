/**
 * Consultation state management for HealthConnect AI
 * Managing telemedicine sessions, WebRTC connections, and consultation data
 */

import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { 
  ConsultationSession, 
  ConsultationMessage, 
  ConsultationParticipant,
  ConsultationQueue,
  ProviderAvailability,
  ConsultationFeedback,
  ConsultationAnalytics,
  EmergencyConsultation
} from '@/types/consultation';
import { apiClient } from '@/lib/aws-config';
import { webRTCManager } from '@/lib/webrtc';
import { webSocketManager } from '@/lib/websocket';

interface ConsultationStore {
  // State
  currentSession: ConsultationSession | null;
  consultationHistory: ConsultationSession[];
  messages: ConsultationMessage[];
  participants: ConsultationParticipant[];
  queueStatus: ConsultationQueue | null;
  availableProviders: ProviderAvailability[];
  emergencySession: EmergencyConsultation | null;
  consultationAnalytics: ConsultationAnalytics | null;
  isConnected: boolean;
  isRecording: boolean;
  mediaEnabled: {
    video: boolean;
    audio: boolean;
    screenShare: boolean;
  };
  connectionQuality: {
    video: number;
    audio: number;
    overall: number;
  };
  loading: boolean;
  error: string | null;
  lastUpdated: string | null;

  // Actions
  createConsultation: (consultationData: Partial<ConsultationSession>) => Promise<string>;
  joinConsultation: (sessionId: string, userRole: string) => Promise<void>;
  leaveConsultation: () => Promise<void>;
  sendMessage: (message: Omit<ConsultationMessage, 'id' | 'timestamp'>) => Promise<void>;
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<void>;
  toggleVideo: () => void;
  toggleAudio: () => void;
  startScreenShare: () => Promise<void>;
  stopScreenShare: () => Promise<void>;
  switchCamera: () => Promise<void>;
  inviteParticipant: (userId: string, role: string) => Promise<void>;
  removeParticipant: (participantId: string) => Promise<void>;
  endConsultation: () => Promise<void>;
  submitFeedback: (feedback: ConsultationFeedback) => Promise<void>;
  fetchConsultationHistory: (patientId: string) => Promise<void>;
  fetchAvailableProviders: (specialty?: string) => Promise<void>;
  joinQueue: (queueData: Omit<ConsultationQueue, 'id' | 'queuePosition' | 'estimatedWaitTime'>) => Promise<void>;
  leaveQueue: () => Promise<void>;
  createEmergencyConsultation: (emergencyData: Partial<EmergencyConsultation>) => Promise<string>;
  updateConnectionQuality: (quality: Partial<typeof connectionQuality>) => void;
  clearError: () => void;
  reset: () => void;

  // Computed values
  isInConsultation: () => boolean;
  isInQueue: () => boolean;
  getUnreadMessages: () => ConsultationMessage[];
  getCurrentProvider: () => ConsultationParticipant | null;
  getSessionDuration: () => number;
  canRecord: () => boolean;
}

export const useConsultationStore = create<ConsultationStore>()(
  subscribeWithSelector(
    persist(
      (set, get) => ({
        // Initial state
        currentSession: null,
        consultationHistory: [],
        messages: [],
        participants: [],
        queueStatus: null,
        availableProviders: [],
        emergencySession: null,
        consultationAnalytics: null,
        isConnected: false,
        isRecording: false,
        mediaEnabled: {
          video: true,
          audio: true,
          screenShare: false
        },
        connectionQuality: {
          video: 0,
          audio: 0,
          overall: 0
        },
        loading: false,
        error: null,
        lastUpdated: null,

        // Create consultation
        createConsultation: async (consultationData: Partial<ConsultationSession>) => {
          set({ loading: true, error: null });
          
          try {
            const response = await apiClient.post({
              apiName: 'HealthConnectAPI',
              path: '/consultation/session',
              options: {
                body: {
                  ...consultationData,
                  createdAt: new Date().toISOString(),
                  status: 'scheduled'
                }
              }
            });

            if (response.success) {
              set({
                currentSession: response.data,
                loading: false,
                lastUpdated: new Date().toISOString()
              });
              return response.data.id;
            } else {
              throw new Error(response.error?.message || 'Failed to create consultation');
            }
          } catch (error: any) {
            set({ loading: false, error: error.message });
            throw error;
          }
        },

        // Join consultation
        joinConsultation: async (sessionId: string, userRole: string) => {
          set({ loading: true, error: null });
          
          try {
            // Fetch consultation details
            const sessionResponse = await apiClient.get({
              apiName: 'HealthConnectAPI',
              path: `/consultation/session/${sessionId}`
            });

            if (!sessionResponse.success) {
              throw new Error('Consultation session not found');
            }

            // Initialize WebRTC
            await webRTCManager.initializeLocalStream();
            
            // Join WebSocket room
            await webSocketManager.joinConsultation(sessionId, userRole);
            
            // Create peer connection if needed
            if (userRole === 'patient' || userRole === 'provider') {
              await webRTCManager.createPeerConnection(sessionId);
            }

            const participant: ConsultationParticipant = {
              id: `participant_${Date.now()}`,
              userId: '', // Will be set from auth store
              role: userRole as any,
              name: '', // Will be set from auth store
              joinedAt: new Date().toISOString(),
              connectionStatus: 'connected',
              mediaStatus: {
                video: get().mediaEnabled.video,
                audio: get().mediaEnabled.audio,
                screenShare: false
              },
              permissions: {
                canSpeak: true,
                canVideo: true,
                canScreenShare: userRole === 'provider',
                canRecord: userRole === 'provider',
                canInviteOthers: userRole === 'provider'
              }
            };

            set({
              currentSession: sessionResponse.data,
              participants: [participant],
              isConnected: true,
              loading: false,
              lastUpdated: new Date().toISOString()
            });
          } catch (error: any) {
            set({ loading: false, error: error.message });
            throw error;
          }
        },

        // Leave consultation
        leaveConsultation: async () => {
          const { currentSession } = get();
          if (!currentSession) return;

          set({ loading: true, error: null });
          
          try {
            // Leave WebSocket room
            await webSocketManager.leaveConsultation(currentSession.id);
            
            // Clean up WebRTC connections
            webRTCManager.cleanup();
            
            // Update session status
            await apiClient.put({
              apiName: 'HealthConnectAPI',
              path: `/consultation/session/${currentSession.id}/leave`
            });

            set({
              currentSession: null,
              participants: [],
              messages: [],
              isConnected: false,
              isRecording: false,
              mediaEnabled: {
                video: true,
                audio: true,
                screenShare: false
              },
              loading: false,
              lastUpdated: new Date().toISOString()
            });
          } catch (error: any) {
            set({ loading: false, error: error.message });
            throw error;
          }
        },

        // Send message
        sendMessage: async (message: Omit<ConsultationMessage, 'id' | 'timestamp'>) => {
          const { currentSession } = get();
          if (!currentSession) throw new Error('No active consultation session');

          try {
            const fullMessage: ConsultationMessage = {
              ...message,
              id: `msg_${Date.now()}`,
              consultationId: currentSession.id,
              timestamp: new Date().toISOString(),
              readBy: []
            };

            // Send through WebSocket
            await webSocketManager.sendConsultationMessage(fullMessage);
            
            // Add to local state
            set(state => ({
              messages: [...state.messages, fullMessage],
              lastUpdated: new Date().toISOString()
            }));
          } catch (error: any) {
            set({ error: error.message });
            throw error;
          }
        },

        // Start recording
        startRecording: async () => {
          const { currentSession } = get();
          if (!currentSession) throw new Error('No active consultation session');

          try {
            webRTCManager.startRecording();
            
            await apiClient.put({
              apiName: 'HealthConnectAPI',
              path: `/consultation/session/${currentSession.id}/recording/start`
            });

            set({ 
              isRecording: true,
              lastUpdated: new Date().toISOString()
            });
          } catch (error: any) {
            set({ error: error.message });
            throw error;
          }
        },

        // Stop recording
        stopRecording: async () => {
          const { currentSession } = get();
          if (!currentSession) throw new Error('No active consultation session');

          try {
            webRTCManager.stopRecording();
            
            await apiClient.put({
              apiName: 'HealthConnectAPI',
              path: `/consultation/session/${currentSession.id}/recording/stop`
            });

            set({ 
              isRecording: false,
              lastUpdated: new Date().toISOString()
            });
          } catch (error: any) {
            set({ error: error.message });
            throw error;
          }
        },

        // Toggle video
        toggleVideo: () => {
          const { mediaEnabled } = get();
          const newVideoState = !mediaEnabled.video;
          
          webRTCManager.toggleVideo(newVideoState);
          
          set({
            mediaEnabled: {
              ...mediaEnabled,
              video: newVideoState
            },
            lastUpdated: new Date().toISOString()
          });
        },

        // Toggle audio
        toggleAudio: () => {
          const { mediaEnabled } = get();
          const newAudioState = !mediaEnabled.audio;
          
          webRTCManager.toggleAudio(newAudioState);
          
          set({
            mediaEnabled: {
              ...mediaEnabled,
              audio: newAudioState
            },
            lastUpdated: new Date().toISOString()
          });
        },

        // Start screen share
        startScreenShare: async () => {
          try {
            await webRTCManager.startScreenShare();
            
            set(state => ({
              mediaEnabled: {
                ...state.mediaEnabled,
                screenShare: true
              },
              lastUpdated: new Date().toISOString()
            }));
          } catch (error: any) {
            set({ error: error.message });
            throw error;
          }
        },

        // Stop screen share
        stopScreenShare: async () => {
          try {
            await webRTCManager.stopScreenShare();
            
            set(state => ({
              mediaEnabled: {
                ...state.mediaEnabled,
                screenShare: false
              },
              lastUpdated: new Date().toISOString()
            }));
          } catch (error: any) {
            set({ error: error.message });
            throw error;
          }
        },

        // Switch camera
        switchCamera: async () => {
          try {
            await webRTCManager.switchCamera();
          } catch (error: any) {
            set({ error: error.message });
            throw error;
          }
        },

        // Invite participant
        inviteParticipant: async (userId: string, role: string) => {
          const { currentSession } = get();
          if (!currentSession) throw new Error('No active consultation session');

          set({ loading: true, error: null });
          
          try {
            const response = await apiClient.post({
              apiName: 'HealthConnectAPI',
              path: `/consultation/session/${currentSession.id}/invite`,
              options: {
                body: { userId, role }
              }
            });

            if (response.success) {
              set({ loading: false });
            } else {
              throw new Error(response.error?.message || 'Failed to invite participant');
            }
          } catch (error: any) {
            set({ loading: false, error: error.message });
            throw error;
          }
        },

        // Remove participant
        removeParticipant: async (participantId: string) => {
          const { currentSession } = get();
          if (!currentSession) throw new Error('No active consultation session');

          try {
            await apiClient.delete({
              apiName: 'HealthConnectAPI',
              path: `/consultation/session/${currentSession.id}/participants/${participantId}`
            });

            set(state => ({
              participants: state.participants.filter(p => p.id !== participantId),
              lastUpdated: new Date().toISOString()
            }));
          } catch (error: any) {
            set({ error: error.message });
            throw error;
          }
        },

        // End consultation
        endConsultation: async () => {
          const { currentSession } = get();
          if (!currentSession) throw new Error('No active consultation session');

          set({ loading: true, error: null });
          
          try {
            await apiClient.put({
              apiName: 'HealthConnectAPI',
              path: `/consultation/session/${currentSession.id}/end`
            });

            // Clean up connections
            await get().leaveConsultation();
            
            set({ loading: false });
          } catch (error: any) {
            set({ loading: false, error: error.message });
            throw error;
          }
        },

        // Submit feedback
        submitFeedback: async (feedback: ConsultationFeedback) => {
          set({ loading: true, error: null });
          
          try {
            const response = await apiClient.post({
              apiName: 'HealthConnectAPI',
              path: '/consultation/feedback',
              options: {
                body: {
                  ...feedback,
                  submittedAt: new Date().toISOString()
                }
              }
            });

            if (response.success) {
              set({ loading: false });
            } else {
              throw new Error(response.error?.message || 'Failed to submit feedback');
            }
          } catch (error: any) {
            set({ loading: false, error: error.message });
            throw error;
          }
        },

        // Fetch consultation history
        fetchConsultationHistory: async (patientId: string) => {
          set({ loading: true, error: null });
          
          try {
            const response = await apiClient.get({
              apiName: 'HealthConnectAPI',
              path: `/consultation/history?patientId=${patientId}`
            });

            if (response.success) {
              set({
                consultationHistory: response.data || [],
                loading: false,
                lastUpdated: new Date().toISOString()
              });
            } else {
              throw new Error(response.error?.message || 'Failed to fetch consultation history');
            }
          } catch (error: any) {
            set({ loading: false, error: error.message });
            throw error;
          }
        },

        // Fetch available providers
        fetchAvailableProviders: async (specialty?: string) => {
          set({ loading: true, error: null });
          
          try {
            const queryParams = specialty ? `?specialty=${specialty}` : '';
            const response = await apiClient.get({
              apiName: 'HealthConnectAPI',
              path: `/consultation/providers${queryParams}`
            });

            if (response.success) {
              set({
                availableProviders: response.data || [],
                loading: false,
                lastUpdated: new Date().toISOString()
              });
            } else {
              throw new Error(response.error?.message || 'Failed to fetch available providers');
            }
          } catch (error: any) {
            set({ loading: false, error: error.message });
            throw error;
          }
        },

        // Join queue
        joinQueue: async (queueData: Omit<ConsultationQueue, 'id' | 'queuePosition' | 'estimatedWaitTime'>) => {
          set({ loading: true, error: null });
          
          try {
            const response = await apiClient.post({
              apiName: 'HealthConnectAPI',
              path: '/consultation/queue',
              options: {
                body: {
                  ...queueData,
                  requestedAt: new Date().toISOString()
                }
              }
            });

            if (response.success) {
              set({
                queueStatus: response.data,
                loading: false,
                lastUpdated: new Date().toISOString()
              });
            } else {
              throw new Error(response.error?.message || 'Failed to join consultation queue');
            }
          } catch (error: any) {
            set({ loading: false, error: error.message });
            throw error;
          }
        },

        // Leave queue
        leaveQueue: async () => {
          const { queueStatus } = get();
          if (!queueStatus) return;

          set({ loading: true, error: null });
          
          try {
            await apiClient.delete({
              apiName: 'HealthConnectAPI',
              path: `/consultation/queue/${queueStatus.id}`
            });

            set({
              queueStatus: null,
              loading: false,
              lastUpdated: new Date().toISOString()
            });
          } catch (error: any) {
            set({ loading: false, error: error.message });
            throw error;
          }
        },

        // Create emergency consultation
        createEmergencyConsultation: async (emergencyData: Partial<EmergencyConsultation>) => {
          set({ loading: true, error: null });
          
          try {
            const response = await apiClient.post({
              apiName: 'HealthConnectAPI',
              path: '/consultation/emergency',
              options: {
                body: emergencyData
              }
            });

            if (response.success) {
              set({
                emergencySession: response.data,
                loading: false,
                lastUpdated: new Date().toISOString()
              });
              return response.data.id;
            } else {
              throw new Error(response.error?.message || 'Failed to create emergency consultation');
            }
          } catch (error: any) {
            set({ loading: false, error: error.message });
            throw error;
          }
        },

        // Update connection quality
        updateConnectionQuality: (quality: Partial<typeof connectionQuality>) => {
          set(state => ({
            connectionQuality: {
              ...state.connectionQuality,
              ...quality
            },
            lastUpdated: new Date().toISOString()
          }));
        },

        // Clear error
        clearError: () => {
          set({ error: null });
        },

        // Reset store
        reset: () => {
          // Clean up WebRTC connections
          webRTCManager.cleanup();
          
          set({
            currentSession: null,
            consultationHistory: [],
            messages: [],
            participants: [],
            queueStatus: null,
            availableProviders: [],
            emergencySession: null,
            consultationAnalytics: null,
            isConnected: false,
            isRecording: false,
            mediaEnabled: {
              video: true,
              audio: true,
              screenShare: false
            },
            connectionQuality: {
              video: 0,
              audio: 0,
              overall: 0
            },
            loading: false,
            error: null,
            lastUpdated: null
          });
        },

        // Computed values
        isInConsultation: () => {
          const { currentSession } = get();
          return currentSession !== null && currentSession.status === 'in_progress';
        },

        isInQueue: () => {
          const { queueStatus } = get();
          return queueStatus !== null && queueStatus.status === 'waiting';
        },

        getUnreadMessages: () => {
          const { messages } = get();
          // This would typically check against user's last read timestamp
          return messages.filter(message => message.readBy.length === 0);
        },

        getCurrentProvider: () => {
          const { participants } = get();
          return participants.find(p => p.role === 'provider') || null;
        },

        getSessionDuration: () => {
          const { currentSession } = get();
          if (!currentSession || !currentSession.startTime) return 0;
          
          const startTime = new Date(currentSession.startTime).getTime();
          const currentTime = Date.now();
          return Math.floor((currentTime - startTime) / 1000); // Duration in seconds
        },

        canRecord: () => {
          const { currentSession, participants } = get();
          if (!currentSession) return false;
          
          const currentUser = participants.find(p => p.permissions.canRecord);
          return currentUser !== undefined;
        }
      }),
      {
        name: 'healthconnect-consultation',
        storage: createJSONStorage(() => localStorage),
        partialize: (state) => ({
          consultationHistory: state.consultationHistory,
          lastUpdated: state.lastUpdated
        })
      }
    )
  )
);

export default useConsultationStore;
