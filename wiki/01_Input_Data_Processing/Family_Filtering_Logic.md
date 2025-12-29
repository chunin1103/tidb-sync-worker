# Family Filtering Logic

**Purpose:** Remove product families that don't need cutting work orders
**Applied After:** Keyword filtering (Step 2)

---

## Product Family Structure

### Definition
- **Parent:** Main product entry (e.g., "Oceanside Glass Almond Opalescent 3mm COE96")
- **Children:** Size variants under the parent (typically 4 children)
  - 6"×6" (smallest)
  - 6"×12"
  - 12"×12"
  - 24"×24" (largest, full sheet)
- **Family:** Parent + all children with matching Parent_ID

### Family Identification
```
Child row = any row with non-blank Parent_ID
Family = parent row (if present) + all children where Parent_ID matches
```

---

## Three Filtering Rules

### Rule 1: Well-Stocked Families (Exactly 4 Children @ >0.4 YIS)

**Trigger:** Remove if ALL conditions met:
1. Parent has **exactly 4 children**
2. **Every child** has Years_in_Stock > 0.4 (strictly greater than)
3. No child has blank or non-numeric Years_in_Stock

**Rationale:** All sizes are well-stocked (>0.4 years = >146 days supply). No cutting needed.

**Action:** Remove entire family (parent + all 4 children)

**Example:**
```
Parent: 123456 (Oceanside Clear Glass)
├─ 123457: 6"×6"    YIS: 0.45 ✓
├─ 123458: 6"×12"   YIS: 0.52 ✓
├─ 123459: 12"×12"  YIS: 0.48 ✓
└─ 123460: 24"×24"  YIS: 0.41 ✓

Decision: REMOVE (all children > 0.4)
```

**Typical Impact:** ~11 families removed (~44 rows)

---

### Rule 2: Zero-Stock Families

**Trigger:** Remove if:
- **ALL children** have Quantity/Stock = 0

**Rationale:** Nothing in stock to cut. Can't generate work orders.

**Action:** Remove entire family (parent + all children)

**Example:**
```
Parent: 234567 (Oceanside Blue Glass)
├─ 234568: 6"×6"    Stock: 0
├─ 234569: 6"×12"   Stock: 0
├─ 234570: 12"×12"  Stock: 0
└─ 234571: 24"×24"  Stock: 0

Decision: REMOVE (all zero stock)
```

**Display Before Removal:**
- Parent_ID
- Child count
- Child Product_IDs

**Typical Impact:** ~21 families removed (~84 rows)

---

### Rule 3: Smallest-Size-Only Families

**Trigger:** Remove if:
1. **Only the smallest-size child(ren)** have Stock > 0
2. **All larger-size children** have Stock = 0

**Rationale:** Can't cut small pieces into larger ones. No cutting options available.

**Size Detection:**
- Parse dimensions from Product Name (Column C)
- Patterns: "6x6", '6"×12"', "6 × 12", "6 in x 12 in"
- Calculate area (width × height)
- Smallest = minimum area

**Example:**
```
Parent: 345678 (Oceanside Red Glass)
├─ 345679: 6"×6"    Stock: 5  (smallest - 36 sq in)
├─ 345680: 6"×12"   Stock: 0  (72 sq in)
├─ 345681: 12"×12"  Stock: 0  (144 sq in)
└─ 345682: 24"×24"  Stock: 0  (576 sq in)

Decision: REMOVE (only smallest has stock, can't cut up)
```

**Display Before Removal:**
- Parent_ID
- Child count
- Smallest child Product_IDs
- Non-smallest child Product_IDs

**Typical Impact:** ~4 families removed (~16 rows)

---

## Processing Order

The three rules are applied in this sequence:

```
1. Load inventory (1,410 rows)
2. Remove keywords (→ 784 rows)
3. Rule 1: Well-stocked families (→ 740 rows, -44)
4. Rule 2: Zero-stock families (→ 656 rows, -84)
5. Rule 3: Smallest-only families (→ 640 rows, -16)
6. Output: cleaned_filtered.csv
```

---

## Reporting Requirements

### For Each Rule
- Number of families removed
- Total rows removed
- Summary table with:
  - Parent_ID
  - Child_Count
  - Min_Years (for Rule 1)
  - Max_Years (for Rule 1)

**Display:** Top 25 families inline (full list optional)

---

## What Remains After Filtering

Product families that:
- Have at least one size with low inventory (<0.4 YIS)
- Have at least one size with inventory available to cut from
- Can benefit from cutting larger sizes into smaller sizes

**These families become work order candidates.**

---

**Related Files:**
- [Data Cleanup Master Prompt](./Data_Cleanup_Master_Prompt.md)
- [Keyword Filtering Rules](./Keyword_Filtering_Rules.md)
- [../../02_Business_Rules/Years_In_Stock_Thresholds.md](../02_Business_Rules/Years_In_Stock_Thresholds.md)
