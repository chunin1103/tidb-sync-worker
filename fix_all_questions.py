"""
Fix ALL architectural questions - Put THE QUESTION first, then context
Complete restructure for client-friendly format
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

# ALL improved questions with better structure
IMPROVED_QUESTIONS = {
    # Question 1: Seasonal Products
    'holly_berry_red_seasonal_rule': """# THE QUESTION

**Do seasonal products (like Holly Berry Red) still require pre-ordering by specific deadlines?**

If YES: Should the calculator flag them with deadline warnings?

---

## WHY WE'RE ASKING

The knowledge base mentions "Holly Berry Red must be pre-ordered by June 30th (seasonal)" but the calculator doesn't check for this.

**Impact if ignored:**
- Missing deadline = Can't order Holly Berry Red for the season
- Users might plan regular reorders not knowing about seasonal constraints

---

## WHAT WE FOUND

Source: `MASTER_CONTEXT_PROMPT.md` line 167

| Component | Has Seasonal Logic? |
|-----------|---------------------|
| Decision Tree | NO |
| Calculator Code | NO |
| Knowledge Base | YES (Holly Berry Red mentioned) |

---

## IF YES, WE WOULD ADD

1. Decision node: "Is this a seasonal product?"
2. Deadline check: "Is current date before June 30th?"
3. Alert: "SEASONAL: Must order by June 30th or wait until next season"
4. Maintain list of seasonal products + deadlines

---

## FOLLOW-UP QUESTIONS (if yes)

- Other seasonal products besides Holly Berry Red?
- Different inventory thresholds for seasonal items?
- Separate report section for seasonal products?

---

## RECOMMENDED ANSWER

**YES** - Add seasonal detection with June 30th deadline for Holly Berry Red.

**IF NO:** Remove seasonal mention from MASTER_CONTEXT_PROMPT to avoid confusion.""",

    # Question 2: System Boundaries (inventory_translation_rule_scope)
    'inventory_translation_rule_scope': """# THE QUESTION

**Which system should the "Bullseye Vendor Purchase Decision Tree" describe?**

Choose ONE:
- **A) Ordering System** (decide what to order from vendor)
- **B) Receiving System** (process received inventory, cut sheets)
- **C) Cut Sheet System** (biweekly rebalancing)

---

## WHY WE'RE ASKING

The decision tree is mixing different systems:

**Example confusion:**
- Title: "Vendor **Purchase** Decision Tree" ← Sounds like ordering
- Step 1: "Load & **Snapshot**" ← Sounds like receiving
- Mentions: "**Biweekly** rebalancing" ← Sounds like cut sheets

---

## THE THREE SYSTEMS

| System | Goal | When | Input |
|--------|------|------|-------|
| **Ordering** | Decide vendor order | Monthly | Low inventory |
| **Receiving** | Process delivery, cut sheets | After delivery | Purchase order |
| **Cut Sheets** | Rebalance sizes | Biweekly | Current inventory |

---

## RECOMMENDED ANSWER

**Option A: Ordering System**

**Why:**
- Named "Vendor **Purchase** Decision Tree"
- Questions are: WHEN to order? HOW MUCH?
- Receiving/Cut Sheets are separate workflows

**If chosen:** Remove "snapshot" and "biweekly" references. Focus on vendor ordering logic only.

**Alternative:**
- Option B: Rename to "Receiving Cut Sheet Generator"
- Option C: Rename to "Biweekly Rebalancing Tree"

Let us know which system this tree should cover!""",

    # Question 3 Calculator Implementation (calculator_implementation_scope)
    'calculator_implementation_scope': """# THE QUESTION

**Should the calculator implement the FULL 5-step cascade algorithm or stay simplified?**

---

## QUICK SUMMARY

| Approach | Speed | Manual Review | Complexity |
|----------|-------|---------------|------------|
| **A) Simplified** (current) | Fast | Some needed | Low |
| **B) Full Algorithm** | Slower | None | High |

---

## OPTION A: Simplified Calculator (RECOMMENDED)

**What it does:**
```
For each product:
1. Calculate years_in_stock
2. Check thresholds (0.25 / 0.40)
3. Flag cascade opportunities for manual review
```

**Example:**
```
Product: Black Opal 3mm
Status: NEEDS REVIEW
Reason: "Half Sheet has 2.5 years - can cascade to Full.
         Manual review needed."
```

**PROS:**
- Works for 90% of products automatically
- Safe - doesn't make assumptions
- Fast (< 1 second per product)
- Easy to debug
- Can upgrade later

**CONS:**
- Requires manual review for cascades

---

## OPTION B: Full 5-Step Algorithm

**What it does:**
```
STEP 1: Cascade FROM inventory
STEP 2: Calculate minimum order
STEP 3: Cascade FROM new order
STEP 4: Verify all sizes
STEP 5: Generate cut instructions
```

**Example:**
```
Product: Black Opal 3mm
Cascade: 2 Half → 1 Full
Result: Full now 0.50 years (above target)
Decision: NO ORDER NEEDED
```

**PROS:**
- Fully automatic
- Matches decision tree exactly
- Finds all cascade savings

**CONS:**
- Complex - harder to debug
- Slower processing
- Higher bug risk
- Needs extensive testing

---

## COMPARISON TABLE

| Aspect | Simple | Full |
|--------|--------|------|
| Development Time | Done | 2-3 days |
| Testing | Basic | Extensive (25+ products) |
| Bug Risk | Low | Medium-High |
| Manual Review | Some | None |
| Upgrade Path | Easy | Already complex |

---

## RECOMMENDED ANSWER

**Option A - Keep Simplified**

