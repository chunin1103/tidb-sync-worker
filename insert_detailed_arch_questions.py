"""
Insert DETAILED architectural questions for Bullseye Decision Tree refinement
Includes full context, tables, comparisons, and comprehensive explanations
"""
import os
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv('agent_garden/.env')

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("[ERROR] DATABASE_URL not found in environment variables")
    exit(1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def insert_detailed_questions():
    """Insert comprehensive architectural questions with full analysis"""

    session_id = f"ARCH-DT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"  # 22 chars (within 36 limit)
    filename = "DecisionTree_Analysis_DETAILED.md"
    manufacturer = "Bullseye Glass"

    db = SessionLocal()

    try:
        # Create session
        print(f"[SESSION] Creating: {session_id}")
        db.execute(text("""
            INSERT INTO reorder_sessions (session_id, csv_filename, total_products, manufacturer, status, created_by)
            VALUES (:session_id, :filename, :total_products, :manufacturer, 'pending_questions', :created_by)
        """), {
            'session_id': session_id,
            'filename': filename,
            'total_products': 0,
            'manufacturer': manufacturer,
            'created_by': 'claude_detailed_analysis'
        })
        db.commit()

        # Define comprehensive questions
        questions = [
            # Question 1: Holly Berry Red Seasonal Rule
            {
                'priority': 'HIGH',
                'question_text': """# QUESTION 1: Holly Berry Red Seasonal Rule

## What We Found

**Source:** `Bullseye Glass/MASTER_CONTEXT_PROMPT.md` (lines 167-168)

The knowledge base mentions:
```
**Special:** Holly Berry Red must be pre-ordered by June 30th (seasonal)
```

However, the current **Decision Tree** and **Calculator Code** do NOT include any logic for seasonal products.

## Why This Matters

**Impact:** If Holly Berry Red (or other seasonal products) still require pre-ordering by specific dates:
- The decision tree should have a **decision node** checking if product is seasonal
- The calculator should **flag seasonal products** with HIGH priority
- Users need to know the deadline BEFORE running regular reorder calculations
- Missing the June 30th deadline = Cannot order Holly Berry Red for the season

## Current Coverage

| Component | Has Seasonal Logic? | Details |
|-----------|---------------------|---------|
| **Decision Tree** | ❌ NO | No mention of seasonal products or pre-order deadlines |
| **Calculator Code** | ❌ NO | No seasonal product detection or deadline warnings |
| **REORDER_RULES.md** | ❌ NO | No seasonal rules documented |
| **MASTER_CONTEXT_PROMPT** | ✅ YES | Mentions Holly Berry Red June 30th deadline |

## Your Decision Needed

**Is the "pre-order by June 30th" requirement for Holly Berry Red still active?**

If YES, should the decision tree include:
1. A decision node: "Is this a seasonal product (e.g., Holly Berry Red)?"
2. A special path: "Check if within pre-order window (before June 30th)"
3. An alert: "Seasonal product - must order by [deadline] or wait until next season"
4. A list of seasonal products and their deadlines

**Additional Questions:**
- Are there other seasonal products besides Holly Berry Red?
- Do seasonal products have different inventory thresholds?
- Should seasonal products appear in a separate section of the reorder report?""",
                'field_name': 'holly_berry_red_seasonal_rule',
                'suggested_answer': 'Yes - add seasonal product decision node with deadline checking. Holly Berry Red deadline: June 30th annually.',
                'product_id': 0,
                'product_name': 'SYSTEM: Seasonal Products Logic',
                'pre_answer': None
            },

            # Question 2: System Boundary Confusion
            {
                'priority': 'HIGH',
                'question_text': """# QUESTION 2: System Boundary Clarity - Inventory Translation Rule

## What We Found

**The knowledge base conflates THREE DIFFERENT SYSTEMS:**

| System | Purpose | Frequency | Key Files |
|--------|---------|-----------|-----------|
| **ORDERING** (Vendor Purchase) | What to order from Bullseye | ~10x/year (every 37 days) | REORDER_RULES.md, Decision Tree |
| **RECEIVING** (When sheets arrive) | How to cut incoming Full Sheets | Per order arrival | SESSION_LEARNINGS_2025-12-15.md |
| **CUT SHEETS** (Biweekly rebalancing) | Gap-filling between orders | Every 14 days | GLASS_CUTTING_KNOWLEDGE.md |

## The Confusing Rule

**"Inventory Translation Rule"** appears in multiple knowledge files:

```
Even "Half Sheet" count in inventory = Full Sheets
Odd "Half Sheet" count = Full Sheets + 1 actual Half Sheet
Example: 5 "Half Sheets" = 2 Full + 1 Half
```

**Source:** `GLASS_CUTTING_KNOWLEDGE.md` (lines 88-90)

## Analysis: Which System Does This Rule Apply To?

| System | Does This Rule Apply? | Why / Why Not |
|--------|----------------------|---------------|
| **ORDERING** | ❓ UNCLEAR | The decision tree doesn't reference this rule. Does vendor ordering use this translation? |
| **RECEIVING** | ❓ UNCLEAR | When Full Sheets arrive, they aren't in inventory yet - no translation needed |
| **CUT SHEETS** | ✅ LIKELY YES | Cut Sheet CSV shows "Half Sheet" quantities that need interpretation for "how many Full Sheets are these?" |

## The Problem

If this rule is **CUT SHEET SPECIFIC**, including it in the **VENDOR ORDERING** decision tree causes confusion:
- Users think vendor ordering needs to translate Half Sheet inventory
- Mixes terminology from biweekly rebalancing with vendor purchase logic
- Creates architectural confusion between the three systems

## Current Documentation State

| Document | Includes This Rule? | Context |
|----------|---------------------|---------|
| **MASTER_CONTEXT_PROMPT.md** | ✅ YES | Lines 88-90, under "Cut Sheets System" section |
| **GLASS_CUTTING_KNOWLEDGE.md** | ✅ YES | Lines 88-90, labeled "Inventory Translation Rule" |
| **Decision Tree (Ordering)** | ❌ NO | Does not reference this rule |
| **REORDER_RULES.md (Ordering)** | ❌ NO | Does not reference this rule |

## Your Decision Needed

**Is the "Inventory Translation Rule" only for the Cut Sheet system CSV interpretation?**

If YES, we should:
1. **Remove** references from VENDOR ORDERING documentation
2. Add a **"System Scope"** section to the decision tree explicitly stating: "This workflow is for VENDOR ORDERING only"
3. Add **clear references** to the other two systems: "For RECEIVING workflow, see SESSION_LEARNINGS_2025-12-15.md" and "For CUT SHEETS workflow, see GLASS_CUTTING_KNOWLEDGE.md"
4. Update the MASTER_CONTEXT_PROMPT to clarify which rules apply to which system

**Additional Questions:**
- When looking at inventory for vendor ordering, do you see "Half Sheets" as individual pieces or as Full Sheet equivalents?
- Does the inventory CSV for ordering use the same format as the Cut Sheet CSV?""",
                'field_name': 'inventory_translation_rule_scope',
                'suggested_answer': 'Yes - this is Cut Sheet only. Remove from ordering documentation and add clear system boundary sections to prevent confusion.',
                'product_id': 0,
                'product_name': 'SYSTEM: System Boundary Clarity',
                'pre_answer': None
            },

            # Question 3: Calculator Implementation Scope
            {
                'priority': 'HIGH',
                'question_text': """# QUESTION 3: Calculator Implementation Scope - Simplified vs Full Algorithm

## What We Found

The calculator code (`bullseye_calculator.py`) is a **simplified single-product calculator** with this comment:

```python
# Note: Full cascade algorithm (5 steps) requires manual review.
# This calculator provides basic reorder quantities and flags cascade opportunities.
```

## What the Calculator DOES vs DOES NOT Do

### ✅ Current Calculator Capabilities

| Feature | Implemented? | Details |
|---------|--------------|---------|
| Identify IF order needed | ✅ YES | Uses 0.25 threshold check |
| Calculate basic reorder quantity | ✅ YES | To reach 0.40 target |
| Flag cascade opportunities | ✅ YES | Adds questions like "Check if excess Half Sheets can be cascaded" |
| Handle edge cases | ✅ YES | Purchased=0, zero stock, lean inventory |
| Detect thickness | ✅ YES | Gets thickness but doesn't use it for calculations |
| Generate questions for manual review | ✅ YES | Creates HIGH/MEDIUM/LOW priority questions |

### ❌ Missing Capabilities (Full 5-Step Algorithm)

| Feature | Missing? | Impact |
|---------|----------|--------|
| **Cascade calculation** | ❌ NO | Only flags "review cascade opportunities" - doesn't calculate |
| **Product family grouping** | ❌ NO | Can't group Half/10×10/5×10/5×5 by Parent ID |
| **Thickness-specific cutting logic** | ❌ NO | Knows 3mm vs 2mm but doesn't apply different yields |
| **Cutting yield calculations** | ❌ NO | Doesn't know 3mm Full → 6× 10×10 + 2× 5×10 |
| **Full vs Cut vs Save breakdown** | ❌ NO | Just returns "reorder_quantity: X", not "8 Fulls (1 save as Half + 7 cut)" |
| **Byproduct tracking** | ❌ NO | Doesn't account for 5×10 byproducts from Full cuts |
| **STEP 4 (cascade from new order)** | ❌ NO | Missing entirely |
| **STEP 5 (final verification)** | ❌ NO | No "all sizes ≥ 0.40yr" check across size family |
| **BEFORE/AFTER spreadsheets** | ❌ NO | Doesn't generate validation tables |

## The Decision: Two Architectures

### OPTION A: Keep Simplified (Current Approach)

**How It Works:**
- Calculator processes ONE product at a time (single SKU)
- Identifies IF order is needed and HOW MUCH
- Flags cascade opportunities with questions
- User performs manual validation in Excel/PDF
- Full 5-step algorithm done by hand using spreadsheet

**Pros:**
- ✅ Simpler code (easier to maintain)
- ✅ Manual review ensures quality control
- ✅ User can override AI decisions
- ✅ Faster to implement
- ✅ No complex Parent ID grouping needed
- ✅ Works with current CSV upload workflow

**Cons:**
- ❌ Requires manual Excel/PDF validation step
- ❌ Not fully automated
- ❌ User must understand cascade logic
- ❌ Inconsistent results if different users interpret differently
- ❌ Cannot verify "all sizes ≥ 0.40yr" automatically

### OPTION B: Implement Full Algorithm

**How It Works:**
- Calculator groups products by Parent ID (Half/10×10/5×10/5×5 families)
- Performs all 5 steps automatically:
  1. CASCADE FROM INVENTORY (calculates excess, performs virtual cuts)
  2. CHECK IF ORDER NEEDED (0.25 threshold across all sizes)
  3. CALCULATE MINIMUM ORDER (3mm vs 2mm logic, Half deficit, cutting yields)
  4. CASCADE FROM NEW ORDER (byproduct tracking, surplus cascades)
  5. VERIFY ALL SIZES (ensures every size ≥ 0.40yr)
- Generates detailed BEFORE/AFTER spreadsheets
- Returns: "Order 8 Full Sheets: 1 saved as Half + 7 cut → yields X×10×10, Y×5×10, Z×5×5"

**Pros:**
- ✅ Fully automated calculation
- ✅ Consistent results every time
- ✅ Implements complete decision tree logic
- ✅ Validates across all sizes in family
- ✅ Generates audit trail (BEFORE/AFTER tables)
- ✅ No manual interpretation needed

**Cons:**
- ❌ Complex code (product family grouping)
- ❌ Harder to audit/debug
- ❌ Users can't easily override decisions
- ❌ Requires significant development time
- ❌ May need UI changes to display results

## Current Calculator Output Example

**Input:** Single product (e.g., "Black Opal 3mm Half Sheet")
```json
{
  "reorder_quantity": 8,
  "years_in_stock": 0.16,
  "reason": "Need 8 units to reach 0.40 years target (currently 0.16 years)",
  "questions": [
    {
      "priority": "MEDIUM",
      "question": "Product is 3mm Half Sheet. Check if excess Half Sheets can be cascaded (2 Half = 1 Full for cutting)."
    }
  ]
}
```

**What's Missing:** No cascade calculation, no family grouping, no BEFORE/AFTER, no verification across 10×10/5×10/5×5 siblings.

## Your Decision Needed

**Which approach do you want for the calculator?**

**A) Keep Simplified** (current)
- Calculator stays as-is (flags cascade opportunities)
- Full 5-step algorithm done manually in spreadsheet/PDF
- Faster to deploy, simpler code, manual quality control

**B) Implement Full Algorithm**
- Calculator performs all 5 steps automatically
- Requires product family grouping (Parent ID logic)
- Generates detailed BEFORE/AFTER spreadsheets
- Fully automated, complex code, harder to override

**Additional Questions:**
1. Do you need **product family support** (group Half/10×10/5×10/5×5 by Parent ID)?
2. Should calculator **output BEFORE/AFTER spreadsheets** or just final numbers?
3. Is manual Excel/PDF validation acceptable? Or must it be fully automated?
4. Who will be using this calculator? (Technical users who understand cascade logic, or non-technical warehouse staff?)""",
                'field_name': 'calculator_implementation_scope',
                'suggested_answer': 'Option A - Keep simplified with manual validation for quality control. Users validate in spreadsheet.',
                'product_id': 0,
                'product_name': 'SYSTEM: Calculator Architecture',
                'pre_answer': None
            },

            # Question 4: Formulas Reference Section
            {
                'priority': 'MEDIUM',
                'question_text': """# QUESTION 4: Formulas Reference Section - Python Code Snippets

## What We Found

The **Decision Tree** currently shows **conceptual formulas** like:

```
Years_in_Stock = Stock ÷ (Purchased ÷ 365)
Min_for_0.4yr = ⌈(146 × Purchased) ÷ 365⌉
```

However, **REORDER_RULES.md** includes **implementation-ready Python code**:

```python
# Years in Stock
years_in_stock = stock / (purchased / 365)
# or equivalently
years_in_stock = stock * 365 / purchased

# Minimum Stock for 0.4 Years
min_stock = math.ceil(146 * purchased / 365)

# Minimum Stock for 0.25 Years
min_stock = math.ceil(91 * purchased / 365)

# Target Stock (with lead time)
target = math.ceil(181 * purchased / 365)  # 146 + 35 days
```

## Comparison: Conceptual vs Implementation-Ready

| Formula | Decision Tree (Conceptual) | REORDER_RULES (Python) | Difference |
|---------|----------------------------|------------------------|------------|
| Years in Stock | `Years = Stock ÷ (Purchased ÷ 365)` | `years = stock * 365 / purchased` | Python shows division order, variable naming |
| 0.40yr Target | `Min = ⌈(146 × Purchased) ÷ 365⌉` | `min_stock = math.ceil(146 * purchased / 365)` | Shows `math.ceil()` function, exact syntax |
| 0.25yr Threshold | Not shown | `min_stock = math.ceil(91 * purchased / 365)` | Missing from decision tree |
| Lead Time Buffer | "35 days" (mentioned) | `target = math.ceil(181 * purchased / 365)` | Shows 146 + 35 = 181 calculation |

## Why This Matters

**For Implementation:**
- Users implementing the algorithm need to know: `math.ceil()` vs `round()` vs `floor()`
- Order of operations matters: `stock / (purchased / 365)` vs `stock * 365 / purchased` (mathematically same, but clearer)
- Variable naming conventions help consistency

**For Validation:**
- When checking calculations, knowing the exact Python code eliminates ambiguity
- "⌈⌉" ceiling brackets are clear conceptually, but `math.ceil()` is what actually runs

## Current State

| Component | Has Python Code? | Has Conceptual Formulas? |
|-----------|------------------|--------------------------|
| **Decision Tree** | ❌ NO | ✅ YES (using ⌈⌉ notation) |
| **REORDER_RULES.md** | ✅ YES | ✅ YES (both versions) |
| **Calculator Code** | ✅ YES | N/A (it's the code itself) |
| **Quick Reference Card** | ❌ NO | ✅ YES (simplified) |

## Proposed Addition

Add a **"Formulas Reference"** section to the decision tree with both versions:

```markdown
## Formulas Reference

### Years in Stock
**Conceptual:** Years = Stock ÷ (Purchased ÷ 365)
**Python:** `years_in_stock = stock * 365 / purchased`

### Minimum Stock for 0.25 Years (Order Decision Threshold)
**Conceptual:** Min = ⌈(91 × Purchased) ÷ 365⌉
**Python:** `min_stock_025 = math.ceil(91 * purchased / 365)`

### Minimum Stock for 0.40 Years (Order Target)
**Conceptual:** Min = ⌈(146 × Purchased) ÷ 365⌉
**Python:** `min_stock_040 = math.ceil(146 * purchased / 365)`

### Target Stock with Lead Time Buffer
**Conceptual:** Target = ⌈(181 × Purchased) ÷ 365⌉
**Python:** `target_stock = math.ceil(181 * purchased / 365)  # 146 + 35 days`
```

## Your Decision Needed

**Should the decision tree include implementation-ready Python code snippets in addition to the conceptual formulas currently shown?**

**Additional Questions:**
- Should this be a dedicated section or inline with the algorithm steps?
- Do you want both conceptual AND Python, or just Python?
- Should we include alternative forms (e.g., `stock / (purchased / 365)` vs `stock * 365 / purchased`)?
- Include import statements (e.g., `import math`) for completeness?""",
                'field_name': 'formulas_code_snippets',
                'suggested_answer': 'Yes - add dedicated "Formulas Reference" section with both conceptual notation and Python code. Include math.ceil import.',
                'product_id': 0,
                'product_name': 'SYSTEM: Decision Tree Formulas',
                'pre_answer': None
            },

            # Question 5: Validation Output Format (SKIPPED per user request)
            # Not included - user said "don't do anything yet"

            # Question 6: Validated Examples (ANSWERED: No)
            {
                'priority': 'MEDIUM',
                'question_text': """# QUESTION 6: Validated Examples Expansion

## What We Found

**REORDER_RULES.md** states:

```
## VALIDATED EXAMPLES (December 15, 2025)

Products 17-25 were validated with correct logic:

| Product | Name | Script | Correct | Notes |
|---------|------|--------|---------|-------|
| 17 | Deep Royal Blue Transparent 3mm | 8 | 5 | Cascade savings |
| 18 | Dark Forest Green Opalescent 3mm | 5 | 3 | Half cut + cascade |
| ... (9 products total) ...

**Products 1-16 need re-validation** with this complete logic.
```

## Current Coverage

| Product Range | Validation Status | Count |
|---------------|-------------------|-------|
| Products 17-25 | ✅ Validated (Dec 15, 2025) | 9 products |
| Products 1-16 | ❌ Need re-validation | 16 products |
| **Total** | **Partial coverage** | **25 products** |

## Decision Tree Examples

The decision tree currently includes **3 complete examples**:
1. Example 1: 3mm Product - Cascade Eliminates Order (Black Opal)
2. Example 2: 3mm Product - Half Deficit Requires Saving (Teal Green)
3. Example 3: 2mm Product - Different Logic (White Opal)

## Options for Expansion

### Option A: Re-validate All 25 Products
- Run products 1-16 through current decision tree
- Document all 25 examples in decision tree
- Pros: Complete validation coverage
- Cons: Makes decision tree very long (1,100+ lines → 2,000+ lines?)

### Option B: Keep Current 3 Examples, Reference External Validation
- Decision tree keeps 3 representative examples (3mm cascade, 3mm Half deficit, 2mm)
- Add note: "For additional validated examples, see REORDER_RULES.md products 17-25"
- Pros: Decision tree stays focused on algorithm explanation
- Cons: Examples scattered across documents

### Option C: Separate Validation Document
- Create new document: "Bullseye_Reorder_Validation_Examples.md"
- Include all 25 products with full BEFORE/AFTER spreadsheets
- Decision tree references this document
- Pros: Complete validation in dedicated space, decision tree stays clean
- Cons: Another document to maintain

## Your Decision Needed

**Should we re-validate products 1-16 and add all 25 validation examples to the decision tree?**

**Answer: NO** (per your instruction)

**Follow-up:** Should we at least add a reference to REORDER_RULES.md where the validated examples exist?""",
                'field_name': 'validated_examples_expansion',
                'suggested_answer': 'No - keep current 3 examples in decision tree, add reference note to REORDER_RULES.md for additional validated examples (products 17-25)',
                'product_id': 0,
                'product_name': 'SYSTEM: Validation Examples',
                'pre_answer': 'No'
            },

            # Question 7: PDF Export Requirements (ANSWERED: No)
            {
                'priority': 'MEDIUM',
                'question_text': """# QUESTION 7: PDF Export Requirements in Decision Tree

## What We Found

**REORDER_RULES.md** specifies PDF export requirements:

```markdown
## PDF EXPORT REQUIREMENTS

The PDF export should include for each flagged product:
1. BEFORE spreadsheet (current inventory state)
2. CASCADE FROM INVENTORY analysis
3. DECISION (order needed or not, with reasoning)
4. ORDER details (how many sheets, cut vs save)
5. CASCADE from new order details
6. AFTER spreadsheet (final projected state)
7. VERIFICATION (all above 0.4 years confirmation)
```

Also specifies validation format:

```
PRODUCT [N]: [Name] [Thickness]
================================================================================

BEFORE:
Size         In Stock    Years  Purchased   Est_Annual     Target    Deficit
--------------------------------------------------------------------------------
Half               XX     X.XX         XX           XX         XX         XX
...

STEP 1: CASCADE FROM INVENTORY
  - [describe what can be cascade cut]
...
```

## Current Coverage

| Document | Has Output Format Specs? | Details |
|----------|-------------------------|---------|
| **REORDER_RULES.md** | ✅ YES | PDF export requirements + validation format |
| **Decision Tree** | ❌ NO | Focuses on calculation logic only |
| **Calculator Code** | ❌ NO | Returns JSON, no formatting |

## The Question

The **Decision Tree** is focused on **calculation logic** (how to decide what to order).

The **PDF Export Requirements** are about **output format** (how to present the results).

## Options

### Option A: Include in Decision Tree
- Add "Output Format Requirements" section to decision tree
- Shows exact column headers, table structure, formatting rules
- Pros: Everything in one place
- Cons: Mixes calculation logic with presentation layer

### Option B: Keep Separate
- Decision tree stays focused on algorithm
- Output format documented in REORDER_RULES.md
- Create new "Reorder System Architecture" document showing full workflow (input → calculation → output)
- Pros: Separation of concerns, cleaner decision tree
- Cons: Information across multiple documents

### Option C: Add Reference Only
- Decision tree includes a brief "Output Format" section
- States: "For detailed PDF export specifications, see REORDER_RULES.md"
- Links to external format documentation
- Pros: User knows where to find format specs, tree stays focused
- Cons: Still requires checking another document

## Your Decision Needed

**Should the decision tree include output format specifications (PDF structure, column headers, BEFORE/AFTER spreadsheet layouts)? Or keep output format separate from calculation logic?**

**Answer: NO** (per your instruction)

**Follow-up:** Should we at least add a reference link to where output format is documented?""",
                'field_name': 'pdf_export_in_decision_tree',
                'suggested_answer': 'No - keep separate. Add reference note in decision tree: "For PDF export format specifications, see REORDER_RULES.md"',
                'product_id': 0,
                'product_name': 'SYSTEM: Output Format Specification',
                'pre_answer': 'No'
            },

            # Question 8: Calculator Full Algorithm (MOST CRITICAL)
            {
                'priority': 'HIGH',
                'question_text': """# QUESTION 8: Calculator Full Algorithm Implementation (MOST CRITICAL)

## Summary of Question 3 (Calculator Architecture)

This is the **MOST CRITICAL DECISION** because it determines the entire implementation path.

## The Two Approaches - Detailed Comparison

### OPTION A: Keep Simplified Calculator (Current)

**Architecture:**
```
User uploads CSV → Calculator processes EACH ROW independently
                  ↓
For each product:
  - Calculate years_in_stock
  - Check if < 0.25yr (order needed?)
  - Calculate reorder_quantity to reach 0.40yr
  - Flag cascade opportunities as QUESTIONS
  - Return: {reorder_quantity, questions[]}
                  ↓
User reviews questions in dashboard
User performs manual cascade calculation in Excel
User validates BEFORE/AFTER in spreadsheet
User generates final order
```

**Code Complexity:** ~200 lines (current)

**User Workflow:**
1. Upload CSV
2. Review questions
3. **Manual Excel validation** (cascade calculation, family grouping)
4. Generate order

**Pros:**
- ✅ Simple code (easier to maintain, debug, modify)
- ✅ Manual review ensures quality control
- ✅ User can override AI decisions easily
- ✅ Faster to implement (already done!)
- ✅ No complex Parent ID grouping needed
- ✅ Works with current CSV upload workflow
- ✅ Questions dashboard already built
- ✅ Flexible - user can apply business judgment

**Cons:**
- ❌ Requires manual Excel/PDF validation step
- ❌ Not fully automated
- ❌ User must understand cascade logic deeply
- ❌ Inconsistent results if different users interpret differently
- ❌ Cannot verify "all sizes ≥ 0.40yr" automatically across product family
- ❌ Time-consuming for users (manual spreadsheet work)
- ❌ Error-prone (user might miss cascade opportunities)

---

### OPTION B: Implement Full 5-Step Algorithm

**Architecture:**
```
User uploads CSV → Pre-processor groups products by Parent ID
                  ↓
For each product FAMILY (Half/10×10/5×10/5×5):
  STEP 1: CASCADE FROM INVENTORY
    - Check Half excess (3mm: 2 Half = 1 Full equiv)
    - Check 10×10 excess → cascade to 5×10 or 5×5
    - Check 5×10 excess → cascade to 5×5
    - Update all inventories after cascade

  STEP 2: CHECK IF ORDER NEEDED
    - Calculate years_in_stock for ALL sizes in family
    - If ANY size < 0.25yr → ORDER NEEDED
    - Else → NO ORDER

  STEP 3: CALCULATE MINIMUM ORDER
    - 3mm: Check Half deficit → save Fulls as Half
    - 3mm: Calculate Full_Cut for 10×10 deficit
    - 2mm: Save Half uncut, calculate Half_Cut
    - Account for cutting yields (Full → 6×10×10 + 2×5×10)

  STEP 4: CASCADE FROM NEW ORDER
    - Track byproducts (5×10 from Full cuts)
    - Cascade 10×10 surplus → 5×10 or 5×5
    - Cascade 5×10 surplus → 5×5

  STEP 5: VERIFY ALL SIZES
    - Calculate final years_in_stock for ALL sizes
    - Verify ALL ≥ 0.40yr (including Half!)
    - If any fail → recalculate (increase order)
    - Generate BEFORE/AFTER spreadsheets
                  ↓
Output: {
  order: "8 Full Sheets (1 save as Half + 7 cut)",
  before_table: [...],
  after_table: [...],
  cascade_details: [...],
  verification: "ALL SIZES ≥ 0.40yr ✓"
}
```

**Code Complexity:** ~800-1200 lines (estimated)

**Database Changes Needed:**
- Add `products_parent_id` to link product families
- Store product thickness (3mm vs 2mm)
- Store product size (Half, 10×10, 5×10, 5×5)

**User Workflow:**
1. Upload CSV
2. **Automatic calculation** (all 5 steps)
3. Review results (BEFORE/AFTER tables)
4. Generate order

**Pros:**
- ✅ Fully automated calculation
- ✅ Consistent results every time
- ✅ Implements complete decision tree logic
- ✅ Validates across all sizes in family
- ✅ Generates audit trail (BEFORE/AFTER tables)
- ✅ No manual interpretation needed
- ✅ Catches cascade opportunities automatically
- ✅ Verifies "all sizes ≥ 0.40yr" requirement
- ✅ Saves user time (no manual spreadsheet work)
- ✅ Eliminates human error in cascade calculations

**Cons:**
- ❌ Complex code (product family grouping logic)
- ❌ Harder to audit/debug
- ❌ Users can't easily override decisions
- ❌ Requires significant development time (~40-60 hours?)
- ❌ May need UI changes to display BEFORE/AFTER tables
- ❌ Needs product family data (Parent ID linking)
- ❌ More brittle - edge cases harder to handle
- ❌ If algorithm is wrong, affects ALL products

## Development Time Estimates

| Task | Option A | Option B |
|------|----------|----------|
| Core calculator logic | ✅ Done | ~16 hours |
| Product family grouping | N/A | ~8 hours |
| Cascade calculation (Step 1) | N/A | ~8 hours |
| Threshold checking (Step 2) | ✅ Done | ~4 hours |
| Order calculation (Step 3) | ✅ Basic | ~12 hours |
| Cascade from order (Step 4) | N/A | ~8 hours |
| Verification (Step 5) | N/A | ~4 hours |
| BEFORE/AFTER tables | N/A | ~6 hours |
| UI updates | ✅ Done | ~8 hours |
| Testing & debugging | ~4 hours | ~20 hours |
| **TOTAL** | **~4 hours** | **~94 hours** |

## Critical Questions for Option B

If you choose Option B, we need to know:

1. **Product Family Support:**
   - Can you provide Parent ID linking in the CSV? (Half/10×10/5×10/5×5 must have same Parent ID)
   - Or should the calculator detect families by product name parsing?

2. **Output Format:**
   - Display BEFORE/AFTER tables in the web UI? Or generate downloadable Excel?
   - Should each product family get a separate report page?

3. **Override Capability:**
   - Can users override the automatic calculations? Or is it read-only?
   - If override, do we store manual adjustments in database?

4. **Edge Case Handling:**
   - What if a product family is incomplete (has Half and 10×10 but missing 5×10)?
   - What if Purchased=0 for some sizes but not others in the family?

## Recommendation

**For immediate deployment:** Option A (Keep Simplified)
- ✅ Already working
- ✅ Lower risk
- ✅ Users maintain control via manual validation
- ✅ Can upgrade to Option B later if needed

**For long-term automation:** Option B (Full Algorithm)
- ✅ Eliminates manual work
- ✅ Ensures consistency
- ✅ Implements complete decision tree
- ⚠️ Requires ~3-4 weeks development time
- ⚠️ Higher complexity = higher risk

## Your Decision Needed

**Which approach for calculator?**

**A) Keep simplified** - Flag cascade opportunities, manual spreadsheet validation, simpler code

**B) Implement full 5-step algorithm** - Product family grouping (Parent ID), automatic cascade calculation, BEFORE/AFTER spreadsheets, fully automated

**Also answer:**
1. Do you have Parent ID data available in the CSV to link product families?
2. Is ~94 hours of development time acceptable for Option B?
3. Who will be using this calculator? (Technical users or warehouse staff?)
4. Is manual validation acceptable long-term? Or must it be automated?""",
                'field_name': 'calculator_architecture_decision',
                'suggested_answer': 'Option A - Keep simplified with manual validation for quality control. Can upgrade to Option B later if automation becomes critical.',
                'product_id': 0,
                'product_name': 'SYSTEM: Calculator Full Algorithm (MOST CRITICAL)',
                'pre_answer': None
            }
        ]

        # Insert questions
        for idx, q in enumerate(questions, 1):
            print(f"[QUESTION {idx}] Inserting: {q['product_name']}")

            db.execute(text("""
                INSERT INTO reorder_questions (session_id, product_id, product_name, priority, question_text, field_name, suggested_answer)
                VALUES (:session_id, :product_id, :product_name, :priority, :question_text, :field_name, :suggested_answer)
            """), {
                'session_id': session_id,
                'product_id': q['product_id'],
                'product_name': q['product_name'],
                'priority': q['priority'],
                'question_text': q['question_text'],
                'field_name': q['field_name'],
                'suggested_answer': q['suggested_answer']
            })
            db.commit()

            # If pre-answered, update with answer
            if q['pre_answer'] is not None:
                result = db.execute(text("""
                    SELECT question_id FROM reorder_questions
                    WHERE session_id = :session_id AND field_name = :field_name
                """), {
                    'session_id': session_id,
                    'field_name': q['field_name']
                }).fetchone()

                if result:
                    question_id = result[0]
                    print(f"          >> Pre-answered: {q['pre_answer']}")
                    db.execute(text("""
                        UPDATE reorder_questions
                        SET client_answer = :answer, answered_at = :answered_at
                        WHERE question_id = :question_id
                    """), {
                        'question_id': question_id,
                        'answer': q['pre_answer'],
                        'answered_at': datetime.utcnow()
                    })
                    db.commit()

        print(f"\n[SUCCESS] Inserted {len(questions)} detailed architectural questions")
        print(f"[SESSION] {session_id}")
        print(f"[VIEW] https://gpt-mcp.onrender.com/reports/reorder-calculator/questions")
        print(f"\n[BREAKDOWN]")
        print(f"  - Unanswered (need client input): 5 questions")
        print(f"    1. Holly Berry Red seasonal rule")
        print(f"    2. System boundary clarity")
        print(f"    3. Calculator implementation scope")
        print(f"    4. Formulas reference section")
        print(f"    8. Calculator full algorithm (MOST CRITICAL)")
        print(f"  - Pre-answered 'No': 2 questions")
        print(f"    6. Validated examples expansion")
        print(f"    7. PDF export in decision tree")
        print(f"\n[NOTE] Questions include full context, tables, and comprehensive analysis")
        print(f"[NOTE] UI may need updates to display markdown tables properly")

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == '__main__':
    insert_detailed_questions()
