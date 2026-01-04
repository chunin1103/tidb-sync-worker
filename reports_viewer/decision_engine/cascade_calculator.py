"""
Bullseye Glass Cascade Calculator
Implements the full 5-step cascade algorithm for family-level ordering optimization.

Ported from: Bullseye Ordering/bullseye/scripts/analyze_reorder_needs.py v2.0

COMPLETE ALGORITHM:
1. CASCADE FROM INVENTORY FIRST - cut excess before ordering
2. CHECK 0.25yr THRESHOLD - decide if order needed
3. ORDER MINIMUM TO REACH 0.4yr - calculate sheets needed
4. CASCADE FROM ORDER - use surplus to cover smaller sizes
5. VERIFY ALL ABOVE 0.4yr - final check

CUTTING YIELDS:
- 3mm Full Sheet: 6x 10x10 + 2x 5x10
- 3mm: 2 Half Sheets = 1 Full equivalent (6x 10x10 + 2x 5x10)
- 2mm Half Sheet: 2x 10x10 + 2x 5x10

CASCADE OPTIONS (all thicknesses):
- 10x10 -> 2x 5x10
- 10x10 -> 4x 5x5
- 5x10 -> 2x 5x5
"""

import math
from typing import Dict, List, Tuple, Optional
from collections import defaultdict


# Configuration - matches REORDER_RULES.md
TARGET_YEARS = 0.40  # 146 days - order target
ORDER_THRESHOLD_YEARS = 0.25  # 91 days - triggers order decision
CRITICAL_DAYS = 28  # Below this is critical


def calc_years(stock: float, purchased: float) -> float:
    """Calculate years of stock on hand.

    Formula: years = stock / annual_sales
    Example: 6 units / 46 sales per year = 0.13 years
    """
    if purchased <= 0:
        return 999.0 if stock > 0 else 0.0
    return stock / purchased


def calc_min_stock(purchased: float, years: float) -> int:
    """Calculate minimum stock needed for given years coverage.

    Formula: min_stock = years_coverage * annual_sales
    Example: 0.40 years * 46 sales/year = 18.4 -> ceil = 19 units
    """
    if purchased <= 0:
        return 0
    return math.ceil(years * purchased)


def get_size_type(row: Dict) -> Optional[str]:
    """Determine the size type of the product."""
    name = str(row.get('Product_Name', '')).lower()
    model = str(row.get('Model', '')).lower()

    if 'half sheet' in name or 'halfsheet' in name or '.hs' in model:
        return 'Half'
    elif 'full sheet' in name or 'fullsheet' in name or '.fs' in model:
        return 'Full'
    elif '10x10' in name or '10"x10"' in name or '.10x10' in model:
        return '10x10'
    elif '5x10' in name or '5"x10"' in name or '.5x10' in model:
        return '5x10'
    elif '5x5' in name or '5"x5"' in name or '.5x5' in model:
        return '5x5'
    return None


def get_thickness(row: Dict) -> str:
    """Determine glass thickness (2mm or 3mm)."""
    name = str(row.get('Product_Name', '')).lower()
    vendor_sku = str(row.get('Vendor SKU', row.get('Vendor_SKU', ''))).lower()

    if '2mm' in name or 'thin-rolled' in name or '-0050-' in vendor_sku:
        return '2mm'
    elif '3mm' in name or 'double-rolled' in name or '-0030-' in vendor_sku:
        return '3mm'
    return '3mm'  # Default to 3mm


