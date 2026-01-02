"""
Mermaid Parser - Converts Mermaid flowchart syntax to decision tree JSON

Parses Mermaid graph TD diagrams from wiki markdown files and converts them
to the JSON format used by the Decision Tree Visualizer.

Supports:
- Node definitions: A[Label], B{Decision}, C([Rounded])
- Edge definitions: A --> B, A -->|Label| B, A -->|Yes| B
- Style definitions: style A fill:#color
"""

import re
import os
from typing import Dict, List, Tuple, Optional, Any


class MermaidParser:
    """Parse Mermaid flowchart syntax into structured JSON."""

    # Node shape patterns
    NODE_PATTERNS = [
        # Diamond decision: {text}
        (r'(\w+)\{([^}]+)\}', 'decision'),
        # Stadium/rounded: ([text])
        (r'(\w+)\(\[([^\]]+)\]\)', 'rounded'),
        # Rounded rect: (text)
        (r'(\w+)\(([^)]+)\)', 'start'),
        # Rectangle: [text]
        (r'(\w+)\[([^\]]+)\]', 'action'),
        # Plain node ID
        (r'^(\w+)$', 'default'),
    ]

    # Edge patterns
    EDGE_PATTERNS = [
        # Arrow with label: A -->|Label| B
        r'(\w+)\s*-->\s*\|([^|]*)\|\s*(\w+)',
        # Arrow without label: A --> B
        r'(\w+)\s*-->\s*(\w+)',
        # Dotted with label: A -.->|Label| B
        r'(\w+)\s*-\.?->\s*\|([^|]*)\|\s*(\w+)',
        # Dotted without label: A -.-> B
        r'(\w+)\s*-\.?->\s*(\w+)',
    ]

    def __init__(self):
        self.nodes = {}
        self.edges = []
        self.styles = {}
        self.node_positions = {}

    def parse_file(self, filepath: str) -> Dict:
        """Parse a markdown file and extract Mermaid diagram."""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        return self.parse_markdown(content, filepath)

    def parse_markdown(self, content: str, source_file: str = '') -> Dict:
        """Extract and parse Mermaid diagram from markdown content."""
        # Find mermaid code block
        mermaid_match = re.search(
            r'```mermaid\s*\n(.*?)```',
            content,
            re.DOTALL | re.IGNORECASE
        )

        if not mermaid_match:
            return self._empty_tree(source_file)

        mermaid_code = mermaid_match.group(1)
        return self.parse_mermaid(mermaid_code, source_file)

    def parse_mermaid(self, mermaid_code: str, source_file: str = '') -> Dict:
        """Parse Mermaid flowchart code."""
        self.nodes = {}
        self.edges = []
        self.styles = {}

        lines = mermaid_code.strip().split('\n')

        for line in lines:
            line = line.strip()
            if not line or line.startswith('%%'):
                continue

            # Skip graph declaration
            if line.lower().startswith('graph '):
                continue

            # Parse style definitions
            if line.lower().startswith('style '):
                self._parse_style(line)
                continue

            # Parse edges and extract nodes
            self._parse_line(line)

        # Calculate positions
        self._calculate_positions()

        # Determine node types based on connections
        self._infer_node_types()

        # Build tree structure
        return self._build_tree(source_file)

    def _parse_line(self, line: str):
        """Parse a single line for nodes and edges."""
        # Try to match edge patterns
        for pattern in self.EDGE_PATTERNS:
            match = re.search(pattern, line)
            if match:
                groups = match.groups()
                if len(groups) == 3:
                    # Has label
                    from_id, label, to_id = groups
                else:
                    # No label
                    from_id, to_id = groups
                    label = ''

                # Extract nodes from the full line
                self._extract_nodes_from_line(line)

                # Add edge
                edge_id = f"e{len(self.edges) + 1}"
                self.edges.append({
                    'id': edge_id,
                    'from': from_id.strip(),
                    'to': to_id.strip(),
                    'label': label.strip() if label else '',
                })
                return

        # If no edge found, try to extract node definition
        self._extract_nodes_from_line(line)

    def _extract_nodes_from_line(self, line: str):
        """Extract node definitions from a line."""
        # Split by arrows first
        parts = re.split(r'\s*--[>.-]+\s*(?:\|[^|]*\|\s*)?', line)

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Try each node pattern
            for pattern, node_type in self.NODE_PATTERNS:
                match = re.match(pattern, part)
                if match:
                    groups = match.groups()
                    if len(groups) >= 2:
                        node_id = groups[0]
                        label = groups[1]
                    else:
                        node_id = groups[0]
                        label = node_id

                    if node_id not in self.nodes:
                        # Clean up label - remove HTML breaks
                        label = label.replace('<br/>', ' ').replace('<br>', ' ')
                        label = re.sub(r'\s+', ' ', label).strip()

                        self.nodes[node_id] = {
                            'id': node_id,
                            'type': node_type,
                            'label': label,
                            'description': label,
                        }
                    break

    def _parse_style(self, line: str):
        """Parse style definition."""
        # style A fill:#color
        match = re.match(r'style\s+(\w+)\s+(.+)', line, re.IGNORECASE)
        if match:
            node_id = match.group(1)
            style_str = match.group(2)

            # Parse style properties
            styles = {}
            for prop in style_str.split(','):
                prop = prop.strip()
                if ':' in prop:
                    key, value = prop.split(':', 1)
                    styles[key.strip()] = value.strip()

            self.styles[node_id] = styles

    def _calculate_positions(self):
        """Calculate node positions using a layered layout algorithm."""
        if not self.nodes:
            return

        # Find root nodes (no incoming edges)
        incoming = {n: 0 for n in self.nodes}
        for edge in self.edges:
            if edge['to'] in incoming:
                incoming[edge['to']] += 1

        roots = [n for n, count in incoming.items() if count == 0]
        if not roots and self.nodes:
            roots = [list(self.nodes.keys())[0]]

        # Build adjacency list
        children = {n: [] for n in self.nodes}
        for edge in self.edges:
            if edge['from'] in children:
                children[edge['from']].append(edge['to'])

        # Assign layers using BFS
        layers = {}
        visited = set()
        queue = [(r, 0) for r in roots]

        while queue:
            node, layer = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            layers[node] = layer

            for child in children.get(node, []):
                if child not in visited:
                    queue.append((child, layer + 1))

        # Handle unvisited nodes
        max_layer = max(layers.values()) if layers else 0
        for node in self.nodes:
            if node not in layers:
                max_layer += 1
                layers[node] = max_layer

        # Group by layer
        layer_nodes = {}
        for node, layer in layers.items():
            if layer not in layer_nodes:
                layer_nodes[layer] = []
            layer_nodes[layer].append(node)

        # Calculate positions
        canvas_width = 900
        y_spacing = 100
        y_start = 60

        for layer, nodes in sorted(layer_nodes.items()):
            x_spacing = canvas_width / (len(nodes) + 1)
            for i, node in enumerate(nodes):
                x = x_spacing * (i + 1)
                y = y_start + layer * y_spacing
                self.nodes[node]['position'] = {'x': int(x), 'y': int(y)}

    def _infer_node_types(self):
        """Infer node types based on connections and labels."""
        # Find terminal nodes (no outgoing edges)
        outgoing = {n: 0 for n in self.nodes}
        for edge in self.edges:
            if edge['from'] in outgoing:
                outgoing[edge['from']] += 1

        for node_id, node in self.nodes.items():
            label_lower = node['label'].lower()

            # Check for result indicators
            if outgoing.get(node_id, 0) == 0:
                node['type'] = 'result'
                # Determine result action
                if any(x in label_lower for x in ['no order', 'no action', 'skip', 'no reorder']):
                    node['result'] = {'action': 'none', 'priority': 'LOW', 'color': '#4caf50'}
                elif any(x in label_lower for x in ['order needed', 'purchase', 'order approved']):
                    node['result'] = {'action': 'order', 'priority': 'HIGH', 'color': '#f44336'}
                elif any(x in label_lower for x in ['manual', 'review']):
                    node['result'] = {'action': 'review', 'priority': 'MEDIUM', 'color': '#9c27b0'}
                elif any(x in label_lower for x in ['cutting', 'cascade', 'cut']):
                    node['result'] = {'action': 'cascade_review', 'priority': 'MEDIUM', 'color': '#2196f3'}
                else:
                    node['result'] = {'action': 'complete', 'priority': 'LOW', 'color': '#616161'}

            # Check for start node
            elif any(x in label_lower for x in ['start:', 'begin', 'input']):
                node['type'] = 'start'

            # Check for calculation nodes
            elif any(x in label_lower for x in ['calculate', 'compute', 'formula', '=', '÷', '×']):
                node['type'] = 'calculation'

            # Apply style-based coloring
            if node_id in self.styles:
                style = self.styles[node_id]
                if 'fill' in style:
                    if 'result' not in node:
                        node['result'] = {}
                    node['result']['color'] = style['fill']

    def _build_tree(self, source_file: str) -> Dict:
        """Build the final tree structure."""
        # Find root node
        incoming = {n: 0 for n in self.nodes}
        for edge in self.edges:
            if edge['to'] in incoming:
                incoming[edge['to']] += 1

        root = None
        for n, count in incoming.items():
            if count == 0:
                root = n
                break

        if not root and self.nodes:
            root = list(self.nodes.keys())[0]

        # Extract filename for metadata
        filename = os.path.basename(source_file) if source_file else 'parsed_tree'
        title = filename.replace('.md', '').replace('_', ' ').title()

        return {
            'version': '1.0',
            'metadata': {
                'title': title,
                'description': f'Decision tree parsed from {filename}',
                'source_file': source_file,
                'node_count': len(self.nodes),
                'edge_count': len(self.edges),
            },
            'tree': {
                'root': root,
                'nodes': self.nodes,
                'edges': self.edges,
            }
        }

    def _empty_tree(self, source_file: str) -> Dict:
        """Return empty tree structure."""
        return {
            'version': '1.0',
            'metadata': {
                'title': 'Empty Tree',
                'description': 'No Mermaid diagram found',
                'source_file': source_file,
            },
            'tree': {
                'root': None,
                'nodes': {},
                'edges': [],
            }
        }


