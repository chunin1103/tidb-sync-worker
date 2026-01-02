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
│  master_logic.json  │ Decision tree structure (nodes, edges)   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                       FRONTEND (Vanilla JS)                     │
├─────────────────────────────────────────────────────────────────┤
│  decision_tree.html │ Template + window.MASTER_LOGIC/VENDORS   │
│  decision_tree.js   │ DecisionTreeApp class (path calculation) │
│  decision_tree.css  │ Tailwind-inspired styling                │
└─────────────────────────────────────────────────────────────────┘
```

## Key Files

| File | Purpose |
|------|---------|
| `routes.py` | Flask routes, passes `vendors` and `vendor_details` to template |
| `decision_tree.html` | Jinja template, generates `window.VENDORS` from backend |
| `decision_tree.js` | `DecisionTreeApp` class - vendor selection, path calculation, SVG rendering |
| `decision_tree.css` | Responsive styling with CSS variables |
| `config/decision_trees/vendors.json` | Vendor parameters (threshold_years, allow_cascade, etc.) |
| `config/decision_trees/master_logic.json` | Tree structure with placeholders |

## Data Flow

```
1. User clicks vendor button
   ↓
2. selectVendor(vendorId) called
   ↓
3. this.currentVendor = this.vendors[vendorId]
   ↓
4. calculatePath() traces from 'start' node
   ↓
5. evaluateCondition() resolves {threshold_years} placeholders
   ↓
6. renderTree() highlights active path in indigo
```

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

## Adding a New Vendor

1. **Edit `config/decision_trees/vendors.json`:**
```json
"new_vendor": {
  "id": "new_vendor",
  "name": "New Vendor Name",
  "parameters": {
    "threshold_years": 0.30,
    "target_years": 0.40,
    "allow_cascade": false
  },
  "display": { "color": "#4caf50" }
}
```

2. **Restart server** - template auto-generates vendor button and config

## Modifying Decision Tree Logic

Edit `window.MASTER_LOGIC` in `decision_tree.html` or use the "Master Logic" tab in UI:

```javascript
// Node types: start, decision, end
{ id: "my_node", label: "Check Something?", type: "decision", x: 50, y: 50 }

// Edge with condition (placeholders resolved at runtime)
{
  from: "check_stock",
  to: "next_node",
  label: "Below {threshold_years}",
  condition: { field: "yearsInStock", operator: "<", value: "{threshold_years}" }
}

// Edge with complex logic
{
  from: "check_cascade",
  to: "cut_sheet",
  condition: { complex_logic: "cascade_check" }  // Handled in evaluateCondition()
}
```

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
- `config/decision_trees/vendors.json` - Vendor parameter reference
