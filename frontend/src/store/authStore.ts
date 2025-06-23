/**
 * Authentication state management for HealthConnect AI
 * Using Zustand for state management with AWS Cognito integration
 */

import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import { persist, createJSONStorage } from 'zustand/middleware';
import { getCurrentUser, signIn, signOut, signUp, confirmSignUp, resendSignUpCode } from 'aws-amplify/auth';
import type { CognitoAuthState, CognitoSignInData, CognitoSignUpData, CognitoUserAttributes } from '@/types/aws';
import { handleAWSError } from '@/lib/aws-config';

interface AuthStore extends CognitoAuthState {
  // Actions
  initialize: () => Promise<void>;
  signIn: (credentials: CognitoSignInData) => Promise<void>;
  signOut: () => Promise<void>;
  signUp: (userData: CognitoSignUpData) => Promise<{ nextStep: any }>;
  confirmSignUp: (username: string, confirmationCode: string) => Promise<void>;
  resendConfirmationCode: (username: string) => Promise<void>;
  refreshSession: () => Promise<void>;
  updateUserAttributes: (attributes: Partial<CognitoUserAttributes>) => Promise<void>;
  changePassword: (oldPassword: string, newPassword: string) => Promise<void>;
  forgotPassword: (username: string) => Promise<void>;
  confirmResetPassword: (username: string, confirmationCode: string, newPassword: string) => Promise<void>;
  clearError: () => void;
  
  // Computed values
  isPatient: () => boolean;
  isProvider: () => boolean;
  isAdmin: () => boolean;
  getFullName: () => string;
  getUserRole: () => string;
}

