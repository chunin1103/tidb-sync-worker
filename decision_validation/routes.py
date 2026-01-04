"""
Decision Validation Flask Routes

Web interface for decision tree validation and gap analysis
"""

import sys
from pathlib import Path
from flask import Blueprint, render_template, request, jsonify
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from decision_engine.parser import MermaidDecisionParser
from decision_engine.mapper import DecisionMapper, MappingStatus
from decision_engine.validator import DecisionValidator
from decision_engine.analyzer import GapAnalyzer


# Create Blueprint
decision_validation_bp = Blueprint(
    'decision_validation',
    __name__,
    url_prefix='/decision-validation',
    template_folder='templates',
    static_folder='static'
)


# Initialize components
parser = MermaidDecisionParser()
mapper = DecisionMapper()
validator = DecisionValidator()
analyzer = GapAnalyzer(parser, mapper)


@decision_validation_bp.route('/')
def index():
    """Main dashboard showing all decision workflows"""
    wiki_root = Path(__file__).parent.parent.parent / "Production" / "wiki"
    workflow_dir = wiki_root / "03_Decision_Workflows"

    workflows = []

    if workflow_dir.exists():
        for md_file in sorted(workflow_dir.glob("*.md")):
            # Quick parse to get summary
            try:
                parsed = parser.parse_file(str(md_file))
                workflows.append({
                    'name': md_file.stem.replace('_', ' '),
                    'file': md_file.name,
                    'path': str(md_file.relative_to(wiki_root)),
                    'decision_count': len(parsed['decision_nodes']),
                    'process_count': len(parsed['process_nodes']),
                    'data_count': len(parsed['data_nodes'])
                })
            except Exception as e:
                workflows.append({
                    'name': md_file.stem.replace('_', ' '),
                    'file': md_file.name,
                    'error': str(e)
                })

    return render_template('decision_validation/index.html', workflows=workflows)


@decision_validation_bp.route('/workflow/<path:workflow_path>')
def workflow_detail(workflow_path):
    """Detailed view of a single workflow with gap analysis"""
    wiki_root = Path(__file__).parent.parent.parent / "Production" / "wiki"
    file_path = wiki_root / workflow_path

    if not file_path.exists():
        return jsonify({'error': 'Workflow not found'}), 404

    # Perform gap analysis
    analysis = analyzer.analyze_file(str(file_path))

    # Get workflow info
    workflow_info = {
        'name': file_path.stem.replace('_', ' '),
        'file': file_path.name,
        'path': workflow_path
    }

    return render_template(
        'decision_validation/workflow_detail.html',
        workflow=workflow_info,
        analysis=analysis
    )


@decision_validation_bp.route('/clarifications')
def clarifications_list():
    """List all clarification questions across all workflows"""
    wiki_root = Path(__file__).parent.parent.parent / "Production" / "wiki"

    # Analyze all workflows
    all_analyses = analyzer.analyze_all_workflows(str(wiki_root))

    # Collect all clarification questions
    all_questions = []

    for file_path, analysis in all_analyses.items():
        for question in analysis.clarification_questions:
            question['workflow'] = Path(file_path).stem.replace('_', ' ')
            question['workflow_file'] = Path(file_path).name
            all_questions.append(question)

    # Sort by priority
    priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
    all_questions.sort(key=lambda q: priority_order.get(q['priority'], 3))

    # Group by priority
    grouped = {
        'HIGH': [q for q in all_questions if q['priority'] == 'HIGH'],
        'MEDIUM': [q for q in all_questions if q['priority'] == 'MEDIUM'],
        'LOW': [q for q in all_questions if q['priority'] == 'LOW']
    }

    summary = {
        'total': len(all_questions),
        'high': len(grouped['HIGH']),
        'medium': len(grouped['MEDIUM']),
        'low': len(grouped['LOW'])
    }

    return render_template(
        'decision_validation/clarifications.html',
        questions=all_questions,
        grouped=grouped,
        summary=summary
    )


