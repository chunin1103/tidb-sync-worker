"""
Mapping Manager - Handle diagram-to-text mappings

Manages the wiki_mappings.json configuration file that stores:
- Which Mermaid nodes link to which text sections
- Color assignments for each mapping
- Preview text for tooltips

JSON Schema:
{
  "version": "1.0",
  "last_modified": "2025-12-29T10:30:00Z",
  "files": {
    "03_Decision_Workflows/Inventory_Filtering_Workflow.md": {
      "mappings": [
        {
          "id": "map_001",
          "diagram_id": "diagram_0",
          "node_id": "B",
          "section_id": "step-1-load-snapshot",
          "color": "#ffeb3b",
          "label": "Load & Snapshot",
          "preview_text": "Input: Excel or CSV file..."
        }
      ]
    }
  }
}
"""

import json
import os
from datetime import datetime


# 10-color Material Design palette
COLOR_PALETTE = [
    "#ffeb3b",  # Yellow
    "#ff9800",  # Orange
    "#f44336",  # Red
    "#e91e63",  # Pink
    "#9c27b0",  # Purple
    "#3f51b5",  # Indigo
    "#2196f3",  # Blue
    "#00bcd4",  # Cyan
    "#009688",  # Teal
    "#4caf50",  # Green
]


class MappingManager:
    """Manage diagram-to-text mappings"""

    def __init__(self, config_path):
        """
        Initialize mapping manager

        Args:
            config_path: Absolute path to wiki_mappings.json
        """
        self.config_path = config_path
        self.data = self._load()

    def _load(self):
        """
        Load mappings from JSON file

        Returns:
            Mapping configuration dict
        """
        if not os.path.exists(self.config_path):
            # Create empty configuration
            return {
                "version": "1.0",
                "last_modified": datetime.utcnow().isoformat() + "Z",
                "files": {}
            }

        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save(self):
        """Save mappings to JSON file"""
        # Update last modified timestamp
        self.data['last_modified'] = datetime.utcnow().isoformat() + "Z"

        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def get_mappings(self, file_path):
        """
        Get all mappings for a specific file

        Args:
            file_path: Relative path to wiki file

        Returns:
            List of mapping dicts
        """
        return self.data['files'].get(file_path, {}).get('mappings', [])

    def add_mapping(self, file_path, mapping):
        """
        Add new mapping for a file

        Args:
            file_path: Relative path to wiki file
            mapping: Dict with keys:
                - diagram_id: ID of diagram (e.g., "diagram_0")
                - node_id: Mermaid node ID (e.g., "B")
                - section_id: HTML section ID (e.g., "step-1-load-snapshot")
                - color: Hex color code (e.g., "#ffeb3b")
                - label: Human-readable label (e.g., "Load & Snapshot")
                - preview_text: Preview text for tooltip

        Returns:
            Generated mapping ID (e.g., "map_001")
        """
        # Initialize file entry if doesn't exist
        if file_path not in self.data['files']:
            self.data['files'][file_path] = {'mappings': []}

        # Generate unique ID
        existing_ids = [m['id'] for m in self.data['files'][file_path]['mappings']]
        mapping_id = f"map_{len(existing_ids) + 1:03d}"

        # Add ID to mapping
        mapping['id'] = mapping_id

        # Append to list
        self.data['files'][file_path]['mappings'].append(mapping)

        # Save to disk
        self._save()

        return mapping_id

    def delete_mapping(self, file_path, mapping_id):
        """
        Delete a specific mapping

        Args:
            file_path: Relative path to wiki file
            mapping_id: Mapping ID to delete (e.g., "map_001")

        Returns:
            True if deleted, False if not found
        """
        if file_path not in self.data['files']:
            return False

        # Filter out the mapping
        mappings = self.data['files'][file_path]['mappings']
        new_mappings = [m for m in mappings if m['id'] != mapping_id]

        # Check if anything was removed
        if len(new_mappings) == len(mappings):
            return False

        # Update and save
        self.data['files'][file_path]['mappings'] = new_mappings
        self._save()

        return True

    def get_colors_used(self, file_path):
        """
        Get list of colors already used in a file

        Args:
            file_path: Relative path to wiki file

        Returns:
            List of hex color codes
        """
        mappings = self.get_mappings(file_path)
        return [m['color'] for m in mappings]

    def suggest_next_color(self, file_path):
        """
        Suggest next available color from palette

        Args:
            file_path: Relative path to wiki file

        Returns:
            Hex color code from palette
        """
        used_colors = self.get_colors_used(file_path)

        # Find first unused color
        for color in COLOR_PALETTE:
            if color not in used_colors:
                return color

        # All colors used, cycle back (use modulo of count)
        return COLOR_PALETTE[len(used_colors) % len(COLOR_PALETTE)]

    def get_all_files(self):
        """
        Get list of all files that have mappings

        Returns:
            List of file paths
        """
        return list(self.data['files'].keys())

    def get_mapping_count(self, file_path):
        """
        Get number of mappings for a file

        Args:
            file_path: Relative path to wiki file

        Returns:
            Count of mappings
        """
        return len(self.get_mappings(file_path))