export const useAuthStore = create<AuthStore>()(
  subscribeWithSelector(
    persist(
      (set, get) => ({
        // Initial state
        isAuthenticated: false,
        user: null,
        session: null,
        userAttributes: null,
        loading: false,
        error: null,

        // Initialize authentication state
        initialize: async () => {
          set({ loading: true, error: null });
          
          try {
            const user = await getCurrentUser();
            const session = await user.getSession();
            const userAttributes = await user.getUserAttributes();
            
            // Transform Cognito attributes to our format
            const transformedAttributes: CognitoUserAttributes = {
              sub: userAttributes.sub,
              email: userAttributes.email,
              email_verified: userAttributes.email_verified === 'true',
              given_name: userAttributes.given_name,
              family_name: userAttributes.family_name,
              phone_number: userAttributes.phone_number,
              phone_number_verified: userAttributes.phone_number_verified === 'true',
              'custom:user_type': userAttributes['custom:user_type'] as 'patient' | 'provider' | 'admin',
              'custom:organization': userAttributes['custom:organization'],
              'custom:license_number': userAttributes['custom:license_number'],
              'custom:specialty': userAttributes['custom:specialty'],
              preferred_username: userAttributes.preferred_username,
              picture: userAttributes.picture,
              locale: userAttributes.locale,
              zoneinfo: userAttributes.zoneinfo
            };

            set({
              isAuthenticated: true,
              user,
              session,
              userAttributes: transformedAttributes,
              loading: false,
              error: null
            });
          } catch (error) {
            console.log('User not authenticated:', error);
            set({
              isAuthenticated: false,
              user: null,
              session: null,
              userAttributes: null,
              loading: false,
              error: null
            });
          }
        },

        // Sign in user
        signIn: async (credentials: CognitoSignInData) => {
          set({ loading: true, error: null });
          
          try {
            const { isSignedIn, nextStep } = await signIn({
              username: credentials.username,
              password: credentials.password,
              options: {
                userAttributes: {}
              }
            });

            if (isSignedIn) {
              // Get user details after successful sign in
              await get().initialize();
            } else {
              // Handle MFA or other next steps
              set({ 
                loading: false, 
                error: `Additional step required: ${nextStep.signInStep}` 
              });
            }
          } catch (error: any) {
            const errorMessage = handleAWSError(error);
            set({ 
              loading: false, 
              error: errorMessage,
              isAuthenticated: false,
              user: null,
              session: null,
              userAttributes: null
            });
            throw error;
          }
        },

        // Sign out user
        signOut: async () => {
          set({ loading: true, error: null });
          
          try {
            await signOut();
            set({
              isAuthenticated: false,
              user: null,
              session: null,
              userAttributes: null,
              loading: false,
              error: null
            });
          } catch (error: any) {
            const errorMessage = handleAWSError(error);
            set({ loading: false, error: errorMessage });
            throw error;
          }
        },

        // Sign up new user
        signUp: async (userData: CognitoSignUpData) => {
          set({ loading: true, error: null });
          
          try {
            const { isSignUpComplete, userId, nextStep } = await signUp({
              username: userData.username,
              password: userData.password,
              options: {
                userAttributes: {
                  email: userData.email,
                  given_name: userData.givenName,
                  family_name: userData.familyName,
                  phone_number: userData.phoneNumber,
                  'custom:user_type': userData.userType,
                  'custom:organization': userData.organization,
                  'custom:license_number': userData.licenseNumber,
                  'custom:specialty': userData.specialty
                }
              }
            });

            set({ loading: false });
            return { nextStep };
          } catch (error: any) {
            const errorMessage = handleAWSError(error);
            set({ loading: false, error: errorMessage });
            throw error;
          }
        },

        // Confirm sign up with verification code
        confirmSignUp: async (username: string, confirmationCode: string) => {
          set({ loading: true, error: null });
          
          try {
            const { isSignUpComplete, nextStep } = await confirmSignUp({
              username,
              confirmationCode
            });

            if (isSignUpComplete) {
              set({ loading: false });
            } else {
              set({ 
                loading: false, 
                error: `Additional step required: ${nextStep?.signUpStep}` 
              });
            }
          } catch (error: any) {
            const errorMessage = handleAWSError(error);
            set({ loading: false, error: errorMessage });
            throw error;
          }
        },

        // Resend confirmation code
        resendConfirmationCode: async (username: string) => {
          set({ loading: true, error: null });
          
          try {
            await resendSignUpCode({ username });
            set({ loading: false });
          } catch (error: any) {
            const errorMessage = handleAWSError(error);
            set({ loading: false, error: errorMessage });
            throw error;
          }
        },

        // Refresh user session
        refreshSession: async () => {
          const { user } = get();
          if (!user) return;

          set({ loading: true, error: null });
          
          try {
            const session = await user.getSession({ forceRefresh: true });
            set({ session, loading: false });
          } catch (error: any) {
            const errorMessage = handleAWSError(error);
            set({ loading: false, error: errorMessage });
            throw error;
          }
        },

        // Update user attributes
        updateUserAttributes: async (attributes: Partial<CognitoUserAttributes>) => {
          const { user } = get();
          if (!user) throw new Error('User not authenticated');

          set({ loading: true, error: null });
          
          try {
            // Convert our attributes format to Cognito format
            const cognitoAttributes: Record<string, string> = {};
            
            Object.entries(attributes).forEach(([key, value]) => {
              if (value !== undefined && value !== null) {
                cognitoAttributes[key] = String(value);
              }
            });

            await user.updateAttributes(cognitoAttributes);
            
            // Refresh user attributes
            const updatedAttributes = await user.getUserAttributes();
            const transformedAttributes: CognitoUserAttributes = {
              sub: updatedAttributes.sub,
              email: updatedAttributes.email,
              email_verified: updatedAttributes.email_verified === 'true',
              given_name: updatedAttributes.given_name,
              family_name: updatedAttributes.family_name,
              phone_number: updatedAttributes.phone_number,
              phone_number_verified: updatedAttributes.phone_number_verified === 'true',
              'custom:user_type': updatedAttributes['custom:user_type'] as 'patient' | 'provider' | 'admin',
              'custom:organization': updatedAttributes['custom:organization'],
              'custom:license_number': updatedAttributes['custom:license_number'],
              'custom:specialty': updatedAttributes['custom:specialty'],
              preferred_username: updatedAttributes.preferred_username,
              picture: updatedAttributes.picture,
              locale: updatedAttributes.locale,
              zoneinfo: updatedAttributes.zoneinfo
            };

            set({ 
              userAttributes: transformedAttributes,
              loading: false 
            });
          } catch (error: any) {
            const errorMessage = handleAWSError(error);
            set({ loading: false, error: errorMessage });
            throw error;
          }
        },

        // Change password
        changePassword: async (oldPassword: string, newPassword: string) => {
          const { user } = get();
          if (!user) throw new Error('User not authenticated');

          set({ loading: true, error: null });
          
          try {
            await user.changePassword(oldPassword, newPassword);
            set({ loading: false });
          } catch (error: any) {
            const errorMessage = handleAWSError(error);
            set({ loading: false, error: errorMessage });
            throw error;
          }
        },

        // Forgot password
        forgotPassword: async (username: string) => {
          set({ loading: true, error: null });
          
          try {
            // Implementation would use AWS Amplify's forgotPassword
            // await forgotPassword({ username });
            set({ loading: false });
          } catch (error: any) {
            const errorMessage = handleAWSError(error);
            set({ loading: false, error: errorMessage });
            throw error;
          }
        },

        // Confirm reset password
        confirmResetPassword: async (username: string, confirmationCode: string, newPassword: string) => {
          set({ loading: true, error: null });
          
          try {
            // Implementation would use AWS Amplify's confirmResetPassword
            // await confirmResetPassword({ username, confirmationCode, newPassword });
            set({ loading: false });
          } catch (error: any) {
            const errorMessage = handleAWSError(error);
            set({ loading: false, error: errorMessage });
            throw error;
          }
        },

        // Clear error
        clearError: () => {
          set({ error: null });
        },

        // Computed values
        isPatient: () => {
          const { userAttributes } = get();
          return userAttributes?.['custom:user_type'] === 'patient';
        },

        isProvider: () => {
          const { userAttributes } = get();
          return userAttributes?.['custom:user_type'] === 'provider';
        },

        isAdmin: () => {
          const { userAttributes } = get();
          return userAttributes?.['custom:user_type'] === 'admin';
        },

        getFullName: () => {
          const { userAttributes } = get();
          if (!userAttributes) return '';
          return `${userAttributes.given_name} ${userAttributes.family_name}`.trim();
        },

        getUserRole: () => {
          const { userAttributes } = get();
          return userAttributes?.['custom:user_type'] || 'unknown';
        }
      }),
      {
        name: 'healthconnect-auth',
        storage: createJSONStorage(() => localStorage),
        partialize: (state) => ({
          isAuthenticated: state.isAuthenticated,
          userAttributes: state.userAttributes
        })
      }
    )
  )
);

// Subscribe to auth state changes for side effects
useAuthStore.subscribe(
  (state) => state.isAuthenticated,
  (isAuthenticated) => {
    if (isAuthenticated) {
      console.log('User authenticated');
      // Initialize other stores or services
    } else {
      console.log('User signed out');
      // Clear other stores or services
    }
  }
);

export default useAuthStore;
