"""
TARA - Telemetry Awareness and Response Analyzer

A comprehensive neural security platform for brain-computer interfaces.
Combines neural simulation, attack modeling, and real-time monitoring
in a unified framework aligned with the ONI 14-layer model.

Named after Tara, the Buddhist goddess of protection who guides
travelers safely through darkness — with 8 forms protecting against
8 fears, just as TARA protects neural interfaces across all ONI layers.

Components:
- Core: Coherence metrics, 14-layer model, neural firewall
- Simulation: Neural network simulation (neurons, synapses, networks)
- Attacks: Attack pattern generation and injection
- NSAM: Neural Signal Assurance Monitoring for neural interfaces
- Visualization: Real-time dashboards and analytics
- UI: Web interface for non-technical users

Quick Start:
    >>> from tara import NeuralFirewall, AttackSimulator, NeuralNSAM
    >>> from tara.simulation import LayeredNetwork
    >>> from tara.ui import launch_dashboard

    >>> # Create ONI-aligned network
    >>> network = LayeredNetwork.create_oni_model()

    >>> # Initialize Neural Signal Assurance Monitoring
    >>> nsam = NeuralNSAM()

    >>> # Launch unified dashboard
    >>> launch_dashboard()

CLI Usage:
    $ tara ui                    # Launch web dashboard
    $ tara simulate --network oni --duration 1000
    $ tara attack --scenario ransomware --target network.json
    $ tara monitor --input signals.json --realtime

License: Apache 2.0
Repository: https://github.com/qikevinl/ONI
"""

__version__ = "0.5.1"
__author__ = "Kevin L. Qi"
__name_full__ = "Telemetry Awareness and Response Analyzer"  # TARA

# Core security components (from oni-framework)
from .core import (
    CoherenceMetric,
    calculate_cs,
    ONIStack,
    Layer,
    NeuralFirewall,
    ScaleFrequencyInvariant,
)

# Attack simulation
from .attacks import (
    AttackSimulator,
    AttackPattern,
    AttackScenario,
)

# Neural Signal Assurance Monitoring (NSAM)
from .nsam import (
    NeuralMonitor as NeuralNSAM,
    NeuralMonitor,
    Alert,
    AlertLevel,
    DetectionRule,
    AnomalyDetector,
    EventStore,
)

# Neurosecurity (Kohno 2009, Bonaci et al. 2015)
from .neurosecurity import (
    NeurosecurityMonitor,
    create_kohno_rules,
    KOHNO_DETECTION_RULES,
    _ONI_AVAILABLE as ONI_NEUROSECURITY_AVAILABLE,
)

# Conditionally export ONI components if available
try:
    from .neurosecurity import (
        ThreatType,
        KohnoThreatModel,
        BCIAnonymizer,
        PrivacyScoreCalculator,
        ERPType,
        PrivacySensitivity,
    )
    _neurosecurity_exports = [
        "ThreatType",
        "KohnoThreatModel",
        "BCIAnonymizer",
        "PrivacyScoreCalculator",
        "ERPType",
        "PrivacySensitivity",
    ]
except (ImportError, TypeError):
    _neurosecurity_exports = []

__all__ = [
    # Version info
    "__version__",
    "__name_full__",
    # Core
    "CoherenceMetric",
    "calculate_cs",
    "ONIStack",
    "Layer",
    "NeuralFirewall",
    "ScaleFrequencyInvariant",
    # Attacks
    "AttackSimulator",
    "AttackPattern",
    "AttackScenario",
    # NSAM (Neural Signal Assurance Monitoring)
    "NeuralNSAM",
    "NeuralMonitor",
    "Alert",
    "AlertLevel",
    "DetectionRule",
    "AnomalyDetector",
    "EventStore",
    # Neurosecurity
    "NeurosecurityMonitor",
    "create_kohno_rules",
    "KOHNO_DETECTION_RULES",
    "ONI_NEUROSECURITY_AVAILABLE",
] + _neurosecurity_exports
