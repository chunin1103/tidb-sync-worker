-- Reorder Calculator Database Schema
-- Location: Agent Garden Database
-- Purpose: Store calculation sessions, questions, answers, and audit logs

-- Table 1: Calculation Sessions
CREATE TABLE IF NOT EXISTS reorder_sessions (
    session_id VARCHAR(36) PRIMARY KEY,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    csv_filename VARCHAR(255),
    total_products INT,
    manufacturer VARCHAR(100),
    status VARCHAR(20),  -- 'pending_questions', 'completed', 'exported'
    created_by VARCHAR(100),
    INDEX idx_created_at (created_at),
    INDEX idx_status (status)
);

-- Table 2: Clarification Questions
CREATE TABLE IF NOT EXISTS reorder_questions (
    question_id INT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(36),
    product_id INT,
    product_name VARCHAR(255),
    priority VARCHAR(10),  -- 'HIGH', 'MEDIUM', 'LOW'
    question_text TEXT,
    field_name VARCHAR(100),
    suggested_answer TEXT,
    client_answer TEXT,
    answered_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES reorder_sessions(session_id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_answered (answered_at)
);

-- Table 3: Manual Edit Audit Log
CREATE TABLE IF NOT EXISTS reorder_manual_edits (
    edit_id INT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(36),
    product_id INT,
    product_name VARCHAR(255),
    calculated_reorder_qty INT,
    manual_reorder_qty INT,
    difference INT,
    reason TEXT,
    edited_by VARCHAR(100),
    edited_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES reorder_sessions(session_id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_edited_at (edited_at)
);

-- Table 4: Decision Improvement Tracking
CREATE TABLE IF NOT EXISTS reorder_decision_learning (
    learning_id INT PRIMARY KEY AUTO_INCREMENT,
    question_type VARCHAR(50),
    question_text TEXT,
    client_answer TEXT,
    frequency INT DEFAULT 1,
    last_asked DATETIME,
    should_automate BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_question_type (question_type),
    INDEX idx_should_automate (should_automate)
);
