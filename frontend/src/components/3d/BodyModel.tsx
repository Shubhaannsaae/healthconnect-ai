/**
 * BodyModel component for HealthConnect AI
 * 3D human body model with health data overlay
 */

import React, { useRef, useEffect, useState, Suspense } from 'react';
import { Canvas, useFrame, useLoader } from '@react-three/fiber';
import { OrbitControls, Html, useGLTF, Text } from '@react-three/drei';
import * as THREE from 'three';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import type { VitalSigns, HealthRecord } from '@/types/health';
import { 
  RotateCcw, 
  Eye, 
  EyeOff,
  Layers,
  Info
} from 'lucide-react';
import { clsx } from 'clsx';

interface BodyModelProps {
  vitalSigns?: VitalSigns;
  healthRecords?: HealthRecord[];
  highlightedSystems?: string[];
  showVitalSigns?: boolean;
  showAnnotations?: boolean;
  className?: string;
}

interface HealthMarker {
  position: [number, number, number];
  type: 'heart' | 'lungs' | 'brain' | 'liver' | 'kidneys' | 'stomach';
  status: 'normal' | 'warning' | 'critical';
  value?: number;
  unit?: string;
  description: string;
}

const HumanBodyModel: React.FC<{
  showVitalSigns: boolean;
  vitalSigns: VitalSigns | undefined;
  highlightedSystems: string[];
}> = ({ showVitalSigns, vitalSigns, highlightedSystems }) => {
  const groupRef = useRef<THREE.Group>(null);
  const [bodyParts, setBodyParts] = useState<THREE.Object3D[]>([]);

  // In a real implementation, you would load a 3D model file
  // For this example, we'll create a simplified body representation
  useEffect(() => {
    if (!groupRef.current) return;

    // Create simplified body parts
    const parts: THREE.Object3D[] = [];
    
    // Head
    const head = new THREE.Mesh(
      new THREE.SphereGeometry(0.8, 16, 16),
      new THREE.MeshStandardMaterial({ color: '#fdbcb4' })
    );
    head.position.set(0, 3, 0);
    head.userData = { type: 'head', system: 'nervous' };
    parts.push(head);
    
    // Torso
    const torso = new THREE.Mesh(
      new THREE.CylinderGeometry(1, 1.2, 2.5, 8),
      new THREE.MeshStandardMaterial({ color: '#fdbcb4' })
    );
    torso.position.set(0, 1, 0);
    torso.userData = { type: 'torso', system: 'respiratory' };
    parts.push(torso);
    
    // Arms
    const leftArm = new THREE.Mesh(
      new THREE.CylinderGeometry(0.3, 0.3, 2, 8),
      new THREE.MeshStandardMaterial({ color: '#fdbcb4' })
    );
    leftArm.position.set(-1.5, 1.5, 0);
    leftArm.rotation.z = Math.PI / 6;
    leftArm.userData = { type: 'arm', system: 'circulatory' };
    parts.push(leftArm);
    
    const rightArm = leftArm.clone();
    rightArm.position.set(1.5, 1.5, 0);
    rightArm.rotation.z = -Math.PI / 6;
    parts.push(rightArm);
    
    // Legs
    const leftLeg = new THREE.Mesh(
      new THREE.CylinderGeometry(0.4, 0.4, 2.5, 8),
      new THREE.MeshStandardMaterial({ color: '#fdbcb4' })
    );
    leftLeg.position.set(-0.5, -1.5, 0);
    leftLeg.userData = { type: 'leg', system: 'muscular' };
    parts.push(leftLeg);
    
    const rightLeg = leftLeg.clone();
    rightLeg.position.set(0.5, -1.5, 0);
    parts.push(rightLeg);
    
    // Add parts to group
    parts.forEach(part => groupRef.current?.add(part));
    setBodyParts(parts);
    
    return () => {
      parts.forEach(part => groupRef.current?.remove(part));
    };
  }, []);

  // Update body part colors based on highlighted systems
  useEffect(() => {
    bodyParts.forEach(part => {
      const material = (part as THREE.Mesh).material as THREE.MeshStandardMaterial;
      const system = part.userData.system;
      
      if (highlightedSystems.includes(system)) {
        material.color.setHex(0x4ade80); // Green highlight
        material.emissive.setHex(0x166534);
        material.emissiveIntensity = 0.2;
      } else {
        material.color.setHex(0xfdbcb4); // Normal skin color
        material.emissive.setHex(0x000000);
        material.emissiveIntensity = 0;
      }
    });
  }, [bodyParts, highlightedSystems]);

  const healthMarkers: HealthMarker[] = [
    {
      position: [-0.3, 1.5, 0.5],
      type: 'heart',
      status: vitalSigns?.heartRate ? (
        vitalSigns.heartRate > 100 || vitalSigns.heartRate < 60 ? 'warning' : 'normal'
      ) : 'normal',
      value: vitalSigns?.heartRate ?? 0,
      unit: 'BPM',
      description: 'Heart Rate'
    },
    {
      position: [0.3, 1.8, 0.5],
      type: 'lungs',
      status: vitalSigns?.oxygenSaturation ? (
        vitalSigns.oxygenSaturation < 95 ? 'critical' : 'normal'
      ) : 'normal',
      value: vitalSigns?.oxygenSaturation ?? 0,
      unit: '%',
      description: 'Oxygen Saturation'
    },
    {
      position: [0, 3, 0.8],
      type: 'brain',
      status: 'normal',
      description: 'Neurological System'
    }
  ];

  return (
    <group ref={groupRef}>
      {/* Health markers */}
      {showVitalSigns && healthMarkers.map((marker, index) => (
        <HealthMarkerComponent
          key={index}
          {...marker}
        />
      ))}
    </group>
  );
};

