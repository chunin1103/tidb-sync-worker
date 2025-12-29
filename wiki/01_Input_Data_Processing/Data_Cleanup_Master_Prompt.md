# Data Cleanup Master Prompt

**Source:** Comprehensive Glass Cutting Process (Oceanside Glass System)
**Purpose:** Standard prompt for filtering and cleaning inventory data before generating work orders

---

## Master Prompt Template

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

---

## Expected Results

### Typical Filtering Summary
From a standard inventory file run:
- **Original rows**: 1,410
- **After keyword removals**: 784 (removed 626 rows)
- **Parents removed by 4-children @ >0.4 rule**: 11 (removed 44 rows)
- **Parents removed as zero-stock families**: 21 (removed 84 rows)
- **Parents removed as smallest-size-only families**: 4 (removed 16 rows)
- **Final rows**: 640

---

## Output File

**Filename:** `cleaned_filtered.csv`
**Format:** UTF-8 CSV
**Location:** Do not overwrite original upload

---

**Related Files:**
- [Keyword Filtering Rules](./Keyword_Filtering_Rules.md)
- [Family Filtering Logic](./Family_Filtering_Logic.md)
- [../../03_Decision_Workflows/Inventory_Filtering_Workflow.md](../03_Decision_Workflows/Inventory_Filtering_Workflow.md)
