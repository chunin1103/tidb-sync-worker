# Oceanside Glass COE96 System

**Product Line:** Oceanside Glass and Tile - COE96 sheet glass
**Purpose:** Custom cutting work orders to optimize inventory based on sales patterns
**Workflow:** Ad-hoc cutting when inventory becomes unbalanced

---

## System Overview

This system manages Oceanside glass inventory by:
1. Analyzing current stock vs sales patterns (Years in Stock metric)
2. Identifying products with unbalanced inventory across sizes
3. Generating cutting work orders to rebalance stock
4. Optimizing for sales distribution (94% of sales are ≤12"×12")

---

## Key Files in This Folder

### Primary Documentation
- **[Comprehensive_Process_Documentation.md](./Comprehensive_Process_Documentation.md)**
  Complete 447-line documentation covering entire workflow:
  - Data cleanup process
  - Filtering rules
  - Work order generation
  - Cutting strategies
  - Implementation workflow

- **[Reorder_Calculation_Summary.md](./Reorder_Calculation_Summary.md)**
  Reorder quantity calculation methodology:
  - Target YIS: 0.35 years (4.2 months)
  - Formula and examples
  - Cutting opportunities identification

---

## Glass Specifications

### Standard Sizes (Parent/Child Structure)
Typical parent product has 4 children:
- 6"×6" (smallest)
- 6"×12"
- 12"×12"
- 24"×24" or 24"×22" (full sheet)

### Cutting Yields
See: [../../02_Business_Rules/Glass_Sizes_and_Cutting_Yields.md](../../02_Business_Rules/Glass_Sizes_and_Cutting_Yields.md)

---

## Business Rules

### Years in Stock (YIS) Thresholds
- **Lean:** 0.20 years (73 days)
- **Target:** 0.35 years (128 days) ← Primary reorder target
- **Well-stocked:** 0.40 years (146 days)
- **Overstocked:** > 0.40 years

See: [../../02_Business_Rules/Years_In_Stock_Thresholds.md](../../02_Business_Rules/Years_In_Stock_Thresholds.md)

---

## Workflows

### 1. Data Cleanup & Filtering
**Input:** Raw inventory export (CSV/Excel)
**Output:** cleaned_filtered.csv with work order candidates

**Steps:**
1. Remove non-sheet products (frit, stringers, etc.)
2. Remove well-stocked families (all 4 sizes > 0.4 YIS)
3. Remove zero-stock families
4. Remove smallest-only families

**See:** [../../03_Decision_Workflows/Inventory_Filtering_Workflow.md](../../03_Decision_Workflows/Inventory_Filtering_Workflow.md)

---

### 2. Reorder Calculation
**For each product:**
1. Calculate annual sales from YIS
2. Calculate target quantity (0.35 years coverage)
3. Calculate deficit
4. Check cutting opportunities
5. Generate reorder or cutting recommendation

**See:** [../../03_Decision_Workflows/Reorder_Calculation_Workflow.md](../../03_Decision_Workflows/Reorder_Calculation_Workflow.md)

---

### 3. Work Order Generation
**Output:** Cutting instructions for warehouse

**Format:**
```
WORK ORDER
Parent ID: 156660
Product: Oceanside Glass Almond Opalescent 3mm COE96

CUTTING INSTRUCTIONS:
Step 1: Cut 1× 12"×12" → 4× 6"×6"
Step 2: Cut 1× 12"×12" → 2× 6"×12"
```

---

## Sales Distribution Insight

Historical data shows:
- **6"×6":** 21.5% of sales
- **6"×12":** 25.1% of sales
- **12"×12":** 47.5% of sales
- **24"×24":** 5.9% of sales

**Strategic Implication:** It's acceptable to cut full sheets (24"×24") to zero inventory when it optimizes smaller size availability, since only 5.9% of sales are full sheets.

---

## Cutting Strategy

### Priorities (In Order)
1. **Get products off zero** - prevent stockouts
2. **Optimize balance** - target 0.35 YIS across sizes
3. **Minimize labor** - fewest cuts for maximum impact

### Guardrails
- Don't create new zeros (unless data-driven)
- Check for open orders on full sheets
- Consider lead time to next order
- Respect margin/freight considerations
- Protect rare colors/textures

---

## Related Systems

### Comparison with Bullseye System
- **Oceanside:** Ad-hoc cutting, 0.35yr target, focus on balance
- **Bullseye Cuts:** Biweekly cycle, 0.25yr minimum, focus on zeros
- **Bullseye Orders:** 0.40yr target, cascade logic, 35-day lead time

See: [../../02_Business_Rules/Years_In_Stock_Thresholds.md](../../02_Business_Rules/Years_In_Stock_Thresholds.md) for comparison table

---

## Scripts & Tools

**Location:** Root level (not yet integrated into Production folder)
- `calculate_reorder.py` - Reorder calculation script

**Future:** Move scripts to `Production/scripts/` folder

---

## Sample Data Files

**Location:** [../../06_Reference_Data/Sample_Data_Files/](../../06_Reference_Data/Sample_Data_Files/)

Example files:
- `chatgpt make a cutsheet first complete test 10-22-25.csv`
- `Color De Verre Report 10_20_2025 - Sheet1.csv`

---

## Quick Start

### To Generate Work Orders:

1. **Export inventory** from your system
2. **Run data cleanup** using [Data Cleanup Master Prompt](../../01_Input_Data_Processing/Data_Cleanup_Master_Prompt.md)
3. **Review filtered data** (cleaned_filtered.csv)
4. **Calculate reorders** using methodology in [Reorder_Calculation_Summary.md](./Reorder_Calculation_Summary.md)
5. **Generate work orders** for products with cutting opportunities
6. **Review & approve** before executing cuts

---

## Future Enhancements

### Planned Improvements
1. **Kerf & Trim Accounting** - Real-world yields vs ideal
2. **Target YIS Configuration** - Size-specific targets
3. **Mixed Cutting Strategies** - 2D bin packing optimization
4. **Open Order Integration** - Check reserved inventory

See: Comprehensive_Process_Documentation.md, lines 373-411

---

**Last Updated:** 2025-12-21
**Status:** Active system with documented processes
