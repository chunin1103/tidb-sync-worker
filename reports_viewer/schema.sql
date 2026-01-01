-- Reorder Calculator Database Schema
-- Location: Agent Garden Database (PostgreSQL)
-- Purpose: Store calculation sessions, questions, answers, and audit logs

-- Table 1: Calculation Sessions
CREATE TABLE IF NOT EXISTS reorder_sessions (
    session_id VARCHAR(36) PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    csv_filename VARCHAR(255),
    total_products INTEGER,
    manufacturer VARCHAR(100),
    status VARCHAR(20),  -- 'pending_questions', 'completed', 'exported'
    created_by VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_reorder_sessions_created_at ON reorder_sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_reorder_sessions_status ON reorder_sessions(status);

-- Table 2: Clarification Questions
CREATE TABLE IF NOT EXISTS reorder_questions (
    question_id SERIAL PRIMARY KEY,
    session_id VARCHAR(36),
    product_id INTEGER,
    product_name VARCHAR(255),
    priority VARCHAR(10),  -- 'HIGH', 'MEDIUM', 'LOW'
    question_text TEXT,
    field_name VARCHAR(100),
    suggested_answer TEXT,
    client_answer TEXT,
    answered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES reorder_sessions(session_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_reorder_questions_session_id ON reorder_questions(session_id);
CREATE INDEX IF NOT EXISTS idx_reorder_questions_answered ON reorder_questions(answered_at);

-- Table 3: Manual Edit Audit Log
CREATE TABLE IF NOT EXISTS reorder_manual_edits (
    edit_id SERIAL PRIMARY KEY,
    session_id VARCHAR(36),
    product_id INTEGER,
    product_name VARCHAR(255),
    calculated_reorder_qty INTEGER,
    manual_reorder_qty INTEGER,
    difference INTEGER,
    reason TEXT,
    edited_by VARCHAR(100),
    edited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES reorder_sessions(session_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_reorder_manual_edits_session_id ON reorder_manual_edits(session_id);
CREATE INDEX IF NOT EXISTS idx_reorder_manual_edits_edited_at ON reorder_manual_edits(edited_at);

-- Table 4: Decision Improvement Tracking
CREATE TABLE IF NOT EXISTS reorder_decision_learning (
    learning_id SERIAL PRIMARY KEY,
    question_type VARCHAR(50),
    question_text TEXT,
    client_answer TEXT,
    frequency INTEGER DEFAULT 1,
    last_asked TIMESTAMP,
    should_automate BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reorder_decision_learning_question_type ON reorder_decision_learning(question_type);
CREATE INDEX IF NOT EXISTS idx_reorder_decision_learning_should_automate ON reorder_decision_learning(should_automate);
