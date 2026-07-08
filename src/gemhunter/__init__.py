"""GemHunter — discover recently-founded startups that are already doing extremely well.

Uses the TrustMRR API (verified startup revenue) to surface "gems to replicate":
young companies (founded in the last N months) that have already built strong,
verified traction. Produces a standalone, filterable HTML website plus JSON/CSV.
"""

__version__ = "0.1.0"

from .models import Startup, GemResult
from .client import TrustMRRClient, TrustMRRError

__all__ = ["Startup", "GemResult", "TrustMRRClient", "TrustMRRError", "__version__"]
