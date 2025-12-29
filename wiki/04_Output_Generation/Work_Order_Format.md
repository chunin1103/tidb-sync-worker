# Work Order Format Specifications

**Purpose:** Standardized templates for glass cutting work order outputs
**Applies to:** Oceanside COE96, Bullseye COE90 cutting operations
**Last Updated:** 2025-12-21

---

## 📋 Overview

Work orders are generated in two formats:
1. **Excel Workbook** (.xlsx) - Editable, sortable data table
2. **PDF Instructions** (.pdf) - Print-friendly cutting instructions

Both formats must be generated from the same source data to ensure consistency.

---

## 📊 Excel Workbook Specification

### File Naming Convention

```
WorkOrder_[System]_[Date].xlsx

Examples:
- WorkOrder_Oceanside_2025-12-21.xlsx
- WorkOrder_Bullseye_CutSheet_2025-12-21.xlsx
- WorkOrder_Bullseye_Ordering_2025-12-21.xlsx
```

### Sheet Structure

**Single worksheet named:** "Cutting Instructions"

### Column Specifications

| Column | Header | Data Type | Width | Format | Description |
|--------|--------|-----------|-------|--------|-------------|
| A | Parent_ID | Text | 15 | General | Unique product ID |
| B | Parent_Name | Text | 50 | General | Full product name |
| C | Color | Text | 30 | General | Color/pattern description |
| D | Thickness | Text | 10 | General | e.g., "3mm", "6mm" |
| E | Source_Size | Text | 12 | General | e.g., "24×24", "Full" |
| F | Target_Size | Text | 12 | General | e.g., "6×6", "5×5" |
| G | Sheets_to_Cut | Integer | 10 | Number (0 decimals) | How many source sheets |
| H | Pieces_Produced | Integer | 12 | Number (0 decimals) | Expected output |
| I | Current_Target_Qty | Integer | 12 | Number (0 decimals) | Before cutting |
| J | After_Cut_Target_Qty | Integer | 12 | Number (0 decimals) | After cutting |
| K | Current_YIS | Decimal | 12 | Number (2 decimals) | Before cutting |
| L | Target_YIS | Decimal | 12 | Number (2 decimals) | Goal YIS |
| M | After_Cut_YIS | Decimal | 12 | Number (2 decimals) | Expected after cutting |
| N | Notes | Text | 40 | General | Special instructions |

### Conditional Formatting

**Apply to column M (After_Cut_YIS):**

| Condition | Format | Meaning |
|-----------|--------|---------|
| Value < 0.20 | Red fill, bold | ❌ Below minimum |
| 0.20 ≤ Value < Target | Yellow fill | ⚠️ Below target but safe |
| Value ≥ Target | Green fill | ✅ Target reached |

**Apply to column L (Target_YIS):**
- Bold all values (this is the goal column)

### Sort Order

**Primary:** Parent_Name (A→Z alphabetical)
**Secondary:** Source_Size (largest to smallest: 24×24 → 12×12 → 6×12)
**Tertiary:** Target_Size (largest to smallest)

**Rationale:** Groups by color, cuts largest sources first for efficiency

### Header Row Formatting

