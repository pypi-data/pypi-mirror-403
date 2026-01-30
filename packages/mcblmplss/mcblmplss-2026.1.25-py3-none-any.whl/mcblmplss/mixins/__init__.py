"""
MCP Mixins for BLM data services.

Each mixin provides tools for a specific BLM data domain.
"""

from mcblmplss.census import CountyInfo
from mcblmplss.mixins.acec import ACECMixin
from mcblmplss.mixins.grazing import GrazingMixin
from mcblmplss.mixins.mining_claims import MiningClaimsMixin
from mcblmplss.mixins.plss import BatchPLSSResult, PLSSMixin
from mcblmplss.mixins.recreation import RecreationMixin
from mcblmplss.mixins.surface_management import SurfaceManagementMixin
from mcblmplss.mixins.wild_horses import WildHorseMixin
from mcblmplss.mixins.wild_rivers import WildRiversMixin
from mcblmplss.mixins.wilderness import WildernessMixin

__all__ = [
    # Mixins
    "ACECMixin",
    "PLSSMixin",
    "SurfaceManagementMixin",
    "MiningClaimsMixin",
    "GrazingMixin",
    "WildHorseMixin",
    "WildRiversMixin",
    "WildernessMixin",
    "RecreationMixin",
    # Models
    "BatchPLSSResult",
    "CountyInfo",
]
