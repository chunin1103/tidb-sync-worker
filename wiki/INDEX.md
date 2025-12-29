# Production Wiki - Master Index

**Welcome to the Claude Tools Production Wiki**

This is your Single Source of Truth for all glass cutting systems, vendor ordering rules, and related tools.

**Last Updated:** 2025-12-21
**Governance:** See [../claude.md](../claude.md) for operating protocols

---

## Quick Navigation

### 🔧 By Workflow Stage

| Stage | What's Here | Navigate To |
|-------|-------------|-------------|
| **Input** | Data cleanup, filtering rules | [01_Input_Data_Processing/](./01_Input_Data_Processing/) |
| **Rules** | Business rules, vendor policies, thresholds | [02_Business_Rules/](./02_Business_Rules/) |
| **Decisions** | Flowcharts for complex workflows | [03_Decision_Workflows/](./03_Decision_Workflows/) |
| **Output** | Work orders, reports, formats | [04_Output_Generation/](./04_Output_Generation/) |
| **Systems** | Oceanside, Bullseye, FEIE, Wildcats, Passport | [05_System_Specific/](./05_System_Specific/) |
| **Reference** | Formulas, sample data, common errors | [06_Reference_Data/](./06_Reference_Data/) |
| **Archive** | Historical files, ChatGPT exports | [07_Archive/](./07_Archive/) |

---

## 📋 By System

### Glass Cutting Systems

#### Oceanside Glass COE96
**Path:** [05_System_Specific/Oceanside_Glass_System/](./05_System_Specific/Oceanside_Glass_System/)

- Ad-hoc cutting work orders
- Target YIS: 0.35 years (4.2 months)
- Sizes: 24"×24", 12"×12", 6"×12", 6"×6"
- **Start Here:** [Oceanside README](./05_System_Specific/Oceanside_Glass_System/README.md)

#### Bullseye Glass COE90
**Path:** [05_System_Specific/Bullseye_Glass_System/](./05_System_Specific/Bullseye_Glass_System/)

- **Two systems:** Cut Sheets (biweekly) + Ordering (~37 days)
- Target YIS: 0.25yr (min), 0.40yr (target)
- Sizes: 20"×35", 17"×20", 10×10, 5×10, 5×5
- **CRITICAL:** Cascade cutting logic (see README)
- **Start Here:** [Bullseye README](./05_System_Specific/Bullseye_Glass_System/README.md)
- **Full Documentation:** `C:\Users\tnguyen24_mantu\OneDrive\Claude Tools\Bullseye Glass\MASTER_CONTEXT_PROMPT.md`

---

### Other Systems

#### FEIE Tax Tracking
**Path:** [05_System_Specific/FEIE_Tax_Tracking/](./05_System_Specific/FEIE_Tax_Tracking/)
- Foreign Earned Income Exclusion tracking
- Physical Presence Test (330 days in any rolling 12-month period)
- Rolling window calculation (NOT calendar year!)
- When FEIE saves money (decision tree included)
- TaxBird integration for location data
- **Start Here:** [FEIE README](./05_System_Specific/FEIE_Tax_Tracking/README.md) ⭐ **COMPREHENSIVE**

#### Wildcats SEO Content
**Path:** [05_System_Specific/Wildcats_SEO_System/](./05_System_Specific/Wildcats_SEO_System/)
- AI-generated SEO product content for artglasssupplies.com
- 4-source competitor research workflow
- Content generation decision tree (Mermaid flowchart)
- Style guide: helpful tone, no superlatives, specific details
- Complete example with schema markup
- **Start Here:** [Wildcats README](./05_System_Specific/Wildcats_SEO_System/README.md) ⭐ **COMPREHENSIVE**

#### Passport Generation
**Path:** [05_System_Specific/Passport_Generation/](./05_System_Specific/Passport_Generation/)
- PDF generation from passport photos
- **Start Here:** [Passport README](./05_System_Specific/Passport_Generation/README.md)

---

## 📊 Key Workflows (Decision Trees)

All workflows follow **CLAUDE.md "Decision Tree First" Rule** - visualized with Mermaid flowcharts.

### High Priority Workflows

1. **[Inventory Filtering Workflow](./03_Decision_Workflows/Inventory_Filtering_Workflow.md)**
   - 7-step filtering process
   - Removes non-cuttable products
   - Identifies work order candidates

2. **[Reorder Calculation Workflow](./03_Decision_Workflows/Reorder_Calculation_Workflow.md)**
   - Calculate optimal reorder quantities
   - Target YIS: 0.35 years
   - Vendor-specific rules (CDV, Bullseye, Oceanside)

3. **[Vendor Order Decision Tree](./03_Decision_Workflows/Vendor_Order_Decision_Tree.md)**
   - Order from vendor OR cut from inventory?
   - Cost analysis
   - Guardrails and safety checks

---

## 📖 Business Rules

### Core Rules

- **[Years in Stock Thresholds](./02_Business_Rules/Years_In_Stock_Thresholds.md)**
  - System-specific thresholds (Oceanside vs Bullseye)
  - Calculation formulas
  - Interpretation guide

