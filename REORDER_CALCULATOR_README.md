# Reorder Calculator - CSV-Based Decision Engine

**Status:** ✅ Implementation Complete - Ready for Testing
**Created:** 2026-01-01
**Location:** `render-tidb-sync/reports_viewer/`

---

## 📋 Overview

The Reorder Calculator is a CSV-based system that applies decision tree logic to calculate reorder quantities for products. It supports:

- ✅ CSV upload (no manufacturer table dependency)
- ✅ Automated reorder quantity calculations
- ✅ Clarification questions when logic is unclear
- ✅ Manual edit tracking for continuous improvement
- ✅ Oceanside Glass rules (0.35 years target)

---

## 🏗️ Architecture

```
User uploads CSV (without reorder_quantity column)
       ↓
Flask processes CSV → SQLite temp database
       ↓
Decision engine calculates reorder quantities
       ↓
Questions generated (if needed) → Client answers
       ↓
Export CSV with calculated reorder_quantity column
       ↓
User can edit manually → Re-upload to track changes
```

---

## 📁 Files Created

### Core System
```
render-tidb-sync/
├── reports_viewer/
│   ├── __init__.py                     # Blueprint initialization
│   ├── routes.py                       # Flask routes (9 endpoints)
│   ├── database.py                     # Database helper functions
│   ├── schema.sql                      # Database schema (4 tables)
│   ├── decision_engine/
│   │   ├── __init__.py
│   │   ├── base_calculator.py          # Base class for all calculators
│   │   └── oceanside_calculator.py     # Oceanside-specific logic (0.35yr target)
│   └── templates/
│       ├── reorder_upload.html         # CSV upload page
│       ├── reorder_questions.html      # Clarification questions
│       ├── reorder_download.html       # Download results page
│       └── reorder_audit.html          # Manual edits log
├── temp_sessions/                      # SQLite DBs for each session
├── init_reorder_schema.py             # Database initialization script
└── unified_app.py                      # ✅ Updated (blueprint registered)
```

### Modified Files
- `unified_app.py` - Added Reports Viewer blueprint registration
- `requirements.txt` - Added `pandas>=2.0.0`

---

## 🗄️ Database Schema

**Location:** Agent Garden Database (PostgreSQL)

**Tables Created:**
1. `reorder_sessions` - Calculation sessions
2. `reorder_questions` - Clarification questions
3. `reorder_manual_edits` - Audit log for manual changes
4. `reorder_decision_learning` - Track questions for future automation

---

## 🚀 Deployment Instructions

### Step 1: Initialize Database Schema

```bash
cd render-tidb-sync
python init_reorder_schema.py
```

This creates the 4 required tables in the Agent Garden database.

### Step 2: Commit & Push to Git

```bash
cd render-tidb-sync
git add .
git commit -m "Add Reorder Calculator - CSV-based decision engine

- Implemented Oceanside Glass calculator (0.35 years target)
- Created Flask blueprint with upload/questions/download workflow
- Added 4 database tables for sessions, questions, edits, learning
- Integrated with Agent Garden database
- Created beautiful HTML templates with drag-drop upload

🤖 Generated with Claude Code
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

git push
```

### Step 3: Deploy to Render

Render will automatically deploy when you push to the main branch.

**Verify deployment:**
```
✅ https://gpt-mcp.onrender.com/reports/reorder-calculator
```

---

## 🧪 Testing Instructions

### Test 1: Basic Upload (377 Products)

1. **Navigate to:**
   ```
   https://gpt-mcp.onrender.com/reports/reorder-calculator
   ```

2. **Upload CSV:**
   - File: `Production/Edhoy Warehouse Cutsheet for Shawn - Sheet1.csv`
   - Manufacturer: Oceanside Glass (default)

3. **Expected Result:**
   - Processing completes in 5-10 seconds
   - Redirects to questions page (if any) OR download page
   - Should calculate reorder quantities for products with `Years_in_Stock < 0.35`

### Test 2: Verify Calculations

**Sample Product (from CSV line 2):**
- Product: "Oceanside Glass Almond Opalescent Frit COE96 - Medium Grain"
- Purchased: 15 units/year
- Quantity in Stock: 6 units
- Years in Stock: 6/15 = 0.4 years

**Expected Calculation:**
- Since 0.4 >= 0.35 (target), reorder_quantity should be **0** (no reorder needed)

