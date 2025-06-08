-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS legal_aid;
USE legal_aid;

-- Table for storing case metadata
CREATE TABLE IF NOT EXISTS cases (
    id INT AUTO_INCREMENT PRIMARY KEY,
    case_number VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    filing_date DATE,
    status VARCHAR(50),
    case_type VARCHAR(100),
    court VARCHAR(100),
    judge VARCHAR(100),
    province VARCHAR(50),  -- Ontario, Quebec, etc.
    court_level VARCHAR(50),
    practice_area ENUM(
        'family_law',
        'criminal_law',
        'immigration_law',
        'aboriginal_law',
        'employment_law',
        'civil_litigation',
        'real_estate',
        'wills_and_estates',
        'human_rights',
        'administrative_law',
        'constitutional_law',
        'environmental_law',
        'intellectual_property',
        'tax_law',
        'bankruptcy_insolvency',
        'corporate_commercial',
        'construction_law',
        'labour_relations',
        'class_actions',
        'indigenous_rights',
        'public_interest',
        'cyber_law',
        'health_law'
    ),
    case_category ENUM(
        'divorce',
        'child_custody',
        'maintenance',
        'adoption',
        'domestic_violence',
        'child_abuse',
        'child_support',
        'pre_nuptial',
        'post_nuptial',
        'annulment',
        'legal_separation',
        'parental_rights',
        'surrogacy',
        'elder_care',
        'other'
    ),
    spouse_names TEXT,
    children_info TEXT,
    property_details TEXT,
    verified_by VARCHAR(100),
    verification_status ENUM('pending', 'verified', 'rejected') DEFAULT 'pending',
    verification_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Clio-like fields
    matter_id VARCHAR(50),  -- Unique matter identifier
    client_id VARCHAR(50),  -- Client reference
    lead_id VARCHAR(50),    -- Lead reference
    matter_status ENUM('open', 'closed', 'suspended', 'cancelled'),
    billable_hours DECIMAL(10,2),
    total_amount DECIMAL(10,2),
    matter_type ENUM('matter', 'lead', 'opportunity'),
    next_action_date DATE,
    next_action_description TEXT,
    priority ENUM('low', 'medium', 'high', 'urgent'),
    matter_owner VARCHAR(100),  -- Primary lawyer assigned
    team_members TEXT,         -- JSON array of team members
    matter_tags TEXT           -- JSON array of tags
);
    case_category ENUM(
        'divorce',
        'child_custody',
        'maintenance',
        'adoption',
        'domestic_violence',
        'child_abuse',
        'child_support',
        'pre_nuptial',
        'post_nuptial',
        'annulment',
        'legal_separation',
        'parental_rights',
        'surrogacy',
        'elder_care',
        'other'
    ) NOT NULL,
    spouse_names TEXT,
    children_info TEXT,
    property_details TEXT,
    verified_by VARCHAR(100),
    verification_status ENUM('pending', 'verified', 'rejected') DEFAULT 'pending',
    verification_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Table for storing verification history
CREATE TABLE IF NOT EXISTS case_verifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    case_id INT,
    verified_by VARCHAR(100),
    verification_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('verified', 'rejected', 'updated'),
    notes TEXT,
    FOREIGN KEY (case_id) REFERENCES cases(id)
);

-- Table for storing case updates
CREATE TABLE IF NOT EXISTS case_updates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    case_id INT,
    updated_by VARCHAR(100),
    update_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    field_name VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    notes TEXT,
    FOREIGN KEY (case_id) REFERENCES cases(id)
);