- **[Glass Sizes and Cutting Yields](./02_Business_Rules/Glass_Sizes_and_Cutting_Yields.md)**
  - Oceanside: 24"×24" → 12"×12" → 6"×12" → 6"×6"
  - Bullseye: Full → Half → 10×10 → 5×10 → 5×5
  - Cutting yields and cascade options

- **[Color De Verre Rules](./02_Business_Rules/Color_De_Verre_Rules.md)**
  - Order in multiples of 5
  - +10 units if zero stock
  - Dragonfly mold = always 100

---

## 🎯 Common Tasks

### Generate Oceanside Work Order
1. Start with [Inventory Filtering Workflow](./03_Decision_Workflows/Inventory_Filtering_Workflow.md)
2. Apply [Data Cleanup Master Prompt](./01_Input_Data_Processing/Data_Cleanup_Master_Prompt.md)
3. Calculate reorders using [Reorder Calculation Workflow](./03_Decision_Workflows/Reorder_Calculation_Workflow.md)
4. Review [Oceanside System README](./05_System_Specific/Oceanside_Glass_System/README.md)

### Generate Bullseye Cut Sheet
1. **Read FIRST:** `Bullseye Glass/MASTER_CONTEXT_PROMPT.md`
2. Check cascade opportunities (CRITICAL!)
3. Follow 5-step algorithm
4. See [Bullseye README](./05_System_Specific/Bullseye_Glass_System/README.md)

### Calculate Vendor Order
1. Review [Vendor Order Decision Tree](./03_Decision_Workflows/Vendor_Order_Decision_Tree.md)
2. Check cutting opportunities first
3. Apply vendor-specific rules (CDV, Bullseye, Oceanside)
4. Verify guardrails

---

## 📁 File Organization

```
Production/
├── claude.md (governance protocols)
├── wiki/
│   ├── INDEX.md (you are here!)
│   ├── 01_Input_Data_Processing/
│   ├── 02_Business_Rules/
│   ├── 03_Decision_Workflows/
│   ├── 04_Output_Generation/
│   ├── 05_System_Specific/
│   ├── 06_Reference_Data/
│   └── 07_Archive/
└── scripts/
```

---

## 🚨 Critical Reminders

### When Working on Bullseye
- **ALWAYS check cascade opportunities FIRST** (most common error!)
- 2 Half Sheets = 1 Full Sheet equivalent (3mm ONLY)
- Can only cascade DOWN (large→small), never UP
- Must verify Half Sheet in final check (≥ 0.40yr)

### When Working on Oceanside
- Target: 0.35 years (not 0.40!)
- 94% of sales are ≤12"×12" (OK to zero out 24"×24")
- Check cutting opportunities before ordering

### When Working on Color De Verre
- All orders in multiples of 5
- Add 10 units if zero stock
- Dragonfly mold: always 100 units

---

## 🔗 External Resources

### Full System Documentation (Outside Wiki)

| System | Location |
|--------|----------|
| Bullseye Glass | `C:\Users\tnguyen24_mantu\OneDrive\Claude Tools\Bullseye Glass\` |
| FEIE Tracking | `C:\Users\tnguyen24_mantu\OneDrive\Claude Tools\FEIE\` |
| Wildcats SEO | `C:\Users\tnguyen24_mantu\OneDrive\Claude Tools\Wildcats\` |
| Passport Gen | `C:\Users\tnguyen24_mantu\OneDrive\Claude Tools\passport\` |

---

## 📈 System Comparison Table

| System | Cycle | Min YIS | Target YIS | Priority |
|--------|-------|---------|------------|----------|
| **Oceanside** | Ad-hoc | 0.20yr (73d) | 0.35yr (128d) | Balance inventory |
| **Bullseye Cuts** | 14 days | 0.25yr (91d) | - | Get off zero |
| **Bullseye Orders** | 37 days | 0.25yr (91d) | 0.40yr (146d) | Reach 0.40 all sizes |

---

## 💡 Tips for Using This Wiki

### Before Starting ANY Task:
1. Read [../claude.md](../claude.md) for governance rules
2. Identify which system you're working on
3. Go to that system's README
4. Follow the workflow decision trees
5. Apply relevant business rules

### The "Decision Tree First" Rule:
Per CLAUDE.md governance:
- Processes with steps/conditions = **Mermaid flowchart** (highest priority)
- "If X, Then Y" scenarios = **Markdown table**
- Descriptions/context = **Text**

### Anti-Duplication Protocol:
Before creating new files:
1. **Scan** existing structure
2. **Verify** no duplicate exists
3. **Update** existing file (never create `filename_v2.md`)

---

## 📞 Getting Help

### Workflow Issues
- Check the relevant decision tree in [03_Decision_Workflows/](./03_Decision_Workflows/)
- Review business rules in [02_Business_Rules/](./02_Business_Rules/)

### System-Specific Questions
- Go to [05_System_Specific/](./05_System_Specific/)
- Read the system's README
- Check external documentation (for Bullseye, FEIE, etc.)

### Contradictions or Errors
- Flag them immediately (per CLAUDE.md "Be Critical" rule)
- Reference specific Wiki file names
- Ask for tie-breaker decision

---

**Maintained by:** Claude (System Architect)
**Governance:** CLAUDE.md "Decision Tree First" + "Anti-Duplication Protocol"
**Structure:** Organized by Workflow Stage (Input → Processing → Output)
