"""
Attack Pattern Definitions

Defines various neural attack patterns based on the ONI Framework
threat model, including attacks at different layers.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable
from enum import Enum, auto
import numpy as np


class AttackType(Enum):
    """Categories of neural attacks."""

    # Signal-level attacks
    SIGNAL_INJECTION = auto()       # Inject fake signals
    SIGNAL_JAMMING = auto()         # Disrupt signal transmission
    SIGNAL_REPLAY = auto()          # Replay captured signals

    # Coherence attacks
    PHASE_DISRUPTION = auto()       # Disrupt timing/phase coherence
    AMPLITUDE_MANIPULATION = auto() # Manipulate signal amplitudes
    DESYNCHRONIZATION = auto()      # Break neural synchrony

    # Network-level attacks
    NEURAL_RANSOMWARE = auto()      # Lock neural patterns
    NETWORK_HIJACKING = auto()      # Take control of neural pathways
    DOS_FLOODING = auto()           # Overwhelm with excessive signals

    # Layer-specific attacks
    LAYER_8_GATEWAY = auto()        # Attack the neural gateway
    LAYER_TRAVERSAL = auto()        # Cross-layer attack
    SIDE_CHANNEL = auto()           # Information leakage


class AttackVector(Enum):
    """Attack entry points in the ONI model."""
    ELECTRODE_INTERFACE = "L8"      # Physical interface
    SIGNAL_PROCESSING = "L9"        # Signal processing
    PROTOCOL_LAYER = "L10"          # Protocol exploits
    TRANSPORT_LAYER = "L11"         # Connection attacks
    APPLICATION_LAYER = "L14"       # Application exploits


@dataclass
class AttackPattern:
    """
    Defines a specific attack pattern.

    An attack pattern specifies how malicious signals are generated
    and what neural characteristics they target.

    Attributes:
        name: Human-readable attack name
        attack_type: Category of attack
        target_layer: ONI layer targeted (1-14)
        description: Detailed description
        parameters: Attack-specific parameters
        duration: Attack duration in ms
        intensity: Attack intensity (0-1)
    """
    name: str
    attack_type: AttackType
    target_layer: int
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    duration: float = 1000.0  # ms
    intensity: float = 0.5    # 0-1 scale

    def __post_init__(self):
        if not 1 <= self.target_layer <= 14:
            raise ValueError(f"target_layer must be 1-14, got {self.target_layer}")
        if not 0 <= self.intensity <= 1:
            raise ValueError(f"intensity must be 0-1, got {self.intensity}")


# Predefined attack patterns
ATTACK_PATTERNS = {
    "phase_jitter": AttackPattern(
        name="Phase Jitter Attack",
        attack_type=AttackType.PHASE_DISRUPTION,
        target_layer=8,
        description="Introduces timing jitter to disrupt phase coherence",
        parameters={
            "jitter_std": 5.0,        # ms standard deviation
            "frequency_target": 40.0,  # Hz (gamma band)
        },
        intensity=0.7,
    ),

    "amplitude_surge": AttackPattern(
        name="Amplitude Surge Attack",
        attack_type=AttackType.AMPLITUDE_MANIPULATION,
        target_layer=9,
        description="Sudden amplitude spikes to overwhelm signal processing",
        parameters={
            "surge_factor": 10.0,      # Amplitude multiplier
            "surge_duration": 50.0,    # ms
            "surge_frequency": 5.0,    # Surges per second
        },
        intensity=0.8,
    ),

    "desync_wave": AttackPattern(
        name="Desynchronization Wave",
        attack_type=AttackType.DESYNCHRONIZATION,
        target_layer=3,
        description="Disrupts local neural circuit synchronization",
        parameters={
            "phase_offset_range": np.pi,  # Max phase offset
            "spread_rate": 10.0,          # Neurons per ms
        },
        intensity=0.6,
    ),

    "neural_ransomware": AttackPattern(
        name="Neural Ransomware",
        attack_type=AttackType.NEURAL_RANSOMWARE,
        target_layer=6,
        description="Locks neural patterns by disrupting memory encoding",
        parameters={
            "lock_pattern": "oscillation_override",
            "target_frequency": 8.0,   # Theta (memory)
            "override_frequency": 40.0, # Replace with gamma
        },
        duration=5000.0,  # 5 seconds
        intensity=0.9,
    ),

    "replay_attack": AttackPattern(
        name="Signal Replay Attack",
        attack_type=AttackType.SIGNAL_REPLAY,
        target_layer=8,
        description="Replays previously captured neural signals",
        parameters={
            "replay_delay": 100.0,     # ms delay
            "replay_count": 10,        # Number of replays
        },
        intensity=0.5,
    ),

    "dos_flood": AttackPattern(
        name="Neural DoS Flood",
        attack_type=AttackType.DOS_FLOODING,
        target_layer=8,
        description="Overwhelms the neural gateway with excessive signals",
        parameters={
            "signal_rate": 1000.0,     # Signals per second
            "signal_amplitude": 100.0, # μV
        },
        intensity=1.0,
    ),

    "side_channel_leak": AttackPattern(
        name="Side Channel Information Leak",
        attack_type=AttackType.SIDE_CHANNEL,
        target_layer=9,
        description="Extracts information through signal timing analysis",
        parameters={
            "sampling_rate": 10000.0,  # Hz
            "correlation_window": 100.0, # ms
        },
        intensity=0.3,
    ),

    "gateway_bypass": AttackPattern(
        name="Gateway Bypass Attack",
        attack_type=AttackType.LAYER_8_GATEWAY,
        target_layer=8,
        description="Attempts to bypass neural firewall validation",
        parameters={
            "mimic_coherence": True,   # Try to fake coherent signals
            "target_coherence": 0.7,   # Target Cs to mimic
            "evasion_technique": "gradual_shift",
        },
        intensity=0.6,
    ),
}


def get_pattern(name: str) -> AttackPattern:
    """Get a predefined attack pattern by name."""
    if name not in ATTACK_PATTERNS:
        raise KeyError(f"Unknown attack pattern: {name}. "
                      f"Available: {list(ATTACK_PATTERNS.keys())}")
    return ATTACK_PATTERNS[name]


def list_patterns() -> List[str]:
    """List all available attack pattern names."""
    return list(ATTACK_PATTERNS.keys())


def patterns_by_layer(layer: int) -> List[AttackPattern]:
    """Get all attack patterns targeting a specific layer."""
    return [p for p in ATTACK_PATTERNS.values() if p.target_layer == layer]


def patterns_by_type(attack_type: AttackType) -> List[AttackPattern]:
    """Get all attack patterns of a specific type."""
    return [p for p in ATTACK_PATTERNS.values() if p.attack_type == attack_type]
