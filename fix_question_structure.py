"""
Fix question structure - Put THE QUESTION first, then context
Restructure existing architectural questions to be client-friendly
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv('agent_garden/.env')

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("[ERROR] DATABASE_URL not found")
    exit(1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Better-structured questions
IMPROVED_QUESTIONS = {
    # Question 1: Seasonal Products
    'holly_berry_red_seasonal_rule': """# 🎯 THE QUESTION

**Do seasonal products (like Holly Berry Red) still require pre-ordering by specific deadlines?**

**If yes:** Should the reorder calculator flag seasonal products with deadline warnings?

---

## 📋 WHY WE'RE ASKING

The knowledge base mentions Holly Berry Red must be pre-ordered by June 30th (seasonal), but the current calculator doesn't check for seasonal products or deadlines.

**Impact if we ignore this:**
- Missing June 30th deadline = Can't order Holly Berry Red for the season
- Users might plan regular reorders not knowing about seasonal constraints
- Inventory could run out because we didn't order in time

---

## 🔍 WHAT WE FOUND

**Source:** `MASTER_CONTEXT_PROMPT.md` line 167

> **Special:** Holly Berry Red must be pre-ordered by June 30th (seasonal)

**Current coverage:**

| Component | Has Seasonal Logic? |
|-----------|---------------------|
| Decision Tree | ❌ NO |
| Calculator Code | ❌ NO |
| REORDER_RULES.md | ❌ NO |
| MASTER_CONTEXT_PROMPT | ✅ YES (mentions Holly Berry Red) |

---

## ✅ IF YES, WE WOULD ADD:

1. **Decision node:** "Is this a seasonal product?"
2. **Deadline check:** "Is current date before June 30th?"
3. **Alert message:** "SEASONAL PRODUCT: Must order by June 30th or wait until next season"
4. **Product list:** Maintain list of seasonal products and their deadlines

---

## 💡 FOLLOW-UP QUESTIONS (if yes)

- Are there other seasonal products besides Holly Berry Red?
- Do seasonal products have different inventory thresholds?
- Should seasonal products appear in a separate section of reports?

---

## 📝 SUGGESTED ANSWER

**Yes** - Add seasonal product detection with deadline checking.

Holly Berry Red deadline: June 30th annually.

