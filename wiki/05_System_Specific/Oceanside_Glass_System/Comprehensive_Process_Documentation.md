# AGS Glass Cutting Work Order Process - Comprehensive Documentation

## Overview
This document consolidates the complete process for generating custom work orders for glass cutting operations at Art Glass Supplies. The system analyzes inventory data, filters products based on business rules, and generates cutting instructions to optimize inventory levels based on sales patterns.

---

## Business Context

### Product Structure
- **Parent Products**: Main product entries (e.g., "Oceanside Glass Almond Opalescent 3mm COE96")
- **Child Products**: Specific sizes under each parent, typically 4 children:
  - 6"x6" (smallest)
  - 6"x12"
  - 12"x12"
  - 24"x24" (largest, full sheet)
  - Some products use 24"x22" as the largest size

### Sales Distribution (Oceanside Glass)
Based on historical sales data analysis:
- **6"x6"**: 8,357 units sold (21.5% of sales)
- **6"x12"**: 9,724 units sold (25.1% of sales)
- **12"x12"**: 18,442 units sold (47.5% of sales)
- **24"x24"**: 2,292 units sold (5.9% of sales)

**Key Insight**: 94% of sales are smaller sizes (≤12"x12"), supporting a strategy to cut larger sheets even to zero inventory when it optimizes smaller size availability.

### Cutting Rules
Glass can only be cut from **larger to smaller sizes**:

#### From 24"x24" full sheet:
- 4× 12"x12" pieces
- 8× 6"x12" pieces
- 16× 6"x6" pieces

#### From 12"x12" piece:
- 2× 6"x12" pieces
- 4× 6"x6" pieces
- 1× 6"x12" + 2× 6"x6" (mixed cut)

#### From 6"x12" piece:
- 2× 6"x6" pieces

**Note**: These are ideal yields without accounting for kerf (saw blade width) and trim margins.

### Bullseye Glass (Different Manufacturer)
Uses different sheet sizes:
- **Full sheet**: 17"x20"
- **Half sheets**: Multiple configurations
- **Standard cuts**: 10"x10", 5"x10", 5"x5"

**Cutting yield from 17"x20"**:
- 4× 10"x10" + 2× 5"x10" + scrap (sold separately)

### Years in Stock (YIS) Metric
**Formula**: Years in Stock = On-hand Quantity ÷ Units Sold in Last 12 Months

**Purpose**: Indicates how many years of supply the current inventory represents.

**Target Ranges**:
- **0.20 years** = 2.4 months of supply (lean inventory)
- **0.35 years** = 4.2 months of supply (typical target)
- **0.40 years** = 4.8 months of supply (well-stocked threshold)
- **> 0.40 years** = overstocked

**Example**: 116 units in stock with 326 sold annually = 0.356 years (~4.3 months)

---

## Data Cleanup Process

### Master Prompt for Data Processing

The following prompt is used to filter and clean inventory data before generating work orders:

