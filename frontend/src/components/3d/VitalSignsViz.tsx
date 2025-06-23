/**
 * VitalSignsViz component for HealthConnect AI
 * Real-time 3D visualization of vital signs data
 */

import React, { useRef, useEffect, useState, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Line, Text, Html } from '@react-three/drei';
import * as THREE from 'three';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import type { VitalSigns } from '@/types/health';
import { 
  Play, 
  Pause, 
  RotateCcw,
  TrendingUp,
  Activity
} from 'lucide-react';
import { clsx } from 'clsx';

interface VitalSignsVizProps {
  vitalSigns: VitalSigns[];
  realTimeData?: VitalSigns;
  maxDataPoints?: number;
  autoRotate?: boolean;
  showGrid?: boolean;
  className?: string;
}

interface DataPoint3D {
  position: [number, number, number];
  color: string;
  value: number;
  timestamp: string;
  metric: string;
}

const VitalSignsGraph3D: React.FC<{
  data: VitalSigns[];
  metric: keyof VitalSigns;
  color: string;
  position: [number, number, number];
  scale: number;
}> = ({ data, metric, color, position, scale }) => {
  const lineRef = useRef<THREE.Group>(null);
  const [points, setPoints] = useState<THREE.Vector3[]>([]);

  useEffect(() => {
    const newPoints = data.map((reading, index) => {
      let value: number;
      
      switch (metric) {
        case 'heartRate':
          value = reading.heartRate;
          break;
        case 'temperature':
          value = reading.temperature;
          break;
        case 'oxygenSaturation':
          value = reading.oxygenSaturation;
          break;
        case 'respiratoryRate':
          value = reading.respiratoryRate;
          break;
        default:
          value = 0;
      }
      
      // Normalize value for 3D space
      const normalizedValue = (value - getMinValue(metric)) / (getMaxValue(metric) - getMinValue(metric));
      
      return new THREE.Vector3(
        index * 0.2,
        normalizedValue * scale,
        0
      );
    });
    
    setPoints(newPoints);
  }, [data, metric, scale]);

  const getMinValue = (metric: keyof VitalSigns): number => {
    switch (metric) {
      case 'heartRate': return 40;
      case 'temperature': return 35;
      case 'oxygenSaturation': return 80;
      case 'respiratoryRate': return 8;
      default: return 0;
    }
  };

  const getMaxValue = (metric: keyof VitalSigns): number => {
    switch (metric) {
      case 'heartRate': return 120;
      case 'temperature': return 42;
      case 'oxygenSaturation': return 100;
      case 'respiratoryRate': return 30;
      default: return 100;
    }
  };

  return (
    <group position={position} ref={lineRef}>
      {points.length > 1 && (
        <Line
          points={points}
          color={color}
          lineWidth={3}
        />
      )}
      
      {/* Data points */}
      {points.map((point, index) => (
        <mesh key={index} position={point.toArray()}>
          <sphereGeometry args={[0.05, 8, 8]} />
          <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.3} />
        </mesh>
      ))}
      
      {/* Metric label */}
      <Text
        position={[points.length * 0.1, scale + 0.5, 0]}
        fontSize={0.3}
        color={color}
        anchorX="center"
        anchorY="middle"
      >
        {metric.toUpperCase()}
      </Text>
    </group>
  );
};

const RealTimeIndicator: React.FC<{
  vitalSigns?: VitalSigns;
  position: [number, number, number];
}> = ({ vitalSigns, position }) => {
  const indicatorRef = useRef<THREE.Group>(null);

  useFrame((state) => {
    if (!indicatorRef.current) return;
    
    // Pulsing animation
    const pulse = Math.sin(state.clock.getElapsedTime() * 2) * 0.1 + 1;
    indicatorRef.current.scale.setScalar(pulse);
  });

  if (!vitalSigns) return null;

  return (
    <group ref={indicatorRef} position={position}>
      <mesh>
        <sphereGeometry args={[0.2, 16, 16]} />
        <meshStandardMaterial 
          color="#22c55e" 
          emissive="#22c55e" 
          emissiveIntensity={0.5}
        />
      </mesh>
      
      <Html position={[0, 0.5, 0]} center>
        <div className="bg-black bg-opacity-75 text-white px-3 py-2 rounded text-sm">
          <div className="font-semibold mb-1">Live Data</div>
          <div>HR: {vitalSigns.heartRate} BPM</div>
          <div>Temp: {vitalSigns.temperature.toFixed(1)}°C</div>
          <div>O2: {vitalSigns.oxygenSaturation}%</div>
          <div>RR: {vitalSigns.respiratoryRate}/min</div>
        </div>
      </Html>
    </group>
  );
};

const Grid3D: React.FC<{ size: number; divisions: number }> = ({ size, divisions }) => {
  const gridPoints = useMemo(() => {
    const points: THREE.Vector3[] = [];
    const step = size / divisions;
    
    // Horizontal lines
    for (let i = 0; i <= divisions; i++) {
      points.push(new THREE.Vector3(-size/2, 0, i * step - size/2));
      points.push(new THREE.Vector3(size/2, 0, i * step - size/2));
    }
    
    // Vertical lines
    for (let i = 0; i <= divisions; i++) {
      points.push(new THREE.Vector3(i * step - size/2, 0, -size/2));
      points.push(new THREE.Vector3(i * step - size/2, 0, size/2));
    }
    
    return points;
  }, [size, divisions]);

  return (
    <Line
      points={gridPoints}
      color="#e2e8f0"
      lineWidth={1}
      segments
    />
  );
};

