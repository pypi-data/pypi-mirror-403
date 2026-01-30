"""
TARA - Telemetry Analysis and Response Automation

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
    >>> from tara_mvp import NeuralFirewall, AttackSimulator, NeuralNSAM
    >>> from tara_mvp.simulation import LayeredNetwork
    >>> from tara_mvp.ui import launch_dashboard

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

__version__ = "0.8.0"
__author__ = "Kevin L. Qi"
__name_full__ = "Telemetry Analysis and Response Automation"  # TARA

# Core security components (from oni-framework)
from .core import (
    CoherenceMetric,
    calculate_cs,
    ONIStack,
    Layer,
    NeuralFirewall,
    ScaleFrequencyInvariant,
)

# Bidirectional BCI support
from .core.firewall import (
    FlowDirection,
    StimulationCommand,
    StimulationResult,
    Signal,
    FilterResult,
    Decision,
)

# Attack simulation
from .attacks import (
    AttackSimulator,
    AttackPattern,
    AttackScenario,
)

# Yale Threat Model & CVSS (Schroder et al., 2025)
from .attacks.patterns import (
    YaleThreatCategory,
    CVSSScore,
    get_yale_patterns,
    get_cvss_summary,
    patterns_by_cvss_severity,
)
from .attacks.scenarios import (
    get_yale_scenarios,
    scenarios_by_yale_category,
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
    # Bidirectional BCI
    "FlowDirection",
    "StimulationCommand",
    "StimulationResult",
    "Signal",
    "FilterResult",
    "Decision",
    # Attacks
    "AttackSimulator",
    "AttackPattern",
    "AttackScenario",
    # Yale Threat Model & CVSS
    "YaleThreatCategory",
    "CVSSScore",
    "get_yale_patterns",
    "get_cvss_summary",
    "patterns_by_cvss_severity",
    "get_yale_scenarios",
    "scenarios_by_yale_category",
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