```
Role: You are my data-ops assistant. I will upload an Excel or CSV with a parent/child product structure. Follow these steps exactly every time. Use case-insensitive matching and be resilient to slightly different column names.

Constants (do not change unless I say so):
KEYWORDS_TO_REMOVE_IN_COL_C = ["reserve", "frit", "stringers", "noodles", "pound", "pack"]
THRESHOLD_YEARS = 0.4 (strictly greater than 0.4)
Column C = the sheet's 3rd column (0-based index 2)
Column H = the sheet's 8th column (0-based index 7) and represents "Years in Stock." Use its displayed numeric value only (do not recalc).

Likely headers to autodetect:
Product ID column: one of ["Product_ID","Products_ID","ID","ProductID"]
Parent ID column: header contains both "parent" and "id" (e.g., "Products_Parent_Id")

Tasks (in order):

1. Load & Snapshot
   - Load the uploaded file (first worksheet if Excel).
   - Report the original row count.

2. Keyword removals on Column C
   - Remove any row whose Column C contains any of KEYWORDS_TO_REMOVE_IN_COL_C (case-insensitive substring).
   - Report rows removed per keyword and the remaining count.

3. Identify key columns
   - Detect Product ID and Parent ID columns using the rules above. If multiple candidates exist, choose the best and list alternates considered.
   - Treat Column H as Years in Stock. For comparisons, coerce Column H to numeric with errors='coerce', but do not compute it from other fields.

4. Define families
   - A child row is any row with a non-blank Parent ID.
   - A family = the parent row (if present) plus all children whose Parent ID equals that parent (string compare).

5. Exactly-4-children rule @ 0.4
   - Consider only parents that have exactly 4 children.
   - If every one of the 4 children has Column H (Years in Stock) > THRESHOLD_YEARS, remove the entire family (parent row if present and all 4 children).
   - If any of the 4 children is ≤ 0.4 or Column H is blank/non-numeric, keep the entire family.

6. Additional step — zero-stock families
   - Find all parents where all their children have Quantity/Stock = 0 (for all children). Display this list on the screen (Parent_ID, child count, and child Product_IDs if available), then remove the entire family (parent row if present and all children) from the file.

7. Additional step — smallest-size-only families
   - Find all parents where the only children with Quantity/Stock > 0 are the smallest-size child(ren), and all larger-size children have 0 stock. (Treat "size" by parsing dimensions from Column C text, e.g., 6x6, 6 × 12, 6" x 12; if size cannot be determined for any child in a family, skip that parent.) Display this list on the screen (Parent_ID, child count, smallest child Product_IDs, and non-smallest child Product_IDs if available), then remove the entire family (parent row if present and all children) from the file.

Report:
- Number of parents (families) removed by this rule.
- Total rows removed by this step.
- Display an inline summary table listing each removed parent with: Parent_ID, Child_Count, Min_Years, Max_Years (Top 25 inline; full list is optional and does NOT need to be saved as a file).

Outputs (ONE FILE ONLY)
- Save the final result as CSV (UTF-8) with a URL-safe filename: cleaned_filtered.csv (no spaces/parentheses).
- Do not create any other files. Do not overwrite my original upload.

Sanity checks to display:
- Confirm the keywords used and the threshold (= 0.4).
- Confirm you enforced exactly 4 children for the family-removal rule.
- Show counts: original → after keyword removals → after family removals.
- If headers didn't match expectations, explicitly state which columns you used for Product ID, Parent ID, and Column H.

Deliverables to show me:
- Counts at each stage.
- Top 25 removed parents inline (no second file).
- Download link for cleaned_filtered.csv.

Kickoff instruction (say this after I upload the file):
"Run the AGS cleanup (one-file mode) with the constants above (keywords = reserve, frit, stringers, noodles; exactly-4-children rule; Column H > 0.4). Produce cleaned_filtered.csv with counts and inline removed-parents summary."
```

### What Each Filtering Step Removes (Plain English)

1. **Open the file**
   - Nothing removed yet.

2. **Remove rows with unwanted words**
   - If Column C says **reserve, frit, stringers, noodles, pound, pack**, delete that row.
   - These are not sheet products that can be cut.

3. **Find the key columns**
   - Figure out which columns are Product ID, Parent ID, and Years-in-Stock (Column H). No deletes here.

4. **Group products into families**
   - A **family** = one parent and its children (sizes). No deletes yet.

5. **Remove "well-stocked" 4-child families**
   - If a family has **exactly 4 children** and **all 4** have **Years-in-Stock > 0.4**, delete the whole family (parent + kids).
   - These families don't need cutting because all sizes are well-stocked.

6. **Remove "all zero" families**
   - If **every child** in a family has **0 in stock**, delete the whole family.
   - Nothing to cut or manage.

7. **Remove "smallest-only" families**
   - If **only the smallest size** has stock and **all bigger sizes are 0**, delete the whole family.
   - You can't cut small pieces into bigger ones, so there's nothing we can do.

8. **Show a quick summary**
   - How many rows we started with, what we removed at each step, and examples of parents removed.

9. **Save one clean file**
   - Make **cleaned_filtered.csv**. Don't touch your original file.

### Example Filtering Results
From a typical run:
- **Original rows**: 1,410
- **After keyword removals**: 784 (removed 626 rows)
- **Parents removed by 4-children @ >0.4 rule**: 11 (removed 44 rows)
- **Parents removed as zero-stock families**: 21 (removed 84 rows)
- **Parents removed as smallest-size-only families**: 4 (removed 16 rows)
- **Final rows**: 640

---

## Work Order Generation Process

### Objective
Generate cutting instructions that:
1. Keep every child SKU in stock (no zeros)
2. Balance Years in Stock across the four sizes as closely as possible
3. Use the fewest cuts necessary
4. Account for sales patterns (prioritize popular sizes)

