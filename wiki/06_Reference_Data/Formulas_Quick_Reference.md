# Formulas Quick Reference Card

**Purpose:** All key formulas for glass cutting systems in one place
**Systems:** Oceanside COE96, Bullseye COE90, Color De Verre
**Last Updated:** 2025-12-21

---

## 📊 Core Inventory Formulas

### Years in Stock (YIS)

**Primary Formula:**
```
YIS = Quantity On Hand ÷ Units Sold in Last 12 Months
```

**Example:**
```
116 pieces ÷ 326 units/year = 0.356 years ≈ 4.3 months
```

**Convert YIS to Days:**
```
Days = YIS × 365
```

**Convert YIS to Months:**
```
Months = YIS × 12
```

**Common Conversions:**
| YIS | Days | Months |
|-----|------|--------|
| 0.20 | 73 | 2.4 |
| 0.25 | 91 | 3.0 |
| 0.35 | 128 | 4.2 |
| 0.40 | 146 | 4.8 |

---

### Target Quantity Calculation

**Formula:**
```
Target Quantity = (Units Sold ÷ 12) × Target YIS × 12
```

**Simplified:**
```
Target Quantity = Units Sold × Target YIS
```

**Example (Oceanside, Target = 0.35 YIS):**
```
326 units/year × 0.35 = 114.1 ≈ 114 pieces
```

---

### Pieces Needed

**Formula:**
```
Pieces Needed = Target Quantity - Current Quantity
```

**Example:**
```
114 (target) - 50 (current) = 64 pieces needed
```

**Handle Negative Results:**
```
IF Pieces Needed < 0 THEN
    Already at/above target, no action needed
    Pieces Needed = 0
END IF
```

---

## ✂️ Cutting Calculation Formulas

### Sheets Required

**Formula:**
```
Sheets Required = CEIL(Pieces Needed ÷ Pieces per Cut)
```

**Note:** Use CEIL (round up) to ensure enough pieces

**Example (6×6 from 24×24):**
```
Need 64 pieces, yield 16/sheet
CEIL(64 ÷ 16) = CEIL(4.0) = 4 sheets
```

**Example (6×12 from 24×24):**
```
Need 69 pieces, yield 8/sheet
CEIL(69 ÷ 8) = CEIL(8.625) = 9 sheets
```

---

### Pieces Produced

**Formula:**
```
Pieces Produced = Sheets to Cut × Pieces per Cut
```

**Example:**
```
4 sheets × 16 pieces/sheet = 64 pieces
```

**May produce MORE than needed** (due to CEIL rounding)

---

### Source Quantity After Cut

**Formula:**
```
Source After Cut = Current Source Qty - Sheets Required
```

**Example:**
```
8 sheets (current 24×24) - 4 sheets (cutting) = 4 sheets remain
```

---

### Source YIS After Cut

**Formula:**
```
Source YIS After = Source After Cut ÷ (Source Units Sold ÷ 12)
```

**Example:**
```
4 sheets ÷ (48 units/year ÷ 12) = 4 ÷ 4 = 1.0 years
```

---

### Target Quantity After Cut

**Formula:**
```
Target After Cut = Current Target Qty + Pieces Produced
```

**Example:**
```
50 pieces (current 6×6) + 64 pieces (produced) = 114 pieces
```

---

### Target YIS After Cut

**Formula:**
```
Target YIS After = Target After Cut ÷ (Target Units Sold ÷ 12)
```

**Example:**
```
114 pieces ÷ (326 units/year ÷ 12) = 114 ÷ 27.2 = 4.19 months ≈ 0.35 years
```

---

## 🔄 Cascade Formulas (Bullseye 3mm Only)

### Half Sheets After Cascade

**Formula:**
```
Half After Cascade = Current Half Qty - 2
```

**Note:** Must use 2 Half at a time

**Example:**
```
18 Half sheets - 2 = 16 Half sheets remain
```

---

### Half YIS After Cascade

**Formula:**
```
Half YIS After = Half After Cascade ÷ (Half Units Sold ÷ 12)
```

