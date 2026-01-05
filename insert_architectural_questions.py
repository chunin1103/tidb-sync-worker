"""
Insert architectural questions for Bullseye Decision Tree refinement
These questions help the client guide system design decisions
"""
import sys
import os
from datetime import datetime

# Add parent directory to path to import database module
sys.path.insert(0, os.path.dirname(__file__))

from reports_viewer.database import save_session, save_question, save_answer, get_db_session
from sqlalchemy import text

def insert_architectural_questions():
    """Insert Decision Tree & Calculator architectural questions"""

    # Create special session for architectural questions
    session_id = f"ARCH-DecisionTree-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    filename = "Decision_Tree_Refinement_Questions.md"
    manufacturer = "Bullseye Glass"

    print(f"Creating session: {session_id}")
    save_session(
        session_id=session_id,
        filename=filename,
        total_products=0,  # No products, these are system questions
        manufacturer=manufacturer,
        created_by='claude_analysis'
    )

    # Define questions
    questions = [
        # Question 1: Holly Berry Red
        {
            'priority': 'HIGH',
            'question_text': 'Holly Berry Red seasonal rule: Is the "pre-order by June 30th" requirement still active? Should the decision tree include a special node for seasonal products that require pre-ordering by specific dates?',
            'field_name': 'holly_berry_red_seasonal_rule',
            'suggested_answer': 'Yes - add seasonal product decision node to tree',
            'product_id': 0,
            'product_name': 'SYSTEM: Seasonal Products Logic',
            'answer': None  # Unanswered
        },

        # Question 2: Inventory Translation Rule
        {
            'priority': 'HIGH',
            'question_text': 'Inventory Translation Rule ("Even Half Sheet count = Full Sheets"): Is this rule only for Cut Sheet system CSV interpretation? Should we remove it from VENDOR ORDERING context to avoid confusion between the three systems (Ordering vs Receiving vs Cut Sheets)?',
            'field_name': 'inventory_translation_rule_scope',
            'suggested_answer': 'Yes - this is Cut Sheet only, remove from ordering documentation',
            'product_id': 0,
            'product_name': 'SYSTEM: System Boundary Clarity',
            'answer': None  # Unanswered
        },

        # Question 3: Calculator Scope
        {
            'priority': 'HIGH',
            'question_text': 'Calculator Implementation Scope: Is the calculator intentionally simplified for CSV workflow (flag cascade opportunities for manual review)? Or should it implement the full 5-step algorithm automatically (cascade calculation, product family grouping, BEFORE/AFTER spreadsheets)?',
            'field_name': 'calculator_implementation_scope',
            'suggested_answer': 'Keep simplified - full 5-step algorithm requires manual validation',
            'product_id': 0,
            'product_name': 'SYSTEM: Calculator Architecture',
            'answer': None  # Unanswered
        },

        # Question 4: Formulas in Decision Tree
        {
            'priority': 'MEDIUM',
            'question_text': 'Formulas Reference Section: Should the decision tree include implementation-ready Python code snippets (math.ceil, exact formulas) in addition to the conceptual formulas currently shown?',
            'field_name': 'formulas_code_snippets',
            'suggested_answer': 'Yes - add "Formulas Reference" section with Python-ready code',
            'product_id': 0,
            'product_name': 'SYSTEM: Decision Tree Formulas',
            'answer': None  # Unanswered
        },

        # Question 6: Validated Examples (ANSWERED: No)
        {
            'priority': 'MEDIUM',
            'question_text': 'Validated Examples Expansion: Should we re-validate products 1-16 using the current decision tree and add all 25 validation examples to the decision tree documentation (currently has 3 examples)? Note: REORDER_RULES.md shows only products 17-25 are validated.',
            'field_name': 'validated_examples_expansion',
            'suggested_answer': 'No - keep current 3 examples, reference external validation',
            'product_id': 0,
            'product_name': 'SYSTEM: Validation Examples',
            'answer': 'No'  # PRE-ANSWERED
        },

        # Question 7: PDF Export Requirements (ANSWERED: No)
        {
            'priority': 'MEDIUM',
            'question_text': 'PDF Export Requirements in Decision Tree: Should the decision tree include output format specifications (PDF structure, column headers, BEFORE/AFTER spreadsheet layouts)? Or keep output format separate from calculation logic?',
            'field_name': 'pdf_export_in_decision_tree',
            'suggested_answer': 'No - keep separate in "Reorder System Architecture" document',
            'product_id': 0,
            'product_name': 'SYSTEM: Output Format Specification',
            'answer': 'No'  # PRE-ANSWERED
        },

        # Question 8: Calculator Architecture (MOST CRITICAL)
        {
            'priority': 'HIGH',
            'question_text': 'Calculator Full Algorithm Implementation: Which approach for calculator? (A) Keep simplified - flag cascade opportunities, manual spreadsheet validation, simpler code; (B) Implement full 5-step algorithm - product family grouping (Parent ID), automatic cascade calculation, BEFORE/AFTER spreadsheets, fully automated. Also specify: Do you need product family support to group Half/10×10/5×10/5×5 by Parent ID?',
            'field_name': 'calculator_architecture_decision',
            'suggested_answer': 'Option A - Keep simplified with manual validation for quality control',
            'product_id': 0,
            'product_name': 'SYSTEM: Calculator Full Algorithm',
            'answer': None  # Unanswered
        }
    ]

    # Insert questions
    question_ids = []
    for q in questions:
        print(f"Inserting question: {q['product_name']}")

        # Insert the question
        save_question(
            session_id=session_id,
            product_id=q['product_id'],
            product_name=q['product_name'],
            question={
                'priority': q['priority'],
                'question': q['question_text'],
                'field': q['field_name'],
                'suggested_answer': q['suggested_answer']
            }
        )

        # If pre-answered, get the question_id and save the answer
        if q['answer'] is not None:
            db = get_db_session()
            try:
                result = db.execute(text("""
                    SELECT question_id FROM reorder_questions
                    WHERE session_id = :session_id AND field_name = :field_name
                """), {
                    'session_id': session_id,
                    'field_name': q['field_name']
                }).fetchone()

                if result:
                    question_id = result[0]
                    print(f"  → Pre-answering with: {q['answer']}")
                    save_answer(question_id, q['answer'])
            finally:
                db.close()

    print(f"\n✅ Successfully inserted {len(questions)} architectural questions")
    print(f"📊 Session ID: {session_id}")
    print(f"🌐 View at: https://gpt-mcp.onrender.com/reports/reorder-calculator/questions")
    print(f"\nQuestions breakdown:")
    print(f"  - Unanswered (need client input): Questions 1, 2, 3, 4, 8")
    print(f"  - Pre-answered 'No': Questions 6, 7")
    print(f"  - Skipped (per request): Question 5")


if __name__ == '__main__':
    insert_architectural_questions()
