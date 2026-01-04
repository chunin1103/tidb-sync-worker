"""
Gap Analyzer - Identifies unmapped decision tree nodes

Analyzes decision trees to find:
- Unmapped decisions (no database mapping)
- Unclear decisions (need client clarification)
- Partial mappings (incomplete)
- Data requirements not available in database
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import json


@dataclass
class GapAnalysis:
    """Results of gap analysis for a decision tree"""
    source_file: str
    total_decisions: int
    total_data_nodes: int
    mapped_count: int
    partial_count: int
    unmapped_count: int
    unclear_count: int

    unmapped_decisions: List[Dict] = field(default_factory=list)
    unclear_decisions: List[Dict] = field(default_factory=list)
    partial_decisions: List[Dict] = field(default_factory=list)
    missing_data_fields: List[Dict] = field(default_factory=list)

    clarification_questions: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'source_file': self.source_file,
            'summary': {
                'total_decisions': self.total_decisions,
                'total_data_nodes': self.total_data_nodes,
                'mapped': self.mapped_count,
                'partial': self.partial_count,
                'unmapped': self.unmapped_count,
                'unclear': self.unclear_count,
                'coverage_percentage': round((self.mapped_count / max(self.total_decisions, 1)) * 100, 1)
            },
            'gaps': {
                'unmapped_decisions': self.unmapped_decisions,
                'unclear_decisions': self.unclear_decisions,
                'partial_decisions': self.partial_decisions,
                'missing_data_fields': self.missing_data_fields
            },
            'clarification_questions': self.clarification_questions
        }


class GapAnalyzer:
    """
    Analyzes decision trees to identify gaps in database mappings

    Responsibilities:
    - Compare decision nodes against mapping configuration
    - Identify unmapped/unclear decisions
    - Generate clarification questions for client
    - Track data requirements vs available database fields
    """

    def __init__(self, parser, mapper):
        """
        Initialize analyzer

        Args:
            parser: MermaidDecisionParser instance
            mapper: DecisionMapper instance
        """
        self.parser = parser
        self.mapper = mapper

    def analyze_file(self, file_path: str) -> GapAnalysis:
        """
        Analyze a single wiki file for mapping gaps

        Args:
            file_path: Path to markdown file with decision trees

        Returns:
            GapAnalysis object with detailed gap information
        """
        # Parse decision tree
        parsed = self.parser.parse_file(file_path)
        decisions = self.parser.extract_decision_points()
        data_reqs = self.parser.extract_data_requirements()

        # Create mappings for all decisions
        for decision in decisions:
            self.mapper.create_mapping(decision)

        # Analyze gaps
        unmapped = []
        unclear = []
        partial = []
        mapped_count = 0

        for decision in decisions:
            decision_id = decision['node_id']
            mapping = self.mapper.mappings.get(decision_id)

            if not mapping:
                unmapped.append(decision)
                continue

            if mapping.status.value == 'mapped':
                mapped_count += 1
            elif mapping.status.value == 'partial':
                partial.append({
                    **decision,
                    'current_mapping': mapping.to_dict(),
                    'clarification': mapping.clarification_needed
                })
            elif mapping.status.value == 'unclear':
                unclear.append({
                    **decision,
                    'current_mapping': mapping.to_dict(),
                    'clarification': mapping.clarification_needed
                })
            elif mapping.status.value == 'unmapped':
                unmapped.append(decision)

        # Analyze data requirements
        missing_fields = self._analyze_data_requirements(data_reqs)

        # Generate clarification questions
        questions = self._generate_clarification_questions(unmapped, unclear, partial, missing_fields)

        return GapAnalysis(
            source_file=file_path,
            total_decisions=len(decisions),
            total_data_nodes=len(parsed['data_nodes']),
            mapped_count=mapped_count,
            partial_count=len(partial),
            unmapped_count=len(unmapped),
            unclear_count=len(unclear),
            unmapped_decisions=unmapped,
            unclear_decisions=unclear,
            partial_decisions=partial,
            missing_data_fields=missing_fields,
            clarification_questions=questions
        )

    def analyze_all_workflows(self, wiki_path: str) -> Dict[str, GapAnalysis]:
        """
        Analyze all decision workflow files in wiki

        Args:
            wiki_path: Path to wiki root directory

        Returns:
            Dictionary mapping file paths to GapAnalysis objects
        """
        wiki_root = Path(wiki_path)
        workflow_dir = wiki_root / "03_Decision_Workflows"

        results = {}

        if not workflow_dir.exists():
            return results

        # Analyze each decision workflow file
        for md_file in workflow_dir.glob("*.md"):
            analysis = self.analyze_file(str(md_file))
            results[str(md_file)] = analysis

        return results

    def _analyze_data_requirements(self, data_reqs: List[Dict]) -> List[Dict]:
        """
        Analyze data requirements against database schema

        Args:
            data_reqs: List of data requirement dictionaries

        Returns:
            List of missing/unclear data fields
        """
        missing = []

        # Get available tables/columns from mapper's schema
        available_tables = set(self.mapper.schema_guide.get('tables', {}).keys())

        for req in data_reqs:
            field_name = req['field_name']

            # Check if field name matches database patterns
            is_database_field = self._looks_like_database_field(field_name)

            if is_database_field:
                # Try to find in schema
                found = self._find_field_in_schema(field_name)

                if not found:
                    missing.append({
                        **req,
                        'reason': 'Field name suggests database column but not found in schema',
                        'clarification_needed': f'Is "{field_name}" stored in the database? '
                                                 f'If so, which table and column?'
                    })
            else:
                # Might be a calculated field or business term
                missing.append({
                    **req,
                    'reason': 'Business term or calculated field - needs mapping definition',
                    'clarification_needed': f'How is "{field_name}" calculated or stored? '
                                             f'Provide formula or database location.'
                })

        return missing

    def _looks_like_database_field(self, field_name: str) -> bool:
        """
        Check if field name looks like a database column

        Patterns:
        - snake_case (products_quantity)
        - contains "id", "date", "status"
        """
        db_indicators = ['_id', '_date', '_status', '_name', '_quantity', '_price', '_cost']

        # Snake case pattern
        if '_' in field_name and field_name.islower():
            return True

        # Contains database indicators
        if any(indicator in field_name.lower() for indicator in db_indicators):
            return True

        return False

    def _find_field_in_schema(self, field_name: str) -> Optional[Dict]:
        """
        Try to find field in database schema

        Returns:
            Dictionary with table/column info if found, None otherwise
        """
        # Check in known tables
        for table_name, table_info in self.mapper.schema_guide.get('tables', {}).items():
            if field_name in table_info.get('columns', []):
                return {
                    'table': table_name,
                    'column': field_name
                }

        # Check partial matches (e.g., "quantity" might match "products_quantity")
        field_lower = field_name.lower()
        for table_name, table_info in self.mapper.schema_guide.get('tables', {}).items():
            for col in table_info.get('columns', []):
                if field_lower in col.lower() or col.lower() in field_lower:
                    return {
                        'table': table_name,
                        'column': col,
                        'partial_match': True
                    }

        return None

    def _generate_clarification_questions(self, unmapped: List, unclear: List,
                                           partial: List, missing_fields: List) -> List[Dict]:
        """
        Generate prioritized list of clarification questions for client

        Returns:
            List of question dictionaries, ordered by priority
        """
        questions = []
        question_id = 1

        # Priority 1: Critical decision points (unmapped)
        for decision in unmapped:
            questions.append({
                'id': f'Q{question_id:03d}',
                'priority': 'HIGH',
                'category': 'unmapped_decision',
                'decision_node': decision['node_id'],
                'question_text': decision['question'],
                'clarification_needed': f'How should this decision be evaluated? We need to know:\n'
                                         f'1. What database table/column contains this information?\n'
                                         f'2. What is the decision threshold or criteria?\n'
                                         f'3. Provide an example scenario.\n\n'
                                         f'Original question: {decision["question"]}',
                'context': decision['condition']
            })
            question_id += 1

        # Priority 2: Unclear mappings (need refinement)
        for decision_info in unclear:
            questions.append({
                'id': f'Q{question_id:03d}',
                'priority': 'MEDIUM',
                'category': 'unclear_mapping',
                'decision_node': decision_info['node_id'],
                'question_text': decision_info['question'],
                'clarification_needed': decision_info['clarification'],
                'current_guess': decision_info['current_mapping'],
                'context': decision_info['condition']
            })
            question_id += 1

        # Priority 3: Partial mappings (need completion)
        for decision_info in partial:
            questions.append({
                'id': f'Q{question_id:03d}',
                'priority': 'LOW',
                'category': 'partial_mapping',
                'decision_node': decision_info['node_id'],
                'question_text': decision_info['question'],
                'clarification_needed': decision_info['clarification'],
                'current_mapping': decision_info['current_mapping'],
                'context': decision_info['condition']
            })
            question_id += 1

        # Priority 4: Missing data fields
        for field_info in missing_fields:
            questions.append({
                'id': f'Q{question_id:03d}',
                'priority': 'LOW',
                'category': 'missing_data',
                'field_name': field_info['field_name'],
                'referenced_in': field_info['referenced_in'],
                'clarification_needed': field_info['clarification_needed'],
                'context': field_info['context']
            })
            question_id += 1

        return questions

    def export_gap_report(self, analysis: GapAnalysis, output_path: str):
        """
        Export gap analysis to JSON file

        Args:
            analysis: GapAnalysis object
            output_path: Path to output JSON file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis.to_dict(), f, indent=2, ensure_ascii=False)

    def generate_summary_report(self, all_analyses: Dict[str, GapAnalysis]) -> Dict:
        """
        Generate summary report across all analyzed workflows

        Args:
            all_analyses: Dictionary of file path -> GapAnalysis

        Returns:
            Summary dictionary
        """
        total_decisions = sum(a.total_decisions for a in all_analyses.values())
        total_mapped = sum(a.mapped_count for a in all_analyses.values())
        total_unmapped = sum(a.unmapped_count for a in all_analyses.values())
        total_unclear = sum(a.unclear_count for a in all_analyses.values())
        total_partial = sum(a.partial_count for a in all_analyses.values())

        coverage_pct = round((total_mapped / max(total_decisions, 1)) * 100, 1)

        return {
            'summary': {
                'files_analyzed': len(all_analyses),
                'total_decisions': total_decisions,
                'total_mapped': total_mapped,
                'total_unmapped': total_unmapped,
                'total_unclear': total_unclear,
                'total_partial': total_partial,
                'coverage_percentage': coverage_pct
            },
            'files': {
                path: analysis.to_dict()
                for path, analysis in all_analyses.items()
            }
        }