def is_sheet_glass(row: Dict) -> bool:
    """Check if product is sheet glass (orderable from Bullseye)."""
    name = str(row.get('Product_Name', '')).lower()
    model = str(row.get('Model', '')).lower()
    vendor_sku = str(row.get('Vendor SKU', row.get('Vendor_SKU', ''))).lower()

    exclusions = [
        'by the pound', 'sampler', 'disco pack', 'disco round',
        'mystery box', 'class pack', '10 pack', 'wissmach', 'coe96',
        'colorline', 'frit', '-tube', 'thinfire', 'shelf paper',
        'ribbon', 'stringer', 'noodle', 'rod', 'confetti', 'billet',
        'accessory', 'tool', 'kiln', 'mold', 'tekta'
    ]

    for excl in exclusions:
        if excl in name or excl in model or excl in vendor_sku:
            return False

    sizes = ['half sheet', 'full sheet', '10x10', '5x10', '5x5',
             'halfsheet', 'hs', 'fs', '10"x10"', '5"x10"', '5"x5"']

    for size in sizes:
        if size in name.lower() or size in model.lower():
            return True

    return False


def calculate_order_with_cascade(inv_data: Dict, thickness: str) -> Tuple[int, int, int, Dict]:
    """
    COMPLETE CASCADE ALGORITHM

    Args:
        inv_data: Dict with keys 'Half', '10x10', '5x10', '5x5', each containing:
            - qty: current stock
            - purchased: annual sales
            - name: product name
        thickness: '2mm' or '3mm'

    Returns:
        Tuple of (sheets_to_order, sheets_to_cut, sheets_to_save, validation_data)
    """
    validation = {
        'before': {},
        'after_inv_cascade': {},
        'after_order': {},
        'inv_cascade_steps': [],
        'order_steps': [],
        'order_needed': False,
        'decision_reason': '',
        'all_above_04': False
    }

    # Build initial state
    sizes = ['Half', '10x10', '5x10', '5x5']
    stock = {}
    purchased = {}

    for size in sizes:
        if size in inv_data:
            stock[size] = inv_data[size]['qty']
            purchased[size] = inv_data[size]['purchased']
        else:
            stock[size] = 0
            purchased[size] = 0

    # Calculate min stock for thresholds
    min_025 = {s: calc_min_stock(purchased[s], 0.25) for s in sizes}
    min_040 = {s: calc_min_stock(purchased[s], 0.40) for s in sizes}
    target = {s: calc_min_stock(purchased[s], 0.496) for s in sizes}  # 181 days

    # BEFORE state
    for size in sizes:
        validation['before'][size] = {
            'stock': stock[size],
            'years': calc_years(stock[size], purchased[size]),
            'purchased': purchased[size],
            'target': target[size],
            'deficit': max(0, target[size] - stock[size])
        }

    # =========================================
    # STEP 1: CASCADE FROM EXISTING INVENTORY
    # =========================================
    working_stock = stock.copy()
    cascade_steps = []

    # For 3mm: Check Half Sheet excess (2 Half = 1 Full equiv)
    half_cut_from_inv = 0
    if thickness == '3mm':
        half_excess = max(0, working_stock['Half'] - min_040['Half'])
        if half_excess >= 2:
            pairs_to_cut = half_excess // 2
            half_cut_from_inv = pairs_to_cut * 2

            # Yields from cutting Half pairs
            ten_from_half = pairs_to_cut * 6
            five10_from_half = pairs_to_cut * 2

            working_stock['Half'] -= half_cut_from_inv
            working_stock['10x10'] += ten_from_half
            working_stock['5x10'] += five10_from_half

            cascade_steps.append(f"Cut {half_cut_from_inv} Half Sheets (inventory) -> {ten_from_half}x 10x10 + {five10_from_half}x 5x10")

    # Check other cascade from inventory (5x10 excess -> 5x5, etc.)
    five10_excess = max(0, working_stock['5x10'] - min_040['5x10'])
    five5_deficit = max(0, min_040['5x5'] - working_stock['5x5'])

    if five10_excess > 0 and five5_deficit > 0:
        five10_to_cascade = min(five10_excess, math.ceil(five5_deficit / 2))
        five5_from_cascade = five10_to_cascade * 2
        working_stock['5x10'] -= five10_to_cascade
        working_stock['5x5'] += five5_from_cascade
        cascade_steps.append(f"Cascade {five10_to_cascade}x 5x10 (inventory) -> {five5_from_cascade}x 5x5")

    validation['inv_cascade_steps'] = cascade_steps if cascade_steps else ["No cascade possible from inventory"]

    # After inventory cascade state
    for size in sizes:
        validation['after_inv_cascade'][size] = {
            'stock': working_stock[size],
            'years': calc_years(working_stock[size], purchased[size]),
            'purchased': purchased[size],
            'target': target[size],
            'deficit': max(0, target[size] - working_stock[size])
        }

    # =========================================
    # STEP 2: CHECK IF ORDER NEEDED (0.25yr)
    # =========================================
    below_threshold = []
    for size in sizes:
        years = calc_years(working_stock[size], purchased[size])
        if years < 0.25 and purchased[size] > 0:
            below_threshold.append(f"{size} at {years:.2f}yr")

    if not below_threshold:
        validation['order_needed'] = False
        validation['decision_reason'] = "All sizes at 0.25+ years after inventory cascade"
        validation['after_order'] = validation['after_inv_cascade'].copy()
        validation['all_above_04'] = True
        return 0, 0, 0, validation

    validation['order_needed'] = True
    validation['decision_reason'] = f"Below 0.25yr: {', '.join(below_threshold)}"

    # =========================================
    # STEP 3: CALCULATE MINIMUM ORDER (0.4yr)
    # =========================================
    order_steps = []

    # Calculate deficits to reach 0.4yr
    deficits = {s: max(0, min_040[s] - working_stock[s]) for s in sizes}

    sheets_to_cut = 0
    sheets_to_save = 0

    if thickness == '3mm':
        # Check Half deficit - need to SAVE Full Sheets as Half
        if deficits['Half'] > 0:
            sheets_to_save = math.ceil(deficits['Half'] / 2)
            order_steps.append(f"Save {sheets_to_save} Full Sheet(s) as {sheets_to_save * 2} Half")

        # Calculate Full Sheets to cut for 10x10 deficit
        if deficits['10x10'] > 0:
            sheets_to_cut = math.ceil(deficits['10x10'] / 6)

        # Check if 5x10 needs more sheets
        five10_from_cuts = sheets_to_cut * 2
        remaining_five10_deficit = max(0, deficits['5x10'] - five10_from_cuts)
        if remaining_five10_deficit > 0:
            extra_for_five10 = math.ceil(remaining_five10_deficit / 2)
            if extra_for_five10 > sheets_to_cut:
                sheets_to_cut = extra_for_five10

        if sheets_to_cut > 0:
            order_steps.append(f"Cut {sheets_to_cut} Full Sheet(s) -> {sheets_to_cut * 6}x 10x10 + {sheets_to_cut * 2}x 5x10")

        # Apply cuts
        final_stock = working_stock.copy()
        final_stock['Half'] += sheets_to_save * 2
        final_stock['10x10'] += sheets_to_cut * 6
        final_stock['5x10'] += sheets_to_cut * 2

        # =========================================
        # STEP 4: CASCADE FROM ORDER
        # =========================================
        # Check 10x10 surplus for cascading
        ten_surplus = final_stock['10x10'] - min_040['10x10']
        five10_still_need = max(0, min_040['5x10'] - final_stock['5x10'])
        five5_still_need = max(0, min_040['5x5'] - final_stock['5x5'])

        # Cascade 10x10 -> 5x10 if needed
        if ten_surplus > 0 and five10_still_need > 0:
            tens_for_five10 = min(ten_surplus, math.ceil(five10_still_need / 2))
            final_stock['10x10'] -= tens_for_five10
            final_stock['5x10'] += tens_for_five10 * 2
            order_steps.append(f"Cascade {tens_for_five10}x 10x10 -> {tens_for_five10 * 2}x 5x10")
            ten_surplus = final_stock['10x10'] - min_040['10x10']

        # Cascade 10x10 -> 5x5 if needed
        five5_still_need = max(0, min_040['5x5'] - final_stock['5x5'])
        if ten_surplus > 0 and five5_still_need > 0:
            tens_for_five5 = min(ten_surplus, math.ceil(five5_still_need / 4))
            final_stock['10x10'] -= tens_for_five5
            final_stock['5x5'] += tens_for_five5 * 4
            order_steps.append(f"Cascade {tens_for_five5}x 10x10 -> {tens_for_five5 * 4}x 5x5")

        # Cascade 5x10 -> 5x5 if still needed
        five10_surplus = final_stock['5x10'] - min_040['5x10']
        five5_still_need = max(0, min_040['5x5'] - final_stock['5x5'])
        if five10_surplus > 0 and five5_still_need > 0:
            five10s_for_five5 = min(five10_surplus, math.ceil(five5_still_need / 2))
            final_stock['5x10'] -= five10s_for_five5
            final_stock['5x5'] += five10s_for_five5 * 2
            order_steps.append(f"Cascade {five10s_for_five5}x 5x10 -> {five10s_for_five5 * 2}x 5x5")

    else:  # 2mm
        # Check Half deficit - need to SAVE Half Sheets uncut
        if deficits['Half'] > 0:
            sheets_to_save = deficits['Half']
            order_steps.append(f"Keep {sheets_to_save} Half Sheet(s) uncut")

        # Calculate Half Sheets to cut for 10x10/5x10 deficit
        if deficits['10x10'] > 0:
            sheets_to_cut = math.ceil(deficits['10x10'] / 2)

        five10_from_cuts = sheets_to_cut * 2
        remaining_five10_deficit = max(0, deficits['5x10'] - five10_from_cuts)
        if remaining_five10_deficit > 0:
            extra = math.ceil(remaining_five10_deficit / 2)
            if extra > sheets_to_cut:
                sheets_to_cut = extra

        if sheets_to_cut > 0:
            order_steps.append(f"Cut {sheets_to_cut} Half Sheet(s) -> {sheets_to_cut * 2}x 10x10 + {sheets_to_cut * 2}x 5x10")

        # Apply cuts
        final_stock = working_stock.copy()
        final_stock['Half'] += sheets_to_save
        final_stock['10x10'] += sheets_to_cut * 2
        final_stock['5x10'] += sheets_to_cut * 2

        # Cascade from order
        ten_surplus = final_stock['10x10'] - min_040['10x10']
        five5_still_need = max(0, min_040['5x5'] - final_stock['5x5'])

        if ten_surplus > 0 and five5_still_need > 0:
            tens_for_five5 = min(ten_surplus, math.ceil(five5_still_need / 4))
            final_stock['10x10'] -= tens_for_five5
            final_stock['5x5'] += tens_for_five5 * 4
            order_steps.append(f"Cascade {tens_for_five5}x 10x10 -> {tens_for_five5 * 4}x 5x5")

    validation['order_steps'] = order_steps if order_steps else ["No order steps needed"]

    # After order state
    for size in sizes:
        validation['after_order'][size] = {
            'stock': final_stock[size],
            'years': calc_years(final_stock[size], purchased[size]),
            'purchased': purchased[size],
            'target': target[size],
            'deficit': max(0, target[size] - final_stock[size])
        }

    # =========================================
    # STEP 5: VERIFY ALL ABOVE 0.4yr
    # =========================================
    all_above_04 = True
    for size in sizes:
        if purchased[size] > 0:
            years = calc_years(final_stock[size], purchased[size])
            if years < 0.40:
                all_above_04 = False
                break

    validation['all_above_04'] = all_above_04

    total_sheets = sheets_to_cut + sheets_to_save
    return total_sheets, sheets_to_cut, sheets_to_save, validation


