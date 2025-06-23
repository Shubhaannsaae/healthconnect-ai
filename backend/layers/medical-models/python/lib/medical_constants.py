"""Medical constants and reference values for healthcare applications"""

# ICD-10 Common Codes
ICD10_CODES = {
    'hypertension': {
        'I10': 'Essential hypertension',
        'I11': 'Hypertensive heart disease',
        'I12': 'Hypertensive chronic kidney disease',
        'I13': 'Hypertensive heart and chronic kidney disease'
    },
    'diabetes': {
        'E10': 'Type 1 diabetes mellitus',
        'E11': 'Type 2 diabetes mellitus',
        'E13': 'Other specified diabetes mellitus',
        'E14': 'Unspecified diabetes mellitus'
    },
    'cardiovascular': {
        'I20': 'Angina pectoris',
        'I21': 'Acute myocardial infarction',
        'I25': 'Chronic ischemic heart disease',
        'I50': 'Heart failure'
    }
}

# CPT Codes for Common Procedures
CPT_CODES = {
    'office_visits': {
        '99213': 'Office visit, established patient, level 3',
        '99214': 'Office visit, established patient, level 4',
        '99215': 'Office visit, established patient, level 5'
    },
    'laboratory': {
        '80053': 'Comprehensive metabolic panel',
        '85025': 'Complete blood count with differential',
        '83036': 'Hemoglobin A1c'
    }
}

# Laboratory Reference Ranges
LAB_REFERENCE_RANGES = {
    'complete_blood_count': {
        'hemoglobin': {
            'male': {'min': 13.8, 'max': 17.2, 'unit': 'g/dL'},
            'female': {'min': 12.1, 'max': 15.1, 'unit': 'g/dL'}
        },
        'hematocrit': {
            'male': {'min': 40.7, 'max': 50.3, 'unit': '%'},
            'female': {'min': 36.1, 'max': 44.3, 'unit': '%'}
        },
        'white_blood_cells': {'min': 4.5, 'max': 11.0, 'unit': '10³/μL'},
        'platelets': {'min': 150, 'max': 450, 'unit': '10³/μL'}
    },
    'basic_metabolic_panel': {
        'glucose': {'min': 70, 'max': 100, 'unit': 'mg/dL'},
        'sodium': {'min': 136, 'max': 145, 'unit': 'mEq/L'},
        'potassium': {'min': 3.5, 'max': 5.1, 'unit': 'mEq/L'},
        'chloride': {'min': 98, 'max': 107, 'unit': 'mEq/L'},
        'bun': {'min': 7, 'max': 20, 'unit': 'mg/dL'},
        'creatinine': {'min': 0.7, 'max': 1.3, 'unit': 'mg/dL'}
    },
    'lipid_panel': {
        'total_cholesterol': {'target': '<200', 'unit': 'mg/dL'},
        'ldl_cholesterol': {'target': '<100', 'unit': 'mg/dL'},
        'hdl_cholesterol': {
            'male': {'min': 40, 'unit': 'mg/dL'},
            'female': {'min': 50, 'unit': 'mg/dL'}
        },
        'triglycerides': {'target': '<150', 'unit': 'mg/dL'}
    }
}

# Vital Signs Normal Ranges
VITAL_SIGNS_RANGES = {
    'blood_pressure': {
        'normal': {'systolic': '<120', 'diastolic': '<80'},
        'elevated': {'systolic': '120-129', 'diastolic': '<80'},
        'stage_1_hypertension': {'systolic': '130-139', 'diastolic': '80-89'},
        'stage_2_hypertension': {'systolic': '≥140', 'diastolic': '≥90'},
        'hypertensive_crisis': {'systolic': '>180', 'diastolic': '>120'}
    },
    'heart_rate': {
        'bradycardia': '<60',
        'normal': '60-100',
        'tachycardia': '>100'
    },
    'respiratory_rate': {
        'adult': {'min': 12, 'max': 20, 'unit': 'breaths/min'},
        'child': {'min': 20, 'max': 30, 'unit': 'breaths/min'},
        'infant': {'min': 30, 'max': 60, 'unit': 'breaths/min'}
    },
    'temperature': {
        'hypothermia': '<95°F (35°C)',
        'normal': '97-99°F (36.1-37.2°C)',
        'fever': '>100.4°F (38°C)',
        'high_fever': '>103°F (39.4°C)'
    }
}

