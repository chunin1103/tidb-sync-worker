# Wiki Mapping Instructions

**Purpose:** Guide for creating node-to-text mappings for Wiki Viewer Mermaid diagrams

**Last Updated:** 2025-12-30

---

## Overview

Wiki mappings enable bidirectional linking between Mermaid diagram nodes and their corresponding text explanations. When a user clicks a diagram node, the page scrolls to the relevant text section and vice versa.

---

## JSON Structure (CRITICAL!)

### Correct Structure

```json
{
  "version": "1.0",
  "last_modified": "2025-12-30T00:00:00Z",
  "files": {
    "03_Decision_Workflows/Cut_Sheet_Logic_Decision_Tree.md": {
      "mappings": [
        {
          "diagram_id": "diagram_0",
          "node_id": "A",
          "section_id": "overview",
          "color": "#ffeb3b",
          "label": "Overview",
          "preview_text": "This workflow determines..."
        }
      ]
    }
  }
}
```

### Common Error (DO NOT DO THIS!)

```json
{
  "files": {
    "path/to/file.md": [  // ❌ WRONG - Direct array
      { "node_id": "A", ... }
    ]
  }
}
```

**Why this matters:**
- Code expects: `data['files'][path].get('mappings', [])`
- If you use direct array: `AttributeError: 'list' object has no attribute 'get'`
- Always wrap mappings in `{"mappings": [...]}` object

---

## Mapping Workflow

### Step 1: Analyze the Wiki File

1. **Read the markdown file** containing the Mermaid diagram
2. **Identify all diagram nodes** (A, B, C, D, etc.)
3. **Understand the flow** - what each node represents in the decision tree
4. **Locate text sections** that explain each node's logic

### Step 2: Match Nodes to Text Sections

For each diagram node, identify:
- **What concept does this node represent?**
- **Which heading/section explains this concept?**
- **What are the key details in that section?**

**Example from Cut Sheet Logic:**
- Node `H` = "Check Cascade Opportunity"
- Maps to section: "Example 3: Bullseye with Cascade (Complex)"
- Why? That section explains cascade logic in detail with calculations

### Step 3: Generate Section IDs

Section IDs are **derived from markdown headings** using these rules:

1. **Take the heading text** (without `#` symbols)
2. **Convert to lowercase**
3. **Replace spaces with hyphens**
4. **Remove special characters** (keep only letters, numbers, hyphens)
5. **Remove parentheses and colons**

**Examples:**
```
## 📋 Overview                              → overview
## 🔢 Impact Calculation Formulas           → impact-calculation-formulas
### Step 1: Calculate Pieces Needed         → step-1-calculate-pieces-needed
### Example 3: Bullseye with Cascade (Complex) → example-3-bullseye-with-cascade-complex
## ⚠️ Safety Checks and Guardrails          → safety-checks-and-guardrails
### Critical Errors to Prevent              → critical-errors-to-prevent
```

**Verification:** Open the wiki page in browser, right-click heading → Inspect → check the `id` attribute.

### Step 4: Choose Colors

Use the **10-color Material Design palette** in order:

```json
[
  "#ffeb3b",  // 1. Yellow
  "#ff9800",  // 2. Orange
  "#f44336",  // 3. Red
  "#e91e63",  // 4. Pink
  "#9c27b0",  // 5. Purple
  "#3f51b5",  // 6. Indigo
  "#2196f3",  // 7. Blue
  "#00bcd4",  // 8. Cyan
  "#009688",  // 9. Teal
  "#4caf50"   // 10. Green
]
```

**Best Practices:**
- **Assign colors sequentially** for most nodes
- **Reuse colors** for related concepts (e.g., all "Oceanside Strategy" nodes use same color)
- **Use contrasting colors** for branching decisions (Yes/No paths)
- **Green tones** for success/completion nodes
- **Red/Orange tones** for warnings/errors

**Color Grouping Example (Cut Sheet):**
- Nodes A, B = Yellow, Orange (overview/matrix)
- Nodes C, E, F, I, K = Red (all Oceanside strategy)
- Nodes D, G, N, O = Pink (all Bullseye strategy)
- Nodes P, Q, R, S = Blue family (calculation formulas)
- Node L = Red-Orange (vendor order fallback)
- Node Y = Green (success example)

### Step 5: Write Preview Text

Preview text appears in **tooltip on hover**. Guidelines:

1. **Length:** 100-200 characters optimal
2. **Content:** Key takeaway from the section
3. **Format:** Plain text, no markdown
4. **Focus:** Answer "What will I learn if I click this?"

**Good Examples:**
```json
"preview_text": "ALWAYS check cascade opportunities FIRST (most common error!). Critical Constraint: For 3mm glass, 2 Half Sheets = 1 Full Sheet equivalent."

"preview_text": "Decision: Cut 4 sheets of 24×24 → 64 pieces of 6×6. Result: 6×6: 50 → 114 pieces (0.35 YIS) ✓ Target reached."
```

