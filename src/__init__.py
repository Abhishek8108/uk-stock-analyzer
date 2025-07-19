"""
UK Stock Analyzer Package
=========================

An automated AI-powered UK stock analysis tool that:
- Analyzes UK stocks with technical indicators
- Uses Groq AI for intelligent stock selection
- Provides daily recommendations via Google Sheets
- Runs automated analysis via GitHub Actions

Modules:
--------
- stock_analyzer: Technical analysis and data fetching
- groq_analyzer: AI-powered stock analysis and recommendations
- google_sheets_updater: Google Sheets integration for output

Author: Your Name
License: MIT
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"
__license__ = "MIT"

# Import main classes for easy access
from .stock_analyzer import StockAnalyzer
from .groq_analyzer import GroqStockAnalyzer
from .google_sheets_updater import GoogleSheetsUpdater

# Package metadata
__all__ = [
    "StockAnalyzer",
    "GroqStockAnalyzer", 
    "GoogleSheetsUpdater",
]

# Package information
PACKAGE_INFO = {
    "name": "uk-stock-analyzer",
    "version": __version__,
    "description": "Automated AI-powered UK stock analysis with daily Google Sheets updates",
    "author": __author__,
    "license": __license__,
    "keywords": ["stocks", "UK", "FTSE", "analysis", "AI", "automation", "trading"],
    "dependencies": [
        "yfinance",
        "pandas", 
        "numpy",
        "requests",
        "groq",
        "google-api-python-client",
        "PyYAML",
        "python-dotenv"
    ]
}
