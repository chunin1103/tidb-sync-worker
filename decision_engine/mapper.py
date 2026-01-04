"""
Decision Mapper - Maps decision tree nodes to database operations

Provides configuration management for mapping business logic decisions
to actual database queries and field operations.
"""

import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum


class MappingStatus(Enum):
    """Status of a decision-to-database mapping"""
    MAPPED = "mapped"  # Successfully mapped to database
    PARTIAL = "partial"  # Partially mapped, needs clarification
    UNMAPPED = "unmapped"  # No mapping exists
    UNCLEAR = "unclear"  # Business logic unclear, needs client input


@dataclass
class DatabaseMapping:
    """Represents a mapping from decision logic to database operation"""
    decision_id: str
    status: MappingStatus
    table: Optional[str] = None
    column: Optional[str] = None
    calculation: Optional[str] = None  # SQL expression or Python code
    filters: Dict[str, Any] = field(default_factory=dict)  # WHERE conditions
    notes: str = ""
    clarification_needed: str = ""  # Questions for client
    examples: List[Dict] = field(default_factory=list)  # Test cases

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'decision_id': self.decision_id,
            'status': self.status.value,
            'table': self.table,
            'column': self.column,
            'calculation': self.calculation,
            'filters': self.filters,
            'notes': self.notes,
            'clarification_needed': self.clarification_needed,
            'examples': self.examples
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'DatabaseMapping':
        """Create from dictionary"""
        return cls(
            decision_id=data['decision_id'],
            status=MappingStatus(data['status']),
            table=data.get('table'),
            column=data.get('column'),
            calculation=data.get('calculation'),
            filters=data.get('filters', {}),
            notes=data.get('notes', ''),
            clarification_needed=data.get('clarification_needed', ''),
            examples=data.get('examples', [])
        )