const AxisLabels: React.FC = () => {
  return (
    <group>
      {/* X-axis label */}
      <Text
        position={[5, -0.5, 0]}
        fontSize={0.3}
        color="#6b7280"
        anchorX="center"
        anchorY="middle"
      >
        Time
      </Text>
      
      {/* Y-axis label */}
      <Text
        position={[-0.5, 3, 0]}
        fontSize={0.3}
        color="#6b7280"
        anchorX="center"
        anchorY="middle"
        rotation={[0, 0, Math.PI / 2]}
      >
        Value
      </Text>
      
      {/* Z-axis label */}
      <Text
        position={[0, -0.5, 3]}
        fontSize={0.3}
        color="#6b7280"
        anchorX="center"
        anchorY="middle"
        rotation={[0, -Math.PI / 2, 0]}
      >
        Metrics
      </Text>
    </group>
  );
};

export const VitalSignsViz: React.FC<VitalSignsVizProps> = ({
  vitalSigns,
  realTimeData,
  maxDataPoints = 50,
  autoRotate = false,
  showGrid = true,
  className
}) => {
  const [isAnimated, setIsAnimated] = useState(true);
  const [resetCamera, setResetCamera] = useState(false);
  const [selectedMetrics, setSelectedMetrics] = useState<(keyof VitalSigns)[]>([
    'heartRate',
    'temperature',
    'oxygenSaturation',
    'respiratoryRate'
  ]);

  // Limit data points for performance
  const limitedData = useMemo(() => {
    return vitalSigns.slice(-maxDataPoints);
  }, [vitalSigns, maxDataPoints]);

  const metricConfigs = {
    heartRate: { color: '#ef4444', position: [0, 0, -2] as [number, number, number] },
    temperature: { color: '#f59e0b', position: [0, 0, -1] as [number, number, number] },
    oxygenSaturation: { color: '#3b82f6', position: [0, 0, 0] as [number, number, number] },
    respiratoryRate: { color: '#22c55e', position: [0, 0, 1] as [number, number, number] }
  };

  const handleResetCamera = () => {
    setResetCamera(true);
    setTimeout(() => setResetCamera(false), 100);
  };

  const toggleMetric = (metric: keyof VitalSigns) => {
    setSelectedMetrics(prev => 
      prev.includes(metric)
        ? prev.filter(m => m !== metric)
        : [...prev, metric]
    );
  };

  return (
    <Card className={clsx('relative overflow-hidden', className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center space-x-2">
            <Activity className="w-5 h-5 text-primary-600" />
            <span>3D Vital Signs Visualization</span>
          </CardTitle>
          
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsAnimated(!isAnimated)}
            >
              {isAnimated ? (
                <Pause className="w-4 h-4" />
              ) : (
                <Play className="w-4 h-4" />
              )}
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={handleResetCamera}
            >
              <RotateCcw className="w-4 h-4" />
            </Button>
          </div>
        </div>
        
        {/* Metric toggles */}
        <div className="flex flex-wrap gap-2 mt-4">
          {Object.entries(metricConfigs).map(([metric, config]) => (
            <button
              key={metric}
              onClick={() => toggleMetric(metric as keyof VitalSigns)}
              className={clsx(
                'flex items-center space-x-2 px-3 py-1 rounded-full text-sm transition-colors',
                selectedMetrics.includes(metric as keyof VitalSigns)
                  ? 'bg-gray-900 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              )}
            >
              <div 
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: config.color }}
              />
              <span className="capitalize">{metric.replace(/([A-Z])/g, ' $1').trim()}</span>
            </button>
          ))}
        </div>
      </CardHeader>
      
      <CardContent className="p-0">
        <div className="h-96 relative">
          <Canvas
            camera={{ position: [8, 5, 8], fov: 60 }}
            style={{ background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)' }}
          >
            <ambientLight intensity={0.6} />
            <directionalLight position={[10, 10, 5]} intensity={0.8} />
            <pointLight position={[-10, 0, -10]} intensity={0.3} />
            
            {/* Grid */}
            {showGrid && <Grid3D size={10} divisions={10} />}
            
            {/* Axis labels */}
            <AxisLabels />
            
            {/* Vital signs graphs */}
            {selectedMetrics.map(metric => (
              <VitalSignsGraph3D
                key={metric}
                data={limitedData}
                metric={metric}
                color={metricConfigs[metric].color}
                position={metricConfigs[metric].position}
                scale={2}
              />
            ))}
            
            {/* Real-time indicator */}
            {realTimeData && (
              <RealTimeIndicator
                vitalSigns={realTimeData}
                position={[limitedData.length * 0.2, 0, 2]}
              />
            )}
            
            <OrbitControls 
              enablePan={true}
              enableZoom={true}
              enableRotate={true}
              autoRotate={autoRotate && isAnimated}
              autoRotateSpeed={1}
              maxDistance={20}
              minDistance={5}
            />
          </Canvas>
          
          {/* Data summary overlay */}
          <div className="absolute top-4 left-4 bg-black bg-opacity-75 text-white p-3 rounded-lg">
            <h3 className="font-semibold mb-2">Data Summary</h3>
            <div className="space-y-1 text-sm">
              <div>Total Points: {limitedData.length}</div>
              <div>Time Span: {limitedData.length * 5} minutes</div>
              <div>Active Metrics: {selectedMetrics.length}</div>
              {realTimeData && (
                <div className="flex items-center space-x-2 mt-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                  <span>Live Data</span>
                </div>
              )}
            </div>
          </div>
          
          {/* Controls overlay */}
          <div className="absolute bottom-4 right-4 bg-black bg-opacity-75 text-white p-2 rounded-lg text-xs">
            <div>Mouse: Rotate view</div>
            <div>Wheel: Zoom in/out</div>
            <div>Right-click: Pan</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default VitalSignsViz;
