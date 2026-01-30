"""
ONI Framework - Neural Security Library for Brain-Computer Interfaces
======================================================================

A Python library providing security primitives for BCI development and research.

WHAT YOU GET:
    Signal Trust      - Calculate coherence scores to validate neural signals
    Neural Firewall   - Accept/reject signals based on trust and authentication
    Privacy Tools     - Anonymize neural data, calculate privacy risk scores
    Threat Detection  - Classify threats using Kohno's CIA model
    Reference Model   - Navigate the 14-layer ONI architecture
    Consent Tracking  - Manage patient consent (including pediatric)

QUICK START:
    >>> from oni import CoherenceMetric, NeuralFirewall
    >>>
    >>> # Calculate signal trust score (0-1)
    >>> metric = CoherenceMetric(reference_freq=40.0)
    >>> cs = metric.calculate([0.0, 0.025, 0.050], [100, 98, 102])
    >>> print(f"Trust score: {cs:.2f}")
    >>>
    >>> # Filter signals through firewall
    >>> from oni.firewall import Signal
    >>> firewall = NeuralFirewall(threshold_high=0.6)
    >>> result = firewall.filter(Signal([0.0, 0.025], [100, 98]))
    >>> print(f"Decision: {result.decision.name}")  # ACCEPT, REJECT, or ACCEPT_FLAG

INSTALLATION:
    pip install oni-framework          # Core (zero dependencies)
    pip install oni-framework[ui]      # With interactive UI
    pip install oni-framework[all]     # Everything

LAUNCH UI:
    oni ui                             # Interactive learning interface

Built on research from:
    - Kohno et al. (2009): Neurosecurity threat model
    - Chizeck & Bonaci (2014): BCI Anonymizer architecture
    - Yuste et al. (2017): Neurorights framework
    - Ienca & Andorno (2017): Cognitive liberty principles

License: Apache 2.0
Author: Kevin L. Qi
"""

__version__ = "0.2.2"
__author__ = "Kevin L. Qi"

# =============================================================================
# BRAND: Project Identity (Single Source of Truth)
# =============================================================================
from .brand import ONI, TARA, ONI_VERSION, TARA_VERSION, get_brand

# =============================================================================
# CORE: Signal Trust & Validation
# =============================================================================
from .coherence import CoherenceMetric, calculate_cs, VarianceComponents
from .firewall import NeuralFirewall
from .scale_freq import ScaleFrequencyInvariant

# =============================================================================
# ARCHITECTURE: 14-Layer Reference Model
# =============================================================================
from .layers import ONIStack, Layer, Domain

# =============================================================================
# NEUROSECURITY: Threat Detection (Kohno 2009)
# =============================================================================
from .neurosecurity import (
    # Threat Model
    ThreatType,
    SecurityDecision,
    KohnoThreatModel,
    NeurosecurityFirewall,
    NeurosecurityConfig,
    # Privacy (BCI Anonymizer - Bonaci 2015)
    BCIAnonymizer,
    AnonymizerConfig,
    ERPType,
    PrivacySensitivity,
    # Privacy Scoring
    PrivacyScoreCalculator,
    PrivacyScoreResult,
)

# =============================================================================
# CONSENT: Patient Consent Management
# =============================================================================
try:
    from .neurosecurity.consent import (
        ConsentManager,
        ConsentScope,
        ConsentState,
        PediatricConsentState,
    )
    _CONSENT_AVAILABLE = True
except ImportError:
    _CONSENT_AVAILABLE = False

# =============================================================================
# PUBLIC API
# =============================================================================
__all__ = [
    # Version
    "__version__",
    "__author__",

    # Brand Identity
    "ONI",
    "TARA",
    "ONI_VERSION",
    "TARA_VERSION",
    "get_brand",

    # Signal Trust
    "CoherenceMetric",
    "calculate_cs",
    "VarianceComponents",
    "NeuralFirewall",
    "ScaleFrequencyInvariant",

    # Architecture
    "ONIStack",
    "Layer",
    "Domain",

    # Threat Detection (Kohno 2009)
    "ThreatType",
    "SecurityDecision",
    "KohnoThreatModel",
    "NeurosecurityFirewall",
    "NeurosecurityConfig",

    # Privacy (BCI Anonymizer)
    "BCIAnonymizer",
    "AnonymizerConfig",
    "ERPType",
    "PrivacySensitivity",
    "PrivacyScoreCalculator",
    "PrivacyScoreResult",
]

# Add consent exports if available
if _CONSENT_AVAILABLE:
    __all__.extend([
        "ConsentManager",
        "ConsentScope",
        "ConsentState",
        "PediatricConsentState",
    ])


def get_version() -> str:
    """Return the current ONI Framework version."""
    return __version__


def print_summary():
    """Print a summary of available modules and their purposes."""
    print(f"""
{ONI.name} v{__version__} — {ONI.tagline}
{'=' * 50}
{ONI.slogan}

SIGNAL TRUST
  CoherenceMetric      Calculate Cₛ trust scores (0-1)
  NeuralFirewall       Accept/reject signals
  ScaleFrequencyInvariant   Validate f × S ≈ k

ARCHITECTURE
  ONIStack             Navigate 14-layer model
  Layer                Individual layer details

THREAT DETECTION
  KohnoThreatModel     CIA threat classification
  NeurosecurityFirewall Combined coherence + threats

PRIVACY
  BCIAnonymizer        Strip sensitive ERPs (P300, N170)
  PrivacyScoreCalculator   Quantify info leakage risk

CONSENT
  ConsentManager       Track patient consent
  PediatricConsentState    Pediatric-aware consent

QUICK START
  >>> from oni import CoherenceMetric
  >>> metric = CoherenceMetric(reference_freq=40.0)
  >>> cs = metric.calculate([0.0, 0.025, 0.050], [100, 98, 102])

INTERACTIVE UI
  $ pip install oni-framework[ui]
  $ oni ui

DOCUMENTATION
  https://github.com/qikevinl/ONI
""")
