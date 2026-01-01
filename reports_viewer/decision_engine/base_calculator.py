"""
Base Calculator Class
All manufacturer-specific calculators inherit from this
"""
import math
from typing import Dict, List, Optional


class BaseCalculator:
    """Base class for reorder calculators"""

    def __init__(self, manufacturer: str):
        self.manufacturer = manufacturer

    def calculate(self, product: Dict) -> Dict:
        """
        Calculate reorder quantity for a product

        Args:
            product: Dictionary with keys:
                - Product_Name (str)
                - Product_ID (int)
                - Products_Parent_Id (int)
                - Purchased (int) - units sold in last year
                - Quantity_in_Stock (int)
                - Vendor_SKU (str)
                - Products_Status (str)

        Returns:
            Dictionary with:
                - reorder_quantity (int)
                - years_in_stock (float or None)
                - questions (list of dicts)
                - reason (str)
                - calculation_details (dict)
        """
        raise NotImplementedError("Subclasses must implement calculate()")

    def calculate_years_in_stock(self, quantity: int, purchased: int) -> Optional[float]:
        """Calculate years in stock metric"""
        if purchased == 0:
            return None
        return quantity / purchased

    def generate_question(self, priority: str, question_text: str,
                         field_name: str, suggested_answer: str) -> Dict:
        """Generate a standardized question dictionary"""
        return {
            'priority': priority,
            'question': question_text,
            'field': field_name,
            'suggested_answer': suggested_answer
        }