def parse_wiki_decision_trees(wiki_dir: str) -> Dict[str, Dict]:
    """Parse all decision tree files from the wiki directory."""
    parser = MermaidParser()
    trees = {}

    decision_workflow_dir = os.path.join(wiki_dir, '03_Decision_Workflows')
    if not os.path.exists(decision_workflow_dir):
        return trees

    for filename in os.listdir(decision_workflow_dir):
        if filename.endswith('.md'):
            filepath = os.path.join(decision_workflow_dir, filename)
            tree_id = filename.replace('.md', '').lower().replace('_', '-')

            try:
                tree_data = parser.parse_file(filepath)
                if tree_data['tree']['nodes']:  # Only add if has nodes
                    trees[tree_id] = tree_data
            except Exception as e:
                print(f"Error parsing {filename}: {e}")

    return trees


# Singleton cache
_parsed_trees_cache = None

def get_available_trees(wiki_dir: str) -> Dict[str, Dict]:
    """Get all available decision trees, with caching."""
    global _parsed_trees_cache
    if _parsed_trees_cache is None:
        _parsed_trees_cache = parse_wiki_decision_trees(wiki_dir)
    return _parsed_trees_cache

def reload_trees(wiki_dir: str) -> Dict[str, Dict]:
    """Force reload of decision trees."""
    global _parsed_trees_cache
    _parsed_trees_cache = parse_wiki_decision_trees(wiki_dir)
    return _parsed_trees_cache