const HealthMarkerComponent: React.FC<HealthMarker> = ({
  position,
  type,
  status,
  value,
  unit,
  description
}) => {
  const markerRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (!markerRef.current) return;
    
    // Pulsing animation for critical status
    if (status === 'critical') {
      const pulse = Math.sin(state.clock.getElapsedTime() * 4) * 0.2 + 1;
      markerRef.current.scale.setScalar(pulse);
    }
  });

  const getMarkerColor = () => {
    switch (status) {
      case 'normal': return '#22c55e';
      case 'warning': return '#f59e0b';
      case 'critical': return '#ef4444';
      default: return '#6b7280';
    }
  };

  return (
    <group position={position}>
      <mesh ref={markerRef}>
        <sphereGeometry args={[0.1, 8, 8]} />
        <meshStandardMaterial 
          color={getMarkerColor()}
          emissive={getMarkerColor()}
          emissiveIntensity={0.3}
        />
      </mesh>
      
      <Html position={[0, 0.3, 0]} center>
        <div className="bg-black bg-opacity-75 text-white px-2 py-1 rounded text-xs">
          <div className="font-semibold">{description}</div>
          {value && unit && (
            <div>{value} {unit}</div>
          )}
        </div>
      </Html>
    </group>
  );
};

const SystemLegend: React.FC<{
  systems: string[];
  highlightedSystems: string[];
  onSystemToggle: (system: string) => void;
}> = ({ systems, highlightedSystems, onSystemToggle }) => {
  const systemColors = {
    nervous: '#8b5cf6',
    respiratory: '#06b6d4',
    circulatory: '#ef4444',
    digestive: '#f59e0b',
    muscular: '#22c55e',
    skeletal: '#6b7280'
  };

  return (
    <div className="space-y-2">
      <h4 className="font-semibold text-sm">Body Systems</h4>
      {systems.map(system => (
        <button
          key={system}
          onClick={() => onSystemToggle(system)}
          className={clsx(
            'flex items-center space-x-2 text-sm p-2 rounded transition-colors w-full text-left',
            highlightedSystems.includes(system)
              ? 'bg-blue-100 text-blue-800'
              : 'hover:bg-gray-100'
          )}
        >
          <div 
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: systemColors[system as keyof typeof systemColors] }}
          />
          <span className="capitalize">{system}</span>
          {highlightedSystems.includes(system) ? (
            <Eye className="w-3 h-3 ml-auto" />
          ) : (
            <EyeOff className="w-3 h-3 ml-auto opacity-50" />
          )}
        </button>
      ))}
    </div>
  );
};