**Why:**
1. Catches 90% automatically
2. Safe - flags uncertain cases
3. Already working
4. Can upgrade later if needed

**When to upgrade to B:**
- Processing 100+ products regularly
- Manual review too time-consuming
- After validating with 25+ real products""",

    # Question 4: Calculator Architecture (calculator_architecture_decision)
    'calculator_architecture_decision': """# THE QUESTION

**Should the calculator process products INDEPENDENTLY or TOGETHER as a group?**

Quick context: Independent = fast but might miss optimizations. Together = slower but can optimize across all sizes.

---

## OPTION A: Process Independently (Current)

**How it works:**
```
FOR EACH product row:
  Calculate years_in_stock
  Check thresholds
  Flag if needs attention
  → Move to next row
```

**PROS:**
- Simple and fast
- Easy to debug
- Works for most products
- Can run in parallel

**CONS:**
- Doesn't see cascade opportunities between products
- Can't optimize "Black Opal 3mm Half + Full" together

---

## OPTION B: Process Together

**How it works:**
```
Group by color + thickness:
  Get all sizes (Half, 10x10, 5x10, 5x5)
  Analyze as ONE decision
  Calculate cascade opportunities
  Optimize across all sizes
```

**PROS:**
- Sees full picture
- Can cascade between sizes
- Matches decision tree logic

**CONS:**
- More complex code
- Slower processing
- Harder to debug

---

## RECOMMENDATION

**Option A - Independent Processing**

Use with simplified calculator (flags opportunities for manual review).

**Option B** would be needed only if you implement the full 5-step algorithm.""",

    # Question 5: Formulas Section
    'formulas_code_snippets': """# THE QUESTION

**Should the decision tree include Python code examples for formulas?**

Current: Formulas shown as `Years = Stock / (Purchased / 365)`
Proposed: Add Python code snippets

---

## EXAMPLE OF WHAT WE'D ADD

**Current (conceptual):**
```
Years = Stock / (Purchased / 365)
```

**Proposed (with Python):**
```python
# Calculate years in stock
years_in_stock = stock_quantity / (lifetime_purchased / 365)

# Round up for sheet count
import math
full_sheets = math.ceil(deficit_years * (annual_purchased / 2))
```

---

## PROS OF ADDING CODE

- Copy-paste ready for developers
- Eliminates translation errors
- Shows Python idioms (math.ceil vs manual rounding)
- Clear what imports needed

---

## CONS

- Makes tree longer
- Language-specific (only helps Python users)
- Must keep code and formulas in sync

---

## RECOMMENDED FORMAT

Add dedicated "Formulas Quick Reference" section at bottom:

- Keep formulas in main decision steps (conceptual)
- Add section at end with Python code
- Include all imports

---

## RECOMMENDED ANSWER

**YES** - Add "Formulas Reference" section with Python code.

Include `import math` for `ceil()` function.

**Alternative:** Create separate "Implementation Guide" document.""",

    # Question 6: Validated Examples
    'validated_examples_expansion': """# THE QUESTION

**Should we add all 25 validated product examples to the decision tree?**

Current: Tree has 3 examples
Available: 25 validated products in REORDER_RULES.md

---

## CURRENT STATE

| Product Range | Status | Count |
|---------------|--------|-------|
| Products 17-25 | Validated (Dec 15) | 9 |
| Products 1-16 | Need validation | 16 |
| **In Decision Tree** | **3 examples** | **3** |

**Tree examples:**
1. 3mm cascade eliminates order
2. 3mm Half deficit needs saving
3. 2mm different logic

---

## OPTIONS

### A) Add All 25 Products

- Run 1-16 through tree
- Document all in tree
- **PROS:** Complete coverage
- **CONS:** Tree becomes 2000+ lines

### B) Keep 3 Examples, Add Reference

- Tree keeps current 3
- Add note: "See REORDER_RULES.md for 25 validated examples"
- **PROS:** Tree stays focused
- **CONS:** Examples scattered

### C) Separate Validation Document

- New file: "Bullseye_Validation_Examples.md"
- All 25 products with BEFORE/AFTER
- **PROS:** Complete in dedicated space
- **CONS:** Another doc to maintain

---

## RECOMMENDED ANSWER

**Option B** - Keep current 3 examples, add reference to REORDER_RULES.md

**Why:** Tree stays focused on algorithm. Users know where to find validated examples."""
}

def update_all_questions():
    """Update ALL question types"""
    db = SessionLocal()

    try:
        # Get all unanswered questions
        results = db.execute(text("""
            SELECT question_id, field_name, product_name, priority
            FROM reorder_questions
            WHERE client_answer IS NULL
            AND field_name IN :field_names
        """), {
            'field_names': tuple(IMPROVED_QUESTIONS.keys())
        }).fetchall()

        print(f"\n[INFO] Found {len(results)} questions to update")

        updated = 0
        for row in results:
            question_id, field_name, product_name, priority = row

            if field_name in IMPROVED_QUESTIONS:
                new_text = IMPROVED_QUESTIONS[field_name]

                db.execute(text("""
                    UPDATE reorder_questions
                    SET question_text = :new_text
                    WHERE question_id = :question_id
                """), {
                    'question_id': question_id,
                    'new_text': new_text
                })

                print(f"[UPDATED] Q{question_id} [{priority}] {field_name}")
                updated += 1

        db.commit()
        print(f"\n[SUCCESS] Updated {updated} questions")
        print("\nNew structure:")
        print("  1. THE QUESTION (clear, bold, upfront)")
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
    print("FIX ALL ARCHITECTURAL QUESTIONS")
    print("=" * 70)
    update_all_questions()
