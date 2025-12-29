# Size Detection & Analysis Workflow

**Purpose:** Parse product names to extract glass dimensions and classify size categories
**Applies to:** All glass systems (Oceanside COE96, Bullseye COE90)
**Last Updated:** 2025-12-21

---

## 📋 Overview

Product names contain size information in various formats (e.g., "6x6", "6 × 12", "6\" x 12\"", "17x20"). This workflow extracts dimensions, validates them, and classifies products into size categories for cutting decisions.

---

## 🎯 Size Detection Decision Tree

```mermaid
graph TD
    A[Product Name String<br/>Column C] --> B[Extract Dimension Pattern]

    B --> C{Pattern Match?}
    C -->|Regex: \\d+\\s*[xX×]\\s*\\d+| D[Parse Numbers]
    C -->|Regex: \\d+\"\\s*x\\s*\\d+\"| D
    C -->|No Match| E[Check Fallback Patterns]

    D --> F{Valid Dimensions?}
    F -->|Yes - Two Numbers| G[Calculate Size Category]
    F -->|No - Invalid Format| E

    E --> H{Keyword Match?}
    H -->|Full, Full Sheet| I[Assign: Full Sheet]
    H -->|Half, Half Sheet| J[Assign: Half Sheet]
    H -->|No Keywords| K[Flag: SIZE_UNKNOWN]

    G --> L{Classify by Dimensions}
    I --> M[Record: System Default Full]
    J --> N[Record: System Default Half]

    L -->|Oceanside COE96| O{Match Standard Sizes?}
    L -->|Bullseye COE90| P{Match Standard Sizes?}

    O -->|24×24 or 24×22| Q[Category: FULL]
    O -->|12×12| R[Category: HALF]
    O -->|6×12| S[Category: QUARTER]
    O -->|6×6| T[Category: SMALL]
    O -->|Non-standard| U[Category: CUSTOM<br/>Flag for Review]

    P -->|17×20 or 20×35| V[Category: FULL]
    P -->|10×10| W[Category: MEDIUM]
    P -->|5×10| X[Category: SMALL]
    P -->|5×5| Y[Category: TINY]
    P -->|Half variants| Z[Category: HALF<br/>Check exact dimensions]
    P -->|Non-standard| U

    M --> AA[Lookup System Defaults]
    N --> AA
    K --> AB[Manual Review Queue]
    Q --> AC[Size Classification Complete]
    R --> AC
    S --> AC
    T --> AC
    U --> AB
    V --> AC
    W --> AC
    X --> AC
    Y --> AC
    Z --> AC

    AA --> AC
    AB --> AD[Flag in Output]
    AC --> AE{Sort Order Needed?}
    AE -->|Yes| AF[Assign Sort Priority<br/>Largest=1, Smallest=4+]
    AE -->|No| AG[Classification Complete]
    AF --> AG

    style AC fill:#90EE90
    style K fill:#FFB6C1
    style U fill:#FFD700
    style AB fill:#FFA500
    style AG fill:#87CEEB
```

---

## 📏 Size Pattern Matching

### Primary Regex Patterns

#### Pattern 1: Basic Dimension Format
```regex
\d+\s*[xX×]\s*\d+
```
**Matches:**
- `6x6` → [6, 6]
- `12 x 12` → [12, 12]
- `24×24` → [24, 24]
- `17x20` → [17, 20]

#### Pattern 2: Inch Notation
```regex
\d+"\s*x\s*\d+"
```
**Matches:**
- `6" x 6"` → [6, 6]
- `12" x 12"` → [12, 12]

#### Pattern 3: Full Dimension with Units
```regex
(\d+\.?\d*)\s*(?:inches?|in|\")\s*[xX×]\s*(\d+\.?\d*)\s*(?:inches?|in|\")
```
**Matches:**
- `6 inches x 12 inches` → [6, 12]
- `10in x 10in` → [10, 10]

### Fallback Keywords

When regex patterns fail, check for these keywords:

| Keyword | Interpretation | System Default |
|---------|----------------|----------------|
| "Full Sheet", "Full" | Maximum size for system | Oceanside: 24×24<br/>Bullseye: 17×20 or 20×35 |
| "Half Sheet", "Half" | Half size for system | Oceanside: 12×12<br/>Bullseye: Various |
| "Quarter" | Quarter size | Oceanside: 6×12 |
| "Scrap" | Not a standard size | Flag: NON_CUTTABLE |
| "Sheet" (alone) | Ambiguous | Flag: SIZE_UNKNOWN |

