"""
Flask routes for Reorder Calculator
Handles CSV upload, question/answer workflow, and export
"""
import os
import uuid
import sqlite3
import pandas as pd
from flask import render_template, request, redirect, Response, jsonify, url_for
from . import reports_bp
from .decision_engine import OceansideCalculator, BullseyeCalculator
from .database import (
    save_session, get_session, update_session_status,
    save_question, get_unanswered_questions, save_answer,
    save_manual_edit, get_manual_edits,
    track_question_for_learning
)


# ============================================================================
# LANDING PAGE
# ============================================================================

@reports_bp.route('/reorder-calculator')
def reorder_calculator_home():
    """Landing page with upload form"""
    return render_template('reorder_upload.html')


# ============================================================================
# CSV UPLOAD & PROCESSING
# ============================================================================

@reports_bp.route('/reorder-calculator/upload', methods=['POST'])
def upload_csv():
    """Process uploaded CSV and calculate reorder quantities"""
    try:
        # Validate file upload
        if 'csv_file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        csv_file = request.files['csv_file']
        if csv_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        manufacturer = request.form.get('manufacturer', 'Oceanside Glass')

        # Create session
        session_id = str(uuid.uuid4())

        # Read CSV
        try:
            df = pd.read_csv(csv_file)
        except Exception as e:
            return jsonify({'error': f'Failed to read CSV: {str(e)}'}), 400

        # Validate required columns
        required = ['Product_Name', 'Product_ID', 'Purchased', 'Quantity_in_Stock']
        missing = [col for col in required if col not in df.columns]
        if missing:
            return jsonify({'error': f'Missing required columns: {", ".join(missing)}'}), 400

        # Create temp_sessions directory if not exists
        temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp_sessions')
        os.makedirs(temp_dir, exist_ok=True)

        # Save to SQLite temp DB
        db_path = os.path.join(temp_dir, f'{session_id}.db')
        conn = sqlite3.connect(db_path)

        # Add calculated columns to dataframe
        df['Years_in_Stock'] = None
        df['Reorder_Quantity'] = 0
        df['Reorder_Reason'] = ''
        df['Calculation_Details'] = ''

        # Save to SQLite
        df.to_sql('products', conn, index=False, if_exists='replace')

        # Save session to database
        save_session(session_id, csv_file.filename, len(df), manufacturer)

        # Calculate reorder quantities - select calculator based on manufacturer
        if manufacturer == 'Bullseye Glass':
            calculator = BullseyeCalculator()
        else:  # Default to Oceanside
            calculator = OceansideCalculator()

        all_questions = []

        for idx, row in df.iterrows():
            product = row.to_dict()
            result = calculator.calculate(product)

            # Update product with calculated values
            conn.execute("""
                UPDATE products
                SET Years_in_Stock = ?,
                    Reorder_Quantity = ?,
                    Reorder_Reason = ?,
                    Calculation_Details = ?
                WHERE Product_ID = ?
            """, (
                result['years_in_stock'],
                result['reorder_quantity'],
                result['reason'],
                str(result['calculation_details']),
                product['Product_ID']
            ))

            # Collect questions
            if result['questions']:
                for q in result['questions']:
                    save_question(session_id, product['Product_ID'], product['Product_Name'], q)
                    all_questions.extend(result['questions'])

        conn.commit()
        conn.close()

        # Redirect based on questions
        if all_questions:
            return redirect(url_for('reports.show_questions', session_id=session_id))
        else:
            update_session_status(session_id, 'completed')
            return redirect(url_for('reports.download_page', session_id=session_id))

    except Exception as e:
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500


# ============================================================================
# QUESTIONS & ANSWERS
# ============================================================================

@reports_bp.route('/reorder-calculator/questions/<session_id>')
def show_questions(session_id):
    """Show clarification questions"""
    session = get_session(session_id)
    if not session:
        return "Session not found", 404

    questions = get_unanswered_questions(session_id)

    if not questions:
        # No questions left, go to download
        update_session_status(session_id, 'completed')
        return redirect(url_for('reports.download_page', session_id=session_id))

    return render_template('reorder_questions.html',
                          questions=questions,
                          session=session)