**Bad Examples:**
```json
"preview_text": "See section for details"  // ❌ Not helpful
"preview_text": "This section explains..."  // ❌ Too vague
```

### Step 6: Write Label

Label appears as **visible text in mapping UI**. Guidelines:

1. **Length:** 2-5 words
2. **Descriptive:** Clear what the node represents
3. **Consistent:** Use same terminology as diagram/text

**Good Examples:**
```json
"label": "Cascade Half→Full"
"label": "Impact Formulas"
"label": "Cut from 24×24"
"label": "Safety Checks"
```

**Bad Examples:**
```json
"label": "A"                    // ❌ Just node ID
"label": "This is the step"    // ❌ Too vague
"label": "Calculate the target inventory after cutting from source" // ❌ Too long
```

---

## Mapping Strategies

### Strategy 1: One-to-One Mapping

**Use when:** Each node has a dedicated section explaining it.

**Example:**
```
Node A ("Size Below Target YIS")
  → Maps to: "## 📋 Overview"
  → Why: Overview explains when workflow triggers
```

### Strategy 2: Many-to-One Mapping

**Use when:** Multiple nodes reference the same detailed section.

**Example:**
```
Node P, Q ("Calculate Impact")
  → Both map to: "## 🔢 Impact Calculation Formulas"
  → Why: Section covers all calculation steps

Node R, S ("Source After Cut ≥ Minimum?")
  → Both map to: "### Step 3: Validate Source Inventory After Cut"
  → Why: Same validation logic applies
```

### Strategy 3: Example-Based Mapping

**Use when:** Node represents a decision, best explained through examples.

**Example:**
```
Node H ("Check Cascade Opportunity")
  → Maps to: "### Example 3: Bullseye with Cascade (Complex)"
  → Why: Example shows cascade logic in action with real numbers

Node L ("No Cutting Options → Vendor Order")
  → Maps to: "### Example 4: No Cutting Option (Vendor Order)"
  → Why: Example demonstrates when to skip cutting
```

### Strategy 4: Concept Grouping

**Use when:** Multiple nodes share a common concept.

**Example (Oceanside Strategy):**
```
Node C: "24×24 Available & Above Min?"
Node E: "Option 1: Cut from 24×24"
Node F: "12×12 Available & Above Min?"
Node I: "Option 2: Cut from 12×12"
Node K: "Option 3: Cut from 6×12"

All map to: "### Oceanside COE96 Strategy"
All use same color: #f44336 (Red)
Why: Table shows all source priorities together
```

---

## Complete Mapping Example

**Scenario:** Map Node H from Cut Sheet Logic Decision Tree

**Node in Mermaid:**
```mermaid
D -->|No| H{Check Cascade<br/>Opportunity}
H -->|2 Half ≥ 0.40 YIS| M[Option: Cascade Half→Full<br/>Then Cut Full]
```

**Corresponding Text Section:**
```markdown
### Example 3: Bullseye with Cascade (Complex)

**Scenario:**
- **Target:** 10×10 Black Opal 3mm
- **Current:** 30 pieces (0.20 YIS, at minimum)
- **Full Sheet:** 0 (out of stock)
- **Half Sheet:** 18 pieces (0.65 YIS)

**Decision Process:**
1. ❌ Full Sheet not available
2. ✅ Check cascade: 2 Half = 1 Full for 3mm
3. Calculate cascade: Need 1 Full (yields 4× 10×10)
4. Use 2 Half sheets → Creates 1 Full equivalent
5. Check Half after cascade: 18 - 2 = 16 → 16÷24.6 = 0.65 YIS ✓ Still > 0.40
```

**Mapping JSON:**
```json
{
  "diagram_id": "diagram_0",
  "node_id": "H",
  "section_id": "example-3-bullseye-with-cascade-complex",
  "color": "#9c27b0",
  "label": "Cascade Example",
  "preview_text": "Check cascade: 2 Half = 1 Full for 3mm. Calculate cascade: Need 1 Full (yields 4× 10×10). Use 2 Half sheets → Creates 1 Full equivalent. Check Half after cascade must still be > 0.40 YIS. Without checking cascade, would have incorrectly ordered Full sheet!"
}
```

**Explanation:**
- **diagram_id:** Always `diagram_0` for first diagram in file
- **node_id:** `H` from the Mermaid diagram
- **section_id:** `example-3-bullseye-with-cascade-complex` (heading converted to ID)
- **color:** `#9c27b0` (Purple - 5th in palette, used for cascade-related nodes)
- **label:** "Cascade Example" (concise, descriptive)
- **preview_text:** Highlights the critical cascade logic and common mistake

---

## Testing Mappings

### Before Committing

1. **Validate JSON syntax:**
   ```bash
   python -c "import json; json.load(open('wiki_mappings.json'))"
   ```
   - If no errors → JSON is valid
   - If errors → fix syntax issues