### Cutting Strategy Rules

#### General Principle
- It's acceptable for **24"x24"** (and similar large sizes like 24"x22") to reach **0 inventory** if cutting it increases smaller-size Years-in-Stock toward the target.
- Sales data shows only 5.9% of units sold are 24"x24", so depleting large sheets to stock smaller sizes aligns with demand.

#### Cut-Down Priority
When balancing inventory:
1. Identify sizes with **lowest YIS** (undersupplied)
2. Identify sizes with **highest YIS** (oversupplied)
3. Cut from larger to smaller, targeting the most undersupplied sizes
4. Repeat until YIS are balanced (within ±0.05–0.10 of each other)

#### Guardrails (when NOT to zero out large sheets)
- **Open orders / known demand** for 24"x24" (don't cut below what you need to fulfill)
- **Lead time risk**: if resupply is slow/unreliable, keep 1–2 sheets minimum
- **Margin / freight**: if 24"x24" has unique margin or shipping benefits
- **Special products** (rare colors/textures) where full sheets matter

### Example Work Order: Parent 156660

**Parent**: Oceanside Glass Almond Opalescent 3mm COE96
**Children**:
- 156661: 6"x6"
- 156662: 6"x12"
- 156663: 12"x12"
- 156664: 24"x24"

**Current Stock Analysis**:
- 6"x6" (156661): 0 in stock (out of stock)
- 6"x12" (156662): 0 in stock (out of stock)
- 12"x12" (156663): 3 in stock
- 24"x24" (156664): 1 in stock

**Recommended Cutting Instructions**:
```
For product 156660, please cut it like this:
- From child 156663 (12"x12") → cut 1 into 4 pieces of child 156661 (6"x6")
- From child 156663 (12"x12") → cut 1 into 2 pieces of child 156662 (6"x12")
```

**Result After Cutting**:
- 6"x6": 4 in stock (improved from 0)
- 6"x12": 2 in stock (improved from 0)
- 12"x12": 1 in stock (reduced from 3)
- 24"x24": 1 in stock (unchanged)
- **All sizes now have stock** and YIS is more balanced

### Shop-Floor Work Order Format

When providing instructions to cutters, use this simple format:

```
WORK ORDER
Parent ID: 156660
Product: Oceanside Glass Almond Opalescent 3mm COE96

CUTTING INSTRUCTIONS:
Step 1: Cut 1× 12"x12" → 4× 6"x6"
Step 2: Cut 1× 12"x12" → 2× 6"x12"

INVENTORY PULLS NEEDED:
- Pull 2 sheets of 12"x12" (Product ID: 156663)

EXPECTED RESULTS:
- Produce 4 pieces of 6"x6" (Product ID: 156661)
- Produce 2 pieces of 6"x12" (Product ID: 156662)
```

---

## Size Detection & Analysis

### Python Logic for "Largest Size per Parent"

The system uses regex pattern matching to extract dimensions from product names:

**Detection Strategy**:
1. Detect WxH patterns like "24x22", '24"x22"', '24 in x 22 in'
2. Else take two largest inch-marked numbers (24", 22 in)
3. Else take top two numeric tokens
4. Else single number → n × n

**Normalization**:
- Labels formatted as 'A"×B"' with A ≥ B
- Example: both "6×12" and "12×6" become "12"×6""
- Integers formatted without decimals (24 not 24.0)

**Area Calculation**:
- Area = width × height
- Used to rank sizes within a family
- Largest area = largest size

### Identified Largest Sizes for Oceanside Glass
From the current inventory:
- **24"×24"** (most common full sheet)
- **24"×22"** (alternate full sheet)

**Note**: Only 2 distinct "largest sizes" were found across all Oceanside parent products.

---

## Testing & Validation

### Duplicate Detection
The system identifies duplicate child picks within the same parent.

**Example Issue Found**:
- Donor child 154199 appeared twice in picks
- If total of 5 sheets needed, should be listed once (quantity: 5), not twice
- **Resolution**: Combine duplicate picks for same child product

### Zero Inventory on Largest Size
**Question**: How many parents have 0 purchased/0 stock in the largest size?

**Analysis Approach**:
1. Identify largest size for each parent (by area calculation)
2. Check if that size has Purchased = 0 or Quantity = 0
3. Flag these families for potential cutting strategy

**Business Decision**:
- It's acceptable to have 0 inventory on largest size if it optimizes smaller size availability
- Sales patterns support this (only 5.9% of sales are full sheets)

---

## Implementation Workflow

### For Each Work Order Generation:

1. **Upload Source File**
   - Export from inventory system (Excel or CSV)
   - Include columns: Product_ID, Products_Parent_Id, Product_Name, Quantity_in_Stock, Years_in_Stock, Purchased

2. **Run Data Cleanup**
   - Apply master prompt to filter data
   - Review removal summaries (keywords, well-stocked families, zero-stock families, smallest-only families)
   - Download cleaned_filtered.csv

3. **Generate Cutting Analysis**
   - For each remaining parent with imbalanced YIS:
     - Calculate current YIS by size
     - Identify undersupplied sizes (low YIS)
     - Identify oversupplied sizes (high YIS)
     - Generate optimal cutting plan

4. **Create Work Orders**
   - Format cutting instructions for shop floor
   - Include parent ID, child IDs, step-by-step cuts
   - Show before/after inventory levels
   - Show before/after YIS metrics

5. **Execute Cuts**
   - Print work orders for cutting team
   - Pull inventory as specified
   - Perform cuts in order listed
   - Update inventory system with new quantities

6. **Verify Results**
   - Confirm no products at 0 inventory (goal achieved)
   - Check YIS balance across sizes
   - Monitor next period sales to validate strategy

---

## Key Definitions

- **Parent**: Main product entry representing all size variants
- **Child**: Specific size variant under a parent (e.g., 6"×6", 24"×24")
- **Family**: Parent + all its children
- **Years in Stock (YIS)**: On-hand Quantity ÷ Annual Units Sold
- **Cutting**: Process of reducing larger glass sheets into smaller sizes
- **Kerf**: Width of material removed by saw blade (not yet accounted for in ideal yields)
- **Donor Child**: The size being cut (source)
- **Target Child**: The size being produced (result)

---

## Future Enhancements

### Kerf & Trim Accounting
Currently using ideal yields. To implement real-world yields:
- Add kerf parameter (e.g., 0.125" per cut)
- Add trim margin (e.g., 0.25" per edge)
- Recalculate yields: `floor((effective_size + kerf) / (piece_size + kerf))`

**Example Impact**:
- Ideal: 24"×24" → 8× 6"×12"
- Real (kerf=0.125", trim=0.25"): May reduce to 7× 6"×12" or require layout optimization

### Target YIS Configuration
Allow user to specify target Years in Stock by size:
- Global target (e.g., 0.35 for all sizes)
- Size-specific targets (e.g., 0.40 for 24"×24", 0.30 for 6"×6")
- Seasonal adjustments

### Mixed Cutting Strategies
Optimize for mixed cuts from single sheet:
- Example: 1× 24"×24" → 2× 12"×12" + 8× 6"×6"
- Requires 2D bin packing algorithm
- More complex but can reduce waste

### Multi-Manufacturer Support
Current process is Oceanside-focused. To expand:
- Bullseye (17"×20" sheets → 10"×10", 5"×10", 5"×5")
- Spectrum (different size matrix)
- Wissmach (different size matrix)
- Each needs distinct cutting rule sets

### Open Order Integration
Before zeroing out large sheets, check:
- Pending customer orders
- Required fulfillment quantities
- Reserved inventory
- Lead time to next shipment

---

## Appendix: Example ChatGPT Prompts

### For Specific Parent Analysis
```
How would you recommend cutting parent 156660?
```

### For Work Order Generation
```
Please generate a work order for parent 156660 showing:
1. Current stock and YIS by size
2. Step-by-step cutting instructions
3. Projected stock and YIS after cuts
```

### For Batch Processing
```
Generate work orders for all parents in cleaned_filtered.csv where:
- At least one child has YIS < 0.25 (undersupplied)
- At least one child has YIS > 0.50 (oversupplied)
- Cutting can balance YIS within ±0.10
```

---

## Document History
- **Created**: Based on 4 ChatGPT conversation exports dated 2025-10-22
- **Purpose**: Comprehensive reference for AGS glass cutting work order generation
- **Scope**: Oceanside Glass and Tile (primary), Bullseye (secondary)
- **Status**: Ready for implementation and testing

---

*End of Document*
