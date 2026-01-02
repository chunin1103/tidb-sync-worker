# Decision Tree Visualizer - Development Guide

> Quick reference for maintaining and extending the interactive decision tree UI

## Live URL
https://gpt-mcp.onrender.com/wiki/decision-tree/

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        BACKEND (Flask)                          │
├─────────────────────────────────────────────────────────────────┤
│  routes.py          │ Flask routes, passes vendor_details      │
│  tree_engine.py     │ Path evaluation, placeholder resolution  │
│  vendors.json       │ Vendor parameters (threshold, cascade)   │
│  master_logic.json  │ Decision tree structure (29 nodes)       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                       FRONTEND (Vanilla JS)                     │
├─────────────────────────────────────────────────────────────────┤
│  decision_tree.html │ Template + convertTreeFormat() converter │
│  decision_tree.js   │ DecisionTreeApp class (path calculation) │
│  decision_tree.css  │ Tailwind-inspired styling                │
└─────────────────────────────────────────────────────────────────┘
```

## Comprehensive Tree Structure (v2.0)

The decision tree covers the **complete inventory workflow** from data input to output:

```
PHASES:
├── input        → Data loading and validation
├── analysis     → Filter checks, keyword exclusions
├── cascade      → Family-based cascade logic (Bullseye 3mm)
├── decision     → YIS threshold comparisons
├── calculation  → Order quantity computation
└── output       → Cut sheets, orders, reports
```

**29 nodes** organized across 6 workflow phases with **47 edges** containing condition logic.

## Key Files

| File | Purpose |
|------|---------|
| `routes.py` | Flask routes, loads master tree from `engine.get_tree()` |
| `decision_tree.html` | Jinja template with `convertTreeFormat()` for JSON→array conversion |
| `decision_tree.js` | `DecisionTreeApp` class - vendor selection, path calculation, SVG rendering |
| `decision_tree.css` | Responsive styling with CSS variables |
| `config/decision_trees/vendors.json` | 5 vendors with detailed parameters and cascade rules |
| `config/decision_trees/master_logic.json` | 29-node tree covering full workflow |

## Node Types

| Type | Icon | Purpose |
|------|------|---------|
| `start` | ▶ Play | Entry point of workflow |
| `process` | ⚙ Gear | Data processing step |
| `decision` | ◇ Diamond | Yes/No branch point |
| `calculation` | Σ Sigma | Numeric computation |
| `result` | ■ Square | Terminal outcome |
| `end` | ● Circle | Final endpoint |

## Data Flow

```
1. Backend loads master_logic.json via engine.get_tree()
   ↓
2. Template converts nodes object → array via convertTreeFormat()
   ↓
3. User clicks vendor button → selectVendor(vendorId)
   ↓
4. calculatePath() traces from START node through phases:
   input → analysis → cascade → decision → calculation → output
   ↓
5. evaluateCondition() resolves placeholders like {threshold_years}
   ↓
