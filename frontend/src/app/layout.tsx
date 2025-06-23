/**
 * Root layout for HealthConnect AI
 * Next.js 14 App Router root layout with providers and global setup
 */

import type { Metadata, Viewport } from 'next';
import { Inter } from 'next/font/google';
import { Toaster } from 'react-hot-toast';
import { Providers } from './providers';
import './globals.css';

const inter = Inter({ 
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter'
});

export const metadata: Metadata = {
  title: {
    default: 'HealthConnect AI - Advanced Healthcare Platform',
    template: '%s | HealthConnect AI'
  },
  description: 'Advanced AI-powered healthcare platform for remote patient monitoring, telemedicine, and health analytics.',
  keywords: [
    'healthcare',
    'telemedicine',
    'AI',
    'patient monitoring',
    'health analytics',
    'medical devices',
    'remote care'
  ],
  authors: [{ name: 'HealthConnect AI Team' }],
  creator: 'HealthConnect AI',
  publisher: 'HealthConnect AI',
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  metadataBase: new URL('https://healthconnect-ai.com'),
  alternates: {
    canonical: '/',
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://healthconnect-ai.com',
    siteName: 'HealthConnect AI',
    title: 'HealthConnect AI - Advanced Healthcare Platform',
    description: 'Advanced AI-powered healthcare platform for remote patient monitoring and telemedicine.',
    images: [
      {
        url: '/images/og-image.png',
        width: 1200,
        height: 630,
        alt: 'HealthConnect AI Platform',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'HealthConnect AI - Advanced Healthcare Platform',
    description: 'Advanced AI-powered healthcare platform for remote patient monitoring and telemedicine.',
    images: ['/images/twitter-image.png'],
    creator: '@healthconnectai',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  manifest: '/manifest.json',
  icons: {
    icon: [
      { url: '/icons/icon-32x32.png', sizes: '32x32', type: 'image/png' },
      { url: '/icons/icon-16x16.png', sizes: '16x16', type: 'image/png' },
    ],
    apple: [
      { url: '/icons/apple-touch-icon.png', sizes: '180x180', type: 'image/png' },
    ],
    other: [
      { rel: 'mask-icon', url: '/icons/safari-pinned-tab.svg', color: '#0ea5e9' },
    ],
  },
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: 'HealthConnect AI',
  },
  verification: {
    google: 'google-verification-code',
    yandex: 'yandex-verification-code',
  },
  category: 'healthcare',
};

export const viewport: Viewport = {
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#0ea5e9' },
    { media: '(prefers-color-scheme: dark)', color: '#0ea5e9' },
  ],
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  viewportFit: 'cover',
};

interface RootLayoutProps {
  children: React.ReactNode;
}

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en" className={inter.variable} suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link rel="dns-prefetch" href="//api.healthconnect-ai.com" />
        <link rel="dns-prefetch" href="//cdn.healthconnect-ai.com" />
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <meta name="msapplication-TileColor" content="#0ea5e9" />
        <meta name="msapplication-config" content="/browserconfig.xml" />
      </head>
      <body className={`${inter.className} antialiased`} suppressHydrationWarning>
        <Providers>
          <div id="root" className="min-h-screen bg-gray-50">
            {children}
          </div>
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
              },
              success: {
                duration: 3000,
                iconTheme: {
                  primary: '#22c55e',
                  secondary: '#fff',
                },
              },
              error: {
                duration: 5000,
                iconTheme: {
                  primary: '#ef4444',
                  secondary: '#fff',
                },
              },
            }}
          />
        </Providers>
        <div id="modal-root" />
        <div id="tooltip-root" />
      </body>
    </html>
  );
}