class DecisionMapper:
    """
    Manages mappings between decision tree logic and database operations

    Responsibilities:
    - Load/save mapping configurations
    - Auto-detect potential mappings using schema
    - Identify unmapped decisions
    - Generate clarification questions for client
    """

    def __init__(self, config_path: Optional[str] = None, schema_path: Optional[str] = None):
        """
        Initialize mapper

        Args:
            config_path: Path to mapping configuration JSON
            schema_path: Path to database schema guide
        """
        self.config_path = config_path or self._default_config_path()
        self.schema_path = schema_path or self._default_schema_path()

        self.mappings: Dict[str, DatabaseMapping] = {}
        self.schema_guide: Dict = {}

        self._load_config()
        self._load_schema_guide()

    def _default_config_path(self) -> str:
        """Get default path for mapping configuration"""
        return str(Path(__file__).parent.parent / "decision_mapping_config.json")

    def _default_schema_path(self) -> str:
        """Get default path for schema guide"""
        return str(Path(__file__).parent.parent.parent /
                   "Production" / "wiki" / "08_Database_Schema" / "TIDB_SCHEMA_GUIDE.md")

    def _load_config(self):
        """Load mapping configuration from JSON file"""
        config_file = Path(self.config_path)
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for decision_id, mapping_data in data.items():
                    self.mappings[decision_id] = DatabaseMapping.from_dict(mapping_data)
        else:
            # Create empty config
            self.mappings = {}

    def _load_schema_guide(self):
        """Parse schema guide to understand available tables/columns"""
        schema_file = Path(self.schema_path)
        if schema_file.exists():
            with open(schema_file, 'r', encoding='utf-8') as f:
                content = f.read()
                self.schema_guide = self._parse_schema_guide(content)
        else:
            self.schema_guide = {}

    def _parse_schema_guide(self, content: str) -> Dict:
        """
        Parse TIDB_SCHEMA_GUIDE.md to extract table/column info

        Returns:
            Dictionary of tables with columns and business definitions
        """
        schema = {
            'tables': {},
            'golden_rules': [],
            'calculations': {}
        }

        # Extract golden rules
        rules_section = content.split('## 🚨 CRITICAL DATA RULES')[1].split('##')[0]
        schema['golden_rules'] = self._extract_golden_rules(rules_section)

        # Extract table definitions
        tables_section = content.split('## 📊 TABLE REFERENCE')[1].split('##')[0]
        schema['tables'] = self._extract_table_definitions(tables_section)

        # Extract common calculations
        calc_section = content.split('## 📐 COMMON CALCULATIONS')[1].split('##')[0]
        schema['calculations'] = self._extract_calculations(calc_section)

        return schema

    def _extract_golden_rules(self, section: str) -> List[Dict]:
        """Extract golden rules from schema guide"""
        rules = []

        # Rule 1: Inventory Quantity
        if 'products.products_quantity' in section:
            rules.append({
                'name': 'inventory_quantity',
                'table': 'products',
                'column': 'products_quantity',
                'rule': 'ALWAYS use products.products_quantity (NOT products_description.products_quantity)'
            })

        # Rule 2: Revenue Calculation
        if "class = 'ot_total'" in section:
            rules.append({
                'name': 'revenue',
                'table': 'orders_total',
                'column': 'value',
                'filter': "class = 'ot_total'",
                'rule': 'ALWAYS use orders_total WHERE class=ot_total for revenue'
            })

        # Rule 5: Years in Stock
        if 'years_in_stock' in section.lower():
            rules.append({
                'name': 'years_in_stock',
                'calculation': 'products_quantity / (lifetime_units_sold / 365)',
                'rule': 'Years = Current Stock / Annual Sales Rate'
            })

        return rules

    def _extract_table_definitions(self, section: str) -> Dict:
        """Extract table and column definitions"""
        tables = {}

        # Simple extraction (can be enhanced with more sophisticated parsing)
        table_pattern = r'### \*\*\d+\. Table: `([^`]+)`'
        import re

        table_matches = re.finditer(table_pattern, section)
        for match in table_matches:
            table_name = match.group(1)
            tables[table_name] = {
                'columns': [],
                'primary_key': None,
                'description': ''
            }

            # Extract column info (simplified)
            # In real implementation, parse markdown tables

        # Hardcode key tables for now
        tables['products'] = {
            'columns': ['products_id', 'products_model', 'products_quantity',
                        'products_price', 'products_cost', 'minimum_stock_level'],
            'primary_key': 'products_id',
            'description': 'Master product catalog with inventory levels'
        }

        tables['orders'] = {
            'columns': ['orders_id', 'customers_id', 'date_purchased', 'orders_status'],
            'primary_key': 'orders_id',
            'description': 'Customer orders'
        }

        tables['orders_products'] = {
            'columns': ['orders_id', 'products_id', 'products_quantity', 'final_price'],
            'primary_key': 'orders_products_id',
            'description': 'Order line items'
        }

        return tables

    def _extract_calculations(self, section: str) -> Dict:
        """Extract common calculation formulas"""
        calculations = {
            'years_in_stock': {
                'formula': 'products_quantity / (lifetime_units_sold / 365)',
                'description': 'Years of inventory coverage based on sales velocity'
            },
            'aov': {
                'formula': 'AVG(orders_total.value) WHERE class=ot_total',
                'description': 'Average Order Value'
            },
            'clv': {
                'formula': 'SUM(orders_total.value) WHERE class=ot_total GROUP BY customers_id',
                'description': 'Customer Lifetime Value'
            }
        }
        return calculations

    def save_config(self):
        """Save mapping configuration to JSON file"""
        data = {
            decision_id: mapping.to_dict()
            for decision_id, mapping in self.mappings.items()
        }

        config_file = Path(self.config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)

        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def create_mapping(self, decision: Dict) -> DatabaseMapping:
        """
        Create a mapping for a decision node

        Args:
            decision: Decision node dictionary from parser

        Returns:
            DatabaseMapping object (may be unmapped initially)
        """
        decision_id = decision['node_id']

        # Check if mapping already exists
        if decision_id in self.mappings:
            return self.mappings[decision_id]

        # Try to auto-detect mapping
        mapping = self._auto_detect_mapping(decision)

        # Store mapping
        self.mappings[decision_id] = mapping

        return mapping

    def _auto_detect_mapping(self, decision: Dict) -> DatabaseMapping:
        """
        Attempt to automatically detect database mapping for a decision

        Args:
            decision: Decision node dictionary

        Returns:
            DatabaseMapping with best-guess mapping or unmapped status
        """
        question = decision['question'].lower()
        condition = decision['condition'].lower()

        # Check for known patterns

        # Pattern 1: Years in Stock / Years of Stock
        if 'years' in question and ('stock' in question or 'inventory' in question):
            return DatabaseMapping(
                decision_id=decision['node_id'],
                status=MappingStatus.MAPPED,
                table='products',
                column='products_quantity',
                calculation='products_quantity / (lifetime_units_sold / 365)',
                notes='Uses Years in Stock calculation from schema guide',
                examples=[
                    {'threshold': 0.25, 'operator': '<', 'action': 'trigger_order'},
                    {'threshold': 0.40, 'operator': '>=', 'action': 'sufficient_stock'}
                ]
            )

        # Pattern 2: Stock / Quantity checks
        if 'stock' in question or 'quantity' in question:
            if 'deficit' in condition or 'below' in condition:
                return DatabaseMapping(
                    decision_id=decision['node_id'],
                    status=MappingStatus.PARTIAL,
                    table='products',
                    column='products_quantity',
                    notes='Stock quantity check - threshold needs clarification',
                    clarification_needed='What is the threshold value for this stock check? '
                                         'Is it compared to minimum_stock_level or a calculated target?'
                )

        # Pattern 3: Thickness / Product type
        if 'thickness' in question or '3mm' in condition or '2mm' in condition:
            return DatabaseMapping(
                decision_id=decision['node_id'],
                status=MappingStatus.UNCLEAR,
                table='products_description',
                column='products_name',
                notes='Product thickness classification - may be in product name/description',
                clarification_needed='How is product thickness stored in the database? '
                                     'Is it part of products_name, products_model, or a separate field?'
            )

        # Pattern 4: Size classification (Half, 10x10, 5x10, 5x5)
        if any(size in condition for size in ['half', '10×10', '10x10', '5×10', '5x10', '5×5', '5x5']):
            return DatabaseMapping(
                decision_id=decision['node_id'],
                status=MappingStatus.UNCLEAR,
                table='products',
                column='products_model',
                notes='Product size classification - may be in SKU/model',
                clarification_needed='How are product sizes (Half Sheet, 10×10, 5×10, 5×5) identified? '
                                     'Is there a naming convention in products_model or a separate category?'
            )

        # Pattern 5: Excess / Surplus checks
        if 'excess' in condition or 'surplus' in condition:
            return DatabaseMapping(
                decision_id=decision['node_id'],
                status=MappingStatus.PARTIAL,
                table='products',
                column='products_quantity',
                calculation='products_quantity - minimum_target',
                notes='Excess stock calculation - target needs definition',
                clarification_needed='What is the target/minimum level for this product? '
                                     'Is it minimum_stock_level, a calculated 0.40yr target, or something else?'
            )

        # Default: Unmapped
        return DatabaseMapping(
            decision_id=decision['node_id'],
            status=MappingStatus.UNMAPPED,
            notes='No automatic mapping detected',
            clarification_needed=f'How should this decision be evaluated? Question: {decision["question"]}'
        )

    def get_unmapped_decisions(self) -> List[DatabaseMapping]:
        """Get all decisions that need clarification"""
        return [
            mapping for mapping in self.mappings.values()
            if mapping.status in [MappingStatus.UNMAPPED, MappingStatus.UNCLEAR, MappingStatus.PARTIAL]
        ]

    def get_clarification_questions(self) -> List[Dict]:
        """
        Generate list of questions for client to clarify mappings

        Returns:
            List of dictionaries with decision info and questions
        """
        questions = []
        unmapped = self.get_unmapped_decisions()

        for mapping in unmapped:
            questions.append({
                'decision_id': mapping.decision_id,
                'status': mapping.status.value,
                'current_mapping': {
                    'table': mapping.table,
                    'column': mapping.column,
                    'calculation': mapping.calculation
                },
                'question': mapping.clarification_needed,
                'notes': mapping.notes
            })

        return questions

    def update_mapping(self, decision_id: str, updates: Dict):
        """
        Update a mapping based on client feedback

        Args:
            decision_id: ID of decision to update
            updates: Dictionary with mapping updates
        """
        if decision_id not in self.mappings:
            raise ValueError(f"Decision {decision_id} not found")

        mapping = self.mappings[decision_id]

        if 'table' in updates:
            mapping.table = updates['table']
        if 'column' in updates:
            mapping.column = updates['column']
        if 'calculation' in updates:
            mapping.calculation = updates['calculation']
        if 'filters' in updates:
            mapping.filters = updates['filters']
        if 'notes' in updates:
            mapping.notes = updates['notes']
        if 'status' in updates:
            mapping.status = MappingStatus(updates['status'])

        self.save_config()