def get_reorder_flag(inv_data: Dict) -> Optional[Tuple[str, str]]:
    """Determine reorder flag using Cut Sheet system logic."""
    min_days = 9999
    has_zero_no_source = False
    zero_sizes_no_source = []
    total_sales = 0
    critical_size = None

    half_qty = inv_data.get('Half', {}).get('qty', 0)
    ten_qty = inv_data.get('10x10', {}).get('qty', 0)
    five10_qty = inv_data.get('5x10', {}).get('qty', 0)
    five5_qty = inv_data.get('5x5', {}).get('qty', 0)

    for size in ['Half', '10x10', '5x10', '5x5']:
        if size in inv_data:
            qty = inv_data[size]['qty']
            sold = inv_data[size]['purchased']
            total_sales += sold

            if sold > 0:
                days = int(qty / sold * 365)
                if days < min_days:
                    min_days = days
                    critical_size = size

                if qty == 0:
                    has_source = False
                    if size == '5x5' and (half_qty > 0 or ten_qty > 0 or five10_qty > 0):
                        has_source = True
                    elif size == '5x10' and (half_qty > 0 or ten_qty > 0):
                        has_source = True
                    elif size == '10x10' and half_qty > 0:
                        has_source = True

                    if not has_source:
                        has_zero_no_source = True
                        zero_sizes_no_source.append(size)

    if has_zero_no_source and total_sales >= 100:
        return ('URGENT', f"{', '.join(zero_sizes_no_source)} at ZERO, no source - high volume ({total_sales}/yr)")

    if has_zero_no_source:
        return ('REORDER', f"{', '.join(zero_sizes_no_source)} at ZERO - no source material")

    if min_days < CRITICAL_DAYS and total_sales >= 50:
        return ('REORDER', f"{critical_size} at {min_days}d - below critical threshold")

    if min_days < (ORDER_THRESHOLD_YEARS * 365) and total_sales >= 30:
        return ('WATCH', f"{critical_size} at {min_days}d - below 91 day target")

    return None


