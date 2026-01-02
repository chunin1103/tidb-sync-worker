# Decision Tree Visualizer

> **One Tree, Many Configurations** - Interactive reorder logic visualization

## Live URL
https://gpt-mcp.onrender.com/wiki/decision-tree/

## Architecture

The visualizer uses a **parameterized architecture** where a single master decision tree contains placeholders (like `{threshold_years}`) that get resolved at runtime based on the selected vendor's configuration.

```
┌─────────────────┐     ┌─────────────────┐
│  Master Logic   │  +  │  Vendor Config  │  =  Resolved Tree
│  (placeholders) │     │  (parameters)   │
└─────────────────┘     └─────────────────┘
```

## Files

### Frontend
- `wiki_viewer/templates/decision_tree.html` - Main page template
- `wiki_viewer/static/decision_tree.css` - Tailwind-inspired minimal styling
- `wiki_viewer/static/decision_tree.js` - `DecisionTreeApp` class with:
  - Vendor selection
  - Path calculation with condition evaluation
  - SVG tree rendering
  - JSON editors

### Backend
- `wiki_viewer/decision_tree/routes.py` - Flask routes and APIs
- `wiki_viewer/decision_tree/tree_engine.py` - Path evaluation engine
- `wiki_viewer/decision_tree/mermaid_parser.py` - Parses Mermaid diagrams from wiki (currently unused in new UI)

## Data Structures

### Master Logic (in HTML template)
```javascript
window.MASTER_LOGIC = {
    nodes: [
        { id: "start", label: "Start Evaluation", type: "start", x: 50, y: 5 },
        { id: "check_stock", label: "Stock < Vendor Threshold?", type: "decision", x: 50, y: 30 },
        // ... more nodes
    ],
    edges: [
        { from: "start", to: "check_stock" },
        {
            from: "check_stock",
            to: "stock_ok",
            label: "High Stock (>= {threshold_years})",  // Placeholder!
            condition: { field: "yearsInStock", operator: ">=", value: "{threshold_years}" }
        },
        // ... more edges
    ]
};
```

### Vendor Config
```javascript
window.VENDORS = {
    "Bullseye": {
        name: "Bullseye",
        threshold_years: 0.25,  // Replaces {threshold_years}
        allow_cascade: true
    },
    "Oceanside": {
        threshold_years: 0.35,
        allow_cascade: false
    }
};
```

## UI Components

### View Modes (Top Bar Tabs)
1. **Simulation** - Interactive tree with vendor selection and inputs
2. **Master Logic** - JSON editor for the decision tree structure
3. **Vendor Config** - JSON editor for vendor parameters

### Sidebar (Simulation Mode)
1. **Vendor Grid** - Small buttons to select vendor
2. **Active Rules** - Shows resolved threshold + cascade values
3. **Test Data** - Years in Stock slider + Has Larger Sheets toggle

### Canvas
- SVG-based tree rendering
- Nodes: rounded rectangles with icons (start/decision/end types)
- Edges: lines with arrow markers
- Active path: indigo highlight, inactive: gray

## Path Calculation Logic

```javascript
calculatePath() {
    // Start at 'start' node
    let currentNodeId = 'start';

    while (currentNodeId) {
        this.activePath.add(currentNodeId);

        // Find edge where condition evaluates to true
        const edge = this.masterLogic.edges.find(e =>
            e.from === currentNodeId && this.evaluateCondition(e.condition)
        );

        currentNodeId = edge ? edge.to : null;
    }
}

evaluateCondition(condition) {
    // Handle complex logic (cascade_check, fallback)
    if (condition.complex_logic === 'cascade_check') {
        return this.currentVendor.allow_cascade && this.simData.hasLargerSheets;
    }

    // Handle field comparison with placeholder resolution
    if (condition.field) {
        const val = this.simData[condition.field];
        let target = condition.value;

        // Resolve {placeholder} to vendor value
        if (target.startsWith('{')) {
            target = this.currentVendor[target.slice(1, -1)];
        }

        // Compare based on operator
        switch (condition.operator) {
            case '>=': return val >= target;
            case '<': return val < target;
            // ...
        }
    }
}
```

## React Prototype Reference

The UI was designed to match `VisualizingDecisionTreeLogic.tsx` which features:
- Clean slate color palette
- Small vendor selection buttons
- Simple slider input
- Toggle switch for boolean options
- Mode tabs for switching views
- JSON editors for configuration

## Future Improvements

### High Priority
- [ ] Load master logic from server-side JSON file (not hardcoded in template)
- [ ] Save edited JSON back to server
- [ ] Add more vendors dynamically
- [ ] Better error handling for invalid JSON

### Medium Priority
- [ ] Add node click to show details
- [ ] Add feedback/comments system (was in previous version)
- [ ] Export tree as image/PDF
- [ ] Undo/redo for JSON edits

### Nice to Have
- [ ] Drag-and-drop node positioning
- [ ] Visual node/edge editor (no JSON)
- [ ] Multiple tree support (tabs)
- [ ] Comparison view (two vendors side-by-side)
- [ ] Animation of path traversal

## Related Documentation

- **Reorder Logic**: See `wiki/03_Decision_Workflows/` for business logic documentation
- **Vendor Thresholds**:
  - Bullseye: 0.25yr threshold, 0.40yr target, cascade enabled
  - Oceanside: 0.35yr threshold, no cascade
  - Color De Verre: 0.30yr threshold, round to 5, no cascade

## Development

### Local Testing
The app runs as part of the wiki_viewer Flask blueprint:
```bash
cd render-tidb-sync
python unified_app.py
# Visit http://localhost:10000/wiki/decision-tree/
```

### Deployment
Commits to `master` branch auto-deploy to Render.

---
*Last updated: January 2026*
