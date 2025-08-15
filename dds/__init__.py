"""
Dynamic Data Standardizer (DDS)

A Python package for automatically mapping raw time-series data to predefined 
battery data structures using NLP-based similarity matching.
"""

__version__ = "1.0.0"
__author__ = "Dynamic Data Standardizer Team"

from .data_standardizer import DataStandardizer
from .cell_record import CellRecord, CycleRecord, CyclingProtocol

__all__ = ["DataStandardizer", "CellRecord", "CycleRecord", "CyclingProtocol"]