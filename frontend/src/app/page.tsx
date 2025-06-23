/**
 * Landing page for HealthConnect AI
 * Next.js 14 App Router home page
 */

import React from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { Button } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/Card';
import { 
  Heart, 
  Shield, 
  Zap, 
  Users, 
  Activity, 
  Brain,
  Smartphone,
  Video,
  BarChart3,
  CheckCircle,
  ArrowRight,
  Play
} from 'lucide-react';

const features = [
  {
    icon: Heart,
    title: 'Real-time Health Monitoring',
    description: 'Continuous monitoring of vital signs with AI-powered analysis and instant alerts for critical changes.',
  },
  {
    icon: Video,
    title: 'Telemedicine Platform',
    description: 'High-quality video consultations with healthcare providers, featuring voice recognition and AI assistance.',
  },
  {
    icon: Smartphone,
    title: 'IoT Device Integration',
    description: 'Seamless integration with medical devices for automated data collection and real-time health tracking.',
  },
  {
    icon: Brain,
    title: 'AI Health Assistant',
    description: 'Advanced AI provides personalized health insights, medication reminders, and treatment recommendations.',
  },
  {
    icon: BarChart3,
    title: 'Advanced Analytics',
    description: 'Comprehensive health analytics with 3D visualizations and predictive health modeling.',
  },
  {
    icon: Shield,
    title: 'HIPAA Compliant Security',
    description: 'Enterprise-grade security with end-to-end encryption and compliance with healthcare regulations.',
  },
];

const stats = [
  { value: '10,000+', label: 'Active Patients' },
  { value: '500+', label: 'Healthcare Providers' },
  { value: '99.9%', label: 'Uptime Reliability' },
  { value: '24/7', label: 'Emergency Support' },
];

const testimonials = [
  {
    name: 'Dr. Sarah Johnson',
    role: 'Cardiologist',
    image: '/images/testimonial-1.svg',
    quote: 'HealthConnect AI has revolutionized how I monitor my patients. The real-time alerts have helped prevent several emergency situations.',
  },
  {
    name: 'Michael Chen',
    role: 'Patient',
    image: '/images/testimonial-2.svg',
    quote: 'The platform makes managing my diabetes so much easier. The AI assistant reminds me about medications and tracks my glucose levels automatically.',
  },
  {
    name: 'Dr. Emily Rodriguez',
    role: 'Emergency Medicine',
    image: '/images/testimonial-3.svg',
    quote: 'The emergency alert system is incredibly fast and accurate. It has significantly improved our response times for critical patients.',
  },
];

