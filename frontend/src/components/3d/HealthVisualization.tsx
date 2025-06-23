/**
 * HealthVisualization component for HealthConnect AI
 * 3D visualization of health data using Three.js
 */

import React, { useRef, useEffect, useState, Suspense } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { Line } from '@react-three/drei';
import { OrbitControls, Text, Html, Environment } from '@react-three/drei';
import * as THREE from 'three';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import type { VitalSigns, HealthMetrics } from '@/types/health';
import { 
  RotateCcw, 
  ZoomIn, 
  ZoomOut, 
  Play, 
  Pause,
  Settings,
  Maximize2
} from 'lucide-react';
import { clsx } from 'clsx';

interface HealthVisualizationProps {
  vitalSigns?: VitalSigns;
  healthMetrics?: HealthMetrics;
  historicalData?: VitalSigns[];
  visualizationType: 'heart' | 'brain' | 'lungs' | 'body' | 'data_flow';
  isAnimated?: boolean;
  showControls?: boolean;
  className?: string;
}

interface DataSphere {
  position: [number, number, number];
  color: string;
  value: number;
  label: string;
  pulsing: boolean;
}

const HeartVisualization: React.FC<{ vitalSigns?: VitalSigns; isAnimated: boolean }> = ({ 
  vitalSigns, 
  isAnimated 
}) => {
  const meshRef = useRef<THREE.Mesh>(null);
  const [scale, setScale] = useState(1);

  useFrame((state) => {
    if (!meshRef.current || !isAnimated) return;
    
    const heartRate = vitalSigns?.heartRate || 72;
    const beatInterval = 60 / heartRate;
    const time = state.clock.getElapsedTime();
    
    // Create heartbeat animation
    const beat = Math.sin(time * (2 * Math.PI / beatInterval));
    const newScale = 1 + (beat > 0 ? beat * 0.2 : 0);
    setScale(newScale);
    
    meshRef.current.scale.setScalar(newScale);
    
    // Color based on heart rate
    const material = meshRef.current.material as THREE.MeshStandardMaterial;
    if (heartRate > 100) {
      material.color.setHex(0xff4444); // Red for high heart rate
    } else if (heartRate < 60) {
      material.color.setHex(0x4444ff); // Blue for low heart rate
    } else {
      material.color.setHex(0xff6b6b); // Normal red
    }
  });

  return (
    <group>
      <mesh ref={meshRef} position={[0, 0, 0]}>
        <sphereGeometry args={[1.5, 32, 32]} />
        <meshStandardMaterial 
          color="#ff6b6b" 
          roughness={0.3}
          metalness={0.1}
          emissive="#330000"
          emissiveIntensity={0.2}
        />
      </mesh>
      
      {/* Heart rate text */}
      <Html position={[0, -2.5, 0]} center>
        <div className="text-white text-center">
          <div className="text-2xl font-bold">{vitalSigns?.heartRate || '--'}</div>
          <div className="text-sm opacity-75">BPM</div>
        </div>
      </Html>
      
      {/* Pulse rings */}
      {isAnimated && (
        <>
          <PulseRing radius={2.5} speed={vitalSigns?.heartRate || 72} />
          <PulseRing radius={3.5} speed={vitalSigns?.heartRate || 72} delay={0.5} />
        </>
      )}
    </group>
  );
};

const PulseRing: React.FC<{ radius: number; speed: number; delay?: number }> = ({ 
  radius, 
  speed, 
  delay = 0 
}) => {
  const ringRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (!ringRef.current) return;
    
    const time = state.clock.getElapsedTime() + delay;
    const beatInterval = 60 / speed;
    const phase = (time % beatInterval) / beatInterval;
    
    const opacity = Math.max(0, 1 - phase);
    const scale = 1 + phase * 0.5;
    
    ringRef.current.scale.setScalar(scale);
    const material = ringRef.current.material as THREE.MeshBasicMaterial;
    material.opacity = opacity * 0.3;
  });

  return (
    <mesh ref={ringRef}>
      <ringGeometry args={[radius, radius + 0.1, 32]} />
      <meshBasicMaterial 
        color="#ff6b6b" 
        transparent 
        opacity={0.3}
        side={THREE.DoubleSide}
      />
    </mesh>
  );
};