6. renderTree() highlights active path in indigo (#4f46e5)
```

## JSON Format Conversion

The backend stores nodes as an **object** (keyed by ID), but frontend needs an **array**:

```javascript
// Backend format (master_logic.json)
"nodes": {
  "START": { "label": "Start", "type": "start", "position": {"x": 600, "y": 50} }
}

// Frontend format (after convertTreeFormat)
nodes: [
  { id: "START", label: "Start", type: "start", x: 50, y: 5 }  // x,y as percentages
]
```

The `convertTreeFormat()` function in the template handles this conversion and normalizes pixel positions to 5-95% range.

## Common Issues & Fixes

### Issue: Nodes move on hover
**Cause:** CSS `transform: scale()` on SVG groups conflicts with existing `translate()`
**Fix:** Use `filter: drop-shadow()` instead of scale transforms
```css
/* BAD - causes movement */
.node-group:hover { transform: scale(1.02); }

/* GOOD - no movement */
.node-group:hover rect { filter: drop-shadow(0 4px 8px rgba(79, 70, 229, 0.3)); }
```

### Issue: Vendor selection doesn't work
**Cause:** Mismatch between button `data-vendor-id` and `window.VENDORS` keys
**Fix:** Generate `window.VENDORS` dynamically from backend `vendor_details`
```jinja
{# In decision_tree.html #}
window.VENDORS = {
    {% for vendor_id, vendor_data in vendor_details.items() %}
    "{{ vendor_id }}": { ... }
    {% endfor %}
};
```
**Important:** `routes.py` must pass `vendor_details=engine.get_vendors().get('vendors', {})`

### Issue: Path not updating when slider moves
**Cause:** `calculatePath()` not called or `currentVendor` is null
**Debug:** Open browser console (F12) - logs show path calculation details
```javascript
// Console output when working correctly:
Selected vendor: bullseye {name: "Bullseye Glass", threshold_years: 0.25, ...}
Path calculated: {path: ["start", "check_stock", ...], yearsInStock: 0.15, threshold: 0.25}
```

## Vendor Configuration

Current vendors: **bullseye**, **bullseye_cutsheet**, **oceanside**, **cdv**, **generic**

### Adding a New Vendor

1. **Edit `config/decision_trees/vendors.json`:**
```json
"new_vendor": {
  "id": "new_vendor",
  "name": "New Vendor Name",
  "description": "Description of vendor",
  "parameters": {
    "threshold_years": 0.25,        // YIS below this triggers reorder
    "target_years": 0.40,           // Target YIS after ordering
    "lean_threshold": 0.15,         // Below this = urgent
    "well_stocked_threshold": 0.40, // Above this = skip family cascade
    "overstocked_threshold": 0.50,  // Above this = never order
    "allow_cascade": true,          // Enable family cascade logic
    "source_min_yis": 0.20,         // Min YIS for cascade source
    "half_min_yis": 0.15,           // Min YIS for half-sheet source
    "has_special_rules": false,     // Vendor-specific logic
    "rounding_multiple": 1,         // Round to multiples of N
    "zero_stock_bonus": 50          // Extra units if qty=0
  },
  "cascade_rules": {
    "full_to_half": { "pieces_per_full": 2, "enabled": true }
  },
  "display": { "color": "#4caf50" }
}
```

2. **Restart server** - template auto-generates vendor button and config

### Key Vendor Parameters

| Parameter | Description | Typical Values |
|-----------|-------------|----------------|
| `threshold_years` | Trigger reorder when YIS below this | 0.25 - 0.30 |
| `target_years` | Order enough to reach this YIS | 0.35 - 0.40 |
| `allow_cascade` | Enable "cut from larger sheet" logic | true (Bullseye 3mm) |
| `source_min_yis` | Cascade source must have at least this YIS | 0.20 |
| `zero_stock_bonus` | Extra quantity when current stock = 0 | 50 |

## Modifying Decision Tree Logic

Edit `config/decision_trees/master_logic.json` or use the "Master Logic" tab in UI:

```javascript
// Node with position and phase
{
  "CHECK_YIS": {
    "label": "YIS < Threshold?",
    "type": "decision",
    "description": "Compare years in stock to vendor threshold",
    "phase": "decision",
    "position": { "x": 600, "y": 700 }
  }
}

// Edge with simple condition
{
  "id": "e_yis_yes",
  "from": "CHECK_YIS",
  "to": "CALC_ORDER_QTY",
  "label": "Yes (< {threshold_years})",
  "condition": { "field": "yearsInStock", "operator": "<", "value": "{threshold_years}" },
  "condition_result": true
}

// Edge with complex logic (handled in evaluateCondition)
{
  "id": "e_cascade",
  "from": "CHECK_CASCADE_ALLOWED",
  "to": "CHECK_FAMILY_SOURCE",
  "label": "Cascade Enabled",
  "condition": { "complex_logic": "cascade_check" }
}

// Edge with contains_any condition
{
  "id": "e_keyword_exclude",
  "from": "CHECK_KEYWORD_FILTER",
  "to": "SKIP_PRODUCT",
  "label": "Reserved Keywords",
  "condition": {
    "field": "product_name",
    "operator": "contains_any",
    "value": ["reserve", "frit", "stringers", "noodles", "pound", "pack"]
  }
}
```

### Condition Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `<`, `>`, `<=`, `>=`, `==` | Numeric comparison | `{"field": "yearsInStock", "operator": "<", "value": 0.25}` |
| `contains_any` | String contains any keyword | `{"field": "product_name", "operator": "contains_any", "value": ["reserve"]}` |
| `complex_logic` | Custom JS evaluation | `{"complex_logic": "cascade_check"}` |

## CSS Variables

Key variables in `decision_tree.css`:
```css
:root {
  --primary: #4f46e5;      /* Indigo - active elements */
  --slate-200: #e2e8f0;    /* Borders */
  --slate-400: #94a3b8;    /* Inactive text */
  --sidebar-width: 320px;
}
```

## Testing Checklist

- [ ] Hover nodes - no position shift, shows drop-shadow
- [ ] Click vendor - "Active Rules" panel appears with correct threshold
- [ ] Move slider - path updates in real-time
- [ ] Toggle "Has Larger Sheets" - cascade logic changes path
- [ ] Console shows debug logs (no errors)
- [ ] Mobile responsive - sidebar collapses on small screens

## Related Documentation

- `README.md` - High-level architecture and future improvements
- `Production/wiki/03_Decision_Workflows/` - Business logic documentation
- `Production/wiki/08_Database_Schema/TIDB_SCHEMA_GUIDE.md` - Database field reference
- `config/decision_trees/master_logic.json` - Full 29-node decision tree
- `config/decision_trees/vendors.json` - 5-vendor configuration reference

## Business Logic Sources (Consolidated)

The comprehensive decision tree consolidates logic from:

| Source | Key Concepts |
|--------|--------------|
| `Production/wiki/03_Decision_Workflows/` | YIS calculation, threshold comparisons |
| `Bullseye Glass/scripts/` | Cascade logic (2 Half = 1 Full), keyword filtering |
| `Bullseye Glass/PROCESSES/` | Family grouping, cut sheet generation |

### YIS Calculation Reference
```
Years in Stock (YIS) = quantity_in_stock / annual_purchased
```
- **Threshold**: 0.25 years (trigger reorder)
- **Target**: 0.40 years (order enough to reach)
- **Zero Stock**: Add bonus quantity (typically 50 units)

### Cascade Logic (Bullseye 3mm Only)
```
If 8x10 sheet is low AND 10x10 has YIS >= 0.20:
  → Cut 10x10 in half to make two 8x10 (via cut sheet)
  → Skip vendor order for 8x10
```

## Changelog

### v2.0 (January 2026)
- Expanded master_logic.json from 14 → 29 nodes
- Added 6 workflow phases: input, analysis, cascade, decision, calculation, output
- Added vendors: bullseye_cutsheet, oceanside, cdv, generic
- Template now loads tree from backend JSON
- Added `convertTreeFormat()` for JSON object → array conversion
- Added node types: process, calculation
- Improved edge condition evaluation (contains_any, complex_logic)
- Expanded SVG viewBox to 1200x1400 for larger tree
