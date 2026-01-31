"""
Partner Availability Configuration Package
"""

__version__ = "0.1.1"

from partner_availability.models import PartnerAvailabilityConfig, Base
from partner_availability.service import PartnerAvailabilityService

__all__ = [
    "PartnerAvailabilityConfig",
    "PartnerAvailabilityService",
    "Base",
]