@decision_validation_bp.route('/clarification/<question_id>')
def clarification_detail(question_id):
    """Detail view for a single clarification question with response form"""
    # Find the question across all workflows
    wiki_root = Path(__file__).parent.parent.parent / "Production" / "wiki"
    all_analyses = analyzer.analyze_all_workflows(str(wiki_root))

    question_data = None
    workflow_info = None

    for file_path, analysis in all_analyses.items():
        for question in analysis.clarification_questions:
            if question['id'] == question_id:
                question_data = question
                workflow_info = {
                    'name': Path(file_path).stem.replace('_', ' '),
                    'file': Path(file_path).name,
                    'path': str(Path(file_path).relative_to(wiki_root))
                }
                break
        if question_data:
            break

    if not question_data:
        return jsonify({'error': 'Question not found'}), 404

    return render_template(
        'decision_validation/clarification_form.html',
        question=question_data,
        workflow=workflow_info
    )


@decision_validation_bp.route('/api/submit-clarification', methods=['POST'])
def submit_clarification():
    """Submit client clarification for a decision mapping"""
    data = request.json

    question_id = data.get('question_id')
    decision_id = data.get('decision_id')
    table = data.get('table')
    column = data.get('column')
    calculation = data.get('calculation')
    filters = data.get('filters', {})
    notes = data.get('notes', '')

    if not decision_id:
        return jsonify({'error': 'Missing decision_id'}), 400

    # Update mapping
    updates = {
        'status': 'mapped',
        'notes': notes
    }

    if table:
        updates['table'] = table
    if column:
        updates['column'] = column
    if calculation:
        updates['calculation'] = calculation
    if filters:
        updates['filters'] = filters

    try:
        mapper.update_mapping(decision_id, updates)

        return jsonify({
            'success': True,
            'message': 'Mapping updated successfully',
            'question_id': question_id,
            'decision_id': decision_id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@decision_validation_bp.route('/api/analyze-workflow/<path:workflow_path>')
def api_analyze_workflow(workflow_path):
    """API endpoint for workflow gap analysis (JSON)"""
    wiki_root = Path(__file__).parent.parent.parent / "Production" / "wiki"
    file_path = wiki_root / workflow_path

    if not file_path.exists():
        return jsonify({'error': 'Workflow not found'}), 404

    analysis = analyzer.analyze_file(str(file_path))

    return jsonify(analysis.to_dict())


@decision_validation_bp.route('/api/summary')
def api_summary():
    """API endpoint for overall summary across all workflows"""
    wiki_root = Path(__file__).parent.parent.parent / "Production" / "wiki"

    all_analyses = analyzer.analyze_all_workflows(str(wiki_root))
    summary = analyzer.generate_summary_report(all_analyses)

    return jsonify(summary)


@decision_validation_bp.route('/api/validate-decision', methods=['POST'])
def api_validate_decision():
    """Validate a mapped decision against database"""
    data = request.json

    decision_id = data.get('decision_id')
    context = data.get('context', {})

    if not decision_id:
        return jsonify({'error': 'Missing decision_id'}), 400

    # Get mapping
    mapping = mapper.mappings.get(decision_id)

    if not mapping:
        return jsonify({'error': 'Decision not mapped'}), 404

    # Validate
    result = validator.validate_decision(mapping.to_dict(), context)

    return jsonify(result.to_dict())


@decision_validation_bp.route('/export/<format>')
def export_report(format):
    """Export gap analysis report"""
    wiki_root = Path(__file__).parent.parent.parent / "Production" / "wiki"

    all_analyses = analyzer.analyze_all_workflows(str(wiki_root))
    summary = analyzer.generate_summary_report(all_analyses)

    if format == 'json':
        return jsonify(summary)

    elif format == 'csv':
        # Generate CSV of all clarification questions
        import csv
        from io import StringIO

        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(['ID', 'Priority', 'Category', 'Workflow', 'Question', 'Clarification Needed'])

        # Rows
        for file_path, analysis in all_analyses.items():
            workflow_name = Path(file_path).stem.replace('_', ' ')
            for question in analysis.clarification_questions:
                writer.writerow([
                    question['id'],
                    question['priority'],
                    question['category'],
                    workflow_name,
                    question.get('question_text', question.get('field_name', 'N/A')),
                    question['clarification_needed'][:200]
                ])

        output.seek(0)
        return output.getvalue(), 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment; filename=clarification_questions.csv'
        }

    else:
        return jsonify({'error': 'Invalid format'}), 400


# Error handlers
@decision_validation_bp.errorhandler(404)
def not_found(error):
    return render_template('decision_validation/404.html'), 404


@decision_validation_bp.errorhandler(500)
def internal_error(error):
    return render_template('decision_validation/500.html'), 500