-- Table for storing case statistics
CREATE TABLE IF NOT EXISTS case_statistics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    province VARCHAR(50),
    practice_area ENUM(
        'family_law',
        'criminal_law',
        'immigration_law',
        'aboriginal_law',
        'employment_law',
        'civil_litigation',
        'real_estate',
        'wills_and_estates',
        'human_rights',
        'administrative_law',
        'constitutional_law',
        'environmental_law',
        'intellectual_property',
        'tax_law',
        'bankruptcy_insolvency',
        'corporate_commercial',
        'construction_law',
        'labour_relations',
        'class_actions',
        'indigenous_rights',
        'public_interest',
        'cyber_law',
        'health_law'
    ),
    case_category ENUM(
        'divorce',
        'child_custody',
        'maintenance',
        'adoption',
        'domestic_violence',
        'child_abuse',
        'child_support',
        'pre_nuptial',
        'post_nuptial',
        'annulment',
        'legal_separation',
        'parental_rights',
        'surrogacy',
        'elder_care',
        'other'
    ),
    cases_opened INT DEFAULT 0,
    cases_closed INT DEFAULT 0,
    avg_case_duration DECIMAL(10,2),
    avg_billable_hours DECIMAL(10,2),
    total_amount_billed DECIMAL(15,2),
    avg_support_amount DECIMAL(10,2),
    avg_property_value DECIMAL(15,2),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_stats (province, practice_area, case_category)
);

-- Table for storing CanLII integration data
CREATE TABLE IF NOT EXISTS canlii_integration (
    id INT AUTO_INCREMENT PRIMARY KEY,
    case_id INT,
    canlii_id VARCHAR(100),
    canlii_url VARCHAR(255),
    canlii_citation VARCHAR(255),
    canlii_decision_date DATE,
    canlii_judges TEXT,
    canlii_court VARCHAR(100),
    canlii_proceedings_type VARCHAR(100),
    canlii_headnote TEXT,
    canlii_judgment TEXT,
    FOREIGN KEY (case_id) REFERENCES cases(id)
);

-- Table for storing legal aid statistics
CREATE TABLE IF NOT EXISTS legal_aid_statistics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    province VARCHAR(50),
    year INT,
    quarter ENUM('Q1', 'Q2', 'Q3', 'Q4'),
    total_applications INT,
    approved_applications INT,
    denied_applications INT,
    avg_processing_days INT,
    avg_case_duration_days INT,
    avg_support_amount DECIMAL(10,2),
    avg_legal_costs DECIMAL(10,2),
    avg_client_income DECIMAL(10,2),
    most_common_issues TEXT,
    PRIMARY KEY (province, year, quarter)
);

-- Table for storing case documents metadata
CREATE TABLE IF NOT EXISTS case_documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    case_id INT,
    document_name VARCHAR(255),
    document_type VARCHAR(100),
    file_path VARCHAR(255),
    document_date DATE,
    document_status ENUM('draft', 'final', 'archived'),
    document_category ENUM(
        'court_filings',
        'correspondence',
        'contracts',
        'pleadings',
        'briefs',
        'evidence',
        'settlement',
        'writs',
        'statements_of_claim',
        'defence',
        'affidavits',
        'motion_materials',
        'expert_reports',
        'judgment_orders',
        'settlement_agreements',
        'other'
    ),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_id) REFERENCES cases(id)
);

-- Table for storing case notes and activities
CREATE TABLE IF NOT EXISTS case_activities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    case_id INT,
    activity_type ENUM(
        'meeting',
        'call',
        'email',
        'court_appearance',
        'document_review',
        'research',
        'strategy',
        'billing'
    ),
    activity_date DATE,
    activity_notes TEXT,
    duration_minutes INT,
    billable BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_id) REFERENCES cases(id)
);

-- Table for storing case tasks
CREATE TABLE IF NOT EXISTS case_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    case_id INT,
    task_description TEXT,
    assigned_to VARCHAR(100),
    due_date DATE,
    priority ENUM('low', 'medium', 'high', 'urgent'),
    status ENUM('pending', 'in_progress', 'completed', 'cancelled'),
    completed_date DATE,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_id) REFERENCES cases(id)
);

-- Table for storing case participants
CREATE TABLE IF NOT EXISTS case_participants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    case_id INT,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(50),
    contact_info VARCHAR(255),
    FOREIGN KEY (case_id) REFERENCES cases(id)
);