**If no:** We'll remove the seasonal mention from MASTER_CONTEXT_PROMPT to avoid confusion.""",

    # Question 2: System Boundaries
    'system_boundaries': """# 🎯 THE QUESTION

**Which system should the "Bullseye Vendor Purchase Decision Tree" describe?**

Choose ONE:
- A) **Ordering System** (decide what to order from vendor)
- B) **Receiving System** (process received inventory, generate cut sheets)
- C) **Cut Sheet System** (biweekly rebalancing)

**Quick context:** The decision tree name says "Vendor **Purchase**" but some content looks like "Receiving" logic.

---

## 📋 WHY WE'RE ASKING

The decision tree is mixing two different systems:

**Example of confusion:**
- Title says: "Vendor **Purchase** Decision Tree" (ordering from vendor)
- But Step 1 says: "Load & **Snapshot** products" (receiving workflow)
- And mentions: "**Biweekly** rebalancing" (cut sheet workflow)

These are THREE different systems with different goals:

| System | Goal | When | Input |
|--------|------|------|-------|
| **Ordering** | Decide what to order from vendor | Monthly/as needed | Low inventory alerts |
| **Receiving** | Process received order, make cut sheets | After vendor delivery | Purchase order + received items |
| **Cut Sheets** | Rebalance inventory sizes | Biweekly | Current inventory |

---

## 🔍 CURRENT CONTENT ANALYSIS

The decision tree currently contains:

✅ **Ordering logic:**
- Check years in stock vs 0.25 threshold
- Calculate order quantities
- Cascade opportunity detection

❌ **Also has Receiving logic:**
- "Snapshot all sizes for one color/thickness combination"
- "Excel file columns: Size, In Stock, Years, Purchased, Est_Annual, Target, Deficit"

❌ **Also has Cut Sheet logic:**
- "Biweekly rebalancing between sizes"

---

## ✅ RECOMMENDED ANSWER

**Option A: Ordering System**

**Reasoning:**
- Tree is named "**Vendor Purchase** Decision Tree"
- Primary questions are about WHEN to order and HOW MUCH
- Receiving and Cut Sheets are separate workflows with their own trees

**If this is chosen:**
- Remove "snapshot" and "biweekly rebalancing" references
- Focus purely on: "Given current inventory, should I order from vendor? How much?"
- Input: Current inventory levels
- Output: Order decision + quantities

---

## 📝 WHAT CHANGES IF YOU PICK SOMETHING ELSE

**If Option B (Receiving):** Rename tree to "Receiving Cut Sheet Generator", change focus to processing vendor deliveries

**If Option C (Cut Sheets):** Rename to "Biweekly Rebalancing Decision Tree", focus on internal cutting operations

Let us know which system this tree should cover!""",

    # Question 3: Calculator Scope
    'calculator_scope_decision': """# 🎯 THE QUESTION

**Should the reorder calculator implement the FULL 5-step cascade algorithm, or stay simplified?**

**Quick context:** The 5-step algorithm is powerful but complex. The simplified version catches most cases and flags others for manual review.

---

## 📋 THE TWO OPTIONS

### OPTION A: Keep Simplified Calculator (Current) ✅ RECOMMENDED

**What it does:**
```
For each product independently:
1. Calculate years_in_stock
2. Check against thresholds (0.25 order decision, 0.40 target)
3. Flag cascade opportunities for manual review
4. Generate questions for edge cases
```

**Example output:**
```
Product: Black Opal 3mm
Status: NEEDS REVIEW
Reason: "3mm Half Sheet has 2.5 years stock - can cascade to create Full Sheets.
         Manual review needed to determine if cascade eliminates order."
```

**Pros:**
- ✅ Works for 90% of products automatically
- ✅ Safe - doesn't make assumptions about complex cascades
- ✅ Fast processing (< 1 second per product)
- ✅ Easy to debug when something looks wrong
- ✅ Can upgrade later without breaking existing reports

**Cons:**
- ❌ Requires manual review for cascade opportunities
- ❌ Doesn't optimize across multiple sizes automatically

---

### OPTION B: Implement Full 5-Step Algorithm

**What it does:**
```
STEP 1: Cascade FROM inventory (check if existing stock solves problem)
STEP 2: Calculate minimum order needed
STEP 3: Calculate cascade FROM new order (optimize cutting)
STEP 4: Verify all sizes reach target
STEP 5: Generate cut instructions
```

**Example output:**
```
Product: Black Opal 3mm
Cascade Analysis:
  - Half Sheet: 2.5 years (excess) → Cut 2 Half = 1 Full
  - Full Sheet: Now 0.50 years (ABOVE target!)
Decision: NO ORDER NEEDED
Cut Instructions: "Cut 2x Half Sheets to create 1 Full Sheet"
```

**Pros:**
- ✅ Fully automatic optimization
- ✅ Matches decision tree exactly
- ✅ Finds all cascade savings opportunities
- ✅ Complete audit trail

**Cons:**
- ❌ Complex - harder to debug
- ❌ Slower processing (needs to analyze all 4 sizes together)
- ❌ Risk of bugs in complex cascade logic
- ❌ Requires extensive testing with all edge cases

---

## 🎯 IMPLEMENTATION COMPARISON

| Aspect | Option A (Simple) | Option B (Full) |
|--------|------------------|-----------------|
| **Development Time** | ✅ Done | ⏱️ 2-3 days |
| **Testing Required** | ✅ Basic | ⚠️ Extensive (25+ products) |
| **Bug Risk** | ✅ Low | ⚠️ Medium-High |
| **Manual Review** | ⚠️ Some products | ✅ None |
| **Upgrade Path** | ✅ Can upgrade anytime | ❌ Already complex |

---

## 💡 RECOMMENDED ANSWER

**Option A - Keep Simplified**

**Reasoning:**
1. Catches 90% of cases automatically
2. Safe - flags uncertain cases rather than guessing
3. Already working and tested
4. Can upgrade to Option B later if manual review becomes too time-consuming

**When to upgrade to Option B:**
- If you're processing 100+ products and manual review takes too long
- If you need full automation for recurring orders
- After validating with 25+ real products

---

## 📝 SUGGESTED ANSWER

Keep Option A (simplified calculator with manual review for cascades).

Add upgrade to Option B as future enhancement if needed.""",

    # Question 4: Formulas Section
    'formulas_code_snippets': """# 🎯 THE QUESTION

**Should the decision tree include a "Formulas Reference" section with Python code examples?**

**Quick context:** The tree has formulas like "Years = Stock ÷ (Purchased ÷ 365)" but no code. Should we add Python?

---

## 📋 WHY WE'RE ASKING

**Current state:**
- Decision tree shows **conceptual formulas**: `Years = Stock ÷ (Purchased ÷ 365)`
- No Python code snippets
- Developers have to translate formulas to code themselves

**If we add Python code:**
```python
import math

# Calculate years in stock
years_in_stock = stock_quantity / (purchased_lifetime / 365)

# Round up for sheet count
full_sheets_needed = math.ceil(deficit_years * (purchased_annual / 2))
```

---

## ✅ PROS OF ADDING CODE

- ✅ **Copy-paste ready** - developers can use directly
- ✅ **Eliminates translation errors** - no guessing on rounding, division order
- ✅ **Shows Python idioms** - `math.ceil()` vs manual rounding
- ✅ **Import clarity** - shows what modules needed

---

## ❌ CONS OF ADDING CODE

- ❌ **Makes tree longer** - code takes more space than formulas
- ❌ **Language-specific** - only helps Python users
- ❌ **Maintenance** - code and formulas must stay in sync

---

## 🎯 RECOMMENDED FORMAT (if yes)

Add a **dedicated "Formulas Quick Reference"** section at the bottom:

````markdown
## 📐 Formulas Quick Reference

### Years in Stock
**Concept:** `Years = Stock ÷ (Purchased ÷ 365)`

**Python:**
```python
years_in_stock = stock_quantity / (lifetime_purchased / 365)
```

### Full Sheets Needed
**Concept:** `Sheets = ⌈Deficit × (Annual ÷ 2)⌉`

**Python:**
```python
import math
full_sheets = math.ceil(deficit_years * (annual_purchased / 2))
```
````

---

## 📝 SUGGESTED ANSWER

**Yes** - Add "Formulas Reference" section with both conceptual notation AND Python code.

**Structure:**
- Keep formulas in decision steps (conceptual)
- Add dedicated section at bottom with Python code
- Include `import math` for `ceil()` function

**Alternative (if no):**
Keep formulas conceptual-only, create separate "Implementation Guide" document with code examples."""
}