def analyze_cascade(products: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """
    Group products by parent and analyze reorder needs with cascade logic.

    Args:
        products: List of product dicts with keys:
            - Product_Name
            - Product_ID
            - Products_Parent_Id (or Parent_ID)
            - Purchased
            - Quantity_in_Stock
            - Model (optional)
            - Vendor SKU (optional)

    Returns:
        Tuple of (results_list, validations_list)
        - results_list: Summary CSV data (one row per product family)
        - validations_list: Full validation data for each family
    """
    parents = defaultdict(lambda: {'products': [], 'inv_data': {}})

    for row in products:
        # Skip non-sheet glass
        if not is_sheet_glass(row):
            continue

        # Skip inactive products
        status = str(row.get('Products Status', row.get('Products_Status', ''))).lower()
        if status == 'inactive':
            continue

        size = get_size_type(row)
        if size is None:
            continue

        # Get parent ID - try multiple column names
        parent_id = row.get('Products_Parent_Id', row.get('Parent_ID', row.get('products_parent_id', 0)))
        try:
            parent_id = int(parent_id) if parent_id else 0
        except (ValueError, TypeError):
            parent_id = 0

        thickness = get_thickness(row)
        key = f"{parent_id}_{thickness}"

        try:
            qty = float(row.get('Quantity_in_Stock', 0) or 0)
            sold = float(row.get('Purchased', 0) or 0)
        except (ValueError, TypeError):
            continue

        # Skip parent products (qty >= 75000)
        if qty >= 75000:
            continue

        parents[key]['products'].append(row)
        parents[key]['inv_data'][size] = {
            'qty': qty,
            'purchased': sold,
            'name': row.get('Product_Name', '')
        }
        parents[key]['parent_id'] = parent_id
        parents[key]['thickness'] = thickness

    results = []
    all_validations = []

    for key, data in parents.items():
        inv_data = data['inv_data']
        thickness = data['thickness']

        # Skip if no sizes found
        if not inv_data:
            continue

        flag_result = get_reorder_flag(inv_data)
        if flag_result is None:
            continue

        flag_type, reason = flag_result

        # Calculate with full cascade logic
        sheets_needed, sheets_cut, sheets_save, validation = calculate_order_with_cascade(inv_data, thickness)

        # Get base product name (strip size suffixes)
        base_name = ''
        if data['products']:
            base_name = data['products'][0].get('Product_Name', '')
            for s in ['10x10', '5x10', '5x5', 'Half Sheet', 'Full Sheet',
                     '10"x10"', '5"x10"', '5"x5"', '- Size ']:
                base_name = base_name.replace(f' - Size {s}', '').replace(f' {s}', '').replace(s, '')
            base_name = base_name.strip()

        total_sales = sum(inv_data[s]['purchased'] for s in inv_data)

        # Add metadata to validation
        validation['product_name'] = base_name
        validation['thickness'] = thickness
        validation['flag'] = flag_type
        validation['flag_reason'] = reason
        validation['sheets_to_order'] = sheets_needed
        validation['sheets_to_cut'] = sheets_cut
        validation['sheets_to_save'] = sheets_save
        validation['parent_id'] = data['parent_id']
        all_validations.append(validation)

        # Build result row
        results.append({
            'Parent_ID': data['parent_id'],
            'Product': base_name[:60],
            'Thickness': thickness,
            'Flag': flag_type,
            'Reason': reason,
            'Order_Type': 'Full Sheet' if thickness == '3mm' else 'Half Sheet',
            'Sheets_to_Order': sheets_needed,
            'Sheets_to_Cut': sheets_cut,
            'Sheets_to_Save': sheets_save,
            'Total_Sales': int(total_sales),
            'Order_Needed': 'Yes' if validation['order_needed'] else 'No',
            'Decision_Reason': validation['decision_reason'],
            'Inv_Cascade_Steps': ' | '.join(validation['inv_cascade_steps']),
            'Order_Steps': ' | '.join(validation['order_steps']),
            'All_Above_04': 'Yes' if validation['all_above_04'] else 'No',
            # Before state
            'Half_Before_Stock': validation['before'].get('Half', {}).get('stock', 0),
            'Half_Before_Years': round(validation['before'].get('Half', {}).get('years', 0), 2),
            '10x10_Before_Stock': validation['before'].get('10x10', {}).get('stock', 0),
            '10x10_Before_Years': round(validation['before'].get('10x10', {}).get('years', 0), 2),
            '5x10_Before_Stock': validation['before'].get('5x10', {}).get('stock', 0),
            '5x10_Before_Years': round(validation['before'].get('5x10', {}).get('years', 0), 2),
            '5x5_Before_Stock': validation['before'].get('5x5', {}).get('stock', 0),
            '5x5_Before_Years': round(validation['before'].get('5x5', {}).get('years', 0), 2),
            # After state
            'Half_After_Stock': validation['after_order'].get('Half', {}).get('stock', 0),
            'Half_After_Years': round(validation['after_order'].get('Half', {}).get('years', 0), 2),
            '10x10_After_Stock': validation['after_order'].get('10x10', {}).get('stock', 0),
            '10x10_After_Years': round(validation['after_order'].get('10x10', {}).get('years', 0), 2),
            '5x10_After_Stock': validation['after_order'].get('5x10', {}).get('stock', 0),
            '5x10_After_Years': round(validation['after_order'].get('5x10', {}).get('years', 0), 2),
            '5x5_After_Stock': validation['after_order'].get('5x5', {}).get('stock', 0),
            '5x5_After_Years': round(validation['after_order'].get('5x5', {}).get('years', 0), 2),
        })

    # Sort by flag priority, then by total sales
    flag_order = {'URGENT': 0, 'REORDER': 1, 'WATCH': 2}
    results.sort(key=lambda x: (flag_order.get(x['Flag'], 9), -x['Total_Sales']))
    all_validations.sort(key=lambda x: (flag_order.get(x['flag'], 9), -sum(x['before'][s]['purchased'] for s in x['before'])))

    return results, all_validations