---

## 📊 Size Classification Tables

### Oceanside COE96 Standard Sizes

| Dimensions | Category | Sort Priority | Cutting Yield | Sales % |
|------------|----------|---------------|---------------|---------|
| 24×24 | FULL | 1 | Source sheet | 5.9% |
| 24×22 | FULL_ALT | 1 | Source sheet | Rare |
| 12×12 | HALF | 2 | 4 from FULL | 47.5% |
| 6×12 | QUARTER | 3 | 2 from HALF<br/>8 from FULL | 25.1% |
| 6×6 | SMALL | 4 | 4 from HALF<br/>16 from FULL | 21.5% |

**Key Insights:**
- 94% of sales are ≤12×12
- FULL sheets can be cut to zero for optimization

### Bullseye COE90 Standard Sizes

| Dimensions | Category | Sort Priority | Cutting Yield | Notes |
|------------|----------|---------------|---------------|-------|
| 20×35 | FULL_LARGE | 1 | Source sheet | Rare, special order |
| 17×20 | FULL | 1 | Source sheet | Standard full |
| 10×10 | MEDIUM | 2 | 4 from FULL + scrap | Popular size |
| 5×10 | SMALL | 3 | 2 from FULL + scrap | Common |
| 5×5 | TINY | 4 | 4 from 10×10 | Smallest standard |
| Half (various) | HALF | 1.5 | Multiple configs | Requires exact dimensions |

**Special Cases:**
- **3mm Half Sheet:** Can be combined (2 Half = 1 Full equivalent)
- **Full Sheet:** Never cut to zero (needed for cascade logic)
- **Scrap:** Sold separately, not part of cutting calculations

---

## 🔧 Size Detection Algorithm

### Step-by-Step Process

#### 1. Extract Candidate String
```python
# Pseudo-code
product_name = row['Column_C']  # e.g., "Oceanside Glass Almond Opalescent 3mm 6x12 COE96"
candidate = product_name.strip().lower()
```

#### 2. Apply Regex Patterns in Order
```python
patterns = [
    r'(\d+\.?\d*)\s*[xX×]\s*(\d+\.?\d*)',  # Primary
    r'(\d+)\"\s*x\s*(\d+)\"',              # Inch notation
    r'(\d+\.?\d*)\s*(?:in|inches)\s*[xX×]\s*(\d+\.?\d*)\s*(?:in|inches)'  # Full units
]

for pattern in patterns:
    match = regex.search(pattern, candidate)
    if match:
        width, height = match.groups()
        return parse_dimensions(width, height)
```

#### 3. Fallback to Keyword Search
```python
keywords = {
    'full sheet': 'FULL',
    'full': 'FULL',
    'half sheet': 'HALF',
    'half': 'HALF',
    'scrap': 'NON_CUTTABLE'
}

for keyword, category in keywords.items():
    if keyword in candidate:
        return lookup_system_default(category, system_type)
```

#### 4. Handle Unknown Sizes
```python
if size_not_detected:
    flag_for_manual_review(row)
    return 'SIZE_UNKNOWN'
```

---

## ⚠️ Edge Cases and Validation

### Common Issues

#### Issue 1: Non-standard Dimensions
**Example:** "Oceanside Glass 6.5x12.5 Custom Cut"
**Action:** Flag as CUSTOM, add to manual review queue
**Reason:** Not a standard cutting yield size

#### Issue 2: Multiple Dimensions in Name
**Example:** "Glass Pack 6x6, 6x12, 12x12 Assortment"
**Action:** Flag as MULTI_SIZE, skip size detection
**Reason:** Ambiguous which size applies

#### Issue 3: Imperial vs Metric
**Example:** "300mm x 300mm" vs "12x12"
**Action:** Convert metric to inches (300mm ≈ 11.8" → Round to 12")
**Validation:** Check if result matches standard size

#### Issue 4: Aspect Ratio Mismatch
**Example:** Product claims "6x6" but inventory shows "6x8"
**Action:** Flag as SIZE_MISMATCH
**Resolution:** Manual verification needed

### Validation Rules

After size detection, validate:

1. **Dimensions are positive numbers**
   ```python
   if width <= 0 or height <= 0:
       flag_invalid()
   ```

