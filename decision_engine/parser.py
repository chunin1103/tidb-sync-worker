"""
Mermaid Decision Tree Parser

Extracts decision nodes, conditions, and flows from Mermaid flowcharts
in wiki markdown files.
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DecisionNode:
    """Represents a decision point in the flowchart"""
    node_id: str
    condition: str
    question: str
    options: List[Dict[str, str]] = field(default_factory=list)
    source_file: str = ""
    line_number: int = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'node_id': self.node_id,
            'condition': self.condition,
            'question': self.question,
            'options': self.options,
            'source_file': self.source_file,
            'line_number': self.line_number
        }


@dataclass
class ProcessNode:
    """Represents a process/action node"""
    node_id: str
    action: str
    description: str
    source_file: str = ""
    line_number: int = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'node_id': self.node_id,
            'action': self.action,
            'description': self.description,
            'source_file': self.source_file,
            'line_number': self.line_number
        }


@dataclass
class DataNode:
    """Represents a data input/calculation node"""
    node_id: str
    data_type: str
    expression: str
    source_file: str = ""
    line_number: int = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'node_id': self.node_id,
            'data_type': self.data_type,
            'expression': self.expression,
            'source_file': self.source_file,
            'line_number': self.line_number
        }


class MermaidDecisionParser:
    """
    Parses Mermaid flowchart diagrams to extract decision logic

    Identifies:
    - Decision nodes (diamond shapes with conditions)
    - Process nodes (rectangles with actions)
    - Data nodes (calculations, formulas)
    - Flow connections between nodes
    """

    def __init__(self):
        self.decision_nodes: List[DecisionNode] = []
        self.process_nodes: List[ProcessNode] = []
        self.data_nodes: List[DataNode] = []
        self.connections: List[Tuple[str, str, Optional[str]]] = []

    def parse_file(self, file_path: str) -> Dict:
        """
        Parse a markdown file containing Mermaid diagrams

        Args:
            file_path: Path to markdown file

        Returns:
            Dictionary with parsed nodes and connections
        """
        self.decision_nodes = []
        self.process_nodes = []
        self.data_nodes = []
        self.connections = []

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract all Mermaid blocks
        mermaid_blocks = self._extract_mermaid_blocks(content)

        for block_idx, (block, start_line) in enumerate(mermaid_blocks):
            self._parse_mermaid_block(block, file_path, start_line, block_idx)

        return {
            'decision_nodes': [n.to_dict() for n in self.decision_nodes],
            'process_nodes': [n.to_dict() for n in self.process_nodes],
            'data_nodes': [n.to_dict() for n in self.data_nodes],
            'connections': [{'from': f, 'to': t, 'label': l} for f, t, l in self.connections],
            'source_file': file_path
        }

    def _extract_mermaid_blocks(self, content: str) -> List[Tuple[str, int]]:
        """
        Extract all Mermaid code blocks from markdown

        Returns:
            List of (mermaid_code, start_line_number) tuples
        """
        blocks = []
        lines = content.split('\n')
        in_mermaid = False
        current_block = []
        block_start = 0

        for i, line in enumerate(lines, 1):
            if line.strip().startswith('```mermaid'):
                in_mermaid = True
                block_start = i
                current_block = []
            elif line.strip() == '```' and in_mermaid:
                in_mermaid = False
                blocks.append(('\n'.join(current_block), block_start))
            elif in_mermaid:
                current_block.append(line)

        return blocks

    def _parse_mermaid_block(self, block: str, source_file: str, start_line: int, block_idx: int):
        """
        Parse a single Mermaid flowchart block

        Patterns:
        - Decision: nodeID{Question?}
        - Process: nodeID[Action]
        - Data: nodeID[Expression]
        - Connection: A --> B or A -->|label| B
        """
        lines = block.strip().split('\n')

        for line_offset, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('graph ') or line.startswith('style '):
                continue

            line_num = start_line + line_offset

            # Parse decision node: A{Question?}
            decision_match = re.match(r'([A-Z]+[0-9]*)\{(.+?)\}', line)
            if decision_match:
                node_id = decision_match.group(1)
                condition_text = decision_match.group(2)

                # Clean up the condition text
                condition = self._clean_node_text(condition_text)

                # Extract actual question (before <br/> or first line)
                question = condition.split('<br')[0].split('\n')[0].strip()

                self.decision_nodes.append(DecisionNode(
                    node_id=f"diagram_{block_idx}_{node_id}",
                    condition=condition,
                    question=question,
                    source_file=source_file,
                    line_number=line_num
                ))
                continue

            # Parse process/action node: A[Action]
            process_match = re.match(r'([A-Z]+[0-9]*)\[(.+?)\]', line)
            if process_match:
                node_id = process_match.group(1)
                action_text = process_match.group(2)

                action = self._clean_node_text(action_text)

                # Determine if this is a data calculation or process
                if self._is_data_calculation(action):
                    # Extract expression
                    expression = self._extract_expression(action)
                    self.data_nodes.append(DataNode(
                        node_id=f"diagram_{block_idx}_{node_id}",
                        data_type="calculation",
                        expression=expression,
                        source_file=source_file,
                        line_number=line_num
                    ))
                else:
                    # Get first line as primary action
                    primary_action = action.split('<br')[0].split('\n')[0].strip()

                    self.process_nodes.append(ProcessNode(
                        node_id=f"diagram_{block_idx}_{node_id}",
                        action=primary_action,
                        description=action,
                        source_file=source_file,
                        line_number=line_num
                    ))
                continue

            # Parse connections: A -->|label| B or A --> B
            connection_match = re.match(r'([A-Z]+[0-9]*)\s*-->\|?([^|]*)\|?\s*([A-Z]+[0-9]*)', line)
            if connection_match:
                from_node = connection_match.group(1)
                label = connection_match.group(2).strip() if connection_match.group(2) else None
                to_node = connection_match.group(3)

                self.connections.append((
                    f"diagram_{block_idx}_{from_node}",
                    f"diagram_{block_idx}_{to_node}",
                    label
                ))

    def _clean_node_text(self, text: str) -> str:
        """Clean up node text (remove extra whitespace, handle line breaks)"""
        # Replace <br/>, <br>, \n with newlines
        text = re.sub(r'<br\s*/?>', '\n', text)
        text = re.sub(r'\\n', '\n', text)
        # Remove extra whitespace
        lines = [line.strip() for line in text.split('\n')]
        return '\n'.join(lines)

    def _is_data_calculation(self, text: str) -> bool:
        """Determine if node represents a data calculation"""
        calc_indicators = ['=', '÷', '×', 'Calculate', 'Years', 'Stock', 'Deficit', 'Target']
        return any(indicator in text for indicator in calc_indicators)

    def _extract_expression(self, text: str) -> str:
        """Extract mathematical expression from text"""
        # Look for expressions with =, ÷, ×
        lines = text.split('\n')
        for line in lines:
            if '=' in line:
                return line.strip()
        return text.split('\n')[0].strip()

    def extract_decision_points(self) -> List[Dict]:
        """
        Extract all unique decision points across parsed diagrams

        Returns:
            List of decision dictionaries with metadata
        """
        decisions = []

        for node in self.decision_nodes:
            # Find all outgoing connections to get options
            options = []
            for from_node, to_node, label in self.connections:
                if from_node == node.node_id and label:
                    options.append({
                        'label': label,
                        'target': to_node
                    })

            node.options = options
            decisions.append(node.to_dict())

        return decisions

    def extract_data_requirements(self) -> List[Dict]:
        """
        Extract all data fields/calculations referenced in the tree

        Returns:
            List of data requirement dictionaries
        """
        data_reqs = []

        # From decision nodes - extract field references
        for node in self.decision_nodes:
            fields = self._extract_field_references(node.condition)
            for field in fields:
                data_reqs.append({
                    'field_name': field,
                    'referenced_in': 'decision',
                    'node_id': node.node_id,
                    'context': node.question,
                    'source_file': node.source_file
                })

        # From data nodes - extract calculations
        for node in self.data_nodes:
            fields = self._extract_field_references(node.expression)
            for field in fields:
                data_reqs.append({
                    'field_name': field,
                    'referenced_in': 'calculation',
                    'node_id': node.node_id,
                    'context': node.expression,
                    'source_file': node.source_file
                })

        return data_reqs

    def _extract_field_references(self, text: str) -> List[str]:
        """
        Extract field/variable references from text

        Looks for patterns like:
        - Years_in_Stock
        - products_quantity
        - Half_Stock
        - Stock
        """
        # Common field patterns
        patterns = [
            r'\b([A-Z][a-z]+(?:_[A-Z][a-z]+)*)\b',  # CamelCase with underscores
            r'\b([a-z]+_[a-z]+(?:_[a-z]+)*)\b',  # snake_case
            r'\b(Stock|Quantity|Years|Purchased|Deficit|Target|Excess)\b'  # Keywords
        ]

        fields = set()
        for pattern in patterns:
            matches = re.findall(pattern, text)
            fields.update(matches)

        # Filter out common words
        exclude = {'IF', 'THEN', 'ELSE', 'AND', 'OR', 'NOT', 'Yes', 'No', 'True', 'False'}
        return [f for f in fields if f not in exclude]


def main():
    """Test the parser on Bullseye decision tree"""
    parser = MermaidDecisionParser()

    wiki_root = Path(__file__).parent.parent.parent / "Production" / "wiki"
    test_file = wiki_root / "03_Decision_Workflows" / "Bullseye_Vendor_Purchase_Decision_Tree.md"

    if test_file.exists():
        result = parser.parse_file(str(test_file))

        print(f"\n=== Parsed: {test_file.name} ===")
        print(f"Decision Nodes: {len(result['decision_nodes'])}")
        print(f"Process Nodes: {len(result['process_nodes'])}")
        print(f"Data Nodes: {len(result['data_nodes'])}")
        print(f"Connections: {len(result['connections'])}")

        print("\n=== Decision Points ===")
        decisions = parser.extract_decision_points()
        for i, dec in enumerate(decisions[:5], 1):
            print(f"\n{i}. {dec['question']}")
            print(f"   Condition: {dec['condition'][:100]}...")
            print(f"   Options: {len(dec['options'])}")

        print("\n=== Data Requirements ===")
        data_reqs = parser.extract_data_requirements()
        unique_fields = set(req['field_name'] for req in data_reqs)
        print(f"Unique fields referenced: {len(unique_fields)}")
        for field in sorted(unique_fields)[:10]:
            print(f"  - {field}")
    else:
        print(f"Test file not found: {test_file}")


if __name__ == '__main__':
    main()