const DataFlowVisualization: React.FC<{ 
  vitalSigns?: VitalSigns; 
  isAnimated: boolean 
}> = ({ vitalSigns, isAnimated }) => {
  const groupRef = useRef<THREE.Group>(null);
  const [dataSpheres, setDataSpheres] = useState<DataSphere[]>([]);

  useEffect(() => {
    if (!vitalSigns) return;

    const spheres: DataSphere[] = [
      {
        position: [-3, 2, 0],
        color: '#ff6b6b',
        value: vitalSigns.heartRate,
        label: 'Heart Rate',
        pulsing: vitalSigns.heartRate > 100 || vitalSigns.heartRate < 60
      },
      {
        position: [3, 2, 0],
        color: '#4ecdc4',
        value: vitalSigns.oxygenSaturation,
        label: 'O2 Sat',
        pulsing: vitalSigns.oxygenSaturation < 95
      },
      {
        position: [0, -2, 0],
        color: '#45b7d1',
        value: vitalSigns.temperature,
        label: 'Temperature',
        pulsing: vitalSigns.temperature > 37.5 || vitalSigns.temperature < 36
      },
      {
        position: [-3, -2, 0],
        color: '#f39c12',
        value: vitalSigns.bloodPressure.systolic,
        label: 'Systolic BP',
        pulsing: vitalSigns.bloodPressure.systolic > 140
      },
      {
        position: [3, -2, 0],
        color: '#e74c3c',
        value: vitalSigns.respiratoryRate,
        label: 'Resp Rate',
        pulsing: vitalSigns.respiratoryRate > 20 || vitalSigns.respiratoryRate < 12
      }
    ];

    setDataSpheres(spheres);
  }, [vitalSigns]);

  useFrame((state) => {
    if (!groupRef.current || !isAnimated) return;
    groupRef.current.rotation.y = state.clock.getElapsedTime() * 0.1;
  });

  return (
    <group ref={groupRef}>
      {dataSpheres.map((sphere, index) => (
        <DataSphereComponent
          key={index}
          {...sphere}
          isAnimated={isAnimated}
        />
      ))}
      
      {/* Connection lines */}
      {dataSpheres.map((sphere, index) => (
        <ConnectingLine
          key={`line-${index}`}
          start={[0, 0, 0]}
          end={sphere.position}
          color={sphere.color}
          animated={isAnimated}
        />
      ))}
    </group>
  );
};

const DataSphereComponent: React.FC<DataSphere & { isAnimated: boolean }> = ({
  position,
  color,
  value,
  label,
  pulsing,
  isAnimated
}) => {
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (!meshRef.current || !isAnimated) return;
    
    if (pulsing) {
      const pulse = Math.sin(state.clock.getElapsedTime() * 4) * 0.1 + 1;
      meshRef.current.scale.setScalar(pulse);
    }
    
    meshRef.current.rotation.y = state.clock.getElapsedTime();
  });

  return (
    <group position={position}>
      <mesh ref={meshRef}>
        <sphereGeometry args={[0.5, 16, 16]} />
        <meshStandardMaterial 
          color={color}
          emissive={pulsing ? color : '#000000'}
          emissiveIntensity={pulsing ? 0.3 : 0}
        />
      </mesh>
      
      <Html position={[0, -1, 0]} center>
        <div className="text-white text-center text-sm">
          <div className="font-bold">{value}</div>
          <div className="opacity-75">{label}</div>
        </div>
      </Html>
    </group>
  );
};

const ConnectingLine: React.FC<{
  start: [number, number, number];
  end: [number, number, number];
  color: string;
  animated: boolean;
}> = ({ start, end, color, animated }) => {
  const lineRef = useRef<React.ElementRef<typeof Line>>(null);

  useFrame((state) => {
    if (!lineRef.current || !animated) return;
    
    const material = lineRef.current.material as THREE.LineBasicMaterial;
    material.opacity = (Math.sin(state.clock.getElapsedTime() * 2) + 1) * 0.25 + 0.25;
  });

  const points = [new THREE.Vector3(...start), new THREE.Vector3(...end)];
  const geometry = new THREE.BufferGeometry().setFromPoints(points);

  return (
    <line ref={lineRef} geometry={geometry}>
      <lineBasicMaterial color={color} transparent opacity={0.5} />
    </line>
  );
};

