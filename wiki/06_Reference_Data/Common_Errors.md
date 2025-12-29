# Common Errors Reference

**Purpose:** Most frequent mistakes in glass cutting workflows and how to avoid them
**Systems:** All (Oceanside COE96, Bullseye COE90, Color De Verre)
**Last Updated:** 2025-12-21

---

## 🚨 CRITICAL ERROR #1: Forgot Cascade Check (Bullseye 3mm)

**Frequency:** Very Common (THE #1 ERROR!)
**Impact:** High ($$$ wasted on unnecessary vendor orders)
**System:** Bullseye COE90 3mm glass only

### What Happens

**Scenario:**
- Need Full Sheet cuts (e.g., 4× 10×10)
- Full Sheet inventory = 0
- Half Sheet inventory = 18 pieces (well-stocked)

**Wrong Decision:**
```
Full = 0 → Order Full Sheet from vendor ($$$)
```

**Correct Decision:**
```
1. Check cascade: 2 Half = 1 Full (3mm only)
2. Verify: 18 - 2 = 16 Half → 0.65 YIS (> 0.40 ✓)
3. Cascade 2 Half → 1 Full
4. Cut Full → 4× 10×10
5. Save vendor order
```

### Prevention

✅ **ALWAYS** check cascade FIRST before ordering Full sheets
✅ Add "Cascade Check" step to Bullseye workflows
✅ See CLAUDE.md Critical Reminders section
✅ Reference: [Cascade Cutting Logic](./Cascade_Cutting_Logic.md)

---

## 🚨 CRITICAL ERROR #2: Cut Source Below Minimum YIS

**Frequency:** Common
**Impact:** High (creates new inventory problems)
**System:** All systems

### What Happens

**Scenario:**
- Want to cut 6×6 from 24×24
- Current 24×24: 2 sheets (0.08 YIS, already below minimum)
- Need 64 pieces of 6×6 → requires 4 sheets

**Wrong Decision:**
```
Cut all 2 sheets anyway
Result: 24×24 = 0 (except Oceanside can zero 24×24)
```

**Correct Decision:**
```
1. Check source YIS after cut
2. 2 - 4 = negative (can't cut)
3. Don't cut, order 6×6 from vendor instead
```

### Why It's Wrong

- Creates new understocking problem
- Source size drops below minimum threshold
- Next cycle has no source inventory
- **Exception:** Oceanside 24×24 CAN be zeroed out (5.9% of sales)

### Prevention

✅ Validate source YIS AFTER cut ≥ minimum
✅ Use formulas: [Formulas Quick Reference](./Formulas_Quick_Reference.md)
✅ Check minimum thresholds: [Years in Stock Thresholds](../02_Business_Rules/Years_In_Stock_Thresholds.md)

---

## 🚨 ERROR #3: Forgot CEIL Function (Rounding Down)

**Frequency:** Moderate
**Impact:** Medium (produces insufficient pieces)
**System:** All systems

### What Happens

**Scenario:**
- Need 69 pieces of 6×12
- Cut from 24×24 (8 pieces per sheet)
- Calculation: 69 ÷ 8 = 8.625

**Wrong Calculation:**
```
Sheets = 8.625 → Round to 8 sheets
Produces: 8 × 8 = 64 pieces
Shortfall: Need 69, only get 64 (5 pieces short!)
```

**Correct Calculation:**
```
Sheets = CEIL(69 ÷ 8) = CEIL(8.625) = 9 sheets
Produces: 9 × 8 = 72 pieces
Result: 72 ≥ 69 ✓ (3 extra pieces OK)
```

### Why CEIL Matters

- Must produce AT LEAST the pieces needed
- Glass cutting = whole sheets only
- Cannot cut 0.625 of a sheet
- Over-production by a few pieces is acceptable

### Prevention

✅ ALWAYS use CEIL (round up) for sheet calculations
✅ Formula: `Sheets = CEIL(Pieces Needed ÷ Yield)`
✅ Never round down or truncate

---

## 🚨 ERROR #4: Size Detection Failed (Regex Mismatch)

**Frequency:** Moderate
**Impact:** Low-Medium (requires manual review)
**System:** All systems

### What Happens

**Common Patterns That Fail:**
```
"Glass Pack Assortment Mixed Sizes" → No dimensions found
"6 by 6 inches" → Regex expects "6x6" or "6×6"
"Sample size varies" → Ambiguous
"300mm × 300mm" → Metric units (need conversion)
```

**Result:**
- Size = SIZE_UNKNOWN
- Product flagged for manual review
- Delays work order generation

### Prevention

✅ **Standardize product naming:** "Product Name 6×6 3mm COE96"
✅ **Use consistent separators:** "×" or "x" (not "by" or "-")
✅ **Include units:** When using metric, also specify inch equivalent
✅ **Avoid ambiguous terms:** "Mixed", "Assorted", "Varies"
✅ Reference: [Size Detection & Analysis](../03_Decision_Workflows/Size_Detection_And_Analysis.md)

---

## 🚨 ERROR #5: Applied Bullseye Logic to Oceanside (or Vice Versa)

**Frequency:** Moderate
**Impact:** High (wrong cutting strategy)
**System:** Cross-system confusion

### What Happens

**Scenario 1: Used Bullseye thresholds for Oceanside**
```
Wrong: Applied 0.40 YIS target to Oceanside
Correct: Oceanside target = 0.35 YIS (different!)
```

**Scenario 2: Tried to cascade Oceanside sizes**
```
Wrong: Assumed 2× 12×12 = 1× 24×24
Correct: Cascade ONLY applies to Bullseye 3mm Half/Full
```

**Scenario 3: Forgot Oceanside can zero 24×24**
```
Wrong: Kept 24×24 above 0.20 YIS minimum
Correct: Oceanside 24×24 can go to zero (exception)
```

### Prevention

✅ **Check system type FIRST** in every workflow
✅ **Use system-specific thresholds:**
- Oceanside: 0.35 target, can zero 24×24
- Bullseye Cuts: 0.25 minimum
- Bullseye Orders: 0.40 target
- Bullseye Half (3mm): 0.40 minimum

✅ **Cascade = Bullseye 3mm ONLY**
✅ Reference: [System Comparison Table](../wiki/INDEX.md#system-comparison-table)

---

## 🚨 ERROR #6: Wrong Color De Verre Order Quantity

**Frequency:** Moderate
**Impact:** Medium (order rejected or inefficient)
**System:** Color De Verre vendor orders

### What Happens

**Scenario: Need 18 pieces, currently have 0**

**Wrong Order:**
```
Order exactly 18 pieces
Issues:
- Not multiple of 5 (violates Rule 1)
- Forgot +10 for zero stock (violates Rule 2)
```

**Correct Order:**
```
Step 1: Round to multiple of 5
   CEIL(18 ÷ 5) × 5 = 4 × 5 = 20 pieces

Step 2: Check zero stock adjustment
   Current = 0 → Add 10
   20 + 10 = 30 pieces

Final order: 30 pieces
```

**Dragonfly Mold Exception:**
```
IF Product = "Dragonfly Mold" THEN
   Order = 100 (always, ignores other rules)
END IF
```

### Prevention

✅ **Apply CDV rules in order:**
1. Multiples of 5
2. +10 if zero stock
3. Dragonfly = 100 always

✅ Reference: [Color De Verre Rules](../02_Business_Rules/Color_De_Verre_Rules.md)

---

## 🚨 ERROR #7: Forgot to Update Inventory After Cuts

**Frequency:** Low (process error)
**Impact:** High (double-counting inventory)
**System:** All systems

### What Happens

**Scenario:**
- Generated work order to cut 4 sheets 24×24
- Cutting completed
- **Forgot to update inventory system**

**Result:**
- Inventory still shows 8 sheets 24×24 (wrong, should be 4)
- Inventory still shows 50 pieces 6×6 (wrong, should be 114)
- Next work order uses incorrect data
- May generate duplicate cut instructions

### Prevention

✅ **Workflow includes inventory update step**
✅ **Update BOTH source and target quantities**
✅ **Verify YIS calculations after update**
✅ **Best practice:** Update immediately after cutting, not batch at end of day

---

## 🚨 ERROR #8: Ignored 3mm vs 6mm Thickness

**Frequency:** Low-Moderate
**Impact:** High (wrong yields, wrong cascade logic)
**System:** Bullseye COE90

### What Happens

**Scenario 1: Applied cascade to 6mm**
```
Wrong: Tried to cascade 2 Half (6mm) → 1 Full
Correct: Cascade ONLY for 3mm thickness
```

**Scenario 2: Mixed thickness in calculations**
```
Wrong: Used 3mm yields for 6mm glass
Correct: Different thickness = different cutting behavior
```

### Why Thickness Matters

- **3mm:** Cascade possible (2 Half = 1 Full)
- **6mm:** NO cascade, different handling
- **Cutting yields may differ**
- **Sales velocity differs between thicknesses**

### Prevention

✅ **Always check thickness field**
✅ **IF 3mm AND Bullseye → Check cascade**
✅ **IF 6mm AND Bullseye → Skip cascade logic**
✅ **Keep 3mm and 6mm separate in calculations**

---

## 🚨 ERROR #9: Smallest-Only Family Not Filtered

**Frequency:** Low
**Impact:** Medium (wasted effort on uncuttable families)
**System:** All systems

### What Happens

**Scenario:**
- Family has only 6×6 in stock (smallest size)
- All larger sizes (6×12, 12×12, 24×24) = 0
- Work order tries to cut smaller from smaller (impossible!)

**Result:**
- Cannot cut 6×6 into anything smaller
- Family should have been filtered during data cleanup
- Wastes time analyzing uncuttable family

### Prevention

✅ **Apply "smallest-size-only" filter** in data cleanup
✅ **Check:** If ONLY smallest size has stock AND all larger = 0 → Remove family
✅ Reference: [Family Filtering Logic](../01_Input_Data_Processing/Family_Filtering_Logic.md)
✅ Reference: [Inventory Filtering Workflow](../03_Decision_Workflows/Inventory_Filtering_Workflow.md)

---

## 🚨 ERROR #10: Kerf/Trim Loss Not Considered

**Frequency:** Low
**Impact:** Low (minor yield differences)
**System:** All systems

### What Happens

**Ideal Yield (No Loss):**
```
24×24 → 6×6: 24÷6 = 4, 4×4 = 16 pieces (theoretical)
```

**Actual Yield (With Kerf):**
```
Saw blade width (~1/8") + trim margins
Actual: ~14-15 pieces (5-10% loss)
```

**Result:**
- Work order says "expect 16 pieces"
- Actual cutting produces 14-15 pieces
- Slight shortfall vs. projection

### Why We Use Ideal Yields Anyway

- **Simpler calculations**
- **Loss varies by cutter, saw, glass condition**
- **Small percentage difference**
- **Extra safety margin built into target YIS**

### When to Account for Kerf

✅ **Large production runs** (100+ sheets)
✅ **Tight inventory margins** (YIS near minimum)
✅ **Quality/precision requirements**
✅ **Use 5-10% reduction** in yield expectations

**Standard approach:** Use ideal yields, accept minor variance

---

## 📊 Error Prevention Checklist

### Before Starting ANY Work Order

- [ ] **Verify system type** (Oceanside vs Bullseye vs CDV)
- [ ] **Check glass thickness** (3mm vs 6mm for Bullseye)
- [ ] **Confirm data is filtered** (keywords, families, smallest-only removed)
- [ ] **Validate size detection** passed (no SIZE_UNKNOWN flags)

### During Cutting Calculations

- [ ] **Use CEIL** for sheet requirements (round up)
- [ ] **Check source YIS after cut** ≥ minimum
- [ ] **Bullseye 3mm:** CASCADE CHECK performed
- [ ] **Correct yield table** used for system
- [ ] **Target YIS** matches system (0.35 Oceanside, 0.40 Bullseye)

### Before Finalizing Output

- [ ] **All formulas validated** (see Formulas Quick Reference)
- [ ] **No source dropped below minimum** (except Oceanside 24×24)
- [ ] **Cascade opportunities documented** (Bullseye 3mm)
- [ ] **CDV orders** follow 3 rules (multiples of 5, +10 if zero, Dragonfly=100)
- [ ] **Special cases noted** in work order

### After Work Order Execution

- [ ] **Update inventory** (source reduced, target increased)
- [ ] **Verify actual yields** match projections
- [ ] **Record any kerf loss** observed
- [ ] **Flag any recurring issues** for process improvement

---

## 🔗 Related Documents

- **Workflows:** [Inventory Filtering Workflow](../03_Decision_Workflows/Inventory_Filtering_Workflow.md)
- **Workflows:** [Cut Sheet Logic Decision Tree](../03_Decision_Workflows/Cut_Sheet_Logic_Decision_Tree.md)
- **Workflows:** [Size Detection & Analysis](../03_Decision_Workflows/Size_Detection_And_Analysis.md)
- **Reference:** [Cascade Cutting Logic](./Cascade_Cutting_Logic.md)
- **Reference:** [Formulas Quick Reference](./Formulas_Quick_Reference.md)
- **Business Rules:** [Years in Stock Thresholds](../02_Business_Rules/Years_In_Stock_Thresholds.md)
- **Business Rules:** [Color De Verre Rules](../02_Business_Rules/Color_De_Verre_Rules.md)

---

**Governance:** CLAUDE.md "Be Critical" Rule ✓
**Format:** Error catalog + prevention strategies
**Cross-referenced:** 7 related documents