**Sample Product (from CSV line 4):**
- Product: "Oceanside Glass Almond Opalescent, 3mm COE96 - Size 6"×12""
- Purchased: 5 units/year
- Quantity in Stock: 0 units (ZERO STOCK!)
- Years in Stock: 0/5 = 0 years

**Expected Calculation:**
- Target: 0.35 years × 5 units/year = 1.75 units
- Deficit: 1.75 - 0 = 1.75 units
- Reorder Quantity: **2 units** (rounded up)
- Reason: "URGENT: Zero stock, needs 2 units to reach 0.35 years"

### Test 3: Question Flow

Products with `Purchased = 0` (never sold) should generate HIGH priority questions:

**Expected Question:**
- Priority: HIGH
- Question: "Product '...' has never sold. Should we stock it?"
- Suggested Answer: "No (wait for first sale)"

### Test 4: Download CSV

After processing, download the CSV and verify:

**New Columns Added:**
- `Years_in_Stock` - Calculated metric
- `Reorder_Quantity` - Calculated reorder amount
- `Reorder_Reason` - Explanation for calculation
- `Calculation_Details` - JSON with breakdown

---

## 📊 Decision Tree Logic (Oceanside)

**Source:** `Production/wiki/02_Business_Rules/Years_In_Stock_Thresholds.md`

**Thresholds:**
- **Target:** 0.35 years (128 days)
- **Lean:** 0.20 years (73 days)
- **Well-Stocked:** 0.40 years (146 days)

**Formula:**
```python
years_in_stock = quantity_in_stock / purchased

if years_in_stock >= 0.35:
    reorder_quantity = 0  # Already at target
else:
    target_quantity = purchased * 0.35
    deficit = target_quantity - quantity_in_stock
    reorder_quantity = math.ceil(deficit)  # Round up
```

**Special Cases:**
1. **Purchased = 0** → Generate question (no sales history)
2. **Quantity = 0** → Mark as URGENT
3. **Reorder > 2 years worth** → Generate MEDIUM priority question

---

## 🔌 API Endpoints

**Base URL:** `https://gpt-mcp.onrender.com/reports`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/reorder-calculator` | Upload page |
| POST | `/reorder-calculator/upload` | Process CSV |
| GET | `/reorder-calculator/questions/<session_id>` | Show clarification questions |
| POST | `/reorder-calculator/submit-answers/<session_id>` | Submit answers |
| GET | `/reorder-calculator/download/<session_id>` | Download page with preview |
| GET | `/reorder-calculator/export/<session_id>` | Export final CSV |
| GET | `/reorder-calculator/audit/<session_id>` | Manual edits log |

---

## 🐛 Troubleshooting

### Error: "Missing required columns"
**Solution:** Ensure CSV has these columns:
- `Product_Name`
- `Product_ID`
- `Purchased`
- `Quantity_in_Stock`

### Error: "Database not configured"
**Solution:** Run `python init_reorder_schema.py` to create tables

### Error: "Session not found"
**Solution:** Sessions expire after download. Re-upload CSV.

### Calculations seem wrong
**Verification Steps:**
1. Check `Purchased` column (should be annual units sold)
2. Verify `Years_in_Stock` = `Quantity_in_Stock` / `Purchased`
3. Check target threshold (Oceanside = 0.35 years)
4. Review `Calculation_Details` column in exported CSV

---

## 🔮 Future Enhancements

### Phase 2 (Not Yet Implemented)
- [ ] Bullseye Glass calculator (0.25/0.40 thresholds, cascade logic)
- [ ] Color De Verre calculator (multiples of 5, minimum 10 if zero)
- [ ] Cutting opportunity detection (parent/child analysis)
- [ ] Answer incorporation (recalculate when client provides clarifications)
- [ ] Session listing page (view all past calculations)

### Phase 3 (Advanced)
- [ ] Excel export with formatting (color-coded cells)
- [ ] Email delivery (automated daily reports)
- [ ] Historical trend tracking
- [ ] Automated decision rule learning (convert repeated questions → rules)

---

## 📞 Support

**Issues:** Report bugs or request features via GitHub issues
**Documentation:** See `Production/wiki/` for business rules
**Architecture:** See CLAUDE.md Section 9 for Decision Validation system design

---

**Last Updated:** 2026-01-01
**Implementation Time:** ~5 hours
**Status:** ✅ Ready for Production Testing
