# Reorder Quantity Calculation Summary

## File Information
- **Input File**: `make a cutsheet first complete test 10-22-25.csv`
- **Output File**: `UPDATED_make_a_cutsheet_with_reorder.csv`
- **Date Processed**: December 3, 2025

## Calculation Method

### Target Years in Stock (YIS)
**Target**: 0.35 years (4.2 months of supply)

### Formula Used
```
For each product with sales history (YIS > 0):

1. Annual_Sales = Quantity_in_Stock / Years_in_Stock
2. Target_Quantity = Annual_Sales × 0.35
3. Reorder_Quantity = max(0, Target_Quantity - Quantity_in_Stock)
```

### Filters Applied
- **Keywords removed**: "reserve", "frit", "stringers", "noodles", "pound", "pack"
- **Only child products**: Products with Products_Parent_Id ≠ 0
- **Only products with sales history**: Years_in_Stock > 0

## Results Summary

### Overall Statistics
- **Total products in file**: 1,410
- **Child products analyzed**: 784
- **Products needing reorder**: 124
- **Total reorder quantity**: 278.01 units

### Top 15 Products Requiring Reorder

| Product_ID | Size | Current Stock | YIS | Reorder Qty |
|------------|------|---------------|-----|-------------|
| 165105 | 12"x12" | 37 | 0.16 | 43.94 |
| 169634 | 12"x12" | 1 | 0.03 | 10.67 |
| 158871 | 12"x12" | 9 | 0.18 | 8.50 |
| 165405 | 12"x12" | 1 | 0.04 | 7.75 |
| 158870 | 12"x6" | 1 | 0.04 | 7.75 |
| 16488 | 12"x6" | 1 | 0.04 | 7.75 |
| 172143 | 6"x6" | 2 | 0.09 | 5.78 |
| 180789 | 12"x12" | 2 | 0.09 | 5.78 |
| 16489 | 12"x12" | 3 | 0.13 | 5.08 |
| 154219 | 12"x12" | 2 | 0.10 | 5.00 |
| 156686 | 6"x6" | 1 | 0.06 | 4.83 |
| 16104 | 12"x12" | 1 | 0.06 | 4.83 |
| 16274 | 12"x12" | 3 | 0.14 | 4.50 |
| 16573 | 12"x6" | 1 | 0.07 | 4.00 |
| 153397 | 6"x6" | 1 | 0.07 | 4.00 |

### Cutting Opportunities Identified

**Total opportunities**: 65 families where larger sizes could be cut to supply smaller sizes

The analysis found 65 product families where:
- Larger size has Years_in_Stock > 0.40 (excess inventory)
- Smaller size has Reorder_Quantity > 0 (needs stock)
- Cutting could reduce reorder costs

## New Columns Added to CSV

1. **width** - Parsed width dimension from product name
2. **height** - Parsed height dimension from product name
3. **area** - Calculated area (width × height)
4. **size_label** - Normalized size label (e.g., "12\"x12\"")
5. **Reorder_Quantity** - Calculated reorder quantity (main output)
6. **Annual_Sales** - Calculated annual sales rate
7. **Target_Quantity** - Target quantity for 0.35 YIS
8. **Initial_Reorder** - Initial reorder before cutting optimization

## Key Insights

### Products with Highest Reorder Needs
- **Product 165105** (Thin Icicle Clear 12"x12") needs the most: 43.94 units
  - Current: 37 units, YIS: 0.16 (only 1.9 months supply)
  - This is a fast-moving product that needs immediate restocking

### Size Distribution of Reorders
Most reorders are for smaller sizes (6"x6", 6"x12", 12"x12"), which aligns with the sales distribution showing 94% of sales are smaller sizes.

### Cutting Optimization Opportunities
Before placing orders for 124 products totaling 278 units, review the 65 cutting opportunities to:
1. Reduce purchasing costs
2. Utilize existing inventory
3. Free up space from slow-moving large sheets

## Next Steps

1. **Review Cutting Opportunities**: Check which larger sizes can be cut instead of purchased
2. **Validate High-Priority Reorders**: Focus on products with YIS < 0.20 (less than 2.4 months supply)
3. **Consider Lead Times**: Factor in vendor lead times when placing orders
4. **Update Inventory System**: Import the Reorder_Quantity column into your ordering system

## File Location
The updated CSV file with all calculations is saved at:
`C:\ags workspace\UPDATED_make_a_cutsheet_with_reorder.csv`