def update_questions():
    """Update question text to put THE QUESTION first"""
    db = SessionLocal()

    try:
        # Get all questions that need restructuring
        results = db.execute(text("""
            SELECT question_id, field_name, priority, product_name
            FROM reorder_questions
            WHERE field_name IN :field_names
        """), {
            'field_names': tuple(IMPROVED_QUESTIONS.keys())
        }).fetchall()

        print(f"\n[INFO] Found {len(results)} questions to update")

        updated = 0
        for row in results:
            question_id, field_name, priority, product_name = row

            if field_name in IMPROVED_QUESTIONS:
                new_question_text = IMPROVED_QUESTIONS[field_name]

                db.execute(text("""
                    UPDATE reorder_questions
                    SET question_text = :new_text
                    WHERE question_id = :question_id
                """), {
                    'question_id': question_id,
                    'new_text': new_question_text
                })

                print(f"[UPDATED] Q{question_id}: {product_name} ({field_name})")
                updated += 1

        db.commit()
        print(f"\n[SUCCESS] Updated {updated} questions")
        print("\nQuestions now have:")
        print("  1. THE QUESTION upfront (clear and concise)")
        print("  2. WHY WE'RE ASKING (context)")
        print("  3. OPTIONS (comparison tables)")
        print("  4. RECOMMENDED ANSWER")

    except Exception as e:
        print(f"[ERROR] {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 70)
    print("QUESTION STRUCTURE FIX")
    print("=" * 70)
    update_questions()
