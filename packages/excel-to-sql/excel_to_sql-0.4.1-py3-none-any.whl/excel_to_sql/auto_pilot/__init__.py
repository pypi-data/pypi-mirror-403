"""
Auto-Pilot Mode for Zero-Configuration Excel Import.

This module provides intelligent detection and configuration capabilities
for automatically importing Excel files into SQLite databases.
"""

from excel_to_sql.auto_pilot.detector import PatternDetector
from excel_to_sql.auto_pilot.header_detector import HeaderDetector

__all__ = ["PatternDetector", "HeaderDetector"]
