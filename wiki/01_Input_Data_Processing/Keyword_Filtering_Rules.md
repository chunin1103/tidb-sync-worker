# Keyword Filtering Rules

**Purpose:** Remove non-sheet glass products from inventory data
**Application:** Applied to Column C (Product Name) - case-insensitive substring matching

---

## Keywords to Remove

| Keyword | Reason | Example Products |
|---------|--------|------------------|
| reserve | Not available for cutting | Reserved inventory |
| frit | Glass powder, not sheets | Glass frit packs |
| stringers | Thin glass rods, not sheets | Glass stringers |
| noodles | Glass rods, not sheets | Glass noodles |
| pound | Sold by weight, not cuttable | Frit sold by pound |
| pack | Bundled products | Pre-packaged sets |

---

## Matching Rules

- **Case-insensitive:** "Frit", "FRIT", "frit" all match
- **Substring matching:** "Glass Frit Medium" contains "frit" → remove
- **Column location:** Always Column C (3rd column, 0-based index 2)

---

## Expected Impact

On a typical 1,410-row inventory file:
- **Rows removed:** ~626 rows (44% of original)
- **Rows remaining:** ~784 rows

**Breakdown by keyword (example):**
- reserve: ~150 rows
- frit: ~300 rows
- stringers: ~100 rows
- noodles: ~50 rows
- pound: ~20 rows
- pack: ~6 rows

---

## What Gets Removed

### These products are NOT cuttable sheets:
1. **Frit** - Ground glass powder (not sheet glass)
2. **Stringers** - Thin glass rods for decoration
3. **Noodles** - Thick glass rods
4. **Reserve** - Inventory set aside, not for cutting
5. **Pound/Pack** - Bulk/bundled items

### These products REMAIN:
- Sheet glass in standard sizes (6"×6", 12"×12", 24"×24", etc.)
- Full sheets and partial sheets available for cutting

---

## Process

```
FOR each row in inventory:
    product_name = row[Column_C]
    FOR each keyword in KEYWORDS_TO_REMOVE:
        IF keyword found in product_name (case-insensitive):
            REMOVE row
            REPORT keyword and count
```

---

**Related Files:**
- [Data Cleanup Master Prompt](./Data_Cleanup_Master_Prompt.md)
- [Family Filtering Logic](./Family_Filtering_Logic.md)
