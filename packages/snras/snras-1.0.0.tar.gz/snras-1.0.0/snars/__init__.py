"""
SNRAS Library
-------------
A professional tool for exoplanet transit vetting using the 
Signal-to-Noise Ratio with Adjusted Stability (SNRAS) metric.

Developed by: Ahmed Sattar Jabbar
License: MIT
Reference: A&A Manuscript aa59231-26
"""

# Import the core calculator and plotting tools to make them accessible 
# directly from the library level (e.g., import snras; snras.SNRASCalculator)
from .core import SNRASCalculator
from .utils import plot_veto_curve

# Define the library version
__version__ = "1.0.0"
__author__ = "Ahmed Sattar Jabbar"

# This allows users to see what is available in the package
__all__ = ["SNRASCalculator", "plot_veto_curve"]