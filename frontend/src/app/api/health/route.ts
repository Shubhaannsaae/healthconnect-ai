/**
 * Health data API routes for HealthConnect AI
 * Next.js 14 API routes for health operations
 */

import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const patientId = searchParams.get('patientId');
    const type = searchParams.get('type');

    if (!patientId) {
      return NextResponse.json(
        { error: 'Patient ID is required' },
        { status: 400 }
      );
    }

    // Mock health data based on type
    switch (type) {
      case 'vital-signs':
        return NextResponse.json({
          success: true,
          data: generateMockVitalSigns()
        });
      case 'records':
        return NextResponse.json({
          success: true,
          data: generateMockHealthRecords()
        });
      case 'alerts':
        return NextResponse.json({
          success: true,
          data: generateMockAlerts()
        });
      default:
        return NextResponse.json({
          success: true,
          data: {
            vitalSigns: generateMockVitalSigns(),
            records: generateMockHealthRecords(),
            alerts: generateMockAlerts()
          }
        });
    }
  } catch (error) {
    console.error('Health API error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { type, data } = body;

    switch (type) {
      case 'vital-signs':
        return handleAddVitalSigns(data);
      case 'health-record':
        return handleAddHealthRecord(data);
      case 'alert':
        return handleCreateAlert(data);
      default:
        return NextResponse.json(
          { error: 'Invalid type' },
          { status: 400 }
        );
    }
  } catch (error) {
    console.error('Health API POST error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

function generateMockVitalSigns() {
  return {
    id: 'vs-' + Date.now(),
    heartRate: 72 + Math.floor(Math.random() * 20) - 10,
    bloodPressure: {
      systolic: 120 + Math.floor(Math.random() * 20) - 10,
      diastolic: 80 + Math.floor(Math.random() * 10) - 5
    },
    temperature: 37.0 + (Math.random() - 0.5),
    oxygenSaturation: 98 + Math.floor(Math.random() * 3) - 1,
    respiratoryRate: 16 + Math.floor(Math.random() * 6) - 3,
    timestamp: new Date().toISOString()
  };
}

function generateMockHealthRecords() {
  return Array.from({ length: 10 }, (_, i) => ({
    id: 'hr-' + (Date.now() + i),
    patientId: 'patient-123',
    recordType: 'vital_signs',
    vitalSigns: generateMockVitalSigns(),
    timestamp: new Date(Date.now() - i * 24 * 60 * 60 * 1000).toISOString(),
    notes: 'Regular health check'
  }));
}

function generateMockAlerts() {
  return [
    {
      id: 'alert-1',
      patientId: 'patient-123',
      alertType: 'vital_signs_abnormal',
      severity: 'medium',
      title: 'Elevated Heart Rate',
      message: 'Heart rate above normal range detected',
      timestamp: new Date().toISOString(),
      acknowledged: false,
      resolved: false
    }
  ];
}

async function handleAddVitalSigns(data: any) {
  // Mock response for adding vital signs
  return NextResponse.json({
    success: true,
    data: {
      id: 'vs-' + Date.now(),
      ...data,
      timestamp: new Date().toISOString()
    }
  });
}

async function handleAddHealthRecord(data: any) {
  return NextResponse.json({
    success: true,
    data: {
      id: 'hr-' + Date.now(),
      ...data,
      timestamp: new Date().toISOString()
    }
  });
}

async function handleCreateAlert(data: any) {
  return NextResponse.json({
    success: true,
    data: {
      id: 'alert-' + Date.now(),
      ...data,
      timestamp: new Date().toISOString(),
      acknowledged: false,
      resolved: false
    }
  });
}