**Example:**
```
16 pieces ÷ (24.6 units/year ÷ 12) = 16 ÷ 2.05 = 7.8 months ≈ 0.65 years
```

---

### Cascade Validation Check

**Formula:**
```
Can Cascade = (Half YIS After ≥ 0.40) AND (Current Half Qty ≥ 2)
```

**Example:**
```
(0.65 ≥ 0.40) AND (18 ≥ 2) = TRUE AND TRUE = TRUE ✓ Can cascade
```

---

## 📦 Vendor Order Formulas

### Color De Verre Order Quantity

**Rule 1: Multiples of 5**
```
Order Qty = CEIL(Pieces Needed ÷ 5) × 5
```

**Example:**
```
Need 18 pieces
CEIL(18 ÷ 5) × 5 = CEIL(3.6) × 5 = 4 × 5 = 20 pieces
```

**Rule 2: Zero Stock Adjustment**
```
IF Current Quantity = 0 THEN
    Order Qty = Order Qty + 10
END IF
```

**Example:**
```
Need 18 pieces, currently have 0
Base order: 20 pieces (from Rule 1)
Adjusted: 20 + 10 = 30 pieces
```

**Rule 3: Dragonfly Mold Exception**
```
IF Product = "Dragonfly Mold" THEN
    Order Qty = 100 (always)
END IF
```

---

### Bullseye Order Quantity

**Formula:**
```
Order Qty = Pieces Needed (round to whole number)
```

**Target YIS:**
- Cut Sheets: 0.25 years minimum
- Ordering: 0.40 years target

---

### Oceanside Order Quantity

**Formula:**
```
Order Qty = Target Quantity - Current Quantity
```

**Target YIS:** 0.35 years

---

## 📈 Sales Velocity Formulas

### Monthly Sales Rate

**Formula:**
```
Monthly Sales = Units Sold in Last 12 Months ÷ 12
```

**Example:**
```
326 units/year ÷ 12 = 27.2 units/month
```

---

### Daily Sales Rate

**Formula:**
```
Daily Sales = Units Sold in Last 12 Months ÷ 365
```

**Example:**
```
326 units/year ÷ 365 = 0.89 units/day
```

---

### Time Until Stockout

**Formula:**
```
Days Until Stockout = Current Quantity ÷ Daily Sales Rate
```

**Example:**
```
50 pieces ÷ 0.89 units/day = 56 days until zero
```

---

## 🎯 Threshold Validation Formulas

### Check Minimum YIS

**Formula:**
```
Above Minimum = (Current YIS ≥ Minimum YIS for System/Size)
```

**Thresholds:**
| System | Size | Minimum YIS |
|--------|------|-------------|
| Oceanside | All | 0.20 |
| Oceanside | 24×24 | 0 (can zero out) |
| Bullseye | Full, 10×10, 5×10, 5×5 | 0.25 |
| Bullseye | Half (3mm) | 0.40 |

---

### Check Target YIS

**Formula:**
```
At Target = (Current YIS ≥ Target YIS for System)
```

**Targets:**
| System | Target YIS |
|--------|-----------|
| Oceanside | 0.35 |
| Bullseye Cuts | 0.25 (minimum goal) |
| Bullseye Orders | 0.40 |

---

### Safety Margin Check

**Formula:**
```
Safety Margin = Current YIS - Minimum YIS
```

**Interpretation:**
| Safety Margin | Status |
|---------------|--------|
| < 0 | ❌ Below minimum |
| 0 to 0.05 | ⚠️ Critically low |
| 0.05 to 0.15 | ⚠️ Low safety margin |
| > 0.15 | ✅ Adequate buffer |

**Example:**
```
Current: 0.36 YIS
Minimum: 0.20 YIS
Safety Margin: 0.36 - 0.20 = 0.16 ✅ Adequate
```

---

## 🧮 Cutting Yield Reference Tables

### Oceanside COE96 Yields

