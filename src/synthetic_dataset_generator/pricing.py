"""Pricing concepts used by the generator.

Category price profiles live in :mod:`synthetic_dataset_generator.constants`; item-level
realization is performed with seeded log-normal variation in the order-item generator.
"""

from synthetic_dataset_generator.constants import CATEGORY_PROFILES

__all__ = ["CATEGORY_PROFILES"]
