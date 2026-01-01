"""
Database helper functions for Reorder Calculator
Uses Agent Garden database (PostgreSQL via SQLAlchemy)
"""
import os
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Database configuration (same as Agent Garden)
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True) if DATABASE_URL else None
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None


def get_db_session():
    """Get database session"""
    if SessionLocal is None:
        raise RuntimeError("Database not configured. Set DATABASE_URL environment variable.")
    return SessionLocal()


def init_schema():
    """Initialize database schema (create tables if not exist)"""
    if engine is None:
        raise RuntimeError("Database not configured")

    with engine.connect() as conn:
        # Read schema file
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        with open(schema_path, 'r') as f:
            schema_sql = f.read()

        # Execute each CREATE TABLE statement
        for statement in schema_sql.split(';'):
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                conn.execute(text(statement))
        conn.commit()


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

def save_session(session_id: str, filename: str, total_products: int, manufacturer: str, created_by: str = 'web_user') -> None:
    """Create new calculation session"""
    db = get_db_session()
    try:
        db.execute(text("""
            INSERT INTO reorder_sessions (session_id, csv_filename, total_products, manufacturer, status, created_by)
            VALUES (:session_id, :filename, :total_products, :manufacturer, 'pending_questions', :created_by)
        """), {
            'session_id': session_id,
            'filename': filename,
            'total_products': total_products,
            'manufacturer': manufacturer,
            'created_by': created_by
        })
        db.commit()
    finally:
        db.close()


def get_session(session_id: str) -> Optional[Dict]:
    """Get session details"""
    db = get_db_session()
    try:
        result = db.execute(text("""
            SELECT session_id, csv_filename, total_products, manufacturer, status, created_at, created_by
            FROM reorder_sessions
            WHERE session_id = :session_id
        """), {'session_id': session_id}).fetchone()

        if result:
            return {
                'session_id': result[0],
                'csv_filename': result[1],
                'total_products': result[2],
                'manufacturer': result[3],
                'status': result[4],
                'created_at': result[5],
                'created_by': result[6]
            }
        return None
    finally:
        db.close()


def update_session_status(session_id: str, status: str) -> None:
    """Update session status"""
    db = get_db_session()
    try:
        db.execute(text("""
            UPDATE reorder_sessions
            SET status = :status
            WHERE session_id = :session_id
        """), {'session_id': session_id, 'status': status})
        db.commit()
    finally:
        db.close()


# ============================================================================
# QUESTION MANAGEMENT
# ============================================================================

def save_question(session_id: str, product_id: int, product_name: str, question: Dict) -> None:
    """Save a clarification question"""
    db = get_db_session()
    try:
        db.execute(text("""
            INSERT INTO reorder_questions (session_id, product_id, product_name, priority, question_text, field_name, suggested_answer)
            VALUES (:session_id, :product_id, :product_name, :priority, :question_text, :field_name, :suggested_answer)
        """), {
            'session_id': session_id,
            'product_id': product_id,
            'product_name': product_name,
            'priority': question['priority'],
            'question_text': question['question'],
            'field_name': question['field'],
            'suggested_answer': question['suggested_answer']
        })
        db.commit()
    finally:
        db.close()


def get_unanswered_questions(session_id: str) -> List[Dict]:
    """Get all unanswered questions for a session"""
    db = get_db_session()
    try:
        results = db.execute(text("""
            SELECT question_id, product_id, product_name, priority, question_text, field_name, suggested_answer
            FROM reorder_questions
            WHERE session_id = :session_id AND client_answer IS NULL
            ORDER BY
                CASE priority
                    WHEN 'HIGH' THEN 1
                    WHEN 'MEDIUM' THEN 2
                    WHEN 'LOW' THEN 3
                END,
                question_id
        """), {'session_id': session_id}).fetchall()

        return [{
            'question_id': r[0],
            'product_id': r[1],
            'product_name': r[2],
            'priority': r[3],
            'question_text': r[4],
            'field_name': r[5],
            'suggested_answer': r[6]
        } for r in results]
    finally:
        db.close()