const CameraController: React.FC<{ 
  resetCamera: boolean; 
  onResetComplete: () => void;
}> = ({ resetCamera, onResetComplete }) => {
  const { camera } = useThree();

  useEffect(() => {
    if (resetCamera) {
      camera.position.set(0, 0, 10);
      camera.lookAt(0, 0, 0);
      onResetComplete();
    }
  }, [resetCamera, camera, onResetComplete]);

  return null;
};

export const HealthVisualization: React.FC<HealthVisualizationProps> = ({
  vitalSigns,
  healthMetrics,
  historicalData,
  visualizationType,
  isAnimated = true,
  showControls = true,
  className
}) => {
  const [animationEnabled, setAnimationEnabled] = useState(isAnimated);
  const [resetCamera, setResetCamera] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleResetCamera = () => {
    setResetCamera(true);
  };

  const handleResetComplete = () => {
    setResetCamera(false);
  };

  const toggleFullscreen = () => {
    if (!isFullscreen && containerRef.current) {
      containerRef.current.requestFullscreen();
      setIsFullscreen(true);
    } else if (document.fullscreenElement) {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  const renderVisualization = () => {
    switch (visualizationType) {
      case 'heart':
        return <HeartVisualization vitalSigns={vitalSigns} isAnimated={animationEnabled} />;
      case 'data_flow':
        return <DataFlowVisualization vitalSigns={vitalSigns} isAnimated={animationEnabled} />;
      default:
        return <HeartVisualization vitalSigns={vitalSigns} isAnimated={animationEnabled} />;
    }
  };

  return (
    <Card className={clsx('relative overflow-hidden', className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>3D Health Visualization</CardTitle>
          
          {showControls && (
            <div className="flex items-center space-x-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setAnimationEnabled(!animationEnabled)}
              >
                {animationEnabled ? (
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
              
              <Button
                variant="ghost"
                size="sm"
                onClick={toggleFullscreen}
              >
                <Maximize2 className="w-4 h-4" />
              </Button>
            </div>
          )}
        </div>
      </CardHeader>
      
      <CardContent className="p-0">
        <div 
          ref={containerRef}
          className={clsx('relative', {
            'h-96': !isFullscreen,
            'h-screen': isFullscreen
          })}
        >
          <Suspense 
            fallback={
              <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
                <LoadingSpinner size="lg" variant="white" showLabel label="Loading 3D visualization..." />
              </div>
            }
          >
            <Canvas
              camera={{ position: [0, 0, 10], fov: 75 }}
              style={{ background: 'linear-gradient(135deg, #1e3a8a 0%, #3730a3 50%, #581c87 100%)' }}
            >
              <ambientLight intensity={0.4} />
              <pointLight position={[10, 10, 10]} intensity={1} />
              <pointLight position={[-10, -10, -10]} intensity={0.5} color="#4f46e5" />
              
              <Environment preset="night" />
              
              {renderVisualization()}
              
              <OrbitControls 
                enablePan={true}
                enableZoom={true}
                enableRotate={true}
                autoRotate={false}
                maxDistance={20}
                minDistance={5}
              />
              
              <CameraController 
                resetCamera={resetCamera} 
                onResetComplete={handleResetComplete}
              />
            </Canvas>
          </Suspense>
          
          {/* Overlay Information */}
          <div className="absolute top-4 left-4 text-white">
            <div className="bg-black bg-opacity-50 rounded-lg p-3">
              <h3 className="font-semibold mb-2">
                {visualizationType.replace('_', ' ').toUpperCase()} VIEW
              </h3>
              {vitalSigns && (
                <div className="space-y-1 text-sm">
                  <div>Heart Rate: {vitalSigns.heartRate} BPM</div>
                  <div>O2 Sat: {vitalSigns.oxygenSaturation}%</div>
                  <div>Temp: {vitalSigns.temperature}°C</div>
                  <div>BP: {vitalSigns.bloodPressure.systolic}/{vitalSigns.bloodPressure.diastolic}</div>
                </div>
              )}
            </div>
          </div>
          
          {/* Controls Overlay */}
          {showControls && (
            <div className="absolute bottom-4 right-4">
              <div className="bg-black bg-opacity-50 rounded-lg p-2 flex space-x-2">
                <div className="text-white text-xs">
                  <div>Mouse: Rotate</div>
                  <div>Wheel: Zoom</div>
                  <div>Right-click: Pan</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default HealthVisualization;