2. **Dimensions are within reasonable range**
   ```python
   if width > 48 or height > 48:  # No glass sheets larger than 48"
       flag_suspicious()
   ```

3. **Aspect ratio makes sense**
   ```python
   ratio = max(width, height) / min(width, height)
   if ratio > 4:  # e.g., 6x30 is suspicious
       flag_review()
   ```

4. **Matches system-specific sizes**
   ```python
   if system == 'Oceanside':
       valid_sizes = [(24,24), (24,22), (12,12), (6,12), (6,6)]
       if (width, height) not in valid_sizes:
           flag_nonstandard()
   ```

---

## 📈 Sort Priority Assignment

### Priority Calculation

**Rule:** Larger sheets get lower priority numbers (cut first)

```python
def assign_sort_priority(category, system):
    oceanside_priority = {
        'FULL': 1,
        'HALF': 2,
        'QUARTER': 3,
        'SMALL': 4
    }

    bullseye_priority = {
        'FULL_LARGE': 1,
        'FULL': 1,
        'HALF': 1.5,  # Between full and medium
        'MEDIUM': 2,
        'SMALL': 3,
        'TINY': 4
    }

    return oceanside_priority.get(category) if system == 'Oceanside' else bullseye_priority.get(category)
```

**Usage in Work Orders:**
Sort cutting instructions by priority (1 → 4) so largest sheets are cut first.

---

## 🔗 Related Workflows

- **Used by:** [Work Order Generation Process](./Work_Order_Generation_Process.md)
- **Used by:** [Inventory Filtering Workflow](./Inventory_Filtering_Workflow.md) (for smallest-size-only rule)
- **Business Rules:** [Glass Sizes and Cutting Yields](../02_Business_Rules/Glass_Sizes_and_Cutting_Yields.md)
- **Reference:** [Common Errors Reference](../06_Reference_Data/Common_Errors.md) (for size detection failures)

---

## 📊 Example Detection Results

### Example 1: Standard Oceanside Product
**Input:** "Oceanside Glass Almond Opalescent 3mm 6x12 COE96"
**Detection:**
- Pattern match: `6x12` → [6, 12]
- System: Oceanside COE96
- Category: QUARTER
- Sort Priority: 3
- **Result:** ✅ Valid, standard size

### Example 2: Bullseye Full Sheet
**Input:** "Bullseye Glass 0100 Black Opal 3mm Full Sheet COE90"
**Detection:**
- Regex: No dimension found
- Keyword: "Full Sheet" detected
- System: Bullseye COE90
- Default: 17×20 (standard full)
- Category: FULL
- Sort Priority: 1
- **Result:** ✅ Valid, using fallback

### Example 3: Ambiguous Size
**Input:** "Oceanside Glass Sample Pack Mixed Sizes"
**Detection:**
- Regex: No dimension found
- Keyword: No match
- **Result:** ⚠️ FLAG: SIZE_UNKNOWN → Manual review

### Example 4: Non-Standard Custom
**Input:** "Bullseye Custom Cut 8.5x11 Special Order"
**Detection:**
- Pattern match: `8.5x11` → [8.5, 11]
- System: Bullseye COE90
- Validation: Not in standard sizes list
- Category: CUSTOM
- **Result:** ⚠️ FLAG: NON_STANDARD → Manual review queue

---

## 💡 Best Practices

### When to Skip Size Detection
- Product name contains "Pack", "Assortment", "Kit", "Mixed"
- Product is frit, powder, stringers (already filtered)
- Product is scrap or remnant
- Product name is ambiguous (e.g., just "Glass Sheet")

### When to Force Manual Review
- Dimensions detected but don't match any standard size
- Multiple dimension patterns found in same name
- Aspect ratio > 4:1 (suspiciously long/narrow)
- Size units are metric (verify conversion)

### Improving Detection Accuracy
1. **Standardize product naming:** Use consistent format (e.g., "Product Name Size mm COE")
2. **Maintain size lookup table:** Map non-standard sizes to nearest standard equivalent
3. **Log detection failures:** Track which patterns aren't matching to improve regex
4. **Manual review stats:** If >10% need review, naming convention needs improvement

---

**Governance:** CLAUDE.md "Decision Tree First" Rule ✓
**Format:** Mermaid flowchart + markdown tables + code examples
**Cross-referenced:** 4 related documents
