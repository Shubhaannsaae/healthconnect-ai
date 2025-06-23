/** @type {import('next').NextConfig} */
const withPWA = require('next-pwa')({
    dest: 'public',
    register: true,
    skipWaiting: true,
    disable: process.env.NODE_ENV === 'development',
    buildExcludes: [/middleware-manifest\.json$/],
    runtimeCaching: [
      {
        urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
        handler: 'CacheFirst',
        options: {
          cacheName: 'google-fonts',
          expiration: {
            maxEntries: 4,
            maxAgeSeconds: 365 * 24 * 60 * 60 // 365 days
          }
        }
      },
      {
        urlPattern: /^https:\/\/fonts\.gstatic\.com\/.*/i,
        handler: 'CacheFirst',
        options: {
          cacheName: 'google-fonts-static',
          expiration: {
            maxEntries: 4,
            maxAgeSeconds: 365 * 24 * 60 * 60 // 365 days
          }
        }
      },
      {
        urlPattern: /\.(?:eot|otf|ttc|ttf|woff|woff2|font.css)$/i,
        handler: 'StaleWhileRevalidate',
        options: {
          cacheName: 'static-font-assets',
          expiration: {
            maxEntries: 4,
            maxAgeSeconds: 7 * 24 * 60 * 60 // 7 days
          }
        }
      },
      {
        urlPattern: /\.(?:jpg|jpeg|gif|png|svg|ico|webp)$/i,
        handler: 'StaleWhileRevalidate',
        options: {
          cacheName: 'static-image-assets',
          expiration: {
            maxEntries: 64,
            maxAgeSeconds: 24 * 60 * 60 // 24 hours
          }
        }
      },
      {
        urlPattern: /\/_next\/image\?url=.+$/i,
        handler: 'StaleWhileRevalidate',
        options: {
          cacheName: 'next-image',
          expiration: {
            maxEntries: 64,
            maxAgeSeconds: 24 * 60 * 60 // 24 hours
          }
        }
      },
      {
        urlPattern: /\.(?:mp3|wav|ogg)$/i,
        handler: 'CacheFirst',
        options: {
          rangeRequests: true,
          cacheName: 'static-audio-assets',
          expiration: {
            maxEntries: 32,
            maxAgeSeconds: 24 * 60 * 60 // 24 hours
          }
        }
      },
      {
        urlPattern: /\.(?:js)$/i,
        handler: 'StaleWhileRevalidate',
        options: {
          cacheName: 'static-js-assets',
          expiration: {
            maxEntries: 32,
            maxAgeSeconds: 24 * 60 * 60 // 24 hours
          }
        }
      },
      {
        urlPattern: /\.(?:css|less)$/i,
        handler: 'StaleWhileRevalidate',
        options: {
          cacheName: 'static-style-assets',
          expiration: {
            maxEntries: 32,
            maxAgeSeconds: 24 * 60 * 60 // 24 hours
          }
        }
      },
      {
        urlPattern: /^https:\/\/.+\/_next\/static.+$/i,
        handler: 'CacheFirst',
        options: {
          cacheName: 'next-static',
          expiration: {
            maxEntries: 64,
            maxAgeSeconds: 24 * 60 * 60 // 24 hours
          }
        }
      }
    ]
  });
  
  const nextConfig = {
    experimental: {
      serverComponentsExternalPackages: ['three']
    },
    // The 'appDir' option is deprecated in Next.js 14.2.5 and should be removed.
    // If you were using it for the App Router, it's now the default behavior.
    // If you need to configure a custom app directory, refer to the Next.js documentation.

    images: {
      remotePatterns: [
        {
          protocol: 'http',
          hostname: 'localhost',
          port: '3000',
          pathname: '/images/**.svg',
        },
        {
          protocol: 'http',
          hostname: 'localhost',
          port: '3000',
          pathname: '/images/**.png',
        },
        {
          protocol: 'http',
          hostname: 'localhost',
          port: '3000',
          pathname: '/images/**.jpg',
        },
        {
          protocol: 'https',
          hostname: 'healthconnect-ai.com',
          pathname: '/images/**.svg',
        },
        {
          protocol: 'https',
          hostname: 'healthconnect-ai.com',
          pathname: '/images/**.png',
        },
        {
          protocol: 'https',
          hostname: 'healthconnect-ai.com',
          pathname: '/images/**.jpg',
        },
        {
          protocol: 'https',
          hostname: 's3.amazonaws.com',
          pathname: '/**',
        },
        {
          protocol: 'https',
          hostname: 'cloudfront.net',
          pathname: '/**',
        },
      ],
      formats: ['image/webp', 'image/avif'],
      deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
      imageSizes: [16, 32, 48, 64, 96, 128, 256, 384]
    },
    env: {
      NEXT_PUBLIC_AWS_REGION: process.env.NEXT_PUBLIC_AWS_REGION,
      NEXT_PUBLIC_AWS_USER_POOL_ID: process.env.NEXT_PUBLIC_AWS_USER_POOL_ID,
      NEXT_PUBLIC_AWS_USER_POOL_CLIENT_ID: process.env.NEXT_PUBLIC_AWS_USER_POOL_CLIENT_ID,
      NEXT_PUBLIC_AWS_IDENTITY_POOL_ID: process.env.NEXT_PUBLIC_AWS_IDENTITY_POOL_ID,
      NEXT_PUBLIC_API_GATEWAY_URL: process.env.NEXT_PUBLIC_API_GATEWAY_URL,
      NEXT_PUBLIC_WEBSOCKET_URL: process.env.NEXT_PUBLIC_WEBSOCKET_URL,
      NEXT_PUBLIC_IOT_ENDPOINT: process.env.NEXT_PUBLIC_IOT_ENDPOINT,
      NEXT_PUBLIC_BEDROCK_MODEL_ID: process.env.NEXT_PUBLIC_BEDROCK_MODEL_ID,
      NEXT_PUBLIC_ENVIRONMENT: process.env.NEXT_PUBLIC_ENVIRONMENT
    },
    webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
      // Handle Three.js
      config.module.rules.push({
        test: /\.(glsl|vs|fs|vert|frag)$/,
        use: ['raw-loader', 'glslify-loader']
      });
  
      // Handle audio files
      config.module.rules.push({
        test: /\.(mp3|wav|ogg)$/,
        use: {
          loader: 'file-loader',
          options: {
            publicPath: '/_next/static/audio/',
            outputPath: 'static/audio/'
          }
        }
      });
  
      // Bundle analyzer
      if (process.env.ANALYZE === 'true') {
        const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');
        config.plugins.push(
          new BundleAnalyzerPlugin({
            analyzerMode: 'static',
            openAnalyzer: false,
            reportFilename: isServer
              ? '../analyze/server.html'
              : './analyze/client.html'
          })
        );
      }
  
      return config;
    },
    headers: async () => {
      return [
        {
          source: '/(.*)',
          headers: [
            {
              key: 'X-Frame-Options',
              value: 'DENY'
            },
            {
              key: 'X-Content-Type-Options',
              value: 'nosniff'
            },
            {
              key: 'Referrer-Policy',
              value: 'strict-origin-when-cross-origin'
            },
            {
              key: 'Permissions-Policy',
              value: 'camera=(), microphone=(), geolocation=()'
            }
          ]
        },
        {
          source: '/api/(.*)',
          headers: [
            {
              key: 'Access-Control-Allow-Origin',
              value: process.env.NODE_ENV === 'production' 
                ? 'https://healthconnect-ai.com' 
                : 'http://localhost:3000'
            },
            {
              key: 'Access-Control-Allow-Methods',
              value: 'GET, POST, PUT, DELETE, OPTIONS'
            },
            {
              key: 'Access-Control-Allow-Headers',
              value: 'Content-Type, Authorization'
            }
          ]
        }
      ];
    },
    redirects: async () => {
      return [
        {
          source: '/dashboard',
          destination: '/dashboard/overview',
          permanent: false
        }
      ];
    },
    rewrites: async () => {
      return [
        {
          source: '/health-check',
          destination: '/api/health'
        }
      ];
    }
  };
  
  module.exports = withPWA(nextConfig);
  