export default function HomePage() {
  return (
    <div className="min-h-screen">
      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-2">
              <Heart className="w-8 h-8 text-primary-600" />
              <span className="text-xl font-bold text-gray-900">HealthConnect AI</span>
            </div>
            
            <div className="hidden md:flex items-center space-x-8">
              <Link href="#features" className="text-gray-700 hover:text-primary-600 transition-colors">
                Features
              </Link>
              <Link href="#about" className="text-gray-700 hover:text-primary-600 transition-colors">
                About
              </Link>
              <Link href="#contact" className="text-gray-700 hover:text-primary-600 transition-colors">
                Contact
              </Link>
              <Link href="/dashboard">
                <Button variant="outline">Sign In</Button>
              </Link>
              <Link href="/dashboard">
                <Button>Get Started</Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-primary-600 via-primary-700 to-purple-800 text-white">
        <div className="absolute inset-0 bg-black opacity-20"></div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h1 className="text-4xl md:text-6xl font-bold leading-tight mb-6">
                The Future of
                <span className="block text-gradient">Healthcare is Here</span>
              </h1>
              <p className="text-xl md:text-2xl text-blue-100 mb-8 leading-relaxed">
                Advanced AI-powered platform for remote patient monitoring, telemedicine, and personalized healthcare management.
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <Link href="/dashboard">
                  <Button size="xl" className="w-full sm:w-auto">
                    Start Your Journey
                    <ArrowRight className="w-5 h-5 ml-2" />
                  </Button>
                </Link>
                <Button variant="outline" size="xl" className="w-full sm:w-auto bg-white/10 border-white/20 text-white hover:bg-white/20">
                  <Play className="w-5 h-5 mr-2" />
                  Watch Demo
                </Button>
              </div>
            </div>
            
            <div className="relative">
              <div className="relative z-10">
                <Image
                  src="/images/hero-dashboard.svg"
                  alt="HealthConnect AI Dashboard"
                  width={600}
                  height={400}
                  className="rounded-lg shadow-2xl"
                  priority
                />
              </div>
              <div className="absolute -top-4 -right-4 w-full h-full bg-gradient-to-br from-purple-400 to-pink-400 rounded-lg opacity-20"></div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="bg-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-3xl md:text-4xl font-bold text-primary-600 mb-2">
                  {stat.value}
                </div>
                <div className="text-gray-600 font-medium">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="bg-gray-50 py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Comprehensive Healthcare Solutions
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Our platform combines cutting-edge AI technology with intuitive design to deliver 
              the most advanced healthcare experience available today.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <Card key={index} className="hover:shadow-lg transition-shadow duration-300">
                <CardContent className="p-6">
                  <div className="flex items-center mb-4">
                    <div className="p-3 bg-primary-100 rounded-lg">
                      <feature.icon className="w-6 h-6 text-primary-600" />
                    </div>
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-3">
                    {feature.title}
                  </h3>
                  <p className="text-gray-600 leading-relaxed">
                    {feature.description}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="bg-white py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              How HealthConnect AI Works
            </h2>
            <p className="text-xl text-gray-600">
              Simple, secure, and seamless healthcare management in three easy steps
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-primary-600 text-white rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-6">
                1
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Connect Your Devices</h3>
              <p className="text-gray-600">
                Easily connect your medical devices and wearables to start monitoring your health in real-time.
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-primary-600 text-white rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-6">
                2
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">AI-Powered Analysis</h3>
              <p className="text-gray-600">
                Our advanced AI continuously analyzes your health data and provides personalized insights and recommendations.
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-primary-600 text-white rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-6">
                3
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Stay Connected</h3>
              <p className="text-gray-600">
                Connect with healthcare providers through our telemedicine platform and receive immediate care when needed.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="bg-gray-50 py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Trusted by Healthcare Professionals
            </h2>
            <p className="text-xl text-gray-600">
              See what doctors and patients are saying about HealthConnect AI
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <Card key={index} className="bg-white">
                <CardContent className="p-6">
                  <p className="text-gray-600 mb-6 italic">"{testimonial.quote}"</p>
                  <div className="flex items-center">
                    <Image
                      src={testimonial.image}
                      alt={testimonial.name}
                      width={48}
                      height={48}
                      className="rounded-full mr-4"
                    />
                    <div>
                      <div className="font-semibold text-gray-900">{testimonial.name}</div>
                      <div className="text-sm text-gray-600">{testimonial.role}</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-primary-600 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Ready to Transform Your Healthcare Experience?
          </h2>
          <p className="text-xl text-blue-100 mb-8 max-w-2xl mx-auto">
            Join thousands of patients and healthcare providers who trust HealthConnect AI 
            for their healthcare management needs.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/dashboard">
              <Button size="xl" variant="secondary">
                Get Started Free
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
            <Button size="xl" variant="outline" className="border-white text-white hover:bg-white hover:text-primary-600">
              Schedule Demo
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div className="col-span-1 md:col-span-2">
              <div className="flex items-center space-x-2 mb-4">
                <Heart className="w-8 h-8 text-primary-400" />
                <span className="text-xl font-bold">HealthConnect AI</span>
              </div>
              <p className="text-gray-400 mb-6 max-w-md">
                Advanced AI-powered healthcare platform for remote patient monitoring, 
                telemedicine, and personalized healthcare management.
              </p>
              <div className="flex space-x-4">
                <CheckCircle className="w-5 h-5 text-green-400" />
                <span className="text-sm text-gray-400">HIPAA Compliant</span>
              </div>
            </div>
            
            <div>
              <h3 className="font-semibold mb-4">Platform</h3>
              <ul className="space-y-2 text-gray-400">
                <li><Link href="/dashboard" className="hover:text-white transition-colors">Dashboard</Link></li>
                <li><Link href="/consultation" className="hover:text-white transition-colors">Telemedicine</Link></li>
                <li><Link href="/devices" className="hover:text-white transition-colors">Devices</Link></li>
                <li><Link href="/analytics" className="hover:text-white transition-colors">Analytics</Link></li>
              </ul>
            </div>
            
            <div>
              <h3 className="font-semibold mb-4">Support</h3>
              <ul className="space-y-2 text-gray-400">
                <li><Link href="/help" className="hover:text-white transition-colors">Help Center</Link></li>
                <li><Link href="/contact" className="hover:text-white transition-colors">Contact Us</Link></li>
                <li><Link href="/privacy" className="hover:text-white transition-colors">Privacy Policy</Link></li>
                <li><Link href="/terms" className="hover:text-white transition-colors">Terms of Service</Link></li>
              </ul>
            </div>
          </div>
          
          <div className="border-t border-gray-800 mt-12 pt-8 text-center text-gray-400">
            <p>&copy; 2025 HealthConnect AI. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