| Source Size | Target Size | Pieces per Cut | Formula |
|-------------|-------------|----------------|---------|
| 24×24 | 12×12 | 4 | (24÷12) × (24÷12) = 4 |
| 24×24 | 6×12 | 8 | (24÷6) × (24÷12) = 8 |
| 24×24 | 6×6 | 16 | (24÷6) × (24÷6) = 16 |
| 12×12 | 6×12 | 2 | (12÷6) × (12÷12) = 2 |
| 12×12 | 6×6 | 4 | (12÷6) × (12÷6) = 4 |
| 6×12 | 6×6 | 2 | (6÷6) × (12÷6) = 2 |

### Bullseye COE90 Yields

| Source Size | Target Size | Pieces per Cut | Notes |
|-------------|-------------|----------------|-------|
| Full (17×20) | 10×10 | 4 | + 2× 5×10 + scrap |
| Full (20×35) | 10×10 | 7 | Special full size |
| 10×10 | 5×10 | 2 | Standard cut |
| 10×10 | 5×5 | 4 | Standard cut |
| 5×10 | 5×5 | 2 | Standard cut |

---

## 💡 Quick Calculation Examples

### Example 1: Complete Work Order Calculation

**Given:**
- Product: Oceanside Almond Opalescent 6×6
- Current Qty: 50 pieces
- Units Sold: 326/year
- Target YIS: 0.35
- Source (24×24): 8 sheets, 48 sold/year

**Step 1: Current YIS**
```
50 ÷ 326 = 0.15 years (below target)
```

**Step 2: Target Quantity**
```
326 × 0.35 = 114 pieces
```

**Step 3: Pieces Needed**
```
114 - 50 = 64 pieces
```

**Step 4: Sheets Required**
```
CEIL(64 ÷ 16) = 4 sheets
```

**Step 5: Source After Cut**
```
8 - 4 = 4 sheets
YIS: 4 ÷ (48 ÷ 12) = 1.0 years ✓
```

**Step 6: Target After Cut**
```
50 + 64 = 114 pieces
YIS: 114 ÷ (326 ÷ 12) = 0.35 years ✓ Target reached
```

---

### Example 2: Cascade Check Calculation

**Given:**
- Product: Bullseye Black Opal 3mm 10×10
- Need: 4 pieces (to reach 0.40 YIS)
- Full sheets: 0
- Half sheets: 18, sold 24.6/year

**Step 1: Check Cascade Availability**
```
Half Qty ≥ 2? → 18 ≥ 2 ✓
```

**Step 2: Half After Cascade**
```
18 - 2 = 16 Half sheets
```

**Step 3: Half YIS After**
```
16 ÷ (24.6 ÷ 12) = 16 ÷ 2.05 = 7.8 months = 0.65 years
```

**Step 4: Validate**
```
0.65 ≥ 0.40? ✓ Can cascade
```

**Decision:** Cascade 2 Half → 1 Full, cut to 4× 10×10

---

### Example 3: Color De Verre Order

**Given:**
- Product: CDV Powder (NOT Dragonfly)
- Current Qty: 0
- Need: 18 pieces

**Step 1: Base Order (Multiple of 5)**
```
CEIL(18 ÷ 5) × 5 = 4 × 5 = 20 pieces
```

**Step 2: Zero Stock Adjustment**
```
Current = 0 → Add 10
20 + 10 = 30 pieces
```

**Final Order:** 30 pieces

---

## 🔗 Related Documents

- **Workflows:** [Cut Sheet Logic Decision Tree](../03_Decision_Workflows/Cut_Sheet_Logic_Decision_Tree.md)
- **Business Rules:** [Years in Stock Thresholds](../02_Business_Rules/Years_In_Stock_Thresholds.md)
- **Business Rules:** [Glass Sizes and Cutting Yields](../02_Business_Rules/Glass_Sizes_and_Cutting_Yields.md)
- **Business Rules:** [Color De Verre Rules](../02_Business_Rules/Color_De_Verre_Rules.md)
- **Reference:** [Cascade Cutting Logic](./Cascade_Cutting_Logic.md)

---

**Governance:** CLAUDE.md "Decision Tree First" + tables for formulas ✓
**Format:** Formula reference + worked examples
**Cross-referenced:** 5 related documents
