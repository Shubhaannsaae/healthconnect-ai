/** @type {import('next').NextConfig} */
const nextConfig = {
    experimental: {
      appDir: true,
      serverComponentsExternalPackages: ['three']
    },
    images: {
      domains: [
        'localhost',
        'healthconnect-ai.com',
        's3.amazonaws.com',
        'cdn.healthconnect-ai.com'
      ],
      formats: ['image/webp', 'image/avif']
    },
    env: {
      CUSTOM_KEY: process.env.CUSTOM_KEY,
    },
    async headers() {
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
              value: 'camera=self, microphone=self, geolocation=self'
            }
          ]
        }
      ];
    },
    async rewrites() {
      return [
        {
          source: '/api/health/:path*',
          destination: `${process.env.NEXT_PUBLIC_API_URL}/health/:path*`
        },
        {
          source: '/api/devices/:path*',
          destination: `${process.env.NEXT_PUBLIC_API_URL}/devices/:path*`
        }
      ];
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
  
      // Handle 3D model files
      config.module.rules.push({
        test: /\.(gltf|glb|fbx|obj)$/,
        use: {
          loader: 'file-loader',
          options: {
            publicPath: '/_next/static/models/',
            outputPath: 'static/models/'
          }
        }
      });
  
      return config;
    },
    poweredByHeader: false,
    compress: true,
    generateEtags: true,
    httpAgentOptions: {
      keepAlive: true
    },
    onDemandEntries: {
      maxInactiveAge: 25 * 1000,
      pagesBufferLength: 2
    },
    productionBrowserSourceMaps: false,
    optimizeFonts: true,
    swcMinify: true
  };
  
  // Bundle analyzer
  if (process.env.ANALYZE === 'true') {
    const withBundleAnalyzer = require('@next/bundle-analyzer')({
      enabled: true
    });
    module.exports = withBundleAnalyzer(nextConfig);
  } else {
    module.exports = nextConfig;
  }
  