export const BodyModel: React.FC<BodyModelProps> = ({
  vitalSigns,
  healthRecords,
  highlightedSystems = [],
  showVitalSigns = true,
  showAnnotations = true,
  className
}) => {
  const [activeHighlights, setActiveHighlights] = useState<string[]>(highlightedSystems);
  const [showLegend, setShowLegend] = useState(true);
  const [resetCamera, setResetCamera] = useState(false);

  const bodySystems = ['nervous', 'respiratory', 'circulatory', 'digestive', 'muscular', 'skeletal'];

  const handleSystemToggle = (system: string) => {
    setActiveHighlights(prev => 
      prev.includes(system)
        ? prev.filter(s => s !== system)
        : [...prev, system]
    );
  };

  const handleResetCamera = () => {
    setResetCamera(true);
    setTimeout(() => setResetCamera(false), 100);
  };

  return (
    <Card className={clsx('relative overflow-hidden', className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>3D Body Model</CardTitle>
          
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowLegend(!showLegend)}
            >
              <Layers className="w-4 h-4" />
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
      </CardHeader>
      
      <CardContent className="p-0">
        <div className="relative h-96 flex">
          {/* 3D Canvas */}
          <div className="flex-1">
            <Suspense 
              fallback={
                <div className="h-full flex items-center justify-center bg-gray-100">
                  <LoadingSpinner size="lg" showLabel label="Loading 3D model..." />
                </div>
              }
            >
              <Canvas
                camera={{ position: [5, 2, 5], fov: 50 }}
                style={{ background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)' }}
              >
                <ambientLight intensity={0.6} />
                <directionalLight position={[10, 10, 5]} intensity={1} />
                <pointLight position={[-10, 0, -10]} intensity={0.3} />
                
                <HumanBodyModel
                  showVitalSigns={showVitalSigns}
                  vitalSigns={vitalSigns}
                  highlightedSystems={activeHighlights}
                />
                
                <OrbitControls 
                  enablePan={true}
                  enableZoom={true}
                  enableRotate={true}
                  autoRotate={false}
                  maxDistance={15}
                  minDistance={3}
                  target={[0, 1, 0]}
                />
              </Canvas>
            </Suspense>
          </div>
          
          {/* Legend Panel */}
          {showLegend && (
            <div className="w-64 bg-gray-50 border-l p-4 overflow-y-auto">
              <SystemLegend
                systems={bodySystems}
                highlightedSystems={activeHighlights}
                onSystemToggle={handleSystemToggle}
              />
              
              {/* Vital Signs Summary */}
              {vitalSigns && (
                <div className="mt-6 space-y-3">
                  <h4 className="font-semibold text-sm">Current Vital Signs</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Heart Rate:</span>
                      <span className={clsx('font-medium', {
                        'text-green-600': vitalSigns.heartRate >= 60 && vitalSigns.heartRate <= 100,
                        'text-yellow-600': vitalSigns.heartRate > 100 || vitalSigns.heartRate < 60,
                        'text-red-600': vitalSigns.heartRate > 120 || vitalSigns.heartRate < 50
                      })}>
                        {vitalSigns.heartRate} BPM
                      </span>
                    </div>
                    
                    <div className="flex justify-between">
                      <span>O2 Saturation:</span>
                      <span className={clsx('font-medium', {
                        'text-green-600': vitalSigns.oxygenSaturation >= 95,
                        'text-yellow-600': vitalSigns.oxygenSaturation >= 90 && vitalSigns.oxygenSaturation < 95,
                        'text-red-600': vitalSigns.oxygenSaturation < 90
                      })}>
                        {vitalSigns.oxygenSaturation}%
                      </span>
                    </div>
                    
                    <div className="flex justify-between">
                      <span>Temperature:</span>
                      <span className={clsx('font-medium', {
                        'text-green-600': vitalSigns.temperature >= 36.1 && vitalSigns.temperature <= 37.2,
                        'text-yellow-600': vitalSigns.temperature > 37.2 && vitalSigns.temperature < 38.5,
                        'text-red-600': vitalSigns.temperature >= 38.5 || vitalSigns.temperature < 36.1
                      })}>
                        {vitalSigns.temperature.toFixed(1)}°C
                      </span>
                    </div>
                    
                    <div className="flex justify-between">
                      <span>Blood Pressure:</span>
                      <span className={clsx('font-medium', {
                        'text-green-600': vitalSigns.bloodPressure.systolic < 120 && vitalSigns.bloodPressure.diastolic < 80,
                        'text-yellow-600': vitalSigns.bloodPressure.systolic >= 120 && vitalSigns.bloodPressure.systolic < 140,
                        'text-red-600': vitalSigns.bloodPressure.systolic >= 140
                      })}>
                        {vitalSigns.bloodPressure.systolic}/{vitalSigns.bloodPressure.diastolic}
                      </span>
                    </div>
                  </div>
                </div>
              )}
              
              {/* Instructions */}
              <div className="mt-6 p-3 bg-blue-50 rounded-lg">
                <div className="flex items-start space-x-2">
                  <Info className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                  <div className="text-xs text-blue-800">
                    <p className="font-medium mb-1">How to use:</p>
                    <ul className="space-y-1">
                      <li>• Click systems to highlight</li>
                      <li>• Drag to rotate the model</li>
                      <li>• Scroll to zoom in/out</li>
                      <li>• Right-click and drag to pan</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default BodyModel;
