# Wiki Viewer - Interactive Documentation System

**Live URL:** https://gpt-mcp.onrender.com/wiki/

Interactive web-based documentation system that visualizes the Production wiki with bidirectional linking between Mermaid diagrams and text explanations.

---

## Quick Reference

| Property | Value |
|----------|-------|
| **Main URL** | https://gpt-mcp.onrender.com/wiki/ |
| **Total Files** | 31 markdown files across 7 folders |
| **Diagrams** | 6 files with Mermaid flowcharts (11 total diagrams) |
| **Routes** | 9 routes (4 pages + 5 APIs) |

---

## Key Pages

| URL | Description |
|-----|-------------|
| `/wiki/` | Workflow overview with visual timeline |
| `/wiki/browse` | File browser showing all folders and files |
| `/wiki/view/<path>` | Markdown viewer with Mermaid diagram rendering |
| `/wiki/admin` | Admin mode guide for creating mappings |
| `/wiki/api/mappings/<path>` | REST API for mapping CRUD operations |

---

## Features

### Workflow Navigation
- Visual SVG timeline showing 4 production stages
- Click any stage to browse files in that folder
- Color-coded folders (Input: blue, Rules: orange, Decision: purple, Output: green)

### Markdown Rendering
- Full GitHub-flavored markdown support
- Syntax highlighting for code blocks
- Table of contents auto-generated from headings
- Relative links converted to absolute `/wiki/` paths

### Mermaid Diagram Integration
- Client-side rendering via Mermaid.js (CDN)
- Diagrams preserved during markdown parsing
- Interactive SVG elements (click, hover)

### Bidirectional Linking
- **Node → Text:** Click Mermaid node → scroll to text section + show tooltip preview
- **Text → Node:** Click text section → highlight corresponding Mermaid node
- Color-coded associations (10-color Material Design palette)
- Pulse animations for visual feedback

### Admin Mode
- Toggle at top of any wiki file page
- Click-to-create mapping workflow
- No code changes required
- Mappings saved to `wiki_mappings.json`

---

## Architecture

### Backend
```
wiki_viewer/
├── __init__.py          # Blueprint registration
├── routes.py            # 9 Flask routes
├── markdown_parser.py   # Mermaid extraction/restoration
└── mapping_manager.py   # JSON-based mapping CRUD
```

### Frontend
```
wiki_viewer/
├── templates/
│   ├── wiki_base.html   # Base template
│   ├── wiki_overview.html
│   ├── wiki_viewer.html
│   ├── wiki_browser.html
│   └── wiki_admin.html
└── static/
    ├── wiki.css         # Responsive layout (800+ lines)
    └── wiki.js          # WikiViewer class (500+ lines)
```

### Content
- All 31 wiki files in `wiki/` folder
- 7 folders: `01_Input_Data_Processing` → `07_Archive`
- Mappings config: `wiki_mappings.json`

---

## Creating Mappings

### Quick Start

1. **Navigate to a file with Mermaid diagram:**
   ```
   https://gpt-mcp.onrender.com/wiki/view/03_Decision_Workflows/Inventory_Filtering_Workflow
   ```

2. **Toggle Admin Mode:** Click checkbox at top

3. **Select Mermaid Node:** Click any node (gets green border)

4. **Select Text Section:** Click a heading (H2, H3, or H4)

5. **Confirm Mapping:** Review and click "Create Mapping"

6. **Refresh & Test:** Refresh page to see bidirectional linking

### Recommended Files for Mapping

| File | Nodes | Complexity |
|------|-------|------------|
| Inventory_Filtering_Workflow.md | 26 | High |
| Reorder_Calculation_Workflow.md | 15 | Medium |
| Vendor_Order_Decision_Tree.md | 8 | Low |
| Cut_Sheet_Logic_Decision_Tree.md | 12 | Medium |

---

## API Reference

### Get Mappings
```bash
curl https://gpt-mcp.onrender.com/wiki/api/mappings/03_Decision_Workflows/Inventory_Filtering_Workflow.md
```

### Create Mapping
```bash
curl -X POST https://gpt-mcp.onrender.com/wiki/api/mappings/<file_path> \
  -H "Content-Type: application/json" \
  -d '{
    "diagram_id": "diagram_0",
    "node_id": "B",
    "section_id": "step-1-load-snapshot",
    "color": "#ffeb3b",
    "label": "Load & Snapshot"
  }'
```

### Suggest Next Color
```bash
curl "https://gpt-mcp.onrender.com/wiki/api/suggest-color?file=<file_path>"
```

---

## Color Palette

Mappings use a 10-color Material Design palette (auto-suggested in order):

1. `#ffeb3b` Yellow
2. `#ff9800` Orange
3. `#f44336` Red
4. `#e91e63` Pink
5. `#9c27b0` Purple
6. `#3f51b5` Indigo
7. `#2196f3` Blue
8. `#00bcd4` Cyan
9. `#009688` Teal
10. `#4caf50` Green

---

## Decision Tree Visualizer

**URL:** https://gpt-mcp.onrender.com/wiki/decision-tree/

Interactive playground for testing reorder decision logic with vendor-specific parameters.

### Features
- **Vendor Selection:** Bullseye, Oceanside, CDV, Generic configs
- **Live Path Tracing:** Active path highlights as inputs change
- **Test Inputs:** Years in Stock slider, Has Larger Sheets toggle
- **JSON Editors:** Modify master logic and vendor config in-browser

### Architecture
One master tree with `{placeholders}` resolved at runtime by vendor parameters.

### Files
| File | Purpose |
|------|---------|
| `decision_tree/routes.py` | Flask routes |
| `templates/decision_tree.html` | Jinja template |
| `static/decision_tree.js` | DecisionTreeApp class |
| `static/decision_tree.css` | Styling |
| `config/decision_trees/vendors.json` | Vendor parameters |

See `wiki_viewer/decision_tree/DEVELOPMENT.md` for development guide.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Can't click Mermaid node | Enable admin mode (orange banner visible) |
| Can't click text heading | Only H2, H3, H4 clickable; must select node first |
| Mapping doesn't work | Refresh page (Ctrl+R) |
| 404 error on /wiki/view | Check file path (case-sensitive) |
| Diagram not rendering | Check browser console for Mermaid.js errors |

---

## Dependencies

- `markdown>=3.5.0` - Markdown to HTML conversion
- `pymdown-extensions>=10.0` - Extended markdown features
- Flask (already installed)
- Mermaid.js (CDN - no server-side dependency)

---

## Integration

Same deployment as TiDB Sync + Agent Garden + Claude Task Queue:
- URL: https://gpt-mcp.onrender.com
- Paths: `/` (TiDB), `/AgentGarden/` (Agent Garden), `/wiki/` (Wiki Viewer)