@reports_bp.route('/reorder-calculator/submit-answers/<session_id>', methods=['POST'])
def submit_answers(session_id):
    """Store client answers and recalculate"""
    try:
        # Get all question IDs from form
        question_ids = request.form.getlist('question_id[]')

        if not question_ids:
            return jsonify({'error': 'No answers provided'}), 400

        # Store answers
        for question_id in question_ids:
            answer = request.form.get(f'answer_{question_id}', '').strip()
            if answer:
                save_answer(int(question_id), answer)

                # Track for learning
                # TODO: Get question type from database
                track_question_for_learning('manual_review', f'Question {question_id}', answer)

        # TODO: Implement recalculation with answers
        # For now, just mark session as completed
        update_session_status(session_id, 'completed')

        # Check if more questions
        remaining = get_unanswered_questions(session_id)
        if remaining:
            return redirect(url_for('reports.show_questions', session_id=session_id))
        else:
            return redirect(url_for('reports.download_page', session_id=session_id))

    except Exception as e:
        return jsonify({'error': f'Failed to save answers: {str(e)}'}), 500


# ============================================================================
# DOWNLOAD & EXPORT
# ============================================================================

@reports_bp.route('/reorder-calculator/download/<session_id>')
def download_page(session_id):
    """Show download page with preview"""
    session = get_session(session_id)
    if not session:
        return "Session not found", 404

    # Load data from SQLite
    temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp_sessions')
    db_path = os.path.join(temp_dir, f'{session_id}.db')

    if not os.path.exists(db_path):
        return "Session data not found", 404

    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM products", conn)
    conn.close()

    # Get summary stats
    total_products = len(df)
    products_needing_reorder = len(df[df['Reorder_Quantity'] > 0])
    total_units_to_order = df['Reorder_Quantity'].sum()
    zero_stock_count = len(df[df['Quantity_in_Stock'] == 0])

    stats = {
        'total_products': total_products,
        'products_needing_reorder': products_needing_reorder,
        'total_units_to_order': int(total_units_to_order),
        'zero_stock_count': zero_stock_count
    }

    # Get preview (first 20 products needing reorder)
    preview_df = df[df['Reorder_Quantity'] > 0].head(20)
    preview = preview_df.to_dict('records')

    return render_template('reorder_download.html',
                          session=session,
                          stats=stats,
                          preview=preview)


@reports_bp.route('/reorder-calculator/export/<session_id>')
def export_csv(session_id):
    """Export final CSV with reorder_quantity"""
    session = get_session(session_id)
    if not session:
        return "Session not found", 404

    # Load data from SQLite
    temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp_sessions')
    db_path = os.path.join(temp_dir, f'{session_id}.db')

    if not os.path.exists(db_path):
        return "Session data not found", 404

    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM products", conn)
    conn.close()

    # Generate CSV
    csv_data = df.to_csv(index=False)

    # Update session status
    update_session_status(session_id, 'exported')

    return Response(
        csv_data,
        mimetype='text/csv',
        headers={"Content-disposition": f"attachment; filename=reorder_calculation_{session_id}.csv"}
    )


# ============================================================================
# MANUAL EDIT TRACKING
# ============================================================================

@reports_bp.route('/reorder-calculator/audit/<session_id>')
def show_audit(session_id):
    """Show manual edits log"""
    session = get_session(session_id)
    if not session:
        return "Session not found", 404

    edits = get_manual_edits(session_id)

    return render_template('reorder_audit.html',
                          session=session,
                          edits=edits)


@reports_bp.route('/reorder-calculator/track-edit/<session_id>', methods=['POST'])
def track_manual_edit(session_id):
    """Track a manual edit (called when user re-uploads edited CSV)"""
    try:
        product_id = request.json.get('product_id')
        product_name = request.json.get('product_name')
        calculated_qty = request.json.get('calculated_qty')
        manual_qty = request.json.get('manual_qty')
        reason = request.json.get('reason', '')

        save_manual_edit(session_id, product_id, product_name, calculated_qty, manual_qty, reason)

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

@reports_bp.route('/reorder-calculator/sessions')
def list_sessions():
    """List all calculation sessions"""
    # TODO: Implement session listing
    return jsonify({'message': 'Session listing not yet implemented'}), 501
