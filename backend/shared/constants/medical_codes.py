"""Medical coding constants for healthcare applications"""

# ICD-10-CM Diagnosis Codes
ICD10_DIAGNOSIS_CODES = {
    # Cardiovascular Diseases
    'I10': 'Essential (primary) hypertension',
    'I11.0': 'Hypertensive heart disease with heart failure',
    'I11.9': 'Hypertensive heart disease without heart failure',
    'I20.0': 'Unstable angina',
    'I20.1': 'Angina pectoris with documented spasm',
    'I20.8': 'Other forms of angina pectoris',
    'I20.9': 'Angina pectoris, unspecified',
    'I21.0': 'ST elevation (STEMI) myocardial infarction of anterior wall',
    'I21.1': 'ST elevation (STEMI) myocardial infarction of inferior wall',
    'I21.2': 'ST elevation (STEMI) myocardial infarction of other sites',
    'I21.3': 'ST elevation (STEMI) myocardial infarction of unspecified site',
    'I21.4': 'Non-ST elevation (NSTEMI) myocardial infarction',
    'I25.10': 'Atherosclerotic heart disease of native coronary artery without angina pectoris',
    'I25.110': 'Atherosclerotic heart disease of native coronary artery with unstable angina pectoris',
    'I50.1': 'Left ventricular failure, unspecified',
    'I50.9': 'Heart failure, unspecified',
    
    # Diabetes Mellitus
    'E10.10': 'Type 1 diabetes mellitus with ketoacidosis without coma',
    'E10.11': 'Type 1 diabetes mellitus with ketoacidosis with coma',
    'E10.9': 'Type 1 diabetes mellitus without complications',
    'E11.00': 'Type 2 diabetes mellitus with hyperosmolarity without nonketotic hyperglycemic-hyperosmolar coma (NKHHC)',
    'E11.01': 'Type 2 diabetes mellitus with hyperosmolarity with coma',
    'E11.9': 'Type 2 diabetes mellitus without complications',
    'E11.65': 'Type 2 diabetes mellitus with hyperglycemia',
    'E11.649': 'Type 2 diabetes mellitus with hypoglycemia without coma',
    
    # Respiratory Diseases
    'J44.0': 'Chronic obstructive pulmonary disease with acute lower respiratory infection',
    'J44.1': 'Chronic obstructive pulmonary disease with (acute) exacerbation',
    'J44.9': 'Chronic obstructive pulmonary disease, unspecified',
    'J45.0': 'Predominantly allergic asthma',
    'J45.1': 'Nonallergic asthma',
    'J45.9': 'Asthma, unspecified',
    'J18.9': 'Pneumonia, unspecified organism',
    
    # Mental Health
    'F32.0': 'Major depressive disorder, single episode, mild',
    'F32.1': 'Major depressive disorder, single episode, moderate',
    'F32.2': 'Major depressive disorder, single episode, severe without psychotic features',
    'F32.9': 'Major depressive disorder, single episode, unspecified',
    'F41.0': 'Panic disorder [episodic paroxysmal anxiety]',
    'F41.1': 'Generalized anxiety disorder',
    'F41.9': 'Anxiety disorder, unspecified'
}

