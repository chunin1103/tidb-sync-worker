# Bullseye Glass COE90 System

**Product Line:** Bullseye COE90 glass (3mm double-rolled primary, 2mm thin-rolled)
**Location:** `../../../Bullseye Glass/` (relative to Claude Tools root)
**Status:** Fully documented system with TWO integrated subsystems

---

## ⚠️ Important: Complete Documentation Location

This system has comprehensive documentation in:
```
C:\Users\tnguyen24_mantu\OneDrive\Claude Tools\Bullseye Glass\
```

**This README is a navigation guide only. Full system documentation lives in the Bullseye Glass folder.**

---

## System Overview

The Bullseye Glass system consists of **TWO INTEGRATED SYSTEMS**:

### 1. Bullseye Cut Sheets
**Location:** `Bullseye Glass/Bullseye Cut Sheets/`
**Purpose:** Biweekly cutting to rebalance inventory between Bullseye orders
**Cycle:** Every 14 days

### 2. Bullseye Ordering
**Location:** `Bullseye Glass/Bullseye Ordering/bullseye/`
**Purpose:** Vendor reorder recommendations (~10 orders/year)
**Frequency:** ~Every 37 days

---

## Master Context File

**CRITICAL - READ FIRST:**
```
C:\Users\tnguyen24_mantu\OneDrive\Claude Tools\Bullseye Glass\MASTER_CONTEXT_PROMPT.md
```

This 445-line file contains:
- Complete system overview
- Glass sizes and cutting yields
- Cascade cutting logic (CRITICAL!)
- The 5 business rules (Phase 2 learnings)
- Tier system
- Complete workflows for both subsystems
- 5-step algorithm for ordering
- Common errors to avoid
- Validation display formats
- Checklists for every session

---

## Quick Reference: Key Differences from Oceanside

| Aspect | Oceanside | Bullseye |
|--------|-----------|----------|
| **Sizes** | 24"×24", 12"×12", 6"×12", 6"×6" | 20"×35", 17"×20", 10×10, 5×10, 5×5 |
| **Min YIS** | 0.20yr | 0.25yr (91 days) |
| **Target YIS** | 0.35yr | 0.40yr (146 days) |
| **Cycle** | Ad-hoc | Biweekly (cut sheets) / 37 days (ordering) |
| **Priority** | Balance inventory | Get off zero first |
| **Special Rules** | Sales-driven (94% small) | Cascade logic (CRITICAL!), 3mm Half=Full equiv |

---

## Glass Sizes (Bullseye)

### Standard Retail Sizes
- **Full Sheet:** 20"×35" (700 sq in) - immediately cut upon receiving
- **Half Sheet:** 17"×20" (340 sq in) - largest retail size
- **10×10:** 10"×10" (100 sq in) - **MOST POPULAR**
- **5×10:** 5"×10" (50 sq in)
- **5×5:** 5"×5" (25 sq in) - smallest

---

## Critical: Cascade Cutting Logic

**CASCADE = using freshly-produced pieces for secondary cuts**

```
Full Sheet  → 6× 10×10 + 2× 5×10
Half Sheet  → 2× 10×10 + 2× 5×10
10×10       → 2× 5×10 OR 4× 5×5 OR 1× 5×10 + 2× 5×5
5×10        → 2× 5×5
5×5         → Never cut (smallest)
```

**CRITICAL RULE:** Can ONLY cascade DOWN (large→small), NEVER UP
- 5×10 surplus CANNOT help 10×10 deficit
- 5×5 surplus CANNOT help anything

---

## The 5 Business Rules (Phase 2)

1. **Cascade cutting** - use freshly-produced pieces to minimize warehouse trips
2. **Getting off zero > perfect safety margins**
3. **Byproduct accumulation is acceptable** (5×10 overstock from Half cuts is OK)
4. **Don't sacrifice popular sizes** (protect 10×10 bestsellers)
5. **Priority-based Half Sheet preservation** - cut Halves as last resort when Fulls available

---

## Systems Comparison

### Cut Sheets System
- **Frequency:** Biweekly (14 days)
- **Goal:** Get products off zero, prevent stockouts
- **Threshold:** 0.25 years (91 days) minimum
- **Tiers:**
  - Tier 1: At least one size at zero (HIGHEST priority)
  - Tier 2: Rebalancing needed (urgency buckets: Critical/Urgent/Watch/OK)
  - Tier 3: Adequate stock

