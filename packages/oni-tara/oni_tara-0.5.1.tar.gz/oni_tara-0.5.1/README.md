# TARA - Neural Security Platform

**Telemetry Awareness and Response Analyzer**

TARA is a comprehensive neural security platform for brain-computer interfaces (BCIs). It combines neural network simulation, attack modeling, real-time security monitoring, and interactive visualization in a unified framework aligned with the ONI 14-layer model.

Named after Tara, the Buddhist goddess of protection who guides travelers safely through darkness — with 8 forms protecting against 8 fears, just as TARA protects neural interfaces across all ONI layers.

---

## Overview

TARA provides:

- **Neural Simulation**: Biologically plausible neural network simulation with LIF, Izhikevich, and Hodgkin-Huxley neuron models
- **Attack Simulation**: Comprehensive attack pattern library for security testing (ransomware, DoS, gateway bypass, etc.)
- **Neural Signal Assurance Monitoring (NSAM)**: Real-time anomaly detection and signal integrity validation
- **Brain Topology Visualization**: 3D brain visualization with electrode monitoring and region analysis
- **Neural Firewall**: ONI-aligned 7-layer (L8-L14) signal validation pipeline
- **Neural Simulator**: Interactive brain region security analysis with attack vectors and defenses
- **BCI Node Network**: Monitoring and connectivity visualization for distributed firewall nodes
- **Unified Dashboard**: Streamlit-based web interface for monitoring, testing, and analysis
- **Neurosecurity Module**: Kohno threat taxonomy (2009) and BCI privacy filtering (Bonaci et al. 2015)

---

## Installation

```bash
# Basic installation
pip install oni-tara

# With web UI support
pip install oni-tara[ui]

# With simulation features
pip install oni-tara[simulation]

# With MOABB datasets (real EEG for security testing)
pip install oni-tara[moabb]

# Full installation (includes MOABB)
pip install oni-tara[full]

# Development installation (from source)
cd MAIN/tara-neural-security-platform
pip install -e ".[full,dev]"
```

---

## Quick Start

### Launch the Dashboard

```bash
tara ui
```

The dashboard opens at `http://localhost:8501` with these pages:

| Page | Section | Description |
|------|---------|-------------|
| **Dashboard** | Monitoring | System status, alerts, BCI nodes, real-time metrics |
| **Brain Topology** | Monitoring | 3D brain visualization with electrode monitoring |
| **Neural Firewall** | Monitoring | ONI L8-L14 validation pipeline |
| **Signal Assurance** | Monitoring | Live metrics, alerts management, event logs |
| **Neural Simulator** | Testing | Brain region security analysis |
| **Attack Testing** | Testing | Execute attack scenarios |
| **Settings** | Configuration | Thresholds, rules, system parameters |

### Test with Real EEG Data (MOABB)

