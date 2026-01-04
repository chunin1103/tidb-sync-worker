"""
Decision Engine - Maps decision trees to database operations

This module provides:
1. Mermaid diagram parsing to extract decision nodes
2. Configuration system for mapping decisions to database fields
3. Validation modules to execute decisions against live data
4. Gap analysis to identify unmapped decisions
"""

__version__ = "1.0.0"
__author__ = "AGS Labs"

from .parser import MermaidDecisionParser
from .mapper import DecisionMapper
from .validator import DecisionValidator
from .analyzer import GapAnalyzer

__all__ = [
    'MermaidDecisionParser',
    'DecisionMapper',
    'DecisionValidator',
    'GapAnalyzer'
]