**Scripts:**
- `glass_cutting_optimizer_balanced.py` (v3.2)
- `generate_work_order_excel.py` (v2.5)
- `generate_logic_pdf.py` (v2.0)

---

### Ordering System
- **Frequency:** ~10 orders/year (every 37 days average)
- **Goal:** Get ALL sizes to 0.40 years coverage
- **Lead Time:** 35-72 days total
- **Special:** Holly Berry Red seasonal pre-order (by June 30)

**Key Algorithm: 5 STEPS (NEVER SKIP ANY)**
1. CASCADE FROM EXISTING INVENTORY (FIRST!)
2. Check if order needed (0.25yr threshold)
3. Calculate minimum order (0.40yr target)
4. Cascade from new order
5. Verify all sizes above 0.40yr

**Scripts:**
- `analyze_reorder_needs.py` (v2.0)

---

## 3mm Special Rule

**CRITICAL:** 2 Half Sheets can be cut as 1 Full Sheet equivalent!
- This is **ONLY for 3mm**, NOT 2mm
- Check for Half Sheet EXCESS before ordering
- Can save significant ordering costs

---

## Common Errors to Avoid

1. **Forgetting to cascade from inventory FIRST** ← Most common!
2. **Not cascading 10×10 → 5×10** (valid and often overlooked)
3. **Trying to cascade UP** (only go large→small)
4. **Forgetting Half Sheet deficit** (need to SAVE Full as Half)
5. **Not verifying Half Sheet in final check** (must also be ≥ 0.40yr)

---

## File Structure

```
Bullseye Glass/
├── MASTER_CONTEXT_PROMPT.md (READ THIS FIRST!)
├── Bullseye Cut Sheets/
│   ├── README.md
│   ├── reference/ (business knowledge, rules, learnings)
│   ├── scripts/ (Python cutting optimizers)
│   ├── data/
│   │   ├── input/
│   │   ├── output/
│   │   └── temp/
│   └── archive/
└── Bullseye Ordering/
    └── bullseye/
        ├── context/ (REORDER_RULES.md, VERSION_HISTORY.md)
        ├── scripts/ (analyze_reorder_needs.py)
        └── data/
```

---

## Workflow Access

### For Cut Sheets Work:
```bash
cd "C:\Users\tnguyen24_mantu\OneDrive\Claude Tools\Bullseye Glass\Bullseye Cut Sheets"
python scripts/glass_cutting_optimizer_balanced.py
python scripts/generate_work_order_excel.py
python scripts/generate_logic_pdf.py
```

### For Ordering Work:
```bash
cd "C:\Users\tnguyen24_mantu\OneDrive\Claude Tools\Bullseye Glass\Bullseye Ordering\bullseye\scripts"
python analyze_reorder_needs.py
```

---

## Related Wiki Files

**Business Rules:**
- [../../02_Business_Rules/Glass_Sizes_and_Cutting_Yields.md](../../02_Business_Rules/Glass_Sizes_and_Cutting_Yields.md) - Comparison with Oceanside
- [../../02_Business_Rules/Years_In_Stock_Thresholds.md](../../02_Business_Rules/Years_In_Stock_Thresholds.md) - Threshold comparison table

**Workflows:**
- [../../03_Decision_Workflows/Bullseye_Vendor_Purchase_Decision_Tree.md](../../03_Decision_Workflows/Bullseye_Vendor_Purchase_Decision_Tree.md) - **Complete purchasing workflow** ⭐
- See Bullseye Glass/Bullseye Cut Sheets/reference/ for cut sheet workflows

---

## Quick Start Checklist

Before working on Bullseye system:
- [ ] Read `MASTER_CONTEXT_PROMPT.md`
- [ ] Read `Bullseye Cut Sheets/reference/GLASS_CUTTING_KNOWLEDGE.md` (for cuts)
- [ ] Read `Bullseye Ordering/bullseye/context/REORDER_RULES.md` (for orders)
- [ ] Identify which subsystem (Cut Sheets or Ordering)
- [ ] Load latest inventory CSV
- [ ] **ALWAYS check cascade opportunities FIRST!**

---

**Last Updated:** 2025-12-21
**System Version:** Cut Sheets v3.2, Ordering v2.0