def save_answer(question_id: int, answer: str) -> None:
    """Save client's answer to a question"""
    db = get_db_session()
    try:
        db.execute(text("""
            UPDATE reorder_questions
            SET client_answer = :answer, answered_at = :answered_at
            WHERE question_id = :question_id
        """), {
            'question_id': question_id,
            'answer': answer,
            'answered_at': datetime.utcnow()
        })
        db.commit()
    finally:
        db.close()


def get_answer(question_id: int) -> Optional[str]:
    """Get client's answer to a question"""
    db = get_db_session()
    try:
        result = db.execute(text("""
            SELECT client_answer
            FROM reorder_questions
            WHERE question_id = :question_id
        """), {'question_id': question_id}).fetchone()

        return result[0] if result else None
    finally:
        db.close()


# ============================================================================
# MANUAL EDIT TRACKING
# ============================================================================

def save_manual_edit(session_id: str, product_id: int, product_name: str,
                    calculated_qty: int, manual_qty: int, reason: str = '',
                    edited_by: str = 'web_user') -> None:
    """Log a manual edit to reorder quantity"""
    db = get_db_session()
    try:
        difference = manual_qty - calculated_qty
        db.execute(text("""
            INSERT INTO reorder_manual_edits
            (session_id, product_id, product_name, calculated_reorder_qty, manual_reorder_qty, difference, reason, edited_by)
            VALUES (:session_id, :product_id, :product_name, :calculated_qty, :manual_qty, :difference, :reason, :edited_by)
        """), {
            'session_id': session_id,
            'product_id': product_id,
            'product_name': product_name,
            'calculated_qty': calculated_qty,
            'manual_qty': manual_qty,
            'difference': difference,
            'reason': reason,
            'edited_by': edited_by
        })
        db.commit()
    finally:
        db.close()


def get_manual_edits(session_id: str) -> List[Dict]:
    """Get all manual edits for a session"""
    db = get_db_session()
    try:
        results = db.execute(text("""
            SELECT product_id, product_name, calculated_reorder_qty, manual_reorder_qty, difference, reason, edited_at, edited_by
            FROM reorder_manual_edits
            WHERE session_id = :session_id
            ORDER BY edited_at DESC
        """), {'session_id': session_id}).fetchall()

        return [{
            'product_id': r[0],
            'product_name': r[1],
            'calculated_qty': r[2],
            'manual_qty': r[3],
            'difference': r[4],
            'reason': r[5],
            'edited_at': r[6],
            'edited_by': r[7]
        } for r in results]
    finally:
        db.close()


# ============================================================================
# DECISION LEARNING
# ============================================================================

def track_question_for_learning(question_type: str, question_text: str, answer: str) -> None:
    """Track question/answer pair for future automation"""
    db = get_db_session()
    try:
        # Check if this question type already exists
        result = db.execute(text("""
            SELECT learning_id, frequency
            FROM reorder_decision_learning
            WHERE question_type = :question_type AND question_text = :question_text
        """), {'question_type': question_type, 'question_text': question_text}).fetchone()

        if result:
            # Increment frequency
            db.execute(text("""
                UPDATE reorder_decision_learning
                SET frequency = frequency + 1, last_asked = :last_asked, client_answer = :answer
                WHERE learning_id = :learning_id
            """), {
                'learning_id': result[0],
                'last_asked': datetime.utcnow(),
                'answer': answer
            })
        else:
            # Create new entry
            db.execute(text("""
                INSERT INTO reorder_decision_learning (question_type, question_text, client_answer, last_asked)
                VALUES (:question_type, :question_text, :answer, :last_asked)
            """), {
                'question_type': question_type,
                'question_text': question_text,
                'answer': answer,
                'last_asked': datetime.utcnow()
            })

        db.commit()
    finally:
        db.close()