# Drug Classifications
DRUG_CLASSIFICATIONS = {
    'antihypertensives': {
        'ace_inhibitors': ['lisinopril', 'enalapril', 'captopril'],
        'arbs': ['losartan', 'valsartan', 'irbesartan'],
        'beta_blockers': ['metoprolol', 'atenolol', 'propranolol'],
        'calcium_channel_blockers': ['amlodipine', 'nifedipine', 'diltiazem'],
        'diuretics': ['hydrochlorothiazide', 'furosemide', 'spironolactone']
    },
    'diabetes_medications': {
        'insulin': ['insulin_regular', 'insulin_nph', 'insulin_glargine'],
        'metformin': ['metformin'],
        'sulfonylureas': ['glipizide', 'glyburide', 'glimepiride'],
        'sglt2_inhibitors': ['empagliflozin', 'canagliflozin', 'dapagliflozin']
    }
}

# Medical Specialties
MEDICAL_SPECIALTIES = {
    'primary_care': [
        'family_medicine',
        'internal_medicine',
        'pediatrics',
        'geriatrics'
    ],
    'cardiology': [
        'general_cardiology',
        'interventional_cardiology',
        'electrophysiology',
        'heart_failure'
    ],
    'emergency_medicine': [
        'emergency_medicine',
        'critical_care',
        'trauma_surgery'
    ]
}

# Emergency Triage Levels
TRIAGE_LEVELS = {
    1: {
        'name': 'Resuscitation',
        'color': 'red',
        'time_to_treatment': 'immediate',
        'examples': ['cardiac arrest', 'severe trauma', 'respiratory failure']
    },
    2: {
        'name': 'Emergent',
        'color': 'orange',
        'time_to_treatment': '15 minutes',
        'examples': ['chest pain', 'severe asthma', 'altered mental status']
    },
    3: {
        'name': 'Urgent',
        'color': 'yellow',
        'time_to_treatment': '30 minutes',
        'examples': ['moderate pain', 'vomiting', 'minor trauma']
    },
    4: {
        'name': 'Less Urgent',
        'color': 'green',
        'time_to_treatment': '60 minutes',
        'examples': ['minor injuries', 'cold symptoms', 'prescription refills']
    },
    5: {
        'name': 'Non-Urgent',
        'color': 'blue',
        'time_to_treatment': '120 minutes',
        'examples': ['chronic conditions', 'routine follow-up']
    }
}

# Pain Scales
PAIN_SCALES = {
    'numeric_rating_scale': {
        0: 'No pain',
        1: 'Minimal pain',
        2: 'Minimal pain',
        3: 'Mild pain',
        4: 'Mild pain',
        5: 'Moderate pain',
        6: 'Moderate pain',
        7: 'Severe pain',
        8: 'Severe pain',
        9: 'Very severe pain',
        10: 'Worst possible pain'
    },
    'wong_baker_faces': {
        0: 'No hurt',
        2: 'Hurts little bit',
        4: 'Hurts little more',
        6: 'Hurts even more',
        8: 'Hurts whole lot',
        10: 'Hurts worst'
    }
}

# Body Systems
BODY_SYSTEMS = {
    'cardiovascular': {
        'organs': ['heart', 'blood_vessels', 'blood'],
        'common_conditions': ['hypertension', 'coronary_artery_disease', 'heart_failure']
    },
    'respiratory': {
        'organs': ['lungs', 'trachea', 'bronchi', 'diaphragm'],
        'common_conditions': ['asthma', 'copd', 'pneumonia']
    },
    'endocrine': {
        'organs': ['pancreas', 'thyroid', 'adrenal_glands', 'pituitary'],
        'common_conditions': ['diabetes', 'hypothyroidism', 'hyperthyroidism']
    },
    'neurological': {
        'organs': ['brain', 'spinal_cord', 'nerves'],
        'common_conditions': ['stroke', 'seizures', 'migraine']
    }
}

# Medical Abbreviations
MEDICAL_ABBREVIATIONS = {
    'vital_signs': {
        'BP': 'Blood Pressure',
        'HR': 'Heart Rate',
        'RR': 'Respiratory Rate',
        'T': 'Temperature',
        'O2Sat': 'Oxygen Saturation'
    },
    'laboratory': {
        'CBC': 'Complete Blood Count',
        'BMP': 'Basic Metabolic Panel',
        'CMP': 'Comprehensive Metabolic Panel',
        'PT/INR': 'Prothrombin Time/International Normalized Ratio',
        'PTT': 'Partial Thromboplastin Time'
    },
    'medications': {
        'PO': 'By mouth',
        'IV': 'Intravenous',
        'IM': 'Intramuscular',
        'SQ': 'Subcutaneous',
        'PRN': 'As needed',
        'BID': 'Twice daily',
        'TID': 'Three times daily',
        'QID': 'Four times daily'
    }
}