def main():
    """Test the gap analyzer"""
    from parser import MermaidDecisionParser
    from mapper import DecisionMapper
    from pathlib import Path

    print("\n=== Gap Analyzer Test ===\n")

    # Initialize components
    parser = MermaidDecisionParser()
    mapper = DecisionMapper()
    analyzer = GapAnalyzer(parser, mapper)

    # Analyze Bullseye decision tree
    wiki_root = Path(__file__).parent.parent.parent / "Production" / "wiki"
    test_file = wiki_root / "03_Decision_Workflows" / "Bullseye_Vendor_Purchase_Decision_Tree.md"

    if test_file.exists():
        print(f"Analyzing: {test_file.name}\n")

        analysis = analyzer.analyze_file(str(test_file))

        print("=== Summary ===")
        summary = analysis.to_dict()['summary']
        print(f"Total Decisions: {summary['total_decisions']}")
        print(f"Mapped: {summary['mapped']} ({summary['coverage_percentage']}%)")
        print(f"Partial: {summary['partial']}")
        print(f"Unclear: {summary['unclear']}")
        print(f"Unmapped: {summary['unmapped']}\n")

        print("=== Clarification Questions (Top 5) ===")
        for q in analysis.clarification_questions[:5]:
            print(f"\n{q['id']} [{q['priority']}] {q['category']}")
            print(f"Question: {q.get('question_text', q.get('field_name', 'N/A'))}")
            print(f"Needed: {q['clarification_needed'][:200]}...")

        # Export report
        output_path = Path(__file__).parent.parent / "gap_analysis_report.json"
        analyzer.export_gap_report(analysis, str(output_path))
        print(f"\n✓ Exported report to: {output_path}")

    else:
        print(f"Test file not found: {test_file}")


if __name__ == '__main__':
    main()
