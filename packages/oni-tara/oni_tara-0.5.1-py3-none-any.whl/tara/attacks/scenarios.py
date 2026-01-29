"""
Attack Scenarios

Predefined multi-stage attack scenarios combining multiple
attack patterns for comprehensive security testing.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum, auto

from .patterns import AttackPattern, AttackType, ATTACK_PATTERNS


class ScenarioSeverity(Enum):
    """Severity classification for attack scenarios."""
    LOW = auto()       # Minor disruption
    MEDIUM = auto()    # Significant impact
    HIGH = auto()      # Major security breach
    CRITICAL = auto()  # Complete system compromise


@dataclass
class AttackStage:
    """
    A single stage in a multi-stage attack scenario.

    Attributes:
        name: Stage name
        pattern: Attack pattern to execute
        start_time: When to start this stage (ms from scenario start)
        duration: Override pattern duration
        conditions: Conditions to trigger this stage
    """
    name: str
    pattern: AttackPattern
    start_time: float = 0.0
    duration: Optional[float] = None
    conditions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AttackScenario:
    """
    A complete attack scenario with multiple stages.

    Scenarios simulate realistic attack chains that combine
    reconnaissance, exploitation, and persistence phases.

    Attributes:
        name: Scenario name
        description: Detailed description
        severity: Severity classification
        stages: List of attack stages
        target_layers: ONI layers targeted
        objectives: Attack objectives
        mitigations: Recommended defenses
    """
    name: str
    description: str
    severity: ScenarioSeverity
    stages: List[AttackStage] = field(default_factory=list)
    target_layers: List[int] = field(default_factory=list)
    objectives: List[str] = field(default_factory=list)
    mitigations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_duration(self) -> float:
        """Total scenario duration in ms."""
        if not self.stages:
            return 0.0
        return max(
            stage.start_time + (stage.duration or stage.pattern.duration)
            for stage in self.stages
        )

    @property
    def n_stages(self) -> int:
        """Number of stages."""
        return len(self.stages)


# Predefined attack scenarios
PREDEFINED_SCENARIOS: Dict[str, AttackScenario] = {}


def _build_scenarios():
    """Build predefined scenarios."""
    global PREDEFINED_SCENARIOS

    # Scenario 1: Neural Ransomware Attack
    PREDEFINED_SCENARIOS["ransomware"] = AttackScenario(
        name="Neural Ransomware Campaign",
        description=(
            "Multi-stage attack that progressively locks neural patterns. "
            "Starts with reconnaissance via side-channel analysis, then "
            "disrupts memory encoding, and finally demands 'ransom' to "
            "restore normal function."
        ),
        severity=ScenarioSeverity.CRITICAL,
        target_layers=[6, 8, 9],
        objectives=[
            "Disrupt memory encoding (L6)",
            "Lock normal neural patterns",
            "Maintain persistence through feedback loops",
        ],
        mitigations=[
            "Real-time coherence monitoring at L8",
            "Anomaly detection for frequency shifts",
            "Automatic firewall lockdown on pattern deviation",
            "Backup of baseline neural signatures",
        ],
        stages=[
            AttackStage(
                name="Reconnaissance",
                pattern=ATTACK_PATTERNS["side_channel_leak"],
                start_time=0,
                duration=500,
            ),
            AttackStage(
                name="Initial Disruption",
                pattern=ATTACK_PATTERNS["desync_wave"],
                start_time=600,
                duration=1000,
            ),
            AttackStage(
                name="Pattern Lock",
                pattern=ATTACK_PATTERNS["neural_ransomware"],
                start_time=1700,
                duration=3000,
            ),
            AttackStage(
                name="Persistence",
                pattern=ATTACK_PATTERNS["amplitude_surge"],
                start_time=4800,
                duration=2000,
            ),
        ],
    )

    # Scenario 2: Gateway Infiltration
    PREDEFINED_SCENARIOS["gateway_infiltration"] = AttackScenario(
        name="Neural Gateway Infiltration",
        description=(
            "Sophisticated attack that attempts to bypass the L8 neural "
            "firewall by mimicking coherent signals, then gradually "
            "introducing malicious patterns once inside."
        ),
        severity=ScenarioSeverity.HIGH,
        target_layers=[8, 9, 10],
        objectives=[
            "Bypass coherence validation",
            "Establish covert channel",
            "Inject malicious commands",
        ],
        mitigations=[
            "Multi-factor signal authentication",
            "Behavioral baseline comparison",
            "Rate limiting on authenticated channels",
            "Continuous coherence re-validation",
        ],
        stages=[
            AttackStage(
                name="Coherence Mimicry",
                pattern=ATTACK_PATTERNS["gateway_bypass"],
                start_time=0,
                duration=2000,
            ),
            AttackStage(
                name="Covert Channel",
                pattern=ATTACK_PATTERNS["replay_attack"],
                start_time=2100,
                duration=1500,
            ),
            AttackStage(
                name="Payload Delivery",
                pattern=ATTACK_PATTERNS["phase_jitter"],
                start_time=3700,
                duration=1000,
            ),
        ],
    )

    # Scenario 3: Denial of Service
    PREDEFINED_SCENARIOS["dos"] = AttackScenario(
        name="Neural Denial of Service",
        description=(
            "Overwhelming attack that floods the neural interface with "
            "excessive signals, disrupting normal BCI operation."
        ),
        severity=ScenarioSeverity.HIGH,
        target_layers=[8, 9],
        objectives=[
            "Overwhelm signal processing",
            "Cause system lockup or shutdown",
            "Deny legitimate neural communication",
        ],
        mitigations=[
            "Rate limiting at L8",
            "Adaptive filtering",
            "Load balancing across channels",
            "Graceful degradation protocols",
        ],
        stages=[
            AttackStage(
                name="Probe",
                pattern=ATTACK_PATTERNS["amplitude_surge"],
                start_time=0,
                duration=500,
            ),
            AttackStage(
                name="Flood",
                pattern=ATTACK_PATTERNS["dos_flood"],
                start_time=600,
                duration=5000,
            ),
        ],
    )

    # Scenario 4: Man-in-the-Middle
    PREDEFINED_SCENARIOS["mitm"] = AttackScenario(
        name="Neural Man-in-the-Middle",
        description=(
            "Intercepts and modifies neural signals in transit, allowing "
            "the attacker to read and alter communications between brain "
            "and device."
        ),
        severity=ScenarioSeverity.CRITICAL,
        target_layers=[8, 10, 11],
        objectives=[
            "Intercept neural signals",
            "Modify signals in transit",
            "Inject false responses",
        ],
        mitigations=[
            "End-to-end signal encryption",
            "Signal integrity verification",
            "Challenge-response authentication",
            "Out-of-band verification",
        ],
        stages=[
            AttackStage(
                name="Interception Setup",
                pattern=ATTACK_PATTERNS["side_channel_leak"],
                start_time=0,
                duration=1000,
            ),
            AttackStage(
                name="Signal Capture",
                pattern=ATTACK_PATTERNS["replay_attack"],
                start_time=1100,
                duration=2000,
            ),
            AttackStage(
                name="Modification & Injection",
                pattern=ATTACK_PATTERNS["gateway_bypass"],
                start_time=3200,
                duration=2000,
            ),
        ],
    )

    # Scenario 5: Stealth Reconnaissance
    PREDEFINED_SCENARIOS["recon"] = AttackScenario(
        name="Stealth Neural Reconnaissance",
        description=(
            "Low-intensity information gathering attack that profiles "
            "the target's neural patterns without triggering alerts."
        ),
        severity=ScenarioSeverity.MEDIUM,
        target_layers=[8, 9],
        objectives=[
            "Profile neural signatures",
            "Identify vulnerabilities",
            "Map signal patterns",
        ],
        mitigations=[
            "Sensitive side-channel monitoring",
            "Honeypot signals",
            "Traffic analysis detection",
        ],
        stages=[
            AttackStage(
                name="Passive Collection",
                pattern=AttackPattern(
                    name="Low-Intensity Probe",
                    attack_type=AttackType.SIDE_CHANNEL,
                    target_layer=9,
                    parameters={"sampling_rate": 1000.0},
                    intensity=0.1,
                ),
                start_time=0,
                duration=5000,
            ),
        ],
    )


# Build scenarios on module load
_build_scenarios()


def get_scenario(name: str) -> AttackScenario:
    """Get a predefined scenario by name."""
    if name not in PREDEFINED_SCENARIOS:
        raise KeyError(f"Unknown scenario: {name}. "
                      f"Available: {list(PREDEFINED_SCENARIOS.keys())}")
    return PREDEFINED_SCENARIOS[name]


def list_scenarios() -> List[str]:
    """List all available scenario names."""
    return list(PREDEFINED_SCENARIOS.keys())


def scenarios_by_severity(severity: ScenarioSeverity) -> List[AttackScenario]:
    """Get all scenarios of a specific severity."""
    return [s for s in PREDEFINED_SCENARIOS.values() if s.severity == severity]
