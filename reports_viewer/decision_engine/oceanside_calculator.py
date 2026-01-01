"""
Oceanside Glass Reorder Calculator
Target: 0.35 years (128 days)
Source: Production/wiki/02_Business_Rules/Years_In_Stock_Thresholds.md
"""
import math
from typing import Dict, List
from .base_calculator import BaseCalculator


class OceansideCalculator(BaseCalculator):
    """Oceanside Glass decision tree logic"""

    # Thresholds from wiki
    LEAN_THRESHOLD = 0.20  # 73 days - minimum acceptable
    TARGET = 0.35  # 128 days - standard reorder target
    WELL_STOCKED = 0.40  # 146 days - adequate stock

    def __init__(self):
        super().__init__("Oceanside Glass")

    def calculate(self, product: Dict) -> Dict:
        """
        Calculate reorder quantity for Oceanside Glass product

        Decision tree:
        1. If never sold (Purchased = 0) → Generate question
        2. Calculate years_in_stock
        3. If >= 0.35 years → No reorder needed
        4. If < 0.35 years → Calculate deficit to reach 0.35
        5. Sanity check: Flag if ordering > 2 years worth
        """
        questions = []
        calculation_details = {}

        # Step 1: Handle products with no sales
        purchased = product.get('Purchased', 0)
        if purchased == 0:
            questions.append(self.generate_question(
                priority='HIGH',
                question_text=f"Product '{product['Product_Name']}' (ID: {product['Product_ID']}) has never sold. Should we stock it?",
                field_name='should_stock_new_product',
                suggested_answer='No (wait for first sale)'
            ))
            return {
                'reorder_quantity': 0,
                'years_in_stock': None,
                'questions': questions,
                'reason': 'No sales history - needs manual review',
                'calculation_details': calculation_details
            }

        # Step 2: Calculate years in stock
        quantity_in_stock = product.get('Quantity_in_Stock', 0)
        years_in_stock = self.calculate_years_in_stock(quantity_in_stock, purchased)

        calculation_details['purchased_annual'] = purchased
        calculation_details['quantity_in_stock'] = quantity_in_stock
        calculation_details['years_in_stock'] = round(years_in_stock, 2)
        calculation_details['target_years'] = self.TARGET

        # Step 3: Check if already at target
        if years_in_stock >= self.TARGET:
            return {
                'reorder_quantity': 0,
                'years_in_stock': years_in_stock,
                'questions': [],
                'reason': f'Already at {years_in_stock:.2f} years (target: {self.TARGET})',
                'calculation_details': calculation_details
            }

        # Step 4: Calculate deficit to reach target
        target_quantity = purchased * self.TARGET
        deficit = target_quantity - quantity_in_stock

        calculation_details['target_quantity'] = math.ceil(target_quantity)
        calculation_details['deficit'] = math.ceil(deficit)

        # Step 5: Round to reasonable unit (whole units)
        reorder_quantity = max(1, math.ceil(deficit))

        calculation_details['reorder_quantity_raw'] = deficit
        calculation_details['reorder_quantity_rounded'] = reorder_quantity

        # Step 6: Sanity checks
        if reorder_quantity > purchased * 2:
            # Ordering more than 2 years worth - flag for review
            suggested_qty = max(1, int(purchased * 0.5))
            questions.append(self.generate_question(
                priority='MEDIUM',
                question_text=f"Product '{product['Product_Name']}' (ID: {product['Product_ID']}): Calculated reorder is {reorder_quantity} units ({reorder_quantity / purchased:.2f} years worth). This seems high. Confirm or adjust?",
                field_name='reorder_quantity_override',
                suggested_answer=f'Reduce to {suggested_qty} units (0.5 years)'
            ))

        # Check if product is at zero (HIGH priority)
        if quantity_in_stock == 0:
            calculation_details['alert'] = 'ZERO STOCK - URGENT'
            reason = f'URGENT: Zero stock, needs {reorder_quantity} units to reach {self.TARGET} years'
        elif years_in_stock < self.LEAN_THRESHOLD:
            calculation_details['alert'] = 'LEAN INVENTORY'
            reason = f'Lean inventory ({years_in_stock:.2f} years < {self.LEAN_THRESHOLD}), needs {reorder_quantity} units'
        else:
            reason = f'Below target ({years_in_stock:.2f} < {self.TARGET}), needs {reorder_quantity} units'

        return {
            'reorder_quantity': reorder_quantity,
            'years_in_stock': years_in_stock,
            'questions': questions,
            'reason': reason,
            'calculation_details': calculation_details
        }