- **Row 1:** Bold, 11pt font
- **Background:** Light blue (#D9E2F3)
- **Borders:** All cells
- **Freeze:** Row 1 (headers stay visible when scrolling)

### Example Excel Rows

| Parent_ID | Parent_Name | Color | Thickness | Source_Size | Target_Size | Sheets_to_Cut | Pieces_Produced | Current_Target_Qty | After_Cut_Target_Qty | Current_YIS | Target_YIS | After_Cut_YIS | Notes |
|-----------|-------------|-------|-----------|-------------|-------------|---------------|-----------------|-------------------|---------------------|-------------|------------|---------------|-------|
| 12345 | Oceanside Almond Opalescent COE96 | Almond Opalescent | 3mm | 24×24 | 6×6 | 4 | 64 | 50 | 114 | 0.15 | 0.35 | 0.35 | Target reached |
| 12345 | Oceanside Almond Opalescent COE96 | Almond Opalescent | 3mm | 24×24 | 6×12 | 2 | 16 | 50 | 66 | 0.19 | 0.35 | 0.25 | Partially optimized |
| 12346 | Oceanside Cobalt Blue COE96 | Cobalt Blue | 3mm | 24×24 | 12×12 | 3 | 12 | 40 | 52 | 0.12 | 0.35 | 0.16 | Still below target |

---

## 📄 PDF Instructions Specification

### File Naming Convention

```
WorkOrder_[System]_[Date]_Instructions.pdf

Examples:
- WorkOrder_Oceanside_2025-12-21_Instructions.pdf
- WorkOrder_Bullseye_CutSheet_2025-12-21_Instructions.pdf
```

### Page Layout

- **Paper Size:** US Letter (8.5" × 11")
- **Orientation:** Portrait
- **Margins:** 0.75" all sides
- **Font:** Sans-serif (Arial, Helvetica, or Calibri)

### Page 1: Summary Page

#### Header Section
```
┌─────────────────────────────────────────────┐
│ GLASS CUTTING WORK ORDER                    │
│ System: [Oceanside COE96 / Bullseye COE90]  │
│ Date Generated: YYYY-MM-DD                  │
│ Total Colors: [N]                           │
│ Total Cuts: [N] sheets                      │
└─────────────────────────────────────────────┘
```

#### Summary Table
| Metric | Value |
|--------|-------|
| Families processed | [N] |
| Total source sheets to cut | [N] |
| Total pieces to produce | [N] |
| Average YIS improvement | [N%] |
| Estimated cutting time | [N] hours |

#### Critical Notes Section
**Special Attention Required:**
- List any families requiring cascade logic (Bullseye)
- List any sizes being cut to zero
- List any non-standard cuts
- List any manual review flags

---

### Pages 2+: One Page Per Parent Color

#### Page Template

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ COLOR: [Parent Name]                         ┃
┃ ID: [Parent_ID]        Thickness: [3mm/6mm]  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┌─ CURRENT INVENTORY ─────────────────────────┐
│ Size    │ Qty │  YIS  │ Status             │
├─────────┼─────┼───────┼────────────────────┤
│ 24×24   │  8  │ 0.52  │ Overstocked        │
│ 12×12   │ 116 │ 0.36  │ At target          │
│ 6×12    │  50 │ 0.19  │ ⚠️ Below target    │
│ 6×6     │  50 │ 0.15  │ ⚠️ Below target    │
└─────────┴─────┴───────┴────────────────────┘

┌─ CUTTING INSTRUCTIONS ──────────────────────┐
│                                              │
│ INSTRUCTION 1:                               │
│ ✂️ Cut 2 sheets of 24×24                    │
│    → Produces 16 pieces of 6×12             │
│                                              │
│    Result:                                   │
│    • 6×12: 50 → 66 pieces (0.19 → 0.25 YIS) │
│    • 24×24: 8 → 6 sheets (0.52 → 0.39 YIS)  │
│                                              │
│ INSTRUCTION 2:                               │
│ ✂️ Cut 4 sheets of 24×24                    │
│    → Produces 64 pieces of 6×6              │
│                                              │
│    Result:                                   │
│    • 6×6: 50 → 114 pieces (0.15 → 0.35 YIS) ✓│
│    • 24×24: 6 → 2 sheets (0.39 → 0.13 YIS)  │
│                                              │
└──────────────────────────────────────────────┘

┌─ FINAL INVENTORY (After All Cuts) ──────────┐
│ Size    │ Qty │  YIS  │ Status             │
├─────────┼─────┼───────┼────────────────────┤
│ 24×24   │  2  │ 0.13  │ Below minimum      │
│ 12×12   │ 116 │ 0.36  │ ✓ At target        │
│ 6×12    │  66 │ 0.25  │ Improved           │
│ 6×6     │ 114 │ 0.35  │ ✓ Target reached   │
└─────────┴─────┴───────┴────────────────────┘

┌─ NOTES ─────────────────────────────────────┐
│ • 24×24 will be below minimum after cuts    │
│   (acceptable: only 5.9% of sales)          │
│ • Consider ordering 24×24 on next cycle     │
└──────────────────────────────────────────────┘

                                    Page 2 of 15
```

#### Visual Indicators

| Symbol | Meaning |
|--------|---------|
| ✅ / ✓ | Target reached |
| ⚠️ | Below target but safe |
| ❌ | Below minimum threshold |
| ✂️ | Cutting instruction |
| 📦 | Order from vendor |

---

## 🎨 Formatting Guidelines

### Color Coding (PDF)

**Status Colors:**
- **Green (#00B050):** ≥ Target YIS
- **Yellow (#FFC000):** Between minimum and target
- **Red (#FF0000):** Below minimum
- **Blue (#0070C0):** Headers and titles

### Typography

**Headers:**
- Main title: 18pt bold
- Section headers: 14pt bold
- Subsections: 12pt bold

**Body Text:**
- Instructions: 11pt regular
- Tables: 10pt regular
- Notes: 9pt italic

### Table Borders

- **Outer border:** 2pt solid black
- **Header row:** 1pt solid black bottom border
- **Data rows:** 0.5pt gray (#808080)

---

## 📋 Special Format Cases

### Bullseye Cascade Instructions

When cascade logic applies (3mm only), add special notation:

```
┌─ CASCADE OPPORTUNITY ───────────────────────┐
│ ⚠️ CRITICAL: Check cascade before cutting   │
│                                              │
│ Option A: Direct Cut (if Full available)    │
│ ✂️ Cut 1 Full Sheet → 4× 10×10              │
│                                              │
│ Option B: Cascade Cut (if Full unavailable) │
│ 1. Cascade: 2 Half → 1 Full equivalent      │
│    • Verify Half ≥ 0.40 YIS after cascade   │
│ 2. ✂️ Cut cascaded Full → 4× 10×10          │
│                                              │
│ ✅ Recommended: Option B (saves ordering)   │
└──────────────────────────────────────────────┘
```

### Vendor Order Flag

When cutting is not viable:

```
┌─ VENDOR ORDER REQUIRED ─────────────────────┐
│ 📦 Cannot cut: Insufficient source inventory│
│                                              │
│ Order from vendor:                           │
│ • Size: 12×12                               │
│ • Quantity: 93 pieces                       │
│ • Reason: Only 2 sheets of 24×24 available  │
│           (need 24 sheets for full cut)     │
│                                              │
│ See: Vendor Order Decision Tree             │
└──────────────────────────────────────────────┘
```

### Mixed Strategy

When both cutting and ordering needed:

```
┌─ HYBRID APPROACH ───────────────────────────┐
│ Step 1: Cut Available Inventory             │
│ ✂️ Cut 5 sheets 24×24 → 40 pieces 6×12      │
│    • Uses all available 24×24               │
│    • 6×12: 20 → 60 pieces                   │
│                                              │
│ Step 2: Order Remainder from Vendor         │
│ 📦 Order 29 pieces of 6×12                  │
│    • Brings total to 89 pieces (0.34 YIS)   │
│    • Near target of 0.35 YIS                │
└──────────────────────────────────────────────┘
```

---

## ✅ Quality Checklist

Before finalizing output:

### Excel Workbook
- [ ] All columns present and properly formatted
- [ ] Conditional formatting applied
- [ ] Sorted correctly (Parent → Source → Target)
- [ ] Headers frozen
- [ ] No #VALUE or #DIV/0 errors
- [ ] File name follows convention

### PDF Instructions
- [ ] Summary page present
- [ ] One page per parent color
- [ ] All visual indicators (✓, ⚠️, ❌) used correctly
- [ ] Color coding applied
- [ ] Page numbers included
- [ ] File name follows convention

### Content Validation
- [ ] Cutting math verified (pieces × yield = total)
- [ ] YIS calculations correct
- [ ] No source cut below minimum (except Oceanside 24×24)
- [ ] Cascade opportunities flagged (Bullseye 3mm)
- [ ] Special cases documented in notes

---

## 🔗 Related Documents

- **Generation Logic:** [Work Order Generation Process](../03_Decision_Workflows/Work_Order_Generation_Process.md)
- **Cutting Strategy:** [Cut Sheet Logic Decision Tree](../03_Decision_Workflows/Cut_Sheet_Logic_Decision_Tree.md)
- **Business Rules:** [Years in Stock Thresholds](../02_Business_Rules/Years_In_Stock_Thresholds.md)
- **Reference:** [Formulas Quick Reference](../06_Reference_Data/Formulas_Quick_Reference.md)

---

**Governance:** CLAUDE.md "Anti-Duplication Protocol" ✓
**Format:** Specification tables + visual examples + checklists
**Cross-referenced:** 4 related documents
