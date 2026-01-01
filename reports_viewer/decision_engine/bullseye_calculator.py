"""
Bullseye Glass Reorder Calculator
Implements simplified decision logic with 0.25/0.40 year thresholds
"""
import math
from typing import Dict, List, Optional
from .base_calculator import BaseCalculator


class BullseyeCalculator(BaseCalculator):
    """
    Bullseye Glass reorder calculation logic

    Thresholds:
    - ORDER_DECISION: 0.25 years (91 days) - if below, order is needed
    - ORDER_TARGET: 0.40 years (146 days) - target inventory level

    Note: Full cascade algorithm (5 steps) requires manual review.
    This calculator provides basic reorder quantities and flags cascade opportunities.
    """

    ORDER_DECISION = 0.25  # 91 days - order if below this
    ORDER_TARGET = 0.40    # 146 days - target inventory level
    LEAN_THRESHOLD = 0.20  # Flag as lean inventory

    def __init__(self):
        super().__init__()
        self.manufacturer = "Bullseye Glass"

    def calculate(self, product: Dict) -> Dict:
        """
        Calculate reorder quantity for Bullseye Glass product

        Args:
            product: Dict with keys:
                - Product_Name: str
                - Product_ID: int
                - Purchased: float (annual sales)
                - Quantity_in_Stock: int
                - (Optional) Product_Thickness: str (2mm or 3mm)
                - (Optional) Product_Size: str (Half, 10x10, 5x10, 5x5)

        Returns:
            Dict with keys:
                - reorder_quantity: int
                - years_in_stock: float
                - reason: str
                - questions: List[Dict] (if any)
                - calculation_details: Dict
        """
        product_name = product.get('Product_Name', 'Unknown')
        product_id = product.get('Product_ID', 0)
        purchased = product.get('Purchased', 0)
        quantity_in_stock = product.get('Quantity_in_Stock', 0)

        # Calculate years in stock
        years_in_stock = self.calculate_years_in_stock(quantity_in_stock, purchased)

        questions = []
        calculation_details = {}

        # CASE 1: Never sold (Purchased = 0)
        if purchased == 0:
            return {
                'reorder_quantity': 0,
                'years_in_stock': None,
                'reason': 'No sales history - manual review needed',
                'questions': [{
                    'priority': 'HIGH',
                    'question': f'Product "{product_name}" (ID: {product_id}) has never sold. Should we stock it?',
                    'field_name': 'reorder_quantity',
                    'suggested_answer': 'No (wait for first sale)'
                }],
                'calculation_details': {
                    'threshold_used': 'N/A',
                    'alert': 'NO_SALES'
                }
            }

        # CASE 2: Already at or above target (0.40 years)
        if years_in_stock >= self.ORDER_TARGET:
            return {
                'reorder_quantity': 0,
                'years_in_stock': years_in_stock,
                'reason': f'Adequate stock ({years_in_stock:.2f} years ≥ {self.ORDER_TARGET} target)',
                'questions': [],
                'calculation_details': {
                    'threshold_used': f'{self.ORDER_TARGET} years',
                    'alert': 'WELL_STOCKED' if years_in_stock >= 0.50 else None
                }
            }

        # CASE 3: Above order decision threshold (0.25) but below target (0.40)
        if years_in_stock >= self.ORDER_DECISION:
            # Optional: Order to reach target or accept current level
            deficit = (purchased * self.ORDER_TARGET) - quantity_in_stock
            reorder_quantity = max(1, math.ceil(deficit))

            questions.append({
                'priority': 'MEDIUM',
                'question': f'Product "{product_name}" is at {years_in_stock:.2f} years (above 0.25 but below 0.40 target). Order {reorder_quantity} units to reach target?',
                'field_name': 'reorder_quantity',
                'suggested_answer': f'{reorder_quantity} units (conservative approach)'
            })

            return {
                'reorder_quantity': reorder_quantity,
                'years_in_stock': years_in_stock,
                'reason': f'Optional reorder to reach target (currently {years_in_stock:.2f} years)',
                'questions': questions,
                'calculation_details': {
                    'threshold_used': f'{self.ORDER_TARGET} years target',
                    'target_quantity': purchased * self.ORDER_TARGET,
                    'deficit': deficit,
                    'alert': 'OPTIONAL_REORDER'
                }
            }

        # CASE 4: Below order decision threshold (0.25) - ORDER NEEDED
        # Calculate quantity needed to reach 0.40 year target
        target_quantity = purchased * self.ORDER_TARGET
        deficit = target_quantity - quantity_in_stock
        reorder_quantity = max(1, math.ceil(deficit))

        # Check if this is a zero stock situation (URGENT)
        alert = None
        priority_flag = ''
        if quantity_in_stock == 0:
            alert = 'ZERO_STOCK'
            priority_flag = 'URGENT: '
        elif years_in_stock <= self.LEAN_THRESHOLD:
            alert = 'LEAN_INVENTORY'
            priority_flag = 'LEAN: '

        # Check if product might benefit from cascade logic
        thickness = product.get('Product_Thickness', '').lower()
        size = product.get('Product_Size', '').lower()

        if thickness == '3mm' and 'half' in size:
            questions.append({
                'priority': 'MEDIUM',
                'question': f'Product "{product_name}" is 3mm Half Sheet. Check if excess Half Sheets can be cascaded (2 Half = 1 Full for cutting).',
                'field_name': 'cascade_opportunity',
                'suggested_answer': 'Review inventory for cascade opportunity before ordering'
            })
        elif '10' in size and 'x' in size:  # 10x10 or 5x10
            questions.append({
                'priority': 'LOW',
                'question': f'Product "{product_name}" ({size}). Check if larger sizes can be cascaded down to reduce order.',
                'field_name': 'cascade_opportunity',
                'suggested_answer': 'Review cascade options (10×10→5×10→5×5)'
            })

        reason = f'{priority_flag}Need {reorder_quantity} units to reach {self.ORDER_TARGET} years target (currently {years_in_stock:.2f} years)'

        return {
            'reorder_quantity': reorder_quantity,
            'years_in_stock': years_in_stock,
            'reason': reason,
            'questions': questions,
            'calculation_details': {
                'threshold_used': f'{self.ORDER_TARGET} years',
                'current_years': years_in_stock,
                'target_quantity': target_quantity,
                'deficit': deficit,
                'alert': alert,
                'note': 'Full cascade algorithm requires manual review - see Bullseye_Vendor_Purchase_Decision_Tree.md'
            }
        }

    def get_manufacturer_info(self) -> Dict:
        """Return information about this manufacturer's rules"""
        return {
            'name': 'Bullseye Glass',
            'order_decision_threshold': self.ORDER_DECISION,
            'order_target_threshold': self.ORDER_TARGET,
            'lean_threshold': self.LEAN_THRESHOLD,
            'thresholds': {
                '0.25 years (91 days)': 'Order Decision - if below, order is needed',
                '0.40 years (146 days)': 'Order Target - aim for this level',
                '0.20 years (73 days)': 'Lean Inventory - flag for urgent attention'
            },
            'notes': [
                'Bullseye uses two-threshold system (0.25 decision, 0.40 target)',
                'Full 5-step cascade algorithm not automated - manual review required',
                'Cascade opportunities flagged in questions for manual processing',
                '3mm products: 2 Half Sheets = 1 Full Sheet equivalent for cutting',
                '2mm products: Half Sheets cut individually (cannot combine)',
                'Cutting yields: Full (3mm) → 6× 10×10 + 2× 5×10',
                'Cutting yields: Half (2mm) → 2× 10×10 + 2× 5×10'
            ]
        }