2. **Verify structure:**
   ```python
   import json
   data = json.load(open('wiki_mappings.json'))

   # Check correct structure
   assert 'files' in data
   for path, file_data in data['files'].items():
       assert 'mappings' in file_data  # Must have 'mappings' key
       assert isinstance(file_data['mappings'], list)
   ```

3. **Count mappings:**
   ```bash
   # Should match number of nodes you mapped
   grep -c '"node_id"' wiki_mappings.json
   ```

### After Deploying

1. **Open wiki page:** https://gpt-mcp.onrender.com/wiki/view/[file-path]
2. **Check node colors:** All mapped nodes should have colored backgrounds
3. **Test node → text:** Click a colored node → page should scroll to corresponding section
4. **Test text → node:** Click a colored section heading → node should highlight with pulse
5. **Verify tooltips:** Hover over node → tooltip should show preview text

---

## Troubleshooting

### Issue: Mappings not loading

**Symptoms:**
- Nodes don't have colored backgrounds
- Clicking nodes doesn't scroll to text
- Browser console shows no errors

**Solutions:**
1. **Check file path:**
   ```json
   "03_Decision_Workflows/Cut_Sheet_Logic_Decision_Tree.md"  // ✓ Correct
   "03_Decision_Workflows/Cut_Sheet_Logic_Decision_Tree"     // ✗ Missing .md
   "Cut_Sheet_Logic_Decision_Tree.md"                        // ✗ Missing folder
   ```

2. **Verify structure:**
   - Ensure `{"mappings": [...]}` wrapper exists
   - Check for trailing commas (invalid JSON)

3. **Clear browser cache:**
   - Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)

### Issue: Section not found

**Symptoms:**
- Click node → page scrolls to wrong section or not at all
- Browser console: "Section ID not found"

**Solutions:**
1. **Verify section_id matches heading ID:**
   - Open page, right-click heading → Inspect
   - Check `<h2 id="...">` or `<h3 id="...">`
   - Copy exact ID to `section_id` field

2. **Check for typos:**
   ```
   "section_id": "impact-calculation-formulas"  // ✓ Correct
   "section_id": "impact-calculation-formula"   // ✗ Missing 's'
   "section_id": "Impact-Calculation-Formulas"  // ✗ Wrong case
   ```

### Issue: AttributeError 'list' object has no attribute 'get'

**Cause:** Incorrect JSON structure (direct array instead of object wrapper)

**Fix:**
```json
// WRONG
"files": {
  "path/file.md": [...]
}

// CORRECT
"files": {
  "path/file.md": {
    "mappings": [...]
  }
}
```

### Issue: Colors not displaying

**Symptoms:**
- Nodes have no background color
- Text sections have no colored border

**Solutions:**
1. **Verify color format:**
   ```json
   "color": "#ffeb3b"   // ✓ Correct (hex with #)
   "color": "ffeb3b"    // ✗ Missing #
   "color": "yellow"    // ✗ Use hex codes
   ```

2. **Check CSS conflicts:**
   - Some Mermaid themes override colors
   - Ensure `wiki.css` is loading correctly

---

## Best Practices Summary

### DO:
- ✅ Use `{"mappings": [...]}` structure (not direct array)
- ✅ Map important decision nodes and formulas
- ✅ Group related nodes with same color
- ✅ Write descriptive preview text (100-200 chars)
- ✅ Test mappings after deploying
- ✅ Validate JSON syntax before committing

### DON'T:
- ❌ Map every single node (focus on key concepts)
- ❌ Use generic labels like "Step 1", "Option A"
- ❌ Create mappings for trivial nodes (Start, End)
- ❌ Forget to include .md extension in file path
- ❌ Use relative paths (always relative to wiki/ root)

---

## Reference Files

- **Example Mapping:** `wiki_mappings.json` → `Cut_Sheet_Logic_Decision_Tree.md` (27 nodes)
- **Mapping Manager Code:** `wiki_viewer/mapping_manager.py`
- **Wiki Viewer Documentation:** CLAUDE.md Section 7
- **Color Palette:** `wiki_viewer/static/wiki/wiki.css` (lines with `.mapping-color-`)

---

## Quick Start Checklist

When creating mappings for a new decision tree:

1. [ ] Read the wiki markdown file
2. [ ] Count total diagram nodes (A, B, C...)
3. [ ] Identify 10-15 most important nodes to map
4. [ ] For each node:
   - [ ] Identify corresponding text section
   - [ ] Generate section_id from heading
   - [ ] Choose color from palette
   - [ ] Write 2-5 word label
   - [ ] Write 100-200 char preview text
5. [ ] Create JSON with correct structure (`{"mappings": [...]}`)
6. [ ] Validate JSON syntax
7. [ ] Commit and push to GitHub
8. [ ] Wait for Render deploy (2-3 minutes)
9. [ ] Test on live wiki page
10. [ ] Verify all mappings work correctly

---

**Version:** 1.0
**Last Updated:** 2025-12-30
**Maintainer:** Claude (System Architect)