# CPT Procedure Codes
CPT_PROCEDURE_CODES = {
    # Office Visits
    '99201': 'Office or other outpatient visit for the evaluation and management of a new patient (Level 1)',
    '99202': 'Office or other outpatient visit for the evaluation and management of a new patient (Level 2)',
    '99203': 'Office or other outpatient visit for the evaluation and management of a new patient (Level 3)',
    '99204': 'Office or other outpatient visit for the evaluation and management of a new patient (Level 4)',
    '99205': 'Office or other outpatient visit for the evaluation and management of a new patient (Level 5)',
    '99211': 'Office or other outpatient visit for the evaluation and management of an established patient (Level 1)',
    '99212': 'Office or other outpatient visit for the evaluation and management of an established patient (Level 2)',
    '99213': 'Office or other outpatient visit for the evaluation and management of an established patient (Level 3)',
    '99214': 'Office or other outpatient visit for the evaluation and management of an established patient (Level 4)',
    '99215': 'Office or other outpatient visit for the evaluation and management of an established patient (Level 5)',
    
    # Telemedicine
    '99441': 'Telephone evaluation and management service; 5-10 minutes',
    '99442': 'Telephone evaluation and management service; 11-20 minutes',
    '99443': 'Telephone evaluation and management service; 21-30 minutes',
    
    # Laboratory Tests
    '80053': 'Comprehensive metabolic panel',
    '80061': 'Lipid panel',
    '85025': 'Blood count; complete (CBC), automated',
    '83036': 'Hemoglobin; glycosylated (A1C)',
    '84443': 'Thyroid stimulating hormone (TSH)',
    '82947': 'Glucose; quantitative, blood',
    '83718': 'Lipoprotein, direct measurement; high density cholesterol (HDL cholesterol)',
    '83721': 'Lipoprotein, direct measurement; LDL cholesterol',
    
    # Cardiovascular Procedures
    '93000': 'Electrocardiogram, routine ECG with at least 12 leads',
    '93005': 'Electrocardiogram, routine ECG with at least 12 leads; tracing only',
    '93224': 'External electrocardiographic recording up to 48 hours by continuous rhythm recording',
    '93306': 'Echocardiography, transthoracic, real-time with image documentation',
    
    # Preventive Care
    'G0438': 'Annual wellness visit; includes a personalized prevention plan of service (PPS), initial visit',
    'G0439': 'Annual wellness visit, includes a personalized prevention plan of service (PPS), subsequent visit'
}

# HCPCS Level II Codes
HCPCS_CODES = {
    # Durable Medical Equipment
    'E0424': 'Stationary compressed gaseous oxygen system, rental',
    'E0431': 'Portable gaseous oxygen system, rental',
    'E0470': 'Respiratory assist device, bi-level pressure capability',
    'E0601': 'Continuous positive airway pressure (CPAP) device',
    
    # Supplies
    'A4253': 'Blood glucose test or reagent strips for home blood glucose monitor',
    'A4259': 'Insulin pen needle, per needle',
    'A4364': 'Adhesive, liquid or equal, any type, per oz',
    
    # Drugs
    'J1815': 'Injection, insulin, per 5 units',
    'J3420': 'Injection, vitamin B-12 cyanocobalamin, up to 1,000 mcg'
}

# NDC Drug Codes (National Drug Code)
NDC_DRUG_CODES = {
    # Common medications with NDC format examples
    'metformin_500mg': '00093-1074-01',
    'lisinopril_10mg': '00093-7663-01',
    'atorvastatin_20mg': '00093-7672-01',
    'amlodipine_5mg': '00093-7693-01',
    'metoprolol_50mg': '00093-7355-01',
    'omeprazole_20mg': '00093-7347-01',
    'levothyroxine_50mcg': '00093-4120-01',
    'hydrochlorothiazide_25mg': '00093-0058-01'
}

# SNOMED CT Codes (Systematized Nomenclature of Medicine Clinical Terms)
SNOMED_CODES = {
    # Clinical findings
    '38341003': 'Hypertensive disorder',
    '44054006': 'Diabetes mellitus type 2',
    '53741008': 'Coronary artery disease',
    '195967001': 'Asthma',
    '13645005': 'Chronic obstructive lung disease',
    '370143000': 'Major depressive disorder',
    '48694002': 'Anxiety',
    
    # Procedures
    '18956007': 'Electrocardiography',
    '40701008': 'Echocardiography',
    '77343006': 'Immunization',
    '182836005': 'Review of medication',
    
    # Body structures
    '80891009': 'Heart structure',
    '39607008': 'Lung structure',
    '181414000': 'Kidney structure',
    '69536005': 'Head structure'
}