def main():
    """Test the mapper"""
    from parser import MermaidDecisionParser
    from pathlib import Path

    # Parse decision tree
    parser = MermaidDecisionParser()
    wiki_root = Path(__file__).parent.parent.parent / "Production" / "wiki"
    test_file = wiki_root / "03_Decision_Workflows" / "Bullseye_Vendor_Purchase_Decision_Tree.md"

    if test_file.exists():
        result = parser.parse_file(str(test_file))
        decisions = parser.extract_decision_points()

        # Create mappings
        mapper = DecisionMapper()

        print("\n=== Auto-Detecting Mappings ===")
        for decision in decisions[:10]:  # First 10 decisions
            mapping = mapper.create_mapping(decision)
            print(f"\nDecision: {decision['question']}")
            print(f"Status: {mapping.status.value}")
            if mapping.table:
                print(f"Mapped to: {mapping.table}.{mapping.column}")
            if mapping.clarification_needed:
                print(f"Question: {mapping.clarification_needed}")

        # Save mappings
        mapper.save_config()
        print(f"\n✓ Saved {len(mapper.mappings)} mappings to {mapper.config_path}")

        # Show clarification questions
        questions = mapper.get_clarification_questions()
        print(f"\n=== Clarification Needed ({len(questions)} items) ===")
        for i, q in enumerate(questions[:5], 1):
            print(f"\n{i}. {q['question']}")


if __name__ == '__main__':
    main()
