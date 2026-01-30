# src/aletheia/__init__.py

"""
AletheiaEmu: A fast emulator for the non-linear matter power spectrum
based on the evolution mapping framework.
"""

# Promote the main classes to the top-level of the package
from .AletheiaEmu import AletheiaEmu
from .cosmology import Cosmology 
from .growth import GrowthCalculator     

# Control what 'from aletheia import *' does
__all__ = ['AletheiaEmu', 'Cosmology', 'GrowthCalculator']