TARA integrates with [MOABB](https://github.com/NeuroTechX/moabb) (BSD 3-Clause) for testing against real BCI data:

```python
from tara.data import MOABBAdapter, is_moabb_available
from tara import NeuralFirewall, CoherenceMetric

# Check if MOABB is installed
if not is_moabb_available():
    print("Install with: pip install oni-tara[moabb]")
else:
    # Load real EEG dataset
    adapter = MOABBAdapter()
    dataset = adapter.load_dataset("BNCI2014_001")  # Motor imagery
    signals = adapter.get_signals(dataset, subject=1, max_epochs=10)

    # Test coherence metric on real signals
    coherence = CoherenceMetric()
    firewall = NeuralFirewall()

    for signal in signals:
        cs_score = coherence.calculate(signal.data)
        result = firewall.process_signal(signal.to_tara_format())
        print(f"Signal: {signal.label}, Cₛ={cs_score:.3f}, Passed={result}")

    # Inject attack and test detection
    attacked = adapter.inject_attack(signals[0], "spike", intensity=2.0)
    attack_cs = coherence.calculate(attacked.attacked)
    print(f"Attack injected: Cₛ dropped from {cs_score:.3f} to {attack_cs:.3f}")
```

**Available Datasets:**
| Dataset | Paradigm | Subjects | ONI Relevance |
|---------|----------|----------|---------------|
| BNCI2014_001 | Motor Imagery | 9 | Motor cortex (L13) attack detection |
| BNCI2014_002 | Motor Imagery | 14 | Longitudinal firewall validation |
| EPFLP300 | P300 | 8 | Privacy-sensitive ERP (Kohno threats) |
| SSVEP_Exo | SSVEP | 12 | Frequency injection attack vectors |

**Citation:** When publishing results using MOABB data, cite:
> Jayaram, V., & Barachant, A. (2018). MOABB: Trustworthy algorithm benchmarking for BCIs. *J Neural Eng*, 15(6), 066011.

---

### Python API

```python
from tara import NeuralNSAM, AttackSimulator, NeuralFirewall, NeurosecurityMonitor
from tara.simulation import LayeredNetwork

# Create ONI-aligned neural network
network = LayeredNetwork.create_oni_model()

# Initialize Neural Signal Assurance Monitoring
nsam = NeuralNSAM()
session = nsam.start()

# Process incoming metrics
metrics = {"coherence": 0.75, "spike_rate": 50.0}
result = nsam.process(metrics)

if result and result.detected:
    print(f"Anomaly detected: {result.anomaly_type}")

# Stop monitoring
session = nsam.stop()
print(f"Processed {session.samples_processed} samples")
```

### Run Attack Simulations

```python
from tara.attacks import AttackSimulator
from tara.attacks.scenarios import get_scenario

simulator = AttackSimulator()
scenario = get_scenario("ransomware")

result = simulator.run_scenario(scenario)
print(f"Detection rate: {result.detection_rate:.1%}")
print(f"Block rate: {result.block_rate:.1%}")
```

---

## CLI Reference

```bash
# Launch web dashboard
tara ui --port 8501

# Run neural simulation
tara simulate --network oni --neurons 200 --duration 1000

# Execute attack scenario
tara attack --scenario ransomware --intensity 0.7

# Start monitoring
tara monitor --realtime

# List available resources
tara list patterns
tara list scenarios
tara list rules
```

---

## Architecture

TARA follows the ONI (Organic Neurocomputing Interface) 14-layer model:

```
BIOLOGICAL DOMAIN (L1-L7):
  L1-L7: Molecular → Behavioral (brain-side processing)

BRIDGE (L8):
  L8: Neural Gateway (primary security boundary - FIREWALL LOCATION)

SILICON DOMAIN (L9-L14):
  L9:  Signal Processing  - ADC, filtering, amplification
  L10: Protocol           - Data formatting, transmission rules
  L11: Transport          - Encryption, reliable delivery
  L12: Session            - Connection management, state tracking
  L13: Presentation       - Data interpretation, motor intention
  L14: Application        - End-user interfaces, identity & ethics
```

### Brain Regions → ONI Layer Mapping

| Region | Name | ONI Layer | Function |
|--------|------|-----------|----------|
| M1 | Primary Motor Cortex | L13 | Motor command execution |
| S1 | Primary Somatosensory | L12 | Tactile/proprioceptive processing |
| PMC | Premotor Cortex | L13 | Movement planning |
| SMA | Supplementary Motor | L13 | Sequence coordination |
| PFC | Prefrontal Cortex | L14 | Executive function, decision-making |
| BROCA | Broca's Area | L14 | Speech production |
| WERNICKE | Wernicke's Area | L14 | Language comprehension |
| V1 | Primary Visual | L12 | Visual processing |
| A1 | Primary Auditory | L12 | Auditory processing |
| HIPP | Hippocampus | L11 | Memory formation |

### Components

```
tara/
├── core/                  # ONI Framework security primitives
│   ├── coherence.py       # Coherence metric (Cₛ) calculation
│   ├── layers.py          # 14-layer model implementation
│   ├── firewall.py        # Neural firewall with decision matrix
│   └── scale_freq.py      # Scale-frequency invariant (f × S ≈ k)
│
├── simulation/            # Neural network simulation
│   ├── neurons/           # LIF, Izhikevich, Hodgkin-Huxley, Adaptive LIF
│   ├── synapses/          # Chemical, Electrical, STDP
│   ├── networks/          # Layered, Recurrent, Small-World
│   └── engine/            # Simulation execution engine
│
├── attacks/               # Attack simulation
│   ├── patterns.py        # Attack pattern definitions
│   ├── generator.py       # Attack signal generation
│   ├── scenarios.py       # Multi-stage attack scenarios
│   └── simulator.py       # Attack execution engine
│
├── nsam/                  # Neural Signal Assurance Monitoring (NSAM)
│   ├── events.py          # Event storage and management
│   ├── rules.py           # Detection rules engine
│   ├── detector.py        # Anomaly detection algorithms
│   ├── alerts.py          # Alert management
│   └── monitor.py         # Real-time monitoring
│
├── data/                  # Data models
│   ├── brain_regions.py   # Brain region definitions (10 regions)
│   └── bci_nodes.py       # BCI node network models
│
├── neurosecurity/         # Neurosecurity integration
│   ├── __init__.py        # ONI neurosecurity wrapper
│   └── integration.py     # Kohno rules, NeurosecurityMonitor
│
├── visualization/         # Real-time visualization
│   ├── components/
│   │   ├── brain_topology.py      # 3D brain visualization
│   │   └── firewall_pipeline.py   # ONI L8-L14 pipeline
│   ├── embeds/
│   │   └── html_bridge.py         # ONI-visualizations embedding
│   └── themes/
│       └── oni_theme.py           # ONI color scheme
│
├── ui/                    # Web interface
│   └── app.py             # Streamlit dashboard
│
└── cli.py                 # Command-line interface
```

---

## Dashboard Features

### Dashboard Page
- **Real-time Signal Monitor**: Coherence and spike rate charts (expandable)
- **System Status**: Monitor status, alerts, BCI nodes, network health, firewall pass rate
- **Recent Alerts**: Color-coded alert feed with severity levels
- **BCI Node Network**: Interactive topology visualization with node details

### Brain Topology Page
- **3D Brain Visualization**: Transparent brain mesh with electrode markers
- **Region Highlighting**: Click to focus on specific brain regions
- **Electrode Metrics**: Color-coded by spike rate, impedance, SNR, or status
- **Thread Visualization**: Electrode thread paths through cortex

### Neural Firewall Page
- **ONI L8-L14 Pipeline**: 7-checkpoint validation pipeline
- **Signal Processing**: Process signals through each checkpoint
- **Pass/Block Statistics**: Per-checkpoint pass rates and block counts
- **Checkpoint Details**: Threshold values and validation rules

### Neural Simulator Page
- **3D Brain with Regions**: Color-coded by ONI layer (L11-L14)
- **Region Security Analysis**: Function, attack vectors, defenses per region
- **Neuron Network Visualization**: 3D neuron connections within regions
- **ONI Layer Stack**: Visual representation of full layer model

### Attack Testing Page
- **Attack Scenarios**: Ransomware, DoS, gateway bypass, reconnaissance
- **Attack Timeline**: Stage-by-stage visualization
- **Detection Metrics**: Detection rate, block rate, response time, impact score

---

## Attack Patterns

TARA includes these predefined attack patterns:

| Pattern | Type | Target | Description |
|---------|------|--------|-------------|
| `phase_jitter` | Phase Disruption | L8 | Timing jitter to disrupt coherence |
| `amplitude_surge` | Amplitude Manipulation | L9 | Sudden amplitude spikes |
| `desync_wave` | Desynchronization | L3 | Disrupt neural synchrony |
| `neural_ransomware` | Ransomware | L6 | Lock neural patterns |
| `dos_flood` | DoS Flooding | L8 | Overwhelm signal processing |
| `gateway_bypass` | Layer 8 Gateway | L8 | Bypass firewall validation |
| `replay_attack` | Signal Replay | L8 | Replay captured signals |
| `side_channel_leak` | Side Channel | L9 | Information leakage via timing |

### Region-Specific Attack Vectors

| Region | Attack | Severity | Description |
|--------|--------|----------|-------------|
| M1 | Motor Hijacking | CRITICAL | Unauthorized motor commands |
| M1 | Motor Lockout | CRITICAL | Signal suppression causing paralysis |
| PFC | Decision Manipulation | CRITICAL | Influencing decision-making |
| PFC | Identity Erosion | CRITICAL | Long-term personality alteration |
| BROCA | Speech Hijacking | CRITICAL | Forcing unintended speech |
| HIPP | False Memory Implant | CRITICAL | Creating fabricated memories |
| HIPP | Memory Erasure | CRITICAL | Disrupting memory consolidation |

---

## Detection Rules

Predefined NSAM detection rules:

| Rule | Type | Action |
|------|------|--------|
| `coherence_low` | Threshold | Alert when Cₛ < 0.5 |
| `coherence_critical` | Threshold | Block when Cₛ < 0.3 |
| `spike_surge` | Threshold | Alert on spike rate > 200 Hz |
| `dos_signature` | Signature | Detect DoS attack pattern |
| `ransomware_signature` | Signature | Detect ransomware pattern |
| `gateway_bypass` | Signature | Detect bypass attempts |

---

## Neurosecurity Module

TARA includes a neurosecurity module implementing foundational BCI security research:

### Kohno Threat Taxonomy (2009)

Based on Denning, Matsuoka, & Kohno's seminal neurosecurity research, TARA detects three fundamental threat categories:

| Category | CIA Property | Description | Example Attacks |
|----------|--------------|-------------|-----------------|
| **Alteration** | Integrity | Unauthorized signal modification | Signal injection, command tampering, stimulation manipulation |
| **Blocking** | Availability | Denial or suppression of signals | DoS flooding, signal suppression, jamming, motor lockout |
| **Eavesdropping** | Confidentiality | Unauthorized information extraction | Cognitive leakage, memory extraction, face recognition probes |

### Kohno Detection Rules

| Rule | Category | Severity | Description |
|------|----------|----------|-------------|
| `kohno_signal_injection` | Alteration | Critical | Detects unauthorized signal injection |
| `kohno_command_modification` | Alteration | Critical | Detects tampering with motor commands |
| `kohno_stimulation_tampering` | Alteration | Critical | Detects unsafe stimulation parameters |
| `kohno_neural_dos` | Blocking | Critical | Detects signal flooding attacks |
| `kohno_signal_suppression` | Blocking | High | Detects malicious signal blocking |
| `kohno_jamming` | Blocking | Critical | Detects RF/EM jamming |
| `kohno_motor_lockout` | Blocking | Critical | Detects motor signal suppression |
| `kohno_cognitive_leakage` | Eavesdropping | Critical | Detects cognitive state extraction |
| `kohno_memory_extraction` | Eavesdropping | Critical | Detects memory content extraction |
| `kohno_face_recognition_probe` | Eavesdropping | High | Detects N170-based face probes |
| `kohno_emotional_inference` | Eavesdropping | High | Detects emotional state extraction |
| `kohno_side_channel` | Eavesdropping | High | Detects timing/power side channels |

### BCI Privacy Filtering

Inspired by Bonaci et al. (2015) research on BCI privacy, TARA includes:

- **Privacy Score Calculator**: Quantifies information leakage risk (0-1 scale)
- **BCI Anonymizer**: Filters privacy-sensitive ERP components while preserving motor commands
- **ERP Classification**: P300, N170, N400, ERN, LRP, CNV component identification

### Usage Example

```python
from tara import NeurosecurityMonitor, create_kohno_rules
from tara.nsam import RuleEngine

# Initialize neurosecurity monitor
monitor = NeurosecurityMonitor()

# Load Kohno rules into NSAM
engine = RuleEngine()
rules_loaded = monitor.load_kohno_rules(engine)
print(f"Loaded {rules_loaded} Kohno rules")

# Calculate privacy score
score = monitor.calculate_privacy_score(
    signal_data=[0.1, 0.2, 0.3, ...],
    detected_erps=["P300", "N170"]
)
if score:
    print(f"Privacy Risk: {score['score']:.2f}")
    print(f"Interpretation: {score['interpretation']}")

# Classify threat based on metrics
threat = monitor.classify_threat({
    "spike_rate": 600,
    "coherence": 0.2,
    "signal_entropy": 0.95,
})
if threat and threat['threats_detected']:
    for t in threat['threats']:
        print(f"Detected: {t['type']} ({t['category']})")
```

### References

- Denning, T., Matsuoka, Y., & Kohno, T. (2009). Neurosecurity: Security and privacy for neural devices. *Neurosurgical Focus*, 27(1), E7.
- Bonaci, T., Calo, R., & Chizeck, H. J. (2015). App stores for the brain: Privacy and security in brain-computer interfaces. *IEEE Technology and Society Magazine*, 34(2), 32-39.

**Note on BCI Anonymizer Patent:** The related patent application (US20140228701A1) was **abandoned** and never granted. The concepts from the academic research are freely available for implementation.

---

## API Reference

### Core Classes

```python
# Coherence calculation
from tara import calculate_cs
cs = calculate_cs(phase_data, amplitude_data, frequency_data)

# Neural firewall
from tara import NeuralFirewall
firewall = NeuralFirewall(threshold=0.5)
decision = firewall.evaluate(signal)

# Attack simulation
from tara import AttackSimulator, AttackPattern
simulator = AttackSimulator(dt=0.1, seed=42)

# Neural Signal Assurance Monitoring
from tara import NeuralNSAM, AlertLevel
nsam = NeuralNSAM()
nsam.on_alert(lambda a: print(f"Alert: {a.title}"))

# Neurosecurity (Kohno + Privacy)
from tara import NeurosecurityMonitor, create_kohno_rules
monitor = NeurosecurityMonitor()
privacy = monitor.calculate_privacy_score(signal_data, detected_erps=["P300"])
```

### Simulation Classes

```python
from tara.simulation import (
    LIFNeuron,
    IzhikevichNeuron,
    LayeredNetwork,
    RecurrentNetwork,
    Simulator,
)
```

### Data Models

```python
from tara.data import (
    BrainRegion,
    BRAIN_REGIONS,
    Electrode,
    ElectrodeThread,
    ElectrodeArray,
    BCINode,
    BCINodeNetwork,
    create_demo_network,
)
```

### Visualization

```python
from tara.visualization.components import (
    BrainTopologyVisualization,
    FirewallPipelineVisualization,
    NeuralFirewall,
)
from tara.visualization.themes import ONI_COLORS, apply_oni_theme
```

---

## Requirements

- Python 3.9+
- NumPy >= 1.21.0
- SciPy >= 1.7.0

Optional:
- Streamlit >= 1.28.0 (for UI)
- Plotly >= 5.17.0 (for visualizations)
- Matplotlib >= 3.5.0 (for simulation plots)
- Pandas >= 1.4.0 (for data manipulation)
- scikit-learn >= 1.0.0 (for anomaly detection)

---

## Development

### Project Structure

```
tara/
├── CLAUDE.md        # Claude AI instructions for updates
├── AGENTS.md        # Learnings from development sessions
├── README.md        # This file
├── pyproject.toml   # Package configuration
└── tests/           # Unit tests
```

### Running Locally

```bash
# Install in development mode
pip install -e ".[full,dev]"

# Run UI
python -m streamlit run tara/ui/app.py --server.port 8505

# Run tests
pytest tests/ -v
```

### Contributing

See `CLAUDE.md` for development conventions and update procedures.

---

## Related Projects

- [ONI Framework](https://github.com/qikevinl/ONI) - The underlying 14-layer BCI security model
- [oni-framework](../oni-framework) - Python library for ONI primitives

---

## License

Apache 2.0 License

---

## Citation

If you use TARA in your research, please cite:

```bibtex
@software{tara2026,
  title={TARA: Telemetry Awareness and Response Analyzer},
  author={Qi, Kevin L.},
  year={2026},
  url={https://github.com/qikevinl/ONI}
}
```

---

## Changelog

### v0.4.0 (2026-01-23)
- Added neurosecurity module with Kohno threat taxonomy (2009)
- Added 12 Kohno-based detection rules for NSAM
- Added BCI privacy filtering (Bonaci et al. 2015)
- Added NeurosecurityMonitor for real-time threat classification
- Added Privacy Score Calculator for information leakage risk assessment
- Integrated ONI Framework neurosecurity components

### v0.3.0 (2026-01-22)
- Added Neural Simulator with brain region security analysis
- Added region-specific attack vectors and defenses
- Added ONI layer stack visualization
- Renamed Simulation to Neural Simulator
- Updated documentation with comprehensive CLAUDE.md and AGENTS.md

### v0.2.0 (2026-01-22)
- Added visualization module with brain topology and firewall pipeline
- Added BCI node network monitoring
- Added ONI L8-L14 aligned firewall (7 checkpoints)
- Reorganized UI navigation into Monitoring/Testing/Configuration sections
- Consolidated BCI nodes to Dashboard

### v0.1.0 (2026-01)
- Initial release
- Core modules: coherence, layers, firewall, scale_freq
- Simulation: LIF, Izhikevich, Hodgkin-Huxley neurons
- Attacks: 8 predefined patterns, scenarios
- NSAM: Real-time monitoring with detection rules
- CLI: Basic commands for ui, simulate, attack, monitor

---

*Documents: README.md, CLAUDE.md, AGENTS.md*
*Modules: 9 | Sub-modules: 16 | Lines of Code: ~17,000*
*Last Updated: 2026-01-23*