# LOINC Codes (Logical Observation Identifiers Names and Codes)
LOINC_CODES = {
    # Vital signs
    '8480-6': 'Systolic blood pressure',
    '8462-4': 'Diastolic blood pressure',
    '8867-4': 'Heart rate',
    '9279-1': 'Respiratory rate',
    '8310-5': 'Body temperature',
    '2708-6': 'Oxygen saturation in Arterial blood',
    '29463-7': 'Body weight',
    '8302-2': 'Body height',
    '39156-5': 'Body mass index (BMI)',
    
    # Laboratory tests
    '33747-0': 'Hemoglobin A1c/Hemoglobin.total in Blood by HPLC',
    '2339-0': 'Glucose [Mass/volume] in Blood',
    '2093-3': 'Cholesterol [Mass/volume] in Serum or Plasma',
    '2085-9': 'Cholesterol in HDL [Mass/volume] in Serum or Plasma',
    '13457-7': 'Cholesterol in LDL [Mass/volume] in Serum or Plasma by calculation',
    '2571-8': 'Triglyceride [Mass/volume] in Serum or Plasma',
    '33765-2': 'Creatinine [Mass/volume] in Serum or Plasma',
    '3094-0': 'Urea nitrogen [Mass/volume] in Serum or Plasma'
}

# RxNorm Codes for Medications
RXNORM_CODES = {
    'metformin': '6809',
    'lisinopril': '29046',
    'atorvastatin': '83367',
    'amlodipine': '17767',
    'metoprolol': '6918',
    'omeprazole': '7646',
    'levothyroxine': '10582',
    'hydrochlorothiazide': '5487',
    'insulin_glargine': '274783',
    'aspirin': '1191'
}

# Medical Specialty Codes
MEDICAL_SPECIALTY_CODES = {
    '01': 'General Practice',
    '02': 'General Surgery',
    '03': 'Allergy/Immunology',
    '04': 'Otolaryngology',
    '05': 'Anesthesiology',
    '06': 'Cardiology',
    '07': 'Dermatology',
    '08': 'Family Practice',
    '09': 'Interventional Pain Management',
    '10': 'Gastroenterology',
    '11': 'Internal Medicine',
    '12': 'Osteopathic Manipulative Medicine',
    '13': 'Neurology',
    '14': 'Neurosurgery',
    '15': 'Speech Language Pathology',
    '16': 'Obstetrics/Gynecology',
    '17': 'Hospice and Palliative Care',
    '18': 'Ophthalmology',
    '19': 'Oral Surgery (dentists only)',
    '20': 'Orthopedic Surgery',
    '21': 'Cardiac Electrophysiology',
    '22': 'Pathology',
    '23': 'Sports Medicine',
    '24': 'Plastic and Reconstructive Surgery',
    '25': 'Physical Medicine and Rehabilitation',
    '26': 'Psychiatry',
    '27': 'Geriatric Psychiatry',
    '28': 'Colorectal Surgery (formerly proctology)',
    '29': 'Pulmonary Disease',
    '30': 'Diagnostic Radiology',
    '33': 'Thoracic Surgery',
    '34': 'Urology',
    '35': 'Sleep Medicine',
    '36': 'Nuclear Medicine',
    '37': 'Pediatric Medicine',
    '38': 'Geriatric Medicine',
    '39': 'Nephrology',
    '40': 'Hand Surgery',
    '41': 'Optometry',
    '42': 'Certified Nurse Midwife',
    '43': 'CRNA',
    '44': 'Infectious Disease',
    '46': 'Endocrinology',
    '48': 'Podiatry',
    '50': 'Nurse Practitioner',
    '89': 'Certified Clinical Nurse Specialist',
    '90': 'Medical Oncology',
    '91': 'Surgical Oncology',
    '92': 'Radiation Oncology',
    '93': 'Emergency Medicine',
    '94': 'Interventional Radiology',
    '98': 'Gynecologist/Oncologist',
    '99': 'Unknown Physician Specialty'
